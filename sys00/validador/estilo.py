"""
Validador genérico de estilo culinario basado en datos
"""

from typing import Dict, Any
from conocimiento.models import Plato
from .base import ReglaValidacion, ResultadoValidacion


class ValidadorEstilo(ReglaValidacion):
    """Validador genérico de estilos que lee configuración de estilos.json"""
    
    def __init__(self, config_estilo: Dict[str, Any], tecnicas_db: Dict[str, Dict]):
        """
        Inicializa el validador con la configuración de un estilo
        
        Args:
            config_estilo: Diccionario con la configuración del estilo específico
            tecnicas_db: Base de datos de técnicas de cocción
        """
        self._nombre = config_estilo['nombre']
        self._descripcion = config_estilo['descripcion']
        self._tecnicas_requeridas = set(config_estilo.get('tecnicas_requeridas', []))
        self._tecnicas_preferidas = set(config_estilo.get('tecnicas_preferidas', []))
        self._tecnicas_excluidas = set(config_estilo.get('tecnicas_excluidas', []))
        self._ingredientes_tipicos = set(config_estilo.get('ingredientes_tipicos', []))
        self._caracteristicas = config_estilo.get('caracteristicas', [])
        self.tecnicas_db = tecnicas_db
    
    @property
    def nombre(self) -> str:
        return f"Estilo {self._nombre.capitalize()}"
    
    @property
    def tipo(self) -> str:
        return "estilo"
    
    def validar(self, plato: Plato, contexto: Dict[str, Any]) -> ResultadoValidacion:
        """Valida que un plato respete el estilo culinario"""
        tecnica_plato_str = self._obtener_tecnica_string(plato.tecnica_coccion)
        
        errores = []
        advertencias = []
        detalles = {
            'estilo': self._nombre,
            'descripcion': self._descripcion,
            'tecnica_plato': tecnica_plato_str,
            'tecnicas_requeridas': list(self._tecnicas_requeridas),
            'tecnicas_preferidas': list(self._tecnicas_preferidas),
            'tecnicas_excluidas': list(self._tecnicas_excluidas),
            'caracteristicas': self._caracteristicas
        }
        
        # Verificar técnicas excluidas (error crítico)
        if tecnica_plato_str in self._tecnicas_excluidas:
            errores.append(
                f"Técnica '{tecnica_plato_str}' no compatible con estilo {self._nombre}"
            )
            detalles['violacion'] = 'tecnica_excluida'
        
        # Verificar técnicas requeridas (si las hay)
        if self._tecnicas_requeridas and tecnica_plato_str not in self._tecnicas_requeridas:
            # Solo error si hay técnicas estrictamente requeridas
            if len(self._tecnicas_requeridas) > 0 and not self._tecnicas_preferidas:
                errores.append(
                    f"Estilo {self._nombre} requiere una de estas técnicas: "
                    f"{', '.join(self._tecnicas_requeridas)}"
                )
                detalles['violacion'] = 'tecnica_no_requerida'
        
        # Verificar técnicas preferidas (advertencia si no se usa)
        if self._tecnicas_preferidas and tecnica_plato_str not in self._tecnicas_preferidas:
            if not errores:  # Solo advertir si no hay errores
                advertencias.append(
                    f"Se recomienda usar técnicas típicas de {self._nombre}: "
                    f"{', '.join(self._tecnicas_preferidas)}"
                )
        
        # Verificar ingredientes típicos (informativo)
        if self._ingredientes_tipicos:
            ingredientes_plato = {ing.nombre for ing in plato.ingredientes}
            ingredientes_tipicos_encontrados = ingredientes_plato.intersection(self._ingredientes_tipicos)
            
            detalles['ingredientes_tipicos_encontrados'] = list(ingredientes_tipicos_encontrados)
            
            if ingredientes_tipicos_encontrados:
                detalles['info'] = f"Usa {len(ingredientes_tipicos_encontrados)} ingredientes típicos del estilo"
        
        return ResultadoValidacion(
            valido=len(errores) == 0,
            errores=errores,
            advertencias=advertencias,
            detalles=detalles
        )
    
    def _obtener_tecnica_string(self, tecnica_coccion) -> str:
        """Obtiene la técnica como string, manejando listas y enums"""
        # Si es una lista, tomar el primer elemento
        if isinstance(tecnica_coccion, list):
            if len(tecnica_coccion) > 0:
                tecnica = tecnica_coccion[0]
            else:
                return "desconocida"
        else:
            tecnica = tecnica_coccion
        
        # Convertir enum a string
        if hasattr(tecnica, 'value'):
            return tecnica.value
        return str(tecnica).lower()
