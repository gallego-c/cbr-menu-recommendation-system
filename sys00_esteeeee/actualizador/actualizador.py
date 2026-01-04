"""
Actualizador de Conocimiento - Coordinador principal simplificado

Este módulo coordina todas las actualizaciones de las bases de conocimiento.
Usa las clases Menu y Caso de conocimiento.models para type safety.
"""

import os
from typing import Dict, List, Any
from datetime import datetime

# Importar modelos del dominio
from conocimiento import Menu, Caso

# Importar gestores especializados
from .gestor_ingredientes import GestorIngredientes
from .gestor_platos import GestorPlatos
from .gestor_casos import GestorCasos
from .gestor_persistencia import GestorPersistencia


class ActualizadorConocimiento:
    """
    Coordinador principal de actualizaciones de conocimiento.
    
    Delega responsabilidades a gestores especializados:
    - GestorIngredientes: Detecta y agrega ingredientes
    - GestorPlatos: Detecta y agrega platos
    - GestorCasos: Detecta y agrega casos
    - GestorPersistencia: Maneja archivos JSON y backups
    """
    
    def __init__(self, directorio_conocimiento: str = None):
        """Inicializa el actualizador y todos sus gestores"""
        if directorio_conocimiento is None:
            directorio_conocimiento = os.path.join(
                os.path.dirname(__file__), '..', 'conocimiento'
            )
        
        self.dir_conocimiento = directorio_conocimiento
        self.historial_actualizaciones = []
        
        # Inicializar gestor de persistencia
        self.persistencia = GestorPersistencia(directorio_conocimiento)
        
        # Cargar bases de conocimiento y crear índices
        self._cargar_bases()
        
        # Crear gestores sin duplicar datos (pasan referencias)
        self.gestor_ingredientes = GestorIngredientes(self.ingredientes, self.ingredientes_set)
        self.gestor_platos = GestorPlatos(self.platos, self.platos_set, self.persistencia)
        self.gestor_casos = GestorCasos(self.casos, self.casos_dict)
    
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
