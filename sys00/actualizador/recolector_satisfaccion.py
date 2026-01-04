"""
Recolector de Satisfacción del Usuario
======================================

Módulo para recolectar ratings de satisfacción de los usuarios
después de generar menús válidos.

Soporta:
- Modo interactivo (CLI con prompts)
- Modo no-interactivo (fallback seguro)
- Validación de entrada
- Rating individual por menú y agregado por caso
"""

import sys
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field

from .config_retencion import ConfiguracionRetencion, CONFIG_RETENCION_DEFAULT


@dataclass
class RatingMenu:
    """Rating de satisfacción para un menú individual."""
    score: Optional[float] = None  # Puntuación (None si no se proporcionó)
    skipped: bool = False  # Si el usuario saltó el rating
    timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'score': self.score,
            'skipped': self.skipped,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RatingMenu':
        return cls(
            score=data.get('score'),
            skipped=data.get('skipped', False),
            timestamp=data.get('timestamp')
        )


@dataclass 
class SatisfaccionCaso:
    """
    Información de satisfacción completa para un caso.
    
    Almacena tanto ratings individuales de menús como el agregado.
    """
    # Puntuación agregada del caso (media de ratings de menús)
    satisfaction_score: Optional[float] = None
    
    # Ratings individuales por menú (si el caso tiene múltiples menús)
    ratings_por_menu: List[RatingMenu] = field(default_factory=list)
    
    # Metadatos
    rating_scale: Tuple[int, int] = (1, 5)  # (min, max)
    timestamp: Optional[str] = None
    rating_source: str = 'interactive'  # 'interactive', 'default', 'skipped'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización JSON."""
        return {
            'satisfaction_score': self.satisfaction_score,
            'ratings_por_menu': [r.to_dict() for r in self.ratings_por_menu],
            'rating_scale': list(self.rating_scale),
            'timestamp': self.timestamp,
            'rating_source': self.rating_source
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SatisfaccionCaso':
        """Crea desde diccionario (para cargar casos antiguos)."""
        if data is None:
            return cls()
        
        ratings = [RatingMenu.from_dict(r) for r in data.get('ratings_por_menu', [])]
        scale = data.get('rating_scale', [1, 5])
        
        return cls(
            satisfaction_score=data.get('satisfaction_score'),
            ratings_por_menu=ratings,
            rating_scale=tuple(scale) if isinstance(scale, list) else scale,
            timestamp=data.get('timestamp'),
            rating_source=data.get('rating_source', 'unknown')
        )
    
    def has_rating(self) -> bool:
        """Retorna True si hay alguna puntuación válida."""
        return self.satisfaction_score is not None


class RecolectorSatisfaccion:
    """
    Recolecta ratings de satisfacción del usuario.
    
    Soporta modo interactivo y no-interactivo con fallback seguro.
    """
    
    def __init__(self, config: ConfiguracionRetencion = None):
        """
        Inicializa el recolector.
        
        Args:
            config: Configuración de retención (usa defaults si None)
        """
        self.config = config or CONFIG_RETENCION_DEFAULT
    
    def recolectar_rating_menu(self, menu: Dict[str, str], 
                                numero_menu: int = 1,
                                total_menus: int = 1) -> RatingMenu:
        """
        Recolecta rating para un menú individual.
        
        Args:
            menu: Diccionario con 'entrante', 'principal', 'postre'
            numero_menu: Número del menú actual (para display)
            total_menus: Total de menús a evaluar
            
        Returns:
            RatingMenu con el resultado
        """
        if not self.config.is_interactive():
            return self._rating_no_interactivo()
        
        return self._rating_interactivo(menu, numero_menu, total_menus)
    
    def recolectar_satisfaccion_caso(self, menus: List[Dict[str, str]]) -> SatisfaccionCaso:
        """
        Recolecta satisfacción para un caso completo (uno o más menús).
        
        Args:
            menus: Lista de menús a evaluar
            
        Returns:
            SatisfaccionCaso con ratings individuales y agregado
        """
        if not menus:
            return SatisfaccionCaso(
                rating_source='empty',
                timestamp=datetime.now().isoformat()
            )
        
        ratings = []
        scores_validos = []
        
        for i, menu in enumerate(menus, 1):
            rating = self.recolectar_rating_menu(menu, i, len(menus))
            ratings.append(rating)
            
            if rating.score is not None:
                scores_validos.append(rating.score)
        
        # Calcular puntuación agregada
        satisfaction_score = None
        if scores_validos:
            satisfaction_score = sum(scores_validos) / len(scores_validos)
        
        # Determinar fuente del rating
        if all(r.skipped for r in ratings):
            rating_source = 'skipped'
        elif not self.config.is_interactive():
            rating_source = 'default'
        else:
            rating_source = 'interactive'
        
        return SatisfaccionCaso(
            satisfaction_score=satisfaction_score,
            ratings_por_menu=ratings,
            rating_scale=(self.config.rating_scale_min, self.config.rating_scale_max),
            timestamp=datetime.now().isoformat(),
            rating_source=rating_source
        )
    
    def _rating_interactivo(self, menu: Dict[str, str], 
                            numero_menu: int, 
                            total_menus: int) -> RatingMenu:
        """Recolecta rating en modo interactivo CLI."""
        min_val = self.config.rating_scale_min
        max_val = self.config.rating_scale_max
        
        # Mostrar menú de forma compacta
        print(f"\n{'─'*50}")
        if total_menus > 1:
            print(f"📋 MENÚ {numero_menu}/{total_menus}")
        else:
            print(f"📋 MENÚ GENERADO")
        print(f"{'─'*50}")
        print(f"  🥗 Entrante:  {menu.get('entrante', 'N/A')}")
        print(f"  🍽️  Principal: {menu.get('principal', 'N/A')}")
        print(f"  🍰 Postre:    {menu.get('postre', 'N/A')}")
        print(f"{'─'*50}")
        
        # Prompt de rating
        max_intentos = 3
        for intento in range(max_intentos):
            try:
                prompt = f"⭐ Puntúa este menú ({min_val}-{max_val}, 's' para saltar): "
                respuesta = input(prompt).strip().lower()
                
                # Permitir saltar
                if respuesta in ('s', 'skip', 'saltar', ''):
                    print("  ⏭️  Rating saltado")
                    return RatingMenu(
                        score=self.config.default_satisfaction_on_skip,
                        skipped=True,
                        timestamp=datetime.now().isoformat()
                    )
                
                # Validar entrada numérica
                score = float(respuesta)
                if min_val <= score <= max_val:
                    print(f"  ✅ Rating: {score}/{max_val}")
                    return RatingMenu(
                        score=score,
                        skipped=False,
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    print(f"  ⚠️  El valor debe estar entre {min_val} y {max_val}")
                    
            except ValueError:
                print(f"  ⚠️  Por favor ingresa un número entre {min_val} y {max_val}")
            except (EOFError, KeyboardInterrupt):
                print("\n  ⏭️  Entrada cancelada, saltando rating")
                return RatingMenu(
                    score=self.config.default_satisfaction_on_skip,
                    skipped=True,
                    timestamp=datetime.now().isoformat()
                )
        
        # Después de max intentos, usar default
        print(f"  ⏭️  Máximo de intentos alcanzado, usando default")
        return RatingMenu(
            score=self.config.default_satisfaction_on_skip,
            skipped=True,
            timestamp=datetime.now().isoformat()
        )
    
    def _rating_no_interactivo(self) -> RatingMenu:
        """Retorna rating por defecto en modo no-interactivo."""
        return RatingMenu(
            score=self.config.default_satisfaction_on_skip,
            skipped=True,
            timestamp=datetime.now().isoformat()
        )
    
    def debe_guardar_caso(self, satisfaccion: SatisfaccionCaso) -> bool:
        """
        Determina si un caso debe guardarse basado en su satisfacción.
        
        Args:
            satisfaccion: Información de satisfacción del caso
            
        Returns:
            True si el caso debe guardarse según la política configurada
        """
        # Si require_rating_for_retention es False, siempre guardar
        if not self.config.require_rating_for_retention:
            return True
        
        # Si se requiere rating, verificar que haya uno
        return satisfaccion.has_rating()


def formatear_menu_compacto(menu: Dict[str, str]) -> str:
    """
    Formatea un menú de forma compacta para mostrar en logs.
    
    Args:
        menu: Diccionario del menú
        
    Returns:
        String formateado
    """
    entrante = menu.get('entrante', 'N/A')[:30]
    principal = menu.get('principal', 'N/A')[:30]
    postre = menu.get('postre', 'N/A')[:30]
    
    return f"[{entrante} | {principal} | {postre}]"
