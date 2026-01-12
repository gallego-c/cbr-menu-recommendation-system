#!/usr/bin/env python3
"""
Generador de Gráficas y Tablas para Informe del Sistema CBR
Sistema de Recomendación de Menús basado en Razonamiento Basado en Casos
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter, defaultdict
from pathlib import Path
import pandas as pd

# Configuración de estilo
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Colores para gráficas
COLORS = {
    'primary': '#3498db',
    'secondary': '#2ecc71', 
    'accent': '#e74c3c',
    'neutral': '#95a5a6',
    'dark': '#2c3e50',
    'bodas': '#e91e63',
    'familiares': '#4caf50',
    'congresos': '#2196f3',
    'clasico': '#ff9800',
    'molecular': '#9c27b0'
}

TRADICIONES_COLORS = {
    'italiana': '#009688',
    'catalana': '#f44336',
    'francesa': '#3f51b5',
    'mexicana': '#ff5722',
    'india': '#ffc107',
    'china': '#e91e63',
    'mediterranea': '#00bcd4',
    'Sin especificar': '#9e9e9e'
}

def cargar_datos():
    """Carga todos los archivos JSON de conocimiento"""
    base_path = Path(__file__).parent / "conocimiento"
    
    with open(base_path / "casos.json", "r", encoding="utf-8") as f:
        casos = json.load(f)
    with open(base_path / "platos.json", "r", encoding="utf-8") as f:
        platos = json.load(f)
    with open(base_path / "ingredientes.json", "r", encoding="utf-8") as f:
        ingredientes = json.load(f)
    with open(base_path / "tradiciones.json", "r", encoding="utf-8") as f:
        tradiciones = json.load(f)
    with open(base_path / "estilos.json", "r", encoding="utf-8") as f:
        estilos = json.load(f)
    with open(base_path / "restricciones.json", "r", encoding="utf-8") as f:
        restricciones = json.load(f)
    
    return casos, platos, ingredientes, tradiciones, estilos, restricciones

def crear_directorio_output():
    """Crea directorio para las gráficas"""
    output_dir = Path(__file__).parent / "graficas_informe"
    output_dir.mkdir(exist_ok=True)
    return output_dir

# =====================================================
# GRÁFICAS DE LA BASE DE CASOS
# =====================================================

def grafica_distribucion_eventos(casos, output_dir):
    """Gráfica de distribución por tipo de evento (requisito CBR)"""
    tipos = [c['tipo_evento'] for c in casos]
    conteo = Counter(tipos)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Gráfico de barras
    categorias = ['boda', 'familiar', 'congreso']
    valores = [conteo.get(cat, 0) for cat in categorias]
    colores = [COLORS['bodas'], COLORS['familiares'], COLORS['congresos']]
    
    bars = ax1.bar(categorias, valores, color=colores, edgecolor='white', linewidth=2)
    ax1.set_xlabel('Tipo de Evento')
    ax1.set_ylabel('Número de Casos')
    ax1.set_title('Distribución de Casos por Tipo de Evento')
    
    # Añadir valores en las barras
    for bar, val in zip(bars, valores):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, 
                str(val), ha='center', va='bottom', fontweight='bold', fontsize=14)
    
    # Línea de referencia para distribución ideal
    ax1.axhline(y=35/3, color='gray', linestyle='--', alpha=0.7, label='Distribución uniforme')
    ax1.legend()
    
    # Gráfico circular
    ax2.pie(valores, labels=[f'{cat.capitalize()}\n({v} casos)' for cat, v in zip(categorias, valores)],
            colors=colores, autopct='%1.1f%%', startangle=90,
            explode=(0.02, 0.02, 0.02), shadow=True)
    ax2.set_title('Proporción por Tipo de Evento')
    
    plt.tight_layout()
    plt.savefig(output_dir / '01_distribucion_eventos.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Gráfica: Distribución de eventos")

def grafica_distribucion_tradiciones(casos, output_dir):
    """Gráfica de distribución por tradición culinaria"""
    tradiciones = [c['tradicion'] or 'Sin especificar' for c in casos]
    conteo = Counter(tradiciones)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Ordenar por frecuencia
    sorted_items = sorted(conteo.items(), key=lambda x: x[1], reverse=True)
    nombres = [item[0].capitalize() for item in sorted_items]
    valores = [item[1] for item in sorted_items]
    colores = [TRADICIONES_COLORS.get(item[0], '#607d8b') for item in sorted_items]
    
    bars = ax.barh(nombres, valores, color=colores, edgecolor='white', linewidth=1.5)
    ax.set_xlabel('Número de Casos')
    ax.set_title('Distribución de Casos por Tradición Culinaria')
    ax.invert_yaxis()
    
    # Añadir valores
    for bar, val in zip(bars, valores):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2, 
                str(val), ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / '02_distribucion_tradiciones.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Gráfica: Distribución de tradiciones")

def grafica_distribucion_temporadas(casos, output_dir):
    """Gráfica de distribución por temporada"""
    temporadas = [c.get('temporada', 'N/A') or 'N/A' for c in casos]
    conteo = Counter(temporadas)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    orden = ['primavera', 'verano', 'otoño', 'invierno', 'N/A']
    colores_temp = ['#8bc34a', '#ffeb3b', '#ff9800', '#03a9f4', '#9e9e9e']
    
    valores = [conteo.get(t, 0) for t in orden]
    
    wedges, texts, autotexts = ax.pie(valores, labels=orden, colors=colores_temp,
                                       autopct='%1.1f%%', startangle=90,
                                       explode=(0.03, 0.03, 0.03, 0.03, 0.03))
    
    ax.set_title('Distribución de Casos por Temporada')
    
    # Leyenda con conteos
    legend_labels = [f'{t.capitalize()}: {v} casos' for t, v in zip(orden, valores)]
    ax.legend(wedges, legend_labels, title="Temporadas", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    plt.tight_layout()
    plt.savefig(output_dir / '03_distribucion_temporadas.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Gráfica: Distribución de temporadas")

def grafica_distribucion_restricciones(casos, output_dir):
    """Gráfica de distribución de restricciones dietéticas"""
    todas_restricciones = []
    for c in casos:
        if c['restricciones']:
            todas_restricciones.extend(c['restricciones'])
    
    conteo = Counter(todas_restricciones)
    
    # También contar casos sin restricciones
    sin_restricciones = sum(1 for c in casos if not c['restricciones'])
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Gráfico de barras de restricciones
    if conteo:
        nombres = [k.replace('_', ' ').title() for k in conteo.keys()]
        valores = list(conteo.values())
        colores = plt.cm.Set2(np.linspace(0, 1, len(nombres)))
        
        bars = ax1.bar(nombres, valores, color=colores, edgecolor='white')
        ax1.set_xlabel('Tipo de Restricción')
        ax1.set_ylabel('Frecuencia')
        ax1.set_title('Frecuencia de Restricciones Dietéticas')
        ax1.tick_params(axis='x', rotation=45)
        
        for bar, val in zip(bars, valores):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                    str(val), ha='center', va='bottom', fontweight='bold')
    
    # Gráfico de casos con/sin restricciones
    con_restricciones = len(casos) - sin_restricciones
    ax2.pie([con_restricciones, sin_restricciones], 
            labels=[f'Con restricciones\n({con_restricciones})', f'Sin restricciones\n({sin_restricciones})'],
            colors=[COLORS['accent'], COLORS['secondary']],
            autopct='%1.1f%%', startangle=90, explode=(0.05, 0))
    ax2.set_title('Casos con Restricciones Dietéticas')
    
    plt.tight_layout()
    plt.savefig(output_dir / '04_distribucion_restricciones.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Gráfica: Distribución de restricciones")

def grafica_distribucion_estilos(casos, output_dir):
    """Gráfica de distribución por estilo culinario"""
    estilos = [c['estilo'] for c in casos]
    conteo = Counter(estilos)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    nombres = list(conteo.keys())
    valores = list(conteo.values())
    colores = [COLORS['clasico'], COLORS['molecular']][:len(nombres)]
    
    wedges, texts, autotexts = ax.pie(valores, labels=[n.capitalize() for n in nombres],
                                       colors=colores, autopct='%1.1f%%',
                                       startangle=90, explode=[0.03]*len(nombres),
                                       textprops={'fontsize': 12})
    
    ax.set_title('Distribución de Casos por Estilo Culinario')
    
    plt.tight_layout()
    plt.savefig(output_dir / '05_distribucion_estilos.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Gráfica: Distribución de estilos")

def grafica_satisfaccion(casos, output_dir):
    """Gráfica de distribución de puntuaciones de satisfacción"""
    scores = [c.get('satisfaction_score', 0) for c in casos if c.get('satisfaction_score')]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Histograma de satisfacción
    ax1.hist(scores, bins=10, range=(1, 5), color=COLORS['primary'], 
             edgecolor='white', linewidth=1.5, alpha=0.8)
    ax1.axvline(np.mean(scores), color=COLORS['accent'], linestyle='--', 
                linewidth=2, label=f'Media: {np.mean(scores):.2f}')
    ax1.set_xlabel('Puntuación de Satisfacción')
    ax1.set_ylabel('Número de Casos')
    ax1.set_title('Distribución de Puntuaciones de Satisfacción')
    ax1.legend()
    ax1.set_xlim(1, 5)
    
    # Box plot por tipo de evento
    datos_evento = defaultdict(list)
    for c in casos:
        if c.get('satisfaction_score'):
            datos_evento[c['tipo_evento']].append(c['satisfaction_score'])
    
    bp = ax2.boxplot([datos_evento['boda'], datos_evento['familiar'], datos_evento['congreso']],
                     labels=['Boda', 'Familiar', 'Congreso'],
                     patch_artist=True)
    
    colores_box = [COLORS['bodas'], COLORS['familiares'], COLORS['congresos']]
    for patch, color in zip(bp['boxes'], colores_box):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax2.set_ylabel('Puntuación de Satisfacción')
    ax2.set_title('Satisfacción por Tipo de Evento')
    ax2.set_ylim(1, 5.5)
    
    plt.tight_layout()
    plt.savefig(output_dir / '06_satisfaccion.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Gráfica: Satisfacción")

def grafica_reparaciones(casos, output_dir):
    """Gráfica de análisis de reparaciones aplicadas"""
    con_reparaciones = sum(1 for c in casos if c.get('reparaciones_aplicadas'))
    sin_reparaciones = len(casos) - con_reparaciones
    
    # Contar tipos de reparaciones
    acciones = []
    for c in casos:
        for rep in c.get('reparaciones_aplicadas', []):
            if isinstance(rep, dict) and 'accion' in rep:
                acciones.append(rep['accion'])
    
    conteo_acciones = Counter(acciones)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Casos con/sin reparaciones
    ax1.pie([sin_reparaciones, con_reparaciones],
            labels=[f'Sin reparaciones\n({sin_reparaciones})', f'Con reparaciones\n({con_reparaciones})'],
            colors=[COLORS['secondary'], COLORS['accent']],
            autopct='%1.1f%%', startangle=90, explode=(0, 0.05))
    ax1.set_title('Casos que Requirieron Reparación')
    
    # Tipos de acciones de reparación
    if conteo_acciones:
        nombres = [k.replace('_', ' ').title() for k in conteo_acciones.keys()]
        valores = list(conteo_acciones.values())
        ax2.bar(nombres, valores, color=COLORS['primary'], edgecolor='white')
        ax2.set_xlabel('Tipo de Acción')
        ax2.set_ylabel('Frecuencia')
        ax2.set_title('Tipos de Reparaciones Aplicadas')
    else:
        ax2.text(0.5, 0.5, 'No hay reparaciones\nregistradas', ha='center', va='center',
                fontsize=14, transform=ax2.transAxes)
        ax2.set_title('Tipos de Reparaciones Aplicadas')
    
    plt.tight_layout()
    plt.savefig(output_dir / '07_reparaciones.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Gráfica: Reparaciones")

# =====================================================
# GRÁFICAS DE LA BASE DE CONOCIMIENTO
# =====================================================

def grafica_composicion_platos(platos, output_dir):
    """Gráfica de composición de la base de platos"""
    postres = sum(1 for p in platos if p.get('es_postre', False))
    no_postres = len(platos) - postres
    
    # Técnicas de cocción
    tecnicas = []
    for p in platos:
        tecnicas.extend(p.get('tecnica_coccion', []))
    conteo_tecnicas = Counter(tecnicas)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Platos vs Postres
    ax1.pie([no_postres, postres],
            labels=[f'Platos principales/entrantes\n({no_postres})', f'Postres\n({postres})'],
            colors=[COLORS['primary'], COLORS['accent']],
            autopct='%1.1f%%', startangle=90, explode=(0, 0.05))
    ax1.set_title(f'Composición de la Base de Platos (Total: {len(platos)})')
    
    # Top 10 técnicas de cocción
    top_tecnicas = conteo_tecnicas.most_common(10)
    nombres = [t[0].replace('_', ' ').title() for t in top_tecnicas]
    valores = [t[1] for t in top_tecnicas]
    
    bars = ax2.barh(nombres[::-1], valores[::-1], color=plt.cm.viridis(np.linspace(0.2, 0.8, len(nombres))))
    ax2.set_xlabel('Número de Platos')
    ax2.set_title('Top 10 Técnicas de Cocción')
    
    for bar, val in zip(bars, valores[::-1]):
        ax2.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                str(val), ha='left', va='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_dir / '08_composicion_platos.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Gráfica: Composición de platos")

def grafica_sabores(platos, output_dir):
    """Gráfica de distribución de sabores dominantes"""
    sabores = [p.get('sabor_dominante', 'N/A') for p in platos]
    conteo = Counter(sabores)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colores_sabores = {
        'dulce': '#ff69b4',
        'salado': '#87ceeb',
        'umami': '#dda0dd',
        'acido': '#98fb98',
        'amargo': '#f0e68c',
        'picante': '#ff6347'
    }
    
    sorted_items = sorted(conteo.items(), key=lambda x: x[1], reverse=True)
    nombres = [item[0].capitalize() for item in sorted_items]
    valores = [item[1] for item in sorted_items]
    colores = [colores_sabores.get(item[0], '#607d8b') for item in sorted_items]
    
    wedges, texts, autotexts = ax.pie(valores, labels=nombres, colors=colores,
                                       autopct='%1.1f%%', startangle=90,
                                       pctdistance=0.85)
    
    # Círculo central para donut
    centre_circle = plt.Circle((0, 0), 0.60, fc='white')
    ax.add_patch(centre_circle)
    
    ax.set_title('Distribución de Sabores Dominantes en Platos')
    
    # Añadir leyenda
    legend_labels = [f'{n}: {v}' for n, v in zip(nombres, valores)]
    ax.legend(wedges, legend_labels, title="Sabores", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    plt.tight_layout()
    plt.savefig(output_dir / '09_sabores.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Gráfica: Distribución de sabores")

def grafica_categorias_ingredientes(ingredientes, output_dir):
    """Gráfica de categorías de ingredientes"""
    categorias = [i.get('categoria', 'N/A') for i in ingredientes]
    conteo = Counter(categorias)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    sorted_items = sorted(conteo.items(), key=lambda x: x[1], reverse=True)[:15]
    nombres = [item[0].replace('_', ' ').title() for item in sorted_items]
    valores = [item[1] for item in sorted_items]
    
    colores = plt.cm.Set3(np.linspace(0, 1, len(nombres)))
    
    bars = ax.barh(nombres[::-1], valores[::-1], color=colores)
    ax.set_xlabel('Número de Ingredientes')
    ax.set_title(f'Top 15 Categorías de Ingredientes (Total: {len(ingredientes)})')
    
    for bar, val in zip(bars, valores[::-1]):
        ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
                str(val), ha='left', va='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_dir / '10_categorias_ingredientes.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Gráfica: Categorías de ingredientes")

def grafica_matriz_evento_tradicion(casos, output_dir):
    """Matriz de calor: tipo de evento vs tradición"""
    eventos = ['boda', 'familiar', 'congreso']
    tradiciones_unicas = list(set(c['tradicion'] or 'Sin especificar' for c in casos))
    
    matriz = np.zeros((len(eventos), len(tradiciones_unicas)))
    
    for c in casos:
        i = eventos.index(c['tipo_evento'])
        j = tradiciones_unicas.index(c['tradicion'] or 'Sin especificar')
        matriz[i, j] += 1
    
    fig, ax = plt.subplots(figsize=(12, 5))
    
    im = ax.imshow(matriz, cmap='YlOrRd', aspect='auto')
    
    ax.set_xticks(range(len(tradiciones_unicas)))
    ax.set_yticks(range(len(eventos)))
    ax.set_xticklabels([(t or 'Sin especificar').capitalize() for t in tradiciones_unicas], rotation=45, ha='right')
    ax.set_yticklabels([e.capitalize() for e in eventos])
    
    # Añadir valores en las celdas
    for i in range(len(eventos)):
        for j in range(len(tradiciones_unicas)):
            if matriz[i, j] > 0:
                text = ax.text(j, i, int(matriz[i, j]), ha="center", va="center",
                              color="white" if matriz[i, j] > matriz.max()/2 else "black",
                              fontweight='bold')
    
    ax.set_title('Matriz: Tipo de Evento vs Tradición Culinaria')
    plt.colorbar(im, ax=ax, label='Número de casos')
    
    plt.tight_layout()
    plt.savefig(output_dir / '11_matriz_evento_tradicion.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Gráfica: Matriz evento-tradición")

def grafica_ciclo_cbr(output_dir):
    """Diagrama del ciclo CBR"""
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Definir las 5 fases del ciclo CBR
    fases = [
        ('RECUPERAR', 0.9, 0.6, '#3498db'),
        ('REUTILIZAR', 1.1, -0.3, '#2ecc71'),
        ('REVISAR', 0, -1.1, '#e74c3c'),
        ('RETENER', -1.1, -0.3, '#9b59b6'),
        ('VALIDAR', -0.9, 0.6, '#f39c12')
    ]
    
    # Dibujar círculo central
    circle = plt.Circle((0, 0), 0.4, color='#34495e', zorder=5)
    ax.add_patch(circle)
    ax.text(0, 0, 'BASE DE\nCASOS', ha='center', va='center', fontsize=12, 
            fontweight='bold', color='white', zorder=6)
    
    # Dibujar fases
    for nombre, x, y, color in fases:
        box = plt.Rectangle((x-0.35, y-0.2), 0.7, 0.4, color=color, 
                            ec='white', linewidth=2, zorder=4, alpha=0.9)
        ax.add_patch(box)
        ax.text(x, y, nombre, ha='center', va='center', fontsize=11, 
                fontweight='bold', color='white', zorder=5)
    
    # Flechas del ciclo (simplificado)
    style = "Simple,tail_width=0.5,head_width=4,head_length=6"
    from matplotlib.patches import FancyArrowPatch
    
    arrow_color = '#7f8c8d'
    # Flechas entre fases
    ax.annotate('', xy=(0.75, 0.1), xytext=(0.55, 0.4),
                arrowprops=dict(arrowstyle='->', color=arrow_color, lw=2))
    ax.annotate('', xy=(0.55, -0.5), xytext=(0.75, -0.1),
                arrowprops=dict(arrowstyle='->', color=arrow_color, lw=2))
    ax.annotate('', xy=(-0.55, -0.5), xytext=(0.35, -0.9),
                arrowprops=dict(arrowstyle='->', color=arrow_color, lw=2))
    ax.annotate('', xy=(-0.75, 0.1), xytext=(-0.55, -0.5),
                arrowprops=dict(arrowstyle='->', color=arrow_color, lw=2))
    ax.annotate('', xy=(-0.55, 0.4), xytext=(-0.75, 0.1),
                arrowprops=dict(arrowstyle='->', color=arrow_color, lw=2))
    ax.annotate('', xy=(0.55, 0.6), xytext=(-0.55, 0.6),
                arrowprops=dict(arrowstyle='->', color=arrow_color, lw=2))
    
    ax.set_title('Ciclo CBR del Sistema de Menús', fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_dir / '12_ciclo_cbr.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Gráfica: Ciclo CBR")

# =====================================================
# TABLAS
# =====================================================

def generar_tablas(casos, platos, ingredientes, tradiciones, estilos, restricciones, output_dir):
    """Genera tablas en formato Markdown y LaTeX"""
    
    # Tabla 1: Resumen de la Base de Casos
    tabla1_md = """
# Tabla 1: Resumen de la Base de Casos

| Métrica | Valor |
|---------|-------|
| Total de casos | {} |
| Casos para Bodas | {} |
| Casos para Familiares | {} |
| Casos para Congresos | {} |
| Casos con reparaciones | {} |
| Puntuación media de satisfacción | {:.2f} |
| Casos protegidos (C001-C035) | 35 |
""".format(
        len(casos),
        sum(1 for c in casos if c['tipo_evento'] == 'boda'),
        sum(1 for c in casos if c['tipo_evento'] == 'familiar'),
        sum(1 for c in casos if c['tipo_evento'] == 'congreso'),
        sum(1 for c in casos if c.get('reparaciones_aplicadas')),
        np.mean([c.get('satisfaction_score', 0) for c in casos if c.get('satisfaction_score')])
    )
    
    # Tabla 2: Distribución por Tradición
    conteo_trad = Counter(c['tradicion'] or 'Sin especificar' for c in casos)
    tabla2_md = """
# Tabla 2: Distribución por Tradición Culinaria

| Tradición | Casos | Porcentaje |
|-----------|-------|-----------|
"""
    for trad, count in sorted(conteo_trad.items(), key=lambda x: x[1], reverse=True):
        trad_name = (trad or 'Sin especificar').capitalize()
        tabla2_md += f"| {trad_name} | {count} | {100*count/len(casos):.1f}% |\n"
    
    # Tabla 3: Distribución de Restricciones
    todas_rest = []
    for c in casos:
        todas_rest.extend(c.get('restricciones', []))
    conteo_rest = Counter(todas_rest)
    sin_rest = sum(1 for c in casos if not c.get('restricciones'))
    
    tabla3_md = """
# Tabla 3: Distribución de Restricciones Dietéticas

| Restricción | Frecuencia | Porcentaje |
|-------------|------------|------------|
"""
    for rest, count in sorted(conteo_rest.items(), key=lambda x: x[1], reverse=True):
        tabla3_md += f"| {rest.replace('_', ' ').title()} | {count} | {100*count/len(casos):.1f}% |\n"
    tabla3_md += f"| Sin restricciones | {sin_rest} | {100*sin_rest/len(casos):.1f}% |\n"
    
    # Tabla 4: Estadísticas de la Base de Conocimiento
    postres = sum(1 for p in platos if p.get('es_postre', False))
    tabla4_md = """
# Tabla 4: Estadísticas de la Base de Conocimiento

| Componente | Cantidad |
|------------|----------|
| Total de platos | {} |
| Platos (entrantes/principales) | {} |
| Postres | {} |
| Total de ingredientes | {} |
| Tradiciones culinarias | {} |
| Estilos culinarios | {} |
| Restricciones dietéticas | {} |
""".format(
        len(platos),
        len(platos) - postres,
        postres,
        len(ingredientes),
        len(tradiciones),
        len(estilos),
        len(restricciones)
    )
    
    # Tabla 5: Matriz Evento-Tradición
    eventos = ['boda', 'familiar', 'congreso']
    trads_unicas = sorted(set(c['tradicion'] or 'Sin especificar' for c in casos), key=lambda x: x or '')
    
    tabla5_md = """
# Tabla 5: Matriz de Casos por Evento y Tradición

| Tradición | Boda | Familiar | Congreso | Total |
|-----------|------|----------|----------|-------|
"""
    for trad in trads_unicas:
        counts = [sum(1 for c in casos if (c['tradicion'] or 'Sin especificar') == trad and c['tipo_evento'] == e) for e in eventos]
        total = sum(counts)
        trad_name = (trad or 'Sin especificar').capitalize()
        tabla5_md += f"| {trad_name} | {counts[0]} | {counts[1]} | {counts[2]} | {total} |\n"
    
    totales = [sum(1 for c in casos if c['tipo_evento'] == e) for e in eventos]
    tabla5_md += f"| **Total** | **{totales[0]}** | **{totales[1]}** | **{totales[2]}** | **{sum(totales)}** |\n"
    
    # Tabla 6: Estadísticas de Satisfacción
    scores_boda = [c.get('satisfaction_score') for c in casos if c['tipo_evento'] == 'boda' and c.get('satisfaction_score')]
    scores_fam = [c.get('satisfaction_score') for c in casos if c['tipo_evento'] == 'familiar' and c.get('satisfaction_score')]
    scores_cong = [c.get('satisfaction_score') for c in casos if c['tipo_evento'] == 'congreso' and c.get('satisfaction_score')]
    
    tabla6_md = """
# Tabla 6: Estadísticas de Satisfacción por Tipo de Evento

| Tipo de Evento | Media | Desv. Estándar | Mínimo | Máximo |
|----------------|-------|----------------|--------|--------|
"""
    for nombre, scores in [('Boda', scores_boda), ('Familiar', scores_fam), ('Congreso', scores_cong)]:
        if scores:
            tabla6_md += f"| {nombre} | {np.mean(scores):.2f} | {np.std(scores):.2f} | {min(scores):.1f} | {max(scores):.1f} |\n"
    
    all_scores = scores_boda + scores_fam + scores_cong
    if all_scores:
        tabla6_md += f"| **Global** | **{np.mean(all_scores):.2f}** | **{np.std(all_scores):.2f}** | **{min(all_scores):.1f}** | **{max(all_scores):.1f}** |\n"
    
    # Guardar tablas
    todas_tablas = tabla1_md + "\n\n" + tabla2_md + "\n\n" + tabla3_md + "\n\n" + tabla4_md + "\n\n" + tabla5_md + "\n\n" + tabla6_md
    
    with open(output_dir / 'tablas_informe.md', 'w', encoding='utf-8') as f:
        f.write(todas_tablas)
    
    print("✓ Tablas generadas en: tablas_informe.md")
    
    return todas_tablas

def grafica_resumen_sistema(casos, platos, ingredientes, output_dir):
    """Gráfica resumen del sistema CBR"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Distribución de eventos (top-left)
    ax1 = axes[0, 0]
    tipos = Counter(c['tipo_evento'] for c in casos)
    ax1.bar(['Boda', 'Familiar', 'Congreso'], 
            [tipos['boda'], tipos['familiar'], tipos['congreso']],
            color=[COLORS['bodas'], COLORS['familiares'], COLORS['congresos']])
    ax1.set_title('Distribución por Tipo de Evento')
    ax1.set_ylabel('Número de Casos')
    for i, (k, v) in enumerate(tipos.items()):
        ax1.text(i, v + 0.2, str(v), ha='center', fontweight='bold')
    
    # 2. Satisfacción (top-right)
    ax2 = axes[0, 1]
    scores = [c.get('satisfaction_score', 0) for c in casos if c.get('satisfaction_score')]
    ax2.hist(scores, bins=10, range=(1, 5), color=COLORS['primary'], edgecolor='white', alpha=0.8)
    ax2.axvline(np.mean(scores), color=COLORS['accent'], linestyle='--', linewidth=2)
    ax2.set_title(f'Distribución de Satisfacción (μ={np.mean(scores):.2f})')
    ax2.set_xlabel('Puntuación')
    ax2.set_ylabel('Frecuencia')
    
    # 3. Tradiciones (bottom-left)
    ax3 = axes[1, 0]
    tradiciones = Counter(c['tradicion'] or 'Sin especificar' for c in casos)
    sorted_trad = sorted(tradiciones.items(), key=lambda x: x[1], reverse=True)
    ax3.barh([(t[0] or 'Sin especificar').capitalize() for t in sorted_trad][::-1], 
             [t[1] for t in sorted_trad][::-1],
             color=[TRADICIONES_COLORS.get(t[0], '#607d8b') for t in sorted_trad][::-1])
    ax3.set_title('Casos por Tradición Culinaria')
    ax3.set_xlabel('Número de Casos')
    
    # 4. Métricas clave (bottom-right)
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    postres = sum(1 for p in platos if p.get('es_postre', False))
    metricas = [
        ('Total de Casos', len(casos)),
        ('Total de Platos', len(platos)),
        ('Total de Postres', postres),
        ('Total de Ingredientes', len(ingredientes)),
        ('Satisfacción Media', f'{np.mean(scores):.2f}'),
        ('Casos Protegidos', '35 (C001-C035)'),
        ('Límite Memoria', '40 casos máx.')
    ]
    
    y_pos = 0.9
    for nombre, valor in metricas:
        ax4.text(0.1, y_pos, f'{nombre}:', fontsize=12, fontweight='bold', transform=ax4.transAxes)
        ax4.text(0.7, y_pos, str(valor), fontsize=12, transform=ax4.transAxes)
        y_pos -= 0.12
    
    ax4.set_title('Métricas Clave del Sistema', fontsize=14, fontweight='bold')
    
    plt.suptitle('Resumen del Sistema CBR de Recomendación de Menús', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / '00_resumen_sistema.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Gráfica: Resumen del sistema")

def main():
    print("=" * 60)
    print("GENERADOR DE GRÁFICAS Y TABLAS PARA INFORME CBR")
    print("=" * 60)
    
    # Cargar datos
    print("\n📂 Cargando datos...")
    casos, platos, ingredientes, tradiciones, estilos, restricciones = cargar_datos()
    print(f"   - Casos: {len(casos)}")
    print(f"   - Platos: {len(platos)}")
    print(f"   - Ingredientes: {len(ingredientes)}")
    
    # Crear directorio de salida
    output_dir = crear_directorio_output()
    print(f"\n📁 Directorio de salida: {output_dir}")
    
    # Generar gráficas
    print("\n📊 Generando gráficas...")
    grafica_resumen_sistema(casos, platos, ingredientes, output_dir)
    grafica_distribucion_eventos(casos, output_dir)
    grafica_distribucion_tradiciones(casos, output_dir)
    grafica_distribucion_temporadas(casos, output_dir)
    grafica_distribucion_restricciones(casos, output_dir)
    grafica_distribucion_estilos(casos, output_dir)
    grafica_satisfaccion(casos, output_dir)
    grafica_reparaciones(casos, output_dir)
    grafica_composicion_platos(platos, output_dir)
    grafica_sabores(platos, output_dir)
    grafica_categorias_ingredientes(ingredientes, output_dir)
    grafica_matriz_evento_tradicion(casos, output_dir)
    grafica_ciclo_cbr(output_dir)
    
    # Generar tablas
    print("\n📋 Generando tablas...")
    tablas = generar_tablas(casos, platos, ingredientes, tradiciones, estilos, restricciones, output_dir)
    
    print("\n" + "=" * 60)
    print("✅ GENERACIÓN COMPLETADA")
    print("=" * 60)
    print(f"\n📁 Archivos generados en: {output_dir}")
    print("\nGráficas generadas:")
    for f in sorted(output_dir.glob("*.png")):
        print(f"   - {f.name}")
    print("\nTablas generadas:")
    for f in sorted(output_dir.glob("*.md")):
        print(f"   - {f.name}")
    
    # Mostrar preview de las tablas
    print("\n" + "=" * 60)
    print("PREVIEW DE TABLAS")
    print("=" * 60)
    print(tablas)

if __name__ == "__main__":
    main()
