"""
Paquete de Recuperación para Sistema CBR de Menús
===============================================

Dos métodos de similitud:
- Ponderada: Combina similitudes locales con pesos (por defecto)
- Vectorial: Vectoriza casos y usa métricas de distancia reales
"""

from .recuperacion import ModuloRecuperacion, ConfiguracionRecuperacion, ResultadoRecuperacion, MetodoSimilitud
from .similitud_ponderada import CalculadorSimilitudPonderada, PesosSimilitud
from .similitud_vectorial import CalculadorSimilitudVectorial, MetricaDistancia

__all__ = [
    # Recuperación principal
    'ModuloRecuperacion',
    'ConfiguracionRecuperacion', 
    'ResultadoRecuperacion',
    'MetodoSimilitud',
    
    # Similitud ponderada
    'CalculadorSimilitudPonderada',
    'PesosSimilitud',
    
    # Similitud vectorial
    'CalculadorSimilitudVectorial',
    'MetricaDistancia'
]