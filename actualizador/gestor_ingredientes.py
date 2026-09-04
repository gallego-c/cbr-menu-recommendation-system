"""
Gestor de ingredientes - Detecta y agrega ingredientes nuevos a la base
"""

from typing import List, Dict, Any, Optional, Set


class GestorIngredientes:
    """Gestiona la detección y agregación de ingredientes nuevos"""
    
    def __init__(self, ingredientes: List[Dict], ingredientes_set: Set[str]):
        self.ingredientes = ingredientes
        self.ingredientes_set = ingredientes_set
    
    def detectar_nuevos(self, menu: Dict[str, Any]) -> List[str]:
        """
        Detecta ingredientes en el menú que no existen en la base.
        
        Args:
            menu: Menú a analizar
            
        Returns:
            Lista de nombres de ingredientes nuevos
        """
        print(f"\nDETECTANDO INGREDIENTES NUEVOS")
        
        # Extraer todos los ingredientes del menú
        # Nota: Asume que menu tiene acceso a los platos y sus ingredientes
        ingredientes_menu = []
        
        # Por ahora, no podemos extraer ingredientes del menú directamente
        # ya que solo tenemos nombres de platos
        # Esta funcionalidad requeriría acceso a la base de platos
        
        ingredientes_nuevos = []
        for ingrediente in set(ingredientes_menu):
            if ingrediente not in self.ingredientes_set:
                ingredientes_nuevos.append(ingrediente)
        
        if ingredientes_nuevos:
            print(f"Ingredientes nuevos detectados: {ingredientes_nuevos}")
        else:
            print(f"Todos los ingredientes ya existen en la base")
        
        return ingredientes_nuevos
    
    def agregar(self, ingredientes_nuevos: List[str]) -> List[str]:
        """
        Agrega nuevos ingredientes a la base con información inferida.
        
        Args:
            ingredientes_nuevos: Lista de nombres de ingredientes a agregar
            
        Returns:
            Lista de ingredientes agregados exitosamente
        """
        print(f"\nAGREGANDO INGREDIENTES NUEVOS")
        
        agregados = []
        
        for ingrediente_nombre in ingredientes_nuevos:
            nuevo_ingrediente = self._generar_info(ingrediente_nombre)
            
            if nuevo_ingrediente:
                self.ingredientes.append(nuevo_ingrediente)
                self.ingredientes_set.add(ingrediente_nombre)
                agregados.append(ingrediente_nombre)
                
                print(f"Agregado: {ingrediente_nombre}")
                print(f"  - Categoria: {nuevo_ingrediente['categoria']}")
                print(f"  - Temporada: {nuevo_ingrediente['temporada']}")
                print(f"  - Sabor: {nuevo_ingrediente['sabor']}")
        
        return agregados
    
    def _generar_info(self, nombre: str) -> Optional[Dict[str, Any]]:
        """
        Genera información básica para un nuevo ingrediente.
        Usa patrones y heurísticas para inferir categoría, temporada, etc.
        
        Args:
            nombre: Nombre del ingrediente
            
        Returns:
            Diccionario con la información del ingrediente o None si falla
        """
        # Patrones para categorizar ingredientes
        categorias_comunes = {
            'vegetal': ['tomate', 'cebolla', 'ajo', 'pimiento', 'pepino', 'lechuga', 
                       'espinaca', 'brócoli', 'calabaza', 'berenjena'],
            'fruta': ['manzana', 'naranja', 'limón', 'fresa', 'plátano', 'uva', 
                     'melón', 'sandía', 'melocotón', 'pera'],
            'animal': ['pollo', 'ternera', 'cerdo', 'pescado', 'atún', 'salmón', 
                      'huevo', 'cordero', 'pato'],
            'lacteo': ['leche', 'queso', 'yogur', 'mantequilla', 'nata', 'mozzarella', 
                      'parmesano', 'requesón'],
            'cereal': ['arroz', 'trigo', 'avena', 'quinoa', 'pasta', 'pan', 'cebada'],
            'condimento': ['sal', 'pimienta', 'azúcar', 'aceite', 'vinagre', 'canela'],
            'hongo': ['setas', 'champiñón', 'shiitake', 'portobello'],
            'leguminosa': ['lentejas', 'garbanzos', 'judías', 'guisantes', 'alubias']
        }
        
        sabores_comunes = {
            'salado': ['sal', 'queso', 'jamón', 'anchoa', 'bacon'],
            'dulce': ['azúcar', 'miel', 'fruta', 'chocolate', 'canela'],
            'ácido': ['limón', 'vinagre', 'tomate', 'naranja'],
            'amargo': ['café', 'cacao', 'rúcula', 'endibia'],
            'umami': ['setas', 'queso', 'tomate', 'soja']
        }
        
        # Inferir categoría
        categoria = 'vegetal'  # por defecto
        for cat, palabras in categorias_comunes.items():
            if any(palabra in nombre.lower() for palabra in palabras):
                categoria = cat
                break
        
        # Inferir sabor
        sabor = 'salado'  # por defecto
        for sab, palabras in sabores_comunes.items():
            if any(palabra in nombre.lower() for palabra in palabras):
                sabor = sab
                break
        
        # Temporadas por defecto (disponible todo el año)
        temporada = ['primavera', 'verano', 'otoño', 'invierno']
        
        return {
            'nombre': nombre,
            'categoria': categoria,
            'temporada': temporada,
            'sabor': sabor,
            'tradicion': ['general']
        }
