"""
Interactive Rating Collector for Menu Satisfaction
===================================================

Collects user ratings for generated menus with interactive prompts
and non-interactive fallback mode.
"""

import sys
from typing import Dict, Optional, Tuple
from datetime import datetime

from .config_retention import RetentionConfig, DEFAULT_RETENTION_CONFIG


class RatingCollector:
    """
    Collects satisfaction ratings from users interactively.
    
    Supports:
    - Interactive CLI mode (input prompts)
    - Non-interactive mode (configurable defaults)
    - Individual menu item ratings
    - Aggregate case-level scores
    """
    
    def __init__(self, config: RetentionConfig = None):
        """
        Initialize rating collector.
        
        Args:
            config: Retention configuration (uses default if None)
        """
        self.config = config or DEFAULT_RETENTION_CONFIG
        self._is_interactive = self._check_interactive()
    
    def _check_interactive(self) -> bool:
        """
        Check if running in interactive mode.
        
        Returns:
            True if stdin is a terminal (interactive)
        """
        return sys.stdin.isatty()
    
    def collect_menu_rating(self, menu: Dict[str, str], caso_id: str = None) -> Tuple[Optional[float], Optional[Dict[str, float]], str]:
        """
        Collect rating for a complete menu.
        
        Args:
            menu: Dictionary with 'entrante', 'principal', 'postre'
            caso_id: Optional case ID for display
            
        Returns:
            Tuple of (aggregate_score, per_menu_scores, timestamp)
            aggregate_score: Overall satisfaction (1-5) or None if skipped
            per_menu_scores: Individual ratings dict or None
            timestamp: ISO format timestamp
        """
        timestamp = datetime.now().isoformat()
        
        if not self._is_interactive:
            return self._handle_non_interactive()
        
        print("\n" + "="*70)
        print("SATISFACCIÓN DEL MENÚ GENERADO")
        print("="*70)
        
        if caso_id:
            print(f"Caso: {caso_id}")
        
        print("\nMenú generado:")
        print(f"  Entrante:  {menu.get('entrante', 'N/A')}")
        print(f"  Principal: {menu.get('principal', 'N/A')}")
        print(f"  Postre:    {menu.get('postre', 'N/A')}")
        print()
        
        # Ask if user wants to rate
        if not self.config.rating_required:
            print("¿Desea calificar este menú? (s/n): ", end='', flush=True)
            try:
                response = input().strip().lower()
                if response not in ['s', 'si', 'sí', 'y', 'yes']:
                    print(f"Calificación omitida. Usando valor neutral: {self.config.default_satisfaction_if_skipped}")
                    return (self.config.default_satisfaction_if_skipped, None, timestamp)
            except (EOFError, KeyboardInterrupt):
                print("\nCalificación omitida.")
                return (self.config.default_satisfaction_if_skipped, None, timestamp)
        
        # Collect individual ratings
        per_menu_scores = {}
        ratings_collected = []
        
        for tipo_plato, nombre_plato in [('entrante', menu.get('entrante')), 
                                          ('principal', menu.get('principal')), 
                                          ('postre', menu.get('postre'))]:
            if not nombre_plato:
                continue
            
            rating = self._prompt_rating_for_dish(tipo_plato, nombre_plato)
            if rating is not None:
                per_menu_scores[tipo_plato] = rating
                ratings_collected.append(rating)
        
        # Compute aggregate
        if ratings_collected:
            aggregate_score = sum(ratings_collected) / len(ratings_collected)
            print(f"\nCalificación promedio: {aggregate_score:.2f}/{self.config.rating_scale_max}")
        else:
            aggregate_score = self.config.default_satisfaction_if_skipped
            per_menu_scores = None
            print(f"Sin calificaciones individuales. Usando neutral: {aggregate_score}")
        
        return (aggregate_score, per_menu_scores, timestamp)
    
    def _prompt_rating_for_dish(self, tipo_plato: str, nombre_plato: str, max_retries: int = 3) -> Optional[float]:
        """
        Prompt for rating of a single dish.
        
        Args:
            tipo_plato: Type of dish (entrante, principal, postre)
            nombre_plato: Name of the dish
            max_retries: Maximum retry attempts for invalid input
            
        Returns:
            Rating (1-5) or None if skipped
        """
        prompt = f"  {tipo_plato.capitalize()}: Califique de {self.config.rating_scale_min} a {self.config.rating_scale_max} (o 's' para omitir): "
        
        for attempt in range(max_retries):
            try:
                print(prompt, end='', flush=True)
                response = input().strip()
                
                # Allow skip
                if response.lower() in ['s', 'skip', 'omit', 'omitir']:
                    return None
                
                # Parse rating
                rating = float(response)
                
                # Validate range
                if self.config.rating_scale_min <= rating <= self.config.rating_scale_max:
                    return rating
                else:
                    print(f"    Error: Calificación debe estar entre {self.config.rating_scale_min} y {self.config.rating_scale_max}")
            
            except ValueError:
                print(f"    Error: Ingrese un número o 's' para omitir")
            except (EOFError, KeyboardInterrupt):
                print("\n    Omitido")
                return None
        
        print(f"    Demasiados intentos. Omitiendo.")
        return None
    
    def _handle_non_interactive(self) -> Tuple[Optional[float], Optional[Dict[str, float]], str]:
        """
        Handle rating collection in non-interactive mode.
        
        Returns:
            Tuple of (default_score, None, timestamp)
        """
        timestamp = datetime.now().isoformat()
        
        if self.config.non_interactive_default is not None:
            score = self.config.non_interactive_default
        elif not self.config.rating_required:
            score = self.config.default_satisfaction_if_skipped
        else:
            # Rating required but can't collect - use neutral
            score = self.config.default_satisfaction_if_skipped
        
        return (score, None, timestamp)
    
    def collect_batch_ratings(self, menus: list, caso_ids: list = None) -> list:
        """
        Collect ratings for multiple menus in batch.
        
        Args:
            menus: List of menu dictionaries
            caso_ids: Optional list of case IDs
            
        Returns:
            List of (aggregate_score, per_menu_scores, timestamp) tuples
        """
        if caso_ids is None:
            caso_ids = [None] * len(menus)
        
        results = []
        for i, (menu, caso_id) in enumerate(zip(menus, caso_ids)):
            print(f"\n--- Menú {i+1}/{len(menus)} ---")
            rating_data = self.collect_menu_rating(menu, caso_id)
            results.append(rating_data)
        
        return results


# Simple test/demo
if __name__ == "__main__":
    print("Testing RatingCollector...")
    
    # Test menu
    test_menu = {
        'entrante': 'Bruschetta De Verano',
        'principal': 'Pasta Al Pomodoro',
        'postre': 'Tiramisu'
    }
    
    collector = RatingCollector()
    
    if collector._is_interactive:
        print("\nInteractive mode detected. Testing rating collection...")
        score, per_menu, timestamp = collector.collect_menu_rating(test_menu, "TEST001")
        print(f"\nResult: score={score}, per_menu={per_menu}, timestamp={timestamp}")
    else:
        print("\nNon-interactive mode detected.")
        score, per_menu, timestamp = collector.collect_menu_rating(test_menu, "TEST001")
        print(f"Default score assigned: {score}")
