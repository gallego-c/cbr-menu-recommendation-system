# CBR Retention System Documentation

## Overview

The CBR Retention/Actualizer system implements intelligent memory management for the Case-Based Reasoning menu generation system. It decides which cases to remember vs forget based on **satisfaction scores**, **modification complexity**, and **diversity/novelty**.

---

## Architecture

### Components

```
actualizador/
├── config_retention.py       # Configuration for retention policies
├── rating_collector.py        # Interactive satisfaction rating collection
├── similarity_adapter.py      # Case-to-case similarity (reuses existing metrics)
├── memory_curator.py          # Retention logic + forgetting decisions
├── actualizador.py            # Main coordinator (updated with retention)
└── gestor_casos.py           # Case persistence (existing)

conocimiento/
└── models.py                  # Updated Caso model with satisfaction fields

sistema_cbr.py                 # Main CBR system (integrated retention)
demo_retention.py              # Comprehensive demo script
```

---

## Key Features

### 1. Satisfaction Scoring
- **Interactive rating collection** after valid menu generation
- **1-5 scale** (configurable) with optional skip
- **Per-menu ratings** (entrante, principal, postre) + aggregate score
- **Non-interactive fallback** with neutral defaults

### 2. Intelligent Retention
Cases are scored based on weighted combination of:
- **Satisfaction** (40% default): User happiness with generated menu
- **Modification complexity** (35% default): Number of repairs needed (prioritizes hard-to-reach cases)
- **Novelty** (25% default): Diversity relative to existing cases

### 3. Memory Curation
When memory exceeds cap:
1. **Remove near-duplicates** (similarity > 0.90) keeping higher-value ones
2. **Remove lowest-value cases** until within cap
3. **Never drop below minimum** case count for system stability

### 4. Backward Compatibility
- Old cases without satisfaction fields load correctly (default to `None`)
- New fields only saved if present
- No breaking changes to existing case format

---

## Configuration

### RetentionConfig

Located in `actualizador/config_retention.py`:

```python
from actualizador.config_retention import RetentionConfig

config = RetentionConfig(
    # Memory limits
    max_cases=150,              # Maximum cases to store
    min_cases=50,               # Minimum cases to maintain
    
    # Retention weights (must sum to 1.0)
    weight_satisfaction=0.40,   # User satisfaction importance
    weight_modifications=0.35,  # Complexity/difficulty importance  
    weight_novelty=0.25,        # Diversity importance
    
    # Similarity thresholds
    near_duplicate_threshold=0.90,  # Cases above this are duplicates
    
    # Rating configuration
    rating_scale_min=1,
    rating_scale_max=5,
    rating_required=False,      # Allow skipping ratings
    default_satisfaction_if_skipped=3.0,  # Neutral default
    
    # Modification bonus
    modification_bonus_scale=0.5,  # Logarithmic scaling factor
)
```

### Tuning Guidelines

**Increase `weight_satisfaction`** if user happiness is most important
**Increase `weight_modifications`** to keep more complex/repaired cases  
**Increase `weight_novelty`** to maximize solution space coverage

**Lower `max_cases`** to force more aggressive curation  
**Raise `near_duplicate_threshold`** to be more strict about duplicates

---

## Usage

### Basic Usage (Automatic)

The retention system is **automatically integrated** into `sistema_cbr.py`:

```python
from sistema_cbr import SistemaCBR, PreferenciasUsuario

sistema = SistemaCBR()  # Retention enabled by default

preferencias = PreferenciasUsuario(
    tipo_evento='familiar',
    temporada='verano',
    restricciones=['vegetariano'],
    estilo='clasico',
    tradicion='italiana'
)

resultado = sistema.generar_menu(preferencias)
# → After valid menu generation:
#    1. User is prompted for satisfaction rating
#    2. Case is evaluated for retention
#    3. Memory is curated if needed
#    4. Changes are persisted

if resultado.nuevo_caso_id:
    print(f"Case saved: {resultado.nuevo_caso_id}")
else:
    print("Case not retained (low value or invalid)")
```

### Custom Configuration

```python
from actualizador.config_retention import RetentionConfig
from actualizador import ActualizadorConocimiento

# Create custom retention config
retention_config = RetentionConfig(
    max_cases=100,
    weight_satisfaction=0.50,  # Prioritize satisfaction
    weight_modifications=0.30,
    weight_novelty=0.20
)

# Initialize system with custom config
sistema = SistemaCBR()
sistema.actualizador = ActualizadorConocimiento(
    retention_config=retention_config,
    enable_retention=True
)
```

### Direct API Usage

```python
from actualizador import ActualizadorConocimiento
from conocimiento.models import Menu

actualizador = ActualizadorConocimiento(enable_retention=True)

menu = Menu(
    entrante='Bruschetta',
    principal='Pasta al Pomodoro',
    postre='Tiramisu'
)

caso_id, resultado = actualizador.procesar_caso_con_retencion(
    menu=menu,
    tipo_evento='familiar',
    temporada='verano',
    restricciones=['vegetariano'],
    estilo='clasico',
    tradicion='italiana',
    exito=True,
    reparaciones_aplicadas=[...],  # List of repairs
    collect_rating=True,  # Prompt for rating
    crear_backup=False
)

if resultado['retained']:
    print(f"Case {caso_id} retained")
    print(f"Keep score: {resultado['metrics']['keep_score']:.3f}")
else:
    print(f"Case not retained: {resultado['reason']}")
```

### Disabling Retention

```python
# Disable retention (old behavior - no saving)
actualizador = ActualizadorConocimiento(enable_retention=False)

# Or globally for the system
sistema.actualizador.enable_retention = False
```

---

## Rating Collection

### Interactive Mode (Default)

When running in a terminal with stdin attached:

```
==================================================================
SATISFACCIÓN DEL MENÚ GENERADO
==================================================================
Caso: C026

Menú generado:
  Entrante:  Bruschetta De Verano
  Principal: Pasta al Pomodoro
  Postre:    Tiramisu

¿Desea calificar este menú? (s/n): s
  Entrante: Califique de 1 a 5 (o 's' para omitir): 5
  Principal: Califique de 1 a 5 (o 's' para omitir): 4
  Postre: Califique de 1 a 5 (o 's' para omitir): 5

Calificación promedio: 4.67/5
```

### Non-Interactive Mode

When stdin is not a terminal (scripts, batch jobs):
- Uses `default_satisfaction_if_skipped` (3.0 by default)
- No prompts, silent execution
- Can be configured via `non_interactive_default` in config

### Skipping Ratings

If `rating_required=False` (default):
- User can press 'n' to skip rating
- Individual dishes can be skipped with 's'
- Neutral score (3.0) is assigned

---

## Retention Metrics Explained

### Satisfaction Score (Normalized to [0,1])

```
normalized = (raw_score - min) / (max - min)
Example: 4.0 on 1-5 scale → (4-1)/(5-1) = 0.75
```

### Modification Bonus (Logarithmic)

```
bonus = log(1 + count * scale) / log(1 + max_reasonable * scale)
Example: 5 repairs → log(1 + 5*0.5) / log(1 + 20*0.5) ≈ 0.46
```

Prioritizes cases that required many modifications (hard to reach via modifier alone).

### Novelty (Diversity)

```
novelty = 1 - max_similarity(case, existing_cases)
Example: max_sim = 0.85 → novelty = 0.15
```

High novelty = case covers new part of solution space.

### Keep Score (Weighted Aggregate)

```
keep_score = w_s * satisfaction + w_m * modifications + w_n * novelty
Example: 0.40*0.75 + 0.35*0.46 + 0.25*0.15 = 0.50
```

Higher score = more valuable case, more likely to be retained.

---

## Similarity Reuse Decision

**CHOICE: REUSE existing `CalculadorSimilitudPonderada`**

### Why Reuse?

✓ **Already proven** in retrieval module  
✓ **Deterministic** and fast  
✓ **Symmetric** by design  
✓ **Interpretable** weights  
✓ **Minimal adapter code** (~50 lines)  
✓ **Consistent** with retrieval similarity  

### What Was Adapted?

Created `CaseSimilarityAdapter` in `similarity_adapter.py`:
- Wraps existing `CalculadorSimilitudPonderada`
- Converts `Caso` objects to dict format expected by calculator
- Adds `novelty()` helper for diversity calculation
- Includes sanity tests (symmetry, identity, bounds)

### Similarity Components

Reused from `similitud_ponderada.py`:
- **tipo_evento**: Exact match or lookup table (0.6 for related, 0.2 for distant)
- **restricciones**: Jaccard similarity on restriction sets
- **temporada**: Adjacent seasons = 0.7, opposite = 0.3
- **estilo**: Exact match = 1.0, different = 0.3
- **tradicion**: Exact match = 1.0, different = 0.2
- **menu_ingredientes**: 70% direct ingredient overlap + 30% category similarity

All weighted with default: `tipo_evento=0.25, restricciones=0.20, temporada=0.15, estilo=0.15, tradicion=0.15, menu=0.10`

---

## Case Schema Updates

### New Fields (Backward-Compatible)

```python
@dataclass
class Caso:
    # ... existing fields ...
    
    # NEW: Optional satisfaction fields
    satisfaction_score: Optional[float] = None       # 1-5 aggregate rating
    satisfaction_per_menu: Optional[Dict[str, float]] = None  # Individual ratings
    rating_timestamp: Optional[str] = None           # ISO timestamp
    modification_count: int = 0                      # Number of repairs applied
```

### Serialization Behavior

**Old case (no satisfaction)**:
```json
{
  "id": "C001",
  "restricciones": [],
  "temporada": "verano",
  ...
  "exito": true
}
```
No new fields in JSON (backward-compatible).

**New case (with satisfaction)**:
```json
{
  "id": "C026",
  "restricciones": ["vegetariano"],
  "temporada": "verano",
  ...
  "exito": true,
  "satisfaction_score": 4.67,
  "satisfaction_per_menu": {
    "entrante": 5.0,
    "principal": 4.0,
    "postre": 5.0
  },
  "rating_timestamp": "2026-01-07T14:30:00",
  "modification_count": 2
}
```

---

## Memory Curation Logic

### When Curation Triggers

Curation runs when `len(cases) > max_cases` after adding a new case.

### Curation Steps

1. **Identify near-duplicates**
   - Compute pairwise similarity for all cases
   - Find pairs with `similarity >= near_duplicate_threshold`
   - In each pair, mark the lower-value case for removal

2. **Remove lowest-value cases**
   - Compute keep_score for remaining cases
   - Sort by score (ascending)
   - Remove lowest until `len(cases) <= max_cases`

3. **Safety check**
   - Never drop below `min_cases`
   - If would violate minimum, keep all cases

4. **Persist**
   - Save curated case list to `casos.json`

---

## Statistics and Monitoring

### Get Retention Statistics

```python
stats = actualizador.get_retention_statistics()

print(f"Total cases: {stats['total_casos']}/{stats['max_casos']}")
print(f"Memory usage: {stats['memory_usage_pct']:.1f}%")
print(f"Cases with satisfaction: {stats['casos_with_satisfaction']}")
print(f"Avg satisfaction: {stats['avg_satisfaction']:.2f}/5.0")
print(f"Cases with modifications: {stats['casos_with_modifications']}")
print(f"Avg modifications: {stats['avg_modifications']:.2f}")
```

### Example Output

```
Total cases: 108/150
Memory usage: 72.0%
Cases with satisfaction: 12
Avg satisfaction: 4.25/5.0
Cases with modifications: 45
Avg modifications: 2.8
```

---

## Testing and Validation

### Run All Tests

```bash
cd /home/claudia/Documentos/Github/SBC-sys-cbr/sys00_esteeeee

# Test similarity adapter
python3 actualizador/similarity_adapter.py

# Test memory curator
python3 actualizador/memory_curator.py

# Test rating collector (interactive)
python3 actualizador/rating_collector.py
```

### Run Demos

```bash
# Run all demos (interactive)
python3 demo_retention.py

# Run specific demo
python3 demo_retention.py --demo 1  # Basic retention
python3 demo_retention.py --demo 2  # Memory curation
python3 demo_retention.py --demo 3  # Statistics
python3 demo_retention.py --demo 4  # Backward compatibility
```

### Test Backward Compatibility

```python
# Load old case (no satisfaction fields)
from conocimiento.models import Caso

old_case_dict = {
    'id': 'C001',
    'restricciones': [],
    'temporada': 'verano',
    'tipo_evento': 'familiar',
    'menu': {'entrante': 'A', 'principal': 'B', 'postre': 'C'},
    'estilo': 'clasico',
    'tradicion': 'italiana',
    'exito': True,
    'fallos_detectados': [],
    'reparaciones_aplicadas': []
}

caso = Caso.from_dict(old_case_dict)
assert caso.satisfaction_score is None  # Defaults to None
assert caso.modification_count == 0     # Defaults to 0

# Serialize back - no new fields added
caso_dict = caso.to_dict()
assert 'satisfaction_score' not in caso_dict  # Not saved if None
```

---

## Troubleshooting

### Issue: Ratings not being collected

**Check:**
- Is `enable_retention=True`?
- Is `collect_rating=True` in `procesar_caso_con_retencion()`?
- Is stdin a terminal? (Check `sys.stdin.isatty()`)

**Solution:**
- Enable retention explicitly
- Use interactive mode (not scripts without terminal)
- Or set `non_interactive_default` for automated scenarios

### Issue: Cases not being retained

**Check:**
- Are cases valid? (`exito=True`)
- What is the keep_score vs existing cases?
- Is memory at max capacity?

**Debug:**
```python
should_retain, reason, metrics = memory_curator.should_retain_case(
    candidate_case, existing_cases
)
print(f"Retain: {should_retain}")
print(f"Reason: {reason}")
print(f"Metrics: {metrics}")
```

### Issue: Too many cases being forgotten

**Solution:**
- Increase `max_cases`
- Lower `near_duplicate_threshold` (be less strict)
- Adjust retention weights to match priorities

### Issue: Memory grows too fast

**Solution:**
- Decrease `max_cases`
- Increase `near_duplicate_threshold` (be more aggressive)
- Increase `weight_novelty` to favor diversity over quantity

---

## Future Enhancements

### Potential Improvements

1. **Adaptive weights**: Learn optimal weights from user behavior
2. **Temporal decay**: Older cases gradually lose value
3. **Cluster-based diversity**: Maintain K cases per cluster
4. **Active forgetting triggers**: User-initiated "forget this" command
5. **Export/import**: Backup high-value cases before forgetting
6. **Explainability UI**: Show why case was/wasn't retained

### Extension Points

- **Custom similarity metrics**: Replace `CaseSimilarityAdapter`
- **Custom retention policies**: Subclass `MemoryCurator`
- **Rating sources**: Extend `RatingCollector` for web APIs, files, etc.
- **Storage backends**: Replace JSON with SQLite, PostgreSQL, etc.

---

## Summary

The retention system provides:

✓ **End-to-end pipeline**: Rating → Retention → Curation → Persistence  
✓ **Intelligent decisions**: Multi-factor scoring (satisfaction + complexity + diversity)  
✓ **Bounded memory**: Never exceeds cap, maintains minimum  
✓ **Backward compatible**: Old cases load/save correctly  
✓ **Reuses existing code**: Similarity calculator, persistence layer  
✓ **Configurable**: Easy tuning via `RetentionConfig`  
✓ **Tested**: Unit tests + comprehensive demos  

**All requirements met. System ready for production.**
