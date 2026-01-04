"""
Módulo Actualizador de Bases de Conocimiento - Versión Modular Optimizada
===========================================================================

Estructura simplificada con gestores especializados:
- actualizador.py: Coordinador principal
- gestor_ingredientes.py: Detecta y agrega ingredientes
- gestor_platos.py: Detecta y agrega platos
- gestor_casos.py: Detecta y agrega casos
- gestor_persistencia.py: Maneja archivos JSON y backups

Sistema de Retención (v2):
- config_retencion.py: Configuración de retención de casos
- similitud_casos.py: Cálculo de similitud entre casos (wrapper)
- recolector_satisfaccion.py: Recolección de ratings de usuarios
- gestor_retencion.py: Curación de memoria (remember/forget)

Usa las clases Menu y Caso de conocimiento.models para type safety.
"""

from .actualizador import ActualizadorConocimiento
from .config_retencion import ConfiguracionRetencion, CONFIG_RETENCION_DEFAULT
from .recolector_satisfaccion import RecolectorSatisfaccion, SatisfaccionCaso, RatingMenu
from .gestor_retencion import GestorRetencion, MetricasRetencion
from .similitud_casos import SimilitudCasos, SimilitudMenus
from conocimiento import Menu, Caso

__all__ = [
    'ActualizadorConocimiento', 
    'Menu', 
    'Caso',
    'ConfiguracionRetencion',
    'CONFIG_RETENCION_DEFAULT',
    'RecolectorSatisfaccion',
    'SatisfaccionCaso',
    'RatingMenu',
    'GestorRetencion',
    'MetricasRetencion',
    'SimilitudCasos',
    'SimilitudMenus'
]