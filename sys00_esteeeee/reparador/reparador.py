import sys
import os
from typing import List, Dict, Any, Optional

# Añadir el directorio padre al path para importar models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from conocimiento.models import Plato, Ingrediente, TipoRegla, Temporada, Sabor, Menu, Caso
from conocimiento import cargador

# Importar clases especializadas
from .substituir import SubstitutorPlatos
from .modificar import ModificadorPlatos
from .ingredient_substitutor import IngredientSubstitutor


class Reparador:
    """
    Clase principal del reparador que implementa una estrategia en cascada:
    1. Intentar sustituir el plato completo (con validación de compatibilidad)
    2. Si falla, intentar reparar sustituyendo ingredientes individuales
    3. Si falla, intentar modificar el plato actual según reglas
    """
    
    def __init__(self, archivo_reglas: str = "reparaciones.json", archivo_casos: str = "casos.json"):
        """
        Inicializa el reparador con reglas de modificación y casos para substitución
        
        Args:
            archivo_reglas: Archivo JSON con reglas de modificación de platos
            archivo_casos: Archivo JSON con casos base para substitución de platos
        """
        self.reglas_modificacion = cargador.cargar_json(archivo_reglas)
        self.casos_base = cargador.cargar_casos()
        
        # Componentes especializados (orden de prioridad en la estrategia)
        self.substitutor_platos = SubstitutorPlatos(self.casos_base)
        self.substitutor_ingredientes = IngredientSubstitutor()
        self.modificador_platos = ModificadorPlatos(self.reglas_modificacion)
    
    def reparar_plato(self, plato_problematico: Plato, menu: Menu, 
                     tipo_problema: str, problema_especifico: str) -> Dict[str, Any]:
        """
        Método principal para reparar un plato problemático.
        Estrategia en cascada (orden de prioridad):
        1. Intentar sustituir el plato completo (con validación de que al menos 2 ingredientes combinen con el menú)
        2. Si falla, intentar reparar sustituyendo ingredientes individuales
        3. Si falla, intentar modificar el plato actual según reglas
        
        Args:
            plato_problematico: El plato que necesita ser reparado
            menu: El menú completo con todas las preferencias
            tipo_problema: Tipo de problema (restricciones, temporada, sabor, etc.)
            problema_especifico: Descripción específica del problema
            
        Returns:
            Diccionario con el resultado de la reparación:
            {
                'estrategia': 'substitucion' | 'ingredientes' | 'modificacion',
                'plato_resultado': Plato,
                'mensajes': List[str],
                'exito': bool
            }
        """
        
        # OPTIMIZACIÓN: Para problemas de restricciones dietarias, ir directo a sustitución de ingredientes
        # Para problemas de tradición, verificar si es "plato de tradición incorrecta" o "ingredientes incorrectos"
        if tipo_problema.lower() == 'restricciones':
            print(f"        [DEBUG] Problema de restricciones - saltando a ESTRATEGIA 2 (ingredientes)")
            resultado_ingredientes = self.substitutor_ingredientes.intentar_reparacion_por_ingredientes(
                plato_problematico, menu, tipo_problema, problema_especifico
            )
            
            print(f"        [DEBUG] Resultado ESTRATEGIA 2: exito={resultado_ingredientes['exito']}")
            
            if resultado_ingredientes['exito']:
                return {
                    'estrategia': 'ingredientes',
                    'plato_resultado': resultado_ingredientes['plato_modificado'],
                    'mensajes': [
                        f"[OK] Plato reparado sustituyendo ingredientes:",
                        f"  Plato: {plato_problematico.nombre}"
                    ] + resultado_ingredientes['mensajes'],
                    'exito': True,
                    'ingredientes_sustituidos': resultado_ingredientes['ingredientes_sustituidos']
                }
            else:
                # Si falla sustitución de ingredientes, fallar (no intentar otras estrategias)
                return {
                    'estrategia': None,
                    'plato_resultado': None,
                    'mensajes': ['No se pudo reparar sustituyendo ingredientes'],
                    'exito': False
                }
        
        # Para problemas de tradición, verificar si el plato pertenece a otra tradición
        if 'tradicion' in tipo_problema.lower() or 'tradición' in tipo_problema.lower():
            # Si el problema es "El plato X pertenece a la tradición Y", es un plato de tradición incorrecta
            # En este caso, usar ESTRATEGIA 1 (sustituir plato completo)
            if 'pertenece a la tradición' in problema_especifico or 'pertenece a la tradici' in problema_especifico:
                print(f"        [DEBUG] Plato de tradición incorrecta - usando ESTRATEGIA 1 (sustituir plato completo)")
                # Continuar con ESTRATEGIA 1 normal (no hacer return aquí)
            else:
                # El problema es solo de ingredientes, usar ESTRATEGIA 2
                print(f"        [DEBUG] Problema de ingredientes de tradición - saltando a ESTRATEGIA 2 (ingredientes)")
                resultado_ingredientes = self.substitutor_ingredientes.intentar_reparacion_por_ingredientes(
                    plato_problematico, menu, tipo_problema, problema_especifico
                )
                
                print(f"        [DEBUG] Resultado ESTRATEGIA 2: exito={resultado_ingredientes['exito']}")
                
                if resultado_ingredientes['exito']:
                    return {
                        'estrategia': 'ingredientes',
                        'plato_resultado': resultado_ingredientes['plato_modificado'],
                        'mensajes': [
                            f"[OK] Plato reparado sustituyendo ingredientes:",
                            f"  Plato: {plato_problematico.nombre}"
                        ] + resultado_ingredientes['mensajes'],
                        'exito': True,
                        'ingredientes_sustituidos': resultado_ingredientes['ingredientes_sustituidos']
                    }
                else:
                    # Si falla sustitución de ingredientes, fallar (no intentar otras estrategias)
                    return {
                        'estrategia': None,
                        'plato_resultado': None,
                        'mensajes': ['No se pudo reparar sustituyendo ingredientes'],
                        'exito': False
                    }
        
        print(f"        [DEBUG] Intentando ESTRATEGIA 1: Sustitución de plato completo")
        # ESTRATEGIA 1: Intentar sustituir el plato completo
        # Ventaja: Si hay un plato que cumple todo, es la solución más limpia
        # Validación: El nuevo plato debe tener al menos 2 ingredientes compatibles con el resto del menú
        resultado_substitucion = self.substitutor_platos.buscar_plato_substitucion(
            plato_problematico, menu, tipo_problema, problema_especifico
        )
        
        print(f"        [DEBUG] Resultado ESTRATEGIA 1: exito={resultado_substitucion['exito']}")
        
        if resultado_substitucion['exito']:
            return {
                'estrategia': 'substitucion',
                'plato_resultado': resultado_substitucion['plato_substitucion'],
                'mensajes': [
                    f"[OK] Plato completo substituido:",
                    f"  Original: {plato_problematico.nombre}",
                    f"  Nuevo: {resultado_substitucion['plato_substitucion'].nombre}"
                ] + resultado_substitucion['mensajes'],
                'exito': True
            }
        
        print(f"        [DEBUG] Intentando ESTRATEGIA 2: Sustitución de ingredientes individuales")
        # ESTRATEGIA 2: Intentar reparar sustituyendo ingredientes individuales
        # Ventaja: Preserva el plato original, solo cambia ingredientes problemáticos
        resultado_ingredientes = self.substitutor_ingredientes.intentar_reparacion_por_ingredientes(
            plato_problematico, menu, tipo_problema, problema_especifico
        )
        
        print(f"        [DEBUG] Resultado ESTRATEGIA 2: exito={resultado_ingredientes['exito']}")
        
        if resultado_ingredientes['exito']:
            return {
                'estrategia': 'ingredientes',
                'plato_resultado': resultado_ingredientes['plato_modificado'],
                'mensajes': [
                    f"[OK] Plato reparado sustituyendo ingredientes:",
                    f"  Plato: {plato_problematico.nombre}"
                ] + resultado_ingredientes['mensajes'],
                'exito': True,
                'ingredientes_sustituidos': resultado_ingredientes['ingredientes_sustituidos']
            }
        
        # ESTRATEGIA 3: Intentar modificar el plato actual según reglas
        # IMPORTANTE: NO usar modificaciones basadas en reglas para problemas de tradición
        # (añadir chili_powder a un plato catalán no tiene sentido culinario)
        
        if tipo_problema.lower() == 'tradicion' or 'tradición' in tipo_problema.lower():
            # Para problemas de tradición, si no se pudo sustituir el plato completo,
            # es mejor fallar que añadir ingredientes inapropiados
            return {
                'estrategia': 'ninguna',
                'plato_resultado': plato_problematico,
                'mensajes': [
                    f"✗ No se pudo reparar el plato:",
                    f"  El plato '{plato_problematico.nombre}' no es de la tradición requerida",
                    f"  No hay platos de sustitución adecuados disponibles",
                    f"  No se aplicaron modificaciones para preservar coherencia culinaria"
                ],
                'exito': False
            }
        
        # Para otros tipos de problemas, intentar modificaciones basadas en reglas
        resultado_modificacion = self.modificador_platos.aplicar_modificaciones(
            plato_problematico, tipo_problema, problema_especifico
        )
        
        return {
            'estrategia': 'modificacion',
            'plato_resultado': resultado_modificacion['plato_modificado'],
            'mensajes': [
                f"[~] Plato modificado según reglas:",
                f"  Plato: {plato_problematico.nombre}"
            ] + resultado_modificacion['mensajes'],
            'exito': resultado_modificacion['exito']
        }
    
    def reparar_por_nombre(self, plato_nombre: str, tipo_problema: str, 
                          problema_especifico: str, menu_dict: Dict, 
                          preferencias: Dict) -> Dict[str, Any]:
        """
        Repara un plato dado solo su nombre (carga todos los datos internamente).
        Este método es la interfaz para sistema_cbr.py que no debe cargar datos.
        
        Args:
            plato_nombre: Nombre del plato a reparar
            tipo_problema: Tipo de problema (restricciones, temporada, etc.)
            problema_especifico: Descripción específica del problema
            menu_dict: Diccionario con el menú actual
            preferencias: Preferencias del usuario
            
        Returns:
            Dict con 'exito', 'plato_resultado' o 'plato_modificado', 'mensajes', 'estrategia'
        """
        try:
            from conocimiento import cargador, Ingrediente, Plato, Menu
            
            # Cargar conocimiento necesario
            platos_db = cargador.cargar_platos()
            ingredientes_db = cargador.cargar_ingredientes()
            
            # Buscar información del plato
            if isinstance(platos_db, dict):
                plato_info = platos_db.get(plato_nombre)
            else:
                plato_info = next((p for p in platos_db if p.get('nombre') == plato_nombre), None)
            
            if not plato_info:
                return {
                    'exito': False, 
                    'mensajes': [f'Plato {plato_nombre} no encontrado en base de datos']
                }
            
            # Crear objeto Plato usando from_dict (que maneja la estructura correctamente)
            plato_obj = Plato.from_dict(plato_info)
            
            # Crear objeto Menu con todas las preferencias necesarias
            menu_obj = Menu(
                entrante=menu_dict.get('entrante', ''),
                principal=menu_dict.get('principal', ''),
                postre=menu_dict.get('postre', '')
            )
            # Copiar preferencias al objeto menu
            if 'restricciones' in preferencias:
                menu_obj.restricciones = preferencias['restricciones']
            if 'temporada' in preferencias:
                menu_obj.temporada = preferencias['temporada']
            if 'tradicion' in preferencias:
                menu_obj.tradicion = preferencias['tradicion']
            if 'estilo' in preferencias:
                menu_obj.estilo = preferencias['estilo']
            
            # Llamar al reparador principal
            resultado = self.reparar_plato(plato_obj, menu_obj, tipo_problema, problema_especifico)
            
            if resultado['exito']:
                plato_resultado = resultado['plato_resultado']
                
                # El plato_resultado puede ser un objeto Plato (ingredientes) o Plato (substitución)
                # En ambos casos, retornar el nombre
                nombre_final = plato_resultado.nombre if hasattr(plato_resultado, 'nombre') else str(plato_resultado)
                
                # Preparar respuesta compatible con sistema_cbr
                return {
                    'exito': True,
                    'plato_resultado': plato_resultado,  # Mantener objeto para uso interno
                    'plato_modificado': nombre_final,     # String para compatibilidad con sistema_cbr
                    'mensajes': resultado['mensajes'],
                    'modificaciones': resultado['mensajes'],  # Alias para compatibilidad
                    'estrategia': resultado['estrategia']
                }
            else:
                return {
                    'exito': False,
                    'mensajes': resultado.get('mensajes', ['Reparación falló']),
                    'estrategia': resultado.get('estrategia', 'ninguna')
                }
                
        except Exception as e:
            import traceback
            return {
                'exito': False,
                'mensajes': [f'Error en reparación: {str(e)}', traceback.format_exc()]
            }
    
    def reparar_menu_completo(self, menu: Menu) -> Dict[str, Any]:
        """
        Repara todos los platos problemáticos de un menú
        
        Args:
            menu: Menú completo a reparar
            
        Returns:
            Diccionario con resultados de todas las reparaciones
        """
        resultados = {
            'menu_reparado': menu,
            'reparaciones_aplicadas': [],
            'platos_sin_solucion': [],
            'exito_general': True
        }
        
        # Analizar cada plato del menú
        for i, plato in enumerate(menu.platos):
            problemas = self._detectar_problemas_plato(plato, menu)
            
            if problemas:
                for problema in problemas:
                    resultado = self.reparar_plato(
                        plato, menu, problema['tipo'], problema['descripcion']
                    )
                    
                    if resultado['exito']:
                        # Actualizar el plato en el menú
                        menu.platos[i] = resultado['plato_resultado']
                        resultados['reparaciones_aplicadas'].append({
                            'plato_original': plato.nombre,
                            'problema': problema,
                            'solucion': resultado
                        })
                    else:
                        resultados['platos_sin_solucion'].append({
                            'plato': plato.nombre,
                            'problema': problema,
                            'intentos_fallidos': resultado
                        })
                        resultados['exito_general'] = False
        
        return resultados
    
    def _detectar_problemas_plato(self, plato: Plato, menu: Menu) -> List[Dict[str, str]]:
        """
        Detecta problemas en un plato según las preferencias del menú
        
        Args:
            plato: Plato a analizar
            menu: Menú con las preferencias
            
        Returns:
            Lista de problemas encontrados
        """
        problemas = []
        
        # Verificar restricciones dietéticas
        if menu.restricciones:
            for restriccion in menu.restricciones:
                if not self._cumple_restriccion(plato, restriccion):
                    problemas.append({
                        'tipo': 'restricciones',
                        'descripcion': f"No cumple restricción: {restriccion.value}"
                    })
        
        # Verificar temporada
        if menu.temporada:
            if not self._es_temporada_apropiada(plato, menu.temporada):
                problemas.append({
                    'tipo': 'temporada',
                    'descripcion': f"Ingredientes fuera de temporada: {menu.temporada.value}"
                })
        
        # Verificar tradición culinaria
        if menu.tradicion and plato.tradicion != menu.tradicion:
            problemas.append({
                'tipo': 'tradicion',
                'descripcion': f"Tradición incorrecta: {plato.tradicion.value} -> {menu.tradicion.value}"
            })
        
        # Verificar técnica de cocción preferida
        if menu.tecnica_preferida and plato.tecnica != menu.tecnica_preferida:
            problemas.append({
                'tipo': 'coherencia',
                'descripcion': f"Técnica incorrecta: {plato.tecnica.value} -> {menu.tecnica_preferida.value}"
            })
        
        return problemas
    
    def _cumple_restriccion(self, plato: Plato, restriccion) -> bool:
        """Verifica si un plato cumple una restricción dietética"""
        # Lógica específica para cada restricción
        if restriccion.value == "vegano":
            categorias_no_veganas = ["animal", "lacteo"]
            for ingrediente in plato.ingredientes:
                if hasattr(ingrediente.categoria, 'value'):
                    if ingrediente.categoria.value in categorias_no_veganas:
                        return False
                elif str(ingrediente.categoria) in categorias_no_veganas:
                    return False
        
        elif restriccion.value == "sin_lactosa":
            for ingrediente in plato.ingredientes:
                if hasattr(ingrediente.categoria, 'value'):
                    if ingrediente.categoria.value == "lacteo":
                        return False
                elif str(ingrediente.categoria) == "lacteo":
                    return False
        
        return True
    
    def _es_temporada_apropiada(self, plato: Plato, temporada_deseada) -> bool:
        """Verifica si los ingredientes del plato son apropiados para la temporada"""
        for ingrediente in plato.ingredientes:
            if temporada_deseada not in ingrediente.temporada:
                # Si algún ingrediente principal no está en temporada
                if hasattr(ingrediente.categoria, 'value'):
                    categoria = ingrediente.categoria.value
                else:
                    categoria = str(ingrediente.categoria)
                
                if categoria in ["vegetal", "fruta"]:  # Solo verificar vegetales y frutas
                    return False
        
        return True
    
    def obtener_estadisticas_reparacion(self, menu_original: Menu, 
                                      resultado_reparacion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera estadísticas sobre el proceso de reparación
        
        Args:
            menu_original: Menú antes de la reparación
            resultado_reparacion: Resultado del proceso de reparación
            
        Returns:
            Estadísticas detalladas
        """
        stats = {
            'total_platos': len(menu_original.platos),
            'platos_reparados': len(resultado_reparacion['reparaciones_aplicadas']),
            'platos_sin_solucion': len(resultado_reparacion['platos_sin_solucion']),
            'estrategias_usadas': {
                'substitucion': 0,
                'modificacion': 0
            },
            'tipos_problemas_resueltos': {},
            'tasa_exito': 0.0
        }
        
        # Analizar reparaciones aplicadas
        for reparacion in resultado_reparacion['reparaciones_aplicadas']:
            estrategia = reparacion['solucion']['estrategia']
            stats['estrategias_usadas'][estrategia] += 1
            
            tipo_problema = reparacion['problema']['tipo']
            if tipo_problema not in stats['tipos_problemas_resueltos']:
                stats['tipos_problemas_resueltos'][tipo_problema] = 0
            stats['tipos_problemas_resueltos'][tipo_problema] += 1
        
        # Calcular tasa de éxito
        if stats['total_platos'] > 0:
            stats['tasa_exito'] = stats['platos_reparados'] / stats['total_platos']
        
        return stats
    
    @staticmethod
    def generar_nombre_plato_modificado(nombre_original: str, modificaciones: List[str]) -> str:
        """
        Genera un nuevo nombre para el plato basado en las modificaciones aplicadas.
        
        Args:
            nombre_original: Nombre original del plato
            modificaciones: Lista de modificaciones aplicadas
            
        Returns:
            Nuevo nombre descriptivo para el plato
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
            elif "Añadido ingrediente" in mod or "Añadido" in mod:
                # Formato: "Añadido ingrediente X" o "Añadido X"
                if "ingrediente" in mod:
                    partes = mod.split("ingrediente ")
                    if len(partes) == 2:
                        ingrediente_nuevo = partes[1].strip()
                        ingredientes_nuevos.append(ingrediente_nuevo.capitalize())
                else:
                    # Solo "Añadido X"
                    partes = mod.split("Añadido ")
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
    
    def reparar_plato_objeto(self, plato_obj: Plato, tipo_problema: str,
                            problema_especifico: str, preferencias: Dict) -> Dict[str, Any]:
        """
        Repara un objeto Plato que ya está en memoria (útil para reparaciones múltiples).
        No busca en la base de datos, trabaja directamente con el objeto proporcionado.
        
        IMPLEMENTA LA MISMA ESTRATEGIA EN CASCADA que reparar_plato():
        1. Intentar sustituir ingredientes individuales (si son restricciones)
        2. Si falla, intentar modificar el plato actual según reglas (NO para tradición)
        
        Args:
            plato_obj: Objeto Plato a reparar (se modifica in-place)
            tipo_problema: Tipo de problema (restricciones, temporada, etc.)
            problema_especifico: Descripción del problema
            preferencias: Diccionario con preferencias del usuario
            
        Returns:
            Dict con 'exito', 'plato_resultado' (objeto Plato), 'mensajes', 'estrategia'
        """
        try:
            # Crear objeto Menu a partir de preferencias (necesario para validación)
            from conocimiento.models import Menu
            menu_obj = Menu(
                entrante='',  # No importa para sustitución de ingredientes
                principal='',
                postre=''
            )
            # Copiar preferencias al objeto menu
            if 'restricciones' in preferencias:
                menu_obj.restricciones = preferencias['restricciones']
            if 'temporada' in preferencias:
                menu_obj.temporada = preferencias['temporada']
            if 'tradicion' in preferencias:
                menu_obj.tradicion = preferencias['tradicion']
            if 'estilo' in preferencias:
                menu_obj.estilo = preferencias['estilo']
            
            # ESTRATEGIA 1: Intentar reparar sustituyendo ingredientes individuales
            # (especialmente útil para problemas de restricciones como vegetariano)
            resultado_ingredientes = self.substitutor_ingredientes.intentar_reparacion_por_ingredientes(
                plato_obj, menu_obj, tipo_problema, problema_especifico
            )
            
            if resultado_ingredientes['exito']:
                plato_modificado = resultado_ingredientes['plato_modificado']
                return {
                    'exito': True,
                    'plato_resultado': plato_modificado,
                    'mensajes': resultado_ingredientes['mensajes'],
                    'estrategia': 'ingredientes',
                    'ingredientes_sustituidos': resultado_ingredientes['ingredientes_sustituidos']
                }
            
            # ESTRATEGIA 2: Intentar modificar el plato actual según reglas
            # IMPORTANTE: NO usar modificaciones basadas en reglas para problemas de tradición
            # (añadir chili_powder a un plato catalán no tiene sentido culinario)
            if tipo_problema.lower() == 'tradicion' or 'tradición' in tipo_problema.lower():
                return {
                    'exito': False,
                    'plato_resultado': plato_obj,
                    'mensajes': [
                        f"[X] No se pudo reparar el plato:",
                        f"  El plato '{plato_obj.nombre}' no es de la tradición requerida",
                        f"  No hay sustituciones de ingredientes disponibles",
                        f"  No se aplicaron modificaciones para preservar coherencia culinaria"
                    ],
                    'estrategia': 'ninguna'
                }
            
            # Para otros tipos de problemas, aplicar modificaciones usando el modificador
            resultado_mod = self.modificador_platos.aplicar_modificaciones(
                plato_obj, tipo_problema, problema_especifico
            )
            
            if resultado_mod['exito']:
                # Actualizar el nombre del plato con las modificaciones
                nombre_actualizado = self.generar_nombre_plato_modificado(
                    plato_obj.nombre, resultado_mod['mensajes']
                )
                plato_obj.nombre = nombre_actualizado
                
                return {
                    'exito': True,
                    'plato_resultado': plato_obj,
                    'mensajes': resultado_mod['mensajes'],
                    'estrategia': 'modificacion'
                }
            else:
                return {
                    'exito': False,
                    'mensajes': resultado_mod.get('mensajes', ['No se pudo modificar']),
                    'estrategia': 'ninguna'
                }
        
        except Exception as e:
            return {
                'exito': False,
                'mensajes': [f'Error en reparación: {str(e)}'],
                'estrategia': 'error'
            }