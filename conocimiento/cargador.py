"""
Módulo centralizado para cargar datos del conocimiento
Evita duplicación de código de carga de JSON entre módulos
"""

import json
import os
from typing import Dict, List, Any


class CargadorConocimiento:
    """Clase para cargar datos de la base de conocimiento de forma centralizada"""
    
    def __init__(self):
        """Inicializa el cargador con la ruta base de conocimiento"""
        self.ruta_base = os.path.dirname(__file__)
    
    def cargar_json(self, nombre_archivo: str) -> Any:
        """
        Carga un archivo JSON desde la carpeta conocimiento
        
        Args:
            nombre_archivo: Nombre del archivo JSON (ej: 'ingredientes.json')
            
        Returns:
            Contenido del archivo JSON (lista o diccionario)
        """
        ruta_completa = os.path.join(self.ruta_base, nombre_archivo)
        try:
            with open(ruta_completa, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Advertencia: {nombre_archivo} no encontrado")
            return [] if 'json' in nombre_archivo else {}
        except json.JSONDecodeError as e:
            print(f"Error al cargar {nombre_archivo}: {e}")
            return [] if 'json' in nombre_archivo else {}
    
    def cargar_ingredientes(self) -> Dict[str, Dict]:
        """
        Carga la base de datos de ingredientes
        
        Returns:
            Diccionario con ingredientes indexados por nombre
        """
        ingredientes_lista = self.cargar_json('ingredientes.json')
        return {ing['nombre']: ing for ing in ingredientes_lista}
    
    def cargar_platos(self) -> Dict[str, Dict]:
        """
        Carga la base de datos de platos
        
        Returns:
            Diccionario con platos indexados por nombre
        """
        platos_lista = self.cargar_json('platos.json')
        return {plato['nombre']: plato for plato in platos_lista}
    
    def cargar_casos(self) -> List[Dict]:
        """
        Carga la base de casos
        
        Returns:
            Lista de casos
        """
        return self.cargar_json('casos.json')
    
    def cargar_restricciones(self) -> List[Dict]:
        """
        Carga las restricciones dietéticas
        
        Returns:
            Lista de restricciones
        """
        return self.cargar_json('restricciones.json')
    
    def cargar_tradiciones(self) -> List[Dict]:
        """
        Carga las tradiciones culinarias
        
        Returns:
            Lista de tradiciones
        """
        return self.cargar_json('tradiciones.json')
    
    def cargar_estilos(self) -> List[Dict]:
        """
        Carga los estilos culinarios
        
        Returns:
            Lista de estilos
        """
        return self.cargar_json('estilos.json')
    
    def cargar_reparaciones(self) -> Dict[str, Any]:
        """
        Carga las reglas de reparación
        
        Returns:
            Diccionario con reglas de reparación
        """
        return self.cargar_json('reparaciones.json')


# Instancia global para uso en todo el sistema
cargador = CargadorConocimiento()
