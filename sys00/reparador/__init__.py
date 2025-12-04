"""
Módulo reparador para el sistema CBR de menús

El reparador tiene dos estrategias principales:
1. Substitución de platos completos - busca platos alternativos que cumplan todas las preferencias
2. Modificación de platos - aplica reglas para ajustar ingredientes del plato actual

Uso típico:
    from reparador import Reparador
    
    reparador = Reparador()
    resultado = reparador.reparar_plato(plato_problematico, menu, "restricciones", "vegano")
"""

from .reparador_global_nuevo import Reparador
from .substituir import SubstitutorPlatos
from .modificar import ModificadorPlatos

__all__ = ['Reparador', 'SubstitutorPlatos', 'ModificadorPlatos']

__version__ = '1.0.0'
__author__ = 'Sistema CBR'
__description__ = 'Módulo de reparación para menús gastronómicos'