import os
from typing import List
from ..types import Scene
from .openai_client import OpenAIClient

def load_prompt() -> str:
    """Load listener prompt from file."""
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "listener.txt")
    with open(prompt_path, "r") as f:
        return f.read().strip()

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
    prompt = load_prompt()
    scene_text = format_scene_for_listener(scene, message)

    messages = [
        {
            "role": "system",
            "content": f"{prompt}\n\nThe message follows this grammar:\n{grammar}"
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
