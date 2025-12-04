"""
Clases base para el sistema de validación
"""

from typing import List, Dict, Any, NamedTuple, Union
from abc import ABC, abstractmethod


class ResultadoValidacion(NamedTuple):
    """Resultado de una validación"""
    valido: bool
    errores: List[str] = []
    advertencias: List[str] = []
    detalles: Dict[str, Any] = {}


def convertir_a_string(valor: Any) -> str:
    """
    Convierte enums, listas u objetos a string.
    Función común para evitar duplicación en validadores.
    """
    if isinstance(valor, list):
        return convertir_a_string(valor[0]) if valor else "desconocido"
    return valor.value if hasattr(valor, 'value') else str(valor).lower()


class ReglaValidacion(ABC):
    """Interfaz base para todas las reglas de validación"""
    
    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre descriptivo de la regla"""
        pass
    
    @property
    @abstractmethod
    def tipo(self) -> str:
        """Tipo de validación (restriccion, temporada, etc.)"""
        pass
    
    @abstractmethod
    def validar(self, objetivo: Any, contexto: Dict[str, Any]) -> ResultadoValidacion:
        """
        Valida el objetivo contra esta regla
        
        Args:
            objetivo: Objeto a validar (Plato, Menu, etc.)
            contexto: Contexto adicional para la validación
            
        Returns:
            Resultado de la validación
        """
        pass
