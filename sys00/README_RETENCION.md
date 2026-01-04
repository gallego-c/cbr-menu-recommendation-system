# Sistema de Retención de Casos (Memory Curation)

## Visión General

Este documento describe el sistema de retención de casos implementado en `sys00/`, que gestiona la curación de memoria para mantener una base de casos de alta calidad, diversa y dentro de límites de capacidad.

## Características Principales

### 1. **Satisfacción del Usuario**
- **Rating interactivo**: Después de generar menús válidos, el sistema solicita al usuario que puntúe cada menú.
- **Escala configurable**: Por defecto 1-5, ajustable en configuración.
- **Modo no-interactivo**: Fallback seguro cuando no hay terminal interactiva (CI/CD, scripts).
- **Política flexible**: Puede requerir rating para guardar o permitir casos sin rating.

### 2. **Curación de Memoria (Remember vs Forget)**
- **Límite de casos**: Configurable (default: 100 casos).
- **Estrategia multi-criterio**:
  - **Satisfacción** (weight=0.4): Casos mejor puntuados tienen prioridad.
  - **Modificaciones** (weight=0.3): Casos difíciles de obtener (muchas reparaciones) se priorizan.
  - **Novedad** (weight=0.3): Se favorece la diversidad para cubrir más espacio de soluciones.
- **Eliminación inteligente**:
  1. Identifica clusters de casi-duplicados (similitud > 0.9), mantiene el mejor de cada grupo.
  2. Si aún excede el límite, elimina casos con menor `keep_score` global.

### 3. **Priorización de Casos Difíciles**
Los casos que requirieron muchas modificaciones se valoran más:
- Se cuenta el número total de modificaciones aplicadas.
- Se usa `log(1 + count)` para calcular un bonus normalizado.
- Estos casos representan zonas del espacio de soluciones difíciles de alcanzar con el modificador.

### 4. **Backward Compatibility**
- Casos antiguos sin campos de satisfacción/modificaciones se cargan correctamente.
- Los campos nuevos (`satisfaccion`, `modification_count`) son opcionales (default: `None`).
- El sistema maneja gracefully casos con y sin ratings.

## Arquitectura

### Módulos Principales

```
sys00/actualizador/
├── config_retencion.py          # Configuración del sistema
├── recolector_satisfaccion.py   # Recolección de ratings CLI
├── similitud_casos.py            # Wrapper de similitud (reusa similitud_ponderada)
├── gestor_retencion.py           # Lógica de curación de memoria
├── gestor_casos.py               # Gestión de casos (integrado con retención)
└── actualizador.py               # Coordinador principal (actualizado)
```

### Esquema de Datos

**Caso (actualizado)**:
```python
{
  "id": "C001",
  "menu": {...},
  "tipo_evento": "boda",
  "temporada": "verano",
  "restricciones": ["vegano"],
  "estilo": "molecular",
  "tradicion": "francesa",
  "exito": true,
  "reparaciones_aplicadas": [...],
  
  // Campos nuevos (opcionales)
  "satisfaccion": {
    "satisfaction_score": 4.5,
    "ratings_por_menu": [...],
    "rating_scale": [1, 5],
    "timestamp": "2026-01-04T...",
    "rating_source": "interactive"
  },
  "modification_count": 3
}
```

## Configuración

### Archivo: `sys00/conocimiento/config_retencion.json`

```json
{
  "max_cases": 100,
  "weight_satisfaction": 0.4,
  "weight_modifications": 0.3,
  "weight_novelty": 0.3,
  "similarity_duplicate_threshold": 0.9,
  "rating_scale_min": 1,
  "rating_scale_max": 5,
  "require_rating_for_retention": false,
  "default_satisfaction_on_skip": null
}
```

### Parámetros

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `max_cases` | 100 | Límite máximo de casos en memoria |
| `weight_satisfaction` | 0.4 | Peso de satisfacción en keep_score |
| `weight_modifications` | 0.3 | Peso de modificaciones en keep_score |
| `weight_novelty` | 0.3 | Peso de novedad en keep_score |
| `similarity_duplicate_threshold` | 0.9 | Umbral para considerar casos casi-duplicados |
| `rating_scale_min` | 1 | Mínimo de la escala de rating |
| `rating_scale_max` | 5 | Máximo de la escala de rating |
| `require_rating_for_retention` | false | Si `true`, solo guarda casos con rating |
| `default_satisfaction_on_skip` | null | Valor por defecto si usuario salta rating |

## Flujo de Uso

### 1. Generación de Menú con Rating (Modo Normal)

```python
from sistema_cbr import SistemaCBR, PreferenciasUsuario, ConfiguracionCBR
from actualizador import ConfiguracionRetencion

# Configurar sistema con retención
config_ret = ConfiguracionRetencion(
    max_cases=50,
    weight_modifications=0.4  # Priorizar casos difíciles
)

config_cbr = ConfiguracionCBR(
    config_retencion=config_ret,
    habilitar_ratings=True
)

sistema = SistemaCBR(config_cbr)

# Generar menú
preferencias = PreferenciasUsuario(
    tipo_evento='boda',
    temporada='verano',
    restricciones=['vegano'],
    estilo='molecular',
    tradicion='francesa'
)

resultado = sistema.generar_menu(preferencias)

# Si el menú es válido, el sistema:
# 1. Mostrará el menú generado
# 2. Pedirá rating al usuario (1-5 o 's' para saltar)
# 3. Calculará keep_score con satisfacción + modificaciones + novedad
# 4. Aplicará curación si se excede el límite
# 5. Guardará el caso si cumple criterios
```

### 2. Modo No-Interactivo (Sin Rating)

```python
# Deshabilitar ratings para scripts/CI
config_cbr = ConfiguracionCBR(
    habilitar_ratings=False
)

sistema = SistemaCBR(config_cbr)
resultado = sistema.generar_menu(preferencias)
# No pedirá rating, guardará sin satisfacción
```

### 3. Uso Programático del Actualizador

```python
from actualizador import ActualizadorConocimiento, ConfiguracionRetencion
from conocimiento import Menu

actualizador = ActualizadorConocimiento(
    config_retencion=ConfiguracionRetencion(max_cases=30)
)

menu = Menu(
    entrante='Ensalada César',
    principal='Pollo al horno',
    postre='Tarta de manzana'
)

# Con rating automático
resultado = actualizador.recolectar_y_procesar_con_rating(
    menu=menu,
    tipo_evento='familiar',
    temporada='verano',
    restricciones=[],
    estilo='clasico',
    tradicion='catalana',
    reparaciones_aplicadas=[...]
)

# resultado contiene:
# - caso_guardado: bool
# - satisfaccion: dict
# - actualizaciones: dict
```

## Métricas y Logging

### Keep Score
La puntuación de retención se calcula como:

```
keep_score = wS * satisfaction_norm + wM * modification_bonus + wN * novelty

donde:
- satisfaction_norm ∈ [0, 1] (normalizado desde escala de rating)
- modification_bonus = log(1 + count) / log(11)  ∈ [0, 1]
- novelty = 1 - max_similarity(caso, memoria)  ∈ [0, 1]
```

### Logs de Retención

El sistema imprime logs detallados:

```
[Retención] Memoria excedida: 105/100 casos. Iniciando curación...
[Retención]   Encontrados 2 clusters de casi-duplicados
[Retención]     Duplicado: C042 -> manteniendo C041
[Retención]   Eliminando caso C023 (keep_score=0.423, sat=0.40, mod=0.15, nov=0.60)
[Retención] Curación completada: 100 casos retenidos, 5 eliminados
```

## Similitud de Casos

### Decisión de Diseño

**REUSAMOS** la similitud ponderada existente (`recuperador/similitud_ponderada.py`):
- ✅ Ya implementada y probada
- ✅ Calcula Jaccard para sets + similitud semántica de ingredientes
- ✅ Devuelve [0,1], determinista
- ✅ Sin dependencias externas
- ✅ Solo necesita un wrapper para garantizar simetría

### Wrapper: `similitud_casos.py`

```python
from actualizador.similitud_casos import SimilitudCasos

sim = SimilitudCasos()

# Comparar dos casos
similitud = sim.similarity(caso_a, caso_b)  # [0, 1]

# Calcular novedad
novedad = sim.novelty(caso_nuevo, casos_memoria)  # [0, 1]

# Encontrar clusters de duplicados
clusters = sim.find_near_duplicates(casos, threshold=0.9)
```

### Características Verificadas

- **Simetría**: `sim(a,b) ≈ sim(b,a)` (promediando ambas direcciones)
- **Rango**: `0.0 ≤ sim ≤ 1.0`
- **Sanity check**: Casos idénticos → sim ≈ 1.0
- **Explicabilidad**: `explain_similarity()` devuelve componentes detallados

## Testing

### Ejecutar Tests

```bash
cd sys00/
python test_retencion.py
```

### Cobertura de Tests

1. **Backward Compatibility**: Carga casos antiguos sin satisfacción
2. **Rating Collection (Mock)**: Verifica fallback no-interactivo
3. **Similarity Computation**: Valida cálculo de similitud y novedad
4. **Memory Curation**: Simula curación con límite excedido
5. **Modification Prioritization**: Verifica bonus por modificaciones

### Tests Esperados

```
RESUMEN DE TESTS
============================================================
✅ Backward Compatibility
✅ Rating Collection
✅ Similarity Computation
✅ Memory Curation
✅ Modification Prioritization

Resultado: 5/5 tests pasados
```

## Troubleshooting

### Problema: No se piden ratings

**Causa**: Sistema en modo no-interactivo o ratings deshabilitados.

**Solución**:
```python
config = ConfiguracionCBR(habilitar_ratings=True)
# Asegurar que hay terminal interactiva (sys.stdin.isatty())
```

### Problema: Casos no se guardan

**Causa 1**: `require_rating_for_retention=True` y usuario saltó rating.

**Solución**: Cambiar a `False` o proporcionar `default_satisfaction_on_skip`.

**Causa 2**: Keep_score muy bajo, memoria llena.

**Solución**: Incrementar `max_cases` o ajustar pesos para favorecer este tipo de caso.

### Problema: Muchos casos eliminados

**Causa**: `max_cases` muy bajo o muchos duplicados.

**Solución**:
- Incrementar `max_cases`
- Verificar que los casos sean suficientemente diversos
- Ajustar `similarity_duplicate_threshold` (default 0.9)

## Ejemplo de Sesión Interactiva

```
FASE 4: ACTUALIZACIÓN DE LA BASE DE CASOS
======================================================================

--- Guardando platos nuevos ---
  ✓ Platos guardados correctamente

--- Validación del menú seleccionado ---
✓ El menú seleccionado es completamente válido

--- Actualizando base de casos ---

Actualizando base de casos...

==================================================
📊 RECOLECCIÓN DE SATISFACCIÓN
==================================================

──────────────────────────────────────────────────
📋 MENÚ GENERADO
──────────────────────────────────────────────────
  🥗 Entrante:  Bruschetta De Verano
  🍽️  Principal: Salsa Pomodoro E Basilico Fresco
  🍰 Postre:    Biscotti Italianos
──────────────────────────────────────────────────
⭐ Puntúa este menú (1-5, 's' para saltar): 4
  ✅ Rating: 4.0/5

[Retención] Agregando caso nuevo: C108
[Retención] Memoria OK: 98/100 casos

AGREGANDO NUEVO CASO: C108
  - Keep score: 0.687
  - Satisfacción (norm): 0.75
  - Bonus modificaciones: 0.48
  - Novedad: 0.82
Caso C108 agregado exitosamente

Nuevo caso agregado con rating: C108
```

## Tunning de Pesos

### Escenario 1: Priorizar Satisfacción del Usuario

```json
{
  "weight_satisfaction": 0.6,
  "weight_modifications": 0.2,
  "weight_novelty": 0.2
}
```

### Escenario 2: Priorizar Casos Difíciles (Muchas Modificaciones)

```json
{
  "weight_satisfaction": 0.2,
  "weight_modifications": 0.5,
  "weight_novelty": 0.3
}
```

### Escenario 3: Maximizar Diversidad

```json
{
  "weight_satisfaction": 0.2,
  "weight_modifications": 0.2,
  "weight_novelty": 0.6
}
```

### Escenario 4: Balanceado (Default)

```json
{
  "weight_satisfaction": 0.4,
  "weight_modifications": 0.3,
  "weight_novelty": 0.3
}
```

## Comandos Rápidos

### Ejecutar sistema con ratings
```bash
cd sys00/
python sistema_cbr.py  # O el script de entrada que uses
```

### Ejecutar tests
```bash
cd sys00/
python test_retencion.py
```

### Forzar curación manual (desde Python)
```python
from actualizador import ActualizadorConocimiento

act = ActualizadorConocimiento()
casos_actuales, ids_eliminados = act.gestor_casos.forzar_curacion()
print(f"Casos retenidos: {casos_actuales}, Eliminados: {ids_eliminados}")
```

### Ver resumen de memoria
```python
resumen = act.gestor_casos.obtener_resumen_memoria()
print(resumen)
```

## Próximos Pasos / Extensiones

1. **Análisis de Tendencias**: Tracking de satisfacción promedio over time.
2. **Ajuste Automático de Pesos**: Aprender pesos óptimos según feedback.
3. **Clustering Avanzado**: Usar k-means para identificar regiones del espacio de soluciones.
4. **Export/Import**: Facilitar backup y migración de casos con metadata completa.

## Referencias

- Esquema de Caso: `sys00/conocimiento/models.py`
- Configuración: `sys00/actualizador/config_retencion.py`
- Tests: `sys00/test_retencion.py`
- Sistema principal: `sys00/sistema_cbr.py`
