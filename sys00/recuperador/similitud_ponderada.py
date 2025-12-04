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
    tipo_evento: float = 0.25
    restricciones: float = 0.20
    temporada: float = 0.15
    estilo: float = 0.15
    tradicion: float = 0.15
    menu_ingredientes: float = 0.10
    
    def __post_init__(self):
        # Verificar que los pesos sumen aproximadamente 1.0
        total = sum([
            self.tipo_evento, self.restricciones, self.temporada,
            self.estilo, self.tradicion, self.menu_ingredientes
        ])
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Los pesos deben sumar 1.0, actual: {total}")


class CalculadorSimilitudPonderada:
    """
    Calculadora de similitud ponderada tradicional.
    
    Combina similitudes locales de cada atributo con pesos configurables.
    """
    
    def __init__(self, pesos: PesosSimilitud = None):
        """
        Inicializa el calculador.
        
        Args:
            pesos: Pesos para cada atributo
        """
        self.pesos = pesos or PesosSimilitud()
        self._cargar_conocimiento()
    
    def _cargar_conocimiento(self):
        """Carga el conocimiento de los archivos JSON."""
        conocimiento_dir = os.path.join(os.path.dirname(__file__), '..', 'conocimiento')
        
        # Cargar ingredientes
        with open(os.path.join(conocimiento_dir, 'ingredientes.json'), 'r', encoding='utf-8') as f:
            self.ingredientes_data = json.load(f)
        
        # Cargar platos
        with open(os.path.join(conocimiento_dir, 'platos.json'), 'r', encoding='utf-8') as f:
            self.platos_data = json.load(f)
        
        # Crear índices para búsqueda rápida
        self.ingredientes_por_nombre = {ing['nombre']: ing for ing in self.ingredientes_data}
        self.platos_por_nombre = {plato['nombre']: plato for plato in self.platos_data}
    
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
        
        # Similitud global ponderada
        similitud_total = (
            self.pesos.tipo_evento * sim_tipo +
            self.pesos.restricciones * sim_restricciones +
            self.pesos.temporada * sim_temporada +
            self.pesos.estilo * sim_estilo +
            self.pesos.tradicion * sim_tradicion +
            self.pesos.menu_ingredientes * sim_menu
        )
        
        return min(1.0, max(0.0, similitud_total))
    
    def _similitud_tipo_evento(self, tipo1: str, tipo2: str) -> float:
        """Calcula similitud entre tipos de evento."""
        if not tipo1 or not tipo2:
            return 0.0
        
        if tipo1 == tipo2:
            return 1.0
        
        # Similitudes específicas entre tipos de eventos
        similitudes_evento = {
            ('boda', 'congreso'): 0.6,
            ('congreso', 'boda'): 0.6,
            ('familiar', 'boda'): 0.3,
            ('boda', 'familiar'): 0.3,
            ('familiar', 'congreso'): 0.2,
            ('congreso', 'familiar'): 0.2,
        }
        
        return similitudes_evento.get((tipo1, tipo2), 0.0)
    
    def _similitud_restricciones(self, restricciones1: List[str], restricciones2: List[str]) -> float:
        """Calcula similitud entre listas de restricciones dietéticas."""
        if not restricciones1 and not restricciones2:
            return 1.0
        
        set1 = set(restricciones1)
        set2 = set(restricciones2)
        
        # Si el caso nuevo no tiene restricciones, cualquier caso es válido
        if not set1:
            return 1.0
        
        # Si el caso base cumple todas las restricciones del nuevo
        if set1.issubset(set2):
            return 1.0
        
        # Similitud de Jaccard
        if not set1 or not set2:
            return 0.0
        
        interseccion = len(set1 & set2)
        union = len(set1 | set2)
        
        return interseccion / union if union > 0 else 0.0
    
    def _similitud_temporada(self, temp1: str, temp2: str) -> float:
        """Calcula similitud entre temporadas."""
        if not temp1 or not temp2:
            return 0.0
        
        if temp1 == temp2:
            return 1.0
        
        # Similitudes entre temporadas adyacentes
        similitudes_temporada = {
            ('primavera', 'verano'): 0.7,
            ('verano', 'primavera'): 0.7,
            ('verano', 'otoño'): 0.7,
            ('otoño', 'verano'): 0.7,
            ('otoño', 'invierno'): 0.7,
            ('invierno', 'otoño'): 0.7,
            ('invierno', 'primavera'): 0.7,
            ('primavera', 'invierno'): 0.7,
            # Temporadas opuestas
            ('primavera', 'otoño'): 0.3,
            ('otoño', 'primavera'): 0.3,
            ('verano', 'invierno'): 0.3,
            ('invierno', 'verano'): 0.3,
        }
        
        return similitudes_temporada.get((temp1, temp2), 0.0)
    
    def _similitud_estilo(self, estilo1: str, estilo2: str) -> float:
        """Calcula similitud entre estilos culinarios."""
        if not estilo1 or not estilo2:
            return 0.0
        
        if estilo1 == estilo2:
            return 1.0
        
        return 0.3
    
    def _similitud_tradicion(self, trad1: str, trad2: str) -> float:
        """Calcula similitud entre tradiciones culturales."""
        if not trad1 or not trad2:
            return 0.0
        
        if trad1 == trad2:
            return 1.0
        
        return 0.2
    
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
        
        for tipo_plato in ['entrante', 'principal', 'postre']:
            nombre_plato = menu.get(tipo_plato)
            if nombre_plato and nombre_plato in self.platos_por_nombre:
                plato_info = self.platos_por_nombre[nombre_plato]
                for ingrediente in plato_info.get('ingredientes', []):
                    ingredientes.add(ingrediente)
        
        return ingredientes
    
    def _similitud_conjuntos(self, set1: Set[str], set2: Set[str]) -> float:
        """Calcula similitud de Jaccard entre dos conjuntos."""
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        interseccion = len(set1 & set2)
        union = len(set1 | set2)
        
        return interseccion / union if union > 0 else 0.0
    
    def _similitud_categorias_ingredientes(self, ingredientes1: Set[str], ingredientes2: Set[str]) -> float:
        """Calcula similitud basada en categorías de ingredientes."""
        categorias1 = self._obtener_categorias(ingredientes1)
        categorias2 = self._obtener_categorias(ingredientes2)
        
        return self._similitud_conjuntos(categorias1, categorias2)
    
    def _obtener_categorias(self, ingredientes: Set[str]) -> Set[str]:
        """Obtiene las categorías de un conjunto de ingredientes."""
        categorias = set()
        
        for ingrediente in ingredientes:
            if ingrediente in self.ingredientes_por_nombre:
                categoria = self.ingredientes_por_nombre[ingrediente].get('categoria')
                if categoria:
                    categorias.add(categoria)
        
        return categorias
    
    def explicar_similitud(self, caso_nuevo: Dict, caso_base: Dict) -> Dict[str, float]:
        """Proporciona explicación detallada de la similitud."""
        return {
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
            )
        }
