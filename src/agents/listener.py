from typing import List
from ..types import Scene
from .openai_client import OpenAIClient

# Inline prompt - no external file dependency
LISTENER_PROMPT = """You are the LISTENER. Given a legal message (per the attached grammar) and the list of objects, determine which object the SPEAKER intended. Output only the zero-based index of the target."""

def format_scene_for_listener(scene: Scene, message: str) -> str:
    """Format scene and message for listener prompt."""
    lines = [f"Scene with {len(scene['objects'])} objects:"]

    # Add all objects with their indices
    for i, obj in enumerate(scene['objects']):
        lines.append(f"  Index {i}: Color: {obj['color']}, Shape: {obj['shape']}, Size: {obj['size']}")

    lines.append(f"\nSpeaker message: {message}")
    lines.append("\nWhich object is the speaker referring to? Respond with just the index number.")

    return "\n".join(lines)

def get_listener_prediction(grammar: str, scene: Scene, message: str) -> int:
    """
    Get listener's prediction for which object the message refers to.

    Args:
        grammar: Lark grammar text (for understanding/context)
        scene: Scene with objects
        message: Message from speaker

    Returns:
        Predicted index of target object
    """
    scene_text = format_scene_for_listener(scene, message)

    messages = [
        {
            "role": "system",
            "content": f"{LISTENER_PROMPT}\n\nThe message follows this grammar:\n{grammar}"
        },
        {
            "role": "user",
            "content": scene_text
        }
    ]

    # Use new OpenAIClient with index constraints
    client = OpenAIClient()
    k = len(scene['objects'])  # Total number of objects
    return client.emit_index(messages, k)
