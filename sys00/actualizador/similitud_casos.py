"""
Adaptador de Similitud para Retención de Casos
==============================================

Wrapper sobre la similitud existente (CalculadorSimilitudPonderada)
para proporcionar una interfaz estable y simétrica para la curación de memoria.

DECISIÓN DE DISEÑO:
- REUSAMOS la similitud ponderada existente en recuperador/similitud_ponderada.py
- Ya calcula Jaccard para sets + similitud semántica para ingredientes
- Devuelve [0,1], es determinista, sin dependencias externas
- Solo necesitamos un wrapper para garantizar simetría y normalización
"""

import os
import sys
from typing import Dict, List, Set, Any, Optional
import math

# Añadir directorio padre al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from recuperador.similitud_ponderada import CalculadorSimilitudPonderada


class SimilitudCasos:
    """
    Adaptador de similitud para comparar casos en el contexto de retención.
    
    Envuelve CalculadorSimilitudPonderada para:
    - Garantizar interfaz estable: similarity(caso_a, caso_b) -> float [0,1]
    - Asegurar simetría: sim(a,b) ≈ sim(b,a)
    - Proporcionar métodos adicionales para curación de memoria
    """
    
    def __init__(self):
        """Inicializa el calculador de similitud base."""
        self._calculador = CalculadorSimilitudPonderada()
    
    def similarity(self, caso_a: Dict[str, Any], caso_b: Dict[str, Any]) -> float:
        """
        Calcula la similitud entre dos casos.
        
        Args:
            caso_a: Primer caso (diccionario con campos del Caso)
            caso_b: Segundo caso (diccionario con campos del Caso)
            
        Returns:
            float en [0, 1] donde 1 = idénticos, 0 = completamente diferentes
        """
        # Usar el calculador existente (que ya devuelve [0,1])
        sim_ab = self._calculador.similitud_casos(caso_a, caso_b)
        
        # Para garantizar simetría, promediamos ambas direcciones
        # (aunque en teoría debería ser simétrico, lo hacemos por robustez)
        sim_ba = self._calculador.similitud_casos(caso_b, caso_a)
        
        return (sim_ab + sim_ba) / 2.0
    
    def similarity_to_set(self, caso: Dict[str, Any], casos_memoria: List[Dict[str, Any]]) -> List[float]:
        """
        Calcula la similitud de un caso contra todos los casos en memoria.
        
        Args:
            caso: Caso a comparar
            casos_memoria: Lista de casos en memoria
            
        Returns:
            Lista de similitudes [0,1] en el mismo orden que casos_memoria
        """
        return [self.similarity(caso, caso_mem) for caso_mem in casos_memoria]
    
    def max_similarity(self, caso: Dict[str, Any], casos_memoria: List[Dict[str, Any]]) -> float:
        """
        Calcula la máxima similitud de un caso contra la memoria.
        
        Args:
            caso: Caso a evaluar
            casos_memoria: Lista de casos existentes
            
        Returns:
            Máxima similitud encontrada, o 0.0 si memoria vacía
        """
        if not casos_memoria:
            return 0.0
        
        similitudes = self.similarity_to_set(caso, casos_memoria)
        return max(similitudes)
    
    def novelty(self, caso: Dict[str, Any], casos_memoria: List[Dict[str, Any]]) -> float:
        """
        Calcula la novedad de un caso respecto a la memoria.
        
        novelty = 1 - max_similarity(caso, memoria)
        
        Args:
            caso: Caso a evaluar
            casos_memoria: Lista de casos existentes
            
        Returns:
            float en [0, 1] donde 1 = totalmente novedoso, 0 = duplicado exacto
        """
        if not casos_memoria:
            return 1.0
        
        return 1.0 - self.max_similarity(caso, casos_memoria)
    
    def find_near_duplicates(self, casos: List[Dict[str, Any]], 
                             threshold: float = 0.9) -> List[List[int]]:
        """
        Encuentra clusters de casos casi-duplicados.
        
        Args:
            casos: Lista de casos
            threshold: Umbral de similitud para considerar duplicados
            
        Returns:
            Lista de clusters (cada cluster es una lista de índices)
        """
        n = len(casos)
        if n == 0:
            return []
        
        # Calcular matriz de adyacencia de "casi-duplicados"
        visited = [False] * n
        clusters = []
        
        for i in range(n):
            if visited[i]:
                continue
            
            # Iniciar nuevo cluster con caso i
            cluster = [i]
            visited[i] = True
            
            # Buscar todos los casos similares a este cluster
            for j in range(i + 1, n):
                if visited[j]:
                    continue
                
                # Ver si j es similar a algún miembro del cluster
                for k in cluster:
                    if self.similarity(casos[k], casos[j]) >= threshold:
                        cluster.append(j)
                        visited[j] = True
                        break
            
            if len(cluster) > 1:  # Solo guardar clusters con duplicados
                clusters.append(cluster)
        
        return clusters
    
    def explain_similarity(self, caso_a: Dict[str, Any], caso_b: Dict[str, Any]) -> Dict[str, float]:
        """
        Proporciona una explicación detallada de la similitud entre dos casos.
        
        Returns:
            Diccionario con similitud por componente
        """
        return self._calculador.explicar_similitud(caso_a, caso_b)


class SimilitudMenus:
    """
    Calculador de similitud específico para menús (entrante, principal, postre).
    
    Útil para comparar menús independientemente del contexto del caso.
    """
    
    def __init__(self):
        """Inicializa con acceso al conocimiento de platos e ingredientes."""
        from conocimiento import cargador
        self.platos_db = cargador.cargar_platos()
        self.ingredientes_db = cargador.cargar_ingredientes()
    
    def similarity(self, menu_a: Dict[str, str], menu_b: Dict[str, str]) -> float:
        """
        Calcula similitud entre dos menús.
        
        Args:
            menu_a: Dict con 'entrante', 'principal', 'postre'
            menu_b: Dict con 'entrante', 'principal', 'postre'
            
        Returns:
            float en [0, 1]
        """
        # Similitud por coincidencia de platos
        sim_directa = self._similitud_platos_directa(menu_a, menu_b)
        
        # Similitud por ingredientes compartidos
        sim_ingredientes = self._similitud_ingredientes(menu_a, menu_b)
        
        # Combinar (60% platos, 40% ingredientes)
        return 0.6 * sim_directa + 0.4 * sim_ingredientes
    
    def _similitud_platos_directa(self, menu_a: Dict, menu_b: Dict) -> float:
        """Cuenta cuántos platos coinciden exactamente."""
        coincidencias = 0
        total = 3  # entrante, principal, postre
        
        for tipo in ['entrante', 'principal', 'postre']:
            if menu_a.get(tipo) == menu_b.get(tipo):
                coincidencias += 1
        
        return coincidencias / total
    
    def _similitud_ingredientes(self, menu_a: Dict, menu_b: Dict) -> float:
        """Calcula similitud Jaccard de ingredientes."""
        ing_a = self._extraer_ingredientes(menu_a)
        ing_b = self._extraer_ingredientes(menu_b)
        
        if not ing_a and not ing_b:
            return 1.0
        if not ing_a or not ing_b:
            return 0.0
        
        interseccion = len(ing_a & ing_b)
        union = len(ing_a | ing_b)
        
        return interseccion / union if union > 0 else 0.0
    
    def _extraer_ingredientes(self, menu: Dict) -> Set[str]:
        """Extrae todos los ingredientes de un menú."""
        ingredientes = set()
        
        for tipo in ['entrante', 'principal', 'postre']:
            nombre_plato = menu.get(tipo, '')
            if not nombre_plato:
                continue
            
            plato_info = self.platos_db.get(nombre_plato)
            if plato_info:
                ingredientes.update(plato_info.get('ingredientes', []))
        
        return ingredientes
