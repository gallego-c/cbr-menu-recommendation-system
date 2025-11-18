import json
import math
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# ==================== REPRESENTACIÓN DE CASOS ====================

class TipoEvento(Enum):
    BODA = "boda"
    CONGRESO = "congreso"
    BANQUETE = "banquete"
    FAMILIAR = "familiar"

class EstiloCulinario(Enum):
    MOLECULAR = "molecular"
    AUTOR = "autor"
    CLASICO = "clasico"
    NORDICO = "nordico"
    MEDITERRANEO = "mediterraneo"

class TradicionCultural(Enum):
    GRIEGA = "griega"
    ITALIANA = "italiana"
    CATALANA = "catalana"
    VASCA = "vasca"
    GALLEGA = "gallega"
    MARROQUI = "marroqui"
    TURCA = "turca"
    LIBANESA = "libanesa"
    SOMALI = "somali"
    ETIOPE = "etiope"
    RUSA = "rusa"

@dataclass
class Plato:
    nombre: str
    ingredientes: List[str]
    tecnica_coccion: str
    temporada: List[str]
    restricciones: List[str] = field(default_factory=list)

@dataclass
class Menu:
    entrante: Plato
    principal: Plato
    postre: Plato
    estilo: EstiloCulinario
    tradicion: TradicionCultural

@dataclass
class Caso:
    id: str
    tipo_evento: TipoEvento
    num_comensales: int
    presupuesto: float
    restricciones: List[str]
    preferencias: List[str]
    temporada: str
    menu: Menu
    exito: float = 1.0

    def to_dict(self):
        return asdict(self)

# ==================== BASE DE CASOS ====================

class BaseCasos:
    def __init__(self, archivo_persistencia: str = "base_casos.json"):
        self.casos: List[Caso] = []
        self.archivo_persistencia = archivo_persistencia
        self._cargar_casos()
    
    def _cargar_casos(self):
        """Carga casos desde archivo o inicializa base por defecto"""
        try:
            with open(self.archivo_persistencia, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                for caso_dict in datos:
                    caso = self._dict_a_caso(caso_dict)
                    self.casos.append(caso)
            print(f"✓ Cargados {len(self.casos)} casos desde {self.archivo_persistencia}")
        except FileNotFoundError:
            print(f"→ No se encontró {self.archivo_persistencia}, inicializando base por defecto")
            self._inicializar_casos_base()
            self._guardar_casos()
    
    def _dict_a_caso(self, caso_dict: dict) -> Caso:
        """Convierte diccionario a objeto Caso"""
        menu_dict = caso_dict['menu']
        menu = Menu(
            entrante=Plato(**menu_dict['entrante']),
            principal=Plato(**menu_dict['principal']),
            postre=Plato(**menu_dict['postre']),
            estilo=EstiloCulinario(menu_dict['estilo']),
            tradicion=TradicionCultural(menu_dict['tradicion'])
        )
        
        return Caso(
            id=caso_dict['id'],
            tipo_evento=TipoEvento(caso_dict['tipo_evento']),
            num_comensales=caso_dict['num_comensales'],
            presupuesto=caso_dict['presupuesto'],
            restricciones=caso_dict['restricciones'],
            preferencias=caso_dict['preferencias'],
            temporada=caso_dict['temporada'],
            menu=menu,
            exito=caso_dict.get('exito', 1.0)
        )
    
    def _guardar_casos(self):
        """Persiste casos en archivo JSON"""
        with open(self.archivo_persistencia, 'w', encoding='utf-8') as f:
            casos_dict = [self._caso_a_dict(caso) for caso in self.casos]
            json.dump(casos_dict, f, indent=2, ensure_ascii=False)
        print(f"✓ Base de casos guardada en {self.archivo_persistencia}")
    
    def _caso_a_dict(self, caso: Caso) -> dict:
        """Convierte Caso a diccionario serializable"""
        caso_dict = caso.to_dict()
        caso_dict['tipo_evento'] = caso.tipo_evento.value
        caso_dict['menu']['estilo'] = caso.menu.estilo.value
        caso_dict['menu']['tradicion'] = caso.menu.tradicion.value
        return caso_dict
    
    def _inicializar_casos_base(self):
        """Casos iniciales del sistema"""
        
        # Caso 1: Boda mediterránea
        caso1 = Caso(
            id="C001",
            tipo_evento=TipoEvento.BODA,
            num_comensales=100,
            presupuesto=5000.0,
            restricciones=["vegetariano"],
            preferencias=["ligero", "fresco"],
            temporada="verano",
            menu=Menu(
                entrante=Plato("Ensalada caprese", ["tomate", "mozzarella", "albahaca"], 
                              "crudo", ["verano"], ["vegetariano"]),
                principal=Plato("Risotto de setas", ["arroz", "setas", "parmesano"], 
                               "cocido", ["otoño", "primavera"], ["vegetariano"]),
                postre=Plato("Tiramisú", ["mascarpone", "café", "cacao"], 
                            "montado", ["todo"], ["vegetariano"]),
                estilo=EstiloCulinario.MEDITERRANEO,
                tradicion=TradicionCultural.ITALIANA
            ),
            exito=0.95
        )
        
        # Caso 2: Congreso vasco
        caso2 = Caso(
            id="C002",
            tipo_evento=TipoEvento.CONGRESO,
            num_comensales=50,
            presupuesto=2500.0,
            restricciones=["sin_cerdo"],
            preferencias=["tradicional", "contundente"],
            temporada="invierno",
            menu=Menu(
                entrante=Plato("Pimientos rellenos de bacalao", ["pimiento", "bacalao", "tomate"],
                              "horneado", ["verano", "otoño"], []),
                principal=Plato("Merluza a la vasca", ["merluza", "guisantes", "huevo"],
                               "guisado", ["todo"], []),
                postre=Plato("Cuajada con miel", ["leche", "cuajo", "miel"],
                            "cuajado", ["todo"], ["vegetariano"]),
                estilo=EstiloCulinario.CLASICO,
                tradicion=TradicionCultural.VASCA
            ),
            exito=0.90
        )
        
        # Caso 3: Banquete molecular
        caso3 = Caso(
            id="C003",
            tipo_evento=TipoEvento.BANQUETE,
            num_comensales=30,
            presupuesto=6000.0,
            restricciones=[],
            preferencias=["innovador", "sorprendente"],
            temporada="primavera",
            menu=Menu(
                entrante=Plato("Esferificación de gazpacho", ["tomate", "alginato", "pepino"],
                              "esferificado", ["verano"], ["vegetariano", "vegano"]),
                principal=Plato("Foie deconstruido", ["foie", "manzana", "brioche"],
                               "deconstruido", ["todo"], []),
                postre=Plato("Nitrógeno de chocolate", ["chocolate", "nitrógeno", "frambuesa"],
                            "congelado_flash", ["todo"], ["vegetariano"]),
                estilo=EstiloCulinario.MOLECULAR,
                tradicion=TradicionCultural.CATALANA
            ),
            exito=0.88
        )
        
        # Caso 4: Familiar libanés
        caso4 = Caso(
            id="C004",
            tipo_evento=TipoEvento.FAMILIAR,
            num_comensales=15,
            presupuesto=800.0,
            restricciones=["halal"],
            preferencias=["especiado", "compartir"],
            temporada="otoño",
            menu=Menu(
                entrante=Plato("Mezze variado", ["hummus", "baba_ganoush", "tabule"],
                              "crudo_montado", ["todo"], ["vegetariano", "vegano"]),
                principal=Plato("Shawarma de cordero", ["cordero", "especias", "yogur"],
                               "asado", ["todo"], ["halal"]),
                postre=Plato("Baklava", ["nueces", "miel", "phyllo"],
                            "horneado", ["todo"], ["vegetariano"]),
                estilo=EstiloCulinario.CLASICO,
                tradicion=TradicionCultural.LIBANESA
            ),
            exito=0.92
        )
        
        self.casos = [caso1, caso2, caso3, caso4]
    
    def agregar_caso(self, caso: Caso):
        self.casos.append(caso)
        self._guardar_casos()
    
    def obtener_todos(self) -> List[Caso]:
        return self.casos
    
    def obtener_estadisticas(self):
        """Muestra estadísticas de la base de casos"""
        print(f"\n--- ESTADÍSTICAS BASE DE CASOS ---")
        print(f"Total de casos: {len(self.casos)}")
        print(f"Éxito promedio: {sum(c.exito for c in self.casos) / len(self.casos):.2f}")
        
        eventos = {}
        for caso in self.casos:
            tipo = caso.tipo_evento.value
            eventos[tipo] = eventos.get(tipo, 0) + 1
        
        print(f"Distribución por tipo de evento:")
        for tipo, count in eventos.items():
            print(f"  - {tipo}: {count}")
        print(f"{'='*35}\n")

# ==================== SIMILITUD ====================

class CalculadorSimilitud:
    def __init__(self):
        self.pesos = {
            'tipo_evento': 0.25,
            'num_comensales': 0.15,
            'presupuesto': 0.15,
            'restricciones': 0.20,
            'preferencias': 0.15,
            'temporada': 0.10
        }
    
    def similitud_casos(self, caso_nuevo: Caso, caso_base: Caso) -> float:
        """Calcula similitud global entre dos casos"""
        
        sim_tipo = 1.0 if caso_nuevo.tipo_evento == caso_base.tipo_evento else 0.0
        
        sim_comensales = self._similitud_numerica(
            caso_nuevo.num_comensales, 
            caso_base.num_comensales,
            rango_max=200
        )
        
        sim_presupuesto = self._similitud_numerica(
            caso_nuevo.presupuesto,
            caso_base.presupuesto,
            rango_max=10000
        )
        
        sim_restricciones = self._similitud_conjuntos(
            caso_nuevo.restricciones,
            caso_base.restricciones
        )
        
        sim_preferencias = self._similitud_conjuntos(
            caso_nuevo.preferencias,
            caso_base.preferencias
        )
        
        sim_temporada = 1.0 if caso_nuevo.temporada == caso_base.temporada else 0.5
        
        similitud_total = (
            self.pesos['tipo_evento'] * sim_tipo +
            self.pesos['num_comensales'] * sim_comensales +
            self.pesos['presupuesto'] * sim_presupuesto +
            self.pesos['restricciones'] * sim_restricciones +
            self.pesos['preferencias'] * sim_preferencias +
            self.pesos['temporada'] * sim_temporada
        )
        
        return similitud_total
    
    def _similitud_numerica(self, val1: float, val2: float, rango_max: float) -> float:
        """Similitud entre valores numéricos"""
        diferencia = abs(val1 - val2)
        return max(0, 1 - (diferencia / rango_max))
    
    def _similitud_conjuntos(self, set1: List[str], set2: List[str]) -> float:
        """Similitud de Jaccard entre conjuntos"""
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        s1 = set(set1)
        s2 = set(set2)
        interseccion = len(s1 & s2)
        union = len(s1 | s2)
        
        return interseccion / union if union > 0 else 0.0

# ==================== RECUPERACIÓN ====================

class ModuloRecuperacion:
    def __init__(self, base_casos: BaseCasos, calculador: CalculadorSimilitud):
        self.base_casos = base_casos
        self.calculador = calculador
    
    def recuperar(self, caso_nuevo: Caso, k: int = 3) -> List[Tuple[Caso, float]]:
        """Recupera los k casos más similares"""
        
        similitudes = []
        for caso_base in self.base_casos.obtener_todos():
            sim = self.calculador.similitud_casos(caso_nuevo, caso_base)
            similitudes.append((caso_base, sim))
        
        similitudes.sort(key=lambda x: x[1], reverse=True)
        
        return similitudes[:k]

# ==================== ADAPTACIÓN ====================

class ModuloAdaptacion:
    def adaptar(self, caso_recuperado: Caso, caso_nuevo: Caso) -> Menu:
        """Adapta el menú recuperado al nuevo contexto"""
        
        menu_adaptado = Menu(
            entrante=caso_recuperado.menu.entrante,
            principal=caso_recuperado.menu.principal,
            postre=caso_recuperado.menu.postre,
            estilo=caso_recuperado.menu.estilo,
            tradicion=caso_recuperado.menu.tradicion
        )
        
        # Adaptar según restricciones nuevas
        if caso_nuevo.restricciones:
            menu_adaptado = self._adaptar_restricciones(menu_adaptado, caso_nuevo.restricciones)
        
        # Adaptar según temporada
        if caso_nuevo.temporada != caso_recuperado.temporada:
            menu_adaptado = self._adaptar_temporada(menu_adaptado, caso_nuevo.temporada)
        
        return menu_adaptado
    
    def _adaptar_restricciones(self, menu: Menu, restricciones: List[str]) -> Menu:
        """Verifica compatibilidad con restricciones"""
        # Simplificación: verificar que los platos cumplan restricciones
        return menu
    
    def _adaptar_temporada(self, menu: Menu, temporada: str) -> Menu:
        """Ajusta platos a temporada si es necesario"""
        return menu

# ==================== REVISIÓN ====================

class ModuloRevision:
    def revisar(self, menu_propuesto: Menu, caso_nuevo: Caso) -> Tuple[bool, float, str]:
        """Valida la solución propuesta"""
        
        puntuacion = 1.0
        explicacion = []
        
        # Verificar restricciones
        restricciones_ok = self._verificar_restricciones(menu_propuesto, caso_nuevo.restricciones)
        if not restricciones_ok:
            puntuacion -= 0.3
            explicacion.append("Algunas restricciones no se cumplen completamente")
        
        # Verificar coherencia de estilo
        coherencia = self._verificar_coherencia(menu_propuesto)
        puntuacion *= coherencia
        if coherencia < 1.0:
            explicacion.append("La coherencia del menú es mejorable")
        
        es_valido = puntuacion > 0.6
        explicacion_texto = "; ".join(explicacion) if explicacion else "Menú válido y coherente"
        
        return es_valido, puntuacion, explicacion_texto
    
    def _verificar_restricciones(self, menu: Menu, restricciones: List[str]) -> bool:
        """Verifica cumplimiento de restricciones"""
        platos = [menu.entrante, menu.principal, menu.postre]
        
        for restriccion in restricciones:
            cumple = all(restriccion in plato.restricciones or not plato.restricciones 
                        for plato in platos)
            if restriccion in ["vegetariano", "vegano", "halal"] and not cumple:
                return False
        
        return True
    
    def _verificar_coherencia(self, menu: Menu) -> float:
        """Evalúa coherencia del menú"""
        return 0.9

# ==================== RETENCIÓN ====================

class ModuloRetencion:
    def __init__(self, base_casos: BaseCasos):
        self.base_casos = base_casos
    
    def retener(self, caso_nuevo: Caso, exito: float):
        """Decide si añadir el nuevo caso a la base"""
        
        umbral_exito = 0.7
        
        if exito >= umbral_exito:
            caso_nuevo.exito = exito
            self.base_casos.agregar_caso(caso_nuevo)
            print(f"   → Caso {caso_nuevo.id} añadido a la base (éxito: {exito:.2f})")
            return True
        else:
            print(f"   → Caso {caso_nuevo.id} descartado (éxito {exito:.2f} < umbral {umbral_exito})")
        
        return False

# ==================== SISTEMA CBR PRINCIPAL ====================

class SistemaCBR:
    def __init__(self):
        self.base_casos = BaseCasos()
        self.calculador = CalculadorSimilitud()
        self.recuperacion = ModuloRecuperacion(self.base_casos, self.calculador)
        self.adaptacion = ModuloAdaptacion()
        self.revision = ModuloRevision()
        self.retencion = ModuloRetencion(self.base_casos)
    
    def resolver(self, caso_nuevo: Caso, k: int = 3) -> List[Dict[str, Any]]:
        """Ciclo completo CBR: Retrieve, Reuse, Revise, Retain"""
        
        print(f"\n{'='*60}")
        print(f"RESOLVIENDO CASO: {caso_nuevo.id}")
        print(f"Evento: {caso_nuevo.tipo_evento.value}, Comensales: {caso_nuevo.num_comensales}")
        print(f"Restricciones: {caso_nuevo.restricciones}")
        print(f"{'='*60}\n")
        
        # RETRIEVE: Recuperar casos similares
        print("1. RECUPERACIÓN")
        casos_similares = self.recuperacion.recuperar(caso_nuevo, k)
        
        propuestas = []
        
        for i, (caso_recuperado, similitud) in enumerate(casos_similares, 1):
            print(f"\n   Caso {i}: {caso_recuperado.id} (similitud: {similitud:.2f})")
            print(f"   - Estilo: {caso_recuperado.menu.estilo.value}")
            print(f"   - Tradición: {caso_recuperado.menu.tradicion.value}")
            
            # REUSE: Adaptar solución
            menu_adaptado = self.adaptacion.adaptar(caso_recuperado, caso_nuevo)
            
            # REVISE: Validar solución
            es_valido, puntuacion, explicacion = self.revision.revisar(menu_adaptado, caso_nuevo)
            
            propuesta = {
                'caso_origen': caso_recuperado.id,
                'similitud': similitud,
                'menu': menu_adaptado,
                'valido': es_valido,
                'puntuacion': puntuacion,
                'explicacion': explicacion
            }
            
            propuestas.append(propuesta)
            
            print(f"   - Validación: {'✓' if es_valido else '✗'} (puntuación: {puntuacion:.2f})")
            print(f"   - {explicacion}")
        
        # RETAIN: Retener mejor solución si tiene éxito
        print("\n4. RETENCIÓN")
        if propuestas:
            mejor_propuesta = max(propuestas, key=lambda p: p['puntuacion'])
            if mejor_propuesta['puntuacion'] > 0.7:
                caso_nuevo.menu = mejor_propuesta['menu']
                retenido = self.retencion.retener(caso_nuevo, mejor_propuesta['puntuacion'])
                if not retenido:
                    print(f"   → Caso no retenido (puntuación insuficiente)")
            else:
                print(f"   → Caso no retenido (puntuación {mejor_propuesta['puntuacion']:.2f} < umbral)")
        
        print(f"\n{'='*60}\n")
        
        return propuestas
    
    def explicar_propuesta(self, propuesta: Dict[str, Any]):
        """Genera explicación de la propuesta"""
        menu = propuesta['menu']
        print(f"\n--- MENÚ PROPUESTO ---")
        print(f"Estilo: {menu.estilo.value} | Tradición: {menu.tradicion.value}")
        print(f"\nEntrante: {menu.entrante.nombre}")
        print(f"  Ingredientes: {', '.join(menu.entrante.ingredientes)}")
        print(f"  Técnica: {menu.entrante.tecnica_coccion}")
        print(f"\nPrincipal: {menu.principal.nombre}")
        print(f"  Ingredientes: {', '.join(menu.principal.ingredientes)}")
        print(f"  Técnica: {menu.principal.tecnica_coccion}")
        print(f"\nPostre: {menu.postre.nombre}")
        print(f"  Ingredientes: {', '.join(menu.postre.ingredientes)}")
        print(f"  Técnica: {menu.postre.tecnica_coccion}")
        print(f"\nJustificación: {propuesta['explicacion']}")
        print(f"Puntuación: {propuesta['puntuacion']:.2f}")

# ==================== EJEMPLO DE USO ====================

if __name__ == "__main__":
    # Crear sistema
    sistema = SistemaCBR()
    
    # Mostrar estadísticas iniciales
    sistema.base_casos.obtener_estadisticas()
    
    # Caso de prueba: boda vegetariana en verano
    caso_test = Caso(
        id="TEST002",
        tipo_evento=TipoEvento.CONGRESO,
        num_comensales=300,
        presupuesto=10000.0,
        restricciones=["vegetariano", "sin_gluten"],
        preferencias=["fresco", "ligero"],
        temporada="verano",
        menu=None
    )
    
    # Resolver
    propuestas = sistema.resolver(caso_test, k=3)
    
    # Mostrar mejor propuesta
    mejor = max(propuestas, key=lambda p: p['puntuacion'])
    sistema.explicar_propuesta(mejor)
    
    # Mostrar estadísticas finales
    sistema.base_casos.obtener_estadisticas()
