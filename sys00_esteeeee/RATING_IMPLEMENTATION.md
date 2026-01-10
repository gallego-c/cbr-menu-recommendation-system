# Implementación del Sistema de Rating para CBR

## Descripción General

Se ha implementado un sistema de rating (calificación 1-5) para cada caso en la base de conocimiento del sistema CBR. Este sistema permite que el modelo aprenda de la calidad de los casos y favorezca aquellos con mejor rating.

## Componentes Modificados

### 1. Base de Datos de Casos (`conocimiento/casos.json`)
Todos los casos ahora incluyen:
- `satisfaction_score`: Rating de 1 a 5 que indica la calidad del caso
- `rating_timestamp`: Fecha y hora del rating
- `modification_count`: Número de modificaciones aplicadas al caso

**Distribución de ratings iniciales:**
- 72% de casos con rating ≥ 4.0 (casos de alta calidad)
- 8% de casos con rating < 3.5 (casos problemáticos)
- Rating promedio: 4.21

### 2. Módulo de Similitud (`recuperador/similitud_ponderada.py`)

**Modificaciones realizadas:**

#### Clase `PesosSimilitud`
- Nuevo peso: `rating_quality: float = 0.05` (5% del peso total)
- Se ajustaron otros pesos proporcionalmente para mantener suma = 1.0

#### Clase `CalculadorSimilitudPonderada`
- Nuevo parámetro: `enable_rating_boost: bool = True`

**Nuevos métodos:**

1. **`_similitud_rating(caso_base: Dict) -> float`**
   - Convierte el rating (1-5) a similitud normalizada (0-1)
   - Sin rating: retorna 0.6 (neutral)
   - Fórmula: `(rating - 1.0) / 4.0`

2. **`_calcular_boost_rating(caso_base: Dict) -> float`**
   - Aplica boost/penalización multiplicativa según el rating:
     - Rating ≥ 4.5: boost +15% (factor 1.15)
     - Rating 4.0-4.5: boost +7% (factor 1.07)
     - Rating 3.5-4.0: neutral (factor 1.0)
     - Rating 3.0-3.5: penalización -5% (factor 0.95)
     - Rating < 3.0: penalización -15% (factor 0.85)

**Cálculo de similitud final:**
```python
similitud_base = suma_ponderada_de_componentes
if enable_rating_boost:
    similitud_total = similitud_base * boost_factor
```

### 3. Sistema CBR Principal (`sistema_cbr.py`)

**Nuevos métodos:**

1. **`recolectar_y_guardar_rating(menu, caso_id, guardar_en_base=True)`**
   - Recolecta el rating del usuario usando `RatingCollector`
   - Guarda el rating en la base de casos si se especifica
   - Retorna el rating recolectado

2. **`_actualizar_rating_caso(caso_id, rating, per_menu_scores, timestamp)`**
   - Actualiza el archivo `casos.json` con el nuevo rating
   - Recarga la base de casos en el recuperador
   - Manejo robusto de errores

### 4. Interfaz de Usuario (`menu_interactivo.py`)

**Nueva función:**
- **`preguntar_rating_menu(menu, caso_id=None)`**
  - Pregunta al usuario si desea calificar el menú
  - Solicita calificación del 1 al 5
  - Validación de entrada con reintentos
  - Mensajes descriptivos de las escalas

**Modificación en `main()`:**
- Después de generar un menú exitoso, pregunta por el rating
- Guarda el rating automáticamente en la base de casos
- Usa una instancia persistente de `SistemaCBR` para toda la sesión

### 5. API Simplificada (`cbr_limpio.py`)

**Modificaciones en `generar_menu_simple()`:**
- Nuevo parámetro: `recolectar_rating=False`
- Si `recolectar_rating=True`, recolecta y guarda el rating
- Retorna el rating en el diccionario de resultado: `resultado_dict['rating']`

## Flujo de Uso

### Uso Interactivo (menu_interactivo.py)
```bash
python menu_interactivo.py
```
1. El usuario ingresa sus preferencias
2. El sistema genera un menú
3. Se muestra el menú al usuario
4. Se pregunta si desea calificar el menú (s/n)
5. Si acepta, califica del 1 al 5
6. El rating se guarda en el caso base usado

### Uso Programático (cbr_limpio.py)
```python
from cbr_limpio import generar_menu_simple

# Sin rating
resultado = generar_menu_simple(
    tipo_evento='familiar',
    temporada='verano',
    restricciones=['vegetariano'],
    estilo='clasico',
    tradicion='italiana'
)

# Con rating interactivo
resultado = generar_menu_simple(
    tipo_evento='familiar',
    temporada='verano',
    restricciones=['vegetariano'],
    estilo='clasico',
    tradicion='italiana',
    recolectar_rating=True
)
print(f"Rating recibido: {resultado.get('rating')}")
```

## Impacto en la Recuperación de Casos

El sistema de rating afecta la recuperación de casos en dos niveles:

### 1. Componente de similitud (5% del peso total)
```
sim_rating = (rating - 1.0) / 4.0
contribución = 0.05 * sim_rating
```

### 2. Factor de boost multiplicativo
```
similitud_final = similitud_base * boost_factor
```

**Ejemplo práctico:**

Caso A: similitud_base = 0.80, rating = 4.8
- boost_factor = 1.15
- similitud_final = 0.80 * 1.15 = 0.92

Caso B: similitud_base = 0.82, rating = 2.5
- boost_factor = 0.85
- similitud_final = 0.82 * 0.85 = 0.697

Aunque B tenía mayor similitud base, A es seleccionado por su alto rating.

## Correspondencia con el Enunciado

Esta implementación corresponde al **apartado (c) de la extensión avanzada**:

> **Aprendizaje y evolución de la base de casos**: Añadid un componente de meta-aprendizaje que actualice el conocimiento del sistema a partir del feedback de los usuarios (p. ej. puntuaciones de satisfacción, éxito o rechazo de las propuestas), reorganizando la base de casos y refinando los pesos de similitud.

**Elementos implementados:**
1. ✅ **Feedback del usuario**: Sistema de rating 1-5
2. ✅ **Actualización del conocimiento**: Ratings se guardan en casos.json
3. ✅ **Reorganización de la base**: Casos con mejor rating tienen mayor prioridad en recuperación
4. ✅ **Refinamiento de similitud**: Los ratings modifican la similitud calculada mediante boost/penalización

## Validación y Pruebas

Para probar el sistema:

1. **Verificar ratings existentes:**
```bash
python -c "import json; casos = json.load(open('conocimiento/casos.json')); print(f'Casos con rating: {sum(1 for c in casos if c.get(\"satisfaction_score\"))}')"
```

2. **Ejecutar el sistema interactivo:**
```bash
python menu_interactivo.py
```

3. **Verificar que ratings afecten la recuperación:**
   - Generar múltiples menús con mismas preferencias
   - Observar que casos con rating alto aparecen primero
   - Dar rating bajo a un caso y verificar que baje en el ranking

## Notas Técnicas

- Los ratings son **retrocompatibles**: casos sin rating tienen comportamiento neutral
- El sistema usa `RatingCollector` del módulo `actualizador`
- La persistencia es inmediata: el rating se guarda apenas se ingresa
- El recuperador recarga automáticamente los casos después de actualizar ratings

## Futuras Mejoras

1. **Decay temporal**: Reducir peso de ratings antiguos
2. **Ajuste automático de pesos**: Aprender pesos óptimos según ratings históricos
3. **Clustering de preferencias**: Agrupar usuarios con gustos similares
4. **Explicabilidad**: Mostrar por qué un caso tiene rating alto/bajo
