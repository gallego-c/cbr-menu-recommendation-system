# Debo definir los tipos o puedo poner desconocidos?

import json
from dataclasses import dataclass, field, asdict
from typing import List, Any
from enum import Enum


class TipoEvento(Enum):
    BODA = "boda"
    CONGRESO = "congreso"
    BANQUETE = "banquete"
    FAMILIAR = "familiar"


class EstiloCulinario(Enum):
    MOLECULAR = "molecular"
    AUTOR = "autor"
    CLASICO = "clasico"
    NORDICO = "nordico"
    MEDITERRANEO = "mediterraneo"


class TradicionCultural(Enum):
    GRIEGA = "griega"
    ITALIANA = "italiana"
    CATALANA = "catalana"
    VASCA = "vasca"
    GALLEGA = "gallega"
    MARROQUI = "marroqui"
    TURCA = "turca"
    LIBANESA = "libanesa"
    SOMALI = "somali"
    ETIOPE = "etiope"
    RUSA = "rusa"


@dataclass
class Plato:
    nombre: str
    ingredientes: List[str]
    tecnica_coccion: List[str]
    temporada: List[str]
    textura: str
    sabor_dominante: str
    ingrediente_sabor: str  # El ingrediente específico que proporciona el sabor dominante
    ingredientes_temporada: List[str]  # Los ingredientes que determinan la temporada del plato
    restricciones: List[str] = field(default_factory=list)


@dataclass
class Menu:
    entrante: Plato
    principal: Plato
    postre: Plato
    estilo: EstiloCulinario
    tradicion: TradicionCultural


@dataclass
class Caso:
    id: str
    tipo_evento: TipoEvento
    num_comensales: int
    presupuesto: float
    restricciones: List[str]
    preferencias: List[str]
    temporada: str
    menu: Menu
    exito: float = 1.0
    fallos_detectados: List[str] = field(default_factory=list)
    reparaciones_aplicadas: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
