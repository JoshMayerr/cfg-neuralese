#!/usr/bin/env python3
"""
CFG-Neuralese: Main CLI for running evaluations.

Phase 2: Evolutionary loop with proposer integration.
"""

import argparse
import json
import yaml
import csv
from pathlib import Path
from datetime import datetime

from src.env.scenes import make_batch
from src.loop.evaluate import evaluate
from src.grammar.utils import load_base_grammar
from src.env.scoring import score_fn
from src.agents.proposer import propose
from src.grammar.mutations import apply_patch

def load_config(config_path: str = "configs/defaults.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def save_grammar_artifact(grammar: str, round_idx: int, artifacts_dir: str = "artifacts"):
    """Save grammar artifact for a specific round."""
    Path(artifacts_dir).mkdir(exist_ok=True)
    grammar_path = Path(artifacts_dir) / f"grammar_round_{round_idx}.lark"
    grammar_path.write_text(grammar)
    return grammar_path

def log_round_results(round_idx: int, metrics: dict, grammar: str, artifacts_dir: str = "artifacts"):
    """Log round results to CSV and save grammar artifact."""
    Path(artifacts_dir).mkdir(exist_ok=True)

    # Save grammar artifact
    grammar_path = save_grammar_artifact(grammar, round_idx, artifacts_dir)

    # Log to CSV
    csv_path = Path(artifacts_dir) / "evolution_log.csv"
    file_exists = csv_path.exists()

    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f)

        if not file_exists:
            # Write header
            writer.writerow([
                'round', 'acc', 'avg_len', 'productions', 'avg_rhs',
                'collisions', 'parse_fail', 'notes'
            ])

        # Write data row
        writer.writerow([
            round_idx,
            f"{metrics['accuracy']:.3f}",
            f"{metrics['avg_msg_chars']:.2f}",
            metrics['grammar_complexity']['productions'],
            f"{metrics['grammar_complexity']['avg_rhs_symbols']:.2f}",
            f"{metrics['collisions']:.3f}",
            f"{metrics['parse_fail_rate']:.3f}",
            f"grammar: {grammar_path.name}"
        ])

    return csv_path

def main():
    parser = argparse.ArgumentParser(description="CFG-Neuralese evolutionary evaluation")
    parser.add_argument("--config", default="configs/defaults.yaml",
                       help="Path to config file")
    parser.add_argument("--batch-size", type=int,
                       help="Override batch size from config")
    parser.add_argument("--rounds", type=int, default=10,
                       help="Number of evolutionary rounds")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output with examples")
    parser.add_argument("--artifacts-dir", default="artifacts",
                       help="Directory to save artifacts")

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Override batch size if provided
    if args.batch_size:
        config["batch_size"] = args.batch_size

    print(f"🧠 CFG-Neuralese Evolutionary Evaluation")
    print(f"📊 Batch size: {config['batch_size']}")
    print(f"🎯 K objects: {config['k_objects']}")
    print(f"🔄 Rounds: {args.rounds}")
    print()

    # Load base grammar
    grammar = load_base_grammar()
    print("📝 Base Grammar:")
    print(grammar)
    print()

    # Create artifacts directory
    Path(args.artifacts_dir).mkdir(exist_ok=True)

    # Evolutionary loop
    for round_idx in range(args.rounds):
        print(f"🔄 Round {round_idx}")
        print("=" * 50)

        # Generate scenes for this round
        scenes = make_batch(
            colors=config["attributes"]["color"],
            shapes=config["attributes"]["shape"],
            sizes=config["attributes"]["size"],
            batch_size=config["batch_size"],
            k=config["k_objects"]
        )

        # Evaluate current grammar
        metrics, examples = evaluate(grammar, scenes, return_examples=True)

        # Calculate composite score
        composite_score = score_fn(
            acc=metrics["accuracy"],
            avg_chars=metrics["avg_msg_chars"],
            complexity=metrics["grammar_complexity"],
            collisions=metrics["collisions"],
            lambdas=config["lambdas"]
        )

        # Print results
        print(f"📈 Results:")
        print(f"  Accuracy: {metrics['accuracy']:.3f} ({metrics['n_correct']}/{metrics['n_scenes']})")
        print(f"  Avg Message Length: {metrics['avg_msg_chars']:.1f} chars")
        print(f"  Collision Rate: {metrics['collisions']:.3f}")
        print(f"  Parse Fail Rate: {metrics['parse_fail_rate']:.3f}")
        print(f"  Grammar Complexity: {metrics['grammar_complexity']['productions']} productions")
        print(f"  Composite Score: {composite_score:.3f}")

        # Log round results
        log_round_results(round_idx, metrics, grammar, args.artifacts_dir)

        # Check stopping criteria
        if metrics['accuracy'] >= 0.97 and metrics['avg_msg_chars'] <= 10:
            print("✅ Stopping criteria met!")
            break

        # Stop if accuracy is too low
        if metrics['accuracy'] < 0.90:
            print("⛔ Accuracy too low, stopping evolution")
            break

        # Ask proposer for mutations
        print(f"\n🤖 Asking proposer for mutations...")
        try:
            patch = propose(grammar, metrics, examples[:5])
            print(f"✅ Proposer returned {len(patch.get('mutations', []))} mutations")

            # Quick validation
            ok_ops = {"rename_terminal", "remove_separators", "restrict_terminal", "replace_rule"}
            muts = patch.get("mutations", [])
            if not isinstance(muts, list) or any(m.get("op") not in ok_ops for m in muts):
                print("⚠️ Invalid patch, skipping")
                continue

            # Apply patch
            grammar_candidate = apply_patch(grammar, patch)

            # Smoke test the candidate
            print("🧪 Smoke testing candidate grammar...")
            smoke_metrics, _ = evaluate(grammar_candidate, scenes[:20], return_examples=False)

            if smoke_metrics["parse_fail_rate"] > 0.05:
                print("⛔ Parse fails too high; rejecting patch")
                continue

            if smoke_metrics["accuracy"] < 0.90:
                print("⛔ Accuracy regressed too far; rejecting patch")
                continue

            # Accept the patch
            grammar = grammar_candidate
            print("✅ Patch accepted!")

        except Exception as e:
            print(f"❌ Proposer failed: {e}")
            continue

        print()  # Empty line between rounds

    # Final evaluation
    print(f"\n🏁 Final Results")
    print("=" * 50)

    final_scenes = make_batch(
        colors=config["attributes"]["color"],
        shapes=config["attributes"]["shape"],
        sizes=config["attributes"]["size"],
        batch_size=config["batch_size"],
        k=config["k_objects"]
    )

    final_metrics = evaluate(grammar, final_scenes)
    final_score = score_fn(
        acc=final_metrics["accuracy"],
        avg_chars=final_metrics["avg_msg_chars"],
        complexity=final_metrics["grammar_complexity"],
        collisions=final_metrics["collisions"],
        lambdas=config["lambdas"]
    )

    print(f"📈 Final Metrics:")
    print(f"  Accuracy: {final_metrics['accuracy']:.3f}")
    print(f"  Avg Message Length: {final_metrics['avg_msg_chars']:.1f} chars")
    print(f"  Composite Score: {final_score:.3f}")

    print(f"\n📝 Final Grammar:")
    print(grammar)

    # Save final grammar
    final_grammar_path = Path(args.artifacts_dir) / "final_grammar.lark"
    final_grammar_path.write_text(grammar)
    print(f"\n💾 Final grammar saved to: {final_grammar_path}")

if __name__ == "__main__":
    main()
