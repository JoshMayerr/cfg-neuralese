#!/usr/bin/env python3
"""
CFG-Neuralese: Main CLI for running evaluations.

Phase 1 MVP: Run single evaluation with baseline grammar.
"""

import argparse
import json
import yaml
from pathlib import Path

from src.env.scenes import make_batch
from src.loop.evaluate import evaluate
from src.grammar.utils import load_base_grammar
from src.env.scoring import score_fn

def load_config(config_path: str = "configs/defaults.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="CFG-Neuralese evaluation")
    parser.add_argument("--config", default="configs/defaults.yaml",
                       help="Path to config file")
    parser.add_argument("--batch-size", type=int,
                       help="Override batch size from config")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output with examples")

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Override batch size if provided
    if args.batch_size:
        config["batch_size"] = args.batch_size

    print(f"🧠 CFG-Neuralese MVP Evaluation")
    print(f"📊 Batch size: {config['batch_size']}")
    print(f"🎯 K objects: {config['k_objects']}")
    print()

    # Load base grammar
    grammar = load_base_grammar()
    print("📝 Base Grammar:")
    print(grammar)
    print()

    # Generate scenes
    print("🎭 Generating scenes...")
    scenes = make_batch(
        colors=config["attributes"]["color"],
        shapes=config["attributes"]["shape"],
        sizes=config["attributes"]["size"],
        batch_size=config["batch_size"],
        k=config["k_objects"]
    )

    # Run evaluation
    print("🔍 Running evaluation...")
    metrics = evaluate(grammar, scenes)

    # Calculate composite score
    composite_score = score_fn(
        acc=metrics["accuracy"],
        avg_chars=metrics["avg_msg_chars"],
        complexity=metrics["grammar_complexity"],
        collisions=metrics["collisions"],
        lambdas=config["lambdas"]
    )

    # Print results
    print("\n📈 Results:")
    print(f"  Accuracy: {metrics['accuracy']:.3f} ({metrics['n_correct']}/{metrics['n_scenes']})")
    print(f"  Avg Message Length: {metrics['avg_msg_chars']:.1f} chars")
    print(f"  Collision Rate: {metrics['collisions']:.3f}")
    print(f"  Parse Fail Rate: {metrics['parse_fail_rate']:.3f}")
    print(f"  Grammar Complexity: {metrics['grammar_complexity']['productions']} productions")
    print(f"  Composite Score: {composite_score:.3f}")

    # Show examples if verbose
    if args.verbose and metrics["examples"]:
        print("\n🔍 Examples:")
        for i, example in enumerate(metrics["examples"][:3]):
            print(f"\nExample {i+1}:")
            target = example["scene"]["objects"][example["scene"]["target_idx"]]
            print(f"  Target: {target}")
            print(f"  Message: '{example['message']}'")
            print(f"  Prediction: {example['prediction']} ({'✓' if example['correct'] else '✗'})")

    # Check if meets Phase 1 exit criteria
    print(f"\n🎯 Phase 1 Exit Criteria:")
    print(f"  Accuracy > 97%: {'✓' if metrics['accuracy'] > 0.97 else '✗'} ({metrics['accuracy']:.1%})")
    print(f"  Parse fails < 5%: {'✓' if metrics['parse_fail_rate'] < 0.05 else '✗'} ({metrics['parse_fail_rate']:.1%})")

    if metrics['accuracy'] > 0.97 and metrics['parse_fail_rate'] < 0.05:
        print("🎉 Phase 1 MVP criteria met! Ready for Phase 2.")
    else:
        print("⚠️  Phase 1 criteria not yet met. Check OpenAI client implementation.")

if __name__ == "__main__":
    main()
