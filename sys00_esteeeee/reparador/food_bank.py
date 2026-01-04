"""
Módulo FoodBank - Gestiona la compatibilidad entre ingredientes
================================================================

Este módulo proporciona funcionalidad para:
- Evaluar si dos ingredientes son compatibles
- Encontrar sustituciones para ingredientes
- Calcular puntuaciones de compatibilidad
"""

import sys
import os
import json
from typing import List, Dict, Optional, Set, Tuple

# Añadir el directorio padre al path para importar models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from conocimiento.models import Ingrediente
from conocimiento import cargador


class FoodBank:
    """
    Gestiona la base de conocimiento sobre compatibilidad entre ingredientes.
    Permite evaluar compatibilidades y encontrar sustituciones apropiadas.
    """
    
    def __init__(self, archivo_food_bank: str = "food_bank.json"):
        """
        Inicializa el Food Bank cargando las compatibilidades.
        
        Args:
            archivo_food_bank: Archivo JSON con las compatibilidades
        """
        self.compatibilidades_data = cargador.cargar_json(archivo_food_bank)
        self.compatibilidades = self.compatibilidades_data.get('compatibilidades', {})
        self.incompatibilidades = self.compatibilidades_data.get('incompatibilidades', {})
        self.puntuaciones = self.compatibilidades_data.get('puntuaciones_compatibilidad', {})
        
        # Cargar base de datos de ingredientes para metadata
        ingredientes_lista = cargador.cargar_json("ingredientes.json")
        # Convertir lista a diccionario indexado por nombre
        self.ingredientes_db = {ing['nombre']: ing for ing in ingredientes_lista}
        
        # Crear índice inverso para búsqueda rápida
        self._crear_indice_compatibilidades()
    
    def _crear_indice_compatibilidades(self):
        """Crea un índice para búsqueda rápida de compatibilidades."""
        self.indice_compat = {}
        
        for categoria, ingredientes_dict in self.compatibilidades.items():
            for ingrediente, compatibles in ingredientes_dict.items():
                if ingrediente not in self.indice_compat:
                    self.indice_compat[ingrediente] = set()
                self.indice_compat[ingrediente].update(compatibles)
    
    def son_compatibles(self, ingrediente1: str, ingrediente2: str) -> Tuple[bool, float]:
        """
        Verifica si dos ingredientes son compatibles.
        
        Args:
            ingrediente1: Nombre del primer ingrediente
            ingrediente2: Nombre del segundo ingrediente
            
        Returns:
            Tuple (es_compatible: bool, puntuacion: float)
        """
        # Verificar incompatibilidades explícitas
        if self._son_incompatibles(ingrediente1, ingrediente2):
            return False, self.puntuaciones.get('incompatible', 0.0)
        
        # Verificar compatibilidad directa
        if ingrediente2 in self.indice_compat.get(ingrediente1, set()):
            return True, self.puntuaciones.get('combinacion_directa', 0.9)
        
        if ingrediente1 in self.indice_compat.get(ingrediente2, set()):
            return True, self.puntuaciones.get('combinacion_directa', 0.9)
        
        # Verificar si pertenecen a la misma categoría de sustitución
        if self._mismo_grupo_sustitucion(ingrediente1, ingrediente2):
            return True, self.puntuaciones.get('mismo_grupo', 1.0)
        
        # FALLBACK: Usar información de ingredientes_db (categoría, tradición)
        puntuacion_fallback = self._calcular_compatibilidad_por_metadata(ingrediente1, ingrediente2)
        if puntuacion_fallback > 0.5:
            return True, puntuacion_fallback
        
        # Sin incompatibilidad conocida - puntuación neutral
        return True, self.puntuaciones.get('sin_incompatibilidad', 0.5)
    
    def _son_incompatibles(self, ingrediente1: str, ingrediente2: str) -> bool:
        """
        Verifica si dos ingredientes son explícitamente incompatibles.
        
        Args:
            ingrediente1: Nombre del primer ingrediente
            ingrediente2: Nombre del segundo ingrediente
            
        Returns:
            True si son incompatibles
        """
        # Verificar incompatibilidades generales
        for par_incomp in self.incompatibilidades.get('general', []):
            if set([ingrediente1, ingrediente2]) == set(par_incomp):
                return True
            # También verificar si alguno contiene las palabras clave
            if (ingrediente1 in par_incomp[0] or par_incomp[0] in ingrediente1) and \
               (ingrediente2 in par_incomp[1] or par_incomp[1] in ingrediente2):
                return True
        
        return False
    
    def _mismo_grupo_sustitucion(self, ingrediente1: str, ingrediente2: str) -> bool:
        """
        Verifica si dos ingredientes pertenecen al mismo grupo de sustitución.
        
        Args:
            ingrediente1: Nombre del primer ingrediente
            ingrediente2: Nombre del segundo ingrediente
            
        Returns:
            True si pertenecen al mismo grupo
        """
        sustituciones = self.compatibilidades.get('sustituciones_por_categoria', {})
        
        for grupo, miembros in sustituciones.items():
            if ingrediente1 in miembros and ingrediente2 in miembros:
                return True
        
        return False
    
    def _calcular_compatibilidad_por_metadata(self, ingrediente1: str, ingrediente2: str) -> float:
        """
        Calcula compatibilidad entre ingredientes usando metadata (categoría, tradición).
        Usado como fallback cuando no hay compatibilidad explícita definida.
        
        Args:
            ingrediente1: Nombre del primer ingrediente
            ingrediente2: Nombre del segundo ingrediente
            
        Returns:
            Puntuación de compatibilidad (0.0 a 1.0)
        """
        info1 = self.ingredientes_db.get(ingrediente1)
        info2 = self.ingredientes_db.get(ingrediente2)
        
        if not info1 or not info2:
            return 0.5  # Puntuación neutral si no hay información
        
        puntuacion = 0.5  # Base neutral
        
        # Bonus si comparten categoría (ej: ambos vegetales, ambos condimentos)
        cat1 = info1.get('categoria', '')
        cat2 = info2.get('categoria', '')
        if cat1 and cat2 and cat1 == cat2:
            puntuacion += 0.15
        
        # Bonus si comparten tradición
        trad1 = set(info1.get('tradicion', []))
        trad2 = set(info2.get('tradicion', []))
        if trad1 and trad2:
            tradiciones_comunes = trad1.intersection(trad2)
            if tradiciones_comunes:
                puntuacion += 0.2  # Bonus significativo por tradición compartida
        
        # Bonus si comparten temporada (ingredientes de temporada similar combinan bien)
        temp1 = set(info1.get('temporada', []))
        temp2 = set(info2.get('temporada', []))
        if temp1 and temp2:
            temporadas_comunes = temp1.intersection(temp2)
            if temporadas_comunes:
                puntuacion += 0.1
        
        return min(puntuacion, 1.0)  # Limitar a máximo 1.0
    
    def encontrar_sustitutos(self, ingrediente_original: str, 
                           ingredientes_contexto: List[str],
                           max_sustitutos: int = 5) -> List[Tuple[str, float]]:
        """
        Encuentra sustitutos para un ingrediente que sean compatibles con el contexto.
        
        Args:
            ingrediente_original: Ingrediente que se quiere sustituir
            ingredientes_contexto: Otros ingredientes del plato/menú
            max_sustitutos: Número máximo de sustitutos a retornar
            
        Returns:
            Lista de tuplas (ingrediente_sustituto, puntuacion_compatibilidad)
            ordenadas por puntuación descendente
        """
        candidatos = []
        
        # 1. Buscar en el mismo grupo de sustitución
        sustituciones = self.compatibilidades.get('sustituciones_por_categoria', {})
        for grupo, miembros in sustituciones.items():
            if ingrediente_original in miembros:
                for candidato in miembros:
                    if candidato != ingrediente_original:
                        puntuacion = self._evaluar_sustituto(candidato, ingredientes_contexto)
                        candidatos.append((candidato, puntuacion))
        
        # 2. Buscar ingredientes compatibles directos
        if ingrediente_original in self.indice_compat:
            for candidato in self.indice_compat[ingrediente_original]:
                if not any(c[0] == candidato for c in candidatos):  # Evitar duplicados
                    puntuacion = self._evaluar_sustituto(candidato, ingredientes_contexto)
                    candidatos.append((candidato, puntuacion))
        
        # Ordenar por puntuación descendente y retornar los mejores
        candidatos.sort(key=lambda x: x[1], reverse=True)
        return candidatos[:max_sustitutos]
    
    def _evaluar_sustituto(self, ingrediente_sustituto: str, 
                          ingredientes_contexto: List[str]) -> float:
        """
        Evalúa qué tan bueno es un sustituto considerando el contexto.
        
        Args:
            ingrediente_sustituto: Candidato a sustituto
            ingredientes_contexto: Otros ingredientes del plato
            
        Returns:
            Puntuación de compatibilidad (0.0 a 1.0)
        """
        if not ingredientes_contexto:
            return 0.5
        
        puntuaciones = []
        for ingrediente_contexto in ingredientes_contexto:
            _, puntuacion = self.son_compatibles(ingrediente_sustituto, ingrediente_contexto)
            puntuaciones.append(puntuacion)
        
        # Retornar la puntuación promedio
        return sum(puntuaciones) / len(puntuaciones) if puntuaciones else 0.0
    
    def calcular_compatibilidad_plato(self, ingredientes: List[str]) -> float:
        """
        Calcula la compatibilidad general de todos los ingredientes de un plato.
        
        Args:
            ingredientes: Lista de nombres de ingredientes del plato
            
        Returns:
            Puntuación de compatibilidad promedio (0.0 a 1.0)
        """
        if len(ingredientes) < 2:
            return 1.0
        
        puntuaciones = []
        for i in range(len(ingredientes)):
            for j in range(i + 1, len(ingredientes)):
                _, puntuacion = self.son_compatibles(ingredientes[i], ingredientes[j])
                puntuaciones.append(puntuacion)
        
        return sum(puntuaciones) / len(puntuaciones) if puntuaciones else 0.0
    
    def calcular_compatibilidad(self, ingrediente: str, otros_ingredientes: List[str]) -> float:
        """
        Calcula la compatibilidad promedio de un ingrediente con una lista de otros ingredientes.
        
        Args:
            ingrediente: Ingrediente a evaluar
            otros_ingredientes: Lista de ingredientes con los que comparar
            
        Returns:
            Puntuación de compatibilidad promedio (0.0 a 1.0)
        """
        if not otros_ingredientes:
            return 1.0
        
        puntuaciones = []
        for otro in otros_ingredientes:
            _, puntuacion = self.son_compatibles(ingrediente, otro)
            puntuaciones.append(puntuacion)
        
        return sum(puntuaciones) / len(puntuaciones) if puntuaciones else 0.0
    
    def ingredientes_compatibles_con_grupo(self, ingrediente: str, 
                                          grupo_ingredientes: List[str],
                                          umbral_minimo: float = 0.5) -> bool:
        """
        Verifica si un ingrediente es compatible con un grupo de ingredientes.
        
        Args:
            ingrediente: Ingrediente a evaluar
            grupo_ingredientes: Grupo de ingredientes existentes
            umbral_minimo: Puntuación mínima requerida
            
        Returns:
            True si el ingrediente es suficientemente compatible
        """
        if not grupo_ingredientes:
            return True
        
        puntuacion = self._evaluar_sustituto(ingrediente, grupo_ingredientes)
        return puntuacion >= umbral_minimo
    
    def obtener_categorias_sustitucion(self) -> Dict[str, List[str]]:
        """
        Obtiene todas las categorías de sustitución disponibles.
        
        Returns:
            Diccionario con categorías y sus miembros
        """
        return self.compatibilidades.get('sustituciones_por_categoria', {})
    
    def buscar_categoria_ingrediente(self, ingrediente: str) -> Optional[str]:
        """
        Busca a qué categoría de sustitución pertenece un ingrediente.
        
        Args:
            ingrediente: Nombre del ingrediente
            
        Returns:
            Nombre de la categoría o None si no pertenece a ninguna
        """
        sustituciones = self.compatibilidades.get('sustituciones_por_categoria', {})
        
        for categoria, miembros in sustituciones.items():
            if ingrediente in miembros:
                return categoria
        
        return None
    
    def encontrar_sustitutos_vegetarianos(self, ingrediente_original: str,
                                         ingredientes_contexto: List[str],
                                         max_sustitutos: int = 5) -> List[Tuple[str, float]]:
        """
        Encuentra sustitutos vegetarianos específicos para carne/pescado.
        
        Args:
            ingrediente_original: Ingrediente de origen animal a sustituir
            ingredientes_contexto: Otros ingredientes del plato
            max_sustitutos: Número máximo de sustitutos a retornar
            
        Returns:
            Lista de tuplas (ingrediente_sustituto, puntuacion) ordenadas por puntuación
        """
        candidatos = []
        
        # Buscar en sustituciones vegetarianas específicas
        sustituciones_veg = self.compatibilidades.get('sustituciones_vegetarianas', {})
        
        if ingrediente_original in sustituciones_veg:
            for sustituto in sustituciones_veg[ingrediente_original]:
                # Evaluar compatibilidad con el contexto
                puntuacion = self._evaluar_sustituto(sustituto, ingredientes_contexto)
                # Dar puntuación extra por ser sustituto directo
                puntuacion = min(1.0, puntuacion + 0.2)
                candidatos.append((sustituto, puntuacion))
        
        # Si no hay sustituciones específicas, buscar en proteínas vegetarianas genéricas
        if not candidatos:
            proteinas_veg = self.compatibilidades.get('proteinas_vegetarianas', {})
            for proteina in proteinas_veg.keys():
                puntuacion = self._evaluar_sustituto(proteina, ingredientes_contexto)
                candidatos.append((proteina, puntuacion))
        
        # Ordenar por puntuación y retornar los mejores
        candidatos.sort(key=lambda x: x[1], reverse=True)
        return candidatos[:max_sustitutos]
    
    def encontrar_sustitutos_veganos(self, ingrediente_original: str,
                                    ingredientes_contexto: List[str],
                                    max_sustitutos: int = 5) -> List[Tuple[str, float]]:
        """
        Encuentra sustitutos veganos específicos para productos animales (carne, lácteos, huevos).
        
        Args:
            ingrediente_original: Ingrediente de origen animal a sustituir
            ingredientes_contexto: Otros ingredientes del plato
            max_sustitutos: Número máximo de sustitutos a retornar
            
        Returns:
            Lista de tuplas (ingrediente_sustituto, puntuacion) ordenadas por puntuación
        """
        candidatos = []
        
        # Buscar en sustituciones veganas específicas
        sustituciones_veg = self.compatibilidades.get('sustituciones_veganas', {})
        
        if ingrediente_original in sustituciones_veg:
            for sustituto in sustituciones_veg[ingrediente_original]:
                # Evaluar compatibilidad con el contexto
                puntuacion = self._evaluar_sustituto(sustituto, ingredientes_contexto)
                # Dar puntuación extra por ser sustituto directo
                puntuacion = min(1.0, puntuacion + 0.2)
                candidatos.append((sustituto, puntuacion))
        
        # Si no hay sustituciones específicas, buscar alternativas genéricas
        if not candidatos:
            # Buscar primero en proteínas vegetarianas para carnes
            proteinas_veg = self.compatibilidades.get('proteinas_vegetarianas', {})
            for proteina in proteinas_veg.keys():
                puntuacion = self._evaluar_sustituto(proteina, ingredientes_contexto)
                candidatos.append((proteina, puntuacion))
        
        # Ordenar por puntuación y retornar los mejores
        candidatos.sort(key=lambda x: x[1], reverse=True)
        return candidatos[:max_sustitutos]
