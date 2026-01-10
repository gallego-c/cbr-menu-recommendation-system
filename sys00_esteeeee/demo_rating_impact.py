"""
Demo avanzada del sistema de rating - Muestra cómo los ratings afectan la recuperación
"""
from sistema_cbr import SistemaCBR, PreferenciasUsuario
from recuperador.similitud_ponderada import CalculadorSimilitudPonderada
import json

print("="*80)
print("DEMOSTRACIÓN AVANZADA: IMPACTO DEL RATING EN LA RECUPERACIÓN DE CASOS")
print("="*80)

# Cargar casos para análisis
with open('conocimiento/casos.json', 'r', encoding='utf-8') as f:
    casos = json.load(f)

# Mostrar distribución de ratings
print("\n1. DISTRIBUCIÓN DE RATINGS EN LA BASE DE CASOS")
print("-"*80)

ratings_dict = {}
for caso in casos:
    rating = caso.get('satisfaction_score')
    if rating:
        rating_range = f"{int(rating)}-{int(rating)+0.9:.1f}"
        if rating >= 4.5:
            rating_range = "4.5-5.0 (Excelente)"
        elif rating >= 4.0:
            rating_range = "4.0-4.4 (Bueno)"
        elif rating >= 3.5:
            rating_range = "3.5-3.9 (Regular)"
        elif rating >= 3.0:
            rating_range = "3.0-3.4 (Bajo)"
        else:
            rating_range = "< 3.0 (Muy bajo)"
        
        ratings_dict[rating_range] = ratings_dict.get(rating_range, 0) + 1

for rango, count in sorted(ratings_dict.items(), reverse=True):
    barra = "█" * (count * 2)
    print(f"  {rango:20s} | {barra} ({count} casos)")

# Demostración de recuperación
print("\n2. RECUPERACIÓN CON RATING vs SIN RATING")
print("-"*80)

# Crear consulta de ejemplo
consulta = {
    'tipo_evento': 'familiar',
    'temporada': 'verano',
    'restricciones': [],
    'estilo': 'clasico',
    'tradicion': 'catalana'
}

print(f"\nConsulta:")
print(f"  Tipo: {consulta['tipo_evento']}")
print(f"  Temporada: {consulta['temporada']}")
print(f"  Tradición: {consulta['tradicion']}")

# Recuperar CON rating boost
print("\n┌─ CON RATING BOOST (sistema actual) ─────────────────────────────────┐")
calc_con_rating = CalculadorSimilitudPonderada(enable_rating_boost=True)
resultados_con = []
for caso in casos:
    sim = calc_con_rating.similitud_casos(consulta, caso)
    resultados_con.append({
        'id': caso['id'],
        'similitud': sim,
        'rating': caso.get('satisfaction_score', 'N/A')
    })

resultados_con.sort(key=lambda x: x['similitud'], reverse=True)

print("\nTop 5 casos recuperados:")
for i, caso in enumerate(resultados_con[:5], 1):
    rating_str = f"{caso['rating']:.1f}" if isinstance(caso['rating'], float) else "N/A"
    print(f"  {i}. {caso['id']:5s} | Similitud: {caso['similitud']:.4f} | Rating: {rating_str}")

# Recuperar SIN rating boost
print("\n└─ SIN RATING BOOST (sistema tradicional) ───────────────────────────┐")
calc_sin_rating = CalculadorSimilitudPonderada(enable_rating_boost=False)
resultados_sin = []
for caso in casos:
    sim = calc_sin_rating.similitud_casos(consulta, caso)
    resultados_sin.append({
        'id': caso['id'],
        'similitud': sim,
        'rating': caso.get('satisfaction_score', 'N/A')
    })

resultados_sin.sort(key=lambda x: x['similitud'], reverse=True)

print("\nTop 5 casos recuperados:")
for i, caso in enumerate(resultados_sin[:5], 1):
    rating_str = f"{caso['rating']:.1f}" if isinstance(caso['rating'], float) else "N/A"
    print(f"  {i}. {caso['id']:5s} | Similitud: {caso['similitud']:.4f} | Rating: {rating_str}")

# Análisis comparativo
print("\n3. ANÁLISIS COMPARATIVO")
print("-"*80)

# Comparar top 3 de cada sistema
print("\nCambios en el ranking por efecto del rating:")
for i in range(min(3, len(resultados_con))):
    caso_con = resultados_con[i]
    
    # Buscar posición del mismo caso sin rating
    pos_sin = next((j for j, c in enumerate(resultados_sin) if c['id'] == caso_con['id']), -1)
    
    if pos_sin != i:
        cambio = pos_sin - i
        direccion = "↑" if cambio > 0 else "↓"
        rating_str = f"{caso_con['rating']:.1f}" if isinstance(caso_con['rating'], float) else "N/A"
        print(f"  • {caso_con['id']} (rating {rating_str}): posición {pos_sin+1} → {i+1} {direccion}")

# Estadísticas
ratings_top3_con = [c['rating'] for c in resultados_con[:3] if isinstance(c['rating'], float)]
ratings_top3_sin = [c['rating'] for c in resultados_sin[:3] if isinstance(c['rating'], float)]

if ratings_top3_con and ratings_top3_sin:
    print(f"\nRating promedio top 3:")
    print(f"  Con rating boost:  {sum(ratings_top3_con)/len(ratings_top3_con):.2f}")
    print(f"  Sin rating boost:  {sum(ratings_top3_sin)/len(ratings_top3_sin):.2f}")

print("\n4. CONCLUSIÓN")
print("-"*80)
print("""
El sistema de rating tiene un impacto significativo en la recuperación:

1. Los casos con rating alto (≥4.5) reciben un boost del +15% en similitud
2. Los casos con rating bajo (<3.0) reciben penalización del -15%
3. Esto favorece la recuperación de casos de mayor calidad
4. El sistema aprende de la experiencia previa (feedback del usuario)

El componente de rating representa el 5% del peso de similitud base, y además
se aplica un factor multiplicativo que amplifica el efecto en la selección final.
""")

print("="*80)
print("DEMOSTRACIÓN COMPLETADA")
print("="*80)
print("\nPara probar interactivamente:")
print("  python menu_interactivo.py")
