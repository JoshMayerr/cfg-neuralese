#!/usr/bin/env python3
"""
Minimal test of the evolutionary pipeline with tiny batch sizes.
"""

import json
from src.agents.proposer import propose
from src.grammar.mutations import apply_patch
from src.env.scenes import make_batch
from src.loop.evaluate import evaluate

def test_evolution_mini():
    """Test the evolution pipeline with minimal data."""

    print("🧪 Testing Evolution Pipeline (Mini)")
    print("=" * 40)

    # Load the base grammar
    grammar_path = "src/grammar/base_grammar.lark"
    with open(grammar_path, 'r') as f:
        base_grammar = f.read()

    print("📝 Base Grammar:")
    print(base_grammar)
    print()

    # Generate just 2 scenes for testing
    scenes = make_batch(
        colors=["red", "blue"],
        shapes=["circle", "square"],
        sizes=["small", "large"],
        batch_size=2,
        k=2
    )

    print(f"🎭 Generated {len(scenes)} scenes")
    for i, scene in enumerate(scenes):
        target = scene["objects"][scene["target_idx"]]
        print(f"  Scene {i}: Target = {target}")
    print()

    # Evaluate baseline grammar
    print("🔍 Evaluating baseline grammar...")
    metrics = evaluate(base_grammar, scenes, return_examples=True)
    examples = metrics.get('examples', [])

    print(f"📊 Baseline Results:")
    print(f"  Accuracy: {metrics['accuracy']:.3f}")
    print(f"  Avg Length: {metrics['avg_msg_chars']:.1f} chars")
    print(f"  Parse Fail Rate: {metrics['parse_fail_rate']:.3f}")
    print()

    # Get proposer suggestions
    print("🤖 Asking proposer for mutations...")
    try:
        # Extract messages and predictions from examples
        messages = [ex['message'] for ex in examples]
        predictions = [ex['prediction'] for ex in examples]

        patch = propose(base_grammar, metrics, scenes, messages, predictions)
        print("✅ Proposer returned:")
        print(json.dumps(patch, indent=2))
        print()

        # Apply mutations
        print("🔧 Applying mutations...")
        new_grammar = apply_patch(base_grammar, patch)

        print("📝 New Grammar:")
        print(new_grammar)
        print()

        # Quick smoke test
        print("🧪 Smoke testing new grammar...")
        smoke_metrics = evaluate(new_grammar, scenes, return_examples=False)

        print(f"📊 Smoke Test Results:")
        print(f"  Accuracy: {smoke_metrics['accuracy']:.3f}")
        print(f"  Parse Fail Rate: {smoke_metrics['parse_fail_rate']:.3f}")

        if smoke_metrics['parse_fail_rate'] <= 0.05 and smoke_metrics['accuracy'] >= 0.90:
            print("✅ Smoke test passed!")
        else:
            print("⚠️ Smoke test failed")

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_evolution_mini()
