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
    
    def buscar_plato_substitucion(self, plato_problematico: Plato, menu: Menu,
                                 tipo_problema: str, problema_especifico: str) -> Dict[str, Any]:
        """
        Busca un plato alternativo que cumpla todas las preferencias del menú
        
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
        
        # 2. Calcular similitud con el plato problemático
        candidatos_con_similitud = self._calcular_similitud_candidatos(
            plato_problematico, candidatos_validos
        )
        
        # 3. Seleccionar el más similar
        mejor_candidato = max(candidatos_con_similitud, key=lambda x: x['similitud'])
        
        # 4. Verificar que la similitud sea suficiente
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
                f'Resuelve problema: {tipo_problema} - {problema_especifico}'
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
        Convierte datos JSON a objeto Plato usando la base de datos de ingredientes
        
        Args:
            plato_data: Datos del plato en formato JSON
            
        Returns:
            Objeto Plato o None si hay error
        """
        try:
            ingredientes = []
            
            # Procesar ingredientes usando la base de datos
            for nombre_ingrediente in plato_data.get('ingredientes', []):
                info_ingrediente = self.ingredientes_db.get(nombre_ingrediente)
                
                if info_ingrediente:
                    ingrediente = self._crear_ingrediente_desde_db(info_ingrediente)
                    ingredientes.append(ingrediente)
                else:
                    print(f"Advertencia: Ingrediente '{nombre_ingrediente}' no encontrado en la base de datos")
            
            # Crear el plato
            plato = Plato(
                nombre=plato_data.get('nombre', ''),
                ingredientes=ingredientes,
                tecnica=self._string_a_tecnica(plato_data.get('tecnica_coccion', ['hervido'])[0]),
                tradicion=self._inferir_tradicion(plato_data)  # Necesitamos inferir o añadir a platos.json
            )
            
            return plato
            
        except Exception as e:
            print(f"Error convirtiendo JSON a Plato: {e}")
            return None
    
    def _crear_ingrediente_desde_db(self, info_ingrediente: Dict) -> Ingrediente:
        """Crea un objeto Ingrediente desde la información de la base de datos usando from_dict"""
        return Ingrediente.from_dict(info_ingrediente)
    
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
        
        # Verificar tradición culinaria
        if menu.tradicion:
            if hasattr(plato.tradicion, 'value'):
                tradicion_plato = plato.tradicion.value
            else:
                tradicion_plato = str(plato.tradicion)
            
            if hasattr(menu.tradicion, 'value'):
                tradicion_menu = menu.tradicion.value
            else:
                tradicion_menu = str(menu.tradicion)
                
            if tradicion_plato != tradicion_menu:
                return False
        
        # Verificar técnica preferida
        if menu.tecnica_preferida:
            if hasattr(plato.tecnica, 'value'):
                tecnica_plato = plato.tecnica.value
            else:
                tecnica_plato = str(plato.tecnica)
            
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
            restriccion_valor = str(restriccion)
        
        if restriccion_valor == "vegano":
            categorias_no_veganas = ["animal", "lacteo"]
            for ingrediente in plato.ingredientes:
                if hasattr(ingrediente.categoria, 'value'):
                    categoria = ingrediente.categoria.value
                else:
                    categoria = str(ingrediente.categoria)
                
                if categoria in categorias_no_veganas:
                    return False
        
        elif restriccion_valor == "sin_lactosa":
            for ingrediente in plato.ingredientes:
                if hasattr(ingrediente.categoria, 'value'):
                    categoria = ingrediente.categoria.value
                else:
                    categoria = str(ingrediente.categoria)
                
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