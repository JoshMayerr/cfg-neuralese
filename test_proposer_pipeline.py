#!/usr/bin/env python3
"""
Test the full proposer → mutations → updated grammar pipeline.
"""

import json
from src.agents.proposer import propose
from src.grammar.mutations import apply_mutations_to_grammar
# No need for this import

def test_proposer_pipeline():
    """Test the complete pipeline from proposer to mutated grammar."""

    # Load the base grammar
    grammar_path = "src/grammar/base_grammar.lark"
    with open(grammar_path, 'r') as f:
        base_grammar = f.read()

    print("=== Original Grammar ===")
    print(base_grammar)
    print()

    # Mock metrics and examples for testing
    test_metrics = {
        "accuracy": 1.0,
        "avg_msg_chars": 17.5,
        "parse_fail_rate": 0.0,
        "collision_rate": 0.0
    }

    test_scenes = [
        {
            "target_idx": 0,
            "objects": [
                {"color": "red", "shape": "circle", "size": "small"},
                {"color": "blue", "shape": "square", "size": "large"}
            ]
        }
    ]

    test_messages = ["color:red;shape:circle;size:small"]
    test_predictions = [0]

    print("=== Getting Proposer Suggestions ===")
    try:
        # Get mutation suggestions from proposer
        patch = propose(
            base_grammar,
            test_metrics,
            test_scenes,
            test_messages,
            test_predictions
        )

        print("✅ Proposer returned:")
        print(json.dumps(patch, indent=2))
        print()

        # Apply mutations to grammar
        print("=== Applying Mutations ===")
        new_grammar, success = apply_mutations_to_grammar(base_grammar, patch['mutations'])

        if success:
            print("✅ Mutations applied successfully!")
            print()
            print("=== Updated Grammar ===")
            print(new_grammar)
            print()

            # Save the mutated grammar
            output_path = "src/grammar/mutated_grammar.lark"
            with open(output_path, 'w') as f:
                f.write(new_grammar)
            print(f"💾 Mutated grammar saved to: {output_path}")

        else:
            print("❌ Failed to apply mutations")

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_proposer_pipeline()
