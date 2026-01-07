#!/usr/bin/env python3
"""
Validación profunda de coherencia cultural y estilo culinario.
Detecta casos donde los platos NO coinciden con la tradición o estilo del caso.
"""

import json
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict


class ValidadorCoherenciaProfunda:
    """Validador de coherencia cultural y estilo."""
    
    def __init__(self, conocimiento_dir: str = 'conocimiento'):
        self.conocimiento_dir = Path(conocimiento_dir)
        
        self.casos = self._cargar_json('casos.json')
        self.platos = self._cargar_json('platos.json')
        self.ingredientes = self._cargar_json('ingredientes.json')
        self.restricciones = self._cargar_json('restricciones.json')
        
        self.platos_por_nombre = {p['nombre']: p for p in self.platos}
        self.ingredientes_por_nombre = {ing['nombre']: ing for ing in self.ingredientes}
        
        self.errores_criticos = []
        self.warnings = []
        
        # Indicadores culturales en nombres de platos
        self.indicadores_culturales = {
            'italiana': ['italian', 'pasta', 'pizza', 'risotto', 'gnocchi', 'tiramisu', 'bruschetta', 
                        'parmigiano', 'mozzarella', 'focaccia', 'cannelloni', 'linguine', 'penne',
                        'spaghetti', 'lasagna', 'ravioli', 'pesto', 'pomodoro', 'basilico', 'salsa'],
            'francesa': ['french', 'crème', 'soufflé', 'croissant', 'baguette', 'ratatouille',
                        'bouillabaisse', 'coq au vin', 'cassoulet', 'crêpe', 'fenouil', 'salade',
                        'provence', 'pâtissière', 'gratin'],
            'mexicana': ['mexican', 'taco', 'burrito', 'enchilada', 'quesadilla', 'guacamole',
                        'salsa', 'chile', 'jalapeño', 'chipotle', 'mole', 'tortilla', 'frijoles',
                        'pico de gallo', 'carnitas', 'al pastor', 'pozole', 'tamales'],
            'china': ['chinese', 'wok', 'noodle', 'dim sum', 'stir fry', 'fried rice', 'chow mein',
                     'lo mein', 'kung pao', 'szechuan', 'beijing', 'peking', 'canton', 'shanghai',
                     'soy sauce', 'sesame', 'ginger', 'shiitake', 'bok choy'],
            'catalana': ['catalan', 'escalivada', 'pa amb tomaquet', 'butifarra', 'suquet',
                        'cannelloni catalana', 'crema catalana', 'fideuà', 'coca', 'mel i mató'],
            'mediterranea': ['mediterranean', 'olive', 'feta', 'hummus', 'tabbouleh', 'greek',
                           'mediterranean', 'greco', 'libanés', 'turco'],
            'india': ['indian', 'curry', 'masala', 'tandoori', 'biryani', 'naan', 'chapati',
                     'dal', 'paneer', 'samosa', 'pakora', 'tikka', 'garam', 'vindaloo', 'korma',
                     'roti', 'urad'],
        }
        
        # Técnicas culinarias por estilo
        self.tecnicas_por_estilo = {
            'molecular': ['esferificacion', 'gelificacion', 'emulsion', 'espuma', 'nitrogen'],
            'clasico': ['horneado', 'hervido', 'asado', 'guisado', 'salteado', 'frito'],
            'gourmet': ['sous vide', 'flambeado', 'reduccion', 'confitado', 'asado'],
            'comfort_food': ['frito', 'guisado', 'horneado', 'hervido'],
            'picante': ['salteado', 'frito', 'asado', 'guisado'],
            'fusion': ['cualquiera'],  # Permite cualquier técnica
            'saludable': ['al_vapor', 'hervido', 'salteado', 'crudo', 'horneado'],
        }
    
    def _cargar_json(self, filename: str) -> List[Dict]:
        """Carga archivo JSON."""
        path = self.conocimiento_dir / filename
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _error(self, mensaje: str):
        """Registra error crítico."""
        self.errores_criticos.append(f"❌ {mensaje}")
    
    def _warning(self, mensaje: str):
        """Registra warning."""
        self.warnings.append(f"⚠️  {mensaje}")
    
    def _detectar_tradicion_plato(self, nombre_plato: str) -> Set[str]:
        """Detecta la tradición cultural de un plato por su nombre."""
        nombre_lower = nombre_plato.lower()
        tradiciones_detectadas = set()
        
        for tradicion, palabras_clave in self.indicadores_culturales.items():
            for palabra in palabras_clave:
                if palabra in nombre_lower:
                    tradiciones_detectadas.add(tradicion)
                    break
        
        return tradiciones_detectadas
    
    def _plato_cumple_restricciones(self, plato_nombre: str, restricciones: List[str]) -> tuple:
        """Verifica si un plato cumple restricciones. Retorna (cumple: bool, violaciones: list)."""
        if not restricciones:
            return (True, [])
        
        plato = self.platos_por_nombre.get(plato_nombre)
        if not plato:
            return (True, [])
        
        ingredientes_plato = set(plato.get('ingredientes', []))
        violaciones = []
        
        for restriccion_nombre in restricciones:
            restriccion = next((r for r in self.restricciones if r['nombre'] == restriccion_nombre), None)
            if not restriccion:
                continue
            
            # Ingredientes prohibidos
            prohibidos = set(restriccion.get('ingredientes_prohibidos', []))
            conflicto_ing = ingredientes_plato & prohibidos
            if conflicto_ing:
                violaciones.append(f"ingredientes prohibidos: {list(conflicto_ing)[:3]}")
            
            # Categorías prohibidas
            categorias_prohibidas = set(restriccion.get('categorias_prohibidas', []))
            for ing_nombre in ingredientes_plato:
                ing_data = self.ingredientes_por_nombre.get(ing_nombre)
                if ing_data and ing_data.get('categoria') in categorias_prohibidas:
                    violaciones.append(f"ingrediente '{ing_nombre}' es categoría prohibida '{ing_data.get('categoria')}'")
        
        return (len(violaciones) == 0, violaciones)
    
    def validar_coherencia_cultural_estricta(self):
        """Valida que cada plato sea coherente con la tradición del caso."""
        print("🔍 Validando coherencia cultural estricta...")
        
        casos_problematicos = []
        
        for caso in self.casos:
            caso_id = caso['id']
            tradicion_caso = caso.get('tradicion', '')
            menu = caso.get('menu', {})
            
            for tipo_plato, nombre_plato in menu.items():
                tradiciones_plato = self._detectar_tradicion_plato(nombre_plato)
                
                # Si el plato tiene indicadores culturales claros
                if tradiciones_plato:
                    # Verificar si coincide con la tradición del caso
                    if tradicion_caso not in tradiciones_plato:
                        # Permitir mediterranea <-> italiana, catalana
                        if not (tradicion_caso == 'mediterranea' and any(t in ['italiana', 'catalana'] for t in tradiciones_plato)):
                            if not (tradicion_caso in ['italiana', 'catalana'] and 'mediterranea' in tradiciones_plato):
                                self._error(f"Caso {caso_id} ({tradicion_caso}): Plato '{nombre_plato[:50]}' pertenece a {tradiciones_plato}")
                                casos_problematicos.append(caso_id)
        
        print(f"  {'✓' if not casos_problematicos else '✗'} Casos problemáticos: {len(set(casos_problematicos))}")
        return list(set(casos_problematicos))
    
    def validar_restricciones_alimentarias(self):
        """Valida que todos los platos cumplan las restricciones."""
        print("🔍 Validando restricciones alimentarias...")
        
        casos_con_violaciones = []
        
        for caso in self.casos:
            caso_id = caso['id']
            restricciones = caso.get('restricciones', [])
            
            if not restricciones:
                continue
            
            menu = caso.get('menu', {})
            
            for tipo_plato, nombre_plato in menu.items():
                cumple, violaciones = self._plato_cumple_restricciones(nombre_plato, restricciones)
                
                if not cumple:
                    self._error(f"Caso {caso_id} ({', '.join(restricciones)}): Plato '{nombre_plato[:50]}' viola: {violaciones[0]}")
                    casos_con_violaciones.append(caso_id)
        
        print(f"  {'✓' if not casos_con_violaciones else '✗'} Violaciones encontradas: {len(casos_con_violaciones)}")
        return casos_con_violaciones
    
    def validar_coherencia_estilo(self):
        """Valida que las técnicas de cocción sean apropiadas para el estilo."""
        print("🔍 Validando coherencia de estilo culinario...")
        
        casos_problematicos = []
        
        for caso in self.casos:
            caso_id = caso['id']
            estilo_caso = caso.get('estilo', '')
            
            if estilo_caso == 'fusion':
                continue  # Fusion permite cualquier combinación
            
            menu = caso.get('menu', {})
            
            tecnicas_esperadas = self.tecnicas_por_estilo.get(estilo_caso, [])
            if not tecnicas_esperadas or tecnicas_esperadas == ['cualquiera']:
                continue
            
            for tipo_plato, nombre_plato in menu.items():
                plato = self.platos_por_nombre.get(nombre_plato)
                if not plato:
                    continue
                
                tecnicas_plato = plato.get('tecnica_coccion', [])
                
                # Verificar si al menos una técnica coincide
                if tecnicas_plato:
                    tiene_tecnica_apropiada = any(
                        any(esp in tec.lower() for esp in tecnicas_esperadas)
                        for tec in tecnicas_plato
                    )
                    
                    if not tiene_tecnica_apropiada and estilo_caso == 'molecular':
                        # Molecular es muy específico
                        self._warning(f"Caso {caso_id} (molecular): Plato '{nombre_plato[:50]}' usa técnicas {tecnicas_plato}, no molecular")
                        casos_problematicos.append(caso_id)
        
        print(f"  {'✓' if not casos_problematicos else '⚠️ '} Casos con estilo inconsistente: {len(set(casos_problematicos))}")
        return list(set(casos_problematicos))
    
    def generar_reporte(self, casos_cultura, casos_restricciones, casos_estilo):
        """Genera reporte completo."""
        print("\n" + "="*70)
        print("REPORTE DE COHERENCIA CULTURAL Y ESTILO")
        print("="*70 + "\n")
        
        print(f"📊 RESULTADOS:")
        print(f"  - Errores críticos: {len(self.errores_criticos)}")
        print(f"  - Warnings: {len(self.warnings)}\n")
        
        print(f"🌍 COHERENCIA CULTURAL:")
        print(f"  - Casos con problemas: {len(casos_cultura)}")
        if casos_cultura:
            print(f"  - IDs: {', '.join(casos_cultura[:20])}")
            if len(casos_cultura) > 20:
                print(f"    ... y {len(casos_cultura) - 20} más")
        
        print(f"\n🔒 RESTRICCIONES ALIMENTARIAS:")
        print(f"  - Casos con violaciones: {len(casos_restricciones)}")
        if casos_restricciones:
            print(f"  - IDs: {', '.join(casos_restricciones[:20])}")
        
        print(f"\n🎨 COHERENCIA DE ESTILO:")
        print(f"  - Casos con estilo inconsistente: {len(casos_estilo)}")
        if casos_estilo:
            print(f"  - IDs: {', '.join(casos_estilo[:20])}")
        
        print("\n" + "="*70)
        
        if self.errores_criticos:
            print("\n❌ ERRORES CRÍTICOS (primeros 30):\n")
            for error in self.errores_criticos[:30]:
                print(error)
            if len(self.errores_criticos) > 30:
                print(f"\n... y {len(self.errores_criticos) - 30} errores más")
        
        if self.warnings:
            print("\n⚠️  WARNINGS (primeros 20):\n")
            for warning in self.warnings[:20]:
                print(warning)
            if len(self.warnings) > 20:
                print(f"\n... y {len(self.warnings) - 20} warnings más")
        
        # Guardar reporte
        with open('REPORTE_COHERENCIA_DETALLADO.txt', 'w', encoding='utf-8') as f:
            f.write("ERRORES CRÍTICOS:\n")
            f.write("="*70 + "\n")
            for error in self.errores_criticos:
                f.write(f"{error}\n")
            f.write("\n\nWARNINGS:\n")
            f.write("="*70 + "\n")
            for warning in self.warnings:
                f.write(f"{warning}\n")
        
        print("\n💾 Reporte detallado: REPORTE_COHERENCIA_DETALLADO.txt")
    
    def ejecutar(self):
        """Ejecuta todas las validaciones."""
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║    VALIDADOR DE COHERENCIA CULTURAL Y ESTILO - PROFUNDO     ║")
        print("╚══════════════════════════════════════════════════════════════╝\n")
        
        casos_cultura = self.validar_coherencia_cultural_estricta()
        casos_restricciones = self.validar_restricciones_alimentarias()
        casos_estilo = self.validar_coherencia_estilo()
        
        self.generar_reporte(casos_cultura, casos_restricciones, casos_estilo)
        
        return len(self.errores_criticos) == 0


def main():
    """Función principal."""
    validador = ValidadorCoherenciaProfunda()
    exito = validador.ejecutar()
    
    if exito:
        print("\n✅ Validación exitosa (solo warnings)")
        return 0
    else:
        print("\n❌ Validación fallida (errores críticos encontrados)")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
