"""
Script de demostración simplificado del sistema de rating
Muestra un ejemplo completo sin requerir interacción
"""
from sistema_cbr import SistemaCBR, PreferenciasUsuario
import json

print("="*80)
print("DEMO: SISTEMA CBR CON RATING - FLUJO COMPLETO")
print("="*80)

# 1. Mostrar estadísticas iniciales
print("\n📊 ESTADÍSTICAS INICIALES DE LA BASE DE CASOS")
print("-"*80)

with open('conocimiento/casos.json', 'r', encoding='utf-8') as f:
    casos = json.load(f)

ratings = [c.get('satisfaction_score') for c in casos if c.get('satisfaction_score')]
print(f"  Total de casos: {len(casos)}")
print(f"  Casos con rating: {len(ratings)}")
print(f"  Rating promedio: {sum(ratings)/len(ratings):.2f}/5.00")
print(f"  Casos de alta calidad (≥4.0): {sum(1 for r in ratings if r >= 4.0)} ({sum(1 for r in ratings if r >= 4.0)/len(ratings)*100:.0f}%)")

# 2. Generar un menú
print("\n🍽️  GENERANDO MENÚ CON SISTEMA CBR")
print("-"*80)

sistema = SistemaCBR()

preferencias = PreferenciasUsuario(
    tipo_evento='familiar',
    temporada='verano',
    restricciones=[],
    estilo='clasico',
    tradicion='catalana'
)

print(f"\nPreferencias del usuario:")
print(f"  • Tipo de evento: {preferencias.tipo_evento}")
print(f"  • Temporada: {preferencias.temporada}")
print(f"  • Tradición: {preferencias.tradicion}")
print(f"  • Estilo: {preferencias.estilo}")

print("\n⏳ Procesando...")

# Suprimir salida del sistema
import sys
import io
old_stdout = sys.stdout
sys.stdout = io.StringIO()

resultado = sistema.generar_menu(preferencias)

sys.stdout = old_stdout

if resultado.exito:
    print("\n✅ MENÚ GENERADO CON ÉXITO")
    print("-"*80)
    print(f"\n  Entrante:  {resultado.menu['entrante']}")
    print(f"  Principal: {resultado.menu['principal']}")
    print(f"  Postre:    {resultado.menu['postre']}")
    
    print(f"\n📈 Información del caso base:")
    print(f"  • ID: {resultado.caso_base_id}")
    print(f"  • Similitud: {resultado.similitud_caso_base:.3f}")
    
    # Buscar el rating del caso base
    caso_base = next((c for c in casos if c['id'] == resultado.caso_base_id), None)
    if caso_base and caso_base.get('satisfaction_score'):
        print(f"  • Rating del caso base: {caso_base['satisfaction_score']:.1f}/5.0")
        
        # Mostrar el boost que recibió
        from recuperador.similitud_ponderada import CalculadorSimilitudPonderada
        calc = CalculadorSimilitudPonderada()
        boost = calc._calcular_boost_rating(caso_base)
        boost_pct = (boost - 1.0) * 100
        if boost_pct > 0:
            print(f"  • Boost por rating: +{boost_pct:.0f}%")
        elif boost_pct < 0:
            print(f"  • Penalización por rating: {boost_pct:.0f}%")
        else:
            print(f"  • Factor de rating: neutral")
    
    # 3. Simular recolección de rating
    print("\n🌟 SIMULANDO RECOLECCIÓN DE RATING")
    print("-"*80)
    print("  En modo interactivo, aquí se preguntaría al usuario:")
    print("    '¿Te gustaría calificar este menú? (s/n)'")
    print("    'Tu calificación (1-5): ___'")
    print("\n  Para probar esto en modo real, ejecuta:")
    print("    python menu_interactivo.py")
    
else:
    print(f"\n❌ ERROR: {resultado.mensaje}")

# 4. Mostrar top 3 casos por rating
print("\n🏆 TOP 3 CASOS POR RATING")
print("-"*80)

casos_ordenados = sorted(
    [c for c in casos if c.get('satisfaction_score')],
    key=lambda x: x['satisfaction_score'],
    reverse=True
)

for i, caso in enumerate(casos_ordenados[:3], 1):
    print(f"\n{i}. Caso {caso['id']} - Rating: {caso['satisfaction_score']:.1f}/5.0")
    print(f"   Tipo: {caso['tipo_evento']}, Tradición: {caso['tradicion']}")
    print(f"   Entrante: {caso['menu']['entrante']}")

# 5. Mostrar comparativa de recuperación
print("\n📊 IMPACTO DEL RATING EN LA RECUPERACIÓN")
print("-"*80)

from recuperador.similitud_ponderada import CalculadorSimilitudPonderada

calc_con = CalculadorSimilitudPonderada(enable_rating_boost=True)
calc_sin = CalculadorSimilitudPonderada(enable_rating_boost=False)

consulta = {
    'tipo_evento': 'familiar',
    'temporada': 'verano',
    'restricciones': [],
    'estilo': 'clasico',
    'tradicion': 'catalana'
}

# Caso con rating alto
caso_alto = next((c for c in casos if c.get('satisfaction_score', 0) >= 4.5), None)
if caso_alto:
    sim_con = calc_con.similitud_casos(consulta, caso_alto)
    sim_sin = calc_sin.similitud_casos(consulta, caso_alto)
    print(f"\nCaso {caso_alto['id']} (rating {caso_alto['satisfaction_score']:.1f}):")
    print(f"  Sin rating: similitud = {sim_sin:.4f}")
    print(f"  Con rating: similitud = {sim_con:.4f} ({(sim_con/sim_sin-1)*100:+.1f}%)")

# Caso con rating bajo
caso_bajo = next((c for c in casos if c.get('satisfaction_score', 5) < 3.5), None)
if caso_bajo:
    sim_con = calc_con.similitud_casos(consulta, caso_bajo)
    sim_sin = calc_sin.similitud_casos(consulta, caso_bajo)
    print(f"\nCaso {caso_bajo['id']} (rating {caso_bajo['satisfaction_score']:.1f}):")
    print(f"  Sin rating: similitud = {sim_sin:.4f}")
    print(f"  Con rating: similitud = {sim_con:.4f} ({(sim_con/sim_sin-1)*100:+.1f}%)")

print("\n" + "="*80)
print("CONCLUSIÓN:")
print("="*80)
print("""
El sistema de rating permite al CBR:
  ✓ Aprender de la experiencia previa (ratings históricos)
  ✓ Favorecer casos de alta calidad en la recuperación
  ✓ Penalizar casos problemáticos o de baja satisfacción
  ✓ Mejorar continuamente con feedback del usuario

Esto corresponde al apartado (c) de la extensión avanzada:
"Aprendizaje y evolución de la base de casos mediante feedback"
""")

print("="*80)
print("Para probar el sistema completo en modo interactivo:")
print("  python menu_interactivo.py")
print("="*80)
