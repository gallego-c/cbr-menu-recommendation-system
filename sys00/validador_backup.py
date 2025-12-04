"""
Sistema modular de validación para restricciones dietéticas y preferencias

Este módulo valida menús y platos contra restricciones usando datos 
de la carpeta conocimiento de manera completamente modular.
"""

import json
import os
from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Importar modelos del sistema
from conocimiento.models import (
    Plato, Ingrediente, Menu, Restriccion, Temporada, 
    CategoriaIngrediente, TradicionCultural, TecnicaCoccion
)


@dataclass
class ResultadoValidacion:
    """Resultado de una validación"""
    valido: bool
    errores: List[str] = None
    advertencias: List[str] = None
    detalles: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errores is None:
            self.errores = []
        if self.advertencias is None:
            self.advertencias = []
        if self.detalles is None:
            self.detalles = {}


class ReglaValidacion(ABC):
    """Interfaz base para todas las reglas de validación"""
    
    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre descriptivo de la regla"""
        pass
    
    @property
    @abstractmethod
    def tipo(self) -> str:
        """Tipo de validación (restriccion, temporada, etc.)"""
        pass
    
    @abstractmethod
    def validar(self, objetivo: Any, contexto: Dict[str, Any]) -> ResultadoValidacion:
        """
        Valida el objetivo contra esta regla
        
        Args:
            objetivo: Objeto a validar (Plato, Menu, etc.)
            contexto: Contexto adicional para la validación
            
        Returns:
            Resultado de la validación
        """
        pass


class ValidadorRestriccionVegana(ReglaValidacion):
    """Valida restricción vegana"""
    
    @property
    def nombre(self) -> str:
        return "Restricción Vegana"
    
    @property
    def tipo(self) -> str:
        return "restriccion"
    
    def validar(self, plato: Plato, contexto: Dict[str, Any]) -> ResultadoValidacion:
        """Valida que un plato sea vegano"""
        errores = []
        detalles = {
            'ingredientes_problematicos': [],
            'categorias_no_veganas_encontradas': []
        }
        
        categorias_no_veganas = {"animal", "lacteo"}
        
        for ingrediente in plato.ingredientes:
            categoria = self._obtener_categoria_string(ingrediente.categoria)
            
            if categoria in categorias_no_veganas:
                errores.append(f"Ingrediente no vegano: {ingrediente.nombre} (categoría: {categoria})")
                detalles['ingredientes_problematicos'].append({
                    'nombre': ingrediente.nombre,
                    'categoria': categoria,
                    'motivo': 'categoria_no_vegana'
                })
                detalles['categorias_no_veganas_encontradas'].append(categoria)
        
        return ResultadoValidacion(
            valido=len(errores) == 0,
            errores=errores,
            detalles=detalles
        )
    
    def _obtener_categoria_string(self, categoria) -> str:
        """Convierte categoría a string independientemente del tipo"""
        if hasattr(categoria, 'value'):
            return categoria.value
        return str(categoria)


class ValidadorRestriccionSinLactosa(ReglaValidacion):
    """Valida restricción sin lactosa"""
    
    @property
    def nombre(self) -> str:
        return "Restricción Sin Lactosa"
    
    @property
    def tipo(self) -> str:
        return "restriccion"
    
    def validar(self, plato: Plato, contexto: Dict[str, Any]) -> ResultadoValidacion:
        """Valida que un plato no contenga lactosa"""
        errores = []
        detalles = {'ingredientes_con_lactosa': []}
        
        for ingrediente in plato.ingredientes:
            categoria = self._obtener_categoria_string(ingrediente.categoria)
            
            if categoria == "lacteo":
                errores.append(f"Ingrediente con lactosa: {ingrediente.nombre}")
                detalles['ingredientes_con_lactosa'].append({
                    'nombre': ingrediente.nombre,
                    'categoria': categoria
                })
        
        return ResultadoValidacion(
            valido=len(errores) == 0,
            errores=errores,
            detalles=detalles
        )
    
    def _obtener_categoria_string(self, categoria) -> str:
        if hasattr(categoria, 'value'):
            return categoria.value
        return str(categoria)


class ValidadorRestriccionVegetariana(ReglaValidacion):
    """Valida restricción vegetariana"""
    
    @property
    def nombre(self) -> str:
        return "Restricción Vegetariana"
    
    @property
    def tipo(self) -> str:
        return "restriccion"
    
    def validar(self, plato: Plato, contexto: Dict[str, Any]) -> ResultadoValidacion:
        """Valida que un plato sea vegetariano"""
        errores = []
        detalles = {'ingredientes_animales': []}
        
        for ingrediente in plato.ingredientes:
            categoria = self._obtener_categoria_string(ingrediente.categoria)
            
            if categoria == "animal":
                errores.append(f"Ingrediente animal: {ingrediente.nombre}")
                detalles['ingredientes_animales'].append({
                    'nombre': ingrediente.nombre,
                    'categoria': categoria
                })
        
        return ResultadoValidacion(
            valido=len(errores) == 0,
            errores=errores,
            detalles=detalles
        )
    
    def _obtener_categoria_string(self, categoria) -> str:
        if hasattr(categoria, 'value'):
            return categoria.value
        return str(categoria)


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
        
        temporada_str = self._obtener_temporada_string(temporada_objetivo)
        errores = []
        advertencias = []
        detalles = {
            'ingredientes_fuera_temporada': [],
            'temporada_objetivo': temporada_str
        }
        
        for ingrediente in plato.ingredientes:
            info_ingrediente = self.ingredientes_db.get(ingrediente.nombre)
            
            if info_ingrediente:
                temporadas_ingrediente = info_ingrediente.get('temporada', [])
                
                if temporada_str not in temporadas_ingrediente:
                    # Solo considerar error si es vegetal o fruta (ingredientes principales)
                    categoria = info_ingrediente.get('categoria', '')
                    
                    if categoria in ['vegetal', 'fruta']:
                        errores.append(
                            f"Ingrediente fuera de temporada: {ingrediente.nombre} "
                            f"(disponible en: {', '.join(temporadas_ingrediente)})"
                        )
                    else:
                        advertencias.append(
                            f"Condimento/cereal fuera de temporada: {ingrediente.nombre}"
                        )
                    
                    detalles['ingredientes_fuera_temporada'].append({
                        'nombre': ingrediente.nombre,
                        'categoria': categoria,
                        'temporadas_disponibles': temporadas_ingrediente,
                        'severidad': 'error' if categoria in ['vegetal', 'fruta'] else 'advertencia'
                    })
            else:
                advertencias.append(f"Ingrediente no encontrado en DB: {ingrediente.nombre}")
        
        return ResultadoValidacion(
            valido=len(errores) == 0,
            errores=errores,
            advertencias=advertencias,
            detalles=detalles
        )
    
    def _obtener_temporada_string(self, temporada) -> str:
        if hasattr(temporada, 'value'):
            return temporada.value
        return str(temporada).lower()


class ValidadorTradicion(ReglaValidacion):
    """Valida tradición culinaria"""
    
    def __init__(self, ingredientes_db: Dict[str, Dict]):
        self.ingredientes_db = ingredientes_db
        
        # Mapeo de tradiciones a ingredientes característicos
        self.ingredientes_por_tradicion = {
            'catalana': ['aceite_oliva', 'ajo', 'tomate', 'sal'],
            'mexicana': ['chile', 'cilantro', 'aguacate', 'tortilla_maiz', 'limon']
        }
    
    @property
    def nombre(self) -> str:
        return "Validación de Tradición"
    
    @property
    def tipo(self) -> str:
        return "tradicion"
    
    def validar(self, plato: Plato, contexto: Dict[str, Any]) -> ResultadoValidacion:
        """Valida que un plato respete la tradición culinaria"""
        tradicion_objetivo = contexto.get('tradicion')
        if not tradicion_objetivo:
            return ResultadoValidacion(
                valido=False,
                errores=["No se especificó tradición objetivo"]
            )
        
        tradicion_str = self._obtener_tradicion_string(tradicion_objetivo)
        
        ingredientes_plato = {ing.nombre for ing in plato.ingredientes}
        ingredientes_esperados = set(self.ingredientes_por_tradicion.get(tradicion_str, []))
        ingredientes_encontrados = ingredientes_plato.intersection(ingredientes_esperados)
        
        # Buscar ingredientes de otras tradiciones
        ingredientes_conflicto = []
        for otra_tradicion, ingredientes_otra in self.ingredientes_por_tradicion.items():
            if otra_tradicion != tradicion_str:
                conflictos = ingredientes_plato.intersection(set(ingredientes_otra))
                if conflictos:
                    ingredientes_conflicto.extend([
                        {'ingrediente': ing, 'tradicion_conflicto': otra_tradicion}
                        for ing in conflictos
                    ])
        
        errores = []
        advertencias = []
        detalles = {
            'tradicion_objetivo': tradicion_str,
            'ingredientes_esperados': list(ingredientes_esperados),
            'ingredientes_encontrados': list(ingredientes_encontrados),
            'ingredientes_conflicto': ingredientes_conflicto,
            'porcentaje_coherencia': 0
        }
        
        # Calcular coherencia
        if ingredientes_esperados:
            coherencia = len(ingredientes_encontrados) / len(ingredientes_esperados)
            detalles['porcentaje_coherencia'] = coherencia * 100
            
            if coherencia < 0.3:
                errores.append(
                    f"Muy pocos ingredientes de tradición {tradicion_str}: "
                    f"{len(ingredientes_encontrados)}/{len(ingredientes_esperados)}"
                )
            elif coherencia < 0.6:
                advertencias.append(
                    f"Coherencia baja con tradición {tradicion_str}: "
                    f"{coherencia:.1%}"
                )
        
        # Reportar conflictos
        for conflicto in ingredientes_conflicto:
            errores.append(
                f"Ingrediente de tradición {conflicto['tradicion_conflicto']}: "
                f"{conflicto['ingrediente']}"
            )
        
        return ResultadoValidacion(
            valido=len(errores) == 0,
            errores=errores,
            advertencias=advertencias,
            detalles=detalles
        )
    
    def _obtener_tradicion_string(self, tradicion) -> str:
        if hasattr(tradicion, 'value'):
            return tradicion.value
        return str(tradicion).lower()


class ValidadorTecnicaCoccion(ReglaValidacion):
    """Valida técnica de cocción"""
    
    @property
    def nombre(self) -> str:
        return "Validación de Técnica"
    
    @property
    def tipo(self) -> str:
        return "tecnica"
    
    def validar(self, plato: Plato, contexto: Dict[str, Any]) -> ResultadoValidacion:
        """Valida que la técnica de cocción sea la esperada"""
        tecnica_objetivo = contexto.get('tecnica')
        if not tecnica_objetivo:
            return ResultadoValidacion(valido=True)  # Sin restricción
        
        tecnica_objetivo_str = self._obtener_tecnica_string(tecnica_objetivo)
        tecnica_plato_str = self._obtener_tecnica_string(plato.tecnica)
        
        if tecnica_plato_str != tecnica_objetivo_str:
            return ResultadoValidacion(
                valido=False,
                errores=[f"Técnica incorrecta: {tecnica_plato_str} (esperada: {tecnica_objetivo_str})"],
                detalles={
                    'tecnica_actual': tecnica_plato_str,
                    'tecnica_esperada': tecnica_objetivo_str
                }
            )
        
        return ResultadoValidacion(
            valido=True,
            detalles={
                'tecnica_validada': tecnica_plato_str
            }
        )
    
    def _obtener_tecnica_string(self, tecnica) -> str:
        if hasattr(tecnica, 'value'):
            return tecnica.value
        return str(tecnica).lower()


class FabricaValidadores:
    """Factory para crear validadores según el tipo de restricción"""
    
    def __init__(self, ingredientes_db: Dict[str, Dict]):
        self.ingredientes_db = ingredientes_db
        
        # Registro de validadores por tipo de restricción
        self._validadores_restriccion = {
            'vegano': ValidadorRestriccionVegana(),
            'sin_lactosa': ValidadorRestriccionSinLactosa(),
            'vegetariano': ValidadorRestriccionVegetariana()
        }
        
        # Validadores que requieren base de datos
        self._validador_temporada = ValidadorTemporada(ingredientes_db)
        self._validador_tradicion = ValidadorTradicion(ingredientes_db)
        self._validador_tecnica = ValidadorTecnicaCoccion()
    
    def crear_validador_restriccion(self, restriccion: str) -> Optional[ReglaValidacion]:
        """Crea validador para una restricción específica"""
        return self._validadores_restriccion.get(restriccion.lower())
    
    def crear_validador_temporada(self) -> ReglaValidacion:
        """Crea validador de temporada"""
        return self._validador_temporada
    
    def crear_validador_tradicion(self) -> ReglaValidacion:
        """Crea validador de tradición"""
        return self._validador_tradicion
    
    def crear_validador_tecnica(self) -> ReglaValidacion:
        """Crea validador de técnica"""
        return self._validador_tecnica
    
    def listar_restricciones_disponibles(self) -> List[str]:
        """Lista todas las restricciones que pueden validarse"""
        return list(self._validadores_restriccion.keys())


class ValidadorCompleto:
    """Validador principal que coordina todas las validaciones"""
    
    def __init__(self):
        """Inicializa el validador cargando el conocimiento"""
        self.ingredientes_db = self._cargar_ingredientes()
        self.fabrica = FabricaValidadores(self.ingredientes_db)
    
    def _cargar_ingredientes(self) -> Dict[str, Dict]:
        """Carga la base de datos de ingredientes"""
        try:
            ruta_ingredientes = os.path.join(
                os.path.dirname(__file__), 'conocimiento', 'ingredientes.json'
            )
            with open(ruta_ingredientes, 'r', encoding='utf-8') as f:
                ingredientes_lista = json.load(f)
            
            return {ing['nombre']: ing for ing in ingredientes_lista}
        
        except FileNotFoundError:
            print("Error: Archivo ingredientes.json no encontrado")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error al cargar ingredientes.json: {e}")
            return {}
    
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
        
        # Validar tradición
        if 'tradicion' in contexto:
            validador_tradicion = self.fabrica.crear_validador_tradicion()
            resultados['tradicion'] = validador_tradicion.validar(plato, contexto)
        
        # Validar técnica
        if 'tecnica' in contexto:
            validador_tecnica = self.fabrica.crear_validador_tecnica()
            resultados['tecnica'] = validador_tecnica.validar(plato, contexto)
        
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
            'otros_criterios': ['temporada', 'tradicion', 'tecnica'],
            'ingredientes_en_db': list(self.ingredientes_db.keys())
        }
