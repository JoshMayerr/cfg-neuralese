"""
Example usage of the evolved language with few-shots.
This shows how to use the final grammar and few-shots after evolution.
"""

from src.grammar.utils import load_grammar, load_fewshots
from src.agents.speaker import speak
from src.agents.listener import listen

# Load the evolved language
g = load_grammar("src/grammar/final_grammar.lark")
fs = load_fewshots("fewshots/final_fewshots.json")

# Example scene
scene = {
    "objects": [
        {"color": "red", "shape": "circle", "size": "small"},
        {"color": "blue", "shape": "square", "size": "medium"},
        {"color": "red", "shape": "triangle", "size": "large"},
        {"color": "green", "shape": "circle", "size": "small"}
    ],
    "target_idx": 2  # The red triangle
}

# Speaker generates message using evolved language + few-shots
msg = speak(scene, g, fewshots=fs.get("speaker"))
print(f"Speaker message: {msg}")

# Listener interprets message using evolved language + few-shots
pred = listen(scene, msg, k=len(scene["objects"]), fewshots=fs.get("listener"))
print(f"Listener prediction: {pred}")
print(f"Correct answer: {scene['target_idx']}")
print(f"Success: {pred == scene['target_idx']}")
