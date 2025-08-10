"""Offline optimization script to generate best artifacts for demo."""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import main as run_evolution
from src.artifacts.save_best import save_best
from src.artifacts.io import load_text, load_json
from src.env.scenes import make_batch
from src.loop.evaluate import evaluate
from src.agents.speaker import speak
from src.agents.listener import listen


def collect_fewshots(grammar_text: str, n_examples: int = 3):
    """Collect few-shot examples from the evolved grammar."""
    print(f"📚 Collecting {n_examples} few-shot examples...")

    # Generate some scenes
    colors = ["red", "blue", "green", "yellow", "black", "white"]
    shapes = ["circle", "square", "triangle", "star", "hexagon", "diamond"]
    sizes = ["small", "medium", "large", "huge"]

    scenes = make_batch(colors, shapes, sizes, batch_size=n_examples, k=4)

    speaker_fs = []
    listener_fs = []

    for scene in scenes:
        try:
            # Generate message
            msg = speak(scene, grammar_text, fewshots=None, temperature=0.4)

            # Get prediction
            pred = listen(scene, msg, k=4, fewshots=None, temperature=0.2)

            # Store speaker example
            speaker_fs.append({
                "scene": scene,
                "message": msg
            })

            # Store listener example
            listener_fs.append({
                "message": msg,
                "answer": pred
            })

            print(f"  ✅ Scene {len(speaker_fs)}: {msg} → {pred}")

        except Exception as e:
            print(f"  ❌ Failed to collect example: {e}")
            continue

    return speaker_fs, listener_fs


def offline_optimize():
    """Run offline optimization and save best artifacts."""
    print("🔬 QUICK OFFLINE OPTIMIZATION (2-3 min)")
    print("=" * 50)
    print("This will run a quick optimization (3 rounds) to find a decent grammar.")
    print("The results will be saved for the live demo.")
    print()

    # Check if we already have best artifacts
    if Path("artifacts/best/grammar.lark").exists():
        print("⚠️  Best artifacts already exist!")
        print("   Delete artifacts/best/ to regenerate.")
        return

    # Run the main evolution (this will use argparse defaults)
    print("🚀 Starting evolution...")
    print("   (This may take a while - the system will evolve the grammar)")
    print()

    # We need to mock argparse for the main function
    import argparse

    # Create a mock args object with good defaults for offline optimization
    class MockArgs:
        def __init__(self):
            self.config = "configs/defaults.yaml"
            self.batch_size = 50  # Smaller batch for faster processing
            self.rounds = 3  # Just 3 rounds for quick demo
            self.verbose = True
            self.artifacts_dir = "artifacts"

    # Temporarily replace sys.argv to avoid argparse issues
    original_argv = sys.argv
    sys.argv = ["offline_optimize.py", "--rounds", "2", "--batch-size", "2", "--verbose"]

    try:
        # Run the evolution
        run_evolution()

        # Load the final grammar from the run directory
        # Find the most recent run directory
        run_dirs = list(Path("artifacts").glob("run_*"))
        if not run_dirs:
            print("❌ No run directories found!")
            return

        latest_run = max(run_dirs, key=lambda p: p.stat().st_mtime)
        final_grammar_path = latest_run / "final_grammar.lark"

        if not final_grammar_path.exists():
            print(f"❌ Evolution didn't produce a final grammar in {latest_run}!")
            return

        grammar_text = final_grammar_path.read_text()
        print(f"\n✅ Evolution completed! Final grammar: {len(grammar_text.split())} lines")

        # Collect few-shot examples
        speaker_fs, listener_fs = collect_fewshots(grammar_text, n_examples=3)

        # Save best artifacts
        save_best(grammar_text, speaker_fs, listener_fs)

        print(f"\n🎉 Offline optimization complete!")
        print(f"   Best artifacts saved to artifacts/best/")
        print(f"   Ready for live demo!")

    finally:
        # Restore original argv
        sys.argv = original_argv


if __name__ == "__main__":
    offline_optimize()
