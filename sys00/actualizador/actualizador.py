"""
Módulo de Actualización de Bases de Conocimiento
===============================================

Este módulo gestiona la actualización automática de las bases de conocimiento
del sistema CBR cuando se generan nuevos menús exitosos o se detectan nuevos
ingredientes, platos o patrones de reparación.
"""

import json
import os
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import shutil


@dataclass
class NuevoMenu:
    """Representa un nuevo menú generado por el sistema."""
    entrante: str
    principal: str 
    postre: str
    tipo_evento: str
    temporada: str
    restricciones: List[str]
    estilo: str
    tradicion: str
    exito: bool = True
    feedback: Optional[str] = None
    reparaciones_aplicadas: List[Dict[str, Any]] = None  # Info de reparaciones para crear platos correctamente


@dataclass
class NuevoIngrediente:
    """Representa un nuevo ingrediente a agregar a la base."""
    nombre: str
    temporada: List[str]
    categoria: str
    sabor: str
    tradicion: List[str]


@dataclass
class NuevoPlato:
    """Representa un nuevo plato a agregar a la base."""
    nombre: str
    ingredientes: List[str]
    tecnica_coccion: List[str]
    sabor_dominante: str
    ingrediente_sabor: str
    tradicion: str
    temporada: List[str]


@dataclass
class RegistroActualizacion:
    """Registro de una actualización realizada."""
    timestamp: str
    tipo: str  # 'ingrediente', 'plato', 'caso', 'reparacion'
    item_id: str
    accion: str  # 'agregado', 'actualizado', 'modificado'
    detalles: Dict[str, Any]


class ActualizadorConocimiento:
    """
    Gestiona las actualizaciones automáticas de las bases de conocimiento.
    
    Responsabilidades:
    - Detectar nuevos ingredientes en menús
    - Agregar nuevos platos a la base
    - Crear nuevos casos exitosos 
    - Actualizar reglas de reparación
    - Mantener consistencia entre bases
    """
    
    def __init__(self, directorio_conocimiento: str = None):
        """
        Inicializa el actualizador.
        
        Args:
            directorio_conocimiento: Ruta al directorio de conocimiento
        """
        if directorio_conocimiento is None:
            directorio_conocimiento = os.path.join(os.path.dirname(__file__), '..', 'conocimiento')
        
        self.dir_conocimiento = directorio_conocimiento
        self.historial_actualizaciones = []
        
        # Cargar bases de conocimiento actuales
        self._cargar_bases_conocimiento()
    
    def _cargar_bases_conocimiento(self):
        """Carga todas las bases de conocimiento en memoria."""
        try:
            # Cargar ingredientes
            with open(os.path.join(self.dir_conocimiento, 'ingredientes.json'), 'r', encoding='utf-8') as f:
                self.ingredientes = json.load(f)
            
            # Cargar platos  
            with open(os.path.join(self.dir_conocimiento, 'platos.json'), 'r', encoding='utf-8') as f:
                self.platos = json.load(f)
            
            # Cargar casos
            with open(os.path.join(self.dir_conocimiento, 'casos.json'), 'r', encoding='utf-8') as f:
                self.casos = json.load(f)
            
            # Cargar reparaciones
            with open(os.path.join(self.dir_conocimiento, 'reparaciones.json'), 'r', encoding='utf-8') as f:
                self.reparaciones = json.load(f)
            
            # Crear índices para búsqueda rápida
            self.ingredientes_set = {ing['nombre'] for ing in self.ingredientes}
            self.platos_set = {plato['nombre'] for plato in self.platos}
            self.casos_dict = {caso['id']: caso for caso in self.casos}
            
        except Exception as e:
            # Inicializar estructuras vacías si hay error
            self.ingredientes = []
            self.platos = []
            self.casos = []
            self.reparaciones = {}
            self.ingredientes_set = set()
            self.platos_set = set()
            self.casos_dict = {}
    
    def procesar_nuevo_menu(self, menu: NuevoMenu, crear_backup: bool = False) -> Dict[str, List[str]]:
        """
        Procesa un nuevo menú y actualiza las bases de conocimiento necesarias.
        
        Args:
            menu: El nuevo menú a procesar
            crear_backup: Si crear backup antes de actualizar (default: False)
            
        Returns:
            Diccionario con las actualizaciones realizadas
        """
        if crear_backup:
            self._crear_backup()
        
        actualizaciones = {
            'ingredientes_nuevos': [],
            'platos_nuevos': [],
            'casos_agregados': [],
            'reparaciones_actualizadas': []
        }
        
        try:
            # 1. Detectar y agregar ingredientes nuevos
            ingredientes_nuevos = self._detectar_ingredientes_nuevos(menu)
            if ingredientes_nuevos:
                actualizaciones['ingredientes_nuevos'] = self._agregar_ingredientes(ingredientes_nuevos)
            
            # 2. Detectar y agregar platos nuevos
            platos_nuevos = self._detectar_platos_nuevos(menu)
            if platos_nuevos:
                actualizaciones['platos_nuevos'] = self._agregar_platos(platos_nuevos, menu)
            
            # 3. Crear nuevo caso
            nuevo_caso_id = self._generar_id_caso()
            caso_agregado = self._agregar_caso(menu, nuevo_caso_id)
            actualizaciones['casos_agregados'] = [caso_agregado]
            
            # 4. Actualizar reglas de reparación si es necesario
            if menu.exito:
                reparaciones_actualizadas = self._actualizar_reglas_reparacion(menu)
                actualizaciones['reparaciones_actualizadas'] = reparaciones_actualizadas
            
            # 5. Guardar todas las bases actualizadas
            self._guardar_bases_conocimiento()
            
            # 6. Registrar actualizaciones
            self._registrar_actualizaciones(actualizaciones, menu)
            
            print(f"\nPROCESAMIENTO COMPLETADO")
            self._imprimir_resumen_actualizaciones(actualizaciones)
            
            return actualizaciones
            
        except Exception as e:
            print(f"Error durante el procesamiento: {e}")
            if crear_backup:
                print("Restaurando desde backup...")
                self._restaurar_backup()
            raise
    
    def _detectar_ingredientes_nuevos(self, menu: NuevoMenu) -> List[str]:
        """Detecta ingredientes en el menú que no existen en la base."""
        print(f"\nDETECTANDO INGREDIENTES NUEVOS")
        
        # Extraer ingredientes de cada plato del menú
        ingredientes_menu = []
        for plato_nombre in [menu.entrante, menu.principal, menu.postre]:
            if plato_nombre in self.platos_set:
                # Buscar plato en la base
                plato_info = next((p for p in self.platos if p['nombre'] == plato_nombre), None)
                if plato_info:
                    ingredientes_menu.extend(plato_info['ingredientes'])
        
        # Detectar ingredientes nuevos
        ingredientes_nuevos = []
        for ingrediente in set(ingredientes_menu):
            if ingrediente not in self.ingredientes_set:
                ingredientes_nuevos.append(ingrediente)
        
        if ingredientes_nuevos:
            print(f"Ingredientes nuevos detectados: {ingredientes_nuevos}")
        else:
            print(f"Todos los ingredientes ya existen en la base")
        
        return ingredientes_nuevos
    
    def _detectar_platos_nuevos(self, menu: NuevoMenu) -> List[str]:
        """Detecta platos en el menú que no existen en la base."""
        print(f"\nDETECTANDO PLATOS NUEVOS")
        
        platos_menu = [menu.entrante, menu.principal, menu.postre]
        platos_nuevos = []
        
        for plato in platos_menu:
            if plato not in self.platos_set:
                platos_nuevos.append(plato)
        
        if platos_nuevos:
            print(f"Platos nuevos detectados: {platos_nuevos}")
        else:
            print(f"Todos los platos ya existen en la base")
        
        return platos_nuevos
    
    def _agregar_ingredientes(self, ingredientes_nuevos: List[str]) -> List[str]:
        """Agrega nuevos ingredientes a la base con información inferida."""
        print(f"\nAGREGANDO INGREDIENTES NUEVOS")
        
        agregados = []
        
        for ingrediente_nombre in ingredientes_nuevos:
            # Generar información básica del ingrediente
            nuevo_ingrediente = self._generar_info_ingrediente(ingrediente_nombre)
            
            if nuevo_ingrediente:
                self.ingredientes.append(nuevo_ingrediente)
                self.ingredientes_set.add(ingrediente_nombre)
                agregados.append(ingrediente_nombre)
                
                print(f"Agregado: {ingrediente_nombre}")
                print(f"  - Categoria: {nuevo_ingrediente['categoria']}")
                print(f"  - Temporada: {nuevo_ingrediente['temporada']}")
                print(f"  - Sabor: {nuevo_ingrediente['sabor']}")
        
        return agregados
    
    def _generar_info_ingrediente(self, nombre: str) -> Optional[Dict[str, Any]]:
        """
        Genera información básica para un nuevo ingrediente.
        
        Usa patrones y heurísticas para inferir categoría, temporada, etc.
        """
        # Patrones para categorizar ingredientes
        categorias_comunes = {
            'vegetal': ['tomate', 'cebolla', 'ajo', 'pimiento', 'pepino', 'lechuga', 'espinaca', 'brócoli'],
            'fruta': ['manzana', 'naranja', 'limón', 'fresa', 'plátano', 'uva', 'melón', 'sandía'],
            'animal': ['pollo', 'ternera', 'cerdo', 'pescado', 'atún', 'salmón', 'huevo'],
            'lacteo': ['leche', 'queso', 'yogur', 'mantequilla', 'nata', 'mozzarella'],
            'cereal': ['arroz', 'trigo', 'avena', 'quinoa', 'pasta', 'pan'],
            'condimento': ['sal', 'pimienta', 'azúcar', 'aceite', 'vinagre'],
            'hongo': ['setas', 'champiñón', 'shiitake'],
            'leguminosa': ['lentejas', 'garbanzos', 'judías', 'guisantes']
        }
        
        sabores_comunes = {
            'salado': ['sal', 'queso', 'jamón', 'anchoa'],
            'dulce': ['azúcar', 'miel', 'fruta', 'chocolate'],
            'ácido': ['limón', 'vinagre', 'tomate'],
            'amargo': ['café', 'cacao', 'rúcula'],
            'umami': ['setas', 'queso', 'tomate']
        }
        
        # Inferir categoría
        categoria = 'vegetal'  # por defecto
        for cat, palabras in categorias_comunes.items():
            if any(palabra in nombre.lower() for palabra in palabras):
                categoria = cat
                break
        
        # Inferir sabor
        sabor = 'salado'  # por defecto
        for sab, palabras in sabores_comunes.items():
            if any(palabra in nombre.lower() for palabra in palabras):
                sabor = sab
                break
        
        # Temporadas por defecto (se puede refinar)
        temporada = ['primavera', 'verano', 'otoño', 'invierno']  # disponible todo el año por defecto
        
        return {
            'nombre': nombre,
            'categoria': categoria,
            'temporada': temporada,
            'sabor': sabor,
            'tradicion': ['general']  # se puede especializar más tarde
        }
    
    def _agregar_platos(self, platos_nuevos: List[str], menu: NuevoMenu = None) -> List[str]:
        """
        Agrega nuevos platos a la base.
        
        Si hay información de reparaciones, crea el plato copiando del plato base
        y aplicando las modificaciones. Si no, crea un plato básico.
        """
        print(f"\nAGREGANDO PLATOS NUEVOS")
        
        agregados = []
        
        for plato_nombre in platos_nuevos:
            # Buscar si este plato tiene reparaciones aplicadas
            reparacion_info = None
            if menu and menu.reparaciones_aplicadas:
                for rep in menu.reparaciones_aplicadas:
                    if rep.get('accion') == 'modificacion' and rep.get('plato_modificado') == plato_nombre:
                        reparacion_info = rep
                        break
            
            if reparacion_info:
                # Crear plato basado en el plato original + modificaciones
                nuevo_plato = self._crear_plato_con_modificaciones(
                    plato_nombre, 
                    reparacion_info,
                    menu
                )
                print(f"Agregado: {plato_nombre}")
                print(f"  Basado en: {reparacion_info['plato_original']}")
                print(f"  Modificaciones aplicadas: {len(reparacion_info.get('modificaciones', []))}")
            else:
                # Crear entrada básica para el plato (sin info de reparación)
                nuevo_plato = {
                    'nombre': plato_nombre,
                    'ingredientes': [f'ingrediente_de_{plato_nombre.lower().replace(" ", "_")}'],
                    'tecnica_coccion': ['por_definir'],
                    'sabor_dominante': 'salado',
                    'ingrediente_sabor': f'ingrediente_de_{plato_nombre.lower().replace(" ", "_")}',
                    'tradicion': 'general',
                    'temporada': ['primavera', 'verano', 'otoño', 'invierno']
                }
                print(f"Agregado: {plato_nombre}")
                print(f"  ADVERTENCIA: Requiere definicion manual de ingredientes reales")
            
            self.platos.append(nuevo_plato)
            self.platos_set.add(plato_nombre)
            agregados.append(plato_nombre)
        
        return agregados
    
    def _crear_plato_con_modificaciones(self, plato_nombre: str, reparacion: Dict, 
                                       menu: NuevoMenu) -> Dict[str, Any]:
        """
        Crea un nuevo plato copiando del plato base y aplicando modificaciones.
        
        Args:
            plato_nombre: Nombre del nuevo plato
            reparacion: Diccionario con información de la reparación
            menu: Menú con información de contexto
            
        Returns:
            Diccionario con la definición completa del nuevo plato
        """
        plato_original_nombre = reparacion['plato_original']
        modificaciones = reparacion.get('modificaciones', [])
        
        # Buscar plato original en la base
        plato_base = None
        for plato in self.platos:
            if plato['nombre'] == plato_original_nombre:
                plato_base = plato.copy()
                break
        
        if not plato_base:
            # Si no encontramos el plato base, crear uno básico
            return {
                'nombre': plato_nombre,
                'ingredientes': [],
                'tecnica_coccion': ['por_definir'],
                'sabor_dominante': 'salado',
                'ingrediente_sabor': '',
                'tradicion': menu.tradicion if hasattr(menu, 'tradicion') else 'general',
                'temporada': [menu.temporada] if hasattr(menu, 'temporada') else []
            }
        
        # Copiar estructura del plato base
        nuevo_plato = {
            'nombre': plato_nombre,
            'ingredientes': plato_base['ingredientes'].copy(),
            'tecnica_coccion': plato_base.get('tecnica_coccion', ['por_definir']).copy() if isinstance(plato_base.get('tecnica_coccion'), list) else [plato_base.get('tecnica_coccion', 'por_definir')],
            'sabor_dominante': plato_base.get('sabor_dominante', 'salado'),
            'ingrediente_sabor': plato_base.get('ingrediente_sabor', ''),
            'tradicion': plato_base.get('tradicion', 'general'),
            'temporada': plato_base.get('temporada', []).copy() if isinstance(plato_base.get('temporada'), list) else []
        }
        
        # Aplicar modificaciones
        ingredientes_substituidos = {}  # Para trackear substituciones
        ingredientes_eliminados = set()
        ingredientes_añadidos = []
        
        for mod in modificaciones:
            mod_str = str(mod)
            
            if "Substituido" in mod_str and " por " in mod_str:
                # Formato: "Substituido X por Y"
                partes = mod_str.split(" por ")
                if len(partes) == 2:
                    ing_viejo = partes[0].replace("Substituido", "").strip()
                    ing_nuevo = partes[1].strip()
                    
                    # Substituir en la lista de ingredientes
                    if ing_viejo in nuevo_plato['ingredientes']:
                        idx = nuevo_plato['ingredientes'].index(ing_viejo)
                        nuevo_plato['ingredientes'][idx] = ing_nuevo
                        ingredientes_substituidos[ing_viejo] = ing_nuevo
                        print(f"    → Substituido ingrediente: {ing_viejo} → {ing_nuevo}")
            
            elif "Eliminado" in mod_str:
                # Formato: "Eliminado X" o "Eliminado ingrediente X"
                ing_eliminado = mod_str.replace("Eliminado ingrediente", "").replace("Eliminado", "").strip()
                if ing_eliminado in nuevo_plato['ingredientes']:
                    nuevo_plato['ingredientes'].remove(ing_eliminado)
                    ingredientes_eliminados.add(ing_eliminado)
                    print(f"    → Eliminado ingrediente: {ing_eliminado}")
            
            elif "Añadido ingrediente" in mod_str:
                # Formato: "Añadido ingrediente X"
                ing_añadido = mod_str.replace("Añadido ingrediente", "").strip()
                if ing_añadido not in nuevo_plato['ingredientes']:
                    nuevo_plato['ingredientes'].append(ing_añadido)
                    ingredientes_añadidos.append(ing_añadido)
                    print(f"    → Añadido ingrediente: {ing_añadido}")
        
        # Actualizar sabor_dominante e ingrediente_sabor si es necesario
        ingrediente_sabor_original = nuevo_plato['ingrediente_sabor']
        
        # Si el ingrediente que da sabor fue substituido, actualizar
        if ingrediente_sabor_original in ingredientes_substituidos:
            nuevo_plato['ingrediente_sabor'] = ingredientes_substituidos[ingrediente_sabor_original]
            print(f"    → Actualizado ingrediente_sabor: {ingrediente_sabor_original} → {nuevo_plato['ingrediente_sabor']}")
        
        # Si el ingrediente que da sabor fue eliminado, buscar nuevo ingrediente dominante
        elif ingrediente_sabor_original in ingredientes_eliminados:
            if nuevo_plato['ingredientes']:
                # Tomar el primer ingrediente como nuevo ingrediente_sabor
                nuevo_plato['ingrediente_sabor'] = nuevo_plato['ingredientes'][0]
                print(f"    → Nuevo ingrediente_sabor: {nuevo_plato['ingrediente_sabor']}")
            else:
                nuevo_plato['ingrediente_sabor'] = ''
                nuevo_plato['sabor_dominante'] = 'neutro'
                print(f"    → Sin ingrediente_sabor (plato sin ingredientes)")
        
        # Actualizar temporada si hubo substituciones de ingredientes de temporada
        # (Esto es una simplificación - idealmente se buscaría en ingredientes.json)
        if menu and hasattr(menu, 'temporada'):
            if menu.temporada not in nuevo_plato['temporada']:
                nuevo_plato['temporada'].append(menu.temporada)
                print(f"    → Añadida temporada: {menu.temporada}")
        
        return nuevo_plato
    
    def _generar_id_caso(self) -> str:
        """Genera un ID único para un nuevo caso."""
        # Encontrar el número más alto actual
        max_num = 0
        for caso_id in self.casos_dict.keys():
            if caso_id.startswith('C'):
                try:
                    num = int(caso_id[1:])
                    max_num = max(max_num, num)
                except ValueError:
                    continue
        
        return f"C{max_num + 1:03d}"
    
    def _agregar_caso(self, menu: NuevoMenu, caso_id: str) -> str:
        """Agrega un nuevo caso a la base."""
        print(f"\nAGREGANDO NUEVO CASO: {caso_id}")
        
        nuevo_caso = {
            'id': caso_id,
            'restricciones': menu.restricciones,
            'temporada': menu.temporada,
            'tipo_evento': menu.tipo_evento,
            'menu': {
                'entrante': menu.entrante,
                'principal': menu.principal,
                'postre': menu.postre
            },
            'estilo': menu.estilo,
            'tradicion': menu.tradicion,
            'exito': menu.exito,
            'fallos_detectados': [],
            'reparaciones_aplicadas': [],
            'timestamp': datetime.now().isoformat(),
            'feedback': menu.feedback
        }
        
        self.casos.append(nuevo_caso)
        self.casos_dict[caso_id] = nuevo_caso
        
        print(f"Caso {caso_id} agregado exitosamente")
        
        return caso_id
    
    def _actualizar_reglas_reparacion(self, menu: NuevoMenu) -> List[str]:
        """Actualiza las reglas de reparación basándose en casos exitosos."""
        print(f"\nACTUALIZANDO REGLAS DE REPARACION")
        
        actualizaciones = []
        
        # Si el menú fue exitoso, puede servir para refinar reglas existentes
        if menu.exito:
            # Agregar nuevos patrones exitosos a las reglas
            for restriccion in menu.restricciones:
                if restriccion in self.reparaciones:
                    # Actualizar patrones exitosos para esta restricción
                    self._actualizar_patrones_exitosos(restriccion, menu)
                    actualizaciones.append(f"patrones_exitosos_{restriccion}")
        
        if actualizaciones:
            print(f"Reglas actualizadas: {actualizaciones}")
        else:
            print(f"No se requieren actualizaciones de reglas")
        
        return actualizaciones
    
    def _actualizar_patrones_exitosos(self, restriccion: str, menu: NuevoMenu):
        """Actualiza los patrones exitosos para una restricción específica."""
        if 'patrones_exitosos' not in self.reparaciones[restriccion]:
            self.reparaciones[restriccion]['patrones_exitosos'] = []
        
        patron_exitoso = {
            'menu': {
                'entrante': menu.entrante,
                'principal': menu.principal, 
                'postre': menu.postre
            },
            'temporada': menu.temporada,
            'tradicion': menu.tradicion,
            'timestamp': datetime.now().isoformat()
        }
        
        self.reparaciones[restriccion]['patrones_exitosos'].append(patron_exitoso)
    
    def _crear_backup(self):
        """Crea backup de todas las bases de conocimiento."""
        backup_dir = os.path.join(self.dir_conocimiento, 'backup')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, timestamp)
        
        os.makedirs(backup_path, exist_ok=True)
        
        archivos = ['ingredientes.json', 'platos.json', 'casos.json', 'reparaciones.json']
        for archivo in archivos:
            src = os.path.join(self.dir_conocimiento, archivo)
            dst = os.path.join(backup_path, archivo)
            if os.path.exists(src):
                shutil.copy2(src, dst)
        
        print(f"Backup creado: {backup_path}")
    
    def _restaurar_backup(self):
        """Restaura desde el backup más reciente."""
        backup_dir = os.path.join(self.dir_conocimiento, 'backup')
        if not os.path.exists(backup_dir):
            print("No hay backups disponibles")
            return
        
        # Encontrar backup más reciente
        backups = [d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d))]
        if not backups:
            print("No hay backups disponibles")
            return
        
        backup_mas_reciente = max(backups)
        backup_path = os.path.join(backup_dir, backup_mas_reciente)
        
        archivos = ['ingredientes.json', 'platos.json', 'casos.json', 'reparaciones.json']
        for archivo in archivos:
            src = os.path.join(backup_path, archivo)
            dst = os.path.join(self.dir_conocimiento, archivo)
            if os.path.exists(src):
                shutil.copy2(src, dst)
        
        print(f"Restaurado desde: {backup_path}")
        self._cargar_bases_conocimiento()
    
    def _guardar_bases_conocimiento(self):
        """Guarda todas las bases de conocimiento actualizadas."""
        print(f"\nGUARDANDO BASES DE CONOCIMIENTO")
        
        try:
            # Guardar ingredientes
            with open(os.path.join(self.dir_conocimiento, 'ingredientes.json'), 'w', encoding='utf-8') as f:
                json.dump(self.ingredientes, f, indent=2, ensure_ascii=False)
            
            # Guardar platos
            with open(os.path.join(self.dir_conocimiento, 'platos.json'), 'w', encoding='utf-8') as f:
                json.dump(self.platos, f, indent=2, ensure_ascii=False)
            
            # Guardar casos
            with open(os.path.join(self.dir_conocimiento, 'casos.json'), 'w', encoding='utf-8') as f:
                json.dump(self.casos, f, indent=2, ensure_ascii=False)
            
            # Guardar reparaciones
            with open(os.path.join(self.dir_conocimiento, 'reparaciones.json'), 'w', encoding='utf-8') as f:
                json.dump(self.reparaciones, f, indent=2, ensure_ascii=False)
            
            print(f"Todas las bases guardadas exitosamente")
            
        except Exception as e:
            print(f"Error guardando bases: {e}")
            raise
    
    def _registrar_actualizaciones(self, actualizaciones: Dict[str, List[str]], menu: NuevoMenu):
        """Registra las actualizaciones realizadas en el historial."""
        timestamp = datetime.now().isoformat()
        
        for tipo, items in actualizaciones.items():
            for item in items:
                registro = RegistroActualizacion(
                    timestamp=timestamp,
                    tipo=tipo,
                    item_id=item,
                    accion='agregado',
                    detalles={
                        'menu_origen': {
                            'entrante': menu.entrante,
                            'principal': menu.principal,
                            'postre': menu.postre
                        },
                        'tipo_evento': menu.tipo_evento,
                        'exito': menu.exito
                    }
                )
                self.historial_actualizaciones.append(registro)
    
    def _imprimir_resumen_actualizaciones(self, actualizaciones: Dict[str, List[str]]):
        """Imprime un resumen de las actualizaciones realizadas."""
        print(f"\nRESUMEN DE ACTUALIZACIONES")
        print("="*50)
        
        total_actualizaciones = sum(len(items) for items in actualizaciones.values())
        print(f"Total de actualizaciones: {total_actualizaciones}")
        
        for tipo, items in actualizaciones.items():
            if items:
                tipo_limpio = tipo.replace('_', ' ').title()
                print(f"  - {tipo_limpio}: {len(items)}")
                for item in items[:5]:  # Mostrar solo los primeros 5
                    print(f"    - {item}")
                if len(items) > 5:
                    print(f"    ... y {len(items) - 5} mas")
        
        print(f"\nEstado actualizado de la base:")
        print(f"  - Ingredientes: {len(self.ingredientes)}")
        print(f"  - Platos: {len(self.platos)}")
        print(f"  - Casos: {len(self.casos)}")
        print("="*50)
    
    def obtener_estadisticas_actualizaciones(self) -> Dict[str, Any]:
        """Obtiene estadísticas del historial de actualizaciones."""
        if not self.historial_actualizaciones:
            return {'total': 0}
        
        stats = {
            'total': len(self.historial_actualizaciones),
            'por_tipo': {},
            'ultima_actualizacion': None
        }
        
        for registro in self.historial_actualizaciones:
            tipo = registro.tipo
            if tipo not in stats['por_tipo']:
                stats['por_tipo'][tipo] = 0
            stats['por_tipo'][tipo] += 1
        
        if self.historial_actualizaciones:
            stats['ultima_actualizacion'] = self.historial_actualizaciones[-1].timestamp
        
        return stats
    
    def definir_plato_manual(self, nombre_plato: str, ingredientes: List[str], 
                           tecnica_coccion: List[str], sabor_dominante: str,
                           ingrediente_sabor: str, tradicion: str, 
                           temporada: List[str] = None) -> bool:
        """
        Define manualmente los detalles de un plato que fue agregado automáticamente.
        
        Args:
            nombre_plato: Nombre del plato a definir
            ingredientes: Lista de ingredientes del plato
            tecnica_coccion: Técnicas de cocción utilizadas
            sabor_dominante: Sabor principal del plato
            ingrediente_sabor: Ingrediente que aporta el sabor dominante
            tradicion: Tradición culinaria del plato
            temporada: Temporadas apropiadas para el plato
            
        Returns:
            True si se actualizó exitosamente
        """
        print(f"\nDEFINIENDO PLATO MANUAL: {nombre_plato}")
        
        # Buscar el plato en la base
        plato_encontrado = None
        for i, plato in enumerate(self.platos):
            if plato['nombre'] == nombre_plato:
                plato_encontrado = i
                break
        
        if plato_encontrado is None:
            print(f"Plato '{nombre_plato}' no encontrado en la base")
            return False
        
        # Actualizar información del plato
        if temporada is None:
            temporada = ['primavera', 'verano', 'otoño', 'invierno']
        
        self.platos[plato_encontrado].update({
            'ingredientes': ingredientes,
            'tecnica_coccion': tecnica_coccion,
            'sabor_dominante': sabor_dominante,
            'ingrediente_sabor': ingrediente_sabor,
            'tradicion': tradicion,
            'temporada': temporada
        })
        
        print(f"Plato '{nombre_plato}' actualizado exitosamente")
        print(f"  - Ingredientes: {ingredientes}")
        print(f"  - Tecnica: {tecnica_coccion}")
        print(f"  - Sabor dominante: {sabor_dominante}")
        print(f"  - Tradicion: {tradicion}")
        
        # Guardar cambios
        try:
            with open(os.path.join(self.dir_conocimiento, 'platos.json'), 'w', encoding='utf-8') as f:
                json.dump(self.platos, f, indent=2, ensure_ascii=False)
            print(f"Cambios guardados")
            return True
        except Exception as e:
            print(f"Error guardando cambios: {e}")
            return False