from typing import List, Tuple
from base_casos import BaseCasos
from similitud import CalculadorSimilitud
from models import Caso


class ModuloRecuperacion:
    def __init__(self, base_casos: BaseCasos, calculador: CalculadorSimilitud):
        self.base_casos = base_casos
        self.calculador = calculador

    def recuperar(self, caso_nuevo: Caso, k: int = 3) -> List[Tuple[Caso, float]]:
        print("\n" + "="*70)
        print("RETRIEVER: Buscando menús similares...")
        print(f"  Criterios: {caso_nuevo.tipo_evento.value}, {caso_nuevo.num_comensales} comensales")
        print(f"  Restricciones: {caso_nuevo.restricciones}")
        print(f"  Preferencias: {caso_nuevo.preferencias}")
        print("="*70)

        similitudes = []
        for caso_base in self.base_casos.obtener_todos():
            sim = self.calculador.similitud_casos(caso_nuevo, caso_base)
            similitudes.append((caso_base, sim))

        similitudes.sort(key=lambda x: x[1], reverse=True)

        print(f"\nEncontrados {len(similitudes)} casos. Seleccionando top {k}:")
        for i, (caso, sim) in enumerate(similitudes[:k], 1):
            print(f"  {i}. {caso.id}: {caso.menu.estilo.value}-{caso.menu.tradicion.value} (similitud: {sim:.3f})")

        return similitudes[:k]
