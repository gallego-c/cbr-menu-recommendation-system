"""
Memory Curator - Case Retention and Forgetting Logic
=====================================================

Implements bounded memory with intelligent retention based on:
- Satisfaction scores (quality)
- Modification count (complexity/hard-to-reach cases)
- Novelty/diversity (coverage of solution space)
"""

import sys
import os
import math
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from conocimiento.models import Caso

# Handle imports for both module and standalone execution
if __name__ == "__main__":
    from config_retention import RetentionConfig, DEFAULT_RETENTION_CONFIG
    from similarity_adapter import CaseSimilarityAdapter
else:
    from .config_retention import RetentionConfig, DEFAULT_RETENTION_CONFIG
    from .similarity_adapter import CaseSimilarityAdapter


class MemoryCurator:
    """
    Manages case memory with intelligent retention/forgetting.
    
    Key responsibilities:
    1. Decide which cases to keep vs forget when memory is full
    2. Prioritize high-satisfaction, high-complexity, diverse cases
    3. Remove near-duplicates to maintain diversity
    4. Never drop below minimum case count
    """
    
    def __init__(self, config: RetentionConfig = None):
        """
        Initialize memory curator.
        
        Args:
            config: Retention configuration
        """
        self.config = config or DEFAULT_RETENTION_CONFIG
        self.similarity_adapter = CaseSimilarityAdapter()
    
    def should_retain_case(self, candidate: Caso, existing_cases: List[Dict[str, Any]]) -> Tuple[bool, str, Dict[str, float]]:
        """
        Decide whether to retain a new candidate case.
        
        Args:
            candidate: Candidate case to evaluate
            existing_cases: List of existing case dictionaries
            
        Returns:
            Tuple of (should_retain, reason, metrics_dict)
        """
        current_count = len(existing_cases)
        
        # Always retain if below max
        if current_count < self.config.max_cases:
            metrics = self._compute_case_metrics(candidate, existing_cases)
            return (True, f"Memory below cap ({current_count}/{self.config.max_cases})", metrics)
        
        # Memory at/above cap - need to compare with existing cases
        metrics = self._compute_case_metrics(candidate, existing_cases)
        candidate_score = metrics['keep_score']
        
        # Find lowest scoring existing case
        existing_casos_obj = [Caso.from_dict(c) for c in existing_cases]
        existing_scores = [self._compute_case_metrics(c, existing_cases) for c in existing_casos_obj]
        
        min_existing_score = min(s['keep_score'] for s in existing_scores)
        
        if candidate_score > min_existing_score:
            return (True, f"Higher value than worst existing case ({candidate_score:.3f} > {min_existing_score:.3f})", metrics)
        else:
            return (False, f"Lower value than all existing cases ({candidate_score:.3f} <= {min_existing_score:.3f})", metrics)
    
    def curate_memory(self, cases: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Curate memory by removing low-value and redundant cases.
        
        Process:
        1. If below cap: no action
        2. If above cap: remove near-duplicates first, then lowest-value cases
        
        Args:
            cases: List of case dictionaries
            
        Returns:
            Tuple of (curated_cases, removed_case_ids)
        """
        if len(cases) <= self.config.max_cases:
            return (cases, [])
        
        print(f"\n[MEMORY CURATION] Memory above cap: {len(cases)} > {self.config.max_cases}")
        
        # Convert to Caso objects for processing
        casos_obj = [Caso.from_dict(c) for c in cases]
        
        # Step 1: Remove near-duplicates
        casos_obj, removed_dups = self._remove_near_duplicates(casos_obj)
        print(f"  Removed {len(removed_dups)} near-duplicate cases")
        
        # Step 2: If still above cap, remove lowest-value cases
        removed_low_value = []
        if len(casos_obj) > self.config.max_cases:
            casos_obj, removed_low_value = self._remove_lowest_value(casos_obj, self.config.max_cases)
            print(f"  Removed {len(removed_low_value)} low-value cases")
        
        # Ensure we never drop below minimum
        if len(casos_obj) < self.config.min_cases:
            print(f"  WARNING: Would drop below min_cases ({self.config.min_cases}). Keeping all cases.")
            return (cases, [])
        
        # Convert back to dicts
        curated_cases = [c.to_dict() for c in casos_obj]
        all_removed = removed_dups + removed_low_value
        
        print(f"  Final memory size: {len(curated_cases)}")
        
        return (curated_cases, all_removed)
    
    def _remove_near_duplicates(self, casos: List[Caso]) -> Tuple[List[Caso], List[str]]:
        """
        Remove near-duplicate cases, keeping the higher-value one in each cluster.
        
        Args:
            casos: List of Caso objects
            
        Returns:
            Tuple of (remaining_cases, removed_ids)
        """
        if len(casos) <= 1:
            return (casos, [])
        
        # Build similarity matrix (only upper triangle)
        n = len(casos)
        near_duplicate_pairs = []
        
        for i in range(n):
            for j in range(i + 1, n):
                sim = self.similarity_adapter.similarity(casos[i], casos[j])
                if sim >= self.config.near_duplicate_threshold:
                    near_duplicate_pairs.append((i, j, sim))
        
        if not near_duplicate_pairs:
            return (casos, [])
        
        # For each pair, mark the lower-value case for removal
        to_remove = set()
        cases_as_dicts = [c.to_dict() for c in casos]
        
        for i, j, sim in near_duplicate_pairs:
            if i in to_remove or j in to_remove:
                continue  # Already marked
            
            # Compute keep scores
            metrics_i = self._compute_case_metrics(casos[i], cases_as_dicts)
            metrics_j = self._compute_case_metrics(casos[j], cases_as_dicts)
            
            # Remove the lower-value one
            if metrics_i['keep_score'] < metrics_j['keep_score']:
                to_remove.add(i)
            else:
                to_remove.add(j)
        
        # Filter out removed cases
        remaining = [c for idx, c in enumerate(casos) if idx not in to_remove]
        removed_ids = [casos[idx].id for idx in to_remove]
        
        return (remaining, removed_ids)
    
    def _remove_lowest_value(self, casos: List[Caso], target_count: int) -> Tuple[List[Caso], List[str]]:
        """
        Remove lowest-value cases until target count is reached.
        
        Args:
            casos: List of Caso objects
            target_count: Desired number of cases
            
        Returns:
            Tuple of (remaining_cases, removed_ids)
        """
        if len(casos) <= target_count:
            return (casos, [])
        
        # Compute keep scores for all cases
        cases_as_dicts = [c.to_dict() for c in casos]
        scored_cases = []
        
        for caso in casos:
            metrics = self._compute_case_metrics(caso, cases_as_dicts)
            scored_cases.append((caso, metrics['keep_score']))
        
        # Sort by score (ascending) - lowest first
        scored_cases.sort(key=lambda x: x[1])
        
        # Remove lowest until target
        num_to_remove = len(casos) - target_count
        removed = scored_cases[:num_to_remove]
        remaining = scored_cases[num_to_remove:]
        
        removed_ids = [c.id for c, _ in removed]
        remaining_casos = [c for c, _ in remaining]
        
        return (remaining_casos, removed_ids)
    
    def _compute_case_metrics(self, caso: Caso, existing_cases: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Compute all metrics for a case to determine retention value.
        
        Args:
            caso: Caso object to evaluate
            existing_cases: List of existing case dicts (for novelty calculation)
            
        Returns:
            Dictionary with metrics:
            - satisfaction_normalized: Normalized satisfaction [0,1]
            - modification_bonus: Bonus for complexity [0,1]
            - novelty: Diversity score [0,1]
            - keep_score: Weighted aggregate [0,1]
        """
        # 1. Satisfaction score (normalized to [0,1])
        if caso.satisfaction_score is not None:
            sat_normalized = (caso.satisfaction_score - self.config.rating_scale_min) / (
                self.config.rating_scale_max - self.config.rating_scale_min
            )
        else:
            # No rating - use neutral (0.5 normalized from 3.0 on 1-5 scale)
            sat_normalized = 0.5
        
        # 2. Modification bonus (logarithmic scaling for diminishing returns)
        mod_count = caso.modification_count if hasattr(caso, 'modification_count') else 0
        if mod_count > 0:
            # log(1 + count * scale) / log(1 + max_reasonable * scale)
            # Assume max_reasonable = 20 modifications
            max_reasonable = 20
            mod_bonus = math.log(1 + mod_count * self.config.modification_bonus_scale) / \
                       math.log(1 + max_reasonable * self.config.modification_bonus_scale)
        else:
            mod_bonus = 0.0
        
        # 3. Novelty (diversity relative to existing cases)
        # Exclude the case itself if it's in existing_cases
        filtered_existing = [c for c in existing_cases if c.get('id') != caso.id]
        if filtered_existing:
            casos_obj = [Caso.from_dict(c) for c in filtered_existing]
            novelty = self.similarity_adapter.novelty(caso, casos_obj)
        else:
            novelty = 1.0  # Completely novel if no other cases
        
        # 4. Compute weighted keep score
        keep_score = (
            self.config.weight_satisfaction * sat_normalized +
            self.config.weight_modifications * mod_bonus +
            self.config.weight_novelty * novelty
        )
        
        return {
            'satisfaction_normalized': sat_normalized,
            'modification_bonus': mod_bonus,
            'novelty': novelty,
            'keep_score': keep_score
        }
    
    def explain_retention_decision(self, caso: Caso, existing_cases: List[Dict[str, Any]]) -> str:
        """
        Generate human-readable explanation of retention decision.
        
        Args:
            caso: Case to explain
            existing_cases: Existing cases
            
        Returns:
            Explanation string
        """
        metrics = self._compute_case_metrics(caso, existing_cases)
        
        lines = [
            f"Retention metrics for case {caso.id}:",
            f"  Satisfaction: {metrics['satisfaction_normalized']:.3f} (weight: {self.config.weight_satisfaction})",
            f"  Modifications: {metrics['modification_bonus']:.3f} (weight: {self.config.weight_modifications}, count: {caso.modification_count})",
            f"  Novelty: {metrics['novelty']:.3f} (weight: {self.config.weight_novelty})",
            f"  → Keep Score: {metrics['keep_score']:.3f}"
        ]
        
        return "\n".join(lines)


# Simple test
if __name__ == "__main__":
    from conocimiento.models import Menu
    
    print("Testing MemoryCurator...")
    
    # Create test cases
    test_cases = [
        Caso(
            id='C001', restricciones=[], temporada='verano', tipo_evento='boda',
            menu=Menu('A', 'B', 'C'), estilo='clasico', tradicion='italiana',
            satisfaction_score=4.5, modification_count=2
        ),
        Caso(
            id='C002', restricciones=[], temporada='verano', tipo_evento='boda',
            menu=Menu('A', 'B', 'C'), estilo='clasico', tradicion='italiana',
            satisfaction_score=3.0, modification_count=0  # Near-duplicate with lower satisfaction
        ),
        Caso(
            id='C003', restricciones=['vegano'], temporada='invierno', tipo_evento='familiar',
            menu=Menu('X', 'Y', 'Z'), estilo='molecular', tradicion='francesa',
            satisfaction_score=5.0, modification_count=10  # High value, diverse
        ),
    ]
    
    curator = MemoryCurator()
    
    # Test metrics computation
    print("\n--- Metrics ---")
    for caso in test_cases:
        existing = [c.to_dict() for c in test_cases]
        print(curator.explain_retention_decision(caso, existing))
        print()
    
    # Test curation (with low max to force removal)
    config_small = RetentionConfig(max_cases=2, min_cases=1)
    curator_small = MemoryCurator(config_small)
    
    cases_dict = [c.to_dict() for c in test_cases]
    curated, removed = curator_small.curate_memory(cases_dict)
    
    print(f"\n--- Curation Test ---")
    print(f"Original: {len(cases_dict)} cases")
    print(f"Curated: {len(curated)} cases")
    print(f"Removed: {removed}")
