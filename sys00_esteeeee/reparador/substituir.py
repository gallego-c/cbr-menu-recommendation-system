"""
Módulo para substituir platos completos basado en similitud y preferencias del menú
"""

import sys
import os
import json
from typing import Dict, List, Optional, Any

# Añadir el directorio padre al path para importar models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from conocimiento.models import Plato, Menu, Caso, Temporada, CategoriaIngrediente, Ingrediente, TecnicaCoccion, TradicionCultural, Sabor
from conocimiento import cargador
from .food_bank import FoodBank


class SubstitutorPlatos:
    """
    Clase para substituir platos completos buscando alternativas 
    que cumplan todas las preferencias del menú
    """
    
    def __init__(self, casos_base: List[Any]):
        """
        Inicializa el substitutor con la base de casos y carga el conocimiento
        
        Args:
            casos_base: Lista de casos base para buscar platos alternativos
        """
        self.casos_base = casos_base
        self.pesos_similitud = {
            'temporada': 0.3,
            'restricciones': 0.4,  # Más peso a restricciones dietéticas
            'tradicion': 0.2,
            'tecnica': 0.1
        }
        # Cargar conocimiento usando el cargador centralizado
        self.ingredientes_db = cargador.cargar_ingredientes()
        platos_lista = cargador.cargar_platos()
        self.platos_db = list(platos_lista.values())
        # Inicializar Food Bank para validación de compatibilidad
        self.food_bank = FoodBank()
    
    def buscar_plato_substitucion(self, plato_problematico: Plato, menu: Menu,
                                 tipo_problema: str, problema_especifico: str) -> Dict[str, Any]:
        """
        Busca un plato alternativo que cumpla todas las preferencias del menú
        y que tenga al menos 2 ingredientes compatibles con el resto del menú
        
        Args:
            plato_problematico: Plato que necesita ser substituido
            menu: Menú con todas las preferencias
            tipo_problema: Tipo de problema detectado
            problema_especifico: Descripción específica del problema
            
        Returns:
            Resultado de la búsqueda con plato substitucion o fallo
        """
        
        # 1. Filtrar candidatos que cumplan TODAS las preferencias del menú
        candidatos_validos = self._filtrar_candidatos_validos(menu)
        
        if not candidatos_validos:
            return {
                'exito': False,
                'plato_substitucion': None,
                'mensajes': ['No hay platos candidatos que cumplan todas las preferencias'],
                'motivo_fallo': 'sin_candidatos_validos'
            }
        
        # 2. Obtener ingredientes del resto del menú (otros platos)
        ingredientes_menu = self._obtener_ingredientes_resto_menu(menu, plato_problematico)
        
        # 3. Filtrar candidatos que tengan al menos 2 ingredientes compatibles
        candidatos_compatibles = self._filtrar_por_compatibilidad_menu(
            candidatos_validos, 
            ingredientes_menu,
            min_ingredientes_compatibles=2
        )
        
        if not candidatos_compatibles:
            return {
                'exito': False,
                'plato_substitucion': None,
                'mensajes': ['No hay platos con al menos 2 ingredientes compatibles con el menú'],
                'motivo_fallo': 'sin_ingredientes_compatibles'
            }
        
        # 4. Calcular similitud con el plato problemático
        candidatos_con_similitud = self._calcular_similitud_candidatos(
            plato_problematico, candidatos_compatibles
        )
        
        # 5. Seleccionar el más similar
        mejor_candidato = max(candidatos_con_similitud, key=lambda x: x['similitud'])
        
        # 6. Verificar que la similitud sea suficiente
        umbral_minimo = 0.6  # Umbral mínimo de similitud
        if mejor_candidato['similitud'] < umbral_minimo:
            return {
                'exito': False,
                'plato_substitucion': None,
                'mensajes': [f'Similitud insuficiente: {mejor_candidato["similitud"]:.2f} < {umbral_minimo}'],
                'motivo_fallo': 'similitud_insuficiente'
            }
        
        return {
            'exito': True,
            'plato_substitucion': mejor_candidato['plato'],
            'mensajes': [
                f'Plato substituido con similitud: {mejor_candidato["similitud"]:.2f}',
                f'Resuelve problema: {tipo_problema} - {problema_especifico}',
                f'Ingredientes compatibles: {mejor_candidato.get("num_compatibles", "N/A")}'
            ],
            'similitud': mejor_candidato['similitud']
        }
    
    def _filtrar_candidatos_validos(self, menu: Menu) -> List[Plato]:
        """
        Filtra platos candidatos que cumplan TODAS las preferencias del menú
        Usa directamente los platos de platos.json
        
        Args:
            menu: Menú con las preferencias a cumplir
            
        Returns:
            Lista de platos que cumplen todas las preferencias
        """
        candidatos_validos = []
        
        # Usar directamente los platos de platos.json
        for plato_data in self.platos_db:
            plato = self._json_a_plato(plato_data)
            if plato and self._cumple_todas_preferencias(plato, menu):
                candidatos_validos.append(plato)
        
        # También buscar en los casos si están disponibles
        for caso in self.casos_base:
            platos_caso = self._extraer_platos_de_caso(caso)
            for plato in platos_caso:
                if self._cumple_todas_preferencias(plato, menu):
                    candidatos_validos.append(plato)
        
        return candidatos_validos
    
    def _extraer_platos_de_caso(self, caso: Dict[str, Any]) -> List[Plato]:
        """
        Extrae platos de un caso (conversión JSON a objetos Plato)
        
        Args:
            caso: Caso en formato JSON
            
        Returns:
            Lista de objetos Plato
        """
        platos = []
        
        # Asumir que el caso tiene una estructura con 'menu' -> 'platos'
        if 'menu' in caso and 'platos' in caso['menu']:
            for plato_data in caso['menu']['platos']:
                # Conversión simplificada - se podría mejorar
                plato = self._json_a_plato(plato_data)
                if plato:
                    platos.append(plato)
        
        return platos
    
    def _json_a_plato(self, plato_data: Dict[str, Any]) -> Optional[Plato]:
        """
        Convierte datos JSON a objeto Plato.
        IMPORTANTE: Plato.ingredientes es List[str] (nombres), no List[Ingrediente]
        
        Args:
            plato_data: Datos del plato en formato JSON
            
        Returns:
            Objeto Plato o None si hay error
        """
        try:
            # Usar el método from_dict de la clase Plato para asegurar consistencia
            plato = Plato.from_dict(plato_data)
            return plato
            
        except Exception as e:
            print(f"Error convirtiendo JSON a Plato: {e}")
            return None
    
    def _string_a_temporada(self, temporada_str: str) -> Optional[Temporada]:
        """Convierte string de temporada a enum"""
        mapeo = {
            'primavera': Temporada.PRIMAVERA,
            'verano': Temporada.VERANO,
            'otoño': Temporada.OTONO,
            'otono': Temporada.OTONO,
            'invierno': Temporada.INVIERNO
        }
        return mapeo.get(temporada_str.lower())
    
    def _string_a_categoria(self, categoria_str: str) -> CategoriaIngrediente:
        """Convierte string de categoría a enum"""
        mapeo = {
            'vegetal': CategoriaIngrediente.VEGETAL,
            'fruta': CategoriaIngrediente.FRUTA,
            'hongo': CategoriaIngrediente.HONGO,
            'animal': CategoriaIngrediente.ANIMAL,
            'cereal': CategoriaIngrediente.CEREAL,
            'lacteo': CategoriaIngrediente.LACTEO,
            'condimento': CategoriaIngrediente.CONDIMENTO
        }
        return mapeo.get(categoria_str.lower(), CategoriaIngrediente.CONDIMENTO)
    
    def _string_a_sabor(self, sabor_str: str) -> Sabor:
        """Convierte string de sabor a enum"""
        mapeo = {
            'dulce': Sabor.DULCE,
            'salado': Sabor.SALADO,
            'umami': Sabor.UMAMI,
            'ácido': Sabor.ACIDO,
            'acido': Sabor.ACIDO,
            'amargo': Sabor.AMARGO
        }
        return mapeo.get(sabor_str.lower(), Sabor.UMAMI)
    
    def _string_a_tecnica(self, tecnica_str: str) -> TecnicaCoccion:
        """Convierte string de técnica a enum"""
        mapeo = {
            'crudo': TecnicaCoccion.CRUDO,
            'hervido': TecnicaCoccion.HERVIDO,
            'horneado': TecnicaCoccion.HORNEADO,
            'esferificacion': TecnicaCoccion.ESFERIFICACION
        }
        return mapeo.get(tecnica_str.lower(), TecnicaCoccion.HERVIDO)
    
    def _inferir_tradicion(self, plato_data: Dict) -> TradicionCultural:
        """
        Infiere la tradición culinaria basándose en ingredientes y nombres
        TODO: Esto se podría añadir directamente a platos.json
        """
        nombre = plato_data.get('nombre', '').lower()
        ingredientes = plato_data.get('ingredientes', [])
        
        # Ingredientes típicamente mexicanos
        ingredientes_mexicanos = ['aguacate', 'chile', 'tortilla_maiz', 'cilantro']
        if any(ing in ingredientes for ing in ingredientes_mexicanos):
            return TradicionCultural.MEXICANA
        
        # Palabras clave mexicanas
        if any(palabra in nombre for palabra in ['guacamole', 'tortilla', 'chile']):
            return TradicionCultural.MEXICANA
        
        # Por defecto catalana
        return TradicionCultural.CATALANA
    
    def _cumple_todas_preferencias(self, plato: Plato, menu: Menu) -> bool:
        """
        Verifica que un plato cumpla TODAS las preferencias del menú
        
        Args:
            plato: Plato candidato
            menu: Menú con las preferencias
            
        Returns:
            True si cumple todas las preferencias
        """
        
        # Verificar restricciones dietéticas
        if menu.restricciones:
            for restriccion in menu.restricciones:
                if not self._cumple_restriccion_dietetica(plato, restriccion):
                    return False
        
        # Verificar temporada
        if menu.temporada:
            if not self._es_temporada_apropiada(plato, menu.temporada):
                return False
        
        # Verificar tradición culinaria mediante ingredientes típicos
        # (los platos en platos.json no tienen campo tradicion)
        if hasattr(menu, 'tradicion') and menu.tradicion:
            if not self._tiene_ingredientes_tipicos_tradicion(plato, menu.tradicion):
                return False
        
        # Verificar técnica preferida
        if menu.tecnica_preferida:
            if hasattr(plato, 'tecnica_coccion') and plato.tecnica_coccion:
                tecnica_plato = plato.tecnica_coccion[0] if isinstance(plato.tecnica_coccion, list) else str(plato.tecnica_coccion)
            else:
                tecnica_plato = ''
            
            if hasattr(menu.tecnica_preferida, 'value'):
                tecnica_menu = menu.tecnica_preferida.value
            else:
                tecnica_menu = str(menu.tecnica_preferida)
                
            if tecnica_plato != tecnica_menu:
                return False
        
        return True
    
    def _cumple_restriccion_dietetica(self, plato: Plato, restriccion) -> bool:
        """Verifica si un plato cumple una restricción dietética específica"""
        
        if hasattr(restriccion, 'value'):
            restriccion_valor = restriccion.value
        else:
            restriccion_valor = str(restriccion).lower()
        
        # Cargar la configuración de restricciones desde restricciones.json
        restricciones_config = self.cargador.cargar_restricciones()
        
        for restriccion_config in restricciones_config:
            if restriccion_config.get('nombre', '').lower() == restriccion_valor:
                ingredientes_prohibidos = restriccion_config.get('ingredientes_prohibidos', [])
                categorias_prohibidas = restriccion_config.get('categorias_prohibidas', [])
                
                # plato.ingredientes es List[str] según models.py
                for nombre_ingrediente in plato.ingredientes:
                    # Verificar si está en la lista de ingredientes prohibidos
                    if nombre_ingrediente in ingredientes_prohibidos:
                        return False
                    
                    # Verificar categoría (consultar ingredientes_db)
                    info_ingrediente = self.ingredientes_db.get(nombre_ingrediente)
                    if info_ingrediente:
                        categoria = info_ingrediente.get('categoria', '')
                        if categoria in categorias_prohibidas:
                            # Para vegetariano: permitir huevos aunque sean categoría 'animal'
                            if restriccion_valor == 'vegetariano' and nombre_ingrediente in ['eggs', 'egg', 'egg_yolks', 'egg_whites']:
                                continue
                            return False
                
                return True
        
        # Fallback al mapeo antiguo si no se encuentra en restricciones.json
        if restriccion_valor == "vegano":
            categorias_no_veganas = ["animal", "lacteo"]
            for nombre_ingrediente in plato.ingredientes:
                info_ingrediente = self.ingredientes_db.get(nombre_ingrediente)
                if info_ingrediente:
                    categoria = info_ingrediente.get('categoria', '')
                    if categoria in categorias_no_veganas:
                        return False
        
        elif restriccion_valor == "vegetariano":
            # Vegetarianos NO pueden comer carne/pescado pero SÍ huevos y lácteos
            for nombre_ingrediente in plato.ingredientes:
                # Permitir explícitamente huevos
                if nombre_ingrediente in ['eggs', 'egg', 'egg_yolks', 'egg_whites']:
                    continue
                    
                info_ingrediente = self.ingredientes_db.get(nombre_ingrediente)
                if info_ingrediente:
                    categoria = info_ingrediente.get('categoria', '')
                    # Solo prohibir 'animal' (carne/pescado), no lácteos
                    if categoria == 'animal':
                        return False
        
        elif restriccion_valor == "sin_lactosa":
            for nombre_ingrediente in plato.ingredientes:
                info_ingrediente = self.ingredientes_db.get(nombre_ingrediente)
                if info_ingrediente:
                    categoria = info_ingrediente.get('categoria', '')
                    if categoria == "lacteo":
                        return False
        
        return True
    
    def _es_temporada_apropiada(self, plato: Plato, temporada_deseada) -> bool:
        """Verifica si los ingredientes del plato son apropiados para la temporada"""
        
        if hasattr(temporada_deseada, 'value'):
            temporada_valor = temporada_deseada.value
        else:
            temporada_valor = str(temporada_deseada)
        
        for ingrediente in plato.ingredientes:
            # Verificar si la temporada está en la lista de temporadas del ingrediente
            temporadas_ingrediente = []
            for temp in ingrediente.temporada:
                if hasattr(temp, 'value'):
                    temporadas_ingrediente.append(temp.value)
                else:
                    temporadas_ingrediente.append(str(temp))
            
            if temporada_valor not in temporadas_ingrediente:
                # Solo verificar ingredientes principales (vegetales y frutas)
                if hasattr(ingrediente.categoria, 'value'):
                    categoria = ingrediente.categoria.value
                else:
                    categoria = str(ingrediente.categoria)
                
                if categoria in ["vegetal", "fruta"]:
                    return False
        
        return True
    
    def _calcular_similitud_candidatos(self, plato_objetivo: Plato, 
                                     candidatos: List[Plato]) -> List[Dict[str, Any]]:
        """
        Calcula similitud entre el plato objetivo y los candidatos
        
        Args:
            plato_objetivo: Plato que se quiere substituir
            candidatos: Lista de platos candidatos
            
        Returns:
            Lista de candidatos con su puntuación de similitud
        """
        candidatos_con_similitud = []
        
        for candidato in candidatos:
            similitud = self._calcular_similitud_platos(plato_objetivo, candidato)
            candidatos_con_similitud.append({
                'plato': candidato,
                'similitud': similitud
            })
        
        return candidatos_con_similitud
    
    def _calcular_similitud_platos(self, plato1: Plato, plato2: Plato) -> float:
        """
        Calcula similitud entre dos platos
        
        Args:
            plato1: Primer plato
            plato2: Segundo plato
            
        Returns:
            Puntuación de similitud (0.0 - 1.0)
        """
        similitud_total = 0.0
        
        # Similitud de ingredientes (60% del peso)
        similitud_ingredientes = self._similitud_ingredientes(plato1, plato2)
        similitud_total += similitud_ingredientes * 0.6
        
        # Similitud de técnica (20% del peso)
        similitud_tecnica = self._similitud_tecnica(plato1, plato2)
        similitud_total += similitud_tecnica * 0.2
        
        # Similitud de tradición (20% del peso)
        similitud_tradicion = self._similitud_tradicion(plato1, plato2)
        similitud_total += similitud_tradicion * 0.2
        
        return similitud_total
    
    def _similitud_ingredientes(self, plato1: Plato, plato2: Plato) -> float:
        """Calcula similitud de ingredientes entre dos platos"""
        ingredientes1 = {ing.nombre for ing in plato1.ingredientes}
        ingredientes2 = {ing.nombre for ing in plato2.ingredientes}
        
        if not ingredientes1 and not ingredientes2:
            return 1.0
        
        interseccion = len(ingredientes1.intersection(ingredientes2))
        union = len(ingredientes1.union(ingredientes2))
        
        return interseccion / union if union > 0 else 0.0
    
    def _similitud_tecnica(self, plato1: Plato, plato2: Plato) -> float:
        """Calcula similitud de técnica de cocción"""
        if hasattr(plato1.tecnica, 'value'):
            tecnica1 = plato1.tecnica.value
        else:
            tecnica1 = str(plato1.tecnica)
            
        if hasattr(plato2.tecnica, 'value'):
            tecnica2 = plato2.tecnica.value
        else:
            tecnica2 = str(plato2.tecnica)
        
        return 1.0 if tecnica1 == tecnica2 else 0.0
    
    def _similitud_tradicion(self, plato1: Plato, plato2: Plato) -> float:
        """Calcula similitud de tradición culinaria"""
        if hasattr(plato1.tradicion, 'value'):
            tradicion1 = plato1.tradicion.value
        else:
            tradicion1 = str(plato1.tradicion)
            
        if hasattr(plato2.tradicion, 'value'):
            tradicion2 = plato2.tradicion.value
        else:
            tradicion2 = str(plato2.tradicion)
        
        return 1.0 if tradicion1 == tradicion2 else 0.0
    
    def buscar_alternativa_simple(self, nombre_plato: str, preferencias: Dict, 
                                   tipo_plato: Optional[str] = None) -> Optional[str]:
        """
        Busca un plato alternativo simple que cumpla las preferencias.
        Versión simplificada que retorna el primer plato del mismo tipo.
        
        Args:
            nombre_plato: Nombre del plato original
            preferencias: Preferencias a cumplir (no usado en esta versión simple)
            tipo_plato: Tipo de plato ('entrante', 'principal', 'postre')
            
        Returns:
            Nombre del plato alternativo o None
        """
        # Buscar en la base de platos
        for plato_data in self.platos_db:
            # Si se especifica tipo, filtrar por tipo
            if tipo_plato and plato_data.get('tipo') != tipo_plato:
                continue
            
            # No incluir el plato original
            if plato_data['nombre'] == nombre_plato:
                continue
            
            # Retornar el primer plato válido encontrado
            return plato_data['nombre']
        
        return None
    
    def _obtener_ingredientes_resto_menu(self, menu: Menu, plato_excluir: Plato) -> List[str]:
        """
        Obtiene los nombres de todos los ingredientes del menú excepto los del plato a excluir.
        
        Args:
            menu: Menú completo
            plato_excluir: Plato que no se debe incluir
            
        Returns:
            Lista de nombres de ingredientes
        """
        ingredientes_menu = []
        
        # Obtener platos del menú
        if hasattr(menu, 'platos'):
            for plato in menu.platos:
                # Saltar el plato que estamos excluyendo
                if plato.nombre == plato_excluir.nombre:
                    continue
                
                # Añadir nombres de ingredientes
                for ingrediente in plato.ingredientes:
                    ingredientes_menu.append(ingrediente.nombre)
        
        return ingredientes_menu
    
    def _filtrar_por_compatibilidad_menu(self, candidatos: List[Plato], 
                                        ingredientes_menu: List[str],
                                        min_ingredientes_compatibles: int = 2) -> List[Plato]:
        """
        Filtra candidatos que tengan al menos N ingredientes compatibles con el resto del menú.
        
        Args:
            candidatos: Lista de platos candidatos
            ingredientes_menu: Ingredientes del resto del menú
            min_ingredientes_compatibles: Mínimo de ingredientes compatibles requeridos
            
        Returns:
            Lista de platos que cumplen el criterio de compatibilidad
        """
        if not ingredientes_menu:
            # Si no hay otros ingredientes en el menú, todos los candidatos son válidos
            return candidatos
        
        candidatos_compatibles = []
        
        for candidato in candidatos:
            num_compatibles = self._contar_ingredientes_compatibles(
                candidato, 
                ingredientes_menu
            )
            
            if num_compatibles >= min_ingredientes_compatibles:
                candidatos_compatibles.append(candidato)
        
        return candidatos_compatibles
    
    def _contar_ingredientes_compatibles(self, plato: Plato, 
                                        ingredientes_menu: List[str]) -> int:
        """
        Cuenta cuántos ingredientes del plato son compatibles con los del menú.
        
        Args:
            plato: Plato a evaluar
            ingredientes_menu: Ingredientes del resto del menú (nombres como strings)
            
        Returns:
            Número de ingredientes compatibles
        """
        num_compatibles = 0
        
        # plato.ingredientes es List[str] según models.py
        for ingrediente_plato in plato.ingredientes:
            # Verificar si este ingrediente es compatible con al menos uno del menú
            es_compatible_con_algun_ingrediente = False
            
            for ingrediente_menu in ingredientes_menu:
                es_compatible, puntuacion = self.food_bank.son_compatibles(
                    ingrediente_plato,  # Ya es un string (nombre)
                    ingrediente_menu
                )
                
                # Considerar compatible si la puntuación es al menos 0.5
                if es_compatible and puntuacion >= 0.5:
                    es_compatible_con_algun_ingrediente = True
                    break
            
            if es_compatible_con_algun_ingrediente:
                num_compatibles += 1
        
        return num_compatibles
    
    def _tiene_ingredientes_tipicos_tradicion(self, plato: Plato, tradicion_menu) -> bool:
        """
        Verifica si un plato tiene suficientes ingredientes típicos de una tradición.
        
        Args:
            plato: Plato a verificar
            tradicion_menu: Tradición requerida
            
        Returns:
            True si el plato tiene al menos 20% de ingredientes de la tradición
        """
        # Cargar tradiciones
        tradiciones_data = cargador.cargar_tradiciones()
        
        # Convertir tradicion_menu a string
        if hasattr(tradicion_menu, 'value'):
            tradicion_str = tradicion_menu.value.lower()
        else:
            tradicion_str = str(tradicion_menu).lower()
        
        # Buscar la tradición específica
        tradicion_info = None
        for trad in tradiciones_data:
            if trad.get('nombre', '').lower() == tradicion_str:
                tradicion_info = trad
                break
        
        if not tradicion_info:
            return False
        
        # Obtener ingredientes típicos de esta tradición
        ingredientes_caracteristicos = set(tradicion_info.get('ingredientes_caracteristicos', []))
        ingredientes_tipicos = set(tradicion_info.get('ingredientes_tipicos', []))
        todos_ingredientes_tradicion = ingredientes_caracteristicos | ingredientes_tipicos
        
        if not todos_ingredientes_tradicion:
            return False
        
        # Contar cuántos ingredientes del plato son de esta tradición
        ingredientes_plato_set = set(plato.ingredientes)
        ingredientes_de_tradicion = ingredientes_plato_set & todos_ingredientes_tradicion
        
        # Calcular porcentaje
        if len(plato.ingredientes) == 0:
            return False
        
        porcentaje = len(ingredientes_de_tradicion) / len(plato.ingredientes)
        
        # Requerir al menos 20% de ingredientes de la tradición
        # (más relajado que el 20% que se valida después de la reparación)
        return porcentaje >= 0.15  # 15% para dar más opciones en la búsqueda
