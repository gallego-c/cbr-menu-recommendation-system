from copy import deepcopy
from typing import Optional
from dominio import ConocimientoDominio
from base_casos import BaseCasos
from models import Plato


# Funcion plato
def substituir_plato(plato: Plato, preferencia_actual: str, preferencia_nueva: str, base_casos: BaseCasos = None) -> Optional[Plato]:
    """Buscar en la base de casos un plato similar que cumpla la nueva preferencia/restricción.

    - plato: objeto Plato (servirá como referencia de lo que hay que reemplazar)
    - preferencia_actual: etiqueta actual (p.ej. 'carne', 'vegetariano')
    - preferencia_nueva: etiqueta objetivo que debe cumplirse (p.ej. 'vegetariano', 'sin_gluten')
    - base_casos: si no se proporciona se carga la base por defecto

    Devuelve un objeto Plato (copia) que cumpla preferencia_nueva y las restricciones existentes del plato,
    o None si no encuentra ninguno.
    """
    conocimiento = ConocimientoDominio()
    if base_casos is None:
        base_casos = BaseCasos()

    ingredientes_orig = set(plato.ingredientes or [])
    mejores_candidatos = []

    for caso in base_casos.obtener_todos():
        # examinar tres platos del caso base
        for candidato in (caso.menu.entrante, caso.menu.principal, caso.menu.postre):
            # comprobar que el candidato cumple la nueva preferencia/restricción
            cumple = True
            
            # si la preferencia_nueva es una restricción alimentaria (ej. vegetariano), verificar ingredientes
            if preferencia_nueva in ['vegetariano', 'vegano']:
                for ing in candidato.ingredientes:
                    if not conocimiento.verificar_restriccion(ing, preferencia_nueva):
                        cumple = False
                        break
            
            # si es una restricción de temporada, verificar que el plato sea de esa temporada
            elif preferencia_nueva in ['primavera', 'verano', 'otoño', 'invierno']:
                if preferencia_nueva not in candidato.temporada and 'todas' not in candidato.temporada and 'todo' not in candidato.temporada:
                    cumple = False
            
            if not cumple:
                continue

            # además respetar las restricciones que ya tenía el plato original (si las hay)
            for rest in getattr(plato, 'restricciones', []) or []:
                for ing in candidato.ingredientes:
                    if not conocimiento.verificar_restriccion(ing, rest):
                        cumple = False
                        break
                if not cumple:
                    break
            if not cumple:
                continue

            # evitar el mismo plato que ya tenemos
            if candidato.nombre == plato.nombre:
                continue

            mejores_candidatos.append(candidato)

    # si encontramos candidatos, devolver el mejor
    if mejores_candidatos:
        # preferir candidatos que compartan categoría de ingrediente con el original
        for candidato in mejores_candidatos:
            if ingredientes_orig & set(candidato.ingredientes):
                return deepcopy(candidato)
        
        # si no hay overlap de ingredientes, devolver el primer candidato válido
        return deepcopy(mejores_candidatos[0])

    return None

