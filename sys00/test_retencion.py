"""
Test del Sistema de Retención de Casos
======================================

Script de prueba para validar end-to-end:
1. Carga de casos existentes (backward compatibility)
2. Rating de menús válidos
3. Curación de memoria cuando se excede el límite
4. Priorización de casos con alta satisfacción y modificaciones
"""

import sys
import os

# Añadir directorio padre al path
sys.path.insert(0, os.path.dirname(__file__))

from actualizador import (
    ConfiguracionRetencion, 
    RecolectorSatisfaccion,
    GestorRetencion,
    SimilitudCasos,
    SatisfaccionCaso
)
from conocimiento import Menu, Caso, cargador


def test_backward_compatibility():
    """Test 1: Verificar que casos antiguos sin satisfacción se cargan correctamente."""
    print("="*60)
    print("TEST 1: BACKWARD COMPATIBILITY")
    print("="*60)
    
    # Cargar casos existentes como dicts (no objetos Caso)
    casos_raw = cargador.cargar_json('casos.json')
    print(f"\n✓ Casos cargados (raw): {len(casos_raw)}")
    
    # Convertir a objetos Caso para verificar backward compatibility
    casos = [Caso.from_dict(c) for c in casos_raw[:3]]
    
    # Verificar que se pueden leer casos sin campos nuevos
    for caso in casos:
        print(f"\nCaso {caso.id}:")
        print(f"  - Satisfacción: {caso.satisfaccion}")
        print(f"  - Modification count: {caso.modification_count}")
        print(f"  - Reparaciones aplicadas: {len(caso.reparaciones_aplicadas)}")
    
    print("\n✅ Test backward compatibility PASADO\n")
    return True


def test_rating_collection_mock():
    """Test 2: Simular recolección de ratings (modo mock, no interactivo)."""
    print("="*60)
    print("TEST 2: RECOLECCIÓN DE RATINGS (MOCK)")
    print("="*60)
    
    # Crear configuración no-interactiva
    config = ConfiguracionRetencion(
        interactive_mode=False,
        default_satisfaction_on_skip=3.5,
        rating_scale_min=1,
        rating_scale_max=5
    )
    
    recolector = RecolectorSatisfaccion(config)
    
    # Simular menú
    menu_test = {
        'entrante': 'Ensalada César',
        'principal': 'Pollo al horno',
        'postre': 'Tarta de manzana'
    }
    
    # Recolectar (debe usar default en modo no-interactivo)
    satisfaccion = recolector.recolectar_satisfaccion_caso([menu_test])
    
    print(f"\n✓ Satisfacción recolectada:")
    print(f"  - Score: {satisfaccion.satisfaction_score}")
    print(f"  - Source: {satisfaccion.rating_source}")
    print(f"  - Skipped: {satisfaccion.ratings_por_menu[0].skipped}")
    
    assert satisfaccion.satisfaction_score == 3.5
    assert satisfaccion.rating_source in ('default', 'skipped')  # Both are valid for non-interactive
    
    print("\n✅ Test recolección ratings PASADO\n")
    return True


def test_similarity_computation():
    """Test 3: Verificar cálculo de similitud."""
    print("="*60)
    print("TEST 3: CÁLCULO DE SIMILITUD")
    print("="*60)
    
    similitud = SimilitudCasos()
    
    # Cargar dos casos para comparar
    casos_list = cargador.cargar_json('casos.json')
    
    if len(casos_list) < 2:
        print("⚠️ Necesitamos al menos 2 casos. Creando casos sintéticos...")
        caso_a = {
            'id': 'TEST_A',
            'tipo_evento': 'boda',
            'temporada': 'verano',
            'restricciones': ['vegano'],
            'estilo': 'molecular',
            'tradicion': 'francesa',
            'menu': {
                'entrante': 'Ensalada',
                'principal': 'Pasta',
                'postre': 'Helado'
            }
        }
        caso_b = {
            'id': 'TEST_B',
            'tipo_evento': 'boda',
            'temporada': 'verano',
            'restricciones': ['vegano'],
            'estilo': 'molecular',
            'tradicion': 'francesa',
            'menu': {
                'entrante': 'Ensalada',
                'principal': 'Arroz',
                'postre': 'Fruta'
            }
        }
    else:
        caso_a = casos_list[0]
        caso_b = casos_list[1]
    
    # Calcular similitud
    sim = similitud.similarity(caso_a, caso_b)
    
    print(f"\n✓ Similitud entre {caso_a.get('id')} y {caso_b.get('id')}: {sim:.3f}")
    
    # Verificar que está en rango [0, 1]
    assert 0.0 <= sim <= 1.0, f"Similitud fuera de rango: {sim}"
    
    # Verificar simetría
    sim_inversa = similitud.similarity(caso_b, caso_a)
    assert abs(sim - sim_inversa) < 0.01, f"No simétrica: {sim} vs {sim_inversa}"
    
    print(f"✓ Simetría verificada: sim(a,b) = {sim:.3f}, sim(b,a) = {sim_inversa:.3f}")
    
    # Test novelty
    nov = similitud.novelty(caso_a, [caso_b])
    print(f"✓ Novedad de {caso_a.get('id')} respecto a [{caso_b.get('id')}]: {nov:.3f}")
    
    assert 0.0 <= nov <= 1.0
    
    print("\n✅ Test similitud PASADO\n")
    return True


def test_memory_curation():
    """Test 4: Simular curación de memoria."""
    print("="*60)
    print("TEST 4: CURACIÓN DE MEMORIA")
    print("="*60)
    
    # Crear configuración con límite aceptable (mínimo 10)
    config = ConfiguracionRetencion(
        max_cases=10,
        weight_satisfaction=0.4,
        weight_modifications=0.3,
        weight_novelty=0.3,
        similarity_duplicate_threshold=0.9
    )
    
    gestor = GestorRetencion(config)
    
    # Cargar casos reales
    casos_list = cargador.cargar_json('casos.json')
    
    print(f"\n✓ Casos totales en base: {len(casos_list)}")
    print(f"✓ Límite configurado: {config.max_cases}")
    
    # Tomar casos suficientes para exceder el límite
    num_casos_test = min(15, len(casos_list))  # 15 casos (excede límite de 10)
    casos_test = casos_list[:num_casos_test]
    
    print(f"✓ Casos para test: {len(casos_test)}")
    
    # Simular curación
    casos_retenidos, ids_eliminados = gestor.curar_memoria(casos_test)
    
    print(f"\n✓ Resultado curación:")
    print(f"  - Casos retenidos: {len(casos_retenidos)}")
    print(f"  - Casos eliminados: {len(ids_eliminados)}")
    
    if ids_eliminados:
        print(f"  - IDs eliminados: {ids_eliminados[:3]}...")  # Mostrar solo primeros 3
    
    # Verificar que no excede el límite
    assert len(casos_retenidos) <= config.max_cases, \
        f"Excede límite: {len(casos_retenidos)} > {config.max_cases}"
    
    # Generar resumen
    resumen = gestor.resumen_memoria(casos_retenidos)
    print(f"\n✓ Resumen memoria:")
    print(f"  - Total casos: {resumen['total_casos']}")
    print(f"  - Capacidad usada: {resumen['capacidad_usada']*100:.1f}%")
    print(f"  - Satisfacción promedio: {resumen['satisfaccion_promedio']}")
    print(f"  - Modificaciones promedio: {resumen['modificaciones_promedio']:.1f}")
    print(f"  - Diversidad estimada: {resumen['diversidad_estimada']:.3f}")
    
    print("\n✅ Test curación memoria PASADO\n")
    return True


def test_modification_prioritization():
    """Test 5: Verificar que casos con muchas modificaciones se priorizan."""
    print("="*60)
    print("TEST 5: PRIORIZACIÓN POR MODIFICACIONES")
    print("="*60)
    
    config = ConfiguracionRetencion(
        weight_satisfaction=0.2,
        weight_modifications=0.6,  # Alto peso a modificaciones
        weight_novelty=0.2
    )
    
    gestor = GestorRetencion(config)
    
    # Crear casos sintéticos con diferentes niveles de modificaciones
    caso_bajo_mod = {
        'id': 'LOW_MOD',
        'tipo_evento': 'familiar',
        'temporada': 'verano',
        'restricciones': [],
        'estilo': 'clasico',
        'tradicion': 'catalana',
        'menu': {'entrante': 'A', 'principal': 'B', 'postre': 'C'},
        'reparaciones_aplicadas': [],
        'modification_count': 0,
        'satisfaccion': {'satisfaction_score': 3.0, 'rating_scale': [1, 5]}
    }
    
    caso_alto_mod = {
        'id': 'HIGH_MOD',
        'tipo_evento': 'familiar',
        'temporada': 'verano',
        'restricciones': [],
        'estilo': 'clasico',
        'tradicion': 'catalana',
        'menu': {'entrante': 'X', 'principal': 'Y', 'postre': 'Z'},
        'reparaciones_aplicadas': [
            {'modificaciones': ['mod1', 'mod2', 'mod3']},
            {'modificaciones': ['mod4', 'mod5']}
        ],
        'modification_count': 5,
        'satisfaccion': {'satisfaction_score': 3.0, 'rating_scale': [1, 5]}
    }
    
    # Calcular métricas
    metricas_bajo = gestor.calcular_metricas(caso_bajo_mod, [])
    metricas_alto = gestor.calcular_metricas(caso_alto_mod, [])
    
    print(f"\n✓ Caso con pocas modificaciones:")
    print(f"  - Modification count: {metricas_bajo.modification_count}")
    print(f"  - Modification bonus: {metricas_bajo.modification_bonus:.3f}")
    print(f"  - Keep score: {metricas_bajo.keep_score:.3f}")
    
    print(f"\n✓ Caso con muchas modificaciones:")
    print(f"  - Modification count: {metricas_alto.modification_count}")
    print(f"  - Modification bonus: {metricas_alto.modification_bonus:.3f}")
    print(f"  - Keep score: {metricas_alto.keep_score:.3f}")
    
    # Verificar que el caso con más modificaciones tiene mayor keep_score
    assert metricas_alto.keep_score > metricas_bajo.keep_score, \
        f"El caso con más modificaciones debería tener mayor keep_score"
    
    print(f"\n✓ Diferencia keep_score: {metricas_alto.keep_score - metricas_bajo.keep_score:.3f}")
    
    print("\n✅ Test priorización modificaciones PASADO\n")
    return True


def run_all_tests():
    """Ejecuta todos los tests."""
    print("\n" + "="*60)
    print("INICIANDO BATERÍA DE TESTS DEL SISTEMA DE RETENCIÓN")
    print("="*60 + "\n")
    
    tests = [
        ("Backward Compatibility", test_backward_compatibility),
        ("Rating Collection", test_rating_collection_mock),
        ("Similarity Computation", test_similarity_computation),
        ("Memory Curation", test_memory_curation),
        ("Modification Prioritization", test_modification_prioritization)
    ]
    
    resultados = []
    
    for nombre, test_func in tests:
        try:
            exito = test_func()
            resultados.append((nombre, exito, None))
        except Exception as e:
            print(f"\n❌ Test {nombre} FALLÓ: {e}\n")
            resultados.append((nombre, False, str(e)))
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN DE TESTS")
    print("="*60)
    
    pasados = sum(1 for _, exito, _ in resultados if exito)
    total = len(resultados)
    
    for nombre, exito, error in resultados:
        simbolo = "✅" if exito else "❌"
        print(f"{simbolo} {nombre}")
        if error:
            print(f"   Error: {error}")
    
    print(f"\nResultado: {pasados}/{total} tests pasados")
    
    if pasados == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        return 0
    else:
        print(f"\n⚠️ {total - pasados} test(s) fallaron")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
