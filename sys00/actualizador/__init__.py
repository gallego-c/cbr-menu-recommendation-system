"""
Módulo Actualizador de Bases de Conocimiento
==========================================

Este módulo gestiona las actualizaciones automáticas de las bases de conocimiento
del sistema CBR cuando se generan nuevos menús exitosos.
"""

from .actualizador import (
    ActualizadorConocimiento,
    NuevoMenu,
    NuevoIngrediente, 
    NuevoPlato,
    RegistroActualizacion
)

__all__ = [
    'ActualizadorConocimiento',
    'NuevoMenu',
    'NuevoIngrediente',
    'NuevoPlato', 
    'RegistroActualizacion'
]