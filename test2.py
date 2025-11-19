import json
import math
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from copy import deepcopy

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
    textura: str
    sabor_dominante: str
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
    fallos_detectados: List[str] = field(default_factory=list)
    reparaciones_aplicadas: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

# ==================== CONOCIMIENTO DEL DOMINIO ====================

class ConocimientoDominio:
    """Ontología y conocimiento causal del dominio gastronómico"""
    
    # Jerarquía de ingredientes
    JERARQUIA_INGREDIENTES = {
        "proteina": {
            "carne": ["ternera", "cordero", "cerdo", "pollo"],
            "pescado": ["merluza", "bacalao", "salmon", "dorada"],
            "marisco": ["gambas", "mejillones", "langosta"],
            "vegetariano": ["tofu", "tempeh", "setas", "legumbres"]
        },
        "vegetal": {
            "verde": ["espinacas", "brocoli", "guisantes"],
            "raiz": ["zanahoria", "nabo", "remolacha"],
            "tuberculo": ["patata", "boniato"]
        }
    }
    
    # Restricciones dietéticas incompatibles
    INCOMPATIBILIDADES = {
        "vegetariano": ["carne", "pescado", "marisco"],
        "vegano": ["carne", "pescado", "marisco", "huevo", "leche", "mantequilla", "queso"],
        "sin_gluten": ["harina", "pan", "pasta"],
        "halal": ["cerdo", "alcohol"],
        "kosher": ["cerdo", "marisco"]
    }
    
    # Reglas de balance sensorial
    BALANCE_TEXTURAS = {
        "crujiente": ["cremoso", "suave"],
        "cremoso": ["crujiente", "firme"],
        "firme": ["cremoso", "jugoso"],
        "suave": ["crujiente", "firme"],
        "jugoso": ["crujiente", "firme"],
        "liquido": ["crujiente", "firme"]
    }
    
    BALANCE_SABORES = {
        "dulce": ["acido", "salado"],
        "acido": ["dulce", "umami"],
        "salado": ["dulce", "acido"],
        "amargo": ["dulce", "umami"],
        "umami": ["acido", "dulce"]
    }
    
    # Ingredientes por temporada
    TEMPORADA = {
        "primavera": ["esparragos", "guisantes", "fresas", "alcachofas"],
        "verano": ["tomate", "pimiento", "melon", "sandia", "calabacin"],
        "otoño": ["setas", "calabaza", "uvas", "castañas"],
        "invierno": ["col", "puerro", "naranja", "mandarina"]
    }

    # Sustitutos para ingredientes problemáticos
    SUSTITUTOS = {
        "carne": ["tofu", "tempeh", "setas", "legumbres"],
        "pescado": ["tofu", "tempeh", "berenjena"],
        "marisco": ["setas", "berenjena"],
        "cerdo": ["ternera", "pollo", "cordero", "tofu"],
        "alcohol": ["caldo", "vinagre", "zumo"],
        "huevo": ["tofu", "aquafaba", "semillas de lino"],
        "leche": ["leche_almendra", "leche_soja", "leche_avena"],
        "queso": ["tofu_ahumado", "levadura_nutricional"],
        "mantequilla": ["aceite_oliva", "aguacate"],
        "harina": ["harina_almendra", "harina_coco", "harina_arroz"],
        "pan": ["pan_sin_gluten", "tortillas_maiz"],
        "pasta": ["pasta_arroz", "pasta_quinoa", "calabacín"]
    }

    @staticmethod
    def verificar_restriccion(ingrediente: str, restriccion: str) -> bool:
        """Verifica si un ingrediente viola una restricción"""
        if restriccion in ConocimientoDominio.INCOMPATIBILIDADES:
            return ingrediente not in ConocimientoDominio.INCOMPATIBILIDADES[restriccion]
        return True
    
    @staticmethod
    def ingrediente_temporada(ingrediente: str, temporada: str) -> bool:
        """Verifica si un ingrediente es de temporada"""
        return ingrediente in ConocimientoDominio.TEMPORADA.get(temporada, [])
    
    @staticmethod
    def obtener_sustituto(ingrediente: str, restriccion: str) -> Optional[str]:
        """Obtiene un sustituto adecuado para un ingrediente problemático"""
        if ingrediente in ConocimientoDominio.SUSTITUTOS:
            sustitutos = ConocimientoDominio.SUSTITUTOS[ingrediente]
            # Filtrar sustitutos que no violen la restricción
            for sustituto in sustitutos:
                if ConocimientoDominio.verificar_restriccion(sustituto, restriccion):
                    return sustituto
        return None

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
                    try:
                        caso = self._dict_a_caso(caso_dict)
                        self.casos.append(caso)
                    except (KeyError, TypeError, ValueError) as e:
                        print(f"⚠ Error cargando caso {caso_dict.get('id', 'desconocido')}: {e}")
                        continue
            print(f"✓ Cargados {len(self.casos)} casos desde {self.archivo_persistencia}")
        except FileNotFoundError:
            print(f"→ No se encontró {self.archivo_persistencia}, inicializando base por defecto")
            self._inicializar_casos_base()
            self._guardar_casos()
        except json.JSONDecodeError:
            print(f"→ Error leyendo {self.archivo_persistencia}, inicializando base por defecto")
            self._inicializar_casos_base()
            self._guardar_casos()
    
    def _dict_a_caso(self, caso_dict: dict) -> Caso:
        """Convierte diccionario a objeto Caso"""
        menu_dict = caso_dict['menu']
        
        # Convertir valores de enum si son strings
        estilo_value = menu_dict['estilo']
        if isinstance(estilo_value, str):
            estilo_value = EstiloCulinario(estilo_value)
            
        tradicion_value = menu_dict['tradicion']
        if isinstance(tradicion_value, str):
            tradicion_value = TradicionCultural(tradicion_value)
        
        # Crear platos con valores por defecto para campos faltantes
        def crear_plato(plato_dict: dict) -> Plato:
            # Proporcionar valores por defecto para campos requeridos
            defaults = {
                'textura': 'suave',
                'sabor_dominante': 'salado',
                'restricciones': [],
                'temporada': ['todo']
            }
            
            # Combinar dict original con defaults para campos faltantes
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
        """Persiste casos en archivo JSON"""
        with open(self.archivo_persistencia, 'w', encoding='utf-8') as f:
            casos_dict = [self._caso_a_dict(caso) for caso in self.casos]
            json.dump(casos_dict, f, indent=2, ensure_ascii=False)
    
    def _caso_a_dict(self, caso: Caso) -> dict:
        """Convierte Caso a diccionario serializable"""
        caso_dict = caso.to_dict()
        caso_dict['tipo_evento'] = caso.tipo_evento.value
        caso_dict['menu']['estilo'] = caso.menu.estilo.value
        caso_dict['menu']['tradicion'] = caso.menu.tradicion.value
        return caso_dict
    
    def _inicializar_casos_base(self):
        """Casos iniciales del sistema"""
        
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
                              "crudo", ["verano"], "suave", "acido", ["vegetariano"]),
                principal=Plato("Risotto de setas", ["arroz", "setas", "parmesano"], 
                               "cocido", ["otoño", "primavera"], "cremoso", "umami", ["vegetariano"]),
                postre=Plato("Tiramisú", ["mascarpone", "cafe", "cacao"], 
                            "montado", ["todo"], "cremoso", "dulce", ["vegetariano"]),
                estilo=EstiloCulinario.MEDITERRANEO,
                tradicion=TradicionCultural.ITALIANA
            ),
            exito=0.95
        )
        
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
                              "horneado", ["verano", "otoño"], "firme", "salado", []),
                principal=Plato("Merluza a la vasca", ["merluza", "guisantes", "huevo"],
                               "guisado", ["todo"], "jugoso", "umami", []),
                postre=Plato("Cuajada con miel", ["leche", "cuajo", "miel"],
                            "cuajado", ["todo"], "cremoso", "dulce", ["vegetariano"]),
                estilo=EstiloCulinario.CLASICO,
                tradicion=TradicionCultural.VASCA
            ),
            exito=0.90
        )
        
        caso3 = Caso(
            id="C003",
            tipo_evento=TipoEvento.BANQUETE,
            num_comensales=30,
            presupuesto=6000.0,
            restricciones=[],
            preferencias=["innovador", "sorprendente"],
            temporada="primavera",
            menu=Menu(
                entrante=Plato("Esferificacion de gazpacho", ["tomate", "alginato", "pepino"],
                              "esferificado", ["verano"], "liquido", "acido", ["vegetariano", "vegano"]),
                principal=Plato("Foie deconstruido", ["foie", "manzana", "brioche"],
                               "deconstruido", ["todo"], "cremoso", "umami", []),
                postre=Plato("Nitrogeno de chocolate", ["chocolate", "nitrogeno", "frambuesa"],
                            "congelado_flash", ["todo"], "crujiente", "dulce", ["vegetariano"]),
                estilo=EstiloCulinario.MOLECULAR,
                tradicion=TradicionCultural.CATALANA
            ),
            exito=0.88
        )
        
        self.casos = [caso1, caso2, caso3]
    
    def agregar_caso(self, caso: Caso):
        self.casos.append(caso)
        self._guardar_casos()
    
    def obtener_todos(self) -> List[Caso]:
        return self.casos

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
        diferencia = abs(val1 - val2)
        return max(0, 1 - (diferencia / rango_max))
    
    def _similitud_conjuntos(self, set1: List[str], set2: List[str]) -> float:
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
        """RETRIEVER: Recupera los k casos más similares"""
        
        print("\n" + "="*70)
        print("RETRIEVER: Buscando menús similares...")
        print(f"  Criterios: {caso_nuevo.tipo_evento.value}, {caso_nuevo.num_comensales} comensales")
        print(f"  Restricciones: {caso_nuevo.restricciones}")
        print(f"  Preferencias: {caso_nuevo.preferencias}")
        print("="*70)
        
        similitudes = []
        for caso_base in self.base_casos.obtener_todos():
            sim = self.calculador.similitud_casos(caso_nuevo, caso_base)
            similitudes.append((caso_base, sim))
        
        similitudes.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\nEncontrados {len(similitudes)} casos. Seleccionando top {k}:")
        for i, (caso, sim) in enumerate(similitudes[:k], 1):
            print(f"  {i}. {caso.id}: {caso.menu.estilo.value}-{caso.menu.tradicion.value} (similitud: {sim:.3f})")
        
        return similitudes[:k]

# ==================== SIMULADOR ====================

class Simulador:
    """Simula la ejecución del menú y detecta fallos potenciales"""
    
    def __init__(self):
        self.conocimiento = ConocimientoDominio()
    
    def simular_menu(self, menu: Menu, caso: Caso) -> Tuple[bool, List[str]]:
        """Simula el menú y detecta fallos"""
        
        print("\n" + "-"*70)
        print("SIMULATOR: Ejecutando menú propuesto...")
        print("-"*70)
        
        fallos = []
        
        # Verificar restricciones dietéticas
        fallos.extend(self._verificar_restricciones(menu, caso.restricciones))
        
        # Verificar balance sensorial
        fallos.extend(self._verificar_balance(menu))
        
        # Verificar temporada
        fallos.extend(self._verificar_temporada(menu, caso.temporada))
        
        # Verificar coherencia cultural
        fallos.extend(self._verificar_coherencia_cultural(menu))
        
        exito = len(fallos) == 0
        
        if exito:
            print("✓ Menú válido: todos los objetivos cumplidos")
            self._mostrar_resultados_positivos(menu)
        else:
            print(f"✗ Se detectaron {len(fallos)} problemas:")
            for i, fallo in enumerate(fallos, 1):
                print(f"  {i}. {fallo}")
        
        return exito, fallos
    
    def _verificar_restricciones(self, menu: Menu, restricciones: List[str]) -> List[str]:
        """Verifica cumplimiento de restricciones dietéticas"""
        fallos = []
        platos = [
            ("entrante", menu.entrante),
            ("principal", menu.principal),
            ("postre", menu.postre)
        ]
        
        for nombre_plato, plato in platos:
            for restriccion in restricciones:
                for ingrediente in plato.ingredientes:
                    if not self.conocimiento.verificar_restriccion(ingrediente, restriccion):
                        fallos.append(
                            f"RESTRICCION-VIOLADA: {ingrediente} en {nombre_plato} "
                            f"viola restricción '{restriccion}'"
                        )
        
        return fallos
    
    def _verificar_balance(self, menu: Menu) -> List[str]:
        """Verifica balance sensorial del menú"""
        fallos = []
        
        # Balance de texturas
        texturas = [menu.entrante.textura, menu.principal.textura, menu.postre.textura]
        if texturas[0] == texturas[1] == texturas[2]:
            fallos.append(
                f"DESBALANCE-TEXTURA: todas las texturas son '{texturas[0]}'. "
                f"Se recomienda variedad"
            )
        
        # Balance de sabores
        sabores = [menu.entrante.sabor_dominante, menu.principal.sabor_dominante, 
                   menu.postre.sabor_dominante]
        if sabores.count(sabores[0]) == 3:
            fallos.append(
                f"DESBALANCE-SABOR: todos los platos tienen sabor dominante '{sabores[0]}'"
            )
        
        return fallos
    
    def _verificar_temporada(self, menu: Menu, temporada: str) -> List[str]:
        """Verifica uso de ingredientes de temporada"""
        fallos = []
        platos = [menu.entrante, menu.principal, menu.postre]
        
        for plato in platos:
            if temporada not in plato.temporada and "todo" not in plato.temporada:
                fallos.append(
                    f"FUERA-TEMPORADA: {plato.nombre} no es de temporada '{temporada}'"
                )
        
        return fallos
    
    def _verificar_coherencia_cultural(self, menu: Menu) -> List[str]:
        """Verifica coherencia entre estilo y tradición"""
        fallos = []
        
        # Verificar que estilo molecular no esté con tradiciones muy tradicionales
        if menu.estilo == EstiloCulinario.MOLECULAR:
            if menu.tradicion in [TradicionCultural.RUSA, TradicionCultural.ETIOPE]:
                fallos.append(
                    f"INCOHERENCIA-ESTILO: estilo '{menu.estilo.value}' poco común "
                    f"con tradición '{menu.tradicion.value}'"
                )
        
        return fallos
    
    def _mostrar_resultados_positivos(self, menu: Menu):
        """Muestra aspectos positivos del menú simulado"""
        print("\nResultados de la simulación:")
        print(f"  • Texturas: {menu.entrante.textura} → {menu.principal.textura} → {menu.postre.textura}")
        print(f"  • Sabores: {menu.entrante.sabor_dominante} → {menu.principal.sabor_dominante} → {menu.postre.sabor_dominante}")
        print(f"  • Coherencia: {menu.estilo.value} + {menu.tradicion.value} ✓")

# ==================== REPARADOR MEJORADO ====================

class Reparador:
    """Repara menús con fallos detectados"""
    
    def __init__(self, base_casos: BaseCasos):
        self.base_casos = base_casos
        self.conocimiento = ConocimientoDominio()
    
    def reparar_menu(self, menu: Menu, fallos: List[str], caso: Caso) -> Tuple[Menu, List[str]]:
        """REPAIRER: Intenta reparar el menú con fallos"""
        
        print("\n" + "-"*70)
        print("REPAIRER: Analizando fallos y aplicando estrategias de reparación...")
        print("-"*70)
        
        menu_reparado = deepcopy(menu)
        reparaciones = []
        
        # Procesar cada fallo individualmente
        for fallo in fallos:
            if "RESTRICCION-VIOLADA" in fallo:
                # Extraer información del fallo
                partes = fallo.split(": ")
                detalle = partes[1].split(" en ")
                ingrediente_problema = detalle[0]
                plato_problema = detalle[1].split(" ")[0]
                restriccion = partes[2].split("'")[1]
                
                # Reparar este fallo específico
                menu_reparado, rep = self._reparar_ingrediente_problematico(
                    menu_reparado, plato_problema, ingrediente_problema, restriccion
                )
                if rep:
                    reparaciones.append(rep)
            
            elif "DESBALANCE-TEXTURA" in fallo:
                menu_reparado, rep = self._reparar_balance_texturas(menu_reparado)
                if rep:
                    reparaciones.append(rep)
            
            elif "DESBALANCE-SABOR" in fallo:
                menu_reparado, rep = self._reparar_balance_sabores(menu_reparado)
                if rep:
                    reparaciones.append(rep)
            
            elif "FUERA-TEMPORADA" in fallo:
                partes = fallo.split(": ")
                plato_nombre = partes[1].split(" no es")[0]
                menu_reparado, rep = self._reparar_temporada_plato(menu_reparado, plato_nombre, caso.temporada)
                if rep:
                    reparaciones.append(rep)
        
        if reparaciones:
            print(f"\n✓ Se aplicaron {len(reparaciones)} reparaciones:")
            for i, rep in enumerate(reparaciones, 1):
                print(f"  {i}. {rep}")
        else:
            print("\n⚠ No se pudieron aplicar reparaciones automáticas")
        
        return menu_reparado, reparaciones
    
    def _reparar_ingrediente_problematico(self, menu: Menu, plato_nombre: str, ingrediente: str, restriccion: str) -> Tuple[Menu, str]:
        """Reemplaza un ingrediente problemático con un sustituto"""
        sustituto = self.conocimiento.obtener_sustituto(ingrediente, restriccion)
        
        if sustituto:
            # Encontrar y modificar el plato correcto
            if "entrante" in plato_nombre.lower() or menu.entrante.nombre in plato_nombre:
                nuevos_ingredientes = [
                    sustituto if ing == ingrediente else ing 
                    for ing in menu.entrante.ingredientes
                ]
                menu.entrante.ingredientes = nuevos_ingredientes
                menu.entrante.nombre = menu.entrante.nombre.replace(ingrediente, sustituto)
                return menu, f"SUSTITUIR-INGREDIENTE: {ingrediente} → {sustituto} en entrante"
            
            elif "principal" in plato_nombre.lower() or menu.principal.nombre in plato_nombre:
                nuevos_ingredientes = [
                    sustituto if ing == ingrediente else ing 
                    for ing in menu.principal.ingredientes
                ]
                menu.principal.ingredientes = nuevos_ingredientes
                menu.principal.nombre = menu.principal.nombre.replace(ingrediente, sustituto)
                return menu, f"SUSTITUIR-INGREDIENTE: {ingrediente} → {sustituto} en principal"
            
            elif "postre" in plato_nombre.lower() or menu.postre.nombre in plato_nombre:
                nuevos_ingredientes = [
                    sustituto if ing == ingrediente else ing 
                    for ing in menu.postre.ingredientes
                ]
                menu.postre.ingredientes = nuevos_ingredientes
                menu.postre.nombre = menu.postre.nombre.replace(ingrediente, sustituto)
                return menu, f"SUSTITUIR-INGREDIENTE: {ingrediente} → {sustituto} en postre"
        
        return menu, ""
    
    def _reparar_balance_texturas(self, menu: Menu) -> Tuple[Menu, str]:
        """Ajusta las texturas para mejorar el balance"""
        texturas = [menu.entrante.textura, menu.principal.textura, menu.postre.textura]
        
        # Encontrar texturas complementarias
        for i, textura in enumerate(texturas):
            complementarias = self.conocimiento.BALANCE_TEXTURAS.get(textura, [])
            if complementarias:
                # Cambiar la textura del plato principal si es posible
                nueva_textura = complementarias[0]
                menu.principal.textura = nueva_textura
                return menu, f"AJUSTAR-TEXTURA: principal ahora tiene textura {nueva_textura}"
        
        return menu, ""
    
    def _reparar_balance_sabores(self, menu: Menu) -> Tuple[Menu, str]:
        """Ajusta los sabores para mejorar el balance"""
        sabores = [menu.entrante.sabor_dominante, menu.principal.sabor_dominante, menu.postre.sabor_dominante]
        
        # Encontrar sabores complementarios
        for i, sabor in enumerate(sabores):
            complementarios = self.conocimiento.BALANCE_SABORES.get(sabor, [])
            if complementarios:
                # Cambiar el sabor del plato principal si es posible
                nuevo_sabor = complementarios[0]
                menu.principal.sabor_dominante = nuevo_sabor
                return menu, f"AJUSTAR-SABOR: principal ahora tiene sabor {nuevo_sabor}"
        
        return menu, ""
    
    def _reparar_temporada_plato(self, menu: Menu, plato_nombre: str, temporada: str) -> Tuple[Menu, str]:
        """Adapta un plato para usar ingredientes de temporada"""
        ingredientes_temporada = self.conocimiento.TEMPORADA.get(temporada, [])
        
        if ingredientes_temporada:
            # Encontrar el plato y añadir ingredientes de temporada
            if menu.entrante.nombre == plato_nombre:
                nuevo_ingrediente = ingredientes_temporada[0]
                menu.entrante.ingredientes.append(nuevo_ingrediente)
                menu.entrante.temporada = [temporada]
                return menu, f"ADAPTAR-TEMPORADA: añadido {nuevo_ingrediente} a entrante"
            
            elif menu.principal.nombre == plato_nombre:
                nuevo_ingrediente = ingredientes_temporada[0]
                menu.principal.ingredientes.append(nuevo_ingrediente)
                menu.principal.temporada = [temporada]
                return menu, f"ADAPTAR-TEMPORADA: añadido {nuevo_ingrediente} a principal"
            
            elif menu.postre.nombre == plato_nombre:
                nuevo_ingrediente = ingredientes_temporada[0]
                menu.postre.ingredientes.append(nuevo_ingrediente)
                menu.postre.temporada = [temporada]
                return menu, f"ADAPTAR-TEMPORADA: añadido {nuevo_ingrediente} a postre"
        
        return menu, ""

# ==================== SISTEMA CBR ====================

class SistemaCBR:
    def __init__(self):
        self.base_casos = BaseCasos()
        self.calculador = CalculadorSimilitud()
        self.recuperacion = ModuloRecuperacion(self.base_casos, self.calculador)
        self.simulador = Simulador()
        self.reparador = Reparador(self.base_casos)
    
    def resolver(self, caso_nuevo: Caso) -> List[Dict[str, Any]]:
        """Ciclo CBR completo con simulación y reparación"""
        
        print("\n" + "="*70)
        print(f"ANTICIPATOR: Procesando solicitud {caso_nuevo.id}")
        print(f"  Evento: {caso_nuevo.tipo_evento.value}, {caso_nuevo.num_comensales} comensales")
        print(f"  Presupuesto: {caso_nuevo.presupuesto}€, Temporada: {caso_nuevo.temporada}")
        print("="*70)
        
        # RETRIEVE: Recuperar casos similares
        casos_similares = self.recuperacion.recuperar(caso_nuevo, k=3)
        
        propuestas_finales = []
        
        for i, (caso_recuperado, similitud) in enumerate(casos_similares, 1):
            print(f"\n{'='*70}")
            print(f"MODIFICADOR: Procesando candidato {i}/{len(casos_similares)}")
            print(f"  Caso base: {caso_recuperado.id}")
            print(f"  Menú: {caso_recuperado.menu.entrante.nombre} + "
                  f"{caso_recuperado.menu.principal.nombre} + {caso_recuperado.menu.postre.nombre}")
            print("="*70)
            
            # REUSE: Adaptar menú
            menu_adaptado = deepcopy(caso_recuperado.menu)
            
            # REVISE: Simular menú
            exito, fallos = self.simulador.simular_menu(menu_adaptado, caso_nuevo)
            
            if not exito:
                # REPAIR: Reparar menú
                menu_reparado, reparaciones = self.reparador.reparar_menu(
                    menu_adaptado, fallos, caso_nuevo
                )
                
                # Re-simular después de reparación
                print(f"\nRE-SIMULACIÓN después de reparaciones:")
                exito_rep, fallos_rep = self.simulador.simular_menu(menu_reparado, caso_nuevo)
                
                propuesta = {
                    'caso_origen': caso_recuperado.id,
                    'similitud': similitud,
                    'menu': menu_reparado,
                    'valido': exito_rep,
                    'fallos': fallos_rep,
                    'reparaciones': reparaciones,
                    'puntuacion': 0.9 if exito_rep else 0.6
                }
            else:
                propuesta = {
                    'caso_origen': caso_recuperado.id,
                    'similitud': similitud,
                    'menu': menu_adaptado,
                    'valido': True,
                    'fallos': [],
                    'reparaciones': [],
                    'puntuacion': 1.0
                }
            
            propuestas_finales.append(propuesta)
        
        # RETAIN: Almacenar el mejor caso exitoso
        self._retener_mejor_caso(caso_nuevo, propuestas_finales)
        
        return propuestas_finales
    
    
    def _retener_mejor_caso(self, caso_nuevo: Caso, propuestas: List[Dict]):
        """RETAIN: Almacena el mejor caso exitoso en la base"""
        
        # Encontrar la mejor propuesta válida
        propuestas_validas = [p for p in propuestas if p['valido']]
        
        if propuestas_validas:
            mejor = max(propuestas_validas, key=lambda x: x['puntuacion'])
            
            print("\n" + "="*70)
            print("RETAIN: Almacenando experiencia en la base de casos")
            print("="*70)
            
            # Crear nuevo caso con el menú exitoso
            nuevo_caso = Caso(
                id=f"C{len(self.base_casos.obtener_todos()) + 1:03d}",
                tipo_evento=caso_nuevo.tipo_evento,
                num_comensales=caso_nuevo.num_comensales,
                presupuesto=caso_nuevo.presupuesto,
                restricciones=caso_nuevo.restricciones,
                preferencias=caso_nuevo.preferencias,
                temporada=caso_nuevo.temporada,
                menu=mejor['menu'],
                exito=mejor['puntuacion'],
                fallos_detectados=mejor['fallos'],
                reparaciones_aplicadas=mejor['reparaciones']
            )
            
            self.base_casos.agregar_caso(nuevo_caso)
            
            print(f"✓ Caso {nuevo_caso.id} añadido a la base")
            print(f"  Menú: {nuevo_caso.menu.entrante.nombre}")
            print(f"        {nuevo_caso.menu.principal.nombre}")
            print(f"        {nuevo_caso.menu.postre.nombre}")
            print(f"  Puntuación: {nuevo_caso.exito:.2f}")
        else:
            print("\n⚠ No hay propuestas válidas para retener")
    
    def mostrar_propuestas(self, propuestas: List[Dict]):
        """Muestra las propuestas finales de forma clara"""
        
        print("\n" + "="*70)
        print("PROPUESTAS FINALES")
        print("="*70)
        
        for i, prop in enumerate(propuestas, 1):
            print(f"\n--- PROPUESTA {i} ---")
            print(f"Origen: {prop['caso_origen']} (similitud: {prop['similitud']:.3f})")
            print(f"Estado: {'✓ VÁLIDO' if prop['valido'] else '✗ CON PROBLEMAS'}")
            print(f"Puntuación: {prop['puntuacion']:.2f}")
            
            menu = prop['menu']
            print(f"\nMenú {menu.estilo.value} - {menu.tradicion.value}:")
            print(f"  Entrante:  {menu.entrante.nombre}")
            print(f"    Ingredientes: {', '.join(menu.entrante.ingredientes)}")
            print(f"    Textura: {menu.entrante.textura}, Sabor: {menu.entrante.sabor_dominante}")
            print(f"  Principal: {menu.principal.nombre}")
            print(f"    Ingredientes: {', '.join(menu.principal.ingredientes)}")
            print(f"    Textura: {menu.principal.textura}, Sabor: {menu.principal.sabor_dominante}")
            print(f"  Postre:    {menu.postre.nombre}")
            print(f"    Ingredientes: {', '.join(menu.postre.ingredientes)}")
            print(f"    Textura: {menu.postre.textura}, Sabor: {menu.postre.sabor_dominante}")
            
            if prop['reparaciones']:
                print(f"\nReparaciones aplicadas:")
                for rep in prop['reparaciones']:
                    print(f"  • {rep}")
            
            if not prop['valido'] and prop['fallos']:
                print(f"\n⚠ Problemas pendientes:")
                for fallo in prop['fallos']:
                    print(f"  • {fallo}")
        
        # Recomendar la mejor
        if propuestas:
            mejor = max(propuestas, key=lambda x: x['puntuacion'])
            print(f"\n{'='*70}")
            print(f"RECOMENDACIÓN: Propuesta {propuestas.index(mejor) + 1} (puntuación: {mejor['puntuacion']:.2f})")
            print("="*70)

# ==================== PROGRAMA PRINCIPAL ====================

def main():
    """Programa principal con ejemplos de uso"""
    
    print("\n" + "="*70)
    print("SISTEMA CBR DE PLANIFICACIÓN DE MENÚS")
    print("Inspirado en CHEF (Hammond, 1986)")
    print("="*70)
    
    sistema = SistemaCBR()
    
    # ============ EJEMPLO 1: Boda vegetariana en verano ============
    print("\n\n" + "#"*70)
    print("# EJEMPLO 1: Boda vegetariana en verano")
    print("#"*70)
    
    caso_test1 = Caso(
        id="TEST001",
        tipo_evento=TipoEvento.BODA,
        num_comensales=120,
        presupuesto=6000.0,
        restricciones=["vegetariano"],
        preferencias=["elegante", "fresco"],
        temporada="verano",
        menu=Menu(  # Este menú será ignorado, solo estructura
            entrante=Plato("", [], "", [], "", "", []),
            principal=Plato("", [], "", [], "", "", []),
            postre=Plato("", [], "", [], "", "", []),
            estilo=EstiloCulinario.MEDITERRANEO,
            tradicion=TradicionCultural.ITALIANA
        )
    )
    
    propuestas1 = sistema.resolver(caso_test1)
    sistema.mostrar_propuestas(propuestas1)
    
    # ============ EJEMPLO 2: Congreso con restricciones halal ============
    print("\n\n" + "#"*70)
    print("# EJEMPLO 2: Congreso con restricciones halal")
    print("#"*70)
    
    caso_test2 = Caso(
        id="TEST002",
        tipo_evento=TipoEvento.CONGRESO,
        num_comensales=80,
        presupuesto=3000.0,
        restricciones=["halal"],
        preferencias=["tradicional", "sustancioso"],
        temporada="otoño",
        menu=Menu(
            entrante=Plato("", [], "", [], "", "", []),
            principal=Plato("", [], "", [], "", "", []),
            postre=Plato("", [], "", [], "", "", []),
            estilo=EstiloCulinario.CLASICO,
            tradicion=TradicionCultural.MARROQUI
        )
    )
    
    propuestas2 = sistema.resolver(caso_test2)
    sistema.mostrar_propuestas(propuestas2)
    
    # ============ EJEMPLO 3: Banquete innovador ============
    print("\n\n" + "#"*70)
    print("# EJEMPLO 3: Banquete de alta cocina molecular")
    print("#"*70)
    
    caso_test3 = Caso(
        id="TEST003",
        tipo_evento=TipoEvento.BANQUETE,
        num_comensales=40,
        presupuesto=8000.0,
        restricciones=[],
        preferencias=["vanguardista", "sorprendente", "espectacular"],
        temporada="primavera",
        menu=Menu(
            entrante=Plato("", [], "", [], "", "", []),
            principal=Plato("", [], "", [], "", "", []),
            postre=Plato("", [], "", [], "", "", []),
            estilo=EstiloCulinario.MOLECULAR,
            tradicion=TradicionCultural.CATALANA
        )
    )
    
    propuestas3 = sistema.resolver(caso_test3)
    sistema.mostrar_propuestas(propuestas3)
    
    # ============ ESTADÍSTICAS FINALES ============
    print("\n\n" + "="*70)
    print("ESTADÍSTICAS DEL SISTEMA")
    print("="*70)
    
    casos_totales = len(sistema.base_casos.obtener_todos())
    if casos_totales > 0:
        casos_exitosos = len([c for c in sistema.base_casos.obtener_todos() if c.exito >= 0.9])
        
        print(f"Total de casos en la base: {casos_totales}")
        print(f"Casos exitosos (≥90%): {casos_exitosos}")
        print(f"Tasa de éxito: {casos_exitosos/casos_totales*100:.1f}%")
        
        print("\nDistribución por tipo de evento:")
        tipos = {}
        for caso in sistema.base_casos.obtener_todos():
            tipo = caso.tipo_evento.value
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        for tipo, count in tipos.items():
            print(f"  {tipo.capitalize()}: {count}")
    else:
        print("No hay casos en la base de datos")
    
    print("\n" + "="*70)
    print("Sistema CBR finalizado")
    print("="*70)

if __name__ == "__main__":
    main()