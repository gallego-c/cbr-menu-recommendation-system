"""
Módulo para modificar platos aplicando las reglas de reparación del JSON
"""

import sys
import os
import json
from typing import List, Dict, Any, Optional

# Añadir el directorio padre al path para importar models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from conocimiento.models import Plato, Ingrediente, TipoRegla, Temporada, Sabor, CategoriaIngrediente
from conocimiento import cargador


class ModificadorPlatos:
    """
    Clase para modificar platos aplicando las reglas de reparación desde JSON
    """
    
    def __init__(self, reglas_modificacion: Dict[str, Any]):
        """
        Inicializa el modificador con las reglas de reparación y carga el conocimiento
        
        Args:
            reglas_modificacion: Reglas cargadas desde reparaciones.json
        """
        self.reglas = reglas_modificacion
        # Cargar conocimiento usando el cargador centralizado
        self.ingredientes_db = cargador.cargar_ingredientes()
        self.platos_db = cargador.cargar_platos()
    
    def aplicar_modificaciones(self, plato: Plato, tipo_problema: str, 
                             problema_especifico: str) -> Dict[str, Any]:
        """
        Aplica modificaciones a un plato según las reglas de reparación
        
        Args:
            plato: Plato a modificar
            tipo_problema: Tipo de problema (restricciones, temporada, etc.)
            problema_especifico: Descripción específica del problema
            
        Returns:
            Resultado de la modificación
        """
        
        # Buscar la regla apropiada
        regla = self._buscar_regla_aplicable(tipo_problema, problema_especifico)
        
        if not regla:
            return {
                'exito': False,
                'plato_modificado': plato,
                'mensajes': [f'No se encontró regla para: {tipo_problema} - {problema_especifico}'],
                'motivo_fallo': 'regla_no_encontrada'
            }
        
        # Aplicar las modificaciones según la regla
        mensajes_modificacion = self._aplicar_regla(plato, regla)
        
        return {
            'exito': len(mensajes_modificacion) > 0,
            'plato_modificado': plato,  # El plato se modifica in-place
            'mensajes': mensajes_modificacion,
            'regla_aplicada': regla
        }
    
    def _buscar_regla_aplicable(self, tipo_problema: str, 
                              problema_especifico: str) -> Optional[Dict[str, Any]]:
        """
        Busca la regla apropiada para el tipo de problema
        
        Args:
            tipo_problema: Tipo de problema
            problema_especifico: Descripción específica
            
        Returns:
            Regla encontrada o None
        """
        
        # Mapear tipo de problema a categoría en el JSON
        mapeo_categorias = {
            'restricciones': 'reglas_restricciones',
            'temporada': 'reglas_temporada',
            'sabor': 'reglas_sabor',
            'tradicion': 'reglas_tradicion',
            'coherencia': 'reglas_coherencia'
        }
        
        categoria_reglas = mapeo_categorias.get(tipo_problema)
        if not categoria_reglas or categoria_reglas not in self.reglas:
            return None
        
        # Buscar en las subcategorías
        categoria_data = self.reglas[categoria_reglas]
        
        for subcategoria, reglas_lista in categoria_data.items():
            for regla in reglas_lista:
                if self._regla_aplica(regla, tipo_problema, problema_especifico):
                    return regla[2] if len(regla) >= 3 else None
        
        return None
    
    def _regla_aplica(self, regla: List[Any], tipo_problema: str, 
                     problema_especifico: str) -> bool:
        """
        Verifica si una regla aplica al problema específico
        
        Args:
            regla: Regla en formato [inicial, final, configuracion]
            tipo_problema: Tipo de problema
            problema_especifico: Descripción específica
            
        Returns:
            True si la regla aplica
        """
        
        if len(regla) < 3:
            return False
        
        estado_inicial = regla[0].lower() if isinstance(regla[0], str) else regla[0]
        estado_final = regla[1].lower() if isinstance(regla[1], str) else regla[1]
        problema_lower = problema_especifico.lower()
        
        # Lógica específica según el tipo de problema
        if tipo_problema == 'restricciones':
            # Para restricciones, buscar el estado final en problema_especifico
            return estado_final in problema_lower
        
        elif tipo_problema == 'temporada':
            # Para temporada, verificar si hay ingredientes fuera de temporada
            # que esta regla puede reparar
            if "fuera de temporada" in problema_lower or "fuera_temporada" in problema_lower:
                # Extraer el ingrediente problemático del mensaje de error
                # Formato: "entrante (Plato): Ingrediente fuera de temporada: calabaza (disponible en: otoño)"
                if ":" in problema_especifico:
                    partes = problema_especifico.split(":")
                    # El ingrediente está después del segundo ":"
                    if len(partes) >= 3:
                        ingrediente = partes[2].split("(")[0].strip().lower()
                        # Verificar si este ingrediente está en las acciones de la regla
                        if len(regla) >= 3 and isinstance(regla[2], dict):
                            acciones = regla[2].get("acciones_por_ingrediente", [])
                            for accion in acciones:
                                ing_accion = accion.get("ingrediente", "").lower()
                                if ing_accion == ingrediente:
                                    return True
            return False
        
        elif tipo_problema == 'sabor':
            # Para sabor, buscar cambio de sabor
            return "cambio_sabor" in estado_inicial or "sabor" in problema_lower
        
        elif tipo_problema == 'tradicion':
            # Para tradición, puede ser cambio de tradición o añadir ingredientes característicos
            # Formato 1: "catalana -> mexicana" (cambio explícito)
            if "->" in problema_especifico:
                tradiciones = problema_especifico.split(" -> ")
                if len(tradiciones) == 2:
                    return (tradiciones[0].strip().lower() == estado_inicial and
                           tradiciones[1].strip().lower() == estado_final)
            
            # Formato 2: "Muy pocos ingredientes de tradición catalana" (necesita añadir ingredientes)
            # En este caso, buscar reglas que añadan ingredientes de la tradición actual
            if "muy pocos ingredientes" in problema_lower or "pocos ingredientes" in problema_lower:
                # Extraer la tradición del problema (cualquier tradición válida)
                tradicion_buscada = None
                tradiciones_validas = ['catalana', 'mexicana', 'italiana', 'india', 'francesa', 'china', 'mediterranea']
                for palabra in problema_especifico.split():
                    palabra_lower = palabra.strip(':.,').lower()
                    if palabra_lower in tradiciones_validas or palabra_lower.rstrip(':') in tradiciones_validas:
                        tradicion_buscada = palabra_lower.strip(':')
                        break
                
                # Verificar si esta regla puede añadir ingredientes de esa tradición
                if len(regla) >= 3 and isinstance(regla[2], dict):
                    # Para reglas "any -> tradicion", estado_final debe coincidir con la tradición buscada
                    if estado_inicial == "any" and estado_final == tradicion_buscada:
                        return True
                    
                    # Para reglas "tradicion1 -> tradicion2", solo si estamos añadiendo hacia tradicion2
                    if tradicion_buscada and estado_final == tradicion_buscada:
                        acciones = regla[2].get("acciones_por_ingrediente", [])
                        for accion in acciones:
                            opciones = accion.get("opciones", [])
                            for opcion in opciones:
                                if "añadir" in opcion or "anadir" in opcion:
                                    return True
            return False
        
        elif tipo_problema == 'coherencia':
            # Para coherencia, buscar cambio de estilo
            return "estilo" in estado_inicial or "estilo" in problema_lower
        
        return False
    
    def _aplicar_regla(self, plato: Plato, regla: Dict[str, Any]) -> List[str]:
        """
        Aplica una regla específica al plato
        
        Args:
            plato: Plato a modificar
            regla: Configuración de la regla
            
        Returns:
            Lista de mensajes describiendo las modificaciones
        """
        mensajes = []
        
        modo_aplicacion = regla.get("modo_aplicacion", "una_sola_accion")
        acciones_por_ingrediente = regla.get("acciones_por_ingrediente", [])
        
        if modo_aplicacion == "todos_los_ingredientes":
            mensajes.extend(self._aplicar_todos_ingredientes(plato, acciones_por_ingrediente))
        elif modo_aplicacion == "por_ingrediente_una_opcion":
            mensajes.extend(self._aplicar_una_opcion_por_ingrediente(plato, acciones_por_ingrediente))
        elif modo_aplicacion == "una_sola_accion":
            mensajes.extend(self._aplicar_una_sola_accion(plato, acciones_por_ingrediente))
        
        return mensajes
    
    def _aplicar_todos_ingredientes(self, plato: Plato, 
                                  acciones_por_ingrediente: List[Dict]) -> List[str]:
        """Aplica acciones sobre todos los ingredientes problemáticos encontrados"""
        mensajes = []
        # plato.ingredientes es List[str] - nombres de ingredientes
        nombres_ingredientes = plato.ingredientes
        
        for accion_grupo in acciones_por_ingrediente:
            ingrediente_objetivo = accion_grupo.get("ingrediente")
            opciones = accion_grupo.get("opciones", [])
            
            if (ingrediente_objetivo == "cualquiera" or 
                ingrediente_objetivo in nombres_ingredientes):
                
                for opcion in opciones:
                    mensaje = self._aplicar_accion_individual(plato, opcion, ingrediente_objetivo)
                    if mensaje:
                        mensajes.append(mensaje)
        
        return mensajes
    
    def _aplicar_una_opcion_por_ingrediente(self, plato: Plato, 
                                          acciones_por_ingrediente: List[Dict]) -> List[str]:
        """Para cada ingrediente encontrado, aplica solo una de las opciones"""
        mensajes = []
        # plato.ingredientes es List[str]
        nombres_ingredientes = plato.ingredientes
        
        for accion_grupo in acciones_por_ingrediente:
            ingrediente_objetivo = accion_grupo.get("ingrediente")
            opciones = accion_grupo.get("opciones", [])
            
            if ingrediente_objetivo in nombres_ingredientes and opciones:
                # Elegir la primera opción disponible
                opcion_elegida = opciones[0]
                mensaje = self._aplicar_accion_individual(plato, opcion_elegida, ingrediente_objetivo)
                if mensaje:
                    mensajes.append(mensaje)
        
        return mensajes
    
    def _aplicar_una_sola_accion(self, plato: Plato, 
                               acciones_por_ingrediente: List[Dict]) -> List[str]:
        """
        Aplica acciones según el tipo de problema.
        Para restricciones, aplica todas las acciones necesarias (múltiples ingredientes problemáticos).
        Para otros tipos, aplica solo una acción.
        """
        mensajes = []
        
        # Para restricciones, debemos procesar todos los ingredientes problemáticos
        # Para otros tipos, solo una acción
        for accion_grupo in acciones_por_ingrediente:
            opciones = accion_grupo.get("opciones", [])
            ingrediente_objetivo = accion_grupo.get("ingrediente")
            
            if opciones:
                opcion_elegida = opciones[0]
                mensaje = self._aplicar_accion_individual(plato, opcion_elegida, ingrediente_objetivo)
                if mensaje:
                    mensajes.append(mensaje)
                    # No hacer break - continuar procesando todos los ingredientes problemáticos
        
        return mensajes
    
    def _aplicar_accion_individual(self, plato: Plato, accion: Dict, 
                                 ingrediente_objetivo: str) -> Optional[str]:
        """Aplica una acción individual a un plato"""
        
        if "substituir" in accion:
            return self._substituir_ingrediente(plato, accion["substituir"])
        elif "quitar" in accion:
            return self._quitar_ingrediente(plato, accion["quitar"])
        elif "añadir" in accion:
            return self._añadir_ingrediente(plato, accion["añadir"])
        
        return None
    
    def _substituir_ingrediente(self, plato: Plato, substitucion: Dict) -> str:
        """Substituye un ingrediente por otro"""
        ingrediente_origen = substitucion.get("de")
        ingrediente_destino = substitucion.get("por")
        
        # plato.ingredientes es List[str] - nombres de ingredientes
        # Buscar y reemplazar en la lista
        for i, ing_nombre in enumerate(plato.ingredientes):
            if ing_nombre == ingrediente_origen:
                # Verificar que el destino no esté ya presente
                if ingrediente_destino in plato.ingredientes:
                    # Si ya está presente, solo eliminamos el original
                    plato.ingredientes.pop(i)
                    return f"Eliminado {ingrediente_origen} (ya existe {ingrediente_destino})"
                else:
                    # Reemplazar directamente el nombre
                    plato.ingredientes[i] = ingrediente_destino
                    return f"Substituido {ingrediente_origen} por {ingrediente_destino}"
        
        return f"No se encontró {ingrediente_origen} para substituir"
    
    def _quitar_ingrediente(self, plato: Plato, ingrediente_nombre: str) -> str:
        """Quita un ingrediente del plato"""
        ingredientes_originales = len(plato.ingredientes)
        # plato.ingredientes es List[str]
        plato.ingredientes = [ing_nombre for ing_nombre in plato.ingredientes 
                            if ing_nombre != ingrediente_nombre]
        
        if len(plato.ingredientes) < ingredientes_originales:
            return f"Eliminado ingrediente {ingrediente_nombre}"
        else:
            return f"No se encontró {ingrediente_nombre} para eliminar"
    
    def _añadir_ingrediente(self, plato: Plato, ingrediente_nombre: str) -> str:
        """Añade un ingrediente al plato"""
        # Verificar que no esté ya en el plato
        # plato.ingredientes es List[str]
        if ingrediente_nombre in plato.ingredientes:
            return f"El ingrediente {ingrediente_nombre} ya está presente"
        
        # Añadir el nombre del ingrediente directamente
        plato.ingredientes.append(ingrediente_nombre)
        return f"Añadido ingrediente {ingrediente_nombre}"