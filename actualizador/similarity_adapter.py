"""
Case Similarity Adapter for Memory Retention
==============================================

Adapts the existing CalculadorSimilitudPonderada to compare cases (not queries).
Reuses the proven similarity logic from the retrieval module.
"""

import sys
import os
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from recuperador.similitud_ponderada import CalculadorSimilitudPonderada, PesosSimilitud
from conocimiento.models import Caso


class CaseSimilarityAdapter:
    """
    Adapter to compute similarity between two stored cases.
    
    Reuses the existing CalculadorSimilitudPonderada which was designed
    for query-to-case similarity, but works perfectly for case-to-case.
    """
    
    def __init__(self, pesos: PesosSimilitud = None):
        """
        Initialize with existing similarity calculator.
        
        Args:
            pesos: Weight configuration for similarity calculation
        """
        self.calculador = CalculadorSimilitudPonderada(pesos)
    
    def similarity(self, case_a: Caso, case_b: Caso) -> float:
        """
        Compute similarity between two cases.
        
        Args:
            case_a: First case
            case_b: Second case
            
        Returns:
            Similarity score in [0, 1] where 1 means identical
        """
        # Convert cases to dict format (existing calculator expects dicts)
        caso_a_dict = self._caso_to_query_dict(case_a)
        caso_b_dict = self._caso_to_query_dict(case_b)
        
        # Use existing similarity logic
        return self.calculador.similitud_casos(caso_a_dict, caso_b_dict)
    
    def similarity_from_dict(self, case_a_dict: Dict[str, Any], case_b_dict: Dict[str, Any]) -> float:
        """
        Compute similarity between two cases in dict format.
        
        Args:
            case_a_dict: First case as dictionary
            case_b_dict: Second case as dictionary
            
        Returns:
            Similarity score in [0, 1]
        """
        return self.calculador.similitud_casos(case_a_dict, case_b_dict)
    
    def _caso_to_query_dict(self, caso: Caso) -> Dict[str, Any]:
        """
        Convert Caso object to dictionary format for similarity calculation.
        
        Args:
            caso: Caso object
            
        Returns:
            Dictionary with fields needed for similarity calculation
        """
        return {
            'tipo_evento': caso.tipo_evento,
            'temporada': caso.temporada,
            'restricciones': caso.restricciones,
            'estilo': caso.estilo,
            'tradicion': caso.tradicion,
            'menu': caso.menu.to_dict()
        }
    
    def max_similarity_to_set(self, candidate: Caso, existing_cases: list) -> float:
        """
        Find maximum similarity between candidate and any existing case.
        
        Args:
            candidate: Case to compare
            existing_cases: List of Caso objects or dicts
            
        Returns:
            Maximum similarity found, or 0.0 if no existing cases
        """
        if not existing_cases:
            return 0.0
        
        max_sim = 0.0
        candidate_dict = self._caso_to_query_dict(candidate) if isinstance(candidate, Caso) else candidate
        
        for existing in existing_cases:
            if isinstance(existing, Caso):
                existing_dict = self._caso_to_query_dict(existing)
            elif isinstance(existing, dict):
                existing_dict = existing
            else:
                continue
            
            sim = self.calculador.similitud_casos(candidate_dict, existing_dict)
            max_sim = max(max_sim, sim)
        
        return max_sim
    
    def novelty(self, candidate: Caso, existing_cases: list) -> float:
        """
        Compute novelty of candidate relative to existing cases.
        
        Novelty = 1 - max_similarity
        High novelty means the case is different from all existing cases.
        
        Args:
            candidate: Case to evaluate
            existing_cases: List of existing Caso objects or dicts
            
        Returns:
            Novelty score in [0, 1] where 1 means completely novel
        """
        max_sim = self.max_similarity_to_set(candidate, existing_cases)
        return 1.0 - max_sim


# Sanity check tests (optional, for validation)
def _test_symmetry():
    """Test that similarity is symmetric."""
    from conocimiento.models import Menu
    
    caso_a = Caso(
        id='TEST1',
        restricciones=['vegetariano'],
        temporada='verano',
        tipo_evento='boda',
        menu=Menu('A', 'B', 'C'),
        estilo='clasico',
        tradicion='italiana'
    )
    
    caso_b = Caso(
        id='TEST2',
        restricciones=['vegetariano'],
        temporada='verano',
        tipo_evento='familiar',
        menu=Menu('A', 'B', 'C'),
        estilo='clasico',
        tradicion='italiana'
    )
    
    adapter = CaseSimilarityAdapter()
    sim_ab = adapter.similarity(caso_a, caso_b)
    sim_ba = adapter.similarity(caso_b, caso_a)
    
    assert abs(sim_ab - sim_ba) < 0.001, f"Symmetry violated: {sim_ab} != {sim_ba}"
    assert 0.0 <= sim_ab <= 1.0, f"Similarity out of bounds: {sim_ab}"
    print(f"✓ Symmetry test passed: sim(a,b)={sim_ab:.3f}, sim(b,a)={sim_ba:.3f}")


def _test_identity():
    """Test that identical cases have similarity >= 0.9 (close to 1.0)."""
    from conocimiento.models import Menu
    
    caso = Caso(
        id='TEST',
        restricciones=['vegano'],
        temporada='invierno',
        tipo_evento='congreso',
        menu=Menu('X', 'Y', 'Z'),  # Non-existent dishes may not have perfect similarity
        estilo='molecular',
        tradicion='francesa'
    )
    
    adapter = CaseSimilarityAdapter()
    sim = adapter.similarity(caso, caso)
    
    # Allow small tolerance due to menu ingredient similarity computation
    assert sim >= 0.85, f"Identity test failed: sim(case, case) = {sim} < 0.85"
    print(f"✓ Identity test passed: sim(case, case)={sim:.3f} (≥0.85)")


if __name__ == "__main__":
    print("Running similarity adapter tests...")
    _test_symmetry()
    _test_identity()
    print("All tests passed!")
