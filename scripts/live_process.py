"""Live demo script for showing the CFG evolution process on stage."""

import time
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.proposer import propose
from grammar.mutations import apply_patch
from loop.evaluate import evaluate
from env.scenes import make_batch
from artifacts.io import append_csv, save_text
# Import load_config from main
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import load_config


def live_process(grammar_text: str, rounds: int = 3, batch_size: int = 50, verbose: bool = True):
    """
    Run a short, verbose evolutionary process for live demo.

    Args:
        grammar_text: Starting grammar text
        rounds: Number of rounds to run
        batch_size: Number of scenes per evaluation
        verbose: Whether to print detailed progress
    """
    # Load config for scene generation
    config = load_config()

    # Setup logging
    log_header = ["round", "accuracy", "avg_len", "productions", "collisions", "parse_fail", "note"]
    run_dir = f"artifacts/runs/live_{int(time.time())}"

    if verbose:
        print(f"🎭 LIVE DEMO: CFG Evolution Process")
        print(f"📊 Starting with {len(grammar_text.split())} lines")
        print(f"🔄 Running {rounds} rounds with batch size {batch_size}")
        print(f"📁 Logging to {run_dir}")
        print("=" * 60)

    for r in range(rounds):
        if verbose:
            print(f"\n🔄 ROUND {r+1}/{rounds}")
            print("-" * 40)

        # Generate scenes for this round
        scenes = make_batch(
            colors=config["attributes"]["color"],
            shapes=config["attributes"]["shape"],
            sizes=config["attributes"]["size"],
            batch_size=batch_size,
            k=config["k_objects"]
        )

        # Evaluate current grammar
        if verbose:
            print("📊 Evaluating current grammar...")

        metrics, examples = evaluate(grammar_text, scenes, return_examples=True)

        # Log results
        append_csv(f"{run_dir}/round_log.csv", {
            "round": r,
            "accuracy": metrics["accuracy"],
            "avg_len": metrics["avg_msg_chars"],
            "productions": metrics["grammar_complexity"]["productions"],
            "collisions": metrics["collisions"],
            "parse_fail": metrics["parse_fail_rate"],
            "note": "live"
        }, header=log_header)

        if verbose:
            print(f"📈 Results:")
            print(f"  Accuracy: {metrics['accuracy']:.3f} ({metrics['n_correct']}/{metrics['n_scenes']})")
            print(f"  Avg Message Length: {metrics['avg_msg_chars']:.1f} chars")
            print(f"  Collision Rate: {metrics['collisions']:.3f}")
            print(f"  Parse Fail Rate: {metrics['parse_fail_rate']:.3f}")
            print(f"  Grammar Complexity: {metrics['grammar_complexity']['productions']} productions")

        # Ask proposer for mutations
        if verbose:
            print(f"\n🤖 Asking proposer for mutations...")

        try:
            # Extract messages and predictions from examples for proposer
            messages = [ex["message"] for ex in examples]
            predictions = [ex["prediction"] for ex in examples]

            patch = propose(grammar_text, metrics, examples[:5])

            if verbose:
                print(f"✅ Proposer returned {len(patch.get('mutations', []))} mutations")
                for i, mut in enumerate(patch.get('mutations', [])):
                    print(f"  {i+1}. {mut['op']}: {mut}")

            # Apply patch
            grammar_candidate = apply_patch(grammar_text, patch)

            # Quick guard test
            if verbose:
                print("🧪 Quick validation test...")

            smoke_metrics, _ = evaluate(grammar_candidate, scenes[:20], return_examples=False)

            # Check if patch is acceptable
            if smoke_metrics["parse_fail_rate"] <= 0.05 and smoke_metrics["accuracy"] >= 0.90:
                grammar_text = grammar_candidate
                save_text(f"{run_dir}/grammars/round_{r:03d}.lark", grammar_text)

                if verbose:
                    print("✅ Patch accepted! Grammar updated.")
                    print(f"   New size: {len(grammar_text.split())} lines")
            else:
                if verbose:
                    print("⛔ Rejecting patch (guard failed)")
                    print(f"   Parse fail: {smoke_metrics['parse_fail_rate']:.3f}")
                    print(f"   Accuracy: {smoke_metrics['accuracy']:.3f}")

        except Exception as e:
            if verbose:
                print(f"❌ Proposer failed: {e}")
            continue

        # Small delay to keep logs readable
        time.sleep(0.2)

    if verbose:
        print(f"\n🏁 Live demo completed!")
        print(f"📁 Results saved to {run_dir}")

    return grammar_text


if __name__ == "__main__":
    # Load base grammar and run live process
    from grammar.utils import load_base_grammar

    grammar = load_base_grammar()
    live_process(grammar, rounds=3, batch_size=50)
