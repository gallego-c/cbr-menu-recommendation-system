from typing import List, Tuple
from copy import deepcopy
from dominio import ConocimientoDominio
from base_casos import BaseCasos
from models import Menu, Plato
from .substituir import substituir_plato
from .modificar import modificar_plato


def reparador_global(menu: Menu, fallos: List[str], caso, base_casos: BaseCasos = None, max_intentos_substituir: int = 5, max_intentos_modificar: int = 3) -> Tuple[Menu, List[str]]:
    """Orquestador global de reparaciones.

    Por cada fallo detectado en `fallos` intentará:
      1) FASE DE SUSTITUCIÓN: sustituir platos por otros de la base hasta max_intentos_substituir
      2) FASE DE MODIFICACIÓN: modificar platos que no pudieron ser sustituidos hasta max_intentos_modificar

    Devuelve (menu_modificado, lista_de_mensajes_de_reparacion)
    """
    conocimiento = ConocimientoDominio()
    if base_casos is None:
        base_casos = BaseCasos()

    menu_rep = deepcopy(menu)
    reparaciones = []

    # agrupar fallos por plato (entrante, principal, postre)
    fallos_por_plato = {}
    for fallo in fallos:
        key = None
        if 'entrante' in fallo.lower():
            key = 'entrante'
        elif 'principal' in fallo.lower():
            key = 'principal'
        elif 'postre' in fallo.lower():
            key = 'postre'
        else:
            # intentar identificar el plato por su nombre en el fallo
            # formato típico: "TIPO-ERROR: NombrePlato no es..."
            if ': ' in fallo:
                parte_despues_dos_puntos = fallo.split(': ')[1]
                # extraer el nombre del plato (primera parte antes de "no es" o "en")
                if ' no es' in parte_despues_dos_puntos:
                    nombre_plato = parte_despues_dos_puntos.split(' no es')[0].strip()
                elif ' en ' in parte_despues_dos_puntos:
                    nombre_plato = parte_despues_dos_puntos.split(' en ')[0].strip()
                else:
                    nombre_plato = None
                
                if nombre_plato:
                    # buscar a cuál de los tres platos del menú corresponde este nombre
                    if nombre_plato == menu.entrante.nombre:
                        key = 'entrante'
                    elif nombre_plato == menu.principal.nombre:
                        key = 'principal'
                    elif nombre_plato == menu.postre.nombre:
                        key = 'postre'
        
        fallos_por_plato.setdefault(key or 'global', []).append(fallo)

    print(f"  Fallos agrupados: {dict(fallos_por_plato)}")

    # procesar fallos por cada plato detectado
    for plato_key, lista_fallos in fallos_por_plato.items():
        if plato_key == 'global':
            print(f"  ⚠ Fallos no clasificados (global): {lista_fallos}")
            continue  # saltar fallos globales por ahora para evitar confusión
            
        print(f"\n  === Procesando {plato_key.upper()} ===")
        
        # seleccionar el objeto Plato correspondiente
        if plato_key == 'entrante':
            plato_obj = menu_rep.entrante
        elif plato_key == 'principal':
            plato_obj = menu_rep.principal
        elif plato_key == 'postre':
            plato_obj = menu_rep.postre
        else:
            continue
            
        print(f"  Plato actual: {plato_obj.nombre}")
        print(f"  Fallos a resolver: {lista_fallos}")

        # FASE 1: INTENTOS DE SUSTITUCIÓN
        intentos_substitucion = 0
        print(f"  FASE 1: Intentando sustituciones para {plato_key}")
        
        while intentos_substitucion < max_intentos_substituir and lista_fallos:
            intentos_substitucion += 1
            print(f"    [Intento {intentos_substitucion}] Analizando todos los fallos del plato: {lista_fallos}")
            
            # extraer todas las preferencias/restricciones de todos los fallos del plato
            preferencias_requeridas = []
            for fallo in lista_fallos:
                if 'restricción' in fallo and 'vegetariano' in fallo:
                    if 'vegetariano' not in preferencias_requeridas:
                        preferencias_requeridas.append('vegetariano')
                elif 'restricción' in fallo and 'vegano' in fallo:
                    if 'vegano' not in preferencias_requeridas:
                        preferencias_requeridas.append('vegano')
                elif 'temporada' in fallo.lower():
                    if hasattr(caso, 'temporada') and caso.temporada not in preferencias_requeridas:
                        preferencias_requeridas.append(caso.temporada)
            
            print(f"      Preferencias requeridas: {preferencias_requeridas}")
            
            # buscar un candidato que cumpla TODAS las preferencias/restricciones
            mejor_candidato = None
            fallos_resueltos = []
            
            if preferencias_requeridas:
                # buscar en la base de casos platos DEL MISMO TIPO que cumplan todas las restricciones
                for caso_base in base_casos.obtener_todos():
                    # solo considerar candidatos del mismo tipo de plato
                    if plato_key == 'entrante':
                        candidatos_del_tipo = [caso_base.menu.entrante]
                    elif plato_key == 'principal':
                        candidatos_del_tipo = [caso_base.menu.principal]
                    elif plato_key == 'postre':
                        candidatos_del_tipo = [caso_base.menu.postre]
                    else:
                        continue  # saltar si no se puede identificar el tipo
                    
                    for candidato_plato in candidatos_del_tipo:
                        if candidato_plato.nombre == plato_obj.nombre:
                            continue  # evitar el mismo plato
                        
                        # verificar si este candidato cumple todas las preferencias
                        candidato_valido = True
                        candidato_fallos_resueltos = []
                        
                        for pref in preferencias_requeridas:
                            if pref in ['vegetariano', 'vegano']:
                                # verificar restricciones alimentarias
                                cumple_restriccion = True
                                for ing in candidato_plato.ingredientes:
                                    if not conocimiento.verificar_restriccion(ing, pref):
                                        cumple_restriccion = False
                                        break
                                if cumple_restriccion:
                                    # marcar todos los fallos de restricción de este tipo como resueltos
                                    for fallo in lista_fallos:
                                        if 'restricción' in fallo and pref in fallo:
                                            candidato_fallos_resueltos.append(fallo)
                                else:
                                    candidato_valido = False
                                    break
                            elif pref in ['primavera', 'verano', 'otoño', 'invierno']:
                                # verificar temporada
                                if pref in candidato_plato.temporada or 'todas' in candidato_plato.temporada or 'todo' in candidato_plato.temporada:
                                    # marcar todos los fallos de temporada como resueltos
                                    for fallo in lista_fallos:
                                        if 'temporada' in fallo.lower() and candidato_plato.nombre in fallo:
                                            candidato_fallos_resueltos.append(fallo)
                                else:
                                    candidato_valido = False
                                    break
                        
                        # si este candidato es válido y resuelve más fallos que el mejor anterior
                        if candidato_valido and len(candidato_fallos_resueltos) > len(fallos_resueltos):
                            mejor_candidato = candidato_plato
                            fallos_resueltos = candidato_fallos_resueltos
                            print(f"        Candidato prometedor: {candidato_plato.nombre} (resuelve {len(fallos_resueltos)} fallos)")
            
            # aplicar la mejor sustitución encontrada
            if mejor_candidato and fallos_resueltos:
                plato_anterior = plato_obj.nombre
                if plato_key == 'entrante':
                    menu_rep.entrante = mejor_candidato
                    plato_obj = mejor_candidato
                elif plato_key == 'principal':
                    menu_rep.principal = mejor_candidato  
                    plato_obj = mejor_candidato
                elif plato_key == 'postre':
                    menu_rep.postre = mejor_candidato
                    plato_obj = mejor_candidato
                
                reparaciones.append(f"SUSTITUIR-PLATO: {plato_key} {plato_anterior} → {mejor_candidato.nombre} (resuelve {len(fallos_resueltos)} fallos)")
                
                # remover todos los fallos resueltos
                for fallo_resuelto in fallos_resueltos:
                    if fallo_resuelto in lista_fallos:
                        lista_fallos.remove(fallo_resuelto)
                
                print(f"      ✓ Sustitución exitosa: {mejor_candidato.nombre}")
                print(f"      ✓ Fallos resueltos: {len(fallos_resueltos)}")
                print(f"      ✓ Fallos restantes: {len(lista_fallos)}")
                
                if not lista_fallos:
                    print(f"      ✓ Todos los fallos del plato resueltos!")
                    break
            else:
                print(f"      ✗ No se encontró sustituto que resuelva los fallos restantes")
                break

        # FASE 2: INTENTOS DE MODIFICACIÓN (para fallos que no se pudieron resolver con sustitución)
        if lista_fallos:
            intentos_modificacion = 0
            print(f"  FASE 2: Intentando modificaciones para {plato_key} (fallos restantes: {len(lista_fallos)})")
            
            while intentos_modificacion < max_intentos_modificar and lista_fallos:
                intentos_modificacion += 1
                modificaciones_realizadas = False
                
                for fallo in list(lista_fallos):
                    print(f"    [Modificación {intentos_modificacion}] Procesando: {fallo}")
                    
                    if 'RESTRICCION-VIOLADA' in fallo:
                        partes = fallo.split(': ')
                        if len(partes) > 2 and "'" in partes[2]:
                            restr = partes[2].split("'")[1]
                            print(f"      Intentando modificación para restricción: {restr}")
                            mod, msgs = modificar_plato(plato_obj, ('', restr))
                            if mod:
                                plato_anterior = plato_obj.nombre
                                # aplicar modificación
                                if plato_key == 'entrante':
                                    menu_rep.entrante = mod
                                    plato_obj = mod
                                elif plato_key == 'principal':
                                    menu_rep.principal = mod
                                    plato_obj = mod
                                elif plato_key == 'postre':
                                    menu_rep.postre = mod
                                    plato_obj = mod
                                
                                # añadir mensajes de modificación
                                for msg in msgs:
                                    reparaciones.append(f"MODIFICAR-PLATO: {plato_key} {msg}")
                                modificaciones_realizadas = True
                                lista_fallos.remove(fallo)
                                print(f"      ✓ Modificación exitosa")
                                break  # procesar una modificación a la vez
                            else:
                                print(f"      ✗ Modificación falló")
                
                if not modificaciones_realizadas:
                    print(f"    No se pudieron realizar más modificaciones para {plato_key}")
                    break

        # si tras los intentos siguen fallos, añadir aviso
        if lista_fallos:
            reparaciones.append(f"AVISO: quedan {len(lista_fallos)} fallos en {plato_key} — revisar base de conocimiento")

    return menu_rep, reparaciones