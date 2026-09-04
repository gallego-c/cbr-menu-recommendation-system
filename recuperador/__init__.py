"""
Paquete de Recuperación para Sistema CBR de Menús
===============================================

Dos métodos de similitud:
- Ponderada: Combina similitudes locales con pesos (por defecto)
- Vectorial: Vectoriza casos y usa métricas de distancia reales
"""

from .recuperacion import ModuloRecuperacion, ResultadoRecuperacion, MetodoSimilitud
from .similitud_ponderada import CalculadorSimilitudPonderada, PesosSimilitud
from .similitud_vectorial import CalculadorSimilitudVectorial, MetricaDistancia

__all__ = [
    'ModuloRecuperacion',
    'ResultadoRecuperacion',
    'MetodoSimilitud',
    'CalculadorSimilitudPonderada',
    'PesosSimilitud',
    'CalculadorSimilitudVectorial',
    'MetricaDistancia'
]