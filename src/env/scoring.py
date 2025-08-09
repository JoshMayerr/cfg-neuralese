from typing import List, Dict, Any, Optional

def avg_len(messages: List[str]) -> float:
    """Calculate average message length in characters."""
    if not messages:
        return 0.0
    return sum(len(m) for m in messages) / len(messages)

def count_collisions(messages: List[str]) -> int:
    """Count how many messages are duplicated."""
    if not messages:
        return 0
    unique_messages = set(messages)
    return len(messages) - len(unique_messages)

def score_fn(acc: float, avg_chars: float, complexity: Dict[str, float],
             collisions: float, robust: Optional[float] = None,
             lambdas: Optional[Dict[str, float]] = None) -> float:
    """Calculate composite score for a grammar."""
    l = lambdas or {}

    score = acc
    score -= l.get("len_per_char", 0.02) * avg_chars
    score -= l.get("complexity_per_prod", 0.5) * complexity.get("productions", 0)
    score -= l.get("complexity_per_rhs_symbol", 0.1) * complexity.get("avg_rhs_symbols", 0)
    score -= l.get("collisions", 5.0) * collisions

    if robust is not None:
        score += l.get("robust_factor", 0.5) * (robust - acc)

    return score
