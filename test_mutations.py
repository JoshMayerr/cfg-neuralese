#!/usr/bin/env python3
"""
Manual mutation testing script.

Tests the impact of grammar mutations on message length and accuracy
to validate our mutation engine before building the Proposer.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.grammar.mutations import apply_mutations_to_grammar
from src.loop.evaluate import evaluate
from src.env.scenes import make_batch
from src.grammar.utils import load_base_grammar


def test_mutation_impact():
    """Test how mutations affect grammar performance."""

    print("🧬 Testing Grammar Mutations")
    print("=" * 50)

    # Load base grammar
    base_grammar = load_base_grammar()
    print(f"📝 Base Grammar:\n{base_grammar}\n")

    # Generate test scenes
    scenes = make_batch(['red', 'blue', 'green', 'yellow'],
                        ['circle', 'square', 'triangle', 'diamond'],
                        ['small', 'large', 'medium', 'huge'],
                        batch_size=2, k=4)

    # Evaluate base grammar
    print("🔍 Evaluating base grammar...")
    base_metrics = evaluate(base_grammar, scenes)
    print(f"  Accuracy: {base_metrics['accuracy']:.3f}")
    print(f"  Avg Length: {base_metrics['avg_msg_chars']:.1f} chars")
    print(f"  Parse Fail Rate: {base_metrics['parse_fail_rate']:.3f}")
    print()

    # Test mutations
    mutations_to_test = [
        {
            "name": "Rename Terminals (c/s/z)",
            "mutations": [
                {"type": "rename_terminal", "old": "color", "new": "c"},
                {"type": "rename_terminal", "old": "shape", "new": "s"},
                {"type": "rename_terminal", "old": "size", "new": "z"}
            ],
            "description": "Shorten terminal names to single letters"
        },
        {
            "name": "Remove Separators",
            "mutations": [
                {"type": "remove_separators"}
            ],
            "description": "Change from semicolon to whitespace separation"
        },
        {
            "name": "Restrict Value Length",
            "mutations": [
                {"type": "restrict_value_length", "length": 3}
            ],
            "description": "Limit value to exactly 3 characters"
        },
        {
            "name": "Simplify Message Rule",
            "mutations": [
                {"type": "simplify_message_rule"}
            ],
            "description": "Change from multiple phrases to single phrase"
        }
    ]

    best_mutation = None
    best_score = float('-inf')

    for mutation in mutations_to_test:
        print(f"🧪 Testing: {mutation['name']}")
        print(f"   Description: {mutation['description']}")

        # Apply mutations
        new_grammar, success = apply_mutations_to_grammar(
            base_grammar,
            mutation['mutations']
        )

        if not success:
            print("   ❌ Mutation failed!")
            print()
            continue

        print(f"   New Grammar:\n{new_grammar}")

        # Evaluate mutated grammar
        try:
            new_metrics = evaluate(new_grammar, scenes)

            # Calculate improvement
            length_improvement = base_metrics['avg_msg_chars'] - new_metrics['avg_msg_chars']
            accuracy_change = new_metrics['accuracy'] - base_metrics['accuracy']

            print(f"   📊 Results:")
            print(f"     Accuracy: {new_metrics['accuracy']:.3f} ({accuracy_change:+.3f})")
            print(f"     Avg Length: {new_metrics['avg_msg_chars']:.1f} chars ({length_improvement:+.1f})")
            print(f"     Parse Fail Rate: {new_metrics['parse_fail_rate']:.3f}")

            # Simple scoring: prioritize accuracy, then length reduction
            if new_metrics['accuracy'] >= 0.95:  # Maintain 95%+ accuracy
                score = length_improvement - (new_metrics['parse_fail_rate'] * 10)
                if score > best_score:
                    best_score = score
                    best_mutation = mutation
                print(f"   ✅ Valid mutation (score: {score:.2f})")
            else:
                print(f"   ❌ Accuracy too low (< 95%)")

        except Exception as e:
            print(f"   ❌ Evaluation failed: {e}")

        print()

    # Summary
    if best_mutation:
        print("🏆 Best Mutation Found:")
        print(f"   {best_mutation['name']}: {best_mutation['description']}")
        print(f"   Score: {best_score:.2f}")
    else:
        print("⚠️  No beneficial mutations found")

    return best_mutation


if __name__ == "__main__":
    test_mutation_impact()
