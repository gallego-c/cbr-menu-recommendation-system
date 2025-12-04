from copy import deepcopy
from typing import Tuple, Optional, List
from dominio import ConocimientoDominio
from models import Plato

conocimiento = ConocimientoDominio()


def modificar_plato(plato: Plato, preferencias: Tuple[str, str]) -> Tuple[Optional[Plato], List[str]]:
    """Modifica el `plato` para pasar de `preferencia_actual` a `preferencia_nueva`.

    - preferencias: tupla (preferencia_actual, preferencia_nueva)
    Retorna (Plato_modificado o None, lista_de_mensajes)
    """
    preferencia_actual, preferencia_nueva = preferencias
    mensajes: List[str] = []
    nuevo = deepcopy(plato)

    # Detectar el tipo de problema y aplicar reglas específicas organizadas por categoría
    tipo_problema = _detectar_tipo_problema(preferencia_actual, preferencia_nueva)
    
    if tipo_problema:
        reglas_aplicables = conocimiento.obtener_reglas_por_problema(tipo_problema)
        
        # Buscar y aplicar reglas relevantes
        for categoria, lista_reglas in reglas_aplicables.items():
            for origen, destino, acciones in lista_reglas:
                if _regla_aplicable(origen, destino, preferencia_actual, preferencia_nueva):
                    exito = _aplicar_acciones_regla(nuevo, acciones, mensajes)
                    if exito:
                        mensajes.append(f"Aplicada regla {tipo_problema}:{categoria} - {origen}→{destino}")
                        return nuevo, mensajes

    # Fallback: intentar modificaciones específicas por tipo de problema usando métodos originales
    if _aplicar_modificacion_restriccion(nuevo, preferencia_actual, preferencia_nueva, mensajes):
        return nuevo, mensajes
    
    if _aplicar_modificacion_temporada(nuevo, preferencia_actual, preferencia_nueva, mensajes):
        return nuevo, mensajes
        
    if _aplicar_modificacion_textura(nuevo, preferencia_actual, preferencia_nueva, mensajes):
        return nuevo, mensajes

    mensajes.append(f"No se pudo modificar de '{preferencia_actual}' a '{preferencia_nueva}'")
    return None, mensajes


def _detectar_tipo_problema(actual: str, nueva: str) -> Optional[str]:
    """Detecta el tipo de problema basado en las preferencias."""
    if nueva in ['vegetariano', 'vegano', 'sin_gluten', 'halal']:
        return 'restricciones'
    elif nueva in ['primavera', 'verano', 'otoño', 'invierno']:
        return 'temporada'
    elif nueva in ['crujiente', 'cremoso', 'firme', 'suave', 'jugoso']:
        return 'textura'
    elif nueva in ['dulce', 'salado', 'acido', 'amargo', 'umami', 'neutro']:
        return 'sabor'
    elif 'coherencia' in nueva.lower() or 'estilo' in nueva.lower():
        return 'coherencia'
    return None


def _regla_aplicable(origen: str, destino: str, actual: str, nueva: str) -> bool:
    """Verifica si una regla es aplicable a la situación actual."""
    return (origen == "any" or origen == actual) and (destino == nueva or destino.endswith(nueva))


def _aplicar_acciones_regla(plato: Plato, acciones: dict, mensajes: List[str]) -> bool:
    """Aplica las acciones de una regla al plato y retorna True si fue exitoso."""
    cambios = False
    
    # Aplicar eliminaciones
    if 'eliminar' in acciones:
        for ing in acciones['eliminar']:
            if ing in plato.ingredientes:
                eliminar_ingrediente(plato, ing)
                mensajes.append(f"ELIMINAR-INGREDIENTE: {ing}")
                cambios = True

    # Aplicar adiciones
    if 'añadir' in acciones:
        for ing in acciones['añadir']:
            if ing not in plato.ingredientes:
                agregar_ingrediente(plato, ing)
                mensajes.append(f"AÑADIR-INGREDIENTE: {ing}")
                cambios = True

    # Aplicar reemplazos
    if 'reemplazar' in acciones:
        for rep in acciones['reemplazar']:
            de = rep.get('de')
            por = rep.get('por')
            for ing in list(plato.ingredientes):
                if ing == de:
                    substituir_ingrediente(plato, ing, por)
                    mensajes.append(f"REEMPLAZAR-INGREDIENTE: {ing} → {por}")
                    cambios = True
                else:
                    cat_ing = conocimiento.obtener_categoria_ingrediente(ing)
                    if cat_ing and cat_ing == de:
                        substituir_ingrediente(plato, ing, por)
                        mensajes.append(f"REEMPLAZAR-INGREDIENTE: {ing} (cat {de}) → {por}")
                        cambios = True

    # Aplicar cambios de técnica
    if 'tecnica' in acciones:
        tecnica_obj = acciones['tecnica']
        antiguo = plato.tecnica_coccion.copy() if isinstance(plato.tecnica_coccion, list) else [plato.tecnica_coccion]
        if isinstance(tecnica_obj, str):
            plato.tecnica_coccion = [tecnica_obj]
        else:
            plato.tecnica_coccion = tecnica_obj
        mensajes.append(f"CAMBIAR-TECNICA: {antiguo} → {plato.tecnica_coccion}")
        cambios = True

    return cambios


def _aplicar_modificacion_restriccion(plato: Plato, actual: str, nueva: str, mensajes: List[str]) -> bool:
    """Método fallback para restricciones usando lógica original."""
    if nueva in conocimiento.INCOMPATIBILIDADES:
        conflictivos = conocimiento.INCOMPATIBILIDADES[nueva]
        cambios = False
        for i, ing in enumerate(list(plato.ingredientes)):
            if ing in conflictivos:
                sustituto = conocimiento.obtener_sustituto(ing, nueva)
                if not sustituto:
                    sustituto = conocimiento.obtener_sustituto_por_jerarquia(ing, [nueva])
                if sustituto:
                    plato.ingredientes[i] = sustituto
                    mensajes.append(f"REEMPLAZAR-INGREDIENTE: {ing} → {sustituto}")
                    cambios = True
                else:
                    plato.ingredientes[i] = None
                    mensajes.append(f"ELIMINAR-INGREDIENTE: {ing}")
                    cambios = True

        plato.ingredientes = [x for x in plato.ingredientes if x]
        if cambios:
            if nueva not in plato.restricciones:
                plato.restricciones.append(nueva)
        return cambios
    return False


def _aplicar_modificacion_temporada(plato: Plato, actual: str, nueva: str, mensajes: List[str]) -> bool:
    """Método fallback para temporada."""
    # Implementar lógica específica de temporada si es necesario
    return False


def _aplicar_modificacion_textura(plato: Plato, actual: str, nueva: str, mensajes: List[str]) -> bool:
    """Método fallback para textura usando REGLAS_CAMBIO_TEXTURA."""
    regla = conocimiento.obtener_regla_textura(actual, nueva)
    if regla:
        if 'añadir' in regla:
            for ing in regla['añadir']:
                if ing not in plato.ingredientes:
                    agregar_ingrediente(plato, ing)
                    mensajes.append(f"AÑADIR-INGREDIENTE: {ing}")
        
        if 'tecnica' in regla:
            plato.tecnica_coccion = [regla['tecnica']]
            mensajes.append(f"CAMBIAR-TECNICA: → {regla['tecnica']}")
        
        return True
    return False


# Funciones auxiliares ingredientes
def agregar_ingrediente(plato: Plato, ingrediente: str) -> None:
    if ingrediente not in plato.ingredientes:
        plato.ingredientes.append(ingrediente)


def substituir_ingrediente(plato: Plato, ingrediente_actual: str, ingrediente_nuevo: str) -> None:
    plato.ingredientes = [ingrediente_nuevo if x == ingrediente_actual else x for x in plato.ingredientes]


def eliminar_ingrediente(plato: Plato, ingrediente: str) -> None:
    plato.ingredientes = [x for x in plato.ingredientes if x != ingrediente]


# Funciones auxiliares tecnica
def modificar_tecnica(plato: Plato, tecnica_actual: str, tecnica_nueva: str) -> None:
    if tecnica_actual in plato.tecnica_coccion:
        plato.tecnica_coccion = [tecnica_nueva if x == tecnica_actual else x for x in plato.tecnica_coccion]


def eliminar_tecnica(plato: Plato, tecnica: str) -> None:
    if tecnica in plato.tecnica_coccion:
        plato.tecnica_coccion = [x for x in plato.tecnica_coccion if x != tecnica]


def agregar_tecnica(plato: Plato, tecnica: str) -> None:
    if tecnica not in plato.tecnica_coccion:
        plato.tecnica_coccion.append(tecnica)