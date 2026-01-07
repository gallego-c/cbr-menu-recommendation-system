#!/usr/bin/env python3
"""
Corrector de coherencia cultural y estilo.
Reemplaza platos que no coinciden con la tradición del caso.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Set


class CorrectorCoherencia:
    """Corrige casos con problemas de coherencia cultural."""
    
    def __init__(self, conocimiento_dir: str = 'conocimiento'):
        self.conocimiento_dir = Path(conocimiento_dir)
        
        self.casos = self._cargar_json('casos.json')
        self.platos = self._cargar_json('platos.json')
        self.ingredientes = self._cargar_json('ingredientes.json')
        self.restricciones = self._cargar_json('restricciones.json')
        
        self.platos_por_nombre = {p['nombre']: p for p in self.platos}
        self.ingredientes_por_nombre = {ing['nombre']: ing for ing in self.ingredientes}
        
        # Índice: platos por tradición
        self.platos_por_tradicion = {}
        for tradicion in ['catalana', 'italiana', 'francesa', 'mexicana', 'china', 'mediterranea', 'india']:
            self.platos_por_tradicion[tradicion] = self._filtrar_platos_por_tradicion(tradicion)
        
        self.casos_corregidos = []
    
    def _cargar_json(self, filename: str) -> List[Dict]:
        """Carga archivo JSON."""
        path = self.conocimiento_dir / filename
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _guardar_json(self, filename: str, data: List[Dict]):
        """Guarda archivo JSON."""
        path = self.conocimiento_dir / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _filtrar_platos_por_tradicion(self, tradicion: str) -> List[str]:
        """Filtra platos que pertenecen a una tradición específica por nombre."""
        indicadores = {
            'italiana': ['italian', 'pasta', 'pizza', 'risotto', 'gnocchi', 'tiramisu', 'bruschetta', 
                        'parmigiano', 'mozzarella', 'focaccia', 'cannelloni', 'linguine', 'penne',
                        'spaghetti', 'lasagna', 'ravioli', 'pesto', 'pomodoro', 'basilico', 'biscotti',
                        'salsa pomodoro', 'italiana', 'italiano'],
            'francesa': ['french', 'crème', 'soufflé', 'croissant', 'baguette', 'ratatouille',
                        'bouillabaisse', 'coq au vin', 'cassoulet', 'crêpe', 'fenouil', 'salade',
                        'provence', 'pâtissière', 'gratin', 'française', 'francés', 'foie gras'],
            'mexicana': ['mexican', 'taco', 'burrito', 'enchilada', 'quesadilla', 'guacamole',
                        'salsa', 'chile', 'jalapeño', 'chipotle', 'mole', 'tortilla', 'frijoles',
                        'pico de gallo', 'carnitas', 'al pastor', 'pozole', 'tamales', 'mexicana',
                        'mexicano'],
            'china': ['chinese', 'wok', 'noodle', 'dim sum', 'stir fry', 'fried rice', 'chow mein',
                     'lo mein', 'kung pao', 'szechuan', 'beijing', 'peking', 'canton', 'shanghai',
                     'soy', 'sesame', 'ginger', 'shiitake', 'bok choy', 'china', 'chino', 'chino',
                     'wafu', 'sukiyaki'],
            'catalana': ['catalan', 'escalivada', 'pa amb tomaquet', 'butifarra', 'suquet',
                        'cannelloni catalana', 'crema catalana', 'fideuà', 'coca', 'mel i mató',
                        'catalana', 'catalán'],
            'mediterranea': ['mediterranean', 'olive', 'feta', 'hummus', 'tabbouleh', 'greek',
                           'greco', 'libanés', 'turco', 'mediterránea', 'mediterranean'],
            'india': ['indian', 'curry', 'masala', 'tandoori', 'biryani', 'naan', 'chapati',
                     'dal', 'paneer', 'samosa', 'pakora', 'tikka', 'garam', 'vindaloo', 'korma',
                     'roti', 'urad', 'fenugreek', 'india', 'indio', 'sabzi'],
        }
        
        palabras_clave = indicadores.get(tradicion, [])
        platos_tradicion = []
        
        for plato in self.platos:
            nombre_lower = plato['nombre'].lower()
            
            # Buscar indicadores
            for palabra in palabras_clave:
                if palabra in nombre_lower:
                    platos_tradicion.append(plato['nombre'])
                    break
        
        # Si es mediterranea, incluir también algunos italianos y catalanes
        if tradicion == 'mediterranea':
            platos_tradicion.extend(self._filtrar_platos_por_tradicion('italiana')[:20])
            platos_tradicion.extend(self._filtrar_platos_por_tradicion('catalana')[:10])
        
        # Remover duplicados
        return list(set(platos_tradicion))
    
    def _plato_cumple_restricciones(self, plato_nombre: str, restricciones: List[str]) -> bool:
        """Verifica si un plato cumple todas las restricciones."""
        if not restricciones:
            return True
        
        plato = self.platos_por_nombre.get(plato_nombre)
        if not plato:
            return False
        
        ingredientes_plato = set(plato.get('ingredientes', []))
        
        for restriccion_nombre in restricciones:
            restriccion = next((r for r in self.restricciones if r['nombre'] == restriccion_nombre), None)
            if not restriccion:
                continue
            
            # Ingredientes prohibidos
            prohibidos = set(restriccion.get('ingredientes_prohibidos', []))
            if ingredientes_plato & prohibidos:
                return False
            
            # Categorías prohibidas
            categorias_prohibidas = set(restriccion.get('categorias_prohibidas', []))
            for ing_nombre in ingredientes_plato:
                ing_data = self.ingredientes_por_nombre.get(ing_nombre)
                if ing_data and ing_data.get('categoria') in categorias_prohibidas:
                    return False
        
        return True
    
    def _buscar_plato_compatible(self, tradicion: str, restricciones: List[str]) -> str:
        """Busca un plato de la tradición correcta que cumpla restricciones."""
        platos_tradicion = self.platos_por_tradicion.get(tradicion, [])
        
        # Filtrar por restricciones
        platos_validos = [
            p for p in platos_tradicion
            if self._plato_cumple_restricciones(p, restricciones)
        ]
        
        if platos_validos:
            return random.choice(platos_validos)
        
        # Fallback: sin restricciones
        if platos_tradicion:
            return random.choice(platos_tradicion)
        
        return None
    
    def corregir_coherencia_cultural(self):
        """Corrige todos los casos con problemas culturales."""
        print("🔧 Corrigiendo coherencia cultural...")
        
        indicadores_culturales = {
            'italiana': ['italian', 'pasta', 'pizza', 'risotto', 'gnocchi', 'pesto', 'pomodoro', 
                        'linguine', 'spaghetti', 'bruschetta', 'biscotti', 'salsa', 'italiana'],
            'francesa': ['french', 'crème', 'salade', 'fenouil', 'provence', 'foie gras', 'française'],
            'mexicana': ['mexican', 'taco', 'burrito', 'enchilada', 'guacamole', 'chile', 'salsa',
                        'pico de gallo', 'tortilla', 'mexicana'],
            'china': ['chinese', 'wok', 'stir fry', 'chow mein', 'lo mein', 'ginger', 'shiitake',
                     'sesame', 'soy', 'china', 'chino', 'wafu', 'sukiyaki'],
            'catalana': ['catalan', 'escalivada', 'pa amb tomaquet', 'butifarra', 'crema catalana',
                        'fideuà', 'coca', 'mel i mató', 'catalana'],
            'mediterranea': ['mediterranean', 'olive', 'feta', 'greek', 'mediterránea'],
            'india': ['indian', 'curry', 'masala', 'tandoori', 'naan', 'dal', 'garam', 'roti',
                     'fenugreek', 'sabzi', 'india'],
        }
        
        for caso in self.casos:
            caso_id = caso['id']
            tradicion_caso = caso.get('tradicion', '')
            restricciones = caso.get('restricciones', [])
            menu = caso.get('menu', {})
            
            modificado = False
            
            for tipo_plato, nombre_plato in list(menu.items()):
                nombre_lower = nombre_plato.lower()
                
                # Detectar tradición del plato
                tradiciones_plato = set()
                for trad, palabras in indicadores_culturales.items():
                    for palabra in palabras:
                        if palabra in nombre_lower:
                            tradiciones_plato.add(trad)
                            break
                
                # Si tiene tradición clara y NO coincide
                if tradiciones_plato and tradicion_caso not in tradiciones_plato:
                    # Permitir excepciones mediterranea <-> italiana/catalana
                    if tradicion_caso == 'mediterranea' and any(t in ['italiana', 'catalana'] for t in tradiciones_plato):
                        continue
                    if tradicion_caso in ['italiana', 'catalana'] and 'mediterranea' in tradiciones_plato:
                        continue
                    
                    # Buscar reemplazo
                    plato_nuevo = self._buscar_plato_compatible(tradicion_caso, restricciones)
                    
                    if plato_nuevo and plato_nuevo != nombre_plato:
                        print(f"  ✓ {caso_id} ({tradicion_caso}): '{nombre_plato[:40]}' → '{plato_nuevo[:40]}'")
                        menu[tipo_plato] = plato_nuevo
                        modificado = True
            
            if modificado:
                self.casos_corregidos.append(caso_id)
        
        # Guardar casos corregidos
        self._guardar_json('casos.json', self.casos)
        
        print(f"\n✅ Casos corregidos: {len(self.casos_corregidos)}")
        print(f"   IDs: {', '.join(self.casos_corregidos[:30])}")
        if len(self.casos_corregidos) > 30:
            print(f"   ... y {len(self.casos_corregidos) - 30} más")


def main():
    """Función principal."""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║       CORRECTOR DE COHERENCIA CULTURAL - SBC-sys-cbr        ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    corrector = CorrectorCoherencia()
    corrector.corregir_coherencia_cultural()
    
    print("\n🎯 Ejecuta 'python3 validacion_coherencia_profunda.py' para re-validar")


if __name__ == '__main__':
    random.seed(42)
    main()
