"""
Validador de temporada de ingredientes
"""

from typing import Dict, Any, List
from conocimiento.models import Plato
from .base import ReglaValidacion, ResultadoValidacion, convertir_a_string


class ValidadorTemporada(ReglaValidacion):
    """Valida ingredientes de temporada"""
    
    def __init__(self, ingredientes_db: Dict[str, Dict]):
        self.ingredientes_db = ingredientes_db
    
    @property
    def nombre(self) -> str:
        return "Validación de Temporada"
    
    @property
    def tipo(self) -> str:
        return "temporada"
    
    def validar(self, plato: Plato, contexto: Dict[str, Any]) -> ResultadoValidacion:
        """Valida que los ingredientes sean de la temporada especificada"""
        temporada_objetivo = contexto.get('temporada')
        if not temporada_objetivo:
            return ResultadoValidacion(
                valido=False,
                errores=["No se especificó temporada objetivo para validar"]
            )
        
        temporada_str = convertir_a_string(temporada_objetivo)
        errores = []
        advertencias = []
        detalles = {
            'ingredientes_fuera_temporada': [],
            'temporada_objetivo': temporada_str
        }
        
        # plato.ingredientes es List[str] - nombres de ingredientes
        for nombre_ingrediente in plato.ingredientes:
            info_ingrediente = self.ingredientes_db.get(nombre_ingrediente)
            
            if info_ingrediente:
                temporadas_ingrediente = info_ingrediente.get('temporada', [])
                
                if temporada_str not in temporadas_ingrediente:
                    # Solo considerar error si es vegetal o fruta (ingredientes principales)
                    categoria = info_ingrediente.get('categoria', '')
                    
                    if categoria in ['vegetal', 'fruta']:
                        errores.append(
                            f"Ingrediente fuera de temporada: {nombre_ingrediente} "
                            f"(disponible en: {', '.join(temporadas_ingrediente)})"
                        )
                    else:
                        advertencias.append(
                            f"Condimento/cereal fuera de temporada: {nombre_ingrediente}"
                        )
                    
                    detalles['ingredientes_fuera_temporada'].append({
                        'nombre': nombre_ingrediente,
                        'categoria': categoria,
                        'temporadas_disponibles': temporadas_ingrediente,
                        'severidad': 'error' if categoria in ['vegetal', 'fruta'] else 'advertencia'
                    })
            else:
                advertencias.append(f"Ingrediente no encontrado en DB: {nombre_ingrediente}")
        
        return ResultadoValidacion(
            valido=len(errores) == 0,
            errores=errores,
            advertencias=advertencias,
            detalles=detalles
        )
