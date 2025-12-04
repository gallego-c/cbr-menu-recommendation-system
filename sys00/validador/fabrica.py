"""
Fábrica de validadores basada en datos
"""

import json
import os
from typing import Dict, Optional, List
from .base import ReglaValidacion
from .restricciones import ValidadorRestriccion
from .temporada import ValidadorTemporada
from .tradicion import ValidadorTradicion
from .estilo import ValidadorEstilo


class FabricaValidadores:
    """Factory para crear validadores genéricos desde bases de conocimiento"""
    
    def __init__(self, ingredientes_db: Dict[str, Dict]):
        self.ingredientes_db = ingredientes_db
        
        # Cargar configuraciones desde archivos JSON
        self._restricciones_config = self._cargar_json('restricciones.json')
        self._tradiciones_config = self._cargar_json('tradiciones.json')
        self._tecnicas_config = self._cargar_json('tecnicas.json')
        self._estilos_config = self._cargar_json('estilos.json')
        
        # Crear índices por nombre para acceso rápido
        self._restricciones_por_nombre = {
            r['nombre']: r for r in self._restricciones_config
        }
        self._tradiciones_por_nombre = {
            t['nombre']: t for t in self._tradiciones_config
        }
        self._tecnicas_por_nombre = {
            t['nombre']: t for t in self._tecnicas_config
        }
        self._estilos_por_nombre = {
            e['nombre']: e for e in self._estilos_config
        }
        
        # Validadores singleton
        self._validador_temporada = ValidadorTemporada(ingredientes_db)
    
    def _cargar_json(self, filename: str) -> List[Dict]:
        """Carga un archivo JSON de la carpeta conocimiento"""
        try:
            ruta = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'conocimiento',
                filename
            )
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Advertencia: {filename} no encontrado")
            return []
        except json.JSONDecodeError as e:
            print(f"Error al cargar {filename}: {e}")
            return []
    
    def crear_validador_restriccion(self, restriccion: str) -> Optional[ReglaValidacion]:
        """Crea validador para una restricción específica desde la configuración"""
        config = self._restricciones_por_nombre.get(restriccion.lower())
        if config:
            return ValidadorRestriccion(config, self.ingredientes_db)
        return None
    
    def crear_validador_temporada(self) -> ReglaValidacion:
        """Crea validador de temporada"""
        return self._validador_temporada
    
    def crear_validador_tradicion(self, tradicion: str) -> Optional[ReglaValidacion]:
        """Crea validador para una tradición específica desde la configuración"""
        config = self._tradiciones_por_nombre.get(tradicion.lower())
        if config:
            return ValidadorTradicion(config, self._tradiciones_por_nombre)
        return None
    
    def listar_restricciones_disponibles(self) -> List[str]:
        """Lista todas las restricciones que pueden validarse"""
        return list(self._restricciones_por_nombre.keys())
    
    def listar_tradiciones_disponibles(self) -> List[str]:
        """Lista todas las tradiciones que pueden validarse"""
        return list(self._tradiciones_por_nombre.keys())
    
    def listar_tecnicas_disponibles(self) -> List[str]:
        """Lista todas las técnicas disponibles"""
        return list(self._tecnicas_por_nombre.keys())
    
    def crear_validador_estilo(self, estilo: str) -> Optional[ReglaValidacion]:
        """Crea validador para un estilo específico desde la configuración"""
        config = self._estilos_por_nombre.get(estilo.lower())
        if config:
            return ValidadorEstilo(config, self._tecnicas_por_nombre)
        return None
    
    def listar_estilos_disponibles(self) -> List[str]:
        """Lista todos los estilos disponibles"""
        return list(self._estilos_por_nombre.keys())
    
    def obtener_info_restriccion(self, restriccion: str) -> Optional[Dict]:
        """Obtiene información sobre una restricción"""
        return self._restricciones_por_nombre.get(restriccion.lower())
    
    def obtener_info_tradicion(self, tradicion: str) -> Optional[Dict]:
        """Obtiene información sobre una tradición"""
        return self._tradiciones_por_nombre.get(tradicion.lower())
    
    def obtener_info_tecnica(self, tecnica: str) -> Optional[Dict]:
        """Obtiene información sobre una técnica"""
        return self._tecnicas_por_nombre.get(tecnica.lower())
    
    def obtener_info_estilo(self, estilo: str) -> Optional[Dict]:
        """Obtiene información sobre un estilo"""
        return self._estilos_por_nombre.get(estilo.lower())
