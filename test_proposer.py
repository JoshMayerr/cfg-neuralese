#!/usr/bin/env python3
"""
Simple test script for the Proposer agent.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.proposer import get_proposer_suggestion


def test_proposer():
    """Test the proposer with mock data."""
    print("🧪 Testing Proposer Agent")
    print("=" * 50)

    # Test grammar
    grammar_text = """start: msg
msg: phrase (";" phrase)*
phrase: slot ":" value
slot: "color" | "shape" | "size"
value: /[a-z]+/"""

    print(f"📝 Base Grammar:\n{grammar_text}")
    print()

    # Mock metrics
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

    print(f"📊 Mock Metrics: {json.dumps(metrics, indent=2)}")
    print(f"🔍 Examples: {len(scenes)} scenes")
    print()

    try:
        # Get proposal from GPT-5
        print("🤖 Calling Proposer...")
        proposal = get_proposer_suggestion(grammar_text, metrics, scenes, messages, predictions)

        print("✅ Proposer Response:")
        print(json.dumps(proposal, indent=2))
        print()

        # Validate response structure
        if "mutations" in proposal:
            print(f"🔧 Proposed {len(proposal['mutations'])} mutations")
            print("✅ Proposer test completed successfully!")
            return True
        else:
            print("❌ Response missing 'mutations' key")
            return False

    except Exception as e:
        print(f"❌ Proposer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_proposer()
    if not success:
        sys.exit(1)
