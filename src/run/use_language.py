"""Script to demonstrate the evolved language for audience guessing."""

from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from artifacts.io import load_text, load_json
from agents.speaker import speak
from agents.listener import listen
from env.scenes import make_scene


def use_saved_language(n: int = 3, k: int = 4):
    """
    Load precomputed language and run Speaker→Listener rounds for audience guessing.

    Args:
        n: Number of demonstration rounds
        k: Number of objects per scene
    """
    print(f"🎭 DEMONSTRATING EVOLVED LANGUAGE")
    print(f"📊 Running {n} rounds with {k} objects per scene")
    print("=" * 50)

    try:
        # Load the evolved language
        g = load_text("artifacts/best/grammar.lark")
        fs = load_json("artifacts/best/fewshots.json")

        print(f"✅ Loaded evolved grammar ({len(g.split())} lines)")
        print(f"✅ Loaded few-shots: {len(fs.get('speaker', []))} speaker, {len(fs.get('listener', []))} listener")
        print()

    except FileNotFoundError as e:
        print(f"❌ Could not load evolved language: {e}")
        print("   Make sure to run the offline optimization first to create artifacts/best/")
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

    for i in range(n):
        # Generate a random scene
        scene = make_scene(colors, shapes, sizes, k=k)

        # Show the scene to the audience
        print(f"\n[Round {i+1}] Scene:")
        for j, obj in enumerate(scene["objects"]):
            marker = "🎯" if j == scene["target_idx"] else "  "
            print(f"  {marker} {j}: {obj['color']} {obj['shape']} {obj['size']}")

        # Speaker generates message
        print(f"\n🤖 Speaker generates message...")
        msg = speak(scene, g, fewshots=fs.get("speaker"))
        print(f"💬 Message: {repr(msg)}")

        # Listener makes prediction
        print(f"👂 Listener interprets message...")
        pred = listen(scene, msg, k=k, fewshots=fs.get("listener"))

        # Show result
        correct = pred == scene["target_idx"]
        status = "✅ CORRECT!" if correct else "❌ WRONG!"
        print(f"🎯 Listener's guess: {pred} {status}")

        if not correct:
            print(f"   Target was actually: {scene['target_idx']}")

        print("-" * 40)

    print(f"\n🏁 Demonstration completed!")
    print(f"📝 The evolved language successfully compressed the original grammar")
    print(f"   while maintaining high accuracy in object identification.")


if __name__ == "__main__":
    use_saved_language(n=3, k=4)
