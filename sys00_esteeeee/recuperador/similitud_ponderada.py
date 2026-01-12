"""
Módulo de Similitud Ponderada para Sistema CBR de Menús
=======================================================

Calcula similitud combinando múltiples atributos con pesos configurables.
Enfoque clásico de CBR: similitud global = suma ponderada de similitudes locales.
"""

import json
import os
from typing import Dict, List, Set
from dataclasses import dataclass


@dataclass
class PesosSimilitud:
    """Configuración de pesos para el cálculo de similitud ponderada."""
    tipo_evento: float = 0.22
    restricciones: float = 0.18
    temporada: float = 0.15
    estilo: float = 0.15
    tradicion: float = 0.15
    menu_ingredientes: float = 0.10
    rating_quality: float = 0.05  # Peso para el rating de calidad del caso
    
    def __post_init__(self):
        # Verificar que los pesos sumen aproximadamente 1.0
        total = sum([
            self.tipo_evento, self.restricciones, self.temporada,
            self.estilo, self.tradicion, self.menu_ingredientes, self.rating_quality
        ])
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Los pesos deben sumar 1.0, actual: {total}")


class CalculadorSimilitudPonderada:
    """
    Calculadora de similitud ponderada tradicional.
    
    Combina similitudes locales de cada atributo con pesos configurables.
    """
    
    def __init__(self, pesos: PesosSimilitud = None, enable_rating_boost: bool = True):
        """
        Inicializa el calculador.
        
        Args:
            pesos: Pesos para cada atributo
            enable_rating_boost: Si activar boost/penalización por rating (default: True)
        """
        self.pesos = pesos or PesosSimilitud()
        self.enable_rating_boost = enable_rating_boost
        self._cargar_conocimiento()
    
    def _cargar_conocimiento(self):
        """Carga el conocimiento usando el cargador centralizado."""
        # Añadir el directorio padre al path para importar
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from conocimiento import cargador
        
        # Cargar usando el cargador centralizado
        ingredientes_dict = cargador.cargar_ingredientes()
        platos_dict = cargador.cargar_platos()
        
        # Convertir a listas para compatibilidad
        self.ingredientes_data = list(ingredientes_dict.values())
        self.platos_data = list(platos_dict.values())
        
        # Crear índices para búsqueda rápida
        self.ingredientes_por_nombre = ingredientes_dict
        self.platos_por_nombre = platos_dict
    
    def similitud_casos(self, caso_nuevo: Dict, caso_base: Dict) -> float:
        """
        Calcula la similitud total entre dos casos.
        
        Args:
            caso_nuevo: Diccionario con los datos del caso nuevo
            caso_base: Diccionario con los datos del caso base
            
        Returns:
            float: Similitud entre 0.0 y 1.0
        """
        # Calcular similitudes locales
        sim_tipo = self._similitud_tipo_evento(
            caso_nuevo.get('tipo_evento'),
            caso_base.get('tipo_evento')
        )
        
        sim_restricciones = self._similitud_restricciones(
            caso_nuevo.get('restricciones', []),
            caso_base.get('restricciones', [])
        )
        
        sim_temporada = self._similitud_temporada(
            caso_nuevo.get('temporada'),
            caso_base.get('temporada')
        )
        
        sim_estilo = self._similitud_estilo(
            caso_nuevo.get('estilo'),
            caso_base.get('estilo')
        )
        
        sim_tradicion = self._similitud_tradicion(
            caso_nuevo.get('tradicion'),
            caso_base.get('tradicion')
        )
        
        sim_menu = self._similitud_menu_ingredientes(
            caso_nuevo.get('menu', {}),
            caso_base.get('menu', {})
        )
        
        # Similitud de rating/calidad del caso base
        sim_rating = self._similitud_rating(caso_base)
        
        # Similitud global ponderada
        similitud_base = (
            self.pesos.tipo_evento * sim_tipo +
            self.pesos.restricciones * sim_restricciones +
            self.pesos.temporada * sim_temporada +
            self.pesos.estilo * sim_estilo +
            self.pesos.tradicion * sim_tradicion +
            self.pesos.menu_ingredientes * sim_menu +
            self.pesos.rating_quality * sim_rating
        )
        
        # Aplicar boost/penalización adicional basado en el rating si está habilitado
        if self.enable_rating_boost:
            boost_factor = self._calcular_boost_rating(caso_base)
            similitud_total = similitud_base * boost_factor
        else:
            similitud_total = similitud_base
        
        return min(1.0, max(0.0, similitud_total))
    
    # Tabla de similitudes entre tipos de eventos (constante de clase)
    _SIMILITUDES_EVENTO = {
        ('boda', 'congreso'): 0.6, ('congreso', 'boda'): 0.6,
        ('familiar', 'boda'): 0.3, ('boda', 'familiar'): 0.3,
        ('familiar', 'congreso'): 0.2, ('congreso', 'familiar'): 0.2,
    }
    
    def _similitud_tipo_evento(self, tipo1: str, tipo2: str) -> float:
        """Calcula similitud entre tipos de evento."""
        if not tipo1 or not tipo2:
            return 0.0
        return 1.0 if tipo1 == tipo2 else self._SIMILITUDES_EVENTO.get((tipo1, tipo2), 0.0)
    
    def _similitud_restricciones(self, restricciones1: List[str], restricciones2: List[str]) -> float:
        """Calcula similitud entre listas de restricciones dietéticas."""
        set1, set2 = set(restricciones1), set(restricciones2)
        
        # Sin restricciones o cumple todas
        if not set1 or set1.issubset(set2):
            return 1.0
        
        # Similitud de Jaccard
        interseccion = len(set1 & set2)
        union = len(set1 | set2)
        return interseccion / union if union > 0 else 0.0
    
    # Tabla de similitudes entre temporadas (constante de clase)
    _SIMILITUDES_TEMPORADA = {
        # Temporadas adyacentes
        ('primavera', 'verano'): 0.7, ('verano', 'primavera'): 0.7,
        ('verano', 'otoño'): 0.7, ('otoño', 'verano'): 0.7,
        ('otoño', 'invierno'): 0.7, ('invierno', 'otoño'): 0.7,
        ('invierno', 'primavera'): 0.7, ('primavera', 'invierno'): 0.7,
        # Temporadas opuestas
        ('primavera', 'otoño'): 0.3, ('otoño', 'primavera'): 0.3,
        ('verano', 'invierno'): 0.3, ('invierno', 'verano'): 0.3,
    }
    
    def _similitud_temporada(self, temp1: str, temp2: str) -> float:
        """Calcula similitud entre temporadas."""
        if not temp1 or not temp2:
            return 0.0
        return 1.0 if temp1 == temp2 else self._SIMILITUDES_TEMPORADA.get((temp1, temp2), 0.0)
    
    def _similitud_estilo(self, estilo1: str, estilo2: str) -> float:
        """Calcula similitud entre estilos culinarios."""
        if not estilo1 or not estilo2:
            return 0.0
        return 1.0 if estilo1 == estilo2 else 0.3
    
    def _similitud_tradicion(self, trad1: str, trad2: str) -> float:
        """Calcula similitud entre tradiciones culturales.
        
        Si alguna tradición es None/null, se considera compatible con cualquier tradición (1.0).
        Esto permite casos 'universales' que pueden adaptarse a cualquier tradición.
        """
        # Si alguna es None, son compatibles (tradición flexible/universal)
        if trad1 is None or trad2 is None:
            return 1.0
        return 1.0 if trad1 == trad2 else 0.2
    
    def _similitud_menu_ingredientes(self, menu1: Dict, menu2: Dict) -> float:
        """Calcula similitud basada en ingredientes de los menús."""
        if not menu1 or not menu2:
            return 0.0
        
        ingredientes1 = self._extraer_ingredientes_menu(menu1)
        ingredientes2 = self._extraer_ingredientes_menu(menu2)
        
        if not ingredientes1 or not ingredientes2:
            return 0.0
        
        # Similitud directa (Jaccard)
        sim_directa = self._similitud_conjuntos(ingredientes1, ingredientes2)
        
        # Similitud semántica por categorías
        sim_semantica = self._similitud_categorias_ingredientes(ingredientes1, ingredientes2)
        
        # Combinar (70% directa, 30% semántica)
        return 0.7 * sim_directa + 0.3 * sim_semantica
    
    def _extraer_ingredientes_menu(self, menu: Dict) -> Set[str]:
        """Extrae todos los ingredientes de un menú."""
        ingredientes = set()
        for tipo_plato in ('entrante', 'principal', 'postre'):
            if (nombre := menu.get(tipo_plato)) and (plato := self.platos_por_nombre.get(nombre)):
                ingredientes.update(plato.get('ingredientes', []))
        return ingredientes
    
    def _similitud_conjuntos(self, set1: Set[str], set2: Set[str]) -> float:
        """Calcula similitud de Jaccard entre dos conjuntos."""
        if not (set1 or set2):
            return 1.0
        if not (set1 and set2):
            return 0.0
        union = len(set1 | set2)
        return len(set1 & set2) / union if union > 0 else 0.0
    
    def _similitud_categorias_ingredientes(self, ingredientes1: Set[str], ingredientes2: Set[str]) -> float:
        """Calcula similitud basada en categorías de ingredientes."""
        categorias1 = {self.ingredientes_por_nombre[ing].get('categoria') 
                      for ing in ingredientes1 if ing in self.ingredientes_por_nombre}
        categorias2 = {self.ingredientes_por_nombre[ing].get('categoria') 
                      for ing in ingredientes2 if ing in self.ingredientes_por_nombre}
        categorias1.discard(None)
        categorias2.discard(None)
        return self._similitud_conjuntos(categorias1, categorias2)
    
    def _similitud_rating(self, caso_base: Dict) -> float:
        """
        Calcula componente de similitud basado en el rating del caso base.
        
        Rating alto (4.0-5.0) -> similitud alta (0.8-1.0)
        Rating medio (3.0-4.0) -> similitud media (0.5-0.8)
        Rating bajo (1.0-3.0) -> similitud baja (0.0-0.5)
        Sin rating -> neutral (0.6)
        
        Args:
            caso_base: Diccionario del caso base
            
        Returns:
            float: Similitud basada en rating (0.0-1.0)
        """
        rating = caso_base.get('satisfaction_score')
        
        if rating is None:
            # Sin rating: valor neutral
            return 0.6
        
        # Normalizar rating de escala 1-5 a 0-1
        # Rating 5.0 -> 1.0, Rating 3.0 -> 0.5, Rating 1.0 -> 0.0
        normalized = (rating - 1.0) / 4.0
        
        return max(0.0, min(1.0, normalized))
    
    def _calcular_boost_rating(self, caso_base: Dict) -> float:
        """
        Calcula factor de boost/penalización basado en el rating.
        
        Este factor multiplica la similitud base para dar preferencia
        a casos con rating alto y penalizar casos con rating bajo.
        
        Ratings altos (>=4.5): boost +15% (factor 1.15)
        Ratings buenos (4.0-4.5): boost +7% (factor 1.07)
        Ratings medios (3.5-4.0): neutral (factor 1.0)
        Ratings bajos (3.0-3.5): penalización -5% (factor 0.95)
        Ratings muy bajos (<3.0): penalización -15% (factor 0.85)
        Sin rating: neutral (factor 1.0)
        
        Args:
            caso_base: Diccionario del caso base
            
        Returns:
            float: Factor multiplicador (0.8-1.2)
        """
        rating = caso_base.get('satisfaction_score')
        
        if rating is None:
            return 1.0  # Neutral
        
        if rating >= 4.5:
            return 1.15  # Boost alto
        elif rating >= 4.0:
            return 1.07  # Boost moderado
        elif rating >= 3.5:
            return 1.0   # Neutral
        elif rating >= 3.0:
            return 0.95  # Penalización leve
        else:
            return 0.85  # Penalización moderada
    
    def explicar_similitud(self, caso_nuevo: Dict, caso_base: Dict) -> Dict[str, float]:
        """Proporciona explicación detallada de la similitud."""
        explicacion = {
            'tipo_evento': self._similitud_tipo_evento(
                caso_nuevo.get('tipo_evento'),
                caso_base.get('tipo_evento')
            ),
            'restricciones': self._similitud_restricciones(
                caso_nuevo.get('restricciones', []),
                caso_base.get('restricciones', [])
            ),
            'temporada': self._similitud_temporada(
                caso_nuevo.get('temporada'),
                caso_base.get('temporada')
            ),
            'estilo': self._similitud_estilo(
                caso_nuevo.get('estilo'),
                caso_base.get('estilo')
            ),
            'tradicion': self._similitud_tradicion(
                caso_nuevo.get('tradicion'),
                caso_base.get('tradicion')
            ),
            'menu_ingredientes': self._similitud_menu_ingredientes(
                caso_nuevo.get('menu', {}),
                caso_base.get('menu', {})
            ),
            'rating_quality': self._similitud_rating(caso_base)
        }
        
        # Añadir información del boost si está habilitado
        if self.enable_rating_boost:
            explicacion['rating_boost_factor'] = self._calcular_boost_rating(caso_base)
            rating = caso_base.get('satisfaction_score')
            if rating:
                explicacion['caso_rating'] = rating
        
        return explicacion

