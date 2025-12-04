import json
from dataclasses import dataclass, field, asdict
from typing import List, Any, Dict, Union, Optional
from enum import Enum
import os


class TipoEvento(Enum):
    BODA = "boda"
    CONGRESO = "congreso"
    FAMILIAR = "familiar"

class EstiloCulinario(Enum):
    MOLECULAR = "molecular"
    CLASICO = "clasico"

class Temporada(Enum):
    PRIMAVERA = "primavera"
    VERANO = "verano"
    OTONO = "otoño"
    INVIERNO = "invierno"

class TradicionCultural(Enum):
    CATALANA = "catalana"
    MEXICANA = "mexicana"

class Sabor(Enum):
    DULCE = "dulce"
    SALADO = "salado"
    UMAMI = "umami"
    ACIDO = "ácido"
    AMARGO = "amargo"

class Restriccion(Enum):
    VEGANO = "vegano"
    SIN_LACTOSA = "sin_lactosa"

class TecnicaCoccion(Enum):
    CRUDO = "crudo"
    HORNEADO = "horneado" 
    ESFERIFICACION = "esferificacion"
    HERVIDO = "hervido"

class ModoAplicacion(Enum):
    TODOS_LOS_INGREDIENTES = "todos_los_ingredientes"
    POR_INGREDIENTE_UNA_OPCION = "por_ingrediente_una_opcion"
    UNA_SOLA_ACCION = "una_sola_accion"

@dataclass
class AccionReparacion:
    tipo: str  # "substituir", "quitar", "añadir"
    de: Optional[str] = None
    por: Optional[str] = None
    ingrediente: Optional[str] = None

@dataclass
class OpcionReparacion:
    ingrediente: str
    opciones: List[Dict[str, Any]]

@dataclass
class ReglaReparacion:
    estado_inicial: str
    estado_final: str
    modo_aplicacion: ModoAplicacion
    acciones_por_ingrediente: List[OpcionReparacion]

class TipoRegla(Enum):
    RESTRICCIONES = "reglas_restricciones"
    TEMPORADA = "reglas_temporada"
    SABOR = "reglas_sabor"
    TRADICION = "reglas_tradicion"
    COHERENCIA = "reglas_coherencia"


class CategoriaIngrediente(Enum):
    VEGETAL = "vegetal"
    FRUTA = "fruta"
    HONGO = "hongo"
    ANIMAL = "animal"
    CEREAL = "cereal"
    LEGUMINOSA = "leguminosa"
    LACTEO = "lacteo"
    CONDIMENTO = "condimento"


@dataclass
class Ingrediente:
    nombre: str
    temporada: List[Temporada]
    categoria: str
    sabor: Sabor

@dataclass
class Plato:
    nombre: str
    ingredientes: List[Ingrediente]
    tecnica_coccion: List[TecnicaCoccion]
    sabor_dominante: Sabor
    ingrediente_sabor: Ingrediente  # El ingrediente específico que proporciona el sabor dominante


@dataclass
class Menu:
    entrante: Plato
    principal: Plato
    postre: Plato

@dataclass
class Caso:
    id: str
    restricciones: List[str]
    temporada: Temporada
    tipo_evento: TipoEvento
    menu: Menu
    estilo: EstiloCulinario
    tradicion: TradicionCultural
    exito: bool = True
    fallos_detectados: List[str] = field(default_factory=list)
    reparaciones_aplicadas: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
