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
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from .similitud_ponderada import CalculadorSimilitudPonderada, PesosSimilitud
from .similitud_vectorial import CalculadorSimilitudVectorial, MetricaDistancia


class MetodoSimilitud(Enum):
    """Métodos de similitud disponibles."""
    PONDERADA = "ponderada"      # Similitud ponderada clásica (por defecto)
    VECTORIAL = "vectorial"      # Similitud basada en vectorización


@dataclass
class ResultadoRecuperacion:
    """Representa el resultado de una operación de recuperación."""
    caso: Dict
    similitud: float
    explicacion: Dict[str, float] = field(default_factory=dict)
    indice_original: int = -1


@dataclass
class ConfiguracionRecuperacion:
    """Configuración para el proceso de recuperación."""
    k: int = 3  # Número de casos a recuperar
    umbral_minimo: float = 0.0  # Similitud mínima requerida
    explicar_similitud: bool = False  # Si incluir explicación detallada
    
    # Configuración de método de similitud
    metodo: MetodoSimilitud = MetodoSimilitud.PONDERADA  # Método de cálculo (por defecto: ponderada)
    
    # Configuración para método PONDERADA
    pesos_similitud: Optional[PesosSimilitud] = None
    
    # Configuración para método VECTORIAL
    metrica_distancia: MetricaDistancia = MetricaDistancia.EUCLIDIANA
    p_minkowski: float = 2.0  # Parámetro p para Minkowski


class ModuloRecuperacion:
    """
    Módulo de recuperación de casos similares.
    
    Busca los k casos más similares usando la métrica configurada.
    Simple y directo sin filtros complejos.
    """
    
    def __init__(self, config: ConfiguracionRecuperacion = None):
        """
        Inicializa el módulo de recuperación.
        
        Args:
            config: Configuración del módulo
        """
        self.config = config or ConfiguracionRecuperacion()
        
        # Inicializar calculador según método elegido
        if self.config.metodo == MetodoSimilitud.PONDERADA:
            self.calculador = CalculadorSimilitudPonderada(
                pesos=self.config.pesos_similitud
            )
        else:  # VECTORIAL
            self.calculador = CalculadorSimilitudVectorial(
                metrica=self.config.metrica_distancia,
                p_minkowski=self.config.p_minkowski
            )
        
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
    
    def recuperar(self, caso_nuevo: Dict, config_personalizada: ConfiguracionRecuperacion = None) -> List[ResultadoRecuperacion]:
        """
        Recupera los k casos más similares al caso nuevo.
        
        Calcula similitud con TODOS los casos y retorna los k mejores.
        No aplica filtros previos.
        
        Args:
            caso_nuevo: Diccionario con las características del caso a buscar
            config_personalizada: Configuración específica para esta búsqueda
            
        Returns:
            Lista de ResultadoRecuperacion ordenados por similitud descendente
        """
        config = config_personalizada or self.config
        
        if not self.casos:
            return []
        
        # Calcular similitud con TODOS los casos
        resultados = []
        for idx, caso_base in enumerate(self.casos):
            similitud = self.calculador.similitud_casos(caso_nuevo, caso_base)
            
            # Filtrar solo por umbral mínimo
            if similitud >= config.umbral_minimo:
                resultado = ResultadoRecuperacion(
                    caso=caso_base,
                    similitud=similitud,
                    indice_original=idx
                )
                
                # Agregar explicación si se solicita
                if config.explicar_similitud:
                    resultado.explicacion = self.calculador.explicar_similitud(caso_nuevo, caso_base)
                
                resultados.append(resultado)
        
        # Ordenar por similitud descendente
        resultados.sort(key=lambda x: x.similitud, reverse=True)
        
        # Limitar a k resultados
        return resultados[:config.k]
    
    def estadisticas_base_casos(self) -> Dict[str, Any]:
        """
        Proporciona estadísticas sobre la base de casos cargada.
        
        Returns:
            Diccionario con estadísticas de la base de casos
        """
        if not self.casos:
            return {'total_casos': 0}
        
        estadisticas = {
            'total_casos': len(self.casos),
            'tipos_evento': {},
            'temporadas': {},
            'estilos': {},
            'tradiciones': {},
            'restricciones': {},
            'casos_exitosos': 0
        }
        
        for caso in self.casos:
            # Contar tipos de evento
            tipo = caso.get('tipo_evento')
            if tipo:
                estadisticas['tipos_evento'][tipo] = estadisticas['tipos_evento'].get(tipo, 0) + 1
            
            # Contar temporadas
            temporada = caso.get('temporada')
            if temporada:
                estadisticas['temporadas'][temporada] = estadisticas['temporadas'].get(temporada, 0) + 1
            
            # Contar estilos
            estilo = caso.get('estilo')
            if estilo:
                estadisticas['estilos'][estilo] = estadisticas['estilos'].get(estilo, 0) + 1
            
            # Contar tradiciones
            tradicion = caso.get('tradicion')
            if tradicion:
                estadisticas['tradiciones'][tradicion] = estadisticas['tradiciones'].get(tradicion, 0) + 1
            
            # Contar restricciones
            for restriccion in caso.get('restricciones', []):
                estadisticas['restricciones'][restriccion] = estadisticas['restricciones'].get(restriccion, 0) + 1
            
            # Contar casos exitosos
            if caso.get('exito', False):
                estadisticas['casos_exitosos'] += 1
        
        return estadisticas