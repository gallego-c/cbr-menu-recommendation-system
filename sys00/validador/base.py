"""
Clases base para el sistema de validación
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ResultadoValidacion:
    """Resultado de una validación"""
    valido: bool
    errores: List[str] = None
    advertencias: List[str] = None
    detalles: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errores is None:
            self.errores = []
        if self.advertencias is None:
            self.advertencias = []
        if self.detalles is None:
            self.detalles = {}


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
