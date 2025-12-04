from typing import List
from models import Caso


class CalculadorSimilitud:
    def __init__(self):
        self.pesos = {
            'tipo_evento': 0.25,
            'num_comensales': 0.15,
            'presupuesto': 0.15,
            'restricciones': 0.20,
            'preferencias': 0.15,
            'temporada': 0.10
        }

    def similitud_casos(self, caso_nuevo: Caso, caso_base: Caso) -> float:
        # Calcula la similitud entre diferentes atributos de los casos y los suma ponderadamente
        sim_tipo = 1.0 if caso_nuevo.tipo_evento == caso_base.tipo_evento else 0.0

        sim_comensales = self._similitud_numerica(
            caso_nuevo.num_comensales,
            caso_base.num_comensales,
            rango_max=200
        )

        sim_presupuesto = self._similitud_numerica(
            caso_nuevo.presupuesto,
            caso_base.presupuesto,
            rango_max=10000
        )

        sim_restricciones = self._similitud_conjuntos(
            caso_nuevo.restricciones,
            caso_base.restricciones
        )

        sim_preferencias = self._similitud_conjuntos(
            caso_nuevo.preferencias,
            caso_base.preferencias
        )

        sim_temporada = 1.0 if caso_nuevo.temporada == caso_base.temporada else 0.5

        similitud_total = (
            self.pesos['tipo_evento'] * sim_tipo +
            self.pesos['num_comensales'] * sim_comensales +
            self.pesos['presupuesto'] * sim_presupuesto +
            self.pesos['restricciones'] * sim_restricciones +
            self.pesos['preferencias'] * sim_preferencias +
            self.pesos['temporada'] * sim_temporada
        )

        return similitud_total

    def _similitud_numerica(self, val1: float, val2: float, rango_max: float) -> float:
        # Calcula la similitud numérica normalizada entre 0 y 1
        diferencia = abs(val1 - val2)
        return max(0, 1 - (diferencia / rango_max))

    def _similitud_conjuntos(self, set1: List[str], set2: List[str]) -> float:
        # Calcula intersección sobre unión (Jaccard)
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0

        s1 = set(set1)
        s2 = set(set2)
        interseccion = len(s1 & s2)
        union = len(s1 | s2)

        return interseccion / union if union > 0 else 0.0
