"""
Módulo de Modelos de Conocimiento
==================================

Exporta las clases principales del dominio:
- Ingrediente: Ingrediente con propiedades
- Plato: Plato con ingredientes y técnicas
- Menu: Menú con entrante, principal y postre
- Caso: Caso completo con contexto y validaciones
- cargador: Cargador centralizado de archivos JSON
"""

from .models import Ingrediente, Plato, Menu, Caso
from .cargador import cargador, CargadorConocimiento

__all__ = ['Ingrediente', 'Plato', 'Menu', 'Caso', 'cargador', 'CargadorConocimiento']
