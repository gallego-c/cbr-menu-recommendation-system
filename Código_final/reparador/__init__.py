"""
Módulo reparador para el sistema CBR de menús

El reparador implementa una estrategia en cascada (orden de prioridad):
1. Substitución de platos completos - busca platos alternativos con ingredientes compatibles con el menú (≥2 ingredientes)
2. Sustitución de ingredientes individuales - usando el Food Bank para encontrar sustituciones compatibles
3. Modificación de platos - aplica reglas para ajustar ingredientes del plato actual

ARQUITECTURA UNIFICADA DE SUSTITUCIÓN:
=====================================
FoodBank es la fuente central para toda la lógica de sustitución de ingredientes:
- Verificación de restricciones dietéticas (vegano, vegetariano, sin_lactosa, sin_gluten)
- Búsqueda de sustitutos por tipo de restricción
- Evaluación de compatibilidad entre ingredientes
- Sustituciones vegetarianas y veganas

Los otros módulos (IngredientSubstitutor, SubstitutorPlatos) usan FoodBank
en lugar de implementar su propia lógica, evitando duplicación.

Uso típico:
    from reparador import Reparador
    
    reparador = Reparador()
    resultado = reparador.reparar_plato(plato_problematico, menu, "restricciones", "vegano")
    
Para verificar restricciones directamente:
    from reparador import FoodBank
    
    food_bank = FoodBank()
    viola = food_bank.ingrediente_viola_restriccion("chicken", "vegetariano")  # True
    cumple = food_bank.ingrediente_cumple_preferencias("tofu", ["vegetariano"], "verano")
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