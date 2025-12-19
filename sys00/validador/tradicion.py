"""
Validador genérico de tradición culinaria basado en datos
"""

from typing import Dict, Any
from conocimiento.models import Plato
from .base import ReglaValidacion, ResultadoValidacion, convertir_a_string


class ValidadorTradicion(ReglaValidacion):
    """Validador genérico de tradiciones que lee configuración de tradiciones.json"""
    
    def __init__(self, config_tradicion: Dict[str, Any], todas_tradiciones: Dict[str, Dict]):
        """
        Inicializa el validador con la configuración de una tradición
        
        Args:
            config_tradicion: Diccionario con la configuración de la tradición específica
            todas_tradiciones: Diccionario con todas las tradiciones disponibles
        """
        self._nombre = config_tradicion['nombre']
        self._descripcion = config_tradicion['descripcion']
        self._ingredientes_caracteristicos = set(config_tradicion.get('ingredientes_caracteristicos', []))
        self._ingredientes_tipicos = set(config_tradicion.get('ingredientes_tipicos', []))
        self._coherencia_minima = config_tradicion['coherencia_minima']  # Se lee del JSON
        self._todas_tradiciones = todas_tradiciones
    
    @property
    def nombre(self) -> str:
        return f"Tradición {self._nombre.capitalize()}"
    
    @property
    def tipo(self) -> str:
        return "tradicion"
    
    def validar(self, plato: Plato, contexto: Dict[str, Any]) -> ResultadoValidacion:
        """
        Valida que un plato respete la tradición culinaria.
        plato.ingredientes es List[str] - nombres de ingredientes.
        """
        # plato.ingredientes ya es List[str], convertir a set directamente
        ingredientes_plato = set(plato.ingredientes)
        ingredientes_esperados = self._ingredientes_caracteristicos
        ingredientes_encontrados = ingredientes_plato.intersection(ingredientes_esperados)
        
        # Todos los ingredientes de la tradición actual (característicos + típicos)
        todos_ingredientes_tradicion = self._ingredientes_caracteristicos.union(self._ingredientes_tipicos)
        
        # Buscar ingredientes de otras tradiciones que NO están en la tradición actual
        ingredientes_conflicto = []
        for otra_tradicion, config_otra in self._todas_tradiciones.items():
            if otra_tradicion != self._nombre:
                ingredientes_otra = set(config_otra.get('ingredientes_caracteristicos', []))
                # Solo son conflictos si están en otra tradición pero NO en la actual
                conflictos = ingredientes_plato.intersection(ingredientes_otra) - todos_ingredientes_tradicion
                if conflictos:
                    ingredientes_conflicto.extend([
                        {'ingrediente': ing, 'tradicion_conflicto': otra_tradicion}
                        for ing in conflictos
                    ])
        
        errores = []
        advertencias = []
        detalles = {
            'tradicion': self._nombre,
            'descripcion': self._descripcion,
            'ingredientes_caracteristicos': list(self._ingredientes_caracteristicos),
            'ingredientes_encontrados': list(ingredientes_encontrados),
            'ingredientes_conflicto': ingredientes_conflicto,
            'porcentaje_coherencia': 0,
            'coherencia_minima_requerida': self._coherencia_minima * 100
        }
        
        # Calcular coherencia
        if ingredientes_esperados:
            coherencia = len(ingredientes_encontrados) / len(ingredientes_esperados)
            detalles['porcentaje_coherencia'] = coherencia * 100
            
            if coherencia < self._coherencia_minima:
                errores.append(
                    f"Muy pocos ingredientes de tradición {self._nombre}: "
                    f"{len(ingredientes_encontrados)}/{len(ingredientes_esperados)} "
                    f"({coherencia:.1%}, mínimo: {self._coherencia_minima:.1%})"
                )
            elif coherencia < (self._coherencia_minima + 0.2):
                advertencias.append(
                    f"Coherencia baja con tradición {self._nombre}: {coherencia:.1%}"
                )
        
        # Reportar solo conflictos reales (ingredientes de otras tradiciones no presentes en la actual)
        for conflicto in ingredientes_conflicto:
            advertencias.append(
                f"Ingrediente de tradición {conflicto['tradicion_conflicto']}: "
                f"{conflicto['ingrediente']}"
            )
        
        return ResultadoValidacion(
            valido=len(errores) == 0,
            errores=errores,
            advertencias=advertencias,
            detalles=detalles
        )
