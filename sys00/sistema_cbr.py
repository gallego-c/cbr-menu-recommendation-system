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
from recuperador import ModuloRecuperacion, ConfiguracionRecuperacion
from validador import ValidadorCompleto
from reparador import Reparador
from actualizador import ActualizadorConocimiento, NuevoMenu


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
            # Configurar recuperador
            config_recuperacion = ConfiguracionRecuperacion(
                k=self.config.k_casos_recuperar,
                umbral_minimo=self.config.umbral_similitud_minimo,
                explicar_similitud=self.config.usar_explicaciones
            )
            self.recuperador = ModuloRecuperacion(config_recuperacion)
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
                
                # Validar caso (sin mostrar título, ya lo mostramos arriba)
                validacion = self._fase_validacion(resultado_rec_dict, preferencias, 
                                                   mostrar_titulo=False)
                
                casos_validados.append({
                    'caso': resultado_rec_dict,
                    'validacion': validacion
                })
            
            # Paso 3: Reparar los casos que no son válidos
            print("\n" + "="*70)
            print("FASE 3: REPARACIÓN DE LOS MENÚS")
            print("="*70)
            
            casos_procesados = []
            for caso_val in casos_validados:
                if not caso_val['validacion']['valido']:
                    # Reparar caso
                    resultado_reparacion = self._fase_reparacion(caso_val['caso'], preferencias, 
                                                                 caso_val['validacion'],
                                                                 mostrar_titulo=False)
                    
                    if resultado_reparacion['exito']:
                        menu_final = resultado_reparacion['menu']
                        reparaciones = resultado_reparacion['reparaciones_aplicadas']
                        intentos = resultado_reparacion['intentos_totales']
                        valido = True
                    else:
                        # Reparación falló, usar menú original pero marcarlo como no válido
                        menu_final = caso_val['caso']['caso']['menu']
                        reparaciones = []
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
            
            # Paso 4: Seleccionar el mejor caso procesado (primero válido o el de mayor similitud)
            print("\n" + "="*70)
            print("SELECCIÓN DEL MEJOR CASO")
            print("="*70)
            
            caso_seleccionado = None
            for caso_proc in casos_procesados:
                if caso_proc['valido']:
                    caso_seleccionado = caso_proc
                    print(f"\nCaso seleccionado: {caso_proc['caso']['caso']['id']} (VÁLIDO)")
                    print(f"  Similitud: {caso_proc['caso']['similitud']:.3f}")
                    print(f"  Reparaciones aplicadas: {len(caso_proc['reparaciones'])}")
                    break
            
            # Si ninguno es válido, usar el de mayor similitud (el primero)
            if not caso_seleccionado:
                caso_seleccionado = casos_procesados[0]
                print(f"\nNingún caso pudo ser validado/reparado exitosamente.")
                print(f"Usando caso con mayor similitud: {caso_seleccionado['caso']['caso']['id']}")
                return self._crear_resultado_fallo(
                    f"No se pudo obtener un menú válido después de validar y reparar los {len(casos_procesados)} casos",
                    caso_seleccionado['validacion']
                )
            
            # Extraer datos del caso seleccionado
            menu_final = caso_seleccionado['menu_final']
            reparaciones = caso_seleccionado['reparaciones']
            intentos = caso_seleccionado['intentos']
            resultado_validacion = caso_seleccionado['validacion']
            caso_base = caso_seleccionado['caso']
            
            if reparaciones:
                self.estadisticas['casos_reparados'] += 1
                self.estadisticas['reparaciones_totales'] += len(reparaciones)
            
            # Paso 5: Actualización de la base de conocimiento (solo el mejor caso)
            nuevo_caso_id = self._fase_actualizacion(menu_final, preferencias, True, reparaciones)
            
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
        resultados = self.recuperador.recuperar(consulta)
        
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
            
            # Cargar información de platos desde conocimiento
            try:
                platos_path = os.path.join(os.path.dirname(__file__), 'conocimiento', 'platos.json')
                with open(platos_path, 'r', encoding='utf-8') as f:
                    platos_db = json.load(f)
                
                ingredientes_path = os.path.join(os.path.dirname(__file__), 'conocimiento', 'ingredientes.json')
                with open(ingredientes_path, 'r', encoding='utf-8') as f:
                    ingredientes_db = json.load(f)
                
                # Validar cada plato del menú con restricciones
                for tipo_plato, nombre_plato in menu.items():
                    if not nombre_plato or nombre_plato.strip() == '':
                        continue
                    
                    # Buscar plato en base de datos
                    plato_info = next((p for p in platos_db if p['nombre'] == nombre_plato), None)
                    
                    if not plato_info:
                        errores.append(f"{tipo_plato}: Plato '{nombre_plato}' no encontrado en base de datos")
                        continue
                    
                    # Crear objeto Plato para validación
                    ingredientes_plato = []
                    ingrediente_sabor_obj = None
                    
                    for ing_nombre in plato_info.get('ingredientes', []):
                        ing_info = next((i for i in ingredientes_db if i['nombre'] == ing_nombre), None)
                        if ing_info:
                            ing_obj = Ingrediente(
                                nombre=ing_info['nombre'],
                                temporada=ing_info.get('temporada', []),
                                categoria=ing_info.get('categoria', 'vegetal'),
                                sabor=ing_info.get('sabor', 'salado')
                            )
                            ingredientes_plato.append(ing_obj)
                            
                            # Buscar el ingrediente que da el sabor dominante
                            if ing_nombre == plato_info.get('ingrediente_sabor'):
                                ingrediente_sabor_obj = ing_obj
                    
                    # Si no encontramos el ingrediente de sabor, usar el primero
                    if not ingrediente_sabor_obj and ingredientes_plato:
                        ingrediente_sabor_obj = ingredientes_plato[0]
                    
                    # Si aún no hay ingrediente de sabor, crear uno por defecto
                    if not ingrediente_sabor_obj:
                        ingrediente_sabor_obj = Ingrediente(
                            nombre='ingrediente_generico',
                            temporada=[],
                            categoria='vegetal',
                            sabor='salado'
                        )
                    
                    plato = Plato(
                        nombre=plato_info['nombre'],
                        ingredientes=ingredientes_plato,
                        tecnica_coccion=plato_info.get('tecnica_coccion', []),
                        sabor_dominante=plato_info.get('sabor_dominante', 'salado'),
                        ingrediente_sabor=ingrediente_sabor_obj
                    )
                    
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
        
        # Procesar cada error
        errores_por_plato = self._agrupar_errores_por_plato(validacion.get('errores', []))
        
        for plato_nombre, errores_plato in errores_por_plato.items():
            intentos += 1
            if intentos > max_intentos:
                problemas_no_resueltos.extend(errores_plato)
                break
            
            print(f"\n  Reparando {plato_nombre}:")
            for error in errores_plato:
                print(f"    - {error}")
            
            # ESTRATEGIA 1: Intentar substitución completa del plato
            print(f"    [1/2] Intentando substitución...")
            plato_alternativo = self._buscar_plato_alternativo(
                plato_nombre, 
                preferencias,
                menu_reparado
            )
            
            if plato_alternativo:
                # Actualizar el plato en el menú
                if 'entrante' in plato_nombre.lower() or plato_nombre == menu_original.get('entrante', ''):
                    menu_reparado['entrante'] = plato_alternativo
                    tipo_plato = 'entrante'
                elif 'principal' in plato_nombre.lower() or plato_nombre == menu_original.get('principal', ''):
                    menu_reparado['principal'] = plato_alternativo
                    tipo_plato = 'principal'
                elif 'postre' in plato_nombre.lower() or plato_nombre == menu_original.get('postre', ''):
                    menu_reparado['postre'] = plato_alternativo
                    tipo_plato = 'postre'
                else:
                    tipo_plato = 'desconocido'
                
                reparaciones_aplicadas.append({
                    'tipo_plato': tipo_plato,
                    'plato_original': plato_nombre,
                    'plato_nuevo': plato_alternativo,
                    'accion': 'substitucion',
                    'errores_resueltos': errores_plato
                })
                print(f"    ✓ Substituido por: {plato_alternativo}")
            else:
                # ESTRATEGIA 2: Intentar modificar ingredientes del plato
                print(f"    [2/2] Intentando modificación de ingredientes...")
                try:
                    resultado_modificacion = self._intentar_modificacion_plato(
                        plato_nombre,
                        errores_plato,
                        preferencias,
                        menu_reparado
                    )
                except Exception as e:
                    print(f"    ✗ Error en modificación: {e}")
                    resultado_modificacion = {'exito': False}
                
                if resultado_modificacion['exito']:
                    # Actualizar el plato en el menú con el plato modificado
                    plato_modificado_nombre = resultado_modificacion['plato_modificado']
                    
                    if 'entrante' in plato_nombre.lower() or plato_nombre == menu_original.get('entrante', ''):
                        menu_reparado['entrante'] = plato_modificado_nombre
                        tipo_plato = 'entrante'
                    elif 'principal' in plato_nombre.lower() or plato_nombre == menu_original.get('principal', ''):
                        menu_reparado['principal'] = plato_modificado_nombre
                        tipo_plato = 'principal'
                    elif 'postre' in plato_nombre.lower() or plato_nombre == menu_original.get('postre', ''):
                        menu_reparado['postre'] = plato_modificado_nombre
                        tipo_plato = 'postre'
                    else:
                        tipo_plato = 'desconocido'
                    
                    reparaciones_aplicadas.append({
                        'tipo_plato': tipo_plato,
                        'plato_original': plato_nombre,
                        'plato_modificado': plato_modificado_nombre,
                        'accion': 'modificacion',
                        'modificaciones': resultado_modificacion['modificaciones'],
                        'errores_resueltos': errores_plato
                    })
                    
                    for modificacion in resultado_modificacion['modificaciones']:
                        print(f"    ✓ {modificacion}")
                else:
                    problemas_no_resueltos.extend(errores_plato)
                    print(f"    ✗ No se pudo reparar el plato")
        
        # Resultado de la reparación
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
            print(f"  ✓ Reparacion exitosa")
            print(f"  Reparaciones aplicadas: {len(reparaciones_aplicadas)}")
        else:
            print(f"  ✗ Reparacion parcial")
            print(f"  Reparaciones aplicadas: {len(reparaciones_aplicadas)}")
            print(f"  Problemas sin resolver: {len(problemas_no_resueltos)}")
        
        return resultado
    
    def _intentar_modificacion_plato(self, plato_nombre: str, errores: List[str],
                                    preferencias: PreferenciasUsuario, 
                                    menu_actual: Dict) -> Dict:
        """
        Intenta modificar un plato cambiando ingredientes problemáticos.
        
        Returns:
            Dict con 'exito', 'plato_modificado', 'modificaciones'
        """
        from reparador.modificar import ModificadorPlatos
        from conocimiento.models import Plato, Ingrediente, TecnicaCoccion, CategoriaIngrediente
        import json
        import os
        
        # Cargar reglas de reparación
        ruta_reglas = os.path.join(os.path.dirname(__file__), 'conocimiento', 'reparaciones.json')
        try:
            with open(ruta_reglas, 'r', encoding='utf-8') as f:
                reglas = json.load(f)
        except Exception as e:
            return {'exito': False, 'plato_modificado': plato_nombre, 'modificaciones': []}
        
        # Cargar info del plato
        ruta_platos = os.path.join(os.path.dirname(__file__), 'conocimiento', 'platos.json')
        try:
            with open(ruta_platos, 'r', encoding='utf-8') as f:
                platos = json.load(f)
        except Exception as e:
            return {'exito': False, 'plato_modificado': plato_nombre, 'modificaciones': []}
        
        # Buscar el plato
        plato_data = None
        for p in platos:
            if p['nombre'] == plato_nombre:
                plato_data = p
                break
        
        if not plato_data:
            return {'exito': False, 'plato_modificado': plato_nombre, 'modificaciones': []}
        
        # Crear objeto Plato
        try:
            ingredientes = []
            for ing_nombre in plato_data.get('ingredientes', []):
                ing_info = self._buscar_info_ingrediente(ing_nombre)
                if ing_info:
                    from conocimiento.models import Temporada, Sabor
                    
                    # Categoría
                    cat_str = ing_info.get('categoria', 'condimento')
                    try:
                        categoria = cat_str
                    except:
                        categoria = 'condimento'
                    
                    # Temporadas
                    temporadas = []
                    for temp_str in ing_info.get('temporada', []):
                        try:
                            temporadas.append(Temporada(temp_str))
                        except:
                            pass
                    if not temporadas:
                        temporadas = [Temporada.PRIMAVERA, Temporada.VERANO, Temporada.OTONO, Temporada.INVIERNO]
                    
                    # Sabor
                    sabor_str = ing_info.get('sabor', 'umami')
                    try:
                        sabor = Sabor(sabor_str)
                    except:
                        sabor = Sabor.UMAMI
                    
                    ingredientes.append(Ingrediente(
                        nombre=ing_nombre,
                        temporada=temporadas,
                        categoria=categoria,
                        sabor=sabor
                    ))
            
            # Técnica de cocción
            tecnicas = []
            tecnica_str = plato_data.get('tecnica', 'horneado')
            try:
                tecnicas.append(TecnicaCoccion(tecnica_str))
            except:
                tecnicas.append(TecnicaCoccion.HORNEADO)
            
            # Sabor dominante (usar el primer ingrediente como referencia)
            sabor_dominante = ingredientes[0].sabor if ingredientes else Sabor.UMAMI
            ingrediente_sabor = ingredientes[0] if ingredientes else None
            
            plato = Plato(
                nombre=plato_data['nombre'],
                ingredientes=ingredientes,
                tecnica_coccion=tecnicas,
                sabor_dominante=sabor_dominante,
                ingrediente_sabor=ingrediente_sabor
            )
        except Exception as e:
            return {'exito': False, 'plato_modificado': plato_nombre, 'modificaciones': []}
        
        # Crear modificador
        modificador = ModificadorPlatos(reglas)
        
        # Determinar tipo de problema de los errores
        modificaciones_realizadas = []
        for error in errores:
            tipo_problema = self._extraer_tipo_problema(error)
            problema_especifico = error
            
            print(f"        → Tipo '{tipo_problema}': {error[:70]}...")
            
            # Aplicar modificación
            resultado = modificador.aplicar_modificaciones(plato, tipo_problema, problema_especifico)
            
            print(f"        → Resultado: exito={resultado['exito']}")
            if 'mensajes' in resultado and resultado['mensajes']:
                print(f"        → Modificaciones aplicadas:")
                for msg in resultado['mensajes']:
                    print(f"           • {msg}")
            if 'motivo_fallo' in resultado:
                print(f"        → Motivo fallo: {resultado['motivo_fallo']}")
            if 'regla_aplicada' in resultado:
                print(f"        → Regla aplicada: {resultado['regla_aplicada'].get('modo_aplicacion', 'N/A')}")
            
            if resultado['exito']:
                modificaciones_realizadas.extend(resultado['mensajes'])
        
        # Si se realizaron modificaciones, validar el plato modificado
        if modificaciones_realizadas:
            # Crear nuevo nombre para el plato modificado
            nuevo_nombre = self._generar_nombre_plato_modificado(plato_nombre, modificaciones_realizadas)
            plato.nombre = nuevo_nombre
            
            print(f"        → Nuevo nombre del plato: {nuevo_nombre}")
            
            contexto = {
                'restricciones': preferencias.restricciones,
                'temporada': preferencias.temporada,
                'tradicion': preferencias.tradicion,
                'estilo': preferencias.estilo
            }
            
            resultados_validacion = self.validador.validar_plato_completo(plato, contexto)
            
            # Si ahora es válido, retornar éxito
            if all(r.valido for r in resultados_validacion.values()):
                print(f"        → ✓ El plato modificado ES VÁLIDO")
                return {
                    'exito': True,
                    'plato_modificado': plato.nombre,
                    'modificaciones': modificaciones_realizadas
                }
            else:
                print(f"        → ✗ El plato modificado AÚN NO es válido")
                errores_restantes = []
                for tipo, resultado in resultados_validacion.items():
                    if not resultado.valido:
                        errores_restantes.extend(resultado.errores)
                print(f"        → Errores restantes: {len(errores_restantes)}")
                for err in errores_restantes[:3]:  # Mostrar máximo 3
                    print(f"           - {err}")
        
        return {'exito': False, 'plato_modificado': plato_nombre, 'modificaciones': modificaciones_realizadas}
    
    def _generar_nombre_plato_modificado(self, nombre_original: str, modificaciones: List[str]) -> str:
        """
        Genera un nuevo nombre para el plato basado en las modificaciones aplicadas.
        """
        # Extraer ingredientes añadidos o substituidos
        ingredientes_nuevos = []
        for mod in modificaciones:
            if "Substituido" in mod:
                # Formato: "Substituido X por Y"
                partes = mod.split(" por ")
                if len(partes) == 2:
                    ingrediente_nuevo = partes[1].strip()
                    ingredientes_nuevos.append(ingrediente_nuevo.capitalize())
            elif "Añadido ingrediente" in mod:
                # Formato: "Añadido ingrediente X"
                partes = mod.split("ingrediente ")
                if len(partes) == 2:
                    ingrediente_nuevo = partes[1].strip()
                    ingredientes_nuevos.append(ingrediente_nuevo.capitalize())
        
        # Si hay ingredientes nuevos destacables, crear nombre descriptivo
        if ingredientes_nuevos:
            # Tomar los primeros 2 ingredientes más relevantes
            ingredientes_destacados = ingredientes_nuevos[:2]
            if len(ingredientes_destacados) == 1:
                nuevo_nombre = f"{nombre_original} con {ingredientes_destacados[0]}"
            else:
                nuevo_nombre = f"{nombre_original} con {' y '.join(ingredientes_destacados)}"
        else:
            nuevo_nombre = f"{nombre_original} (Modificado)"
        
        return nuevo_nombre
    
    def _extraer_tipo_problema(self, error: str) -> str:
        """Extrae el tipo de problema de un mensaje de error."""
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
    
    def _agrupar_errores_por_plato(self, errores: List[str]) -> Dict[str, List[str]]:
        """Agrupa errores por nombre de plato."""
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
    
    def _buscar_plato_alternativo(self, plato_original: str, preferencias: PreferenciasUsuario, 
                                  menu_actual: Dict) -> Optional[str]:
        """Busca un plato alternativo que cumpla las preferencias."""
        # Cargar base de platos
        import json
        import os
        
        ruta_platos = os.path.join(os.path.dirname(__file__), 'conocimiento', 'platos.json')
        try:
            with open(ruta_platos, 'r', encoding='utf-8') as f:
                platos = json.load(f)
        except:
            return None
        
        # Determinar tipo de plato
        tipo_plato = None
        if plato_original == menu_actual.get('entrante', ''):
            tipo_plato = 'entrante'
        elif plato_original == menu_actual.get('principal', ''):
            tipo_plato = 'principal'
        elif plato_original == menu_actual.get('postre', ''):
            tipo_plato = 'postre'
        
        if not tipo_plato:
            return None
        
        # Buscar platos alternativos del mismo tipo
        platos_alternativos = [p for p in platos if p.get('tipo') == tipo_plato and p['nombre'] != plato_original]
        
        # Validar cada alternativa
        for plato_data in platos_alternativos:
            # Crear objeto Plato para validar
            from conocimiento.models import Plato, Ingrediente, TecnicaCoccion, CategoriaIngrediente, Temporada, TradicionCultural
            
            try:
                ingredientes = []
                for ing_nombre in plato_data.get('ingredientes', []):
                    # Buscar info del ingrediente
                    ing_info = self._buscar_info_ingrediente(ing_nombre)
                    if ing_info:
                        from conocimiento.models import Sabor
                        
                        # Categoría
                        categoria = ing_info.get('categoria', 'condimento')
                        
                        # Temporadas
                        temporadas = []
                        for temp_str in ing_info.get('temporada', []):
                            try:
                                temporadas.append(Temporada(temp_str))
                            except:
                                pass
                        if not temporadas:
                            temporadas = [Temporada.PRIMAVERA, Temporada.VERANO, Temporada.OTONO, Temporada.INVIERNO]
                        
                        # Sabor
                        sabor_str = ing_info.get('sabor', 'umami')
                        try:
                            sabor = Sabor(sabor_str)
                        except:
                            sabor = Sabor.UMAMI
                        
                        ingredientes.append(Ingrediente(
                            nombre=ing_nombre,
                            temporada=temporadas,
                            categoria=categoria,
                            sabor=sabor
                        ))
                
                # Crear plato
                tecnicas = []
                tecnica_str = plato_data.get('tecnica', 'horneado')
                try:
                    tecnicas.append(TecnicaCoccion(tecnica_str))
                except:
                    tecnicas.append(TecnicaCoccion.HORNEADO)
                
                # Sabor dominante (usar el primer ingrediente como referencia)
                sabor_dominante = ingredientes[0].sabor if ingredientes else Sabor.UMAMI
                ingrediente_sabor = ingredientes[0] if ingredientes else None
                
                plato = Plato(
                    nombre=plato_data['nombre'],
                    ingredientes=ingredientes,
                    tecnica_coccion=tecnicas,
                    sabor_dominante=sabor_dominante,
                    ingrediente_sabor=ingrediente_sabor
                )
                
                # Validar este plato
                contexto = {
                    'restricciones': preferencias.restricciones,
                    'temporada': preferencias.temporada,
                    'tradicion': preferencias.tradicion,
                    'estilo': preferencias.estilo
                }
                
                resultados_validacion = self.validador.validar_plato_completo(plato, contexto)
                
                # Si pasa todas las validaciones, retornar este plato
                if all(r.valido for r in resultados_validacion.values()):
                    return plato_data['nombre']
            
            except Exception as e:
                continue
        
        return None
    
    def _buscar_info_ingrediente(self, nombre_ingrediente: str) -> Optional[Dict]:
        """Busca información de un ingrediente en la base de conocimiento."""
        import json
        import os
        
        ruta_ingredientes = os.path.join(os.path.dirname(__file__), 'conocimiento', 'ingredientes.json')
        try:
            with open(ruta_ingredientes, 'r', encoding='utf-8') as f:
                ingredientes = json.load(f)
                for ing in ingredientes:
                    if ing['nombre'] == nombre_ingrediente:
                        return ing
        except:
            pass
        
        return None
    
    def _fase_actualizacion(self, menu: Dict, preferencias: PreferenciasUsuario, 
                           exito: bool, reparaciones_aplicadas: List[Dict] = None) -> Optional[str]:
        """Ejecuta la fase de actualización de la base de conocimiento."""
        print("\n" + "="*70)
        print("FASE 4: ACTUALIZACIÓN DE LA BASE DE CONOCIMIENTO")
        print("="*70)
        
        # Crear nuevo menú para actualización
        nuevo_menu = NuevoMenu(
            entrante=menu.get('entrante', ''),
            principal=menu.get('principal', ''),
            postre=menu.get('postre', ''),
            tipo_evento=preferencias.tipo_evento,
            temporada=preferencias.temporada,
            restricciones=preferencias.restricciones,
            estilo=preferencias.estilo,
            tradicion=preferencias.tradicion,
            exito=exito,
            feedback=f"Generado por sistema CBR - {'Exitoso' if exito else 'Fallido'}",
            reparaciones_aplicadas=reparaciones_aplicadas
        )
        
        print("\nActualizando base de casos...")
        
        # Procesar actualización
        actualizaciones = self.actualizador.procesar_nuevo_menu(
            nuevo_menu, 
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