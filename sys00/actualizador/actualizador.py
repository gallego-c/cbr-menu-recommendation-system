"""
Actualizador de Conocimiento - Coordinador principal simplificado

Este módulo coordina todas las actualizaciones de las bases de conocimiento.
Usa las clases Menu y Caso de conocimiento.models para type safety.

v2: Integrado con sistema de retención para curación de memoria.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Importar modelos del dominio
from conocimiento import Menu, Caso

# Importar gestores especializados
from .gestor_ingredientes import GestorIngredientes
from .gestor_platos import GestorPlatos
from .gestor_casos import GestorCasos
from .gestor_persistencia import GestorPersistencia

# Importar sistema de retención
from .config_retencion import ConfiguracionRetencion, CONFIG_RETENCION_DEFAULT
from .recolector_satisfaccion import RecolectorSatisfaccion, SatisfaccionCaso


class ActualizadorConocimiento:
    """
    Coordinador principal de actualizaciones de conocimiento.
    
    Delega responsabilidades a gestores especializados:
    - GestorIngredientes: Detecta y agrega ingredientes
    - GestorPlatos: Detecta y agrega platos
    - GestorCasos: Detecta y agrega casos (con sistema de retención)
    - GestorPersistencia: Maneja archivos JSON y backups
    - RecolectorSatisfaccion: Recolecta ratings de usuarios
    """
    
    def __init__(self, directorio_conocimiento: str = None,
                 config_retencion: ConfiguracionRetencion = None):
        """
        Inicializa el actualizador y todos sus gestores.
        
        Args:
            directorio_conocimiento: Directorio con archivos JSON de conocimiento
            config_retencion: Configuración del sistema de retención
        """
        if directorio_conocimiento is None:
            directorio_conocimiento = os.path.join(
                os.path.dirname(__file__), '..', 'conocimiento'
            )
        
        self.dir_conocimiento = directorio_conocimiento
        self.historial_actualizaciones = []
        self.config_retencion = config_retencion or CONFIG_RETENCION_DEFAULT
        
        # Inicializar gestor de persistencia
        self.persistencia = GestorPersistencia(directorio_conocimiento)
        
        # Cargar bases de conocimiento y crear índices
        self._cargar_bases()
        
        # Crear gestores con configuración de retención
        self.gestor_ingredientes = GestorIngredientes(self.ingredientes, self.ingredientes_set)
        self.gestor_platos = GestorPlatos(self.platos, self.platos_set, self.persistencia)
        self.gestor_casos = GestorCasos(self.casos, self.casos_dict, self.config_retencion)
        
        # Recolector de satisfacción
        self.recolector_satisfaccion = RecolectorSatisfaccion(self.config_retencion)
    
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
                          feedback: str = None, crear_backup: bool = False,
                          satisfaccion: SatisfaccionCaso = None) -> Dict[str, List[str]]:
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
            satisfaccion: Información de satisfacción del usuario (opcional)
            
        Returns:
            Diccionario con las actualizaciones realizadas
        """
        if crear_backup:
            self.persistencia.crear_backup()
        
        actualizaciones = {
            'ingredientes_nuevos': [],
            'platos_nuevos': [],
            'casos_agregados': [],
            'casos_eliminados': [],
            'reparaciones_actualizadas': []
        }
        
        try:
            # 1. Detectar y agregar platos nuevos
            platos_nuevos = self.gestor_platos.detectar_nuevos(menu)
            if platos_nuevos:
                actualizaciones['platos_nuevos'] = self.gestor_platos.agregar(
                    platos_nuevos, reparaciones_aplicadas
                )
            
            # 2. Calcular modification_count
            modification_count = self._contar_modificaciones(reparaciones_aplicadas)
            
            # 3. Crear nuevo caso (con detección de duplicados y retención)
            nuevo_caso = Caso(
                id='',  # Se generará en el gestor
                restricciones=restricciones,
                temporada=temporada,
                tipo_evento=tipo_evento,
                menu=menu,
                estilo=estilo,
                tradicion=tradicion,
                exito=exito,
                reparaciones_aplicadas=reparaciones_aplicadas or [],
                feedback=feedback,
                satisfaccion=satisfaccion.to_dict() if satisfaccion else None,
                modification_count=modification_count
            )
            
            # Agregar con sistema de retención
            caso_id, fue_agregado = self.gestor_casos.agregar(nuevo_caso, satisfaccion)
            if fue_agregado:
                actualizaciones['casos_agregados'] = [caso_id]
            
            # 4. Actualizar reglas de reparación si el menú fue exitoso
            if exito:
                actualizaciones['reparaciones_actualizadas'] = self._actualizar_reglas_reparacion(
                    menu, restricciones, temporada, tradicion
                )
            
            # 5. Guardar todas las bases actualizadas (solo si hubo cambios)
            if any(actualizaciones.values()):
                self.persistencia.guardar_todas_las_bases(
                    self.ingredientes, self.platos, self.casos, self.reparaciones
                )
                self._registrar_actualizaciones(actualizaciones, menu.to_dict())
            
            print(f"\nPROCESAMIENTO COMPLETADO")
            self._imprimir_resumen(actualizaciones)
            
            return actualizaciones
            
        except Exception as e:
            print(f"Error durante el procesamiento: {e}")
            if crear_backup:
                print("Restaurando desde backup...")
                self.persistencia.restaurar_backup()
            raise
    
    def _contar_modificaciones(self, reparaciones: List[Any]) -> int:
        """Cuenta el número total de modificaciones en las reparaciones."""
        if not reparaciones:
            return 0
        
        total = 0
        for rep in reparaciones:
            if isinstance(rep, dict):
                mods = rep.get('modificaciones', [])
                total += len(mods) if mods else 1
            else:
                total += 1
        return total
    
    def recolectar_y_procesar_con_rating(self, menu: Menu, tipo_evento: str, 
                                          temporada: str, restricciones: List[str],
                                          estilo: str, tradicion: str,
                                          reparaciones_aplicadas: List[Any] = None,
                                          crear_backup: bool = False) -> Dict[str, Any]:
        """
        Flujo completo: recolecta rating del usuario y procesa el menú.
        
        Este es el método principal a usar después de generar un menú válido.
        
        Args:
            menu: Menú generado (ya validado)
            tipo_evento, temporada, etc.: Contexto del caso
            reparaciones_aplicadas: Lista de reparaciones
            crear_backup: Si crear backup
            
        Returns:
            Dict con actualizaciones y información de satisfacción
        """
        print("\n" + "="*50)
        print("📊 RECOLECCIÓN DE SATISFACCIÓN")
        print("="*50)
        
        # Recolectar rating
        satisfaccion = self.recolector_satisfaccion.recolectar_satisfaccion_caso([menu.to_dict()])
        
        # Verificar si debemos guardar
        if not self.recolector_satisfaccion.debe_guardar_caso(satisfaccion):
            print("\n⚠️ Caso no guardado: no se proporcionó rating y está configurado como requerido")
            return {
                'caso_guardado': False,
                'satisfaccion': satisfaccion.to_dict(),
                'actualizaciones': {}
            }
        
        # Procesar con el sistema de retención
        actualizaciones = self.procesar_nuevo_menu(
            menu=menu,
            tipo_evento=tipo_evento,
            temporada=temporada,
            restricciones=restricciones,
            estilo=estilo,
            tradicion=tradicion,
            exito=True,  # Si llegamos aquí, el menú es válido
            reparaciones_aplicadas=reparaciones_aplicadas,
            feedback=f"Rating: {satisfaccion.satisfaction_score}",
            crear_backup=crear_backup,
            satisfaccion=satisfaccion
        )
        
        return {
            'caso_guardado': len(actualizaciones.get('casos_agregados', [])) > 0,
            'satisfaccion': satisfaccion.to_dict(),
            'actualizaciones': actualizaciones
        }
    
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
