"""
Demo del Sistema de Retención - Ejecución Completa
=================================================

Demuestra:
1. Generación de menús válidos
2. Recolección de ratings interactivos (simulados en demo)
3. Curación de memoria cuando se excede el límite
4. Priorización por satisfacción, modificaciones y novedad
"""

import sys
import os

# Añadir al path
sys.path.insert(0, os.path.dirname(__file__))

from sistema_cbr import SistemaCBR, PreferenciasUsuario, ConfiguracionCBR
from actualizador import ConfiguracionRetencion
from conocimiento import cargador


def demo_generacion_con_rating():
    """Demuestra generación de menú con sistema de retención."""
    print("\n" + "="*70)
    print("DEMO: GENERACIÓN DE MENÚ CON RETENCIÓN")
    print("="*70)
    
    # Configurar sistema con retención
    config_retencion = ConfiguracionRetencion(
        max_cases=30,  # Límite bajo para demostrar curación
        weight_satisfaction=0.4,
        weight_modifications=0.3,
        weight_novelty=0.3,
        require_rating_for_retention=False,
        default_satisfaction_on_skip=None
    )
    
    config_cbr = ConfiguracionCBR(
        config_retencion=config_retencion,
        habilitar_ratings=True,
        k_casos_recuperar=3
    )
    
    sistema = SistemaCBR(config_cbr)
    
    # Preparar preferencias
    preferencias = PreferenciasUsuario(
        tipo_evento='boda',
        temporada='verano',
        restricciones=['vegano'],
        estilo='molecular',
        tradicion='francesa'
    )
    
    print("\n🚀 Iniciando generación de menú...")
    print(f"   Tipo evento: {preferencias.tipo_evento}")
    print(f"   Temporada: {preferencias.temporada}")
    print(f"   Restricciones: {preferencias.restricciones}")
    print(f"   Estilo: {preferencias.estilo}")
    
    # Generar menú
    # NOTA: En modo interactivo real, el sistema pedirá rating aquí
    # En este demo, se usa el default o se salta
    resultado = sistema.generar_menu(preferencias)
    
    # Mostrar resultado
    if resultado.exito:
        print("\n✅ Menú generado exitosamente")
        print(f"\n   📋 MENÚ:")
        print(f"      Entrante:  {resultado.menu['entrante']}")
        print(f"      Principal: {resultado.menu['principal']}")
        print(f"      Postre:    {resultado.menu['postre']}")
        print(f"\n   📊 ESTADÍSTICAS:")
        print(f"      Similitud caso base: {resultado.similitud_caso_base:.3f}")
        print(f"      Caso base ID: {resultado.caso_base_id}")
        print(f"      Reparaciones: {len(resultado.reparaciones_aplicadas)}")
        if resultado.nuevo_caso_id:
            print(f"      Nuevo caso ID: {resultado.nuevo_caso_id}")
        
        return True
    else:
        print(f"\n❌ Error: {resultado.mensaje}")
        return False


def demo_estado_memoria():
    """Muestra el estado actual de la memoria de casos."""
    print("\n" + "="*70)
    print("DEMO: ESTADO DE LA MEMORIA")
    print("="*70)
    
    # Cargar casos actuales
    casos = cargador.cargar_json('casos.json')
    
    print(f"\n📦 Total de casos en memoria: {len(casos)}")
    
    # Analizar casos con satisfacción
    casos_con_rating = [c for c in casos if c.get('satisfaccion')]
    casos_con_mods = [c for c in casos if c.get('modification_count', 0) > 0]
    
    print(f"   Casos con rating: {len(casos_con_rating)}")
    print(f"   Casos con modificaciones: {len(casos_con_mods)}")
    
    # Mostrar ejemplos
    if casos_con_rating:
        print(f"\n📊 Ejemplo de caso con rating:")
        caso_ej = casos_con_rating[0]
        print(f"   ID: {caso_ej['id']}")
        print(f"   Satisfacción: {caso_ej['satisfaccion'].get('satisfaction_score')}")
        print(f"   Modificaciones: {caso_ej.get('modification_count', 0)}")
        print(f"   Menú:")
        for tipo, plato in caso_ej['menu'].items():
            print(f"      {tipo}: {plato}")
    
    return True


def demo_similitud_casos():
    """Demuestra cálculo de similitud entre casos."""
    print("\n" + "="*70)
    print("DEMO: SIMILITUD ENTRE CASOS")
    print("="*70)
    
    from actualizador.similitud_casos import SimilitudCasos
    
    casos = cargador.cargar_json('casos.json')
    
    if len(casos) < 2:
        print("⚠️ Necesitamos al menos 2 casos")
        return False
    
    sim = SimilitudCasos()
    
    # Comparar primeros 3 casos
    print("\n📐 Matriz de similitud (primeros 3 casos):\n")
    print("      ", end="")
    for i in range(min(3, len(casos))):
        print(f"{casos[i]['id']:8}", end="")
    print()
    
    for i in range(min(3, len(casos))):
        print(f"{casos[i]['id']:6}", end="")
        for j in range(min(3, len(casos))):
            s = sim.similarity(casos[i], casos[j])
            print(f"{s:8.3f}", end="")
        print()
    
    # Calcular novedad de un caso respecto a otros
    caso_nuevo = casos[0]
    otros = casos[1:4]
    
    nov = sim.novelty(caso_nuevo, otros)
    print(f"\n🆕 Novedad del caso {caso_nuevo['id']} respecto a otros: {nov:.3f}")
    
    # Buscar duplicados
    duplicados = sim.find_near_duplicates(casos[:10], threshold=0.9)
    if duplicados:
        print(f"\n🔍 Clusters de casi-duplicados encontrados: {len(duplicados)}")
        for cluster in duplicados:
            ids = [casos[i]['id'] for i in cluster]
            print(f"   - {ids}")
    else:
        print(f"\n✓ No se encontraron duplicados (threshold=0.9)")
    
    return True


def demo_resumen_completo():
    """Resumen completo del sistema."""
    print("\n" + "="*70)
    print("RESUMEN DEL SISTEMA DE RETENCIÓN")
    print("="*70)
    
    from actualizador import ActualizadorConocimiento, ConfiguracionRetencion
    
    config = ConfiguracionRetencion.load_from_file()
    act = ActualizadorConocimiento(config_retencion=config)
    
    resumen = act.gestor_casos.obtener_resumen_memoria()
    
    print(f"\n📊 ESTADÍSTICAS DE MEMORIA:")
    print(f"   Total casos: {resumen['total_casos']}/{resumen['max_casos']}")
    print(f"   Capacidad usada: {resumen['capacidad_usada']*100:.1f}%")
    print(f"   Casos con rating: {resumen['casos_con_rating']}")
    print(f"   Casos sin rating: {resumen['casos_sin_rating']}")
    if resumen['satisfaccion_promedio']:
        print(f"   Satisfacción promedio: {resumen['satisfaccion_promedio']:.2f}")
    print(f"   Modificaciones promedio: {resumen['modificaciones_promedio']:.1f}")
    print(f"   Diversidad estimada: {resumen['diversidad_estimada']:.3f}")
    
    print(f"\n⚙️  CONFIGURACIÓN:")
    print(f"   Max cases: {config.max_cases}")
    print(f"   Pesos: S={config.weight_satisfaction:.1f}, "
          f"M={config.weight_modifications:.1f}, N={config.weight_novelty:.1f}")
    print(f"   Umbral duplicados: {config.similarity_duplicate_threshold}")
    print(f"   Escala rating: {config.rating_scale_min}-{config.rating_scale_max}")
    
    return True


def main():
    """Ejecuta todas las demos."""
    print("\n" + "="*70)
    print("🎬 DEMO COMPLETA DEL SISTEMA DE RETENCIÓN")
    print("="*70)
    
    demos = [
        ("Estado de Memoria", demo_estado_memoria),
        ("Similitud entre Casos", demo_similitud_casos),
        ("Resumen del Sistema", demo_resumen_completo),
        # Comentado para evitar modificar la base en demo
        # ("Generación con Rating", demo_generacion_con_rating),
    ]
    
    resultados = []
    
    for nombre, demo_func in demos:
        try:
            print(f"\n\n{'▶'*35}")
            exito = demo_func()
            resultados.append((nombre, exito))
        except Exception as e:
            print(f"\n❌ Error en demo '{nombre}': {e}")
            import traceback
            traceback.print_exc()
            resultados.append((nombre, False))
    
    # Resumen
    print("\n\n" + "="*70)
    print("RESUMEN DE DEMOS")
    print("="*70)
    
    for nombre, exito in resultados:
        simbolo = "✅" if exito else "❌"
        print(f"{simbolo} {nombre}")
    
    exitosos = sum(1 for _, exito in resultados if exito)
    print(f"\nResultado: {exitosos}/{len(resultados)} demos completadas exitosamente")
    
    print("\n" + "="*70)
    print("📚 Para más información, ver README_RETENCION.md")
    print("="*70)


if __name__ == "__main__":
    main()
