#!/usr/bin/env python3
"""
Script de validación de integridad referencial y coherencia del sistema CBR.

Verifica:
1. Todo plato usado en casos existe en platos.json
2. Todo ingrediente usado en platos existe en ingredientes.json
3. No hay duplicados por ID/nombre
4. Los valores de preferencias son válidos
5. Las restricciones son válidas
6. Combinaciones de restricciones son permitidas
"""

import json
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import Counter


class ValidadorIntegridadCBR:
    """Validador completo de integridad del sistema CBR."""
    
    def __init__(self, conocimiento_dir: str = 'conocimiento'):
        self.conocimiento_dir = Path(conocimiento_dir)
        self.errores = []
        self.warnings = []
        
        # Cargar datos
        self.casos = self._cargar_json('casos.json')
        self.platos = self._cargar_json('platos.json')
        self.ingredientes = self._cargar_json('ingredientes.json')
        self.restricciones = self._cargar_json('restricciones.json')
        
        # Conjuntos de lookup
        self.platos_nombres = {p['nombre'] for p in self.platos}
        self.ingredientes_nombres = {ing['nombre'] for ing in self.ingredientes}
        self.restricciones_nombres = {r['nombre'] for r in self.restricciones}
        
        # Valores válidos de enums
        self.tradiciones_validas = {'catalana', 'mexicana', 'italiana', 'francesa', 'china', 'mediterranea', 'india'}
        self.temporadas_validas = {'primavera', 'verano', 'otoño', 'invierno'}
        self.eventos_validos = {'boda', 'congreso', 'familiar'}
        self.estilos_validos = {'molecular', 'clasico', 'gourmet', 'comfort_food', 'picante', 'fusion', 'saludable'}
    
    def _cargar_json(self, filename: str) -> List[Dict]:
        """Carga archivo JSON."""
        path = self.conocimiento_dir / filename
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _error(self, mensaje: str):
        """Registra un error."""
        self.errores.append(f"❌ ERROR: {mensaje}")
    
    def _warning(self, mensaje: str):
        """Registra un warning."""
        self.warnings.append(f"⚠️  WARNING: {mensaje}")
    
    def validar_ids_unicos(self):
        """Valida que todos los IDs de casos sean únicos."""
        print("🔍 Validando IDs únicos de casos...")
        
        ids_casos = [c['id'] for c in self.casos]
        ids_counter = Counter(ids_casos)
        
        duplicados = [id_caso for id_caso, count in ids_counter.items() if count > 1]
        
        if duplicados:
            for id_dup in duplicados:
                self._error(f"ID duplicado en casos: {id_dup} (aparece {ids_counter[id_dup]} veces)")
        else:
            print("  ✓ Todos los IDs de casos son únicos")
    
    def validar_platos_existen(self):
        """Valida que todos los platos usados en casos existan en platos.json."""
        print("🔍 Validando existencia de platos en casos...")
        
        platos_faltantes = set()
        
        for caso in self.casos:
            menu = caso.get('menu', {})
            entrante = menu.get('entrante', '')
            principal = menu.get('principal', '')
            postre = menu.get('postre', '')
            
            for plato_nombre in [entrante, principal, postre]:
                if plato_nombre and plato_nombre not in self.platos_nombres:
                    platos_faltantes.add(plato_nombre)
                    self._error(f"Caso {caso['id']}: Plato '{plato_nombre}' no existe en platos.json")
        
        if not platos_faltantes:
            print("  ✓ Todos los platos usados en casos existen")
        else:
            print(f"  ✗ {len(platos_faltantes)} platos faltantes encontrados")
    
    def validar_ingredientes_existen(self):
        """Valida que todos los ingredientes usados en platos existan en ingredientes.json."""
        print("🔍 Validando existencia de ingredientes en platos...")
        
        ingredientes_faltantes = set()
        
        for plato in self.platos:
            for ingrediente in plato.get('ingredientes', []):
                if ingrediente not in self.ingredientes_nombres:
                    ingredientes_faltantes.add(ingrediente)
                    self._error(f"Plato '{plato['nombre']}': Ingrediente '{ingrediente}' no existe en ingredientes.json")
        
        if not ingredientes_faltantes:
            print("  ✓ Todos los ingredientes usados en platos existen")
        else:
            print(f"  ✗ {len(ingredientes_faltantes)} ingredientes faltantes encontrados")
    
    def validar_preferencias_validas(self):
        """Valida que todas las preferencias tengan valores válidos."""
        print("🔍 Validando valores de preferencias...")
        
        for caso in self.casos:
            caso_id = caso['id']
            
            # Tradición
            tradicion = caso.get('tradicion', '')
            if tradicion and tradicion not in self.tradiciones_validas:
                self._error(f"Caso {caso_id}: Tradición inválida '{tradicion}'")
            
            # Temporada
            temporada = caso.get('temporada', '')
            if temporada and temporada not in self.temporadas_validas:
                self._error(f"Caso {caso_id}: Temporada inválida '{temporada}'")
            
            # Tipo evento
            tipo_evento = caso.get('tipo_evento', '')
            if tipo_evento and tipo_evento not in self.eventos_validos:
                self._error(f"Caso {caso_id}: Tipo evento inválido '{tipo_evento}'")
            
            # Estilo
            estilo = caso.get('estilo', '')
            if estilo and estilo not in self.estilos_validos:
                self._error(f"Caso {caso_id}: Estilo inválido '{estilo}'")
        
        if not any('Tradición inválida' in e or 'Temporada inválida' in e or 'Tipo evento inválido' in e or 'Estilo inválido' in e for e in self.errores):
            print("  ✓ Todas las preferencias tienen valores válidos")
    
    def validar_restricciones_validas(self):
        """Valida que todas las restricciones sean válidas."""
        print("🔍 Validando restricciones...")
        
        restricciones_invalidas = set()
        
        for caso in self.casos:
            caso_id = caso['id']
            restricciones = caso.get('restricciones', [])
            
            # Verificar que sea lista
            if not isinstance(restricciones, list):
                self._error(f"Caso {caso_id}: 'restricciones' debe ser una lista, es {type(restricciones).__name__}")
                continue
            
            # Verificar cada restricción
            for restriccion in restricciones:
                if restriccion not in self.restricciones_nombres:
                    restricciones_invalidas.add(restriccion)
                    self._error(f"Caso {caso_id}: Restricción inválida '{restriccion}'")
        
        if not restricciones_invalidas:
            print("  ✓ Todas las restricciones son válidas")
        else:
            print(f"  ✗ {len(restricciones_invalidas)} restricciones inválidas encontradas")
    
    def validar_estructura_casos(self):
        """Valida que todos los casos tengan la estructura correcta."""
        print("🔍 Validando estructura de casos...")
        
        campos_requeridos = {'id', 'restricciones', 'temporada', 'tipo_evento', 'menu', 'estilo', 'tradicion', 'exito', 'fallos_detectados', 'reparaciones_aplicadas'}
        campos_menu_requeridos = {'entrante', 'principal', 'postre'}
        
        for caso in self.casos:
            caso_id = caso.get('id', 'UNKNOWN')
            
            # Verificar campos requeridos
            campos_caso = set(caso.keys())
            campos_faltantes = campos_requeridos - campos_caso
            
            if campos_faltantes:
                self._error(f"Caso {caso_id}: Campos faltantes: {campos_faltantes}")
            
            # Verificar estructura del menú
            menu = caso.get('menu', {})
            if not isinstance(menu, dict):
                self._error(f"Caso {caso_id}: 'menu' debe ser un diccionario")
                continue
            
            campos_menu = set(menu.keys())
            campos_menu_faltantes = campos_menu_requeridos - campos_menu
            
            if campos_menu_faltantes:
                self._error(f"Caso {caso_id}: Campos faltantes en menú: {campos_menu_faltantes}")
        
        if not any('Campos faltantes' in e for e in self.errores):
            print("  ✓ Todos los casos tienen la estructura correcta")
    
    def validar_nombres_platos_unicos(self):
        """Valida que no haya nombres de platos duplicados."""
        print("🔍 Validando unicidad de nombres de platos...")
        
        nombres_platos = [p['nombre'] for p in self.platos]
        nombres_counter = Counter(nombres_platos)
        
        duplicados = [nombre for nombre, count in nombres_counter.items() if count > 1]
        
        if duplicados:
            for nombre in duplicados:
                self._warning(f"Plato duplicado: '{nombre}' (aparece {nombres_counter[nombre]} veces)")
        else:
            print("  ✓ Todos los nombres de platos son únicos")
    
    def validar_nombres_ingredientes_unicos(self):
        """Valida que no haya nombres de ingredientes duplicados."""
        print("🔍 Validando unicidad de nombres de ingredientes...")
        
        nombres_ingredientes = [ing['nombre'] for ing in self.ingredientes]
        nombres_counter = Counter(nombres_ingredientes)
        
        duplicados = [nombre for nombre, count in nombres_counter.items() if count > 1]
        
        if duplicados:
            for nombre in duplicados:
                self._warning(f"Ingrediente duplicado: '{nombre}' (aparece {nombres_counter[nombre]} veces)")
        else:
            print("  ✓ Todos los nombres de ingredientes son únicos")
    
    def validar_combinaciones_restricciones(self):
        """Valida que las combinaciones de restricciones sean lógicas."""
        print("🔍 Validando combinaciones de restricciones...")
        
        # Restricciones incompatibles (vegano implica vegetariano, no deberían estar juntas)
        for caso in self.casos:
            caso_id = caso['id']
            restricciones = set(caso.get('restricciones', []))
            
            # Si es vegano, no debería tener también vegetariano (vegano es más restrictivo)
            if 'vegano' in restricciones and 'vegetariano' in restricciones:
                self._warning(f"Caso {caso_id}: 'vegano' implica 'vegetariano', redundante tener ambos")
        
        print("  ✓ Validación de combinaciones completada")
    
    def generar_reporte(self) -> str:
        """Genera reporte final de validación."""
        total_errores = len(self.errores)
        total_warnings = len(self.warnings)
        
        reporte = "\n"
        reporte += "╔══════════════════════════════════════════════════════════════╗\n"
        reporte += "║           REPORTE DE VALIDACIÓN DE INTEGRIDAD               ║\n"
        reporte += "╚══════════════════════════════════════════════════════════════╝\n"
        reporte += "\n"
        reporte += f"📊 RESUMEN:\n"
        reporte += f"  - Total casos: {len(self.casos)}\n"
        reporte += f"  - Total platos: {len(self.platos)}\n"
        reporte += f"  - Total ingredientes: {len(self.ingredientes)}\n"
        reporte += f"  - Total restricciones: {len(self.restricciones)}\n"
        reporte += "\n"
        reporte += f"🎯 RESULTADOS:\n"
        reporte += f"  - Errores críticos: {total_errores}\n"
        reporte += f"  - Warnings: {total_warnings}\n"
        reporte += "\n"
        
        if total_errores > 0:
            reporte += "❌ ERRORES CRÍTICOS:\n"
            for error in self.errores:
                reporte += f"{error}\n"
            reporte += "\n"
        
        if total_warnings > 0:
            reporte += "⚠️  WARNINGS:\n"
            for warning in self.warnings[:20]:  # Limitar a 20
                reporte += f"{warning}\n"
            if len(self.warnings) > 20:
                reporte += f"  ... y {len(self.warnings) - 20} warnings más\n"
            reporte += "\n"
        
        if total_errores == 0:
            reporte += "✅ ¡VALIDACIÓN EXITOSA! No se encontraron errores críticos.\n"
        else:
            reporte += "❌ VALIDACIÓN FALLIDA. Por favor corrige los errores críticos.\n"
        
        return reporte
    
    def ejecutar(self):
        """Ejecuta todas las validaciones."""
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║         VALIDADOR DE INTEGRIDAD CBR - SBC-sys-cbr           ║")
        print("╚══════════════════════════════════════════════════════════════╝\n")
        
        self.validar_estructura_casos()
        self.validar_ids_unicos()
        self.validar_platos_existen()
        self.validar_ingredientes_existen()
        self.validar_preferencias_validas()
        self.validar_restricciones_validas()
        self.validar_nombres_platos_unicos()
        self.validar_nombres_ingredientes_unicos()
        self.validar_combinaciones_restricciones()
        
        reporte = self.generar_reporte()
        print(reporte)
        
        # Guardar reporte
        with open('REPORTE_VALIDACION.txt', 'w', encoding='utf-8') as f:
            f.write(reporte)
        print("💾 Reporte guardado en: REPORTE_VALIDACION.txt\n")
        
        return len(self.errores) == 0


def main():
    """Función principal."""
    validador = ValidadorIntegridadCBR()
    exito = validador.ejecutar()
    
    if exito:
        print("🎉 Sistema validado correctamente. Integridad garantizada.")
        return 0
    else:
        print("💥 Validación fallida. Revisa los errores y corrígelos.")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
