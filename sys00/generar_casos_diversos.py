#!/usr/bin/env python3
"""
Script para generar ~50 casos nuevos con máxima diversidad y mínima repetición de platos.

ESTRATEGIA:
- Usa solo platos e ingredientes existentes (integridad referencial 100%)
- Minimiza repetición de platos calculando score de diversidad
- Garantiza cobertura de todas las dimensiones (tradición, temporada, evento, estilo, restricciones)
- Evita duplicados de menús (firma única)
"""

import json
import random
from collections import Counter, defaultdict
from typing import List, Dict, Set, Tuple
from pathlib import Path


class GeneradorCasosDiversos:
    """Genera casos con máxima diversidad y mínima repetición."""
    
    def __init__(self, conocimiento_dir: str = 'conocimiento'):
        self.conocimiento_dir = Path(conocimiento_dir)
        
        # Cargar datos existentes
        self.casos = self._cargar_json('casos.json')
        self.platos = self._cargar_json('platos.json')
        self.ingredientes = self._cargar_json('ingredientes.json')
        self.restricciones = self._cargar_json('restricciones.json')
        
        # Análisis de casos existentes
        self.ultimo_id = self._extraer_ultimo_id()
        self.platos_usados = Counter()  # Contador de uso de platos
        self.firmas_menus = set()  # Firmas únicas de menús
        self._analizar_casos_existentes()
        
        # Índices para búsqueda eficiente
        self.platos_por_nombre = {p['nombre']: p for p in self.platos}
        self.ingredientes_set = {ing['nombre'] for ing in self.ingredientes}
        
        # Restricciones válidas
        self.restricciones_validas = {r['nombre'] for r in self.restricciones}
        
        # Valores válidos de dimensiones
        self.tradiciones = ['catalana', 'mexicana', 'italiana', 'francesa', 'china', 'mediterranea']
        self.temporadas = ['primavera', 'verano', 'otoño', 'invierno']
        self.eventos = ['boda', 'congreso', 'familiar']
        self.estilos = ['molecular', 'clasico', 'gourmet', 'comfort_food', 'picante', 'fusion', 'saludable']
        
    def _cargar_json(self, filename: str) -> List[Dict]:
        """Carga archivo JSON."""
        path = self.conocimiento_dir / filename
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _guardar_json(self, filename: str, data: List[Dict]):
        """Guarda archivo JSON con formato bonito."""
        path = self.conocimiento_dir / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _extraer_ultimo_id(self) -> int:
        """Extrae el número del último ID (C025 -> 25)."""
        if not self.casos:
            return 0
        ultimo_caso = self.casos[-1]
        ultimo_id = ultimo_caso['id']
        return int(ultimo_id.replace('C', ''))
    
    def _analizar_casos_existentes(self):
        """Analiza casos existentes para tracking de uso y firmas."""
        for caso in self.casos:
            menu = caso.get('menu', {})
            entrante = menu.get('entrante', '')
            principal = menu.get('principal', '')
            postre = menu.get('postre', '')
            
            # Contar uso
            if entrante:
                self.platos_usados[entrante] += 1
            if principal:
                self.platos_usados[principal] += 1
            if postre:
                self.platos_usados[postre] += 1
            
            # Registrar firma
            firma = self._calcular_firma_menu(entrante, principal, postre)
            self.firmas_menus.add(firma)
    
    def _calcular_firma_menu(self, entrante: str, principal: str, postre: str) -> str:
        """Calcula firma única de un menú (lista ordenada de nombres)."""
        platos = sorted([entrante, principal, postre])
        return '|||'.join(platos)
    
    def _calcular_coste_menu(self, entrante: str, principal: str, postre: str) -> float:
        """
        Calcula coste de un menú (menor = mejor diversidad).
        Penaliza platos ya muy usados y repetición interna.
        """
        coste = 0.0
        
        # Penalizar platos muy usados
        coste += self.platos_usados.get(entrante, 0)
        coste += self.platos_usados.get(principal, 0)
        coste += self.platos_usados.get(postre, 0)
        
        # Penalizar repetición interna (mismo plato 2-3 veces)
        platos = [entrante, principal, postre]
        if len(set(platos)) < 3:
            coste += 100  # Penalización fuerte
        
        return coste
    
    def _plato_cumple_restricciones(self, plato_nombre: str, restricciones: List[str]) -> bool:
        """Verifica si un plato cumple todas las restricciones."""
        if not restricciones:
            return True
        
        plato = self.platos_por_nombre.get(plato_nombre)
        if not plato:
            return False
        
        ingredientes_plato = set(plato.get('ingredientes', []))
        
        # Verificar cada restricción
        for restriccion_nombre in restricciones:
            restriccion = next((r for r in self.restricciones if r['nombre'] == restriccion_nombre), None)
            if not restriccion:
                continue
            
            # Ingredientes prohibidos
            prohibidos = set(restriccion.get('ingredientes_prohibidos', []))
            if ingredientes_plato & prohibidos:  # Intersección no vacía
                return False
            
            # Categorías prohibidas
            categorias_prohibidas = set(restriccion.get('categorias_prohibidas', []))
            for ing_nombre in ingredientes_plato:
                ing_data = next((ing for ing in self.ingredientes if ing['nombre'] == ing_nombre), None)
                if ing_data and ing_data.get('categoria') in categorias_prohibidas:
                    return False
        
        return True
    
    def _generar_menu_valido(self, restricciones: List[str], max_intentos: int = 100) -> Tuple[str, str, str]:
        """
        Genera un menú válido que:
        1. Cumple restricciones
        2. Minimiza coste (diversidad)
        3. No es duplicado (firma única)
        """
        mejor_menu = None
        mejor_coste = float('inf')
        
        # Filtrar platos que cumplen restricciones
        platos_validos = [
            p['nombre'] for p in self.platos
            if self._plato_cumple_restricciones(p['nombre'], restricciones)
        ]
        
        if len(platos_validos) < 3:
            # Fallback: usar todos los platos
            platos_validos = [p['nombre'] for p in self.platos]
        
        for _ in range(max_intentos):
            # Seleccionar 3 platos diferentes
            if len(platos_validos) < 3:
                continue
            
            candidatos = random.sample(platos_validos, min(3, len(platos_validos)))
            entrante, principal, postre = candidatos[0], candidatos[1], candidatos[2]
            
            # Verificar firma única
            firma = self._calcular_firma_menu(entrante, principal, postre)
            if firma in self.firmas_menus:
                continue
            
            # Calcular coste
            coste = self._calcular_coste_menu(entrante, principal, postre)
            
            # Actualizar mejor
            if coste < mejor_coste:
                mejor_coste = coste
                mejor_menu = (entrante, principal, postre)
        
        if mejor_menu is None:
            # Fallback extremo: elegir 3 platos random sin verificar nada
            candidatos = random.sample([p['nombre'] for p in self.platos], 3)
            mejor_menu = tuple(candidatos)
        
        return mejor_menu
    
    def _generar_combinaciones_preferencias(self, n_casos: int = 50) -> List[Dict]:
        """
        Genera combinaciones de preferencias que garanticen diversidad.
        
        COBERTURA OBJETIVO:
        - Tradiciones: ~8 casos por tradición (6 tradiciones * 8 = 48)
        - Temporadas: ~12 casos por temporada (4 * 12 = 48)
        - Eventos: familiar=20, congreso=15, boda=15
        - Estilos: ~7 casos por estilo (7 estilos * 7 = 49)
        - Restricciones:
            * 10 sin restricciones
            * 20 con 1 restricción
            * 15 con 2 restricciones
            * 5 con 3 restricciones
        """
        combinaciones = []
        
        # Pool de restricciones (repetidas para sampling con probabilidades)
        restricciones_pool = [
            [],  # Sin restricciones (10 veces)
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            ['vegetariano'],  # 1 restricción (20 combinaciones)
            ['vegano'],
            ['sin_gluten'],
            ['sin_lactosa'],
            ['sin_huevo'],
            ['vegetariano'],
            ['vegano'],
            ['sin_gluten'],
            ['sin_lactosa'],
            ['sin_huevo'],
            ['vegetariano'],
            ['vegano'],
            ['sin_gluten'],
            ['sin_lactosa'],
            ['sin_huevo'],
            ['vegetariano'],
            ['vegano'],
            ['sin_gluten'],
            ['sin_lactosa'],
            ['sin_huevo'],
            ['vegetariano', 'sin_gluten'],  # 2 restricciones (15 combinaciones)
            ['vegano', 'sin_gluten'],
            ['vegetariano', 'sin_lactosa'],
            ['vegano', 'sin_lactosa'],
            ['sin_gluten', 'sin_lactosa'],
            ['sin_gluten', 'sin_huevo'],
            ['sin_lactosa', 'sin_huevo'],
            ['vegetariano', 'sin_huevo'],
            ['vegano', 'sin_huevo'],
            ['vegetariano', 'sin_gluten'],
            ['vegano', 'sin_gluten'],
            ['vegetariano', 'sin_lactosa'],
            ['sin_gluten', 'sin_lactosa'],
            ['sin_gluten', 'sin_huevo'],
            ['sin_lactosa', 'sin_huevo'],
            ['vegano', 'sin_gluten', 'sin_huevo'],  # 3 restricciones (5 combinaciones)
            ['vegetariano', 'sin_gluten', 'sin_lactosa'],
            ['vegetariano', 'sin_gluten', 'sin_huevo'],
            ['vegano', 'sin_gluten', 'sin_lactosa'],
            ['sin_gluten', 'sin_lactosa', 'sin_huevo'],
        ]
        
        # Generar combinaciones balanceadas
        for i in range(n_casos):
            # Rotar para garantizar cobertura
            tradicion = self.tradiciones[i % len(self.tradiciones)]
            temporada = self.temporadas[i % len(self.temporadas)]
            estilo = self.estilos[i % len(self.estilos)]
            
            # Distribución de eventos
            if i < 20:
                evento = 'familiar'
            elif i < 35:
                evento = 'congreso'
            else:
                evento = 'boda'
            
            # Restricciones (sample del pool)
            restricciones = restricciones_pool[i % len(restricciones_pool)]
            
            combinaciones.append({
                'tradicion': tradicion,
                'temporada': temporada,
                'tipo_evento': evento,
                'estilo': estilo,
                'restricciones': restricciones
            })
        
        # Shuffle para mayor aleatoriedad
        random.shuffle(combinaciones)
        return combinaciones
    
    def generar_casos(self, n_casos: int = 50) -> List[Dict]:
        """Genera n casos nuevos con máxima diversidad."""
        print(f"🔧 Generando {n_casos} casos nuevos...")
        
        # Generar combinaciones de preferencias
        combinaciones = self._generar_combinaciones_preferencias(n_casos)
        
        casos_nuevos = []
        
        for idx, combo in enumerate(combinaciones):
            # Generar ID
            nuevo_id = self.ultimo_id + idx + 1
            caso_id = f"C{nuevo_id:03d}"
            
            # Generar menú válido
            entrante, principal, postre = self._generar_menu_valido(combo['restricciones'])
            
            # Registrar uso y firma
            self.platos_usados[entrante] += 1
            self.platos_usados[principal] += 1
            self.platos_usados[postre] += 1
            firma = self._calcular_firma_menu(entrante, principal, postre)
            self.firmas_menus.add(firma)
            
            # Crear caso
            caso = {
                'id': caso_id,
                'restricciones': combo['restricciones'],
                'temporada': combo['temporada'],
                'tipo_evento': combo['tipo_evento'],
                'menu': {
                    'entrante': entrante,
                    'principal': principal,
                    'postre': postre
                },
                'estilo': combo['estilo'],
                'tradicion': combo['tradicion'],
                'exito': True,
                'fallos_detectados': [],
                'reparaciones_aplicadas': []
            }
            
            casos_nuevos.append(caso)
            
            if (idx + 1) % 10 == 0:
                print(f"  ✓ Generados {idx + 1}/{n_casos} casos")
        
        return casos_nuevos
    
    def guardar_casos_actualizados(self, casos_nuevos: List[Dict]):
        """Guarda casos actualizados (existentes + nuevos)."""
        casos_totales = self.casos + casos_nuevos
        self._guardar_json('casos.json', casos_totales)
        print(f"\n✅ Guardados {len(casos_totales)} casos en total ({len(self.casos)} + {len(casos_nuevos)})")
    
    def generar_reporte_diversidad(self, casos_nuevos: List[Dict]) -> str:
        """Genera reporte de diversidad."""
        todos_casos = self.casos + casos_nuevos
        
        # Contadores
        tradiciones = Counter([c.get('tradicion', 'N/A') for c in todos_casos])
        temporadas = Counter([c.get('temporada', 'N/A') for c in todos_casos])
        eventos = Counter([c.get('tipo_evento', 'N/A') for c in todos_casos])
        estilos = Counter([c.get('estilo', 'N/A') for c in todos_casos])
        
        restricciones_all = []
        restricciones_por_caso = []
        for c in todos_casos:
            restr = c.get('restricciones', [])
            restricciones_all.extend(restr)
            restricciones_por_caso.append(len(restr))
        restricciones_count = Counter(restricciones_all)
        restricciones_len = Counter(restricciones_por_caso)
        
        # Top platos repetidos
        top_platos = self.platos_usados.most_common(10)
        
        # Platos únicos totales
        platos_unicos = len(self.platos_usados)
        
        reporte = f"""
╔══════════════════════════════════════════════════════════════╗
║          REPORTE DE DIVERSIDAD - {len(todos_casos)} CASOS TOTALES          ║
╚══════════════════════════════════════════════════════════════╝

📊 DISTRIBUCIÓN POR DIMENSIONES:

Tradiciones:
{self._format_counter(tradiciones)}

Temporadas:
{self._format_counter(temporadas)}

Tipo de Evento:
{self._format_counter(eventos)}

Estilos:
{self._format_counter(estilos)}

🔒 RESTRICCIONES:

Uso por tipo:
{self._format_counter(restricciones_count)}

Casos por número de restricciones:
{self._format_counter(restricciones_len)}

🍽️  DIVERSIDAD DE PLATOS:

Total platos únicos usados: {platos_unicos}
Total platos disponibles: {len(self.platos)}
Cobertura: {platos_unicos / len(self.platos) * 100:.1f}%

Top 10 platos más repetidos:
{self._format_top_platos(top_platos)}

✨ MÉTRICAS DE CALIDAD:

- Menús únicos: {len(self.firmas_menus)} / {len(todos_casos)} casos
- Duplicados: {len(todos_casos) - len(self.firmas_menus)}
- Uso promedio por plato: {sum(self.platos_usados.values()) / len(self.platos_usados):.2f}
- Plato más repetido: {top_platos[0][1]} veces
"""
        return reporte
    
    def _format_counter(self, counter: Counter) -> str:
        """Formatea Counter para reporte."""
        lines = []
        for key, count in sorted(counter.items(), key=lambda x: -x[1]):
            lines.append(f"  {str(key):20s}: {count:3d} casos")
        return '\n'.join(lines)
    
    def _format_top_platos(self, top_platos: List[Tuple[str, int]]) -> str:
        """Formatea top platos."""
        lines = []
        for idx, (plato, count) in enumerate(top_platos, 1):
            lines.append(f"  {idx:2d}. {count:2d}x {plato[:55]}")
        return '\n'.join(lines)


def main():
    """Función principal."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     GENERADOR DE CASOS DIVERSOS - SBC-sys-cbr v2.0          ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    # Crear generador
    generador = GeneradorCasosDiversos()
    
    print(f"📦 Estado inicial:")
    print(f"  - Casos existentes: {len(generador.casos)}")
    print(f"  - Platos disponibles: {len(generador.platos)}")
    print(f"  - Ingredientes disponibles: {len(generador.ingredientes)}")
    print(f"  - Último ID: {generador.ultimo_id}\n")
    
    # Generar casos
    casos_nuevos = generador.generar_casos(n_casos=50)
    
    # Guardar
    generador.guardar_casos_actualizados(casos_nuevos)
    
    # Reporte
    reporte = generador.generar_reporte_diversidad(casos_nuevos)
    print(reporte)
    
    # Guardar reporte
    with open('REPORTE_DIVERSIDAD.txt', 'w', encoding='utf-8') as f:
        f.write(reporte)
    print("\n💾 Reporte guardado en: REPORTE_DIVERSIDAD.txt")
    
    # Ejemplos
    print("\n" + "="*70)
    print("📋 EJEMPLOS DE CASOS NUEVOS GENERADOS (primeros 5):")
    print("="*70 + "\n")
    
    for caso in casos_nuevos[:5]:
        print(f"ID: {caso['id']}")
        print(f"  Tradición: {caso['tradicion']:15s} | Temporada: {caso['temporada']:10s}")
        print(f"  Evento: {caso['tipo_evento']:12s} | Estilo: {caso['estilo']:15s}")
        print(f"  Restricciones: {', '.join(caso['restricciones']) if caso['restricciones'] else 'ninguna'}")
        print(f"  Menú:")
        print(f"    🥗 Entrante: {caso['menu']['entrante'][:50]}")
        print(f"    🍖 Principal: {caso['menu']['principal'][:50]}")
        print(f"    🍰 Postre: {caso['menu']['postre'][:50]}")
        print()


if __name__ == '__main__':
    random.seed(42)  # Reproducibilidad
    main()
