"""
Módulo de Similitud Vectorial para Sistema CBR de Menús
=======================================================

Vectoriza los casos y calcula distancias métricas reales.
Soporta múltiples métricas: Euclidiana, Manhattan, Minkowski, Canberra, Clark, Coseno, etc.
"""

import json
import os
import math
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class MetricaDistancia(Enum):
    """Métricas de distancia disponibles."""
    EUCLIDIANA = "euclidiana"      # L2, Minkowski p=2
    MANHATTAN = "manhattan"        # L1, Minkowski p=1
    CHEBYSHEV = "chebyshev"        # L∞, Minkowski p=infinito
    MINKOWSKI = "minkowski"        # Lp genérica
    CANBERRA = "canberra"          # Suma ponderada de diferencias
    CLARK = "clark"                # Distancia de Clark
    COSENO = "coseno"              # Similitud del coseno


class CalculadorSimilitudVectorial:
    """
    Calculadora de similitud basada en vectorización y distancias métricas.
    
    Convierte casos a vectores numéricos y aplica métricas de distancia reales.
    """
    
    def __init__(self, 
                 metrica: MetricaDistancia = MetricaDistancia.EUCLIDIANA,
                 p_minkowski: float = 2.0):
        """
        Inicializa el calculador.
        
        Args:
            metrica: Métrica de distancia a utilizar
            p_minkowski: Parámetro p para distancia de Minkowski
        """
        self.metrica = metrica
        self.p_minkowski = p_minkowski
        self._cargar_conocimiento()
        self._inicializar_codificaciones()
    
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
        
        # Crear índices
        self.ingredientes_por_nombre = ingredientes_dict
        self.platos_por_nombre = platos_dict
    
    def _inicializar_codificaciones(self):
        """Inicializa los mapeos de valores categóricos a numéricos."""
        # Codificación de tipos de evento
        self.tipo_evento_map = {
            'familiar': 0,
            'boda': 1,
            'congreso': 2,
            'corporativo': 3
        }
        
        # Codificación de temporadas (ordinal cíclico)
        self.temporada_map = {
            'primavera': 0,
            'verano': 1,
            'otoño': 2,
            'invierno': 3
        }
        
        # Codificación de estilos
        self.estilo_map = {
            'clasico': 0,
            'molecular': 1,
            'fusion': 2
        }
        
        # Codificación de tradiciones
        self.tradicion_map = {
            'catalana': 0,
            'mexicana': 1,
            'italiana': 2,
            'francesa': 3,
            'japonesa': 4
        }
        
        # Crear vocabulario de ingredientes para one-hot encoding
        self.ingredientes_vocabulario = {ing['nombre']: idx 
                                        for idx, ing in enumerate(self.ingredientes_data)}
        
        # Crear vocabulario de restricciones
        self.restricciones_vocabulario = {
            'vegano': 0,
            'vegetariano': 1,
            'sin_gluten': 2,
            'sin_lactosa': 3,
            'sin_frutos_secos': 4
        }
    
    def similitud_casos(self, caso_nuevo: Dict, caso_base: Dict) -> float:
        """
        Calcula la similitud entre dos casos usando vectorización.
        
        Args:
            caso_nuevo: Diccionario con los datos del caso nuevo
            caso_base: Diccionario con los datos del caso base
            
        Returns:
            float: Similitud entre 0.0 y 1.0
        """
        # Vectorizar ambos casos
        vector_nuevo = self._vectorizar_caso(caso_nuevo)
        vector_base = self._vectorizar_caso(caso_base)
        
        # Calcular distancia según métrica
        if self.metrica == MetricaDistancia.EUCLIDIANA:
            distancia = self._distancia_euclidiana(vector_nuevo, vector_base)
        elif self.metrica == MetricaDistancia.MANHATTAN:
            distancia = self._distancia_manhattan(vector_nuevo, vector_base)
        elif self.metrica == MetricaDistancia.CHEBYSHEV:
            distancia = self._distancia_chebyshev(vector_nuevo, vector_base)
        elif self.metrica == MetricaDistancia.MINKOWSKI:
            distancia = self._distancia_minkowski(vector_nuevo, vector_base, self.p_minkowski)
        elif self.metrica == MetricaDistancia.CANBERRA:
            distancia = self._distancia_canberra(vector_nuevo, vector_base)
        elif self.metrica == MetricaDistancia.CLARK:
            distancia = self._distancia_clark(vector_nuevo, vector_base)
        elif self.metrica == MetricaDistancia.COSENO:
            # Coseno devuelve directamente similitud
            return self._similitud_coseno(vector_nuevo, vector_base)
        else:
            distancia = self._distancia_euclidiana(vector_nuevo, vector_base)
        
        # Convertir distancia a similitud (1 / (1 + distancia))
        similitud = 1.0 / (1.0 + distancia)
        return similitud
    
    def _vectorizar_caso(self, caso: Dict) -> List[float]:
        """
        Convierte un caso a vector numérico.
        
        Vector resultante:
        [tipo_evento, temporada_sin, temporada_cos, estilo, tradicion, 
         restriccion_1, ..., restriccion_n, ingrediente_1, ..., ingrediente_m]
        """
        vector = []
        
        # 1. Tipo de evento (ordinal normalizado)
        tipo = caso.get('tipo_evento', 'familiar')
        vector.append(self.tipo_evento_map.get(tipo, 0) / len(self.tipo_evento_map))
        
        # 2. Temporada (codificación cíclica: sin y cos para capturar circularidad)
        temp = caso.get('temporada', 'verano')
        temp_idx = self.temporada_map.get(temp, 0)
        angulo = 2 * math.pi * temp_idx / 4  # 4 temporadas
        vector.append(math.sin(angulo))
        vector.append(math.cos(angulo))
        
        # 3. Estilo (ordinal normalizado)
        estilo = caso.get('estilo', 'clasico')
        vector.append(self.estilo_map.get(estilo, 0) / len(self.estilo_map))
        
        # 4. Tradición (ordinal normalizado)
        tradicion = caso.get('tradicion', 'catalana')
        vector.append(self.tradicion_map.get(tradicion, 0) / len(self.tradicion_map))
        
        # 5. Restricciones (one-hot encoding)
        restricciones = set(caso.get('restricciones', []))
        for restriccion in self.restricciones_vocabulario.keys():
            vector.append(1.0 if restriccion in restricciones else 0.0)
        
        # 6. Ingredientes del menú (one-hot encoding reducido)
        ingredientes_menu = self._extraer_ingredientes_menu(caso.get('menu', {}))
        # Usar solo los 50 ingredientes más comunes para evitar vectores enormes
        ingredientes_importantes = list(self.ingredientes_vocabulario.keys())[:50]
        for ingrediente in ingredientes_importantes:
            vector.append(1.0 if ingrediente in ingredientes_menu else 0.0)
        
        return vector
    
    def _extraer_ingredientes_menu(self, menu: Dict) -> set:
        """Extrae los ingredientes de un menú."""
        ingredientes = set()
        for tipo_plato in ['entrante', 'principal', 'postre']:
            nombre_plato = menu.get(tipo_plato)
            if nombre_plato and nombre_plato in self.platos_por_nombre:
                plato_info = self.platos_por_nombre[nombre_plato]
                ingredientes.update(plato_info.get('ingredientes', []))
        return ingredientes
    
    # ===== MÉTRICAS DE DISTANCIA =====
    
    def _distancia_euclidiana(self, v1: List[float], v2: List[float]) -> float:
        """Distancia euclidiana (L2)."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))
    
    def _distancia_manhattan(self, v1: List[float], v2: List[float]) -> float:
        """Distancia Manhattan (L1)."""
        return sum(abs(a - b) for a, b in zip(v1, v2))
    
    def _distancia_chebyshev(self, v1: List[float], v2: List[float]) -> float:
        """Distancia Chebyshev (L∞)."""
        return max(abs(a - b) for a, b in zip(v1, v2))
    
    def _distancia_minkowski(self, v1: List[float], v2: List[float], p: float) -> float:
        """Distancia de Minkowski (Lp)."""
        return sum(abs(a - b) ** p for a, b in zip(v1, v2)) ** (1.0 / p)
    
    def _distancia_canberra(self, v1: List[float], v2: List[float]) -> float:
        """Distancia de Canberra."""
        distancia = 0.0
        for a, b in zip(v1, v2):
            denominador = abs(a) + abs(b)
            if denominador > 1e-10:
                distancia += abs(a - b) / denominador
        return distancia
    
    def _distancia_clark(self, v1: List[float], v2: List[float]) -> float:
        """Distancia de Clark."""
        distancia_cuadrada = 0.0
        for a, b in zip(v1, v2):
            denominador = abs(a) + abs(b)
            if denominador > 1e-10:
                distancia_cuadrada += ((a - b) / denominador) ** 2
        return math.sqrt(distancia_cuadrada)
    
    def _similitud_coseno(self, v1: List[float], v2: List[float]) -> float:
        """Similitud del coseno."""
        producto_punto = sum(a * b for a, b in zip(v1, v2))
        magnitud_v1 = math.sqrt(sum(a ** 2 for a in v1))
        magnitud_v2 = math.sqrt(sum(b ** 2 for b in v2))
        
        if magnitud_v1 * magnitud_v2 < 1e-10:
            return 0.0
        
        return producto_punto / (magnitud_v1 * magnitud_v2)
    
    def explicar_similitud(self, caso_nuevo: Dict, caso_base: Dict) -> Dict[str, float]:
        """
        Proporciona explicación de la similitud vectorial.
        
        Devuelve las contribuciones de cada grupo de features.
        """
        vector_nuevo = self._vectorizar_caso(caso_nuevo)
        vector_base = self._vectorizar_caso(caso_base)
        
        # Calcular contribuciones por secciones
        idx = 0
        explicacion = {}
        
        # Tipo evento (1 feature)
        explicacion['tipo_evento'] = 1.0 - abs(vector_nuevo[idx] - vector_base[idx])
        idx += 1
        
        # Temporada (2 features: sin, cos)
        dist_temp = math.sqrt((vector_nuevo[idx] - vector_base[idx])**2 + 
                             (vector_nuevo[idx+1] - vector_base[idx+1])**2)
        explicacion['temporada'] = 1.0 - min(1.0, dist_temp / math.sqrt(2))
        idx += 2
        
        # Estilo (1 feature)
        explicacion['estilo'] = 1.0 - abs(vector_nuevo[idx] - vector_base[idx])
        idx += 1
        
        # Tradición (1 feature)
        explicacion['tradicion'] = 1.0 - abs(vector_nuevo[idx] - vector_base[idx])
        idx += 1
        
        # Restricciones (n features)
        n_restricciones = len(self.restricciones_vocabulario)
        dist_restricciones = sum(abs(vector_nuevo[idx+i] - vector_base[idx+i]) 
                                for i in range(n_restricciones))
        explicacion['restricciones'] = 1.0 - min(1.0, dist_restricciones / n_restricciones)
        idx += n_restricciones
        
        # Ingredientes (m features)
        n_ingredientes = 50
        dist_ingredientes = sum(abs(vector_nuevo[idx+i] - vector_base[idx+i]) 
                               for i in range(n_ingredientes))
        explicacion['menu_ingredientes'] = 1.0 - min(1.0, dist_ingredientes / n_ingredientes)
        
        return explicacion
