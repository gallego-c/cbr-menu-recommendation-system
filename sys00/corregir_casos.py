#!/usr/bin/env python3
"""
Script para corregir casos que violan restricciones.
Reemplaza platos que no cumplen con las restricciones del caso.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Set

class CorrectorCasos:
    """Corrige casos con violaciones de restricciones."""
    
    def __init__(self, conocimiento_dir: str = 'conocimiento'):
        self.conocimiento_dir = Path(conocimiento_dir)
        
        # Cargar datos
        self.casos = self._cargar_json('casos.json')
        self.platos = self._cargar_json('platos.json')
        self.ingredientes = self._cargar_json('ingredientes.json')
        self.restricciones = self._cargar_json('restricciones.json')
        
        # Índices
        self.platos_por_nombre = {p['nombre']: p for p in self.platos}
        self.ingredientes_por_nombre = {ing['nombre']: ing for ing in self.ingredientes}
        
        self.casos_corregidos = []
        self.casos_eliminados = []
    
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
                ing_data = next((ing for ing in self.ingredientes if ing['nombre'] == ing_nombre), None)
                if ing_data and ing_data.get('categoria') in categorias_prohibidas:
                    return False
        
        return True
    
    def _buscar_plato_valido(self, restricciones: List[str], tipo_plato: str = None) -> str:
        """Busca un plato que cumpla las restricciones."""
        platos_validos = [
            p['nombre'] for p in self.platos
            if self._plato_cumple_restricciones(p['nombre'], restricciones)
        ]
        
        if not platos_validos:
            return None
        
        return random.choice(platos_validos)
    
    def corregir_casos(self):
        """Corrige todos los casos con violaciones."""
        print("🔧 Corrigiendo casos con violaciones de restricciones...")
        
        casos_validos = []
        
        for caso in self.casos:
            caso_id = caso['id']
            restricciones = caso.get('restricciones', [])
            
            if not restricciones:
                casos_validos.append(caso)
                continue
            
            menu = caso.get('menu', {})
            menu_original = dict(menu)
            necesita_correccion = False
            
            # Verificar cada plato del menú
            for tipo_plato, nombre_plato in list(menu.items()):
                if not self._plato_cumple_restricciones(nombre_plato, restricciones):
                    # Buscar reemplazo
                    plato_nuevo = self._buscar_plato_valido(restricciones, tipo_plato)
                    
                    if plato_nuevo:
                        print(f"  ✓ {caso_id}: Reemplazando '{nombre_plato[:40]}' → '{plato_nuevo[:40]}'")
                        menu[tipo_plato] = plato_nuevo
                        necesita_correccion = True
                    else:
                        print(f"  ⚠️  {caso_id}: No se encontró reemplazo para '{nombre_plato[:40]}', eliminando caso")
                        self.casos_eliminados.append(caso_id)
                        necesita_correccion = None
                        break
            
            if necesita_correccion is None:
                # Caso eliminado
                continue
            elif necesita_correccion:
                self.casos_corregidos.append(caso_id)
                casos_validos.append(caso)
            else:
                casos_validos.append(caso)
        
        # Guardar casos corregidos
        self._guardar_json('casos.json', casos_validos)
        
        print(f"\n✅ Corrección completada:")
        print(f"  - Casos corregidos: {len(self.casos_corregidos)}")
        print(f"  - Casos eliminados: {len(self.casos_eliminados)}")
        print(f"  - Casos totales: {len(casos_validos)}")
        
        return casos_validos


def main():
    """Función principal."""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║       CORRECTOR DE CASOS - SBC-sys-cbr                       ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    corrector = CorrectorCasos()
    casos_corregidos = corrector.corregir_casos()
    
    if corrector.casos_eliminados:
        print(f"\n⚠️  Casos eliminados: {', '.join(corrector.casos_eliminados)}")
    
    print("\n🎯 Ejecuta 'python3 validacion_semantica.py' para re-validar")


if __name__ == '__main__':
    random.seed(42)
    main()
