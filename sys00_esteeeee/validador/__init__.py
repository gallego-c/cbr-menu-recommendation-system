"""
Sistema modular de validación para restricciones dietéticas y preferencias

Este módulo valida menús y platos contra restricciones usando datos 
de la carpeta conocimiento de manera completamente modular y extensible.

CRITERIOS DE VALIDACIÓN:
- Restricciones dietéticas: vegano, sin_lactosa, etc.
- Tradiciones culinarias: catalana, mexicana, etc.
- Estilos culinarios: molecular, clasico, etc. (incluye validación de técnicas)
- Temporada: ingredientes de temporada según época del año

Para agregar nuevas opciones, edita los archivos JSON en conocimiento/:
- restricciones.json: Define nuevas restricciones dietéticas
- tradiciones.json: Define nuevas tradiciones culinarias
- estilos.json: Define nuevos estilos (incluye técnicas permitidas/prohibidas)

NOTA: Las técnicas de cocción están definidas como TecnicaCoccion en conocimiento/models.py
y se validan en el contexto del estilo culinario elegido por el usuario.
"""

from .base import ResultadoValidacion, ReglaValidacion, convertir_a_string
from .restricciones import ValidadorRestriccion
from .temporada import ValidadorTemporada
from .tradicion import ValidadorTradicion
from .estilo import ValidadorEstilo
from .fabrica import FabricaValidadores
from .validador import ValidadorCompleto

__all__ = [
    'ResultadoValidacion',
    'ReglaValidacion',
    'convertir_a_string',
    'ValidadorRestriccion',
    'ValidadorTemporada',
    'ValidadorTradicion',
    'ValidadorEstilo',
    'FabricaValidadores',
    'ValidadorCompleto'
]

__version__ = '2.0.0'
__author__ = 'Sistema CBR'
__description__ = 'Módulo de validación extensible para menús gastronómicos'
