"""
Gestor de platos - Detecta y agrega platos nuevos a la base
"""

from typing import List, Dict, Any, Set
from conocimiento import Menu


class GestorPlatos:
    """Gestiona la detección y agregación de platos nuevos"""
    
    def __init__(self, platos: List[Dict], platos_set: Set[str], persistencia=None):
        self.platos = platos
        self.platos_set = platos_set
        self.persistencia = persistencia
    
    def detectar_nuevos(self, menu: Menu) -> List[str]:
        """
        Detecta platos en el menú que no existen en la base.
        
        Args:
            menu: Objeto Menu con entrante, principal y postre
            
        Returns:
            Lista de nombres de platos nuevos
        """
        print(f"\nDETECTANDO PLATOS NUEVOS")
        
        platos_nuevos = [plato for plato in (menu.entrante, menu.principal, menu.postre) 
                         if plato and plato not in self.platos_set]
        
        if platos_nuevos:
            print(f"Platos nuevos detectados: {platos_nuevos}")
        else:
            print(f"Todos los platos ya existen en la base")
        
        return platos_nuevos
    
    def agregar(self, platos_nuevos: List[str], reparaciones_aplicadas: List[Any] = None) -> List[str]:
        """
        Agrega nuevos platos a la base.
        
        Si hay información de reparaciones con modificación, crea el plato copiando del plato base
        y aplicando las modificaciones. Las substituciones NO crean platos nuevos.
        
        Args:
            platos_nuevos: Lista de nombres de platos a agregar
            reparaciones_aplicadas: Lista de reparaciones aplicadas (opcional)
            
        Returns:
            Lista de platos agregados exitosamente
        """
        print(f"\nAGREGANDO PLATOS NUEVOS")
        
        # Crear índice de reparaciones por plato nuevo
        # Solo las modificaciones crean platos nuevos, las substituciones NO
        reparaciones_map = {}
        if reparaciones_aplicadas:
            for rep in reparaciones_aplicadas:
                accion = rep.get('accion')
                if accion == 'modificacion':
                    # Para modificación, el plato nuevo está en 'plato_nuevo'
                    plato_nuevo = rep.get('plato_nuevo')
                    if plato_nuevo:
                        reparaciones_map[plato_nuevo] = rep
        
        for plato_nombre in platos_nuevos:
            reparacion_info = reparaciones_map.get(plato_nombre)
            
            if reparacion_info:
                nuevo_plato = self._crear_con_modificaciones(plato_nombre, reparacion_info)
                print(f"Agregado: {plato_nombre} (basado en {reparacion_info['plato_original']} "
                      f"con {len(reparacion_info.get('modificaciones', []))} modificaciones)")
            else:
                nuevo_plato = self._crear_basico(plato_nombre)
                print(f"Agregado: {plato_nombre} - ADVERTENCIA: Requiere definición manual")
            
            self.platos.append(nuevo_plato)
            self.platos_set.add(plato_nombre)
        
        # Guardar inmediatamente si hay persistencia disponible
        if self.persistencia:
            self.persistencia.guardar_json('platos.json', self.platos)
            print(f"  ✓ Guardados {len(platos_nuevos)} platos en platos.json")
        
        return platos_nuevos
    
    def _crear_basico(self, nombre: str) -> Dict[str, Any]:
        """
        Crea una entrada básica de plato con información placeholder.
        Mantiene solo los campos que tienen los platos originales.
        
        Args:
            nombre: Nombre del plato
            
        Returns:
            Diccionario con definición básica del plato
        """
        return {
            'nombre': nombre,
            'ingredientes': [f'ingrediente_de_{nombre.lower().replace(" ", "_")}'],
            'tecnica_coccion': ['por_definir'],
            'sabor_dominante': 'salado',
            'ingrediente_sabor': f'ingrediente_de_{nombre.lower().replace(" ", "_")}'
        }
    
    def _crear_con_modificaciones(self, plato_nombre: str, reparacion: Dict) -> Dict[str, Any]:
        """
        Crea un nuevo plato copiando del plato base y aplicando modificaciones.
        
        Args:
            plato_nombre: Nombre del nuevo plato
            reparacion: Diccionario con información de la reparación
            
        Returns:
            Diccionario con la definición completa del nuevo plato
        """
        plato_original_nombre = reparacion['plato_original']
        modificaciones = reparacion.get('modificaciones', [])
        
        # Buscar plato original en la base
        plato_base = self._buscar_plato(plato_original_nombre)
        
        if not plato_base:
            # Si no encontramos el plato base, crear uno básico
            return self._crear_basico(plato_nombre)
        
        # Copiar estructura del plato base
        nuevo_plato = self._copiar_plato(plato_base, plato_nombre)
        
        # Aplicar modificaciones
        self._aplicar_modificaciones(nuevo_plato, modificaciones)
        
        return nuevo_plato
    
    def _buscar_plato(self, nombre: str) -> Dict[str, Any]:
        """Busca un plato por nombre en la base"""
        return next((plato.copy() for plato in self.platos if plato['nombre'] == nombre), None)
    
    def _copiar_plato(self, plato_base: Dict, nuevo_nombre: str) -> Dict[str, Any]:
        """Crea una copia del plato base con nuevo nombre"""
        nuevo_plato = {
            'nombre': nuevo_nombre,
            'ingredientes': plato_base.get('ingredientes', []).copy(),
            'tecnica_coccion': (plato_base.get('tecnica_coccion', ['por_definir']) 
                              if isinstance(plato_base.get('tecnica_coccion'), list)
                              else [plato_base.get('tecnica_coccion', 'por_definir')]),
            'sabor_dominante': plato_base.get('sabor_dominante', 'salado'),
            'ingrediente_sabor': plato_base.get('ingrediente_sabor', '')
        }
        
        # Solo copiar tradicion y temporada si existen en el plato base
        if 'tradicion' in plato_base:
            nuevo_plato['tradicion'] = plato_base['tradicion']
        if 'temporada' in plato_base:
            nuevo_plato['temporada'] = (plato_base['temporada'].copy() 
                                       if isinstance(plato_base['temporada'], list) 
                                       else [])
        
        return nuevo_plato
    
    def _aplicar_modificaciones(self, plato: Dict, modificaciones: List[str]) -> None:
        """
        Aplica las modificaciones documentadas al plato.
        
        Args:
            plato: Diccionario del plato a modificar (se modifica in-place)
            modificaciones: Lista de strings describiendo las modificaciones
        """
        ingredientes_substituidos = {}
        ingredientes_eliminados = set()
        
        for mod_str in map(str, modificaciones):
            if "Substituido" in mod_str and " por " in mod_str:
                self._aplicar_substitucion(plato, mod_str, ingredientes_substituidos)
            elif "Eliminado" in mod_str:
                self._aplicar_eliminacion(plato, mod_str, ingredientes_eliminados)
            elif "Añadido ingrediente" in mod_str:
                self._aplicar_adicion(plato, mod_str)
        
        # Actualizar ingrediente_sabor si fue modificado
        self._actualizar_ingrediente_sabor(plato, ingredientes_substituidos, ingredientes_eliminados)
    
    def _aplicar_substitucion(self, plato: Dict, mod_str: str, 
                            ingredientes_substituidos: Dict) -> None:
        """Aplica una substitución de ingrediente"""
        partes = mod_str.split(" por ", 1)
        if len(partes) == 2:
            ing_viejo = partes[0].replace("Substituido", "").strip()
            ing_nuevo = partes[1].strip()
            
            if ing_viejo in plato['ingredientes']:
                plato['ingredientes'][plato['ingredientes'].index(ing_viejo)] = ing_nuevo
                ingredientes_substituidos[ing_viejo] = ing_nuevo
                print(f"    → Substituido: {ing_viejo} → {ing_nuevo}")
    
    def _aplicar_eliminacion(self, plato: Dict, mod_str: str, 
                           ingredientes_eliminados: Set) -> None:
        """Aplica una eliminación de ingrediente"""
        ing_eliminado = mod_str.replace("Eliminado ingrediente", "").replace("Eliminado", "").strip()
        if ing_eliminado in plato['ingredientes']:
            plato['ingredientes'].remove(ing_eliminado)
            ingredientes_eliminados.add(ing_eliminado)
            print(f"    → Eliminado: {ing_eliminado}")
    
    def _aplicar_adicion(self, plato: Dict, mod_str: str) -> None:
        """Aplica una adición de ingrediente"""
        ing_añadido = mod_str.replace("Añadido ingrediente", "").strip()
        if ing_añadido and ing_añadido not in plato['ingredientes']:
            plato['ingredientes'].append(ing_añadido)
            print(f"    → Añadido: {ing_añadido}")
    
    def _actualizar_ingrediente_sabor(self, plato: Dict, 
                                     ingredientes_substituidos: Dict,
                                     ingredientes_eliminados: Set) -> None:
        """
        Actualiza el ingrediente_sabor si fue modificado o ya no existe en la lista.
        
        Casos manejados:
        1. Ingrediente_sabor fue substituido → usa el nuevo ingrediente
        2. Ingrediente_sabor fue eliminado → usa el primer ingrediente disponible
        3. Ingrediente_sabor ya no existe en la lista → usa el primer ingrediente disponible
        """
        ingrediente_sabor_original = plato['ingrediente_sabor']
        
        # Caso 1: El ingrediente_sabor fue substituido
        if ingrediente_sabor_original in ingredientes_substituidos:
            plato['ingrediente_sabor'] = ingredientes_substituidos[ingrediente_sabor_original]
            print(f"    → Actualizado ingrediente_sabor: {ingrediente_sabor_original} → {plato['ingrediente_sabor']}")
            return
        
        # Caso 2 y 3: El ingrediente_sabor fue eliminado o no está en la lista
        if ingrediente_sabor_original in ingredientes_eliminados or \
           ingrediente_sabor_original not in plato['ingredientes']:
            
            # Usar el primer ingrediente de la lista como nuevo ingrediente_sabor
            if plato['ingredientes']:
                nuevo_ingrediente_sabor = plato['ingredientes'][0]
                plato['ingrediente_sabor'] = nuevo_ingrediente_sabor
                print(f"    → Nuevo ingrediente_sabor: {ingrediente_sabor_original} → {nuevo_ingrediente_sabor}")
            else:
                # Si no quedan ingredientes, dejar vacío y cambiar sabor a neutro
                plato['ingrediente_sabor'] = ''
                plato['sabor_dominante'] = 'neutro'
                print(f"    → ⚠ Sin ingredientes - ingrediente_sabor eliminado, sabor: neutro")
