#!/usr/bin/env python3
"""
Demo Script for CBR Retention System
=====================================

Demonstrates the complete retention pipeline:
1. Generate valid menus
2. Collect satisfaction ratings
3. Intelligent retention based on satisfaction/complexity/diversity
4. Memory curation when cap is reached
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(__file__))

from sistema_cbr import SistemaCBR, PreferenciasUsuario, ConfiguracionCBR
from actualizador.config_retention import RetentionConfig


def demo_basic_retention():
    """Demo 1: Basic retention with rating collection."""
    print("\n" + "="*80)
    print("DEMO 1: BASIC RETENTION WITH RATING COLLECTION")
    print("="*80)
    
    # Create system with retention enabled and low cap for demonstration
    retention_config = RetentionConfig(
        max_cases=30,  # Low cap to trigger curation quickly
        min_cases=20,
        weight_satisfaction=0.40,
        weight_modifications=0.35,
        weight_novelty=0.25
    )
    
    cbr_config = ConfiguracionCBR(
        max_intentos_reparacion=3,
        k_casos_recuperar=3
    )
    
    sistema = SistemaCBR(config=cbr_config)
    # Override actualizador with retention-enabled version
    from actualizador import ActualizadorConocimiento
    sistema.actualizador = ActualizadorConocimiento(
        retention_config=retention_config,
        enable_retention=True
    )
    
    # Generate a menu
    preferencias = PreferenciasUsuario(
        tipo_evento='familiar',
        temporada='verano',
        restricciones=['vegetariano'],
        estilo='clasico',
        tradicion='italiana'
    )
    
    print("\n[DEMO] Generando menú con preferencias vegetarianas italianas...")
    resultado = sistema.generar_menu(preferencias)
    
    if resultado.exito:
        print(f"\n✓ Menú generado exitosamente")
        print(f"  Caso base: {resultado.caso_base_id}")
        print(f"  Nuevo caso: {resultado.nuevo_caso_id}")
        if resultado.reparaciones_aplicadas:
            print(f"  Reparaciones: {len(resultado.reparaciones_aplicadas)}")
    else:
        print(f"\n✗ Error: {resultado.mensaje}")
    
    # Show retention statistics
    stats = sistema.actualizador.get_retention_statistics()
    print("\n" + "-"*80)
    print("ESTADÍSTICAS DE RETENCIÓN")
    print("-"*80)
    print(f"Casos totales: {stats['total_casos']}/{stats['max_casos']}")
    print(f"Uso de memoria: {stats['memory_usage_pct']:.1f}%")
    print(f"Casos con satisfacción: {stats['casos_with_satisfaction']}")
    print(f"Casos con modificaciones: {stats['casos_with_modifications']}")
    if stats['avg_satisfaction']:
        print(f"Satisfacción promedio: {stats['avg_satisfaction']:.2f}/5.0")
    if stats['avg_modifications']:
        print(f"Modificaciones promedio: {stats['avg_modifications']:.2f}")


def demo_memory_curation():
    """Demo 2: Memory curation when cap is exceeded."""
    print("\n" + "="*80)
    print("DEMO 2: MEMORY CURATION (FORGETTING LOW-VALUE CASES)")
    print("="*80)
    
    # Create system with very low cap
    retention_config = RetentionConfig(
        max_cases=27,  # Current DB has 25 cases, so 2 more will trigger curation
        min_cases=20,
        weight_satisfaction=0.40,
        weight_modifications=0.35,
        weight_novelty=0.25,
        near_duplicate_threshold=0.90
    )
    
    sistema = SistemaCBR()
    from actualizador import ActualizadorConocimiento
    sistema.actualizador = ActualizadorConocimiento(
        retention_config=retention_config,
        enable_retention=True
    )
    
    print(f"\n[DEMO] Cap de memoria: {retention_config.max_cases}")
    print(f"[DEMO] Casos actuales: {len(sistema.actualizador.casos)}")
    print(f"[DEMO] Generando múltiples menús para exceder el cap...")
    
    # Generate several menus to trigger curation
    test_preferences = [
        {'tipo_evento': 'boda', 'temporada': 'primavera', 'restricciones': ['sin_gluten'], 
         'estilo': 'clasico', 'tradicion': 'francesa'},
        {'tipo_evento': 'congreso', 'temporada': 'otoño', 'restricciones': ['vegano'], 
         'estilo': 'molecular', 'tradicion': 'italiana'},
        {'tipo_evento': 'familiar', 'temporada': 'invierno', 'restricciones': [], 
         'estilo': 'clasico', 'tradicion': 'mexicana'},
    ]
    
    for i, prefs in enumerate(test_preferences, 1):
        print(f"\n\n{'#'*80}")
        print(f"GENERACIÓN {i}/3")
        print(f"{'#'*80}")
        
        preferencias = PreferenciasUsuario(**prefs)
        resultado = sistema.generar_menu(preferencias)
        
        if resultado.exito and resultado.nuevo_caso_id:
            print(f"\n✓ Caso {resultado.nuevo_caso_id} agregado")
        elif resultado.exito:
            print(f"\n○ Menú generado pero no retenido")
        
        current_count = len(sistema.actualizador.casos)
        print(f"Casos en memoria: {current_count}/{retention_config.max_cases}")


def demo_retention_statistics():
    """Demo 3: Show detailed retention statistics."""
    print("\n" + "="*80)
    print("DEMO 3: ESTADÍSTICAS DETALLADAS DE RETENCIÓN")
    print("="*80)
    
    sistema = SistemaCBR()
    from actualizador import ActualizadorConocimiento
    sistema.actualizador = ActualizadorConocimiento(enable_retention=True)
    
    stats = sistema.actualizador.get_retention_statistics()
    
    print(f"\nSistema de Retención: {'✓ Habilitado' if stats['enabled'] else '✗ Deshabilitado'}")
    
    if stats['enabled']:
        print(f"\n📊 MEMORIA:")
        print(f"  Total de casos: {stats['total_casos']}")
        print(f"  Capacidad máxima: {stats['max_casos']}")
        print(f"  Capacidad mínima: {stats['min_casos']}")
        print(f"  Uso actual: {stats['memory_usage_pct']:.1f}%")
        
        print(f"\n⭐ SATISFACCIÓN:")
        print(f"  Casos con calificación: {stats['casos_with_satisfaction']}/{stats['total_casos']}")
        if stats['avg_satisfaction']:
            print(f"  Promedio: {stats['avg_satisfaction']:.2f}/5.0")
        else:
            print(f"  Promedio: N/A (sin calificaciones)")
        
        print(f"\n🔧 COMPLEJIDAD:")
        print(f"  Casos con modificaciones: {stats['casos_with_modifications']}/{stats['total_casos']}")
        if stats['avg_modifications']:
            print(f"  Promedio de modificaciones: {stats['avg_modifications']:.2f}")
        else:
            print(f"  Promedio: N/A")
        
        print(f"\n⚖️  PESOS DE RETENCIÓN:")
        print(f"  Satisfacción: {stats['retention_weights']['satisfaction']:.2f}")
        print(f"  Modificaciones: {stats['retention_weights']['modifications']:.2f}")
        print(f"  Novedad: {stats['retention_weights']['novelty']:.2f}")


def demo_backward_compatibility():
    """Demo 4: Test backward compatibility with old cases."""
    print("\n" + "="*80)
    print("DEMO 4: COMPATIBILIDAD HACIA ATRÁS")
    print("="*80)
    
    from conocimiento.models import Caso, Menu
    
    # Old case format (without satisfaction fields)
    old_case_dict = {
        'id': 'C001',
        'restricciones': ['vegetariano'],
        'temporada': 'verano',
        'tipo_evento': 'boda',
        'menu': {'entrante': 'A', 'principal': 'B', 'postre': 'C'},
        'estilo': 'clasico',
        'tradicion': 'italiana',
        'exito': True,
        'fallos_detectados': [],
        'reparaciones_aplicadas': []
    }
    
    print("\n[TEST] Cargando caso antiguo (sin campos de satisfacción)...")
    caso = Caso.from_dict(old_case_dict)
    
    print(f"✓ Caso cargado correctamente: {caso.id}")
    print(f"  satisfaction_score: {caso.satisfaction_score}")
    print(f"  satisfaction_per_menu: {caso.satisfaction_per_menu}")
    print(f"  modification_count: {caso.modification_count}")
    
    # New case format (with satisfaction)
    new_case_dict = {
        'id': 'C999',
        'restricciones': [],
        'temporada': 'invierno',
        'tipo_evento': 'familiar',
        'menu': {'entrante': 'X', 'principal': 'Y', 'postre': 'Z'},
        'estilo': 'molecular',
        'tradicion': 'francesa',
        'exito': True,
        'fallos_detectados': [],
        'reparaciones_aplicadas': [],
        'satisfaction_score': 4.5,
        'satisfaction_per_menu': {'entrante': 5.0, 'principal': 4.0, 'postre': 4.5},
        'rating_timestamp': '2026-01-07T10:00:00',
        'modification_count': 3
    }
    
    print("\n[TEST] Cargando caso nuevo (con campos de satisfacción)...")
    caso_new = Caso.from_dict(new_case_dict)
    
    print(f"✓ Caso cargado correctamente: {caso_new.id}")
    print(f"  satisfaction_score: {caso_new.satisfaction_score}")
    print(f"  satisfaction_per_menu: {caso_new.satisfaction_per_menu}")
    print(f"  modification_count: {caso_new.modification_count}")
    
    # Test serialization
    print("\n[TEST] Probando serialización...")
    caso_dict_back = caso.to_dict()
    print(f"✓ Caso antiguo serializado (campos opcionales omitidos)")
    
    caso_new_dict_back = caso_new.to_dict()
    print(f"✓ Caso nuevo serializado (todos los campos presentes)")
    
    print("\n✓ Compatibilidad hacia atrás verificada")


def main():
    """Run all demos."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Demo del Sistema de Retención CBR')
    parser.add_argument('--demo', type=int, choices=[1, 2, 3, 4], 
                       help='Ejecutar demo específico (1-4), o todos si no se especifica')
    
    args = parser.parse_args()
    
    demos = {
        1: ("Retención Básica con Calificación", demo_basic_retention),
        2: ("Curación de Memoria", demo_memory_curation),
        3: ("Estadísticas de Retención", demo_retention_statistics),
        4: ("Compatibilidad Hacia Atrás", demo_backward_compatibility),
    }
    
    if args.demo:
        # Run specific demo
        title, func = demos[args.demo]
        print(f"\n{'='*80}")
        print(f"EJECUTANDO: {title}")
        print(f"{'='*80}")
        func()
    else:
        # Run all demos
        print("\n" + "="*80)
        print("DEMOS DEL SISTEMA DE RETENCIÓN CBR")
        print("="*80)
        print("\nEjecutando todos los demos...")
        
        for num, (title, func) in demos.items():
            try:
                func()
                print(f"\n✓ Demo {num} completado")
            except Exception as e:
                print(f"\n✗ Demo {num} falló: {e}")
                import traceback
                traceback.print_exc()
            
            if num < len(demos):
                input("\n[Presione Enter para continuar al siguiente demo...]")
    
    print("\n" + "="*80)
    print("DEMOS COMPLETADOS")
    print("="*80)


if __name__ == "__main__":
    main()
