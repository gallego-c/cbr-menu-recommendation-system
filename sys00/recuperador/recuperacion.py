"""
Módulo de Recuperación para Sistema CBR de Menús
================================================

Recupera casos similares de la base de conocimiento.
Soporta dos métodos:
- Similitud ponderada (por defecto): Combina similitudes locales con pesos
- Similitud vectorial: Vectoriza casos y usa métricas de distancia reales
"""

import json
import os
from typing import List, Dict, Optional, Any, NamedTuple
from enum import Enum

from conocimiento import Caso
from .similitud_ponderada import CalculadorSimilitudPonderada, PesosSimilitud
from .similitud_vectorial import CalculadorSimilitudVectorial, MetricaDistancia


class MetodoSimilitud(Enum):
    """Métodos de similitud disponibles."""
    PONDERADA = "ponderada"
    VECTORIAL = "vectorial"


class ResultadoRecuperacion(NamedTuple):
    """Resultado de una recuperación con similitud."""
    caso: Dict
    similitud: float
    explicacion: Dict[str, float] = {}
    indice: int = -1


class ModuloRecuperacion:
    """
    Módulo de recuperación de casos similares.
    
    Busca los k casos más similares usando la métrica configurada.
    """
    
    def __init__(self, 
                 metodo: MetodoSimilitud = MetodoSimilitud.PONDERADA,
                 pesos: PesosSimilitud = None,
                 metrica_distancia: MetricaDistancia = MetricaDistancia.EUCLIDIANA,
                 p_minkowski: float = 2.0):
        """
        Inicializa el módulo de recuperación.
        
        Args:
            metodo: Método de similitud a usar (PONDERADA o VECTORIAL)
            pesos: Pesos para método ponderado (opcional)
            metrica_distancia: Métrica para método vectorial
            p_minkowski: Parámetro p para Minkowski
        """
        self.metodo = metodo
        
        # Inicializar calculador según método
        if metodo == MetodoSimilitud.PONDERADA:
            self.calculador = CalculadorSimilitudPonderada(pesos)
        else:
            self.calculador = CalculadorSimilitudVectorial(metrica_distancia, p_minkowski)
        
        self.casos = []
        self._cargar_base_casos()
    
    def _cargar_base_casos(self):
        """Carga los casos de la base de conocimiento."""
        casos_path = os.path.join(os.path.dirname(__file__), '..', 'conocimiento', 'casos.json')
        
        try:
            with open(casos_path, 'r', encoding='utf-8') as f:
                self.casos = json.load(f)
        except FileNotFoundError:
            self.casos = []
        except json.JSONDecodeError:
            self.casos = []
    
    def recuperar(self, caso_nuevo: Dict, k: int = 3, umbral_minimo: float = 0.0,
                 explicar: bool = False) -> List[ResultadoRecuperacion]:
        """
        Recupera los k casos más similares al caso nuevo.
        
        Args:
            caso_nuevo: Diccionario con las características del caso a buscar
            k: Número de casos a recuperar (default: 3)
            umbral_minimo: Similitud mínima requerida (default: 0.0)
            explicar: Si incluir explicación detallada (default: False)
            
        Returns:
            Lista de ResultadoRecuperacion ordenados por similitud descendente
        """
        if not self.casos:
            return []
        
        # Calcular similitud con todos los casos y filtrar por umbral
        resultados = [
            ResultadoRecuperacion(
                caso=caso_base,
                similitud=sim,
                explicacion=self.calculador.explicar_similitud(caso_nuevo, caso_base) if explicar else {},
                indice=idx
            )
            for idx, caso_base in enumerate(self.casos)
            if (sim := self.calculador.similitud_casos(caso_nuevo, caso_base)) >= umbral_minimo
        ]
        
        # Ordenar y limitar
        resultados.sort(key=lambda x: x.similitud, reverse=True)
        return resultados[:k]
    
    def estadisticas_base_casos(self) -> Dict[str, Any]:
        """Proporciona estadísticas sobre la base de casos cargada."""
        if not self.casos:
            return {'total_casos': 0}
        
        from collections import Counter
        
        return {
            'total_casos': len(self.casos),
            'tipos_evento': dict(Counter(c.get('tipo_evento') for c in self.casos if c.get('tipo_evento'))),
            'temporadas': dict(Counter(c.get('temporada') for c in self.casos if c.get('temporada'))),
            'estilos': dict(Counter(c.get('estilo') for c in self.casos if c.get('estilo'))),
            'tradiciones': dict(Counter(c.get('tradicion') for c in self.casos if c.get('tradicion'))),
            'restricciones': dict(Counter(r for c in self.casos for r in c.get('restricciones', []))),
            'casos_exitosos': sum(1 for c in self.casos if c.get('exito', False))
        }