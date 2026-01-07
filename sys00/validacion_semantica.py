#!/usr/bin/env python3
"""
Validación semántica profunda del sistema CBR.

Verifica:
1. Ingredientes duplicados (traducciones, sinónimos)
2. Platos duplicados (mismo nombre o idénticos en composición)
3. Coherencia temporal (ingredientes de temporada correcta)
4. Coherencia cultural (platos alineados con tradición)
5. Coherencia de estilo (técnicas culinarias apropiadas)
"""

import json
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import Counter, defaultdict
import difflib


class ValidadorSemantico:
    """Validador semántico completo."""
    
    def __init__(self, conocimiento_dir: str = 'conocimiento'):
        self.conocimiento_dir = Path(conocimiento_dir)
        self.errores = []
        self.warnings = []
        self.correcciones = []
        
        # Cargar datos
        self.casos = self._cargar_json('casos.json')
        self.platos = self._cargar_json('platos.json')
        self.ingredientes = self._cargar_json('ingredientes.json')
        self.restricciones = self._cargar_json('restricciones.json')
        
        # Índices
        self.platos_por_nombre = {p['nombre']: p for p in self.platos}
        self.ingredientes_por_nombre = {ing['nombre']: ing for ing in self.ingredientes}
    
    def _cargar_json(self, filename: str) -> List[Dict]:
        """Carga archivo JSON."""
        path = self.conocimiento_dir / filename
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _error(self, mensaje: str):
        """Registra un error."""
        self.errores.append(f"❌ {mensaje}")
    
    def _warning(self, mensaje: str):
        """Registra un warning."""
        self.warnings.append(f"⚠️  {mensaje}")
    
    def _correccion(self, mensaje: str):
        """Registra una corrección sugerida."""
        self.correcciones.append(f"🔧 {mensaje}")
    
    def validar_ingredientes_duplicados(self):
        """Detecta ingredientes duplicados por traducciones o similitud."""
        print("🔍 Validando ingredientes duplicados...")
        
        nombres = [ing['nombre'] for ing in self.ingredientes]
        
        # 1. Duplicados exactos
        duplicados_exactos = [nombre for nombre, count in Counter(nombres).items() if count > 1]
        if duplicados_exactos:
            for nombre in duplicados_exactos:
                self._error(f"Ingrediente duplicado exacto: '{nombre}'")
        
        # 2. Similitud por nombres (posibles traducciones)
        similares = []
        for i, nombre1 in enumerate(nombres):
            for j, nombre2 in enumerate(nombres[i+1:], i+1):
                ratio = difflib.SequenceMatcher(None, nombre1.lower(), nombre2.lower()).ratio()
                if ratio > 0.85:  # 85% similar
                    similares.append((nombre1, nombre2, ratio))
        
        if similares:
            print(f"  ⚠️  Encontrados {len(similares)} pares de ingredientes muy similares:")
            for nom1, nom2, ratio in similares[:20]:  # Mostrar primeros 20
                self._warning(f"Ingredientes similares ({ratio:.2%}): '{nom1}' ≈ '{nom2}'")
        
        # 3. Traducción inglés-español obvias
        traducciones_sospechosas = {
            'milk': 'leche',
            'butter': 'mantequilla',
            'cheese': 'queso',
            'chicken': 'pollo',
            'beef': 'carne',
            'fish': 'pescado',
            'bread': 'pan',
            'water': 'agua',
            'tomato': 'tomate',
            'onion': 'cebolla',
            'garlic': 'ajo',
            'salt': 'sal',
            'pepper': 'pimienta',
            'oil': 'aceite',
            'rice': 'arroz',
            'pasta': 'pasta',
            'egg': 'huevo',
        }
        
        nombres_lower = {n.lower(): n for n in nombres}
        for eng, esp in traducciones_sospechosas.items():
            if eng in nombres_lower and esp in nombres_lower:
                self._warning(f"Posible duplicado por traducción: '{nombres_lower[eng]}' y '{nombres_lower[esp]}'")
        
        if not duplicados_exactos and not similares:
            print("  ✓ No se encontraron ingredientes duplicados")
    
    def validar_platos_duplicados(self):
        """Detecta platos duplicados por nombre o composición."""
        print("🔍 Validando platos duplicados...")
        
        nombres = [p['nombre'] for p in self.platos]
        
        # 1. Duplicados exactos por nombre
        duplicados_exactos = [nombre for nombre, count in Counter(nombres).items() if count > 1]
        if duplicados_exactos:
            for nombre in duplicados_exactos:
                self._error(f"Plato duplicado exacto: '{nombre}'")
        
        # 2. Nombres muy similares
        similares_nombre = []
        for i, nombre1 in enumerate(nombres):
            for j, nombre2 in enumerate(nombres[i+1:], i+1):
                ratio = difflib.SequenceMatcher(None, nombre1.lower(), nombre2.lower()).ratio()
                if ratio > 0.90:  # 90% similar
                    similares_nombre.append((nombre1, nombre2, ratio))
        
        if similares_nombre:
            print(f"  ⚠️  Encontrados {len(similares_nombre)} pares de platos con nombres muy similares:")
            for nom1, nom2, ratio in similares_nombre[:10]:
                self._warning(f"Platos con nombres similares ({ratio:.2%}): '{nom1[:50]}' ≈ '{nom2[:50]}'")
        
        # 3. Composición idéntica (mismos ingredientes exactos)
        firmas_ingredientes = defaultdict(list)
        for plato in self.platos:
            ingredientes = tuple(sorted(plato.get('ingredientes', [])))
            firmas_ingredientes[ingredientes].append(plato['nombre'])
        
        duplicados_composicion = {firma: nombres for firma, nombres in firmas_ingredientes.items() if len(nombres) > 1}
        
        if duplicados_composicion:
            print(f"  ⚠️  Encontrados {len(duplicados_composicion)} grupos de platos con composición idéntica:")
            for idx, (firma, nombres_platos) in enumerate(list(duplicados_composicion.items())[:5], 1):
                self._warning(f"Platos idénticos (grupo {idx}): {', '.join([n[:40] for n in nombres_platos])}")
        
        if not duplicados_exactos and not similares_nombre and not duplicados_composicion:
            print("  ✓ No se encontraron platos duplicados")
    
    def validar_coherencia_temporal(self):
        """Valida que los ingredientes de los platos correspondan a la temporada del caso."""
        print("🔍 Validando coherencia temporal (temporada)...")
        
        errores_temporales = 0
        
        for caso in self.casos:
            temporada_caso = caso.get('temporada', '')
            menu = caso.get('menu', {})
            caso_id = caso['id']
            
            for tipo_plato, nombre_plato in menu.items():
                plato = self.platos_por_nombre.get(nombre_plato)
                if not plato:
                    continue
                
                # Verificar temporada de cada ingrediente
                ingredientes = plato.get('ingredientes', [])
                for ing_nombre in ingredientes:
                    ing = self.ingredientes_por_nombre.get(ing_nombre)
                    if not ing:
                        continue
                    
                    temporadas_ing = ing.get('temporada', [])
                    
                    # Si el ingrediente tiene temporadas definidas y NO incluye la del caso
                    if temporadas_ing and temporada_caso not in temporadas_ing:
                        self._warning(f"Caso {caso_id}: Ingrediente '{ing_nombre}' en plato '{nombre_plato[:40]}' no es de temporada '{temporada_caso}' (válido: {temporadas_ing})")
                        errores_temporales += 1
        
        if errores_temporales > 0:
            print(f"  ⚠️  {errores_temporales} incoherencias temporales encontradas")
        else:
            print("  ✓ Coherencia temporal correcta")
    
    def validar_coherencia_cultural(self):
        """Valida que los platos correspondan a la tradición cultural del caso."""
        print("🔍 Validando coherencia cultural (tradición)...")
        
        errores_culturales = 0
        
        # Mapeo de tradiciones (permitir variaciones)
        mapeo_tradiciones = {
            'catalana': {'catalana', 'española', 'mediterranea'},
            'italiana': {'italiana', 'mediterranea'},
            'francesa': {'francesa', 'europea'},
            'mexicana': {'mexicana', 'latina'},
            'china': {'china', 'asiatica', 'asian'},
            'mediterranea': {'mediterranea', 'italiana', 'griega', 'catalana'},
            'india': {'india', 'hindu'},
        }
        
        for caso in self.casos:
            tradicion_caso = caso.get('tradicion', '')
            menu = caso.get('menu', {})
            caso_id = caso['id']
            
            tradiciones_permitidas = mapeo_tradiciones.get(tradicion_caso, {tradicion_caso})
            
            for tipo_plato, nombre_plato in menu.items():
                plato = self.platos_por_nombre.get(nombre_plato)
                if not plato:
                    continue
                
                tradicion_plato = plato.get('tradicion', 'general')
                
                # Si el plato tiene tradición específica y NO coincide
                if tradicion_plato and tradicion_plato != 'general':
                    if tradicion_plato not in tradiciones_permitidas:
                        # Verificar si es un nombre que sugiere otra tradición
                        nombre_lower = nombre_plato.lower()
                        indicadores = {
                            'italiana': ['italian', 'pasta', 'pizza', 'risotto', 'gnocchi', 'tiramisu'],
                            'mexicana': ['mexican', 'tacos', 'burrito', 'salsa', 'guacamole', 'chile'],
                            'francesa': ['french', 'crème', 'soufflé', 'croissant'],
                            'china': ['chinese', 'wok', 'noodles', 'dim sum'],
                        }
                        
                        conflicto = False
                        for trad, palabras in indicadores.items():
                            if any(palabra in nombre_lower for palabra in palabras):
                                if trad != tradicion_caso:
                                    conflicto = True
                                    break
                        
                        if conflicto or tradicion_plato not in tradiciones_permitidas:
                            self._warning(f"Caso {caso_id}: Plato '{nombre_plato[:40]}' (tradición: {tradicion_plato}) no coincide con caso '{tradicion_caso}'")
                            errores_culturales += 1
        
        if errores_culturales > 0:
            print(f"  ⚠️  {errores_culturales} incoherencias culturales encontradas")
        else:
            print("  ✓ Coherencia cultural correcta")
    
    def validar_coherencia_restricciones(self):
        """Valida que los platos cumplan las restricciones del caso."""
        print("🔍 Validando cumplimiento de restricciones...")
        
        errores_restricciones = 0
        
        for caso in self.casos:
            restricciones = caso.get('restricciones', [])
            if not restricciones:
                continue
            
            menu = caso.get('menu', {})
            caso_id = caso['id']
            
            for tipo_plato, nombre_plato in menu.items():
                plato = self.platos_por_nombre.get(nombre_plato)
                if not plato:
                    continue
                
                ingredientes_plato = set(plato.get('ingredientes', []))
                
                # Verificar cada restricción
                for restriccion_nombre in restricciones:
                    restriccion = next((r for r in self.restricciones if r['nombre'] == restriccion_nombre), None)
                    if not restriccion:
                        continue
                    
                    # Ingredientes prohibidos
                    prohibidos = set(restriccion.get('ingredientes_prohibidos', []))
                    conflicto = ingredientes_plato & prohibidos
                    
                    if conflicto:
                        self._error(f"Caso {caso_id}: Plato '{nombre_plato[:40]}' viola restricción '{restriccion_nombre}' (contiene: {list(conflicto)[:3]})")
                        errores_restricciones += 1
                    
                    # Categorías prohibidas
                    categorias_prohibidas = set(restriccion.get('categorias_prohibidas', []))
                    for ing_nombre in ingredientes_plato:
                        ing = self.ingredientes_por_nombre.get(ing_nombre)
                        if ing and ing.get('categoria') in categorias_prohibidas:
                            self._error(f"Caso {caso_id}: Plato '{nombre_plato[:40]}' viola restricción '{restriccion_nombre}' (ingrediente '{ing_nombre}' es categoría prohibida '{ing.get('categoria')}')")
                            errores_restricciones += 1
        
        if errores_restricciones > 0:
            print(f"  ❌ {errores_restricciones} VIOLACIONES DE RESTRICCIONES (crítico)")
        else:
            print("  ✓ Todas las restricciones se cumplen")
    
    def generar_reporte(self) -> str:
        """Genera reporte final."""
        total_errores = len(self.errores)
        total_warnings = len(self.warnings)
        
        reporte = "\n"
        reporte += "╔══════════════════════════════════════════════════════════════╗\n"
        reporte += "║         REPORTE DE VALIDACIÓN SEMÁNTICA                      ║\n"
        reporte += "╚══════════════════════════════════════════════════════════════╝\n\n"
        
        reporte += f"🎯 RESULTADOS:\n"
        reporte += f"  - Errores críticos: {total_errores}\n"
        reporte += f"  - Warnings: {total_warnings}\n\n"
        
        if total_errores > 0:
            reporte += "❌ ERRORES CRÍTICOS:\n"
            for error in self.errores[:50]:
                reporte += f"{error}\n"
            if len(self.errores) > 50:
                reporte += f"  ... y {len(self.errores) - 50} errores más\n"
            reporte += "\n"
        
        if total_warnings > 0:
            reporte += "⚠️  WARNINGS:\n"
            for warning in self.warnings[:50]:
                reporte += f"{warning}\n"
            if len(self.warnings) > 50:
                reporte += f"  ... y {len(self.warnings) - 50} warnings más\n"
            reporte += "\n"
        
        if total_errores == 0 and total_warnings == 0:
            reporte += "✅ ¡VALIDACIÓN SEMÁNTICA EXITOSA!\n"
        elif total_errores == 0:
            reporte += "⚠️  Validación con warnings (revisar pero no crítico)\n"
        else:
            reporte += "❌ VALIDACIÓN FALLIDA. Corrige los errores críticos.\n"
        
        return reporte
    
    def ejecutar(self):
        """Ejecuta todas las validaciones."""
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║       VALIDADOR SEMÁNTICO CBR - SBC-sys-cbr                  ║")
        print("╚══════════════════════════════════════════════════════════════╝\n")
        
        self.validar_ingredientes_duplicados()
        self.validar_platos_duplicados()
        self.validar_coherencia_temporal()
        self.validar_coherencia_cultural()
        self.validar_coherencia_restricciones()
        
        reporte = self.generar_reporte()
        print(reporte)
        
        with open('REPORTE_VALIDACION_SEMANTICA.txt', 'w', encoding='utf-8') as f:
            f.write(reporte)
        print("💾 Reporte guardado en: REPORTE_VALIDACION_SEMANTICA.txt\n")
        
        return len(self.errores) == 0


def main():
    """Función principal."""
    validador = ValidadorSemantico()
    exito = validador.ejecutar()
    
    if exito:
        print("🎉 Validación semántica correcta.")
        return 0
    else:
        print("💥 Validación semántica fallida. Revisa los errores.")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
