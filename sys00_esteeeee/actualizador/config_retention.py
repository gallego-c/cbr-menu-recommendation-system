"""
Configuration for CBR Case Retention System
=============================================

Configures memory management, satisfaction scoring, and retention policies.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RetentionConfig:
    """Configuration for the retention/retain module."""
    
    # Memory limits
    max_cases: int = 25  # Maximum number of cases to store
    min_cases: int = 20   # Minimum cases to keep (never drop below this)
    
    # Retention weights (must sum to ~1.0)
    weight_satisfaction: float = 0.40  # User satisfaction score
    weight_modifications: float = 0.35 # Complexity (hard-to-reach cases)
    weight_novelty: float = 0.25       # Diversity/coverage
    
    # Similarity thresholds for deduplication
    near_duplicate_threshold: float = 0.90  # Cases above this are near-duplicates
    
    # Rating configuration
    rating_scale_min: int = 1
    rating_scale_max: int = 5
    rating_required: bool = False  # If False, allow skipping with neutral score
    default_satisfaction_if_skipped: float = 3.0  # Neutral default
    
    # Non-interactive mode settings
    non_interactive_default: Optional[float] = None  # If None, uses default_satisfaction
    
    # Modification bonus settings
    modification_bonus_scale: float = 0.5  # log(1 + count * scale)
    
    def __post_init__(self):
        """Validate configuration."""
        total_weight = self.weight_satisfaction + self.weight_modifications + self.weight_novelty
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Retention weights must sum to 1.0, got {total_weight}")
        
        if self.max_cases < self.min_cases:
            raise ValueError(f"max_cases ({self.max_cases}) must be >= min_cases ({self.min_cases})")


# Default global configuration instance
DEFAULT_RETENTION_CONFIG = RetentionConfig()
