from typing import List
from ..types import Scene, SceneObj
from .openai_client import OpenAIClient

# Inline prompt - no external file dependency
SPEAKER_PROMPT = """You are the SPEAKER. Given a target object and distractors, emit the SHORTEST legal message under the attached grammar that lets a competent LISTENER uniquely identify the target. Output only the string that matches the grammar's start rule."""

def format_scene(scene: Scene) -> str:
    """Format scene for speaker prompt."""
    target = scene["objects"][scene["target_idx"]]
    distractors = [obj for i, obj in enumerate(scene["objects"]) if i != scene["target_idx"]]

    lines = [f"Target object (index {scene['target_idx']}):"]
    lines.append(f"  Color: {target['color']}, Shape: {target['shape']}, Size: {target['size']}")

    if distractors:
        lines.append("\nDistractor objects:")
        for i, obj in enumerate(distractors):
            lines.append(f"  Index {i}: Color: {obj['color']}, Shape: {obj['shape']}, Size: {obj['size']}")

    return "\n".join(lines)

def get_speaker_message(grammar: str, scene: Scene) -> str:
    """
    Get message from speaker for given scene using grammar constraints.

    Args:
        grammar: Lark grammar text
        scene: Scene with target and distractors

    Returns:
        Message string that should match the grammar's start rule
    """
    scene_text = format_scene(scene)

    messages = [
        {
            "role": "system",
            "content": SPEAKER_PROMPT
        },
        {
            "role": "user",
            "content": f"{scene_text}\n\nRemember: Use the SHORTEST possible message that uniquely identifies the target."
        }
    ]

    # Use new OpenAIClient with grammar constraints
    client = OpenAIClient()
    return client.emit_with_grammar(
        messages=messages,
        grammar_text=grammar,
        tool_name="emit_message",
        syntax="lark"
    )
