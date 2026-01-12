"""
Módulo Actualizador de Bases de Conocimiento - Versión Modular Optimizada
===========================================================================

Estructura simplificada con gestores especializados:
- actualizador.py: Coordinador principal
- gestor_ingredientes.py: Detecta y agrega ingredientes
- gestor_platos.py: Detecta y agrega platos
- gestor_casos.py: Detecta y agrega casos
- gestor_persistencia.py: Maneja archivos JSON y backups

NEW: Retention system modules:
- config_retention.py: Retention configuration
- rating_collector.py: Interactive satisfaction rating
- similarity_adapter.py: Case-to-case similarity
- memory_curator.py: Intelligent retention/forgetting

Usa las clases Menu y Caso de conocimiento.models para type safety.
"""

from .actualizador import ActualizadorConocimiento
from conocimiento import Menu, Caso

# Export retention system components
from .config_retention import RetentionConfig, DEFAULT_RETENTION_CONFIG
from .rating_collector import RatingCollector
from .memory_curator import MemoryCurator
from .similarity_adapter import CaseSimilarityAdapter

__all__ = [
    'ActualizadorConocimiento', 
    'Menu', 
    'Caso',
    # Retention system
    'RetentionConfig',
    'DEFAULT_RETENTION_CONFIG',
    'RatingCollector',
    'MemoryCurator',
    'CaseSimilarityAdapter'
]