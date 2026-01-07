"""
Sistema CBR Completo para Generación de Menús
============================================

Sistema Case-Based Reasoning que integra todos los módulos desarrollados:
- Recuperador: Encuentra casos similares
- Validador: Verifica restricciones y criterios
- Reparador: Arregla problemas encontrados
- Actualizador: Mantiene la base de conocimiento actualizada
"""

import json
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

# Importar módulos del sistema CBR
from recuperador import ModuloRecuperacion
from validador import ValidadorCompleto
from reparador import Reparador
from actualizador import ActualizadorConocimiento
from conocimiento import Menu, Caso, cargador, Plato, Ingrediente


@dataclass
class PreferenciasUsuario:
    """Representa las preferencias del usuario para generar un menú."""
    tipo_evento: str
    temporada: str
    restricciones: List[str] = field(default_factory=list)
    estilo: str = "clasico"
    tradicion: str = "catalana"
    presupuesto: Optional[float] = None
    num_comensales: Optional[int] = None
    preferencias_adicionales: List[str] = field(default_factory=list)


@dataclass
class ResultadoCBR:
    """Resultado del procesamiento CBR."""
    exito: bool
    menu: Optional[Dict[str, str]] = None
    similitud_caso_base: float = 0.0
    caso_base_id: Optional[str] = None
    reparaciones_aplicadas: List[str] = field(default_factory=list)
    fallos_encontrados: List[str] = field(default_factory=list)
    intentos_reparacion: int = 0
    mensaje: str = ""
    nuevo_caso_id: Optional[str] = None


@dataclass
class ConfiguracionCBR:
    """Configuración del sistema CBR."""
    max_intentos_reparacion: int = 5
    umbral_similitud_minimo: float = 0.3
    k_casos_recuperar: int = 3
    usar_explicaciones: bool = True
    crear_backup: bool = False
    validar_estricto: bool = True
    debug: bool = False  # Activar para ver mensajes de depuración


# Variable global para modo debug (usada por otros módulos)
DEBUG_MODE = False


def set_debug_mode(enabled: bool):
    """Activa o desactiva el modo debug globalmente."""
    global DEBUG_MODE
    DEBUG_MODE = enabled


def debug_print(*args, **kwargs):
    """Imprime solo si el modo debug está activado."""
    if DEBUG_MODE:
        print(*args, **kwargs)


class SistemaCBR:
    """
    Sistema CBR completo para generación de menús culinarios.
    
    Integra recuperación, validación, reparación y actualización para
    proporcionar menús personalizados basados en casos previos.
    """
    
    def __init__(self, config: ConfiguracionCBR = None):
        """
        Inicializa el sistema CBR con todos sus módulos.
        
        Args:
            config: Configuración del sistema CBR
        """
        self.config = config or ConfiguracionCBR()
        
        # Configurar modo debug global
        set_debug_mode(self.config.debug)
        
        # Inicializar módulos
        self._inicializar_modulos()
        
        # Estadísticas del sistema
        self.estadisticas = {
            'casos_procesados': 0,
            'casos_exitosos': 0,
            'casos_reparados': 0,
            'casos_fallidos': 0,
            'reparaciones_totales': 0
        }
    
    def _inicializar_modulos(self):
        """Inicializa todos los módulos del sistema CBR."""
        try:
            # Inicializar módulos (configuración se pasa en recuperar())
            self.recuperador = ModuloRecuperacion()
            self.validador = ValidadorCompleto()
            self.reparador = Reparador()
            self.actualizador = ActualizadorConocimiento()
            
        except Exception as e:
            raise Exception(f"Error inicializando módulos: {e}")
    
    def generar_menu(self, preferencias: PreferenciasUsuario) -> ResultadoCBR:
        """
        Genera un menú basado en las preferencias del usuario.
        
        Proceso completo CBR:
        1. Recuperación de casos similares
        2. Validación del mejor caso
        3. Reparación si es necesario
        4. Actualización de la base de conocimiento
        
        Args:
            preferencias: Preferencias del usuario
            
        Returns:
            ResultadoCBR con el menú generado o mensaje de fallo
        """
        print("\n" + "="*70)
        print("SISTEMA CBR DE GENERACIÓN DE MENÚS")
        print("="*70)
        print(f"Solicitud:")
        print(f"  Tipo de evento: {preferencias.tipo_evento}")
        print(f"  Temporada: {preferencias.temporada}")
        print(f"  Restricciones dietéticas: {preferencias.restricciones if preferencias.restricciones else 'ninguna'}")
        print(f"  Estilo culinario: {preferencias.estilo}")
        print(f"  Tradición: {preferencias.tradicion}")
        print("="*70)
        
        self.estadisticas['casos_procesados'] += 1
        
        try:
            # Paso 1: Recuperación
            resultados_recuperacion = self._fase_recuperacion(preferencias)
            if not resultados_recuperacion:
                return self._crear_resultado_fallo("No se encontraron casos similares suficientes")
            
            # Paso 2: Validar los 3 casos
            print("\n" + "="*70)
            print("FASE 2: VALIDACIÓN DE LOS MENÚS")
            print("="*70)
            
            casos_validados = []
            for i, resultado_rec in enumerate(resultados_recuperacion):
                resultado_rec_dict = {
                    'caso': resultado_rec.caso,
                    'similitud': resultado_rec.similitud,
                    'explicacion': resultado_rec.explicacion
                }
                
                # Validar caso
                validacion = self._fase_validacion(resultado_rec_dict, preferencias, 
                                                   mostrar_titulo=False)
                
                casos_validados.append({
                    'caso': resultado_rec_dict,
                    'validacion': validacion
                })
            
            # Paso 3: Reparar los 3 casos (todos, no solo los inválidos)
            print("\n" + "="*70)
            print("FASE 3: REPARACIÓN DE LOS MENÚS")
            print("="*70)
            
            casos_procesados = []
            for caso_val in casos_validados:
                if not caso_val['validacion']['valido']:
                    # Reparar caso inválido
                    resultado_reparacion = self._fase_reparacion(caso_val['caso'], preferencias, 
                                                                 caso_val['validacion'],
                                                                 mostrar_titulo=False)
                    
                    if resultado_reparacion['exito']:
                        menu_final = resultado_reparacion['menu']
                        reparaciones = resultado_reparacion['reparaciones_aplicadas']
                        intentos = resultado_reparacion['intentos_totales']
                        valido = True
                    else:
                        # Reparación falló o parcial - usar menú reparado pero marcarlo como no válido
                        menu_final = resultado_reparacion['menu']  # Usar menú reparado, no original
                        reparaciones = resultado_reparacion['reparaciones_aplicadas']  # Guardar las reparaciones hechas
                        intentos = resultado_reparacion['intentos_totales']
                        valido = False
                else:
                    # Caso válido sin necesidad de reparación
                    print(f"\nCaso {caso_val['caso']['caso']['id']}: No requiere reparacion (VALIDO)")
                    menu_final = caso_val['caso']['caso']['menu']
                    reparaciones = []
                    intentos = 0
                    valido = True
                
                # Guardar caso procesado con su resultado
                casos_procesados.append({
                    'caso': caso_val['caso'],
                    'menu_final': menu_final,
                    'valido': valido,
                    'reparaciones': reparaciones,
                    'intentos': intentos,
                    'validacion': caso_val['validacion']
                })
            
            # Paso 4: Seleccionar el mejor caso procesado que no esté duplicado
            print("\n" + "="*70)
            print("SELECCIÓN DEL MEJOR MENÚ")
            print("="*70)
            
            caso_seleccionado = None
            casos_duplicados = []
            posicion_caso = 0  # Para rastrear la posición del caso seleccionado
            
            for i, caso_proc in enumerate(casos_procesados):
                if caso_proc['valido']:
                    # Verificar si el caso ya está duplicado en la base (usar actualizador)
                    menu_dict = caso_proc['menu_final']
                    menu_obj = Menu(
                        entrante=menu_dict.get('entrante', ''),
                        principal=menu_dict.get('principal', ''),
                        postre=menu_dict.get('postre', '')
                    )
                    es_duplicado = self.actualizador.verificar_duplicado(
                        menu_obj,
                        preferencias.tipo_evento,
                        preferencias.temporada,
                        preferencias.restricciones,
                        preferencias.estilo,
                        preferencias.tradicion
                    )
                    
                    if es_duplicado:
                        casos_duplicados.append({
                            'id': caso_proc['caso']['caso']['id'],
                            'similitud': caso_proc['caso']['similitud'],
                            'menu': caso_proc['menu_final'],
                            'reparaciones': len(caso_proc['reparaciones']),
                            'caso_proc': caso_proc  # Guardar referencia completa
                        })
                        continue
                    
                    # Caso válido y no duplicado - seleccionarlo
                    caso_seleccionado = caso_proc
                    posicion_caso = i + 1  # Posición 1-indexed
                    
                    # Determinar el texto de posición
                    numeros_ordinales = {
                        1: "primer",
                        2: "segundo", 
                        3: "tercer"
                    }
                    texto_posicion = numeros_ordinales.get(posicion_caso, f"{posicion_caso}º")
                    
                    print(f"\nCaso seleccionado: {caso_proc['caso']['caso']['id']} ({texto_posicion} caso - VÁLIDO)")
                    print(f"  Similitud: {caso_proc['caso']['similitud']:.3f}")
                    print(f"  Reparaciones aplicadas: {len(caso_proc['reparaciones'])}")
                    break
            
            # Si todos los casos válidos están duplicados, seleccionar el mejor de todos modos
            if not caso_seleccionado and casos_duplicados:
                print(f"\n[!] Todos los casos válidos ya existen en la base de datos")
                print(f"   Seleccionando el de mayor similitud (no se agregará a la base)...\n")
                
                # Seleccionar el caso duplicado con mayor similitud (el primero de la lista)
                mejor_caso_dup = casos_duplicados[0]
                caso_seleccionado = mejor_caso_dup['caso_proc']
                
                print(f"Caso seleccionado: {mejor_caso_dup['id']}")
                print(f"  Similitud: {mejor_caso_dup['similitud']:.3f}")
                if mejor_caso_dup['reparaciones'] > 0:
                    print(f"  Reparaciones aplicadas: {mejor_caso_dup['reparaciones']}")
            
            # Si ninguno es válido, usar el de mayor similitud (el primero)
            if not caso_seleccionado:
                caso_seleccionado = casos_procesados[0]
                print(f"\nNingún caso pudo ser validado/reparado exitosamente.")
                print(f"Usando caso con mayor similitud: {caso_seleccionado['caso']['caso']['id']}")
            
            # Extraer datos del caso seleccionado
            menu_final = caso_seleccionado['menu_final']
            reparaciones = caso_seleccionado['reparaciones']
            intentos = caso_seleccionado['intentos']
            resultado_validacion = caso_seleccionado['validacion']
            caso_base = caso_seleccionado['caso']
            
            if reparaciones:
                self.estadisticas['casos_reparados'] += 1
                self.estadisticas['reparaciones_totales'] += len(reparaciones)
            
            # Paso 5: Actualización de la base de conocimiento
            print("\n" + "="*70)
            print("FASE 4: ACTUALIZACIÓN DE LA BASE DE CASOS")
            print("="*70)
            
            # Paso 4.1: Guardar platos nuevos en la base de datos
            if reparaciones:
                print("\n--- Guardando platos nuevos ---")
                platos_nuevos = [rep['plato_nuevo'] for rep in reparaciones 
                               if rep.get('plato_nuevo') and rep['plato_nuevo'] != rep.get('plato_original')]
                
                if platos_nuevos:
                    print(f"Guardando {len(platos_nuevos)} platos nuevos en la base de datos...")
                    self.actualizador.gestor_platos.agregar(platos_nuevos, reparaciones)
                    print(f"  [OK] Platos guardados correctamente")
                else:
                    print("  No hay platos nuevos que guardar")
            
            # Paso 4.2: Validar el menú seleccionado
            print("\n--- Validación del menú seleccionado ---")
            
            # Construir un diccionario con los platos modificados para la validación
            # CLAVE: usar el nombre del plato (que puede ser original si solo se modificaron ingredientes)
            platos_modificados = {}
            debug_print(f"  [DEBUG] Total de reparaciones: {len(reparaciones)}")
            for idx, rep in enumerate(reparaciones):
                debug_print(f"  [DEBUG] Reparacion {idx+1}: plato_nuevo={rep.get('plato_nuevo')}, tiene_obj={('plato_modificado_obj' in rep)}")
                if 'plato_modificado_obj' in rep and rep['plato_modificado_obj']:
                    # Usar el nombre del plato (original o nuevo, depende de la estrategia)
                    nombre_plato = rep['plato_nuevo']
                    platos_modificados[nombre_plato] = rep['plato_modificado_obj']
                    debug_print(f"  [DEBUG] Usando plato modificado para validación: {nombre_plato}")
                    debug_print(f"  [DEBUG]   Ingredientes: {rep['plato_modificado_obj'].ingredientes[:5]}...")
            
            debug_print(f"  [DEBUG] Total platos modificados para validación: {len(platos_modificados)}")
            validacion_final = self._fase_validacion_silenciosa(menu_final, preferencias, platos_modificados)
            
            if validacion_final['errores']:
                print(f"[!] El menú todavía tiene {len(validacion_final['errores'])} errores:")
                for error in validacion_final['errores']:
                    print(f"  • {error}")
                print("\n[!] El caso seleccionado no es completamente válido.")
                print("   No se agregará a la base de casos.")
                return self._crear_resultado_fallo(
                    f"No se pudo obtener un menú válido después de validar y reparar los {len(casos_procesados)} casos",
                    validacion_final
                )
            else:
                print("[OK] El menú seleccionado es completamente válido")
            
            # Paso 4.3: Verificar duplicado y actualizar base de casos
            # ACTUALIZACIÓN DESACTIVADA - No se guardan nuevos casos
            # print("\n--- Actualizando base de casos ---")
            # # Verificar duplicado usando actualizador
            # menu_obj = Menu(
            #     entrante=menu_final.get('entrante', ''),
            #     principal=menu_final.get('principal', ''),
            #     postre=menu_final.get('postre', '')
            # )
            # es_duplicado_final = self.actualizador.verificar_duplicado(
            #     menu_obj,
            #     preferencias.tipo_evento,
            #     preferencias.temporada,
            #     preferencias.restricciones,
            #     preferencias.estilo,
            #     preferencias.tradicion
            # )
            # if es_duplicado_final:
            #     nuevo_caso_id = None
            #     print("\n[!] El menú generado ya existe en la base de casos")
            #     print("   No se agregará como caso nuevo")
            # else:
            #     nuevo_caso_id = self._fase_actualizacion_interna(menu_final, preferencias, True, reparaciones)
            nuevo_caso_id = None  # No se guardan nuevos casos
            
            # Crear resultado exitoso
            resultado = ResultadoCBR(
                exito=True,
                menu=menu_final,
                similitud_caso_base=caso_base['similitud'],
                caso_base_id=caso_base['caso']['id'],
                reparaciones_aplicadas=reparaciones,
                fallos_encontrados=resultado_validacion.get('errores', []),
                intentos_reparacion=intentos,
                mensaje="Menú generado exitosamente",
                nuevo_caso_id=nuevo_caso_id
            )
            
            self.estadisticas['casos_exitosos'] += 1
            
            # Mostrar resultado final
            print("\n" + "="*70)
            print("RESULTADO FINAL")
            print("="*70)
            print(f"\nMENU GENERADO:")
            print(f"  Entrante:  {menu_final['entrante']}")
            print(f"  Principal: {menu_final['principal']}")
            print(f"  Postre:    {menu_final['postre']}")
            print(f"\nEstadisticas:")
            print(f"  Similitud con caso base: {caso_base['similitud']:.3f}")
            print(f"  Caso base: {caso_base['caso']['id']}")
            if reparaciones:
                print(f"  Reparaciones aplicadas: {len(reparaciones)}")
            if nuevo_caso_id:
                print(f"  Nuevo caso ID: {nuevo_caso_id}")
            print("="*70 + "\n")
            
            return resultado
            
        except Exception as e:
            return self._crear_resultado_fallo(f"Error del sistema: {str(e)}")
    
    def _fase_recuperacion(self, preferencias: PreferenciasUsuario) -> Optional[List]:
        """Ejecuta la fase de recuperación de casos similares."""
        print("\n" + "="*70)
        print("FASE 1: RECUPERACIÓN DE CASOS SIMILARES")
        print("="*70)
        
        # Convertir preferencias a formato de consulta
        consulta = {
            'tipo_evento': preferencias.tipo_evento,
            'temporada': preferencias.temporada,
            'restricciones': preferencias.restricciones,
            'estilo': preferencias.estilo,
            'tradicion': preferencias.tradicion
        }
        
        # Recuperar casos similares
        resultados = self.recuperador.recuperar(
            consulta,
            k=self.config.k_casos_recuperar,
            umbral_minimo=self.config.umbral_similitud_minimo,
            explicar=self.config.usar_explicaciones
        )
        
        if not resultados:
            print("No se encontraron casos similares")
            return None
        
        print(f"\nCasos recuperados: {len(resultados)}")
        for i, resultado in enumerate(resultados, 1):
            print(f"\n{i}. Caso: {resultado.caso['id']}")
            print(f"   Similitud: {resultado.similitud:.3f}")
            print(f"   Menu:")
            print(f"     Entrante:  {resultado.caso['menu']['entrante']}")
            print(f"     Principal: {resultado.caso['menu']['principal']}")
            print(f"     Postre:    {resultado.caso['menu']['postre']}")
        
        # Retornar todos los resultados para que se validen
        return resultados
    
    def _fase_validacion(self, caso_recuperado: Dict, preferencias: PreferenciasUsuario, mostrar_titulo: bool = True) -> Dict:
        """Ejecuta la fase de validación del caso recuperado."""
        if mostrar_titulo:
            print("\n" + "="*70)
            print("FASE 2: VALIDACIÓN DE LOS MENÚS")
            print("="*70)
        
        print(f"\nValidando caso: {caso_recuperado['caso']['id']}")
        
        menu = caso_recuperado['caso']['menu']
        errores = []
        
        # Validar que todos los platos estén presentes
        platos_requeridos = ['entrante', 'principal', 'postre']
        for tipo_plato in platos_requeridos:
            if tipo_plato not in menu or not menu[tipo_plato] or menu[tipo_plato].strip() == '':
                errores.append(f"Falta {tipo_plato}")
        
        # Si hay restricciones o criterios específicos, usar ValidadorCompleto
        if preferencias.restricciones or self.config.validar_estricto:
            from conocimiento.models import Menu, Plato, Ingrediente
            from conocimiento import cargador
            
            # Cargar información de platos desde conocimiento usando el cargador
            try:
                platos_db = cargador.cargar_json('platos.json')
                ingredientes_db = cargador.cargar_ingredientes()
                
                # Validar cada plato del menú con restricciones
                for tipo_plato, nombre_plato in menu.items():
                    if not nombre_plato or nombre_plato.strip() == '':
                        continue
                    
                    # Cargar plato desde JSON (como dict, no convertir a objetos)
                    plato_dict = next((p for p in platos_db if p['nombre'] == nombre_plato), None)
                    
                    if not plato_dict:
                        errores.append(f"{tipo_plato}: Plato '{nombre_plato}' no encontrado en base de datos")
                        continue
                    
                    # Crear objeto Plato directamente desde dict (sin convertir ingredientes a objetos)
                    plato = Plato.from_dict(plato_dict)
                    
                    # Validar con ValidadorCompleto
                    contexto = {
                        'restricciones': preferencias.restricciones,
                        'temporada': preferencias.temporada,
                        'tradicion': preferencias.tradicion
                    }
                    
                    resultados_validacion = self.validador.validar_plato_completo(plato, contexto)
                    
                    # Recopilar errores de validación
                    for criterio, resultado in resultados_validacion.items():
                        if not resultado.valido:
                            for error in resultado.errores:
                                errores.append(f"{tipo_plato} ({nombre_plato}): {error}")
            
            except Exception as e:
                errores.append(f"Error durante validación detallada: {str(e)}")
        
        # Determinar validez
        valido = len(errores) == 0
        
        if valido:
            print("\nValidacion: EXITOSA")
            print("El menu cumple con todas las restricciones")
        else:
            print("\nValidacion: FALLIDA")
            print("Errores detectados:")
            for error in errores:
                print(f"  - {error}")
        
        resultado = {
            'valido': valido,
            'errores': errores
        }
        
        return resultado
    
    def _extraer_ingrediente_de_error(self, error: str) -> Optional[str]:
        """
        Extrae el nombre del ingrediente mencionado en un mensaje de error.
        
        Args:
            error: Mensaje de error de validación
            
        Returns:
            Nombre del ingrediente o None si no se encuentra
        """
        import re
        
        # Patrones para extraer ingredientes de mensajes de error
        patrones = [
            r'Ingrediente prohibido para \w+: (\w+)',
            r'Ingrediente con categoría prohibida para \w+: (\w+)',
            r'Ingrediente fuera de temporada: (\w+)',
            r'Ingrediente (\w+) viola',
            r': (\w+) \(categoría:',
            r': (\w+) \(disponible en:',
        ]
        
        for patron in patrones:
            match = re.search(patron, error)
            if match:
                return match.group(1)
        
        return None
    
    def _fase_reparacion(self, caso_recuperado: Dict, preferencias: PreferenciasUsuario, 
                        validacion: Dict, mostrar_titulo: bool = True) -> Dict:
        """Ejecuta la fase de reparación del menú."""
        if mostrar_titulo:
            print("\n" + "="*70)
            print("FASE 3: REPARACIÓN DEL MENÚ")
            print("="*70)
        
        menu_original = caso_recuperado['caso']['menu']
        
        # Si el menú es válido, no hay nada que reparar
        if validacion['valido']:
            print("\nNo se requiere reparacion")
            return {
                'exito': True,
                'menu': menu_original,
                'reparaciones_aplicadas': [],
                'problemas_no_resueltos': [],
                'intentos_totales': 0
            }
        
        print(f"\nCaso {caso_recuperado['caso']['id']}: Iniciando reparacion...")
        print(f"Errores detectados: {len(validacion.get('errores', []))}")
        
        # Usar el reparador real
        from reparador import Reparador
        from conocimiento.models import Menu, Plato, Ingrediente, TecnicaCoccion, CategoriaIngrediente
        
        reparador = Reparador()
        
        # Convertir el menú de dict a objetos
        menu_reparado = dict(menu_original)
        reparaciones_aplicadas = []
        problemas_no_resueltos = []
        intentos = 0
        max_intentos = self.config.max_intentos_reparacion
        
        # Procesar cada error (usar validador para agrupar)
        errores_por_plato = ValidadorCompleto.agrupar_errores_por_plato(validacion.get('errores', []))
        
        for plato_nombre, errores_plato in errores_por_plato.items():
            intentos += 1
            if intentos > max_intentos:
                problemas_no_resueltos.extend(errores_plato)
                break
            
            print(f"\n  Reparando {plato_nombre}:")
            for error in errores_plato:
                print(f"    - {error}")
            
            # Determinar tipo de plato
            tipo_plato_busqueda = None
            if plato_nombre == menu_original.get('entrante', ''):
                tipo_plato_busqueda = 'entrante'
            elif plato_nombre == menu_original.get('principal', ''):
                tipo_plato_busqueda = 'principal'
            elif plato_nombre == menu_original.get('postre', ''):
                tipo_plato_busqueda = 'postre'
            
            # Preparar preferencias para el substitutor
            prefs_dict = {
                'restricciones': preferencias.restricciones,
                'temporada': preferencias.temporada,
                'tradicion': preferencias.tradicion,
                'estilo': preferencias.estilo
            }
            
            # Procesar TODOS los errores del plato, no solo el primero
            nombre_plato_actual = plato_nombre
            plato_obj_actual = None  # Mantener objeto Plato en memoria
            reparacion_exitosa = False
            errores_resueltos_acumulados = []
            modificaciones_acumuladas = []  # Guardar las modificaciones reales
            
            for idx, error_actual in enumerate(errores_plato):
                print(f"    [{idx+1}/{len(errores_plato)}] Procesando error: {error_actual}")
                
                # Verificar si este error ya fue resuelto por una reparación anterior
                # (cuando se sustituyen múltiples ingredientes a la vez)
                ingrediente_en_error = self._extraer_ingrediente_de_error(error_actual)
                if ingrediente_en_error and any(ingrediente_en_error in msg for msg in modificaciones_acumuladas):
                    print(f"      [OK] Ya reparado en sustitución anterior ({ingrediente_en_error})")
                    errores_resueltos_acumulados.append(error_actual)
                    continue
                
                # Extraer tipo de problema de este error específico
                tipo_problema = ValidadorCompleto.extraer_tipo_problema(error_actual)
                
                # Intentar reparar este error específico
                # Si ya tenemos un objeto Plato modificado, usarlo; si no, buscar por nombre
                if plato_obj_actual:
                    # Reparar el objeto Plato existente
                    resultado_reparacion = self.reparador.reparar_plato_objeto(
                        plato_obj_actual,
                        tipo_problema,
                        error_actual,
                        prefs_dict
                    )
                else:
                    # Primera reparación, buscar por nombre
                    resultado_reparacion = self.reparador.reparar_por_nombre(
                        nombre_plato_actual,
                        tipo_problema,
                        error_actual,
                        menu_original,  # Pasar el menú completo
                        prefs_dict      # Y las preferencias
                    )
                
                if resultado_reparacion['exito']:
                    plato_resultado = resultado_reparacion['plato_resultado']
                    estrategia = resultado_reparacion['estrategia']
                    
                    # Extraer nombre y objeto del plato (puede ser objeto Plato o string)
                    if isinstance(plato_resultado, str):
                        nombre_plato_nuevo = plato_resultado
                        # Si es string (substitución), cargar el plato como objeto para continuar
                        # con más modificaciones si hay más errores
                        from conocimiento import cargador
                        from conocimiento.models import Plato
                        platos_db = cargador.cargar_platos()
                        plato_info = platos_db.get(nombre_plato_nuevo) if isinstance(platos_db, dict) else \
                                     next((p for p in platos_db if p.get('nombre') == nombre_plato_nuevo), None)
                        if plato_info:
                            plato_obj_actual = Plato.from_dict(plato_info)
                        else:
                            plato_obj_actual = None
                    else:
                        # Es un objeto Plato, extraer el nombre y mantener el objeto
                        nombre_plato_nuevo = plato_resultado.nombre
                        plato_obj_actual = plato_resultado  # Guardar para siguiente iteración
                    
                    # Actualizar el nombre para el siguiente error
                    nombre_plato_actual = nombre_plato_nuevo
                    reparacion_exitosa = True
                    errores_resueltos_acumulados.append(error_actual)
                    
                    # Recolectar mensajes de modificación (substituciones, adiciones, etc.)
                    modificaciones_acumuladas.extend(resultado_reparacion['mensajes'])
                    
                    for mensaje in resultado_reparacion['mensajes']:
                        # No añadir [OK] adicional si el mensaje ya lo tiene
                        if mensaje.startswith('[OK]') or mensaje.startswith('[~]'):
                            print(f"      {mensaje}")
                        else:
                            print(f"      [OK] {mensaje}")
                else:
                    print(f"      [X] No se pudo reparar este error")
                    # Si no se pudo reparar, agregar a problemas no resueltos
                    problemas_no_resueltos.append(error_actual)
            
            # Si hubo al menos una reparación exitosa, actualizar el menú
            if reparacion_exitosa:
                # Si tenemos un objeto Plato modificado, guardarlo con las reparaciones
                plato_modificado_obj = None
                if plato_obj_actual:
                    # El plato fue modificado (objeto Plato), guardarlo
                    plato_modificado_obj = plato_obj_actual
                    debug_print(f"      [DEBUG] Plato modificado guardado: {nombre_plato_actual}")
                    debug_print(f"      [DEBUG]   - Ingredientes modificados: {len(plato_obj_actual.ingredientes)}")
                
                # Actualizar el plato en el menú (siempre con string, no objeto)
                if 'entrante' in plato_nombre.lower() or plato_nombre == menu_original.get('entrante', ''):
                    menu_reparado['entrante'] = nombre_plato_actual
                    tipo_plato = 'entrante'
                elif 'principal' in plato_nombre.lower() or plato_nombre == menu_original.get('principal', ''):
                    menu_reparado['principal'] = nombre_plato_actual
                    tipo_plato = 'principal'
                elif 'postre' in plato_nombre.lower() or plato_nombre == menu_original.get('postre', ''):
                    menu_reparado['postre'] = nombre_plato_actual
                    tipo_plato = 'postre'
                else:
                    tipo_plato = 'desconocido'
                
                reparaciones_aplicadas.append({
                    'tipo_plato': tipo_plato,
                    'plato_original': plato_nombre,
                    'plato_nuevo': nombre_plato_actual,
                    'accion': 'modificacion',
                    'modificaciones': modificaciones_acumuladas,  # Usar las modificaciones reales
                    'errores_resueltos': errores_resueltos_acumulados,
                    'plato_modificado_obj': plato_modificado_obj  # Guardar objeto Plato si fue modificado
                })
            else:
                    # No se pudo reparar ningún error
                print(f"    [X] No se pudo reparar el plato")
                problemas_no_resueltos.extend(errores_plato)
        
        # Resultado de la reparación (NO validar aquí, se hará después de seleccionar)
        exito = len(problemas_no_resueltos) == 0
        
        resultado = {
            'exito': exito,
            'menu': menu_reparado,
            'reparaciones_aplicadas': reparaciones_aplicadas,
            'problemas_no_resueltos': problemas_no_resueltos,
            'intentos_totales': intentos
        }
        
        # Mostrar resumen
        print(f"\nResultado reparacion:")
        if exito:
            print(f"  [OK] Reparacion exitosa")
            print(f"  Reparaciones aplicadas: {len(reparaciones_aplicadas)}")
        else:
            print(f"  [X] Reparacion parcial")
            print(f"  Reparaciones aplicadas: {len(reparaciones_aplicadas)}")
            print(f"  Problemas sin resolver: {len(problemas_no_resueltos)}")
        
        return resultado
    
    # NOTA: Todas las funciones auxiliares y de dominio han sido movidas a los módulos correspondientes:
    # - agrupar_errores_por_plato() -> validador.ValidadorCompleto.agrupar_errores_por_plato()
    # - extraer_tipo_problema() -> validador.ValidadorCompleto.extraer_tipo_problema()
    # - generar_nombre_plato_modificado() -> reparador.Reparador.generar_nombre_plato_modificado()
    # - buscar_plato_alternativo() -> reparador.substitutor_platos.buscar_alternativa_simple()
    # - buscar_info_ingrediente() -> cargador.cargar_ingredientes()
    # - intentar_modificacion_plato() -> reparador.Reparador.reparar_por_nombre()
    
    def _fase_validacion_silenciosa(self, menu: Dict, preferencias: PreferenciasUsuario, platos_modificados: Dict = None) -> Dict:
        """
        Valida un menú sin imprimir encabezados (para validación final post-reparación).
        Reutiliza la función _validar_plato_con_objetos del módulo validador.
        
        Args:
            menu: Menú a validar
            preferencias: Preferencias del usuario
            platos_modificados: Dict opcional con {nombre_plato: objeto_Plato} para platos modificados
        
        Returns:
            Dict con 'errores' (lista de strings) y 'valido' (bool)
        """
        if platos_modificados is None:
            platos_modificados = {}
        
        errores = []
        
        # Validar que todos los platos estén presentes
        platos_requeridos = ['entrante', 'principal', 'postre']
        for tipo_plato in platos_requeridos:
            if tipo_plato not in menu or not menu[tipo_plato] or menu[tipo_plato].strip() == '':
                errores.append(f"Falta {tipo_plato}")
        
        # Si hay restricciones o criterios específicos, usar ValidadorCompleto
        if preferencias.restricciones or self.config.validar_estricto:
            try:
                # Leer directamente del archivo JSON para obtener platos recién guardados
                from conocimiento import cargador
                platos_db = cargador.cargar_platos()
                
                # Validar cada plato del menú
                for tipo_plato, nombre_plato in menu.items():
                    if not nombre_plato or nombre_plato.strip() == '':
                        continue
                    
                    # Si el plato fue modificado, usar el objeto modificado
                    if nombre_plato in platos_modificados:
                        debug_print(f"  [DEBUG] Validando plato modificado: {nombre_plato}")
                        plato_obj = platos_modificados[nombre_plato]
                    else:
                        # Cargar plato desde dict (cargador devuelve Dict[str, Dict])
                        plato_dict = platos_db.get(nombre_plato)
                        
                        if not plato_dict:
                            errores.append(f"{tipo_plato} ({nombre_plato}): Plato no encontrado en base de datos")
                            continue
                        
                        # Convertir a objeto Plato
                        from conocimiento.models import Plato
                        plato_obj = Plato.from_dict(plato_dict)
                    
                    # Validar usando objeto Plato (plato_obj)
                    # Crear contexto de validación
                    contexto = {
                        'restricciones': preferencias.restricciones,
                        'temporada': preferencias.temporada,
                        'tradicion': preferencias.tradicion,
                        'estilo': preferencias.estilo,
                        'tipo_evento': preferencias.tipo_evento
                    }
                    
                    # Validar usando el validador completo
                    resultados_validacion = self.validador.validar_plato_completo(plato_obj, contexto)
                    
                    # Recopilar errores
                    for regla_nombre, resultado in resultados_validacion.items():
                        if not resultado.valido:
                            for error in resultado.errores:
                                errores.append(f"{tipo_plato} ({nombre_plato}): {error}")
                
            except Exception as e:
                errores.append(f"Error durante validación: {str(e)}")
        
        return {
            'errores': errores,
            'valido': len(errores) == 0
        }
    
    def _fase_actualizacion_interna(self, menu: Dict, preferencias: PreferenciasUsuario, 
                           exito: bool, reparaciones_aplicadas: List[Dict] = None) -> Optional[str]:
        """Ejecuta la actualización interna de la base de conocimiento (sin imprimir encabezado)."""
        # Limpiar objetos Plato de las reparaciones antes de guardar (no son JSON serializables)
        if reparaciones_aplicadas:
            for rep in reparaciones_aplicadas:
                if 'plato_modificado_obj' in rep:
                    del rep['plato_modificado_obj']
        
        # Crear objeto Menu para actualización
        menu_obj = Menu(
            entrante=menu.get('entrante', ''),
            principal=menu.get('principal', ''),
            postre=menu.get('postre', '')
        )
        
        print("\nActualizando base de casos...")
        
        # Procesar actualización
        actualizaciones = self.actualizador.procesar_nuevo_menu(
            menu=menu_obj,
            tipo_evento=preferencias.tipo_evento,
            temporada=preferencias.temporada,
            restricciones=preferencias.restricciones,
            estilo=preferencias.estilo,
            tradicion=preferencias.tradicion,
            exito=exito,
            reparaciones_aplicadas=reparaciones_aplicadas,
            feedback=f"Generado por sistema CBR - {'Exitoso' if exito else 'Fallido'}",
            crear_backup=self.config.crear_backup
        )
        
        nuevo_caso_id = actualizaciones.get('casos_agregados', [None])[0]
        
        if nuevo_caso_id:
            print(f"Nuevo caso agregado: {nuevo_caso_id}")
        
        return nuevo_caso_id
    
    def _crear_resultado_fallo(self, mensaje: str, detalles: Dict = None) -> ResultadoCBR:
        """Crea un resultado de fallo y actualiza estadísticas."""
        self.estadisticas['casos_fallidos'] += 1
        
        resultado = ResultadoCBR(
            exito=False,
            mensaje=mensaje,
            fallos_encontrados=detalles.get('errores', []) if detalles else []
        )
        
        return resultado
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas completas del sistema CBR."""
        stats_recuperador = self.recuperador.estadisticas_base_casos()
        stats_actualizador = self.actualizador.obtener_estadisticas_actualizaciones()
        
        return {
            'sistema': self.estadisticas.copy(),
            'base_casos': stats_recuperador,
            'actualizaciones': stats_actualizador,
            'tasa_exito': (self.estadisticas['casos_exitosos'] / 
                          max(1, self.estadisticas['casos_procesados'])) * 100
        }