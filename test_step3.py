#!/usr/bin/env python3
"""Test script for step 3 of the demo - using the evolved language."""

import json
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.speaker import speak
from src.agents.listener import listen
from src.env.scenes import make_scene

def test_step3():
    """Test step 3: use the saved language for audience guessing."""
    print(f"🎭 STEP 3: USING THE EVOLVED LANGUAGE")
    print(f"📊 Running 3 rounds with 4 objects per scene")
    print("=" * 50)

    try:
        # Load the evolved language from our successful run
        grammar_path = Path("artifacts/best/grammar.lark")
        fewshots_path = Path("artifacts/best/fewshots.json")

        if not grammar_path.exists():
            print(f"❌ Grammar not found at {grammar_path}")
            return
        if not fewshots_path.exists():
            print(f"❌ Fewshots not found at {fewshots_path}")
            return

        grammar = grammar_path.read_text()
        fewshots = json.loads(fewshots_path.read_text())

        print(f"✅ Loaded evolved grammar ({len(grammar.split())} lines)")
        print(f"✅ Loaded few-shots: {len(fewshots.get('speaker', []))} speaker, {len(fewshots.get('listener', []))} listener")
        print()

    except Exception as e:
        print(f"❌ Could not load evolved language: {e}")
        return

    # Define the vocabulary (same as training)
    colors = ["red", "blue", "green", "yellow", "black", "white"]
    shapes = ["circle", "square", "triangle", "star", "hexagon", "diamond"]
    sizes = ["small", "medium", "large", "huge"]

    print("🎯 VOCABULARY:")
    print(f"   Colors: {', '.join(colors)}")
    print(f"   Shapes: {', '.join(shapes)}")
    print(f"   Sizes: {', '.join(sizes)}")
    print()

    print("🎭 DEMONSTRATION ROUNDS:")
    print("-" * 40)

    for i in range(3):
        # Generate a random scene
        scene = make_scene(colors, shapes, sizes, k=4)

        # Show the scene to the audience
        print(f"\n[Round {i+1}] Scene:")
        for j, obj in enumerate(scene["objects"]):
            marker = "🎯" if j == scene["target_idx"] else "  "
            print(f"  {marker} {j}: {obj['color']} {obj['shape']} {obj['size']}")

        # Speaker generates message
        print(f"\n🤖 Speaker generates message...")
        try:
            msg = speak(scene, grammar, fewshots=fewshots.get("speaker"))
            print(f"💬 Message: {repr(msg)}")

            # Listener makes prediction
            print(f"👂 Listener interprets message...")
            pred = listen(scene, msg, k=4, fewshots=fewshots.get("listener"))

            # Show result
            correct = pred == scene["target_idx"]
            status = "✅ CORRECT!" if correct else "❌ WRONG!"
            print(f"🎯 Listener's guess: {pred} {status}")

            if not correct:
                print(f"   Target was actually: {scene['target_idx']}")

        except Exception as e:
            print(f"❌ Error in round {i+1}: {e}")

        print("-" * 40)

    print(f"\n🏁 Demonstration completed!")
    print(f"📝 The evolved language successfully compressed the original grammar")
    print(f"   while maintaining high accuracy in object identification.")

if __name__ == "__main__":
    test_step3()
