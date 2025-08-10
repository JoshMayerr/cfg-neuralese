from typing import Dict, List, Tuple
from ..types import Scene, Metrics
from ..env.scoring import avg_len, count_collisions
from ..agents.speaker import get_speaker_message
from ..agents.listener import get_listener_prediction

def calculate_grammar_complexity(grammar: str) -> Dict[str, float]:
    """Calculate basic grammar complexity metrics."""
    lines = grammar.strip().split('\n')
    productions = len([line for line in lines if ':' in line])

    # Simple approximation of average RHS symbols
    rhs_symbols = 0
    rhs_count = 0
    for line in lines:
        if ':' in line:
            rhs = line.split(':')[1].strip()
            # Count non-whitespace tokens as rough symbol count
            symbols = len(rhs.split())
            rhs_symbols += symbols
            rhs_count += 1

    avg_rhs_symbols = rhs_symbols / max(1, rhs_count)

    return {
        "productions": productions,
        "avg_rhs_symbols": avg_rhs_symbols
    }

def evaluate(grammar: str, scenes: List[Scene], return_examples: bool = False) -> Metrics:
    """
    Evaluate grammar performance on a batch of scenes.

    Args:
        grammar: Lark grammar text
        scenes: List of scenes to evaluate on
        return_examples: Whether to include examples in the return value

    Returns:
        Dictionary of metrics including accuracy, length, complexity, etc.
        If return_examples=True, also includes 'examples' key with sample data
    """
    messages = []
    predictions = []
    correct = 0
    parse_failures = 0

    examples = []

    for scene in scenes:
        try:
            # Get speaker message
            message = get_speaker_message(grammar, scene)
            messages.append(message)

            # Get listener prediction
            pred_idx = get_listener_prediction(grammar, scene, message)
            predictions.append(pred_idx)

            # Check if correct
            is_correct = pred_idx == scene["target_idx"]
            if is_correct:
                correct += 1

            # Store example for later analysis
            examples.append({
                "scene": scene,
                "message": message,
                "prediction": pred_idx,
                "correct": is_correct
            })

        except Exception as e:
            # Count as parse failure
            parse_failures += 1
            messages.append("")
            predictions.append(0)

            examples.append({
                "scene": scene,
                "message": "",
                "prediction": 0,
                "correct": False,
                "error": str(e)
            })

    # Calculate metrics
    n_scenes = len(scenes)
    accuracy = correct / max(1, n_scenes)
    avg_msg_chars = avg_len(messages)
    collisions = count_collisions(messages)
    collision_rate = collisions / max(1, n_scenes)
    parse_fail_rate = parse_failures / max(1, n_scenes)
    grammar_complexity = calculate_grammar_complexity(grammar)

    result = {
        "accuracy": accuracy,
        "avg_msg_chars": avg_msg_chars,
        "collisions": collision_rate,
        "parse_fail_rate": parse_fail_rate,
        "grammar_complexity": grammar_complexity,
        "n_scenes": n_scenes,
        "n_correct": correct,
        "n_parse_failures": parse_failures
    }

    if return_examples:
        result["examples"] = examples[:5]  # Keep first 5 examples for analysis

    return result
