"""
Validador genérico de restricciones dietéticas basado en datos
"""

from typing import Dict, Any
from conocimiento.models import Plato
from .base import ReglaValidacion, ResultadoValidacion, convertir_a_string


class ValidadorRestriccion(ReglaValidacion):
    """Validador genérico de restricciones que lee configuración de restricciones.json"""
    
    def __init__(self, config_restriccion: Dict[str, Any], ingredientes_db: Dict[str, Dict]):
        """
        Inicializa el validador con la configuración de una restricción
        
        Args:
            config_restriccion: Diccionario con la configuración de la restricción
            ingredientes_db: Base de datos de ingredientes
        """
        self._nombre = config_restriccion['nombre']
        self._descripcion = config_restriccion['descripcion']
        self._categorias_prohibidas = set(config_restriccion.get('categorias_prohibidas', []))
        self._categorias_permitidas = set(config_restriccion.get('categorias_permitidas', []))
        self._ingredientes_prohibidos = set(config_restriccion.get('ingredientes_prohibidos', []))
        self.ingredientes_db = ingredientes_db
    
    @property
    def nombre(self) -> str:
        return f"Restricción {self._nombre.capitalize()}"
    
    @property
    def tipo(self) -> str:
        return "restriccion"
    
    def validar(self, plato: Plato, contexto: Dict[str, Any]) -> ResultadoValidacion:
        """
        Valida que un plato cumpla con la restricción.
        Trabaja directamente con plato.ingredientes como List[str].
        """
        errores = []
        detalles = {
            'restriccion': self._nombre,
            'ingredientes_problematicos': [],
            'categorias_problematicas': [],
            'descripcion': self._descripcion
        }
        
        # plato.ingredientes es List[str] - nombres de ingredientes
        for nombre_ingrediente in plato.ingredientes:
            # Verificar si el ingrediente está explícitamente prohibido
            if nombre_ingrediente in self._ingredientes_prohibidos:
                errores.append(
                    f"Ingrediente prohibido para {self._nombre}: {nombre_ingrediente}"
                )
                detalles['ingredientes_problematicos'].append({
                    'nombre': nombre_ingrediente,
                    'motivo': 'ingrediente_especifico_prohibido'
                })
                continue
            
            # Buscar información del ingrediente en la base de datos
            info_ingrediente = self.ingredientes_db.get(nombre_ingrediente)
            if not info_ingrediente:
                # Si no está en la DB, asumir que es válido (no podemos validar)
                continue
            
            # Verificar categoría del ingrediente
            categoria = info_ingrediente.get('categoria', 'vegetal')
            
            # Si hay categorías prohibidas, verificar que no esté en ellas
            if self._categorias_prohibidas and categoria in self._categorias_prohibidas:
                errores.append(
                    f"Ingrediente con categoría prohibida para {self._nombre}: "
                    f"{nombre_ingrediente} (categoría: {categoria})"
                )
                detalles['ingredientes_problematicos'].append({
                    'nombre': nombre_ingrediente,
                    'categoria': categoria,
                    'motivo': 'categoria_prohibida'
                })
                if categoria not in detalles['categorias_problematicas']:
                    detalles['categorias_problematicas'].append(categoria)
            
            # Si hay categorías permitidas (whitelist), verificar que esté en ellas
            elif self._categorias_permitidas and categoria not in self._categorias_permitidas:
                errores.append(
                    f"Ingrediente con categoría no permitida para {self._nombre}: "
                    f"{nombre_ingrediente} (categoría: {categoria})"
                )
                detalles['ingredientes_problematicos'].append({
                    'nombre': nombre_ingrediente,
                    'categoria': categoria,
                    'motivo': 'categoria_no_permitida'
                })
                if categoria not in detalles['categorias_problematicas']:
                    detalles['categorias_problematicas'].append(categoria)
        
        return ResultadoValidacion(
            valido=len(errores) == 0,
            errores=errores,
            detalles=detalles
        )
