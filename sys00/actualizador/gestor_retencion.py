"""
Gestor de Retención de Casos (Memory Curation)
==============================================

Implementa la lógica de "remember vs forget" para evitar saturación de memoria
mientras mantiene diversidad y calidad en la base de casos.

Criterios de retención:
1. Satisfacción del usuario (satisfaction_score)
2. Dificultad de obtención (modification_count) - priorizamos casos difíciles
3. Novedad/Diversidad (novelty) - evitamos redundancia

Estrategia:
- Si memoria < límite: agregar caso
- Si memoria >= límite: 
  1. Identificar clusters de casi-duplicados, mantener el mejor de cada cluster
  2. Si sigue excedido, eliminar casos con menor keep_score global
"""

import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from .config_retencion import ConfiguracionRetencion, CONFIG_RETENCION_DEFAULT
from .similitud_casos import SimilitudCasos
from .recolector_satisfaccion import SatisfaccionCaso


@dataclass
class MetricasRetencion:
    """Métricas calculadas para decidir retención de un caso."""
    caso_id: str
    satisfaction_score: float  # Normalizado [0,1]
    modification_bonus: float  # log(1 + count) normalizado [0,1]
    novelty: float  # 1 - max_sim, [0,1]
    keep_score: float  # Puntuación final ponderada
    modification_count: int  # Conteo bruto de modificaciones
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'caso_id': self.caso_id,
            'satisfaction_score': self.satisfaction_score,
            'modification_bonus': self.modification_bonus,
            'novelty': self.novelty,
            'keep_score': self.keep_score,
            'modification_count': self.modification_count
        }


class GestorRetencion:
    """
    Gestiona la curación de memoria: decide qué casos recordar y cuáles olvidar.
    """
    
    # Constante para normalizar modification_bonus (log(1 + MAX_MODS_ESPERADAS))
    MAX_MODIFICATION_LOG = math.log(1 + 10)  # Asumimos que 10 modificaciones es "mucho"
    
    def __init__(self, config: ConfiguracionRetencion = None):
        """
        Inicializa el gestor de retención.
        
        Args:
            config: Configuración de retención
        """
        self.config = config or CONFIG_RETENCION_DEFAULT
        self.similitud = SimilitudCasos()
        self._log_acciones = []  # Log de acciones de retención
    
    def calcular_metricas(self, caso: Dict[str, Any], 
                          casos_memoria: List[Dict[str, Any]]) -> MetricasRetencion:
        """
        Calcula las métricas de retención para un caso.
        
        Args:
            caso: Caso a evaluar (diccionario)
            casos_memoria: Casos actualmente en memoria (sin incluir el caso a evaluar)
            
        Returns:
            MetricasRetencion con todas las métricas calculadas
        """
        caso_id = caso.get('id', 'unknown')
        
        # 1. Satisfaction score (normalizado a [0,1])
        satisfaction_raw = self._extraer_satisfaction(caso)
        satisfaction_norm = self._normalizar_satisfaction(satisfaction_raw)
        
        # 2. Modification bonus (log normalizado)
        mod_count = self._contar_modificaciones(caso)
        mod_bonus = self._calcular_modification_bonus(mod_count)
        
        # 3. Novelty
        novelty = self.similitud.novelty(caso, casos_memoria)
        
        # 4. Keep score (combinación ponderada)
        keep_score = (
            self.config.weight_satisfaction * satisfaction_norm +
            self.config.weight_modifications * mod_bonus +
            self.config.weight_novelty * novelty
        )
        
        return MetricasRetencion(
            caso_id=caso_id,
            satisfaction_score=satisfaction_norm,
            modification_bonus=mod_bonus,
            novelty=novelty,
            keep_score=keep_score,
            modification_count=mod_count
        )
    
    def _extraer_satisfaction(self, caso: Dict) -> Optional[float]:
        """Extrae el satisfaction_score de un caso (compatible con casos antiguos)."""
        # Intentar obtener de satisfaccion (nuevo formato)
        satisfaccion = caso.get('satisfaccion')
        if satisfaccion:
            if isinstance(satisfaccion, dict):
                return satisfaccion.get('satisfaction_score')
            elif isinstance(satisfaccion, (int, float)):
                return float(satisfaccion)
        
        # Intentar campo directo satisfaction_score
        score = caso.get('satisfaction_score')
        if score is not None:
            return float(score)
        
        # Caso antiguo sin satisfacción
        return None
    
    def _normalizar_satisfaction(self, score: Optional[float]) -> float:
        """
        Normaliza satisfaction a [0, 1].
        
        Args:
            score: Puntuación raw (puede ser None)
            
        Returns:
            Valor normalizado [0, 1]. Si None, retorna 0.5 (neutral)
        """
        if score is None:
            return 0.5  # Valor neutral para casos sin rating
        
        min_val = self.config.rating_scale_min
        max_val = self.config.rating_scale_max
        
        # Normalizar de [min, max] a [0, 1]
        return (score - min_val) / (max_val - min_val)
    
    def _contar_modificaciones(self, caso: Dict) -> int:
        """
        Cuenta el número de modificaciones aplicadas a un caso.
        
        Args:
            caso: Diccionario del caso
            
        Returns:
            Número de modificaciones
        """
        # Intentar campo modification_count (nuevo)
        count = caso.get('modification_count')
        if count is not None:
            return int(count)
        
        # Contar desde reparaciones_aplicadas
        reparaciones = caso.get('reparaciones_aplicadas', [])
        
        if not reparaciones:
            return 0
        
        # Contar modificaciones totales
        total = 0
        for rep in reparaciones:
            if isinstance(rep, dict):
                # Contar modificaciones dentro de cada reparación
                mods = rep.get('modificaciones', [])
                total += len(mods) if mods else 1
            else:
                total += 1
        
        return total
    
    def _calcular_modification_bonus(self, count: int) -> float:
        """
        Calcula el bonus por modificaciones (normalizado a [0, 1]).
        
        Usa log(1 + count) para dar más peso a las primeras modificaciones
        y decrecer la ganancia marginal.
        
        Args:
            count: Número de modificaciones
            
        Returns:
            Bonus normalizado [0, 1]
        """
        if count <= 0:
            return 0.0
        
        raw_bonus = math.log(1 + count)
        normalized = min(1.0, raw_bonus / self.MAX_MODIFICATION_LOG)
        
        return normalized
    
    def curar_memoria(self, casos_actuales: List[Dict[str, Any]], 
                      caso_nuevo: Dict[str, Any] = None) -> Tuple[List[Dict], List[str]]:
        """
        Realiza la curación de memoria.
        
        Si hay un caso nuevo, lo incorpora.
        Si se excede el límite, elimina casos según la política de retención.
        
        Args:
            casos_actuales: Lista de casos actualmente en memoria
            caso_nuevo: Caso nuevo a agregar (opcional)
            
        Returns:
            Tuple de (casos_retenidos, ids_eliminados)
        """
        casos = list(casos_actuales)
        ids_eliminados = []
        
        # Si hay caso nuevo, agregarlo temporalmente
        if caso_nuevo:
            casos.append(caso_nuevo)
            self._log(f"Agregando caso nuevo: {caso_nuevo.get('id', 'unknown')}")
        
        # Si estamos bajo el límite, no hay nada que hacer
        if len(casos) <= self.config.max_cases:
            self._log(f"Memoria OK: {len(casos)}/{self.config.max_cases} casos")
            return casos, ids_eliminados
        
        self._log(f"⚠️ Memoria excedida: {len(casos)}/{self.config.max_cases} casos. Iniciando curación...")
        
        # Paso 1: Calcular métricas para todos los casos
        metricas = {}
        for caso in casos:
            otros_casos = [c for c in casos if c.get('id') != caso.get('id')]
            metricas[caso.get('id')] = self.calcular_metricas(caso, otros_casos)
        
        # Paso 2: Identificar y reducir clusters de casi-duplicados
        casos, eliminados_dup = self._reducir_duplicados(casos, metricas)
        ids_eliminados.extend(eliminados_dup)
        
        # Paso 3: Si aún excede, eliminar por keep_score más bajo
        while len(casos) > self.config.max_cases:
            # Recalcular métricas (la novedad cambia al eliminar casos)
            metricas = {}
            for caso in casos:
                otros = [c for c in casos if c.get('id') != caso.get('id')]
                metricas[caso.get('id')] = self.calcular_metricas(caso, otros)
            
            # Encontrar caso con menor keep_score
            caso_menor = min(casos, key=lambda c: metricas[c.get('id')].keep_score)
            caso_id = caso_menor.get('id')
            
            m = metricas[caso_id]
            self._log(f"  Eliminando caso {caso_id} (keep_score={m.keep_score:.3f}, "
                     f"sat={m.satisfaction_score:.2f}, mod={m.modification_bonus:.2f}, "
                     f"nov={m.novelty:.2f})")
            
            casos.remove(caso_menor)
            ids_eliminados.append(caso_id)
        
        self._log(f"Curación completada: {len(casos)} casos retenidos, "
                 f"{len(ids_eliminados)} eliminados")
        
        return casos, ids_eliminados
    
    def _reducir_duplicados(self, casos: List[Dict], 
                            metricas: Dict[str, MetricasRetencion]) -> Tuple[List[Dict], List[str]]:
        """
        Reduce clusters de casi-duplicados manteniendo el mejor de cada grupo.
        
        Args:
            casos: Lista de casos
            metricas: Métricas precalculadas por ID
            
        Returns:
            Tuple de (casos_reducidos, ids_eliminados)
        """
        ids_eliminados = []
        
        # Encontrar clusters de casi-duplicados
        clusters = self.similitud.find_near_duplicates(
            casos, 
            threshold=self.config.similarity_duplicate_threshold
        )
        
        if not clusters:
            return casos, ids_eliminados
        
        self._log(f"  Encontrados {len(clusters)} clusters de casi-duplicados")
        
        # Para cada cluster, mantener solo el caso con mayor keep_score
        casos_a_eliminar_ids = set()
        
        for cluster in clusters:
            # Obtener casos del cluster
            casos_cluster = [casos[i] for i in cluster]
            
            # Encontrar el mejor (mayor keep_score)
            mejor = max(casos_cluster, key=lambda c: metricas[c.get('id')].keep_score)
            mejor_id = mejor.get('id')
            
            # Marcar los demás para eliminación
            for caso in casos_cluster:
                caso_id = caso.get('id')
                if caso_id != mejor_id:
                    casos_a_eliminar_ids.add(caso_id)
                    self._log(f"    Duplicado: {caso_id} -> manteniendo {mejor_id}")
        
        # Eliminar casos marcados
        casos_filtrados = [c for c in casos if c.get('id') not in casos_a_eliminar_ids]
        ids_eliminados = list(casos_a_eliminar_ids)
        
        return casos_filtrados, ids_eliminados
    
    def debe_retener_caso(self, caso: Dict[str, Any], 
                          casos_memoria: List[Dict[str, Any]],
                          satisfaccion: SatisfaccionCaso = None) -> Tuple[bool, str]:
        """
        Decide si un caso debe ser retenido.
        
        Args:
            caso: Caso candidato
            casos_memoria: Casos actuales en memoria
            satisfaccion: Información de satisfacción del caso
            
        Returns:
            Tuple de (debe_retener, razon)
        """
        caso_id = caso.get('id', 'unknown')
        
        # Verificar política de rating
        if self.config.require_rating_for_retention:
            if satisfaccion is None or not satisfaccion.has_rating():
                return False, f"Caso {caso_id} sin rating y require_rating_for_retention=True"
        
        # Si hay espacio, siempre retener
        if len(casos_memoria) < self.config.max_cases:
            return True, f"Espacio disponible ({len(casos_memoria)}/{self.config.max_cases})"
        
        # Calcular métricas del nuevo caso
        metricas_nuevo = self.calcular_metricas(caso, casos_memoria)
        
        # Encontrar el caso con menor keep_score en memoria
        metricas_memoria = [
            self.calcular_metricas(c, [x for x in casos_memoria if x != c])
            for c in casos_memoria
        ]
        peor_caso = min(metricas_memoria, key=lambda m: m.keep_score)
        
        # Si el nuevo caso es mejor que el peor en memoria, retener
        if metricas_nuevo.keep_score > peor_caso.keep_score:
            return True, (f"Nuevo caso mejor que {peor_caso.caso_id} "
                         f"({metricas_nuevo.keep_score:.3f} > {peor_caso.keep_score:.3f})")
        
        # Verificar si aporta novedad significativa
        if metricas_nuevo.novelty > 0.5:
            return True, f"Alta novedad ({metricas_nuevo.novelty:.3f})"
        
        return False, (f"Keep_score insuficiente ({metricas_nuevo.keep_score:.3f}) "
                      f"y baja novedad ({metricas_nuevo.novelty:.3f})")
    
    def _log(self, mensaje: str):
        """Registra una acción de retención."""
        entrada = {
            'timestamp': datetime.now().isoformat(),
            'mensaje': mensaje
        }
        self._log_acciones.append(entrada)
        print(f"[Retención] {mensaje}")
    
    def obtener_log(self) -> List[Dict]:
        """Retorna el log de acciones de retención."""
        return list(self._log_acciones)
    
    def limpiar_log(self):
        """Limpia el log de acciones."""
        self._log_acciones = []
    
    def resumen_memoria(self, casos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Genera un resumen del estado de la memoria.
        
        Args:
            casos: Lista de casos en memoria
            
        Returns:
            Diccionario con estadísticas
        """
        if not casos:
            return {
                'total_casos': 0,
                'capacidad_usada': 0.0,
                'satisfaccion_promedio': None,
                'modificaciones_promedio': 0.0,
                'diversidad_estimada': 1.0
            }
        
        # Calcular estadísticas
        satisfacciones = []
        modificaciones = []
        
        for caso in casos:
            sat = self._extraer_satisfaction(caso)
            if sat is not None:
                satisfacciones.append(sat)
            modificaciones.append(self._contar_modificaciones(caso))
        
        # Estimar diversidad como promedio de novelty
        if len(casos) > 1:
            novedades = []
            for caso in casos:
                otros = [c for c in casos if c.get('id') != caso.get('id')]
                nov = self.similitud.novelty(caso, otros)
                novedades.append(nov)
            diversidad = sum(novedades) / len(novedades)
        else:
            diversidad = 1.0
        
        return {
            'total_casos': len(casos),
            'max_casos': self.config.max_cases,
            'capacidad_usada': len(casos) / self.config.max_cases,
            'satisfaccion_promedio': sum(satisfacciones) / len(satisfacciones) if satisfacciones else None,
            'modificaciones_promedio': sum(modificaciones) / len(modificaciones),
            'diversidad_estimada': diversidad,
            'casos_con_rating': len(satisfacciones),
            'casos_sin_rating': len(casos) - len(satisfacciones)
        }
