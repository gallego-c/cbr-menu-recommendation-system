import json
from typing import List, Dict, Any
from models import Plato, Menu, Caso, EstiloCulinario, TradicionCultural, TipoEvento


class BaseCasos:
    def __init__(self, archivo_persistencia: str = "base_casos.json"):
        self.casos: List[Caso] = []
        self.archivo_persistencia = archivo_persistencia
        self._cargar_casos()

    def _cargar_casos(self):
        try:
            with open(self.archivo_persistencia, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                for caso_dict in datos:
                    try:
                        caso = self._dict_a_caso(caso_dict)
                        self.casos.append(caso)
                    except (KeyError, TypeError, ValueError) as e:
                        print(f"⚠ Error cargando caso {caso_dict.get('id', 'desconocido')}: {e}")
                        continue
            print(f"✓ Cargados {len(self.casos)} casos desde {self.archivo_persistencia}")
        except FileNotFoundError:
            # No crear casos por defecto: informar y dejar la base vacía
            print(f"→ No se encontró {self.archivo_persistencia}. No hay casos en la base de datos.")
            print("→ El sistema no podrá generar respuestas informadas sin casos.")
            self.casos = []
        except json.JSONDecodeError:
            # Archivo corrupto: informar y dejar la base vacía (no sobrescribimos)
            print(f"→ Error leyendo {self.archivo_persistencia} (JSON inválido). No hay casos en la base de datos.")
            print("→ Revisa o repara el archivo JSON; el sistema no generará respuestas informadas.")
            self.casos = []

    def _dict_a_caso(self, caso_dict: dict) -> Caso:
        menu_dict = caso_dict['menu']

        estilo_value = menu_dict['estilo']
        if isinstance(estilo_value, str):
            estilo_value = EstiloCulinario(estilo_value)

        tradicion_value = menu_dict['tradicion']
        if isinstance(tradicion_value, str):
            tradicion_value = TradicionCultural(tradicion_value)

        def crear_plato(plato_dict: dict) -> Plato:
            defaults = {
                'textura': 'suave',
                'sabor_dominante': 'salado',
                'restricciones': [],
                'temporada': ['todo']
            }
            plato_data = plato_dict.copy()
            for key, default_value in defaults.items():
                if key not in plato_data or not plato_data[key]:
                    plato_data[key] = default_value
            return Plato(**plato_data)

        menu = Menu(
            entrante=crear_plato(menu_dict['entrante']),
            principal=crear_plato(menu_dict['principal']),
            postre=crear_plato(menu_dict['postre']),
            estilo=estilo_value,
            tradicion=tradicion_value
        )

        tipo_evento_value = caso_dict['tipo_evento']
        if isinstance(tipo_evento_value, str):
            tipo_evento_value = TipoEvento(tipo_evento_value)

        return Caso(
            id=caso_dict['id'],
            tipo_evento=tipo_evento_value,
            num_comensales=caso_dict['num_comensales'],
            presupuesto=caso_dict['presupuesto'],
            restricciones=caso_dict.get('restricciones', []),
            preferencias=caso_dict.get('preferencias', []),
            temporada=caso_dict['temporada'],
            menu=menu,
            exito=caso_dict.get('exito', 1.0),
            fallos_detectados=caso_dict.get('fallos_detectados', []),
            reparaciones_aplicadas=caso_dict.get('reparaciones_aplicadas', [])
        )

    def _guardar_casos(self):
        with open(self.archivo_persistencia, 'w', encoding='utf-8') as f:
            casos_dict = [self._caso_a_dict(caso) for caso in self.casos]
            json.dump(casos_dict, f, indent=2, ensure_ascii=False)

    def _caso_a_dict(self, caso: Caso) -> dict:
        caso_dict = caso.to_dict()
        caso_dict['tipo_evento'] = caso.tipo_evento.value
        caso_dict['menu']['estilo'] = caso.menu.estilo.value
        caso_dict['menu']['tradicion'] = caso.menu.tradicion.value
        return caso_dict

    def agregar_caso(self, caso: Caso):
        # Verificar si ya existe un caso idéntico
        for caso_existente in self.casos:
            if self._casos_son_identicos(caso, caso_existente):
                return False
        
        self.casos.append(caso)
        self._guardar_casos()
        return True
    
    def _casos_son_identicos(self, caso1: Caso, caso2: Caso) -> bool:
        """Compara dos casos para determinar si son idénticos"""
        # Comparar atributos principales del caso
        if (caso1.tipo_evento != caso2.tipo_evento or
            caso1.num_comensales != caso2.num_comensales or
            abs(caso1.presupuesto - caso2.presupuesto) > 0.01 or
            caso1.restricciones != caso2.restricciones or
            caso1.temporada != caso2.temporada):
            return False
        
        # Comparar menús
        if (caso1.menu.estilo != caso2.menu.estilo or
            caso1.menu.tradicion != caso2.menu.tradicion):
            return False
        
        # Comparar platos
        for plato1, plato2 in [(caso1.menu.entrante, caso2.menu.entrante),
                                (caso1.menu.principal, caso2.menu.principal),
                                (caso1.menu.postre, caso2.menu.postre)]:
            if (plato1.nombre != plato2.nombre or
                set(plato1.ingredientes) != set(plato2.ingredientes) or
                set(plato1.tecnica_coccion) != set(plato2.tecnica_coccion)):
                return False
        
        return True

    def obtener_todos(self) -> List[Caso]:
        return self.casos
