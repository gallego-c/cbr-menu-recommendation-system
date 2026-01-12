"""
Validador completo que coordina todas las validaciones
"""

import json
import os
from typing import List, Dict, Any, Optional
from conocimiento.models import Plato
from conocimiento import cargador
from .base import ResultadoValidacion
from .fabrica import FabricaValidadores


class ValidadorCompleto:
    """Validador principal que coordina todas las validaciones"""
    
    def __init__(
        self,
        ingredientes_db: Optional[Dict[str, Dict]] = None,
        restricciones_config: Optional[List[Dict]] = None,
        tradiciones_config: Optional[List[Dict]] = None,
        estilos_config: Optional[List[Dict]] = None
    ):
        """
        Inicializa el validador con configuraciones opcionales pre-cargadas.
        Si no se proporcionan, las carga automáticamente usando el cargador centralizado.
        
        Args:
            ingredientes_db: Base de datos de ingredientes
            restricciones_config: Configuración de restricciones
            tradiciones_config: Configuración de tradiciones
            estilos_config: Configuración de estilos
        """
        # Cargar datos si no se proporcionan usando el cargador centralizado
        self.ingredientes_db = ingredientes_db or cargador.cargar_ingredientes()
        restricciones = restricciones_config or cargador.cargar_restricciones()
        tradiciones = tradiciones_config or cargador.cargar_tradiciones()
        estilos = estilos_config or cargador.cargar_estilos()
        
        # Crear fábrica con datos pre-cargados
        self.fabrica = FabricaValidadores(
            self.ingredientes_db,
            restricciones,
            tradiciones,
            estilos
        )
    
    def validar_plato_restricciones(self, plato: Plato, restricciones: List[str]) -> Dict[str, ResultadoValidacion]:
        """
        Valida un plato contra múltiples restricciones
        
        Args:
            plato: Plato a validar
            restricciones: Lista de restricciones a verificar
            
        Returns:
            Diccionario con resultado de cada restricción
        """
        resultados = {}
        
        for restriccion in restricciones:
            validador = self.fabrica.crear_validador_restriccion(restriccion)
            if validador:
                resultado = validador.validar(plato, {})
                resultados[restriccion] = resultado
            else:
                resultados[restriccion] = ResultadoValidacion(
                    valido=False,
                    errores=[f"Restricción '{restriccion}' no reconocida"]
                )
        
        return resultados
    
    def validar_plato_completo(self, plato: Plato, contexto: Dict[str, Any]) -> Dict[str, ResultadoValidacion]:
        """
        Validación completa de un plato contra todos los criterios
        
        Args:
            plato: Plato a validar
            contexto: Contexto con restricciones, temporada, tradición, etc.
            
        Returns:
            Diccionario con todos los resultados de validación
        """
        resultados = {}
        
        # Validar restricciones
        restricciones = contexto.get('restricciones', [])
        if restricciones:
            if isinstance(restricciones[0], str):
                # Lista de strings
                restricciones_str = restricciones
            else:
                # Lista de enums
                restricciones_str = [r.value for r in restricciones]
            
            resultados_restricciones = self.validar_plato_restricciones(plato, restricciones_str)
            resultados.update(resultados_restricciones)
        
        # Validar temporada
        if 'temporada' in contexto:
            validador_temporada = self.fabrica.crear_validador_temporada()
            resultados['temporada'] = validador_temporada.validar(plato, contexto)
        
        # Validar tradición (si está especificada y no es None)
        if 'tradicion' in contexto and contexto['tradicion'] is not None:
            tradicion_str = contexto['tradicion']
            if hasattr(tradicion_str, 'value'):
                tradicion_str = tradicion_str.value
            tradicion_str = str(tradicion_str).lower()
            
            validador_tradicion = self.fabrica.crear_validador_tradicion(tradicion_str)
            if validador_tradicion:
                resultados['tradicion'] = validador_tradicion.validar(plato, contexto)
            else:
                resultados['tradicion'] = ResultadoValidacion(
                    valido=False,
                    errores=[f"Tradición '{tradicion_str}' no reconocida. "
                            f"Tradiciones disponibles: {', '.join(self.fabrica.listar_tradiciones_disponibles())}"]
                )
        
        # Validar estilo (incluye validación de técnicas)
        if 'estilo' in contexto:
            estilo_str = contexto['estilo']
            if hasattr(estilo_str, 'value'):
                estilo_str = estilo_str.value
            estilo_str = str(estilo_str).lower()
            
            validador_estilo = self.fabrica.crear_validador_estilo(estilo_str)
            if validador_estilo:
                resultados['estilo'] = validador_estilo.validar(plato, contexto)
            else:
                resultados['estilo'] = ResultadoValidacion(
                    valido=False,
                    errores=[f"Estilo '{estilo_str}' no reconocido. "
                            f"Estilos disponibles: {', '.join(self.fabrica.listar_estilos_disponibles())}"]
                )
        
        return resultados
    
    def generar_informe_validacion(self, resultados: Dict[str, ResultadoValidacion]) -> Dict[str, Any]:
        """
        Genera un informe consolidado de los resultados de validación
        
        Args:
            resultados: Resultados de validación por criterio
            
        Returns:
            Informe consolidado
        """
        informe = {
            'validacion_general': True,
            'total_criterios': len(resultados),
            'criterios_exitosos': 0,
            'criterios_fallidos': 0,
            'errores_totales': 0,
            'advertencias_totales': 0,
            'detalles_por_criterio': {},
            'resumen_errores': [],
            'resumen_advertencias': []
        }
        
        for criterio, resultado in resultados.items():
            informe['detalles_por_criterio'][criterio] = {
                'valido': resultado.valido,
                'num_errores': len(resultado.errores),
                'num_advertencias': len(resultado.advertencias),
                'errores': resultado.errores,
                'advertencias': resultado.advertencias,
                'detalles': resultado.detalles
            }
            
            if resultado.valido:
                informe['criterios_exitosos'] += 1
            else:
                informe['criterios_fallidos'] += 1
                informe['validacion_general'] = False
            
            informe['errores_totales'] += len(resultado.errores)
            informe['advertencias_totales'] += len(resultado.advertencias)
            
            # Agregar al resumen
            for error in resultado.errores:
                informe['resumen_errores'].append(f"{criterio}: {error}")
            for advertencia in resultado.advertencias:
                informe['resumen_advertencias'].append(f"{criterio}: {advertencia}")
        
        return informe
    
    def listar_capacidades(self) -> Dict[str, List[str]]:
        """Lista todas las capacidades de validación disponibles"""
        return {
            'restricciones': self.fabrica.listar_restricciones_disponibles(),
            'tradiciones': self.fabrica.listar_tradiciones_disponibles(),
            'estilos': self.fabrica.listar_estilos_disponibles(),
            'otros_criterios': ['temporada'],
            'ingredientes_en_db': list(self.ingredientes_db.keys()),
            'nota': 'Las técnicas se validan automáticamente dentro del estilo culinario'
        }
    
    @staticmethod
    def agrupar_errores_por_plato(errores: List[str]) -> Dict[str, List[str]]:
        """
        Agrupa errores por nombre de plato.
        
        Args:
            errores: Lista de errores en formato "tipo (Nombre del Plato): error"
            
        Returns:
            Diccionario con errores agrupados por nombre de plato
        """
        errores_agrupados = {}
        
        for error in errores:
            # Extraer nombre del plato del error (formato: "tipo (Nombre del Plato): error")
            if '(' in error and ')' in error:
                inicio = error.find('(') + 1
                fin = error.find(')')
                nombre_plato = error[inicio:fin]
                
                if nombre_plato not in errores_agrupados:
                    errores_agrupados[nombre_plato] = []
                errores_agrupados[nombre_plato].append(error)
        
        return errores_agrupados
    
    @staticmethod
    def extraer_tipo_problema(error: str) -> str:
        """
        Extrae el tipo de problema de un mensaje de error.
        
        Args:
            error: Mensaje de error
            
        Returns:
            Tipo de problema: 'restricciones', 'temporada', 'tradicion', 'coherencia', 'sabor'
        """
        error_lower = error.lower()
        
        if 'restricción' in error_lower or 'restriccion' in error_lower:
            return 'restricciones'
        elif 'temporada' in error_lower:
            return 'temporada'
        elif 'tradición' in error_lower or 'tradicion' in error_lower:
            return 'tradicion'
        elif 'estilo' in error_lower:
            return 'coherencia'
        elif 'sabor' in error_lower:
            return 'sabor'
        else:
            return 'restricciones'  # Por defecto
