import os
from typing import List
from ..types import Scene, SceneObj
from .openai_client import OpenAIClient

def load_prompt() -> str:
    """Load speaker prompt from file."""
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "speaker.txt")
    with open(prompt_path, "r") as f:
        return f.read().strip()

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
    prompt = load_prompt()
    scene_text = format_scene(scene)

    messages = [
        {
            "role": "system",
            "content": prompt
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
