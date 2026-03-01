# ============================================================
# 📊 ANALYTICS CONFIGURATION - Centralized, Versioned
# ============================================================

"""
Configuration module for analytics scoring and rolling window aggregation.

This module provides:
1. Composite weight configuration (configurable, not hardcoded)
2. Threshold and window parameters
3. Rolling window analyzer functions
4. Weighted aggregation functions
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# ============================================================
# 🎯 COMPOSITE SCORE WEIGHTS (Configurable)
# ============================================================

COMPOSITE_CONFIG = {
    "accuracy": 0.45,      # Primary metric (up from 0.40)
    "timing": 0.35,        # Rhythm control (down from 0.40)
    "technique": 0.20,     # Technical proficiency (stable at 0.20)
}

# Validate: Weights must sum to 1.0
_weight_sum = sum(COMPOSITE_CONFIG.values())
assert abs(_weight_sum - 1.0) < 1e-6, f"Weights must sum to 1.0, got {_weight_sum}"

logger.info(f"✅ Composite config loaded: {COMPOSITE_CONFIG}")

# ============================================================
# 📏 ANALYTICS WINDOW & THRESHOLD PARAMETERS
# ============================================================

MAX_ANALYTICS_WINDOW = 30          # Rolling window size
UNLOCK_THRESHOLD = 0.75            # Composite score threshold
REQUIRED_STREAK = 3                # Consecutive successes to unlock

# ============================================================
# 🔄 ROLLING WINDOW ANALYZER
# ============================================================

class RollingWindowAnalytics:
    """
    Implements rolling window aggregation for analytics snapshots.
    
    Features:
    - Bounded memory (keeps only last N)
    - Weighted recency (recent scores weighted more)
    - Multiple aggregation measures (mean, weighted, trend)
    """
    
    def __init__(self, max_window: int = MAX_ANALYTICS_WINDOW):
        """
        Args:
            max_window: Maximum snapshots to keep in memory
        """
        self.max_window = max_window
    
    @staticmethod
    def weighted_average(scores: List[float]) -> float:
        """
        Compute weighted average favoring recent scores.
        
        Linear weights: [1, 2, 3, ..., n]
        Example: [70, 75, 80] → (70*1 + 75*2 + 80*3) / 6 ≈ 77.5
        
        Args:
            scores: List of scores in chronological order
        
        Returns:
            Weighted average (0-100)
        """
        if not scores:
            return 0.0
        
        if len(scores) == 1:
            return scores[0]
        
        weights = list(range(1, len(scores) + 1))
        total_weight = sum(weights)
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        
        return weighted_sum / total_weight
    
    @staticmethod
    def exponential_weighted_avg(scores: List[float], alpha: float = 0.3) -> float:
        """
        Exponential weighted average (alternative, more aggressive recency bias).
        
        Args:
            scores: List of scores in chronological order
            alpha: Smoothing factor (0-1), higher = more recent weight
        
        Returns:
            Exponentially weighted average
        """
        if not scores:
            return 0.0
        
        ewa = scores[0]
        for score in scores[1:]:
            ewa = alpha * score + (1 - alpha) * ewa
        
        return ewa
    
    @staticmethod
    def trend_slope(scores: List[float]) -> float:
        """
        Calculate linear trend slope (improvement rate).
        
        Positive = improving, Negative = declining, ~0 = plateau
        
        Args:
            scores: List of scores in chronological order
        
        Returns:
            Slope of best-fit line
        """
        if len(scores) < 2:
            return 0.0
        
        n = len(scores)
        x = list(range(n))
        
        # Simple linear regression
        x_mean = sum(x) / n
        y_mean = sum(scores) / n
        
        numerator = sum((x[i] - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    @staticmethod
    def consistency_index(scores: List[float], max_deviation: float = 20.0) -> float:
        """
        Calculate consistency as 1 - (std_dev / max_deviation).
        
        Higher consistency = more stable performance.
        
        Args:
            scores: List of scores
            max_deviation: Standard deviation cap for normalization
        
        Returns:
            Consistency index (0-1)
        """
        if len(scores) < 2:
            return 1.0
        
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        
        consistency = max(0.0, 1.0 - (std_dev / max_deviation))
        return min(1.0, consistency)  # Clamp to [0, 1]


# ============================================================
# 🎵 COMPOSITE SCORE CALCULATOR
# ============================================================

def compute_composite_score(
    accuracy_score: float,
    timing_score: float,
    technique_score: float,
    config: Dict[str, float] = None
) -> float:
    """
    ✅ Configurable Composite Score Calculation
    
    Combines three skill dimensions using configurable weights.
    
    Args:
        accuracy_score: Note accuracy (0-100) → normalized to [0,1]
        timing_score: Timing precision (0-100) → normalized to [0,1]
        technique_score: Technique proficiency (0-1)
        config: Optional config override (default: COMPOSITE_CONFIG)
    
    Returns:
        Composite score (0-1)
    
    Example:
        >>> compute_composite_score(accuracy=85, timing=80, technique=0.75)
        0.783
    """
    if config is None:
        config = COMPOSITE_CONFIG
    
    # Normalize scores to [0, 1]
    acc_norm = min(accuracy_score / 100.0, 1.0)
    timing_norm = min(timing_score / 100.0, 1.0)
    tech_norm = min(technique_score, 1.0)
    
    composite = (
        acc_norm * config["accuracy"]
        + timing_norm * config["timing"]
        + tech_norm * config["technique"]
    )
    
    return round(min(composite, 1.0), 3)


def get_composite_config() -> Dict[str, float]:
    """Get current composite configuration."""
    return COMPOSITE_CONFIG.copy()


def validate_composite_config(config: Dict[str, float]) -> bool:
    """
    Validate that a composite config has all required keys and sums to 1.0.
    
    Returns:
        True if valid, False otherwise
    """
    required_keys = {"accuracy", "timing", "technique"}
    
    if set(config.keys()) != required_keys:
        logger.error(f"Missing keys. Required: {required_keys}, got: {set(config.keys())}")
        return False
    
    weight_sum = sum(config.values())
    if abs(weight_sum - 1.0) > 1e-6:
        logger.error(f"Weights must sum to 1.0, got {weight_sum}")
        return False
    
    return True


# ============================================================
# 📊 ANALYTICS SNAPSHOT STRUCTURE
# ============================================================

def build_analytics_snapshot(
    user_id: str,
    skill_id: str,
    session_id: int,
    accuracy: float,
    timing: float,
    technique: float,
    config: Dict[str, float] = None
) -> Dict:
    """
    Build a structured analytics snapshot for a practice session.
    
    Args:
        user_id: User identifier
        skill_id: Skill identifier
        session_id: Session ID in database
        accuracy: Accuracy score (0-100)
        timing: Timing score (0-100)
        technique: Technique score (0-1)
        config: Optional config override
    
    Returns:
        Snapshot dict with computed metrics
    """
    composite = compute_composite_score(accuracy, timing, technique, config)
    
    return {
        "user_id": user_id,
        "skill_id": skill_id,
        "session_id": session_id,
        "accuracy_score": round(accuracy, 2),
        "timing_score": round(timing, 2),
        "technique_score": round(technique, 3),
        "composite_score": composite,
    }


# ============================================================
# 🔬 ANALYTICS INSIGHT BUILDER
# ============================================================

def analyze_performance_trend(
    scores: List[float],
    window_size: int = 5
) -> Dict:
    """
    Analyze performance trend from recent scores.
    
    Args:
        scores: List of composite scores (chronological: oldest → newest)
        window_size: Window for recent trend calculation
    
    Returns:
        {
            "recent_window": [scores],
            "recent_avg": float,
            "overall_trend": str,
            "slope": float,
            "consistency": float,
            "recommendation": str
        }
    """
    if not scores:
        return {
            "recent_window": [],
            "recent_avg": 0.0,
            "overall_trend": "NO_DATA",
            "slope": 0.0,
            "consistency": 0.0,
            "recommendation": "Start practicing to build baseline"
        }
    
    analyzer = RollingWindowAnalytics()
    
    # Get recent window
    recent = scores[-window_size:] if len(scores) >= window_size else scores
    recent_avg = analyzer.weighted_average(recent)
    
    # Calculate trend
    slope = analyzer.trend_slope(scores)
    consistency = analyzer.consistency_index(scores)
    
    # Classify trend
    if slope > 0.5:
        trend = "STRONG_IMPROVEMENT"
        recommendation = "Keep up the momentum! Maintain current practice intensity."
    elif slope > 0.1:
        trend = "GRADUAL_IMPROVEMENT"
        recommendation = "Making progress. Focus on consistency."
    elif slope < -0.5:
        trend = "DECLINING"
        recommendation = "Performance declining. Review technique and increase practice frequency."
    elif abs(slope) < 0.1:
        trend = "PLATEAU"
        recommendation = "Plateau detected. Try new practice methods or increase difficulty."
    else:
        trend = "STABLE"
        recommendation = "Performance stable. Work on deep areas of weakness."
    
    return {
        "recent_window": [round(s, 3) for s in recent],
        "recent_avg": round(recent_avg, 3),
        "overall_trend": trend,
        "slope": round(slope, 3),
        "consistency": round(consistency, 3),
        "recommendation": recommendation,
        "total_sessions": len(scores)
    }
