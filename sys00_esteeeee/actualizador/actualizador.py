"""
Actualizador de Conocimiento - Coordinador principal simplificado

Este módulo coordina todas las actualizaciones de las bases de conocimiento.
Usa las clases Menu y Caso de conocimiento.models para type safety.

NEW: Includes intelligent retention system with satisfaction-based memory curation.
"""

import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Importar modelos del dominio
from conocimiento import Menu, Caso

# Importar gestores especializados
from .gestor_ingredientes import GestorIngredientes
from .gestor_platos import GestorPlatos
from .gestor_casos import GestorCasos
from .gestor_persistencia import GestorPersistencia

# Importar sistema de retención
from .config_retention import RetentionConfig, DEFAULT_RETENTION_CONFIG
from .rating_collector import RatingCollector
from .memory_curator import MemoryCurator


class ActualizadorConocimiento:
    """
    Coordinador principal de actualizaciones de conocimiento.
    
    Delega responsabilidades a gestores especializados:
    - GestorIngredientes: Detecta y agrega ingredientes
    - GestorPlatos: Detecta y agrega platos
    - GestorCasos: Detecta y agrega casos
    - GestorPersistencia: Maneja archivos JSON y backups
    
    NEW: Integrates retention system:
    - RatingCollector: Collects user satisfaction scores
    - MemoryCurator: Manages bounded memory with intelligent retention
    """
    
    def __init__(self, directorio_conocimiento: str = None, 
                 retention_config: RetentionConfig = None,
                 enable_retention: bool = True):
        """
        Inicializa el actualizador y todos sus gestores
        
        Args:
            directorio_conocimiento: Path to knowledge base directory
            retention_config: Configuration for retention system
            enable_retention: Whether to enable intelligent retention (default: True)
        """
        if directorio_conocimiento is None:
            directorio_conocimiento = os.path.join(
                os.path.dirname(__file__), '..', 'conocimiento'
            )
        
        self.dir_conocimiento = directorio_conocimiento
        self.historial_actualizaciones = []
        self.enable_retention = enable_retention
        
        # Inicializar gestor de persistencia
        self.persistencia = GestorPersistencia(directorio_conocimiento)
        
        # Cargar bases de conocimiento y crear índices
        self._cargar_bases()
        
        # Crear gestores sin duplicar datos (pasan referencias)
        self.gestor_ingredientes = GestorIngredientes(self.ingredientes, self.ingredientes_set)
        self.gestor_platos = GestorPlatos(self.platos, self.platos_set, self.persistencia)
        self.gestor_casos = GestorCasos(self.casos, self.casos_dict)
        
        # NEW: Initialize retention system
        if self.enable_retention:
            self.retention_config = retention_config or DEFAULT_RETENTION_CONFIG
            self.rating_collector = RatingCollector(self.retention_config)
            self.memory_curator = MemoryCurator(self.retention_config)
        else:
            self.retention_config = None
            self.rating_collector = None
            self.memory_curator = None
    
    def _cargar_bases(self):
        """Carga todas las bases de conocimiento desde archivos JSON"""
        # Cargar datos
        self.ingredientes = self.persistencia.cargar_json('ingredientes.json')
        self.platos = self.persistencia.cargar_json('platos.json')
        self.casos = self.persistencia.cargar_json('casos.json')
        self.reparaciones = self.persistencia.cargar_json('reparaciones.json')
        
        # Crear índices para búsqueda rápida
        self.ingredientes_set = {ing['nombre'] for ing in self.ingredientes}
        self.platos_set = {plato['nombre'] for plato in self.platos}
        self.casos_dict = {caso['id']: caso for caso in self.casos}
    
    def procesar_nuevo_menu(self, menu: Menu, tipo_evento: str, temporada: str,
                          restricciones: List[str], estilo: str, tradicion: str,
                          exito: bool, reparaciones_aplicadas: List[Any] = None,
                          feedback: str = None, crear_backup: bool = False) -> Dict[str, List[str]]:
        """
        Procesa un nuevo menú y actualiza las bases de conocimiento necesarias.
        
        Args:
            menu: Objeto Menu con entrante, principal y postre
            tipo_evento: Tipo de evento (familiar, boda, etc.)
            temporada: Temporada del menú
            restricciones: Lista de restricciones dietéticas
            estilo: Estilo culinario
            tradicion: Tradición cultural
            exito: Si el menú fue exitoso
            reparaciones_aplicadas: Lista de reparaciones aplicadas (opcional)
            feedback: Feedback del menú (opcional)
            crear_backup: Si crear backup antes de actualizar (default: False)
            
        Returns:
            Diccionario con las actualizaciones realizadas
        """
        if crear_backup:
            self.persistencia.crear_backup()
        
        actualizaciones = {
            'ingredientes_nuevos': [],
            'platos_nuevos': [],
            'casos_agregados': [],
            'reparaciones_actualizadas': []
        }
        
        try:
            # 1. Detectar y agregar platos nuevos
            # ACTUALIZACIÓN DESACTIVADA - No se guardan nuevos platos
            # platos_nuevos = self.gestor_platos.detectar_nuevos(menu)
            # if platos_nuevos:
            #     actualizaciones['platos_nuevos'] = self.gestor_platos.agregar(
            #         platos_nuevos, reparaciones_aplicadas
            #     )
            
            # 2. Crear nuevo caso (con detección de duplicados)
            # ACTUALIZACIÓN DESACTIVADA - No se guardan nuevos casos
            # nuevo_caso = Caso(
            #     id='',  # Se generará en el gestor
            #     restricciones=restricciones,
            #     temporada=temporada,
            #     tipo_evento=tipo_evento,
            #     menu=menu,
            #     estilo=estilo,
            #     tradicion=tradicion,
            #     exito=exito,
            #     reparaciones_aplicadas=reparaciones_aplicadas or [],
            #     feedback=feedback
            # )
            # 
            # caso_id, fue_agregado = self.gestor_casos.agregar(nuevo_caso)
            # if fue_agregado:
            #     actualizaciones['casos_agregados'] = [caso_id]
            caso_id = None  # No se guardan nuevos casos
            fue_agregado = False
            
            # 3. Actualizar reglas de reparación si el menú fue exitoso
            # ACTUALIZACIÓN DESACTIVADA - No se actualizan reglas
            # if exito:
            #     actualizaciones['reparaciones_actualizadas'] = self._actualizar_reglas_reparacion(
            #         menu, restricciones, temporada, tradicion
            #     )
            
            # 4. Guardar todas las bases actualizadas (solo si hubo cambios)
            # ACTUALIZACIÓN DESACTIVADA - No se guardan cambios
            # if any(actualizaciones.values()):
            #     self.persistencia.guardar_todas_las_bases(
            #         self.ingredientes, self.platos, self.casos, self.reparaciones
            #     )
            #     self._registrar_actualizaciones(actualizaciones, menu.to_dict())
            
            print(f"\nPROCESAMIENTO COMPLETADO (sin guardar cambios)")
            self._imprimir_resumen(actualizaciones)
            
            return actualizaciones
            
        except Exception as e:
            print(f"Error durante el procesamiento: {e}")
            if crear_backup:
                print("Restaurando desde backup...")
                self.persistencia.restaurar_backup()
            raise
    
    def _actualizar_reglas_reparacion(self, menu: Menu, restricciones: List[str],
                                     temporada: str, tradicion: str) -> List[str]:
        """
        Actualiza las reglas de reparación basándose en casos exitosos.
        
        Args:
            menu: Objeto Menu
            restricciones: Lista de restricciones
            temporada: Temporada del menú
            tradicion: Tradición cultural
            
        Returns:
            Lista de actualizaciones realizadas
        """
        print(f"\nACTUALIZANDO REGLAS DE REPARACION")
        
        actualizaciones = []
        
        # Si el menú fue exitoso, puede servir para refinar reglas existentes
        for restriccion in restricciones:
            if restriccion in self.reparaciones:
                self._actualizar_patrones_exitosos(restriccion, menu, temporada, tradicion)
                actualizaciones.append(f"patrones_exitosos_{restriccion}")
        
        if actualizaciones:
            print(f"Reglas actualizadas: {actualizaciones}")
        else:
            print(f"No se requieren actualizaciones de reglas")
        
        return actualizaciones
    
    def _actualizar_patrones_exitosos(self, restriccion: str, menu: Menu,
                                     temporada: str, tradicion: str):
        """Actualiza los patrones exitosos para una restricción específica"""
        self.reparaciones[restriccion].setdefault('patrones_exitosos', []).append({
            'menu': menu.to_dict(),
            'temporada': temporada,
            'tradicion': tradicion,
            'timestamp': datetime.now().isoformat()
        })
    
    def _registrar_actualizaciones(self, actualizaciones: Dict[str, List[str]], menu: Dict[str, Any]):
        """Registra las actualizaciones realizadas en el historial"""
        timestamp = datetime.now().isoformat()
        menu_ref = {k: menu.get(k) for k in ('entrante', 'principal', 'postre')}
        
        for tipo, items in actualizaciones.items():
            if items:  # Solo registrar si hay items
                self.historial_actualizaciones.extend([
                    {
                        'timestamp': timestamp,
                        'tipo': tipo,
                        'item_id': item,
                        'accion': 'agregado',
                        'detalles': {'menu_asociado': menu_ref}
                    }
                    for item in items
                ])
    
    def _imprimir_resumen(self, actualizaciones: Dict[str, List[str]]):
        """Imprime un resumen de las actualizaciones realizadas"""
        print(f"\nRESUMEN DE ACTUALIZACIONES")
        print("="*50)
        
        total = sum(len(items) for items in actualizaciones.values())
        print(f"Total de actualizaciones: {total}")
        
        if actualizaciones['ingredientes_nuevos']:
            print(f"  - Ingredientes Nuevos: {len(actualizaciones['ingredientes_nuevos'])}")
            for ing in actualizaciones['ingredientes_nuevos']:
                print(f"    - {ing}")
        
        if actualizaciones['platos_nuevos']:
            print(f"  - Platos Nuevos: {len(actualizaciones['platos_nuevos'])}")
            for plato in actualizaciones['platos_nuevos']:
                print(f"    - {plato}")
        
        if actualizaciones['casos_agregados']:
            print(f"  - Casos Agregados: {len(actualizaciones['casos_agregados'])}")
            for caso in actualizaciones['casos_agregados']:
                print(f"    - {caso}")
        
        print(f"\nEstado actualizado de la base:")
        print(f"  - Ingredientes: {len(self.ingredientes)}")
        print(f"  - Platos: {len(self.platos)}")
        print(f"  - Casos: {len(self.casos)}")
        print("="*50)
    
    def verificar_duplicado(self, menu: Menu, tipo_evento: str, temporada: str,
                           restricciones: List[str], estilo: str, tradicion: str) -> bool:
        """
        Verifica si un caso ya existe en la base de conocimiento.
        
        Args:
            menu: Objeto Menu a verificar
            tipo_evento: Tipo de evento
            temporada: Temporada
            restricciones: Lista de restricciones
            estilo: Estilo culinario
            tradicion: Tradición cultural
            
        Returns:
            True si el caso ya existe, False en caso contrario
        """
        # Crear caso temporal
        caso_temp = Caso(
            id='',  # ID vacío, se generará uno temporal
            restricciones=restricciones,
            temporada=temporada,
            tipo_evento=tipo_evento,
            menu=menu,
            estilo=estilo,
            tradicion=tradicion,
            exito=True
        )
        
        # Usar el gestor de casos para buscar duplicado
        caso_existente_id = self.gestor_casos._buscar_duplicado(caso_temp)
        
        return caso_existente_id is not None
    
    def obtener_estadisticas_actualizaciones(self) -> Dict[str, Any]:
        """Obtiene estadísticas sobre las actualizaciones realizadas"""
        return {
            'total_actualizaciones': len(self.historial_actualizaciones),
            'ingredientes_totales': len(self.ingredientes),
            'platos_totales': len(self.platos),
            'casos_totales': len(self.casos),
            'backups_disponibles': len(self.persistencia.listar_backups())
        }
    
    # =========================================================================
    # NEW: RETENTION SYSTEM METHODS
    # =========================================================================
    
    def procesar_caso_con_retencion(self, menu: Menu, tipo_evento: str, temporada: str,
                                    restricciones: List[str], estilo: str, tradicion: str,
                                    exito: bool, reparaciones_aplicadas: List[Any] = None,
                                    feedback: str = None, 
                                    collect_rating: bool = True,
                                    crear_backup: bool = False) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Process a new menu with intelligent retention.
        
        This is the NEW end-to-end pipeline:
        1. Check if valid (only valid cases are considered)
        2. Collect satisfaction rating (if enabled)
        3. Create case with satisfaction + modification_count
        4. Decide retention based on similarity/satisfaction/complexity
        5. Curate memory if needed
        6. Persist changes
        
        Args:
            menu: Menu object
            tipo_evento: Event type
            temporada: Season
            restricciones: Dietary restrictions
            estilo: Culinary style
            tradicion: Cultural tradition
            exito: Whether menu is valid/successful
            reparaciones_aplicadas: List of modifications applied
            feedback: Optional user feedback
            collect_rating: Whether to collect satisfaction rating
            crear_backup: Whether to create backup before saving
            
        Returns:
            Tuple of (caso_id, result_dict)
            caso_id: ID of saved case (or None if not retained)
            result_dict: Details about retention decision
        """
        if not self.enable_retention:
            # Fallback to old behavior (no saving)
            print("\n[RETENTION DISABLED] Case will not be saved.")
            return (None, {'retained': False, 'reason': 'Retention system disabled'})
        
        # Step 1: Only consider valid cases
        if not exito:
            print("\n[RETENTION] Invalid case - not saving.")
            return (None, {'retained': False, 'reason': 'Invalid case'})
        
        # Step 2: Collect satisfaction rating
        satisfaction_score = None
        satisfaction_per_menu = None
        rating_timestamp = None
        
        if collect_rating and self.rating_collector:
            print("\n" + "="*70)
            print("RECOLECCIÓN DE SATISFACCIÓN")
            print("="*70)
            satisfaction_score, satisfaction_per_menu, rating_timestamp = \
                self.rating_collector.collect_menu_rating(menu.to_dict())
        
        # Step 3: Create caso with all metadata
        modification_count = len(reparaciones_aplicadas) if reparaciones_aplicadas else 0
        
        nuevo_caso = Caso(
            id='',  # Will be generated
            restricciones=restricciones,
            temporada=temporada,
            tipo_evento=tipo_evento,
            menu=menu,
            estilo=estilo,
            tradicion=tradicion,
            exito=exito,
            reparaciones_aplicadas=reparaciones_aplicadas or [],
            feedback=feedback,
            satisfaction_score=satisfaction_score,
            satisfaction_per_menu=satisfaction_per_menu,
            rating_timestamp=rating_timestamp,
            modification_count=modification_count
        )
        
        # Step 4: Decide retention
        should_retain, reason, metrics = self.memory_curator.should_retain_case(
            nuevo_caso, self.casos
        )
        
        print("\n" + "="*70)
        print("DECISIÓN DE RETENCIÓN")
        print("="*70)
        print(f"¿Retener caso? {should_retain}")
        print(f"Razón: {reason}")
        print(f"\nMétricas de retención:")
        print(f"  Satisfacción: {metrics['satisfaction_normalized']:.3f}")
        print(f"  Modificaciones: {metrics['modification_bonus']:.3f} (count: {modification_count})")
        print(f"  Novedad: {metrics['novelty']:.3f}")
        print(f"  → Puntuación total: {metrics['keep_score']:.3f}")
        
        if not should_retain:
            return (None, {
                'retained': False,
                'reason': reason,
                'metrics': metrics
            })
        
        # Step 5: Add case
        if crear_backup:
            self.persistencia.crear_backup()
        
        # Generate ID and add
        nuevo_caso.id = self.gestor_casos._generar_id()
        if not nuevo_caso.timestamp:
            nuevo_caso.timestamp = datetime.now().isoformat()
        
        caso_dict = nuevo_caso.to_dict()
        self.casos.append(caso_dict)
        self.casos_dict[nuevo_caso.id] = caso_dict
        
        print(f"\n✓ Caso {nuevo_caso.id} agregado a memoria")
        
        # Step 6: Curate memory if needed
        casos_curados, casos_eliminados = self.memory_curator.curate_memory(self.casos)
        
        if casos_eliminados:
            print(f"\n[CURACIÓN] Memoria curada: {len(casos_eliminados)} casos eliminados")
            for caso_id in casos_eliminados:
                print(f"  - {caso_id}")
            
            # Update internal state
            self.casos = casos_curados
            self.casos_dict = {c['id']: c for c in self.casos}
        
        # Step 7: Persist to disk
        print(f"\n[PERSISTENCIA] Guardando {len(self.casos)} casos...")
        success = self.persistencia.guardar_json('casos.json', self.casos)
        
        if success:
            print("✓ Base de casos actualizada correctamente")
        else:
            print("✗ Error al guardar base de casos")
        
        return (nuevo_caso.id, {
            'retained': True,
            'reason': reason,
            'metrics': metrics,
            'casos_eliminados': casos_eliminados,
            'memoria_final': len(self.casos)
        })
    
    def get_retention_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the retention system.
        
        Returns:
            Dictionary with retention stats
        """
        if not self.enable_retention:
            return {'enabled': False}
        
        # Compute statistics from current cases
        casos_obj = [Caso.from_dict(c) for c in self.casos]
        
        with_satisfaction = sum(1 for c in casos_obj if c.satisfaction_score is not None)
        with_modifications = sum(1 for c in casos_obj if c.modification_count > 0)
        
        avg_satisfaction = None
        if with_satisfaction > 0:
            scores = [c.satisfaction_score for c in casos_obj if c.satisfaction_score is not None]
            avg_satisfaction = sum(scores) / len(scores)
        
        avg_modifications = None
        if with_modifications > 0:
            counts = [c.modification_count for c in casos_obj if c.modification_count > 0]
            avg_modifications = sum(counts) / len(counts)
        
        return {
            'enabled': True,
            'total_casos': len(self.casos),
            'max_casos': self.retention_config.max_cases,
            'min_casos': self.retention_config.min_cases,
            'memory_usage_pct': (len(self.casos) / self.retention_config.max_cases) * 100,
            'casos_with_satisfaction': with_satisfaction,
            'casos_with_modifications': with_modifications,
            'avg_satisfaction': avg_satisfaction,
            'avg_modifications': avg_modifications,
            'retention_weights': {
                'satisfaction': self.retention_config.weight_satisfaction,
                'modifications': self.retention_config.weight_modifications,
                'novelty': self.retention_config.weight_novelty
            }
        }
