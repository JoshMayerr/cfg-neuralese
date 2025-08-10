#!/usr/bin/env python3
"""
CFG-Neuralese: Main CLI for running evaluations.

Phase 2: Evolutionary loop with proposer integration.
"""

import argparse
import json
import yaml
import csv
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from src.env.scenes import make_batch
from src.loop.evaluate import evaluate
from src.grammar.utils import load_base_grammar
from src.env.scoring import score_fn
from src.agents.proposer import propose
from src.grammar.mutations import apply_patch

def make_run_dir(base: str) -> Path:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(base) / f"run_{run_id}"
    (run_dir / "grammars").mkdir(parents=True, exist_ok=True)
    (run_dir / "metrics").mkdir(parents=True, exist_ok=True)
    (run_dir / "proposer").mkdir(parents=True, exist_ok=True)
    return run_dir

def fewshots_from_examples(examples: List[Dict]) -> Dict[str, List[Dict]]:
    # grab up to 2 correct examples for tiny demo-time few-shots
    spk, lst = [], []
    for ex in examples:
        if ex.get("correct") and len(spk) < 2:
            # speaker few-shot expects scene + message
            spk.append({"scene": ex["scene"]["objects"][ex["scene"]["target_idx"]], "message": ex["message"]})
            # listener few-shot expects message + answer index
            lst.append({"message": ex["message"], "answer": ex["prediction"]})
    return {"speaker": spk, "listener": lst}

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

    # Seed for reproducibility (optional)
    random.seed(42)

    # Make a unique run directory and point artifacts there
    run_dir = make_run_dir(args.artifacts_dir)
    print(f"🗂️  Run dir: {run_dir}")

    # Snapshot config
    (Path(run_dir) / "config.json").write_text(json.dumps(config, indent=2))

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

    # Track "best so far" and save proposer I/O
    best_score = float("-inf")
    best_grammar = None
    best_fewshots = {"speaker": [], "listener": []}

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
        result = evaluate(grammar, scenes, return_examples=True)
        metrics = result
        examples = result.get("examples", [])

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
        log_round_results(round_idx, metrics, grammar, str(run_dir))

        # Update best-so-far bundle
        if composite_score > best_score:
            best_score = composite_score
            best_grammar = grammar
            # derive tiny few-shots from this round's successful examples
            best_fewshots = fewshots_from_examples(examples)

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

        # create a compact proposer input text for provenance
        proposer_input_text = (
            "=== Current Grammar ===\n" + grammar + "\n\n" +
            "=== Metrics ===\n" + json.dumps(metrics, indent=2) + "\n\n" +
            "=== Examples (first 5) ===\n" + json.dumps(examples[:5], indent=2)
        )

        try:
            # Extract messages and predictions from examples for proposer
            messages = [ex["message"] for ex in examples[:5]]
            predictions = [ex["prediction"] for ex in examples[:5]]

            patch = propose(grammar, metrics, examples[:5], messages, predictions)
            print(f"✅ Proposer returned {len(patch.get('mutations', []))} mutations")

            # Save proposer I/O
            (Path(run_dir) / "proposer" / f"round_{round_idx:03d}_in.txt").write_text(proposer_input_text)
            (Path(run_dir) / "proposer" / f"round_{round_idx:03d}_out.json").write_text(json.dumps(patch, indent=2))

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

            # Save current grammar for this round
            (Path(run_dir) / "grammars" / f"round_{round_idx:03d}.lark").write_text(grammar)

        except Exception as e:
            print(f"❌ Proposer failed: {e}")
            continue

        print()  # Empty line between rounds

    # Final evaluation (skip if we already have final results from stopping criteria)
    print(f"\n🏁 Final Results")
    print("=" * 50)

    # If we stopped early due to criteria, use the last round's results
    if round_idx < args.rounds - 1:
        print("✅ Stopped early due to criteria - using last round results")
        final_metrics = metrics  # Use metrics from the last completed round
        final_score = composite_score
    else:
        # Only do final evaluation if we went through all rounds
        print("🔄 Completed all rounds - doing final evaluation...")
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
    final_grammar_path = Path(run_dir) / "final_grammar.lark"
    final_grammar_path.write_text(grammar)
    print(f"\n💾 Final grammar saved to: {final_grammar_path}")

    # Also export "best" bundle for the show
    best_dir = Path("artifacts") / "best"
    best_dir.mkdir(parents=True, exist_ok=True)
    (best_dir / "grammar.lark").write_text(best_grammar or grammar)
    (best_dir / "fewshots.json").write_text(json.dumps(best_fewshots, indent=2))

    print(f"💾 Best grammar → {best_dir / 'grammar.lark'}")
    print(f"💾 Few-shots    → {best_dir / 'fewshots.json'}")

if __name__ == "__main__":
    main()
