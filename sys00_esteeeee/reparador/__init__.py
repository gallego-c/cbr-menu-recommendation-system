"""
Módulo reparador para el sistema CBR de menús

El reparador implementa una estrategia en cascada (orden de prioridad):
1. Substitución de platos completos - busca platos alternativos con ingredientes compatibles con el menú (≥2 ingredientes)
2. Sustitución de ingredientes individuales - usando el Food Bank para encontrar sustituciones compatibles
3. Modificación de platos - aplica reglas para ajustar ingredientes del plato actual

Uso típico:
    from reparador import Reparador
    
    reparador = Reparador()
    resultado = reparador.reparar_plato(plato_problematico, menu, "restricciones", "vegano")
"""

from .reparador import Reparador
from .substituir import SubstitutorPlatos
from .modificar import ModificadorPlatos
from .ingredient_substitutor import IngredientSubstitutor
from .food_bank import FoodBank

__all__ = [
    'Reparador', 
    'SubstitutorPlatos', 
    'ModificadorPlatos',
    'IngredientSubstitutor',
    'FoodBank'
]

__version__ = '2.0.0'
__author__ = 'Sistema CBR'
__description__ = 'Módulo de reparación para menús gastronómicos con sustitución inteligente de ingredientes'