"""
Script de prueba para verificar el sistema de rating
"""
import json

print("="*70)
print("VERIFICACIÓN DEL SISTEMA DE RATING")
print("="*70)

# 1. Verificar que los casos tienen ratings
print("\n1. Verificando casos.json...")
with open('conocimiento/casos.json', 'r', encoding='utf-8') as f:
    casos = json.load(f)

casos_con_rating = [c for c in casos if c.get('satisfaction_score')]
print(f"   ✓ Total de casos: {len(casos)}")
print(f"   ✓ Casos con rating: {len(casos_con_rating)}")

if casos_con_rating:
    ratings = [c['satisfaction_score'] for c in casos_con_rating]
    print(f"   ✓ Rating promedio: {sum(ratings)/len(ratings):.2f}")
    print(f"   ✓ Rating mínimo: {min(ratings):.1f}")
    print(f"   ✓ Rating máximo: {max(ratings):.1f}")

# 2. Verificar que la similitud considera ratings
print("\n2. Verificando módulo de similitud...")
try:
    from recuperador.similitud_ponderada import CalculadorSimilitudPonderada, PesosSimilitud
    
    pesos = PesosSimilitud()
    if hasattr(pesos, 'rating_quality'):
        print(f"   ✓ Peso rating_quality: {pesos.rating_quality}")
    else:
        print("   ✗ ERROR: PesosSimilitud no tiene rating_quality")
    
    calc = CalculadorSimilitudPonderada()
    if hasattr(calc, 'enable_rating_boost'):
        print(f"   ✓ enable_rating_boost disponible: {calc.enable_rating_boost}")
    else:
        print("   ✗ ERROR: CalculadorSimilitudPonderada no tiene enable_rating_boost")
    
    # Verificar métodos
    if hasattr(calc, '_similitud_rating'):
        print("   ✓ Método _similitud_rating existe")
    if hasattr(calc, '_calcular_boost_rating'):
        print("   ✓ Método _calcular_boost_rating existe")
    
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# 3. Verificar SistemaCBR
print("\n3. Verificando sistema_cbr.py...")
try:
    from sistema_cbr import SistemaCBR
    
    sistema = SistemaCBR()
    
    if hasattr(sistema, 'recolectar_y_guardar_rating'):
        print("   ✓ Método recolectar_y_guardar_rating existe")
    else:
        print("   ✗ ERROR: SistemaCBR no tiene recolectar_y_guardar_rating")
    
    if hasattr(sistema, '_actualizar_rating_caso'):
        print("   ✓ Método _actualizar_rating_caso existe")
    else:
        print("   ✗ ERROR: SistemaCBR no tiene _actualizar_rating_caso")
        
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# 4. Verificar cbr_limpio
print("\n4. Verificando cbr_limpio.py...")
try:
    from cbr_limpio import generar_menu_simple
    import inspect
    
    sig = inspect.signature(generar_menu_simple)
    if 'recolectar_rating' in sig.parameters:
        print("   ✓ Parámetro recolectar_rating existe")
    else:
        print("   ✗ ERROR: generar_menu_simple no tiene parámetro recolectar_rating")
        
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# 5. Demostración práctica del boost
print("\n5. Demostrando efecto del rating en similitud...")
try:
    from recuperador.similitud_ponderada import CalculadorSimilitudPonderada
    
    calc = CalculadorSimilitudPonderada()
    
    # Simular dos casos con ratings diferentes
    caso_high_rating = {'satisfaction_score': 4.8}
    caso_low_rating = {'satisfaction_score': 2.5}
    caso_no_rating = {}
    
    boost_high = calc._calcular_boost_rating(caso_high_rating)
    boost_low = calc._calcular_boost_rating(caso_low_rating)
    boost_none = calc._calcular_boost_rating(caso_no_rating)
    
    print(f"   Rating 4.8 → boost factor: {boost_high:.2f} (+{(boost_high-1)*100:.0f}%)")
    print(f"   Rating 2.5 → boost factor: {boost_low:.2f} ({(boost_low-1)*100:.0f}%)")
    print(f"   Sin rating → boost factor: {boost_none:.2f} (neutral)")
    
    # Ejemplo con similitud base
    similitud_base = 0.80
    print(f"\n   Ejemplo con similitud base = {similitud_base:.2f}:")
    print(f"   - Con rating 4.8: {similitud_base * boost_high:.3f}")
    print(f"   - Con rating 2.5: {similitud_base * boost_low:.3f}")
    print(f"   - Sin rating:     {similitud_base * boost_none:.3f}")
    
except Exception as e:
    print(f"   ✗ ERROR: {e}")

print("\n" + "="*70)
print("VERIFICACIÓN COMPLETADA")
print("="*70)
print("\nPara probar el sistema interactivo:")
print("  python menu_interactivo.py")
print("\nPara probar programáticamente:")
print("  python -c \"from cbr_limpio import generar_menu_simple; print(generar_menu_simple())\"")
print()
