"""
Proposer agent for evolving CFG communication protocols.

The Proposer analyzes current grammar performance and proposes mutations
to reduce message length while maintaining high accuracy.
"""

import json
from typing import Any, Dict, List
from src.types import Scene
from .openai_client import OpenAIClient

ALLOWED_OPS = {"rename", "remove_separators", "restrict_length", "replace_rule"}


def propose(
    grammar_text: str,
    metrics: Dict[str, Any],
    scenes: List[Scene],
    messages: List[str],
    predictions: List[int]
) -> Dict[str, Any]:
    """
    Ask GPT-5 to propose a grammar patch.
    Uses freeform tool calling to return JSON text, then parses + validates it.
    """
    client = OpenAIClient()

    sys_prompt = (
        "You are the PROPOSER.\n"
        "You will receive the current grammar, evaluation metrics, and a few examples.\n"
        "Your task: suggest a JSON patch with grammar mutations.\n\n"
        "Allowed operations:\n"
        f"{', '.join(sorted(ALLOWED_OPS))}\n"
        "Output ONLY valid JSON in this format:\n"
        '{ "mutations": [ { "op": "...", ... } ], "speaker_fewshot": [], "listener_fewshot": [] }\n'
        "Do not add any text before or after the JSON."
    )

    # Format examples
    example_strs = []
    for i, (scene, message, pred) in enumerate(zip(scenes, messages, predictions)):
        target_idx = scene["target_idx"]
        correct = pred == target_idx
        target = scene["objects"][target_idx]

        example_strs.append(
            f"Scene {i}: {target['color']} {target['shape']} {target['size']}\n"
            f"Message: {message}\n"
            f"Prediction: {pred}, Correct: {target_idx}, Success: {correct}"
        )

    # Format user content
    user_content = (
        f"=== Current Grammar ===\n{grammar_text}\n\n"
        f"=== Metrics ===\n{json.dumps(metrics, indent=2)}\n\n"
        f"=== Examples ===\n" + "\n---\n".join(example_strs)
    )

    # Call model with freeform tool
    try:
        raw_text = client.emit_freeform(
            [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_content}
            ],
            tool_name="propose_patch"
        )

        patch = _safe_parse_json(raw_text)
        _validate_patch(patch)
        return patch

    except Exception as e:
        print(f"Proposer failed: {e}")
        return _fallback_patch()


def _safe_parse_json(text: str) -> Dict[str, Any]:
    """Safely parse JSON text, with helpful error messages."""
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from proposer: {e}\nRaw text:\n{text}")


def _validate_patch(patch: Dict[str, Any]) -> None:
    """Validate the patch structure and operations."""
    if "mutations" not in patch or not isinstance(patch["mutations"], list):
        raise RuntimeError("Patch missing 'mutations' list.")

    for m in patch["mutations"]:
        if m.get("op") not in ALLOWED_OPS:
            raise RuntimeError(f"Invalid op: {m.get('op')}")

    # Few-shot arrays optional, but should exist
    patch.setdefault("speaker_fewshot", [])
    patch.setdefault("listener_fewshot", [])


def _fallback_patch() -> Dict[str, Any]:
    """Return a simple fallback patch if the proposer fails."""
    return {
        "mutations": [
            {"op": "rename", "from": "color", "to": "c"},
            {"op": "rename", "from": "shape", "to": "s"},
            {"op": "rename", "from": "size", "to": "z"}
        ],
        "speaker_fewshot": [],
        "listener_fewshot": []
    }


# Legacy function for backward compatibility
def get_proposer_suggestion(
    current_grammar: str,
    current_metrics: Dict[str, Any],
    scenes: List[Scene],
    messages: List[str],
    predictions: List[int]
) -> Dict[str, Any]:
    """
    Legacy wrapper for the new propose function.
    """
    return propose(current_grammar, current_metrics, scenes, messages, predictions)


if __name__ == "__main__":
    # Test the proposer with mock data
    test_grammar = """start: msg
msg: phrase (";" phrase)*
phrase: slot ":" value
slot: "color" | "shape" | "size"
value: /[a-z]+/"""

    test_metrics = {
        "accuracy": 1.0,
        "avg_msg_chars": 11.0,
        "parse_fail_rate": 0.0,
        "collision_rate": 0.0
    }

    test_scenes = [
        {
            "target_idx": 0,
            "objects": [
                {"color": "red", "shape": "circle", "size": "small"},
                {"color": "blue", "shape": "square", "size": "large"}
            ]
        }
    ]

    test_messages = ["color:red;shape:circle;size:small"]
    test_predictions = [0]

    patch = propose(
        test_grammar, test_metrics, test_scenes, test_messages, test_predictions
    )

    print("Proposer Test Output:")
    print(f"Mutations: {patch['mutations']}")
    print(f"Speaker Few-shot: {patch['speaker_fewshot']}")
    print(f"Listener Few-shot: {patch['listener_fewshot']}")
