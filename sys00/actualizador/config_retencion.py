"""
Configuración del Sistema de Retención de Casos
==============================================

Define constantes y configuraciones para:
- Límite de memoria (MAX_CASES)
- Pesos para el cálculo de keep_score
- Umbrales de similitud para detección de duplicados
- Escala de satisfacción
"""

from dataclasses import dataclass, field
from typing import Optional
import os
import json


@dataclass
class ConfiguracionRetencion:
    """
    Configuración del sistema de retención de casos.
    
    Atributos:
        max_cases: Máximo número de casos en memoria
        weight_satisfaction: Peso de la satisfacción en keep_score (wS)
        weight_modifications: Peso de modificaciones en keep_score (wM)
        weight_novelty: Peso de la novedad en keep_score (wN)
        similarity_duplicate_threshold: Umbral para considerar casos casi-duplicados
        rating_scale_min: Mínimo de la escala de satisfacción
        rating_scale_max: Máximo de la escala de satisfacción
        require_rating_for_retention: Si True, casos sin rating no se guardan
        default_satisfaction_on_skip: Valor por defecto si usuario salta rating (None = no guardar)
    """
    # Límite de memoria
    max_cases: int = 100
    
    # Pesos para keep_score (deben sumar ~1.0)
    weight_satisfaction: float = 0.4  # wS
    weight_modifications: float = 0.3  # wM  
    weight_novelty: float = 0.3  # wN
    
    # Umbral de similitud para detectar casi-duplicados
    similarity_duplicate_threshold: float = 0.9
    
    # Escala de satisfacción
    rating_scale_min: int = 1
    rating_scale_max: int = 5
    
    # Política de rating
    require_rating_for_retention: bool = False
    default_satisfaction_on_skip: Optional[float] = None  # None = no guardar satisfacción
    
    # Modo interactivo (se detecta automáticamente si no se especifica)
    interactive_mode: Optional[bool] = None
    
    def __post_init__(self):
        """Valida la configuración."""
        # Verificar que los pesos sumen aproximadamente 1.0
        total_weights = self.weight_satisfaction + self.weight_modifications + self.weight_novelty
        if abs(total_weights - 1.0) > 0.05:
            print(f"⚠ Advertencia: Los pesos de retención suman {total_weights:.2f}, no 1.0")
        
        # Verificar rangos válidos
        if self.max_cases < 10:
            raise ValueError("max_cases debe ser al menos 10")
        if self.similarity_duplicate_threshold < 0.5 or self.similarity_duplicate_threshold > 1.0:
            raise ValueError("similarity_duplicate_threshold debe estar entre 0.5 y 1.0")
        if self.rating_scale_min >= self.rating_scale_max:
            raise ValueError("rating_scale_min debe ser menor que rating_scale_max")
    
    def is_interactive(self) -> bool:
        """
        Determina si el sistema está en modo interactivo.
        
        Returns:
            True si hay una terminal interactiva disponible
        """
        if self.interactive_mode is not None:
            return self.interactive_mode
        
        # Detectar automáticamente
        import sys
        try:
            return sys.stdin.isatty() and sys.stdout.isatty()
        except:
            return False
    
    def to_dict(self) -> dict:
        """Convierte la configuración a diccionario."""
        return {
            'max_cases': self.max_cases,
            'weight_satisfaction': self.weight_satisfaction,
            'weight_modifications': self.weight_modifications,
            'weight_novelty': self.weight_novelty,
            'similarity_duplicate_threshold': self.similarity_duplicate_threshold,
            'rating_scale_min': self.rating_scale_min,
            'rating_scale_max': self.rating_scale_max,
            'require_rating_for_retention': self.require_rating_for_retention,
            'default_satisfaction_on_skip': self.default_satisfaction_on_skip
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ConfiguracionRetencion':
        """Crea configuración desde diccionario."""
        return cls(
            max_cases=data.get('max_cases', 100),
            weight_satisfaction=data.get('weight_satisfaction', 0.4),
            weight_modifications=data.get('weight_modifications', 0.3),
            weight_novelty=data.get('weight_novelty', 0.3),
            similarity_duplicate_threshold=data.get('similarity_duplicate_threshold', 0.9),
            rating_scale_min=data.get('rating_scale_min', 1),
            rating_scale_max=data.get('rating_scale_max', 5),
            require_rating_for_retention=data.get('require_rating_for_retention', False),
            default_satisfaction_on_skip=data.get('default_satisfaction_on_skip')
        )
    
    @classmethod
    def load_from_file(cls, filepath: str = None) -> 'ConfiguracionRetencion':
        """
        Carga configuración desde archivo JSON.
        
        Args:
            filepath: Ruta al archivo de configuración. Si None, usa valores por defecto.
            
        Returns:
            ConfiguracionRetencion con los valores cargados o defaults
        """
        if filepath is None:
            filepath = os.path.join(
                os.path.dirname(__file__), '..', 'conocimiento', 'config_retencion.json'
            )
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return cls.from_dict(data)
            except Exception as e:
                print(f"⚠ Error cargando configuración de retención: {e}. Usando defaults.")
        
        return cls()
    
    def save_to_file(self, filepath: str = None) -> bool:
        """
        Guarda configuración a archivo JSON.
        
        Args:
            filepath: Ruta destino. Si None, usa ubicación por defecto.
            
        Returns:
            True si se guardó exitosamente
        """
        if filepath is None:
            filepath = os.path.join(
                os.path.dirname(__file__), '..', 'conocimiento', 'config_retencion.json'
            )
        
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando configuración: {e}")
            return False


# Configuración por defecto global
CONFIG_RETENCION_DEFAULT = ConfiguracionRetencion()
