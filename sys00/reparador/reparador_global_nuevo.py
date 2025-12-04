import json
import os
from typing import List, Dict, Any, Optional
import sys

# Añadir el directorio padre al path para importar models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from conocimiento.models import Plato, Ingrediente, TipoRegla, Temporada, Sabor, Menu, Caso

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
        self.reglas_modificacion = self._cargar_reglas(archivo_reglas)
        self.casos_base = self._cargar_casos(archivo_casos)
        
        # Componentes especializados
        self.substitutor_platos = SubstitutorPlatos(self.casos_base)
        self.modificador_platos = ModificadorPlatos(self.reglas_modificacion)
    
    def _cargar_reglas(self, archivo: str) -> Dict[str, Any]:
        """Carga las reglas de modificación desde el archivo JSON"""
        try:
            ruta_archivo = os.path.join(os.path.dirname(__file__), '..', 'conocimiento', archivo)
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            return {}
    
    def _cargar_casos(self, archivo: str) -> List[Caso]:
        """Carga los casos base desde el archivo JSON"""
        try:
            ruta_archivo = os.path.join(os.path.dirname(__file__), '..', 'conocimiento', archivo)
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                # Convertir datos JSON a objetos Caso
                casos = []
                for caso_data in datos:
                    # Aquí se podría usar un deserializador más sofisticado
                    casos.append(caso_data)
                return casos
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as e:
            return []
    
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