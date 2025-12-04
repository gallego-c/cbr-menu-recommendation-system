"""
Módulo Actualizador de Bases de Conocimiento - Versión Modular Optimizada
===========================================================================

Estructura simplificada con gestores especializados:
- actualizador.py: Coordinador principal
- gestor_ingredientes.py: Detecta y agrega ingredientes
- gestor_platos.py: Detecta y agrega platos
- gestor_casos.py: Detecta y agrega casos
- gestor_persistencia.py: Maneja archivos JSON y backups

Usa las clases Menu y Caso de conocimiento.models para type safety.
"""

from .actualizador import ActualizadorConocimiento
from conocimiento import Menu, Caso

__all__ = ['ActualizadorConocimiento', 'Menu', 'Caso']