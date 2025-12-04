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


class Reparador:
    """
    Clase principal del reparador que decide entre substituir plato completo 
    o modificar plato actual según las preferencias del menú
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
        
        # Componentes especializados
        self.substitutor_platos = SubstitutorPlatos(self.casos_base)
        self.modificador_platos = ModificadorPlatos(self.reglas_modificacion)
    
    def reparar_plato(self, plato_problematico: Plato, menu: Menu, 
                     tipo_problema: str, problema_especifico: str) -> Dict[str, Any]:
        """
        Método principal para reparar un plato problemático
        
        Args:
            plato_problematico: El plato que necesita ser reparado
            menu: El menú completo con todas las preferencias
            tipo_problema: Tipo de problema (restricciones, temporada, sabor, etc.)
            problema_especifico: Descripción específica del problema
            
        Returns:
            Diccionario con el resultado de la reparación:
            {
                'estrategia': 'substitucion' | 'modificacion',
                'plato_resultado': Plato,
                'mensajes': List[str],
                'exito': bool
            }
        """
        
        # 1. Intentar substitución completa del plato
        resultado_substitucion = self.substitutor_platos.buscar_plato_substitucion(
            plato_problematico, menu, tipo_problema, problema_especifico
        )
        
        if resultado_substitucion['exito']:
            return {
                'estrategia': 'substitucion',
                'plato_resultado': resultado_substitucion['plato_substitucion'],
                'mensajes': [f"Plato substituido por: {resultado_substitucion['plato_substitucion'].nombre}"] +
                           resultado_substitucion['mensajes'],
                'exito': True
            }
        
        # 2. Si no se puede substituir, intentar modificación
        resultado_modificacion = self.modificador_platos.aplicar_modificaciones(
            plato_problematico, tipo_problema, problema_especifico
        )
        
        return {
            'estrategia': 'modificacion',
            'plato_resultado': resultado_modificacion['plato_modificado'],
            'mensajes': resultado_modificacion['mensajes'],
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
            Dict con 'exito', 'plato_modificado', 'mensajes', 'modificaciones'
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
            
            # Crear objeto Menu
            menu_obj = Menu(
                entrante=menu_dict.get('entrante', ''),
                principal=menu_dict.get('principal', ''),
                postre=menu_dict.get('postre', '')
            )
            
            # Llamar al reparador principal
            resultado = self.reparar_plato(plato_obj, menu_obj, tipo_problema, problema_especifico)
            
            if resultado['exito']:
                plato_resultado = resultado['plato_resultado']
                
                # Preparar respuesta compatible con sistema_cbr
                return {
                    'exito': True,
                    'plato_modificado': plato_resultado.nombre,
                    'mensajes': resultado['mensajes'],
                    'modificaciones': resultado['mensajes'],  # Alias para compatibilidad
                    'estrategia': resultado['estrategia']
                }
            else:
                return {
                    'exito': False,
                    'mensajes': resultado.get('mensajes', ['Reparación falló'])
                }
                
        except Exception as e:
            return {
                'exito': False,
                'mensajes': [f'Error en reparación: {str(e)}']
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
    
    def reparar_por_nombre(self, plato_nombre: str, tipo_problema: str,
                          problema_especifico: str, preferencias: Dict) -> Dict[str, Any]:
        """
        Método público para reparar un plato usando solo su nombre.
        Esta es la interfaz principal que debe usar sistema_cbr.
        
        Args:
            plato_nombre: Nombre del plato a reparar
            tipo_problema: Tipo de problema (restricciones, temporada, etc.)
            problema_especifico: Descripción del problema
            preferencias: Diccionario con preferencias del usuario
            
        Returns:
            Dict con 'exito', 'plato_resultado' (nombre), 'mensajes', 'estrategia'
        """
        try:
            from conocimiento import cargador
            
            # Cargar plato desde la base de datos
            platos_db = cargador.cargar_platos()
            
            # Buscar el plato
            if isinstance(platos_db, dict):
                plato_info = platos_db.get(plato_nombre)
            else:
                plato_info = next((p for p in platos_db if p.get('nombre') == plato_nombre), None)
            
            if not plato_info:
                return {
                    'exito': False,
                    'mensajes': [f'Plato {plato_nombre} no encontrado'],
                    'estrategia': 'ninguna'
                }
            
            # ESTRATEGIA 1: Intentar substitución (no requiere objetos complejos)
            # Buscar alternativa simple usando el substitutor
            tipo_plato = plato_info.get('tipo', 'principal')
            plato_alternativo = self.substitutor_platos.buscar_alternativa_simple(
                plato_nombre, preferencias, tipo_plato
            )
            
            if plato_alternativo:
                return {
                    'exito': True,
                    'plato_resultado': plato_alternativo,
                    'mensajes': [f'Plato substituido por {plato_alternativo}'],
                    'estrategia': 'substitucion'
                }
            
            # ESTRATEGIA 2: Modificación de ingredientes
            # Crear objeto Plato desde la información cargada
            plato_obj = Plato.from_dict(plato_info)
            
            # Aplicar modificaciones usando el modificador
            resultado_mod = self.modificador_platos.aplicar_modificaciones(
                plato_obj, tipo_problema, problema_especifico
            )
            
            if resultado_mod['exito']:
                # Generar nombre descriptivo para el plato modificado y actualizar el objeto
                nombre_modificado = self.generar_nombre_plato_modificado(
                    plato_nombre, resultado_mod['mensajes']
                )
                plato_obj.nombre = nombre_modificado
                return {
                    'exito': True,
                    'plato_resultado': plato_obj,  # Devolver objeto Plato, no string
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
    
    def reparar_plato_objeto(self, plato_obj: Plato, tipo_problema: str,
                            problema_especifico: str, preferencias: Dict) -> Dict[str, Any]:
        """
        Repara un objeto Plato que ya está en memoria (útil para reparaciones múltiples).
        No busca en la base de datos, trabaja directamente con el objeto proporcionado.
        
        Args:
            plato_obj: Objeto Plato a reparar (se modifica in-place)
            tipo_problema: Tipo de problema (restricciones, temporada, etc.)
            problema_especifico: Descripción del problema
            preferencias: Diccionario con preferencias del usuario
            
        Returns:
            Dict con 'exito', 'plato_resultado' (objeto Plato), 'mensajes', 'estrategia'
        """
        try:
            # Aplicar modificaciones usando el modificador
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