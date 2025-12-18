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
    GOURMET = "gourmet"
    COMFORT_FOOD = "comfort_food"
    PICANTE = "picante"
    FUSION = "fusion"
    SALUDABLE = "saludable"

class Temporada(Enum):
    PRIMAVERA = "primavera"
    VERANO = "verano"
    OTONO = "otoño"
    INVIERNO = "invierno"

class TradicionCultural(Enum):
    CATALANA = "catalana"
    MEXICANA = "mexicana"
    ITALIANA = "italiana"
    FRANCESA = "francesa"
    CHINA = "china"
    MEDITERRANEA = "mediterranea"

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
    ASADO = "asado"
    SALTEADO = "salteado"
    FRITO = "frito"
    GUISADO = "guisado"
    AL_VAPOR = "al_vapor"

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
    LEGUMBRE = "legumbre"
    LACTEO = "lacteo"
    CONDIMENTO = "condimento"
    FRUTO_SECO = "fruto_seco"


@dataclass
class Ingrediente:
    """Representa un ingrediente con sus propiedades"""
    nombre: str
    temporada: List[str]  # Lista de temporadas como strings
    categoria: str
    sabor: str
    tradicion: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para JSON"""
        return {
            'nombre': self.nombre,
            'temporada': self.temporada,
            'categoria': self.categoria,
            'sabor': self.sabor,
            'tradicion': self.tradicion
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Ingrediente':
        """Crea Ingrediente desde diccionario JSON"""
        return cls(
            nombre=data['nombre'],
            temporada=data.get('temporada', []),
            categoria=data.get('categoria', 'vegetal'),
            sabor=data.get('sabor', 'salado'),
            tradicion=data.get('tradicion', ['general'])
        )


@dataclass
class Plato:
    """Representa un plato con sus ingredientes y técnicas"""
    nombre: str
    ingredientes: List[str]  # Lista de nombres de ingredientes
    tecnica_coccion: List[str]
    sabor_dominante: str
    ingrediente_sabor: str  # Nombre del ingrediente que da el sabor
    tradicion: str = 'general'
    temporada: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para JSON"""
        return {
            'nombre': self.nombre,
            'ingredientes': self.ingredientes,
            'tecnica_coccion': self.tecnica_coccion,
            'sabor_dominante': self.sabor_dominante,
            'ingrediente_sabor': self.ingrediente_sabor,
            'tradicion': self.tradicion,
            'temporada': self.temporada
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Plato':
        """Crea Plato desde diccionario JSON"""
        return cls(
            nombre=data['nombre'],
            ingredientes=data.get('ingredientes', []),
            tecnica_coccion=data.get('tecnica_coccion', []),
            sabor_dominante=data.get('sabor_dominante', 'salado'),
            ingrediente_sabor=data.get('ingrediente_sabor', ''),
            tradicion=data.get('tradicion', 'general'),
            temporada=data.get('temporada', [])
        )


@dataclass
class Menu:
    """
    Representa un menú completo con entrante, principal y postre.
    Usa nombres de platos (strings) para ser consistente con el JSON.
    """
    entrante: str
    principal: str
    postre: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convierte el menú a diccionario"""
        return {
            'entrante': self.entrante,
            'principal': self.principal,
            'postre': self.postre
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Menu':
        """Crea un Menu desde un diccionario"""
        return cls(
            entrante=data.get('entrante', ''),
            principal=data.get('principal', ''),
            postre=data.get('postre', '')
        )


@dataclass
class Caso:
    """
    Representa un caso completo en la base de conocimiento.
    Todos los campos son estrictos y tipados correctamente.
    """
    id: str
    restricciones: List[str]
    temporada: str
    tipo_evento: str
    menu: Menu
    estilo: str
    tradicion: str
    exito: bool = True
    fallos_detectados: List[str] = field(default_factory=list)
    reparaciones_aplicadas: List[Any] = field(default_factory=list)
    timestamp: Optional[str] = None
    feedback: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el caso a diccionario para JSON"""
        return {
            'id': self.id,
            'restricciones': self.restricciones,
            'temporada': self.temporada,
            'tipo_evento': self.tipo_evento,
            'menu': self.menu.to_dict(),
            'estilo': self.estilo,
            'tradicion': self.tradicion,
            'exito': self.exito,
            'fallos_detectados': self.fallos_detectados,
            'reparaciones_aplicadas': self.reparaciones_aplicadas,
            'timestamp': self.timestamp,
            'feedback': self.feedback
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Caso':
        """Crea un Caso desde un diccionario JSON"""
        menu_data = data.get('menu', {})
        menu = Menu.from_dict(menu_data) if isinstance(menu_data, dict) else Menu('', '', '')
        
        return cls(
            id=data.get('id', ''),
            restricciones=data.get('restricciones', []),
            temporada=data.get('temporada', ''),
            tipo_evento=data.get('tipo_evento', ''),
            menu=menu,
            estilo=data.get('estilo', ''),
            tradicion=data.get('tradicion', ''),
            exito=data.get('exito', True),
            fallos_detectados=data.get('fallos_detectados', []),
            reparaciones_aplicadas=data.get('reparaciones_aplicadas', []),
            timestamp=data.get('timestamp'),
            feedback=data.get('feedback')
        )
