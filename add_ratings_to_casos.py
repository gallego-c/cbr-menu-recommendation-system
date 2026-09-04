"""
Script para añadir satisfaction_score a todos los casos existentes en casos.json
"""
import json
import random
from datetime import datetime, timedelta

# Configuración
CASOS_JSON = "conocimiento/casos.json"

# Cargar casos
with open(CASOS_JSON, 'r', encoding='utf-8') as f:
    casos = json.load(f)

# Añadir ratings a cada caso que no lo tenga
casos_modificados = 0
base_date = datetime(2025, 11, 1)  # Fecha base para generar timestamps

for i, caso in enumerate(casos):
    if 'satisfaction_score' not in caso or caso['satisfaction_score'] is None:
        # Generar rating basado en características del caso
        # Casos exitosos: ratings entre 3.5 y 5.0
        # Consideraciones adicionales:
        # - Casos con reparaciones: ratings ligeramente más bajos (3.5-4.3)
        # - Casos sin reparaciones: ratings más altos (4.0-5.0)
        # - Algunos casos "problemáticos" con ratings bajos (2.5-3.5) para demostrar el sistema
        
        if caso.get('exito', True):
            if caso.get('reparaciones_aplicadas') and len(caso['reparaciones_aplicadas']) > 0:
                # Con reparaciones: rating medio-alto
                rating = round(random.uniform(3.5, 4.3), 1)
            else:
                # Sin reparaciones: rating alto
                # 80% ratings altos (4.0-5.0), 20% ratings medios (3.5-4.0)
                if random.random() < 0.8:
                    rating = round(random.uniform(4.0, 5.0), 1)
                else:
                    rating = round(random.uniform(3.5, 4.0), 1)
                    
            # Algunos casos excepcionales con rating bajo (10% de probabilidad)
            if random.random() < 0.1 and i % 5 == 0:
                rating = round(random.uniform(2.5, 3.5), 1)
        else:
            # Casos no exitosos: ratings bajos
            rating = round(random.uniform(2.0, 3.5), 1)
        
        # Asegurar que el rating está en el rango 1.0-5.0
        rating = max(1.0, min(5.0, rating))
        
        # Añadir rating y timestamp
        caso['satisfaction_score'] = rating
        
        # Generar timestamp realista (últimos 2 meses)
        days_ago = random.randint(0, 60)
        rating_date = base_date + timedelta(days=days_ago, 
                                           hours=random.randint(0, 23),
                                           minutes=random.randint(0, 59))
        caso['rating_timestamp'] = rating_date.isoformat()
        
        # Añadir modification_count si tiene reparaciones
        if caso.get('reparaciones_aplicadas'):
            caso['modification_count'] = len(caso['reparaciones_aplicadas'])
        else:
            caso['modification_count'] = 0
        
        casos_modificados += 1
        print(f"Caso {caso['id']}: rating={rating}, timestamp={caso['rating_timestamp']}")

# Guardar casos actualizados
with open(CASOS_JSON, 'w', encoding='utf-8') as f:
    json.dump(casos, f, indent=2, ensure_ascii=False)

print(f"\n✅ Proceso completado: {casos_modificados} casos actualizados con ratings")
print(f"   Total de casos: {len(casos)}")

# Estadísticas de ratings
ratings = [c.get('satisfaction_score', 0) for c in casos if c.get('satisfaction_score')]
if ratings:
    print(f"\nEstadísticas de ratings:")
    print(f"   Rating promedio: {sum(ratings)/len(ratings):.2f}")
    print(f"   Rating mínimo: {min(ratings):.1f}")
    print(f"   Rating máximo: {max(ratings):.1f}")
    print(f"   Ratings >= 4.0: {sum(1 for r in ratings if r >= 4.0)} casos ({sum(1 for r in ratings if r >= 4.0)/len(ratings)*100:.1f}%)")
    print(f"   Ratings < 3.5: {sum(1 for r in ratings if r < 3.5)} casos ({sum(1 for r in ratings if r < 3.5)/len(ratings)*100:.1f}%)")
