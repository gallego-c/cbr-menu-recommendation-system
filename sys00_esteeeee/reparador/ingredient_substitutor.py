"""
Módulo para sustituir ingredientes individuales de un plato
===========================================================

Este módulo intenta reparar un plato sustituyendo ingredientes problemáticos
por alternativas compatibles antes de recurrir a sustituir el plato completo.

NOTA: Este módulo trabaja con la estructura de Plato definida en models.py:
- Plato.ingredientes es List[str] (lista de nombres de ingredientes)
- Usa FoodBank como fuente central para sustituciones y verificación de restricciones
"""

import sys
import os
from typing import List, Dict, Optional, Any, Tuple

# Añadir el directorio padre al path para importar models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from conocimiento.models import Plato, Menu
from conocimiento import cargador
from .food_bank import FoodBank

# Control de debug (se puede activar desde fuera)
_DEBUG_MODE = False


def set_debug_mode(enabled: bool):
    """Activa o desactiva el modo debug."""
    global _DEBUG_MODE
    _DEBUG_MODE = enabled


def _debug_print(*args, **kwargs):
    """Imprime solo si el modo debug está activado."""
    if _DEBUG_MODE:
        print(*args, **kwargs)


class IngredientSubstitutor:
    """
    Clase para sustituir ingredientes individuales de un plato problemático
    usando el Food Bank como fuente centralizada para encontrar sustituciones compatibles.
    """
    
    def __init__(self):
        """Inicializa el sustituto de ingredientes con el Food Bank centralizado."""
        self.food_bank = FoodBank()
        self.tradiciones_db = cargador.cargar_tradiciones()
        self.cargador = cargador
    
    @property
    def ingredientes_db(self) -> Dict:
        """Acceso a ingredientes_db a través de FoodBank (evita duplicación)."""
        return self.food_bank.ingredientes_db
    
    def intentar_reparacion_por_ingredientes(self, plato: Plato, menu: Menu,
                                            tipo_problema: str, 
                                            problema_especifico: str) -> Dict[str, Any]:
        """
        Intenta reparar un plato sustituyendo ingredientes problemáticos.
        
        Args:
            plato: Plato que necesita reparación
            menu: Menú completo con preferencias
            tipo_problema: Tipo de problema (restricciones, temporada, etc.)
            problema_especifico: Descripción específica del problema
            
        Returns:
            Diccionario con resultado de la reparación:
            {
                'exito': bool,
                'plato_modificado': Plato o None,
                'ingredientes_sustituidos': List[Tuple[str, str]],  # (original, sustituto)
                'mensajes': List[str]
            }
        """
        # Identificar ingredientes problemáticos según el tipo de problema
        ingredientes_problematicos = self._identificar_ingredientes_problematicos(
            plato, menu, tipo_problema, problema_especifico
        )
        

        
        if not ingredientes_problematicos:
            return {
                'exito': False,
                'plato_modificado': None,
                'ingredientes_sustituidos': [],
                'mensajes': ['No se pudieron identificar ingredientes problemáticos específicos']
            }
        
        # Intentar sustituir cada ingrediente problemático
        sustituciones_exitosas = []
        sustituciones_fallidas = []
        plato_modificado = self._clonar_plato(plato)
        
        # Para problemas de tradición, solo necesitamos alcanzar el 20% mínimo
        es_problema_tradicion = tipo_problema == 'tradicion' or 'tradición' in tipo_problema
        
        for nombre_ingrediente_prob in ingredientes_problematicos:
            # Si es problema de tradición, verificar si ya alcanzamos el mínimo
            if es_problema_tradicion and sustituciones_exitosas:
                if self._verificar_porcentaje_tradicion(plato_modificado, menu):
                    break
            
            resultado_sustitucion = self._sustituir_ingrediente(
                nombre_ingrediente_prob, 
                plato_modificado,
                menu,
                tipo_problema  # Pasar el tipo de problema para sustituciones específicas
            )
            
            if resultado_sustitucion['exito']:
                sustituciones_exitosas.append(
                    (nombre_ingrediente_prob, resultado_sustitucion['sustituto'])
                )
                # Aplicar la sustitución al plato
                self._aplicar_sustitucion(plato_modificado, nombre_ingrediente_prob, 
                                        resultado_sustitucion['sustituto'])
            else:
                sustituciones_fallidas.append(nombre_ingrediente_prob)
        
        # Verificar si se lograron hacer suficientes sustituciones
        if sustituciones_exitosas:
            # Verificar que el plato modificado cumpla con las preferencias
            # Y que las sustituciones tengan sentido culinario
            if self._validar_plato_modificado(plato_modificado, menu):
                # Verificar coherencia de sabores (no mezclar dulce con picante, etc.)
                if self._validar_coherencia_sabores(plato_modificado):
                    return {
                        'exito': True,
                        'plato_modificado': plato_modificado,
                        'ingredientes_sustituidos': sustituciones_exitosas,
                        'mensajes': [
                            f'Sustituciones exitosas: {len(sustituciones_exitosas)}',
                            *[f'{orig} -> {sust}' for orig, sust in sustituciones_exitosas]
                        ]
                    }
                else:
                    return {
                        'exito': False,
                        'plato_modificado': None,
                        'ingredientes_sustituidos': [],
                        'mensajes': [
                            'Las sustituciones crean combinaciones de sabores incoherentes',
                            'Mejor cambiar el plato completo'
                        ]
                    }
        
        return {
            'exito': False,
            'plato_modificado': None,
            'ingredientes_sustituidos': [],
            'mensajes': [
                f'No se pudo reparar el plato sustituyendo ingredientes',
                f'Intentos exitosos: {len(sustituciones_exitosas)}',
                f'Intentos fallidos: {len(sustituciones_fallidas)}',
                'Se recomienda cambiar el plato completo'
            ]
        }
    
    def _identificar_ingredientes_problematicos(self, plato: Plato, menu: Menu,
                                               tipo_problema: str, 
                                               problema_especifico: str) -> List[str]:
        """
        Identifica qué ingredientes del plato están causando el problema.
        
        Args:
            plato: Plato a analizar
            menu: Menú con preferencias
            tipo_problema: Tipo de problema
            problema_especifico: Descripción específica
            
        Returns:
            Lista de nombres de ingredientes problemáticos
        """
        problematicos = []
        
        if tipo_problema == 'restricciones':
            # Identificar ingredientes que violan restricciones
            problematicos = self._ingredientes_violan_restricciones(plato, menu)
        
        elif tipo_problema == 'temporada':
            # Identificar ingredientes fuera de temporada
            problematicos = self._ingredientes_fuera_temporada(plato, menu)
        
        elif tipo_problema == 'coherencia':
            # Identificar ingredientes incompatibles entre sí
            problematicos = self._ingredientes_incoherentes(plato)
        
        elif tipo_problema == 'tradicion' or 'tradición' in tipo_problema:
            # Identificar ingredientes que NO son de la tradición requerida
            problematicos = self._ingredientes_fuera_tradicion(plato, menu)
        
        return problematicos
    
    def _ingredientes_violan_restricciones(self, plato: Plato, menu: Menu) -> List[str]:
        """Identifica ingredientes que violan restricciones dietéticas.
        Usa FoodBank como fuente centralizada para verificación de restricciones."""
        problematicos = []
        
        for nombre_ingrediente in plato.ingredientes:
            # Verificar cada restricción del menú usando FoodBank
            for restriccion in menu.restricciones:
                restriccion_str = restriccion if isinstance(restriccion, str) else str(restriccion)
                if self.food_bank.ingrediente_viola_restriccion(nombre_ingrediente, restriccion_str):
                    problematicos.append(nombre_ingrediente)
                    break
        
        return problematicos
    
    def _ingredientes_fuera_temporada(self, plato: Plato, menu: Menu) -> List[str]:
        """Identifica ingredientes que no están en la temporada del menú."""
        problematicos = []
        
        temporada_menu = menu.temporada.lower() if hasattr(menu, 'temporada') else None
        if not temporada_menu:
            return problematicos
        
        for nombre_ingrediente in plato.ingredientes:
            info_ing = self.ingredientes_db.get(nombre_ingrediente)
            if not info_ing:
                continue
            
            temporadas_ing = info_ing.get('temporada', [])
            temporadas_lower = [t.lower() for t in temporadas_ing]
            
            if temporada_menu not in temporadas_lower:
                problematicos.append(nombre_ingrediente)
        
        return problematicos
    
    def _ingredientes_fuera_tradicion(self, plato: Plato, menu: Menu) -> List[str]:
        """Identifica ingredientes que NO pertenecen a la tradición requerida del menú."""
        problematicos = []
        
        tradicion_menu = menu.tradicion.lower() if hasattr(menu, 'tradicion') else None
        if not tradicion_menu:
            return problematicos
        
        # Buscar información de la tradición en tradiciones.json
        tradicion_info = None
        for trad in self.tradiciones_db:
            if trad['nombre'].lower() == tradicion_menu:
                tradicion_info = trad
                break
        
        if not tradicion_info:
            return problematicos
        
        # Usar SOLO ingredientes característicos para determinar pertenencia a tradición
        # (los típicos son demasiado genéricos y causan solapamiento)
        ingredientes_tradicion = set(tradicion_info.get('ingredientes_caracteristicos', []))
        
        # Proteínas principales que NO deben sustituirse por problemas de tradición
        # (solo por restricciones alimentarias)
        PROTEINAS_PRINCIPALES = {
            'tofu', 'tempeh', 'seitan',  # Vegetarianas
            'chicken', 'cooked_chicken', 'chicken_breast', 'chicken_thighs',  # Aves
            'beef', 'flank_steak', 'ground_beef', 'steak',  # Carnes rojas
            'pork', 'bacon', 'ham',  # Cerdo
            'fish', 'salmon', 'tuna', 'cod',  # Pescados
            'shrimp', 'prawns', 'lobster',  # Mariscos
            'lamb', 'turkey'  # Otras carnes
        }
        
        # Contar cuántos ingredientes del plato son de la tradición correcta
        ingredientes_tradicion_correcta = 0
        total_ingredientes = len(plato.ingredientes)
        
        for nombre_ingrediente in plato.ingredientes:
            if nombre_ingrediente in ingredientes_tradicion:
                ingredientes_tradicion_correcta += 1
            elif nombre_ingrediente not in PROTEINAS_PRINCIPALES:
                # Verificar si el ingrediente aparece en ALGUNA tradición
                # Si no aparece en ninguna, es universal y no se debe sustituir
                if self._ingrediente_pertenece_a_alguna_tradicion(nombre_ingrediente):
                    # Este ingrediente SÍ pertenece a otra tradición específica
                    # pero NO a la requerida, así que se puede sustituir
                    problematicos.append(nombre_ingrediente)
                # Si no pertenece a ninguna tradición, es universal (ej: salt, sugar, oil)
                # y se cuenta como válido para cualquier tradición
                else:
                    ingredientes_tradicion_correcta += 1
        
        # Si ya tenemos suficientes ingredientes de la tradición correcta, no hacer nada
        porcentaje = (ingredientes_tradicion_correcta / total_ingredientes) if total_ingredientes > 0 else 0
        if porcentaje >= 0.2:  # Ya cumple el 20% mínimo
            return []
        
        # Ordenar por los menos compatibles primero (para sustituir los que menos aportan)
        return problematicos
    
    def _verificar_porcentaje_tradicion(self, plato: Plato, menu: Menu) -> bool:
        """Verifica si el plato ya cumple con el porcentaje mínimo de tradición (20%)."""
        tradicion_menu = menu.tradicion.lower() if hasattr(menu, 'tradicion') else None
        if not tradicion_menu:
            return True
        
        # Buscar información de la tradición
        tradicion_info = None
        for trad in self.tradiciones_db:
            if trad['nombre'].lower() == tradicion_menu:
                tradicion_info = trad
                break
        
        if not tradicion_info:
            return True
        
        # Usar SOLO ingredientes característicos (no típicos)
        ingredientes_tradicion = set(tradicion_info.get('ingredientes_caracteristicos', []))
        
        # Contar ingredientes del plato que son de la tradición o universales
        count_tradicion = 0
        for ing in plato.ingredientes:
            if ing in ingredientes_tradicion:
                count_tradicion += 1
            elif not self._ingrediente_pertenece_a_alguna_tradicion(ing):
                # Ingrediente universal (no pertenece a ninguna tradición específica)
                count_tradicion += 1
        
        porcentaje = (count_tradicion / len(plato.ingredientes)) if plato.ingredientes else 0
        
        return porcentaje >= 0.2
    
    def _ingredientes_incoherentes(self, plato: Plato) -> List[str]:
        """
        Identifica ingredientes que son incompatibles con otros del plato.
        Retorna los ingredientes menos compatibles.
        """
        problematicos = []
        
        # Calcular puntuación de incompatibilidad para cada ingrediente
        puntuaciones_incompat = {}
        
        for i, nombre_ingrediente in enumerate(plato.ingredientes):
            incompatibilidades = 0
            
            for j, otro_nombre_ingrediente in enumerate(plato.ingredientes):
                if i != j:
                    es_compatible, puntuacion = self.food_bank.son_compatibles(
                        nombre_ingrediente, otro_nombre_ingrediente
                    )
                    if not es_compatible or puntuacion < 0.3:
                        incompatibilidades += 1
            
            puntuaciones_incompat[nombre_ingrediente] = incompatibilidades
        
        # Retornar los ingredientes con más incompatibilidades
        if puntuaciones_incompat:
            max_incomp = max(puntuaciones_incompat.values())
            if max_incomp > 0:
                problematicos = [ing for ing, score in puntuaciones_incompat.items() 
                               if score == max_incomp]
        
        return problematicos
    
    def _sustituir_ingrediente(self, nombre_ingrediente_original: str, 
                              plato: Plato, menu: Menu,
                              tipo_problema: str = None) -> Dict[str, Any]:
        """
        Encuentra un sustituto apropiado para un ingrediente.
        Prioriza sustitutos específicos según el tipo de problema y restricciones.
        
        Args:
            nombre_ingrediente_original: Nombre del ingrediente a sustituir
            plato: Plato completo (para contexto)
            menu: Menú con preferencias
            tipo_problema: Tipo de problema (restricciones, temporada, etc.)
            
        Returns:
            {'exito': bool, 'sustituto': str (nombre), 'puntuacion': float, 'razon': str}
        """
        # PRIMERO: Verificar si el ingrediente aún existe en el plato
        if nombre_ingrediente_original not in plato.ingredientes:
            # El ingrediente ya fue sustituido en una iteración anterior
            return {
                'exito': False,
                'sustituto': None,
                'puntuacion': 0.0,
                'razon': 'ingrediente_ya_sustituido'
            }
        
        # Obtener otros ingredientes del plato como contexto
        otros_ingredientes = [ing for ing in plato.ingredientes 
                             if ing != nombre_ingrediente_original]
        
        # Obtener restricciones como lista de strings
        restricciones = []
        if hasattr(menu, 'restricciones') and menu.restricciones:
            restricciones = [r if isinstance(r, str) else str(r) for r in menu.restricciones]
        
        temporada_menu = None
        if hasattr(menu, 'temporada') and menu.temporada:
            temporada_menu = menu.temporada.lower() if isinstance(menu.temporada, str) else str(menu.temporada).lower()
        
        candidatos = []
        
        # 0. PRIORIDAD MÁXIMA: Si es problema de TEMPORADA, usar sustitución por temporada
        if tipo_problema == 'temporada':
            # Obtener temporadas del ingrediente original
            temporadas_orig = self.food_bank.obtener_temporada_ingrediente(nombre_ingrediente_original)
            temporada_origen = temporadas_orig[0] if temporadas_orig else 'verano'
            
            exito, sustituto, puntuacion = self.food_bank.encontrar_sustituto_por_temporada(
                nombre_ingrediente_original,
                temporada_origen,
                temporada_menu,
                otros_ingredientes,
                restricciones
            )
            
            if exito:
                return {
                    'exito': True,
                    'sustituto': sustituto,
                    'puntuacion': puntuacion,
                    'razon': 'sustitucion_temporada'
                }
        
        # 1. PRIORIDAD: Si hay restricción vegetariana/vegana y el ingrediente es de origen animal,
        #    buscar sustitutos específicos primero
        if restricciones:
            es_vegano = False
            es_vegetariano = False
            
            for restriccion in menu.restricciones:
                restriccion_str = restriccion if isinstance(restriccion, str) else str(restriccion).lower()
                if 'vegano' in restriccion_str:
                    es_vegano = True
                elif 'vegetarian' in restriccion_str or 'vegetariano' in restriccion_str:
                    es_vegetariano = True
            
            # Verificar si el ingrediente original es de origen animal
            info_original = self.ingredientes_db.get(nombre_ingrediente_original)
            es_animal = info_original and info_original.get('categoria') == 'animal'
            
            # Si no está en la base de datos, detectar por palabras clave
            if not es_animal and not info_original:
                nombre_lower = nombre_ingrediente_original.lower()
                palabras_carne = ['beef', 'pork', 'chicken', 'lamb', 'turkey', 'duck', 
                                 'bacon', 'ham', 'sausage', 'meat', 'steak', 'ribs',
                                 'veal', 'venison', 'rabbit', 'goat', 'mutton',
                                 'chorizo', 'salami', 'prosciutto', 'pancetta']
                palabras_pescado = ['fish', 'salmon', 'tuna', 'cod', 'shrimp', 'prawn',
                                   'lobster', 'crab', 'squid', 'octopus', 'anchovy',
                                   'sardine', 'mackerel', 'trout', 'bass', 'halibut']
                es_animal = any(palabra in nombre_lower for palabra in palabras_carne + palabras_pescado)
            
            # VEGANO: sustituir carne, pescado, lácteos, huevos, miel
            if es_vegano:
                # Buscar sustitutos veganos en food_bank
                candidatos_veganos = self.food_bank.encontrar_sustitutos_veganos(
                    nombre_ingrediente_original,
                    otros_ingredientes
                )
                if candidatos_veganos:
                    candidatos.extend(candidatos_veganos)
                    # Retornar inmediatamente el mejor sustituto vegano
                    # Ya que tenemos alta prioridad para resolver restricciones
                    mejor_candidato = candidatos_veganos[0]
                    return {
                        'exito': True,
                        'sustituto': mejor_candidato[0],
                        'puntuacion': mejor_candidato[1]
                    }
            
            # VEGETARIANO: solo sustituir carne/pescado
            elif es_vegetariano and es_animal:
                # Buscar sustitutos vegetarianos específicos en food_bank
                candidatos_vegetarianos = self.food_bank.encontrar_sustitutos_vegetarianos(
                    nombre_ingrediente_original,
                    otros_ingredientes
                )
                if candidatos_vegetarianos:
                    candidatos.extend(candidatos_vegetarianos)
                    # Retornar inmediatamente el mejor sustituto vegetariano
                    # Ya que tenemos alta prioridad para resolver restricciones
                    mejor_candidato = candidatos_vegetarianos[0]
                    return {
                        'exito': True,
                        'sustituto': mejor_candidato[0],
                        'puntuacion': mejor_candidato[1]
                    }
        
        # 1b. PRIORIDAD: Si es problema de tradición, buscar sustitutos de la tradición correcta
        if hasattr(menu, 'tradicion') and menu.tradicion:
            tradicion_requerida = menu.tradicion.lower()
            _debug_print(f"        [DEBUG] Buscando sustitutos de tradición {tradicion_requerida}")
            
            # Buscar información de la tradición en tradiciones.json
            tradicion_info = None
            for trad in self.tradiciones_db:
                if trad['nombre'].lower() == tradicion_requerida:
                    tradicion_info = trad
                    break
            
            if tradicion_info:
                # Obtener ingredientes de la tradición (característicos primero, luego típicos)
                ingredientes_caracteristicos = tradicion_info.get('ingredientes_caracteristicos', [])
                ingredientes_tipicos = tradicion_info.get('ingredientes_tipicos', [])
                
                candidatos_tradicion = []
                
                # Priorizar ingredientes característicos (más puntuación)
                for nombre_ing in ingredientes_caracteristicos:
                    if nombre_ing not in otros_ingredientes and nombre_ing != nombre_ingrediente_original:
                        compatibilidad = self.food_bank.calcular_compatibilidad(
                            nombre_ing, otros_ingredientes
                        )
                        if compatibilidad > 0.3:
                            # Bonus para ingredientes característicos
                            candidatos_tradicion.append((nombre_ing, compatibilidad * 1.2))
                
                # Luego ingredientes típicos
                for nombre_ing in ingredientes_tipicos:
                    if nombre_ing not in otros_ingredientes and nombre_ing != nombre_ingrediente_original:
                        compatibilidad = self.food_bank.calcular_compatibilidad(
                            nombre_ing, otros_ingredientes
                        )
                        if compatibilidad > 0.3:
                            candidatos_tradicion.append((nombre_ing, compatibilidad))
                
                # Ordenar por compatibilidad descendente
                candidatos_tradicion.sort(key=lambda x: x[1], reverse=True)
                _debug_print(f"        [DEBUG] Candidatos de tradición {tradicion_requerida}: {len(candidatos_tradicion)}")
                if candidatos_tradicion:
                    _debug_print(f"        [DEBUG] Top 3 candidatos: {candidatos_tradicion[:3]}")
                    candidatos.extend(candidatos_tradicion[:10])  # Tomar los 10 más compatibles
        
        # 2. Buscar sustitutos generales usando el Food Bank
        candidatos_generales = self.food_bank.encontrar_sustitutos(
            nombre_ingrediente_original,
            otros_ingredientes,
            max_sustitutos=10
        )
        candidatos.extend(candidatos_generales)
        
        # 3. Filtrar candidatos que cumplan con las preferencias del menú
        #    Y que tengan buena compatibilidad
        # Umbral más bajo para sustitutos vegetarianos (son más difíciles de combinar)
        tiene_candidatos_vegetarianos = any('vegetariano' in str(r).lower() or 'vegetarian' in str(r).lower() 
                                            for r in getattr(menu, 'restricciones', []))
        UMBRAL_COMPATIBILIDAD_MINIMA = 0.4 if tiene_candidatos_vegetarianos else 0.6
        
        _debug_print(f"        [DEBUG] Total candidatos antes de filtrar: {len(candidatos)}")
        for nombre_candidato, puntuacion in candidatos:
            _debug_print(f"        [DEBUG] Evaluando candidato: {nombre_candidato} (puntuacion={puntuacion})")
            # Saltar candidatos con baja compatibilidad
            if puntuacion < UMBRAL_COMPATIBILIDAD_MINIMA:
                _debug_print(f"        [DEBUG]   -> Rechazado por baja compatibilidad ({puntuacion} < {UMBRAL_COMPATIBILIDAD_MINIMA})")
                continue
                
            # Buscar información del candidato en la base de datos
            info_candidato = self.ingredientes_db.get(nombre_candidato)
            
            if info_candidato:
                # Verificar que cumpla con restricciones y temporada
                cumple = self._ingrediente_cumple_preferencias(info_candidato, menu)
                _debug_print(f"        [DEBUG]   -> Cumple preferencias: {cumple}")
                if cumple:
                    return {
                        'exito': True,
                        'sustituto': nombre_candidato,
                        'puntuacion': puntuacion
                    }
            else:
                # Si no está en ingredientes_db pero viene de food_bank.encontrar_sustitutos_vegetarianos,
                # asumimos que es válido (tempeh, seitan, etc. pueden no estar en la BD)
                _debug_print(f"        [DEBUG]   -> NO encontrado en ingredientes_db, pero aceptando por ser sustituto vegetariano")
                return {
                    'exito': True,
                    'sustituto': nombre_candidato,
                    'puntuacion': puntuacion
                }
        
        # Si no se encontró ningún sustituto adecuado, fallar para que se cambie el plato completo
        return {
            'exito': False,
            'sustituto': None,
            'puntuacion': 0.0
        }
    
    def _ingrediente_cumple_preferencias(self, info_ingrediente: Dict, menu: Menu) -> bool:
        """
        Verifica si un ingrediente cumple con las preferencias del menú.
        Usa FoodBank como fuente centralizada.
        
        Args:
            info_ingrediente: Diccionario con información del ingrediente
            menu: Menú con preferencias
            
        Returns:
            True si cumple todas las preferencias
        """
        nombre_ingrediente = info_ingrediente.get('nombre', '')
        restricciones = []
        temporada = None
        
        # Obtener restricciones del menú
        if hasattr(menu, 'restricciones'):
            restricciones = [r if isinstance(r, str) else str(r) for r in menu.restricciones]
        
        # Obtener temporada del menú
        if hasattr(menu, 'temporada') and menu.temporada:
            temporada = menu.temporada.lower() if isinstance(menu.temporada, str) else str(menu.temporada).lower()
        
        # Usar método centralizado de FoodBank
        return self.food_bank.ingrediente_cumple_preferencias(nombre_ingrediente, restricciones, temporada)
    
    def _aplicar_sustitucion(self, plato: Plato, nombre_ingrediente_original: str,
                           nombre_ingrediente_sustituto: str):
        """
        Aplica una sustitución de ingrediente en el plato.
        Verifica primero que el ingrediente original aún existe antes de sustituirlo.
        
        Args:
            plato: Plato a modificar
            nombre_ingrediente_original: Nombre del ingrediente a remover
            nombre_ingrediente_sustituto: Nombre del ingrediente a añadir
        """
        # Verificar si el ingrediente original aún existe en el plato
        if nombre_ingrediente_original not in plato.ingredientes:
            # El ingrediente ya fue sustituido previamente, no hacer nada
            return
        
        # Buscar y reemplazar el ingrediente
        for i, nombre_ing in enumerate(plato.ingredientes):
            if nombre_ing == nombre_ingrediente_original:
                plato.ingredientes[i] = nombre_ingrediente_sustituto
                break
    
    def _validar_plato_modificado(self, plato: Plato, menu: Menu) -> bool:
        """
        Valida que el plato modificado cumpla con las preferencias CRÍTICAS del menú.
        Solo verifica restricciones dietéticas, NO temporada ni otros criterios.
        Usa FoodBank como fuente centralizada.
        
        Args:
            plato: Plato modificado
            menu: Menú con preferencias
            
        Returns:
            True si el plato es válido
        """
        # Verificar SOLO que no haya ingredientes que violen RESTRICCIONES
        # (no verificar temporada ni otros criterios para ser menos estrictos)
        if hasattr(menu, 'restricciones'):
            for nombre_ingrediente in plato.ingredientes:
                # Verificar solo restricciones usando FoodBank
                for restriccion in menu.restricciones:
                    restriccion_str = restriccion if isinstance(restriccion, str) else str(restriccion)
                    if self.food_bank.ingrediente_viola_restriccion(nombre_ingrediente, restriccion_str):
                        _debug_print(f"        [DEBUG] Ingrediente {nombre_ingrediente} VIOLA restricción {restriccion}")
                        return False
        
        # Verificar compatibilidad general del plato
        try:
            compatibilidad = self.food_bank.calcular_compatibilidad_plato(plato.ingredientes)
            _debug_print(f"        [DEBUG] Compatibilidad del plato: {compatibilidad} (mínimo: 0.5)")
            # Umbral mínimo de compatibilidad
            return compatibilidad >= 0.5
        except:
            # Si falla el cálculo de compatibilidad, aceptar el plato
            _debug_print(f"        [DEBUG] Error calculando compatibilidad - aceptando plato")
            return True
    
    def _validar_coherencia_sabores(self, plato: Plato) -> bool:
        """
        Valida que el plato tenga coherencia de sabores.
        Previene mezclas inapropiadas como dulce con picante, etc.
        
        Args:
            plato: Plato a validar
            
        Returns:
            True si hay coherencia de sabores
        """
        # Definir ingredientes por categoría de sabor
        ingredientes_dulces = {'honey', 'sugar', 'brown_sugar', 'maple_syrup', 'chocolate', 
                              'vanilla_extract', 'cinnamon', 'nutmeg', 'condensed_milk',
                              'sweetened_condensed_milk', 'cream', 'heavy_cream'}
        
        ingredientes_picantes = {'chili_powder', 'red_pepper_flakes', 'cayenne', 'jalapeno',
                                'jalapeno_chilies', 'hot_sauce', 'sriracha', 'chipotle',
                                'green_chilies', 'red_chilies'}
        
        ingredientes_plato = set(plato.ingredientes)
        
        # Verificar si hay ingredientes dulces
        tiene_dulce = bool(ingredientes_plato & ingredientes_dulces)
        tiene_picante = bool(ingredientes_plato & ingredientes_picantes)
        
        # No permitir mezcla de dulce con picante (salvo excepciones como mole)
        if tiene_dulce and tiene_picante:
            # Verificar si el sabor dominante del plato justifica la mezcla
            if hasattr(plato, 'sabor_dominante'):
                sabor = plato.sabor_dominante.lower() if isinstance(plato.sabor_dominante, str) else str(plato.sabor_dominante).lower()
                # Solo permitir en platos específicos (ej: mole mexicano tiene ambos)
                if 'dulce' not in sabor and 'picante' not in sabor:
                    return False
            else:
                return False
        
        return True
    
    def _ingrediente_pertenece_a_alguna_tradicion(self, nombre_ingrediente: str) -> bool:
        """
        Verifica si un ingrediente pertenece a alguna tradición específica.
        Si no aparece en ninguna tradición, se considera universal.
        
        Args:
            nombre_ingrediente: Nombre del ingrediente
            
        Returns:
            True si pertenece a alguna tradición específica, False si es universal
        """
        for tradicion in self.tradiciones_db:
            ingredientes_caracteristicos = set(tradicion.get('ingredientes_caracteristicos', []))
            ingredientes_tipicos = set(tradicion.get('ingredientes_tipicos', []))
            
            if nombre_ingrediente in ingredientes_caracteristicos or nombre_ingrediente in ingredientes_tipicos:
                return True
        
        return False
    
    def _clonar_plato(self, plato: Plato) -> Plato:
        """
        Crea una copia profunda de un plato.
        
        Args:
            plato: Plato a clonar
            
        Returns:
            Copia del plato
        """
        return Plato(
            nombre=plato.nombre,
            ingredientes=plato.ingredientes.copy(),  # Lista nueva
            tecnica_coccion=plato.tecnica_coccion.copy() if hasattr(plato, 'tecnica_coccion') else [],
            sabor_dominante=plato.sabor_dominante if hasattr(plato, 'sabor_dominante') else 'umami',
            ingrediente_sabor=plato.ingrediente_sabor if hasattr(plato, 'ingrediente_sabor') else '',
            tradicion=plato.tradicion if hasattr(plato, 'tradicion') else 'general',
            temporada=plato.temporada.copy() if hasattr(plato, 'temporada') else []
        )
