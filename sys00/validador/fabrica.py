"""
Fábrica de validadores basada en datos
"""

from typing import Dict, Optional, List
from .base import ReglaValidacion
from .restricciones import ValidadorRestriccion
from .temporada import ValidadorTemporada
from .tradicion import ValidadorTradicion
from .estilo import ValidadorEstilo


class FabricaValidadores:
    """Factory para crear validadores genéricos desde bases de conocimiento"""
    
    def __init__(
        self,
        ingredientes_db: Dict[str, Dict],
        restricciones_config: List[Dict],
        tradiciones_config: List[Dict],
        estilos_config: List[Dict]
    ):
        """
        Inicializa la fábrica con configuraciones pre-cargadas.
        
        Args:
            ingredientes_db: Base de datos de ingredientes
            restricciones_config: Lista de restricciones desde restricciones.json
            tradiciones_config: Lista de tradiciones desde tradiciones.json
            estilos_config: Lista de estilos desde estilos.json
        """
        self.ingredientes_db = ingredientes_db
        
        # Crear índices por nombre para acceso rápido
        self._restricciones_por_nombre = {r['nombre']: r for r in restricciones_config}
        self._tradiciones_por_nombre = {t['nombre']: t for t in tradiciones_config}
        self._estilos_por_nombre = {e['nombre']: e for e in estilos_config}
        
        # Validadores singleton
        self._validador_temporada = ValidadorTemporada(ingredientes_db)
    
    def crear_validador_restriccion(self, restriccion: str) -> Optional[ReglaValidacion]:
        """Crea validador para una restricción específica desde la configuración"""
        config = self._restricciones_por_nombre.get(restriccion.lower())
        if config:
            return ValidadorRestriccion(config, self.ingredientes_db)
        return None
    
    def crear_validador_temporada(self) -> ReglaValidacion:
        """Crea validador de temporada"""
        return self._validador_temporada
    
    def crear_validador_tradicion(self, tradicion: str) -> Optional[ReglaValidacion]:
        """Crea validador para una tradición específica desde la configuración"""
        config = self._tradiciones_por_nombre.get(tradicion.lower())
        if config:
            return ValidadorTradicion(config, self._tradiciones_por_nombre)
        return None
    
    def listar_restricciones_disponibles(self) -> List[str]:
        """Lista todas las restricciones que pueden validarse"""
        return list(self._restricciones_por_nombre.keys())
    
    def listar_tradiciones_disponibles(self) -> List[str]:
        """Lista todas las tradiciones que pueden validarse"""
        return list(self._tradiciones_por_nombre.keys())
    
    def crear_validador_estilo(self, estilo: str) -> Optional[ReglaValidacion]:
        """Crea validador para un estilo específico desde la configuración"""
        config = self._estilos_por_nombre.get(estilo.lower())
        if config:
            return ValidadorEstilo(config)
        return None
    
    def listar_estilos_disponibles(self) -> List[str]:
        """Lista todos los estilos disponibles"""
        return list(self._estilos_por_nombre.keys())
    
    def obtener_info_restriccion(self, restriccion: str) -> Optional[Dict]:
        """Obtiene información sobre una restricción"""
        return self._restricciones_por_nombre.get(restriccion.lower())
    
    def obtener_info_tradicion(self, tradicion: str) -> Optional[Dict]:
        """Obtiene información sobre una tradición"""
        return self._tradiciones_por_nombre.get(tradicion.lower())
    
    def obtener_info_estilo(self, estilo: str) -> Optional[Dict]:
        """Obtiene información sobre un estilo"""
        return self._estilos_por_nombre.get(estilo.lower())
