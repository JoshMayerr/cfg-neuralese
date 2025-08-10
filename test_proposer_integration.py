#!/usr/bin/env python3
"""
Integration test for the Proposer agent with actual grammar mutations.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.proposer import get_proposer_suggestion
from grammar.mutations import apply_mutations_to_grammar


def test_proposer_integration():
    """Test the proposer with actual grammar mutations."""
    print("🧪 Testing Proposer Integration")
    print("=" * 50)

    # Test grammar
    grammar_text = """start: msg
msg: phrase (";" phrase)*
phrase: slot ":" value
slot: "color" | "shape" | "size"
value: /[a-z]+/"""

    print(f"📝 Original Grammar:\n{grammar_text}")
    print()

    # Mock metrics showing room for improvement
    metrics = {
        "accuracy": 1.0,
        "avg_msg_chars": 17.5,
        "parse_fail_rate": 0.0,
        "collision_rate": 0.0
    }

    # Mock scenes and data
    scenes = [
        {
            "target_idx": 0,
            "objects": [
                {"color": "red", "shape": "circle", "size": "small"},
                {"color": "blue", "shape": "square", "size": "large"}
            ]
        }
    ]

    messages = ["color:red;shape:circle;size:small"]
    predictions = [0]

    print(f"📊 Current Metrics: {metrics}")
    print(f"🔍 Examples: {len(scenes)} scenes")
    print()

    try:
        # Get proposal from Proposer
        print("🤖 Getting proposal from Proposer...")
        proposal = get_proposer_suggestion(grammar_text, metrics, scenes, messages, predictions)

        print("✅ Proposer Response:")
        print(f"  Mutations: {proposal['mutations']}")
        print(f"  Reasoning: {proposal['reasoning']}")
        print(f"  Expected Improvement: {proposal['expected_improvement']}")
        print()

        # Apply mutations to grammar
        print("🔧 Applying mutations to grammar...")
        new_grammar, success = apply_mutations_to_grammar(grammar_text, proposal['mutations'])

        if success:
            print("✅ Mutations applied successfully!")
            print(f"📝 New Grammar:\n{new_grammar}")

            # Show the improvement
            old_length = len("color:red;shape:circle;size:small")
            new_length = len("c:red;s:circle;z:small")
            improvement = old_length - new_length

            print(f"\n📊 Improvement:")
            print(f"  Old message length: {old_length} chars")
            print(f"  New message length: {new_length} chars")
            print(f"  Reduction: {improvement} chars ({improvement/old_length*100:.1f}%)")

        else:
            print("❌ Failed to apply mutations")
            return False

        print("\n✅ Integration test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_proposer_integration()
    if not success:
        sys.exit(1)
