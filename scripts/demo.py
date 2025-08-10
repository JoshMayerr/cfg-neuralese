#!/usr/bin/env python3
"""Main demo script for CFG-Neuralese demonstration."""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from artifacts.io import load_text, load_json


def check_prerequisites():
    """Check if we have the required artifacts for the demo."""
    required_files = [
        "artifacts/best/grammar.lark",
        "artifacts/best/fewshots.json"
    ]

    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)

    if missing:
        print("❌ Missing required artifacts:")
        for file_path in missing:
            print(f"   - {file_path}")
        print("\n💡 Run the offline optimization first:")
        print("   python scripts/offline_optimize.py")
        return False

    return True


def act1_offline_optimization():
    """Act 1: Run offline optimization to generate best artifacts."""
    print("🎭 ACT 1: OFFLINE OPTIMIZATION")
    print("=" * 50)
    print("This will run a longer optimization to find the best grammar.")
    print("The results will be saved for the live demo.")
    print()

    input("Press Enter to start offline optimization...")

    # Import and run offline optimization
    from scripts.offline_optimize import offline_optimize
    offline_optimize()


def act2_live_process():
    """Act 2: Show live evolutionary process."""
    print("\n🎭 ACT 2: LIVE EVOLUTIONARY PROCESS")
    print("=" * 50)
    print("This will show a short, live demonstration of the evolution process.")
    print("Perfect for showing the audience how the system works.")
    print()

    input("Press Enter to start live process...")

    # Import and run live process
    from scripts.live_process import live_process
    from grammar.utils import load_base_grammar

    grammar = load_base_grammar()
    live_process(grammar, rounds=3, batch_size=50)


def act3_use_saved_language():
    """Act 3: Demonstrate the evolved language."""
    print("\n🎭 ACT 3: USING THE EVOLVED LANGUAGE")
    print("=" * 50)
    print("This will demonstrate the evolved language with audience guessing.")
    print("Perfect for showing the final results!")
    print()

    input("Press Enter to start language demonstration...")

    # Import and run use language
    from src.run.use_language import use_saved_language
    use_saved_language(n=3, k=4)


def main():
    parser = argparse.ArgumentParser(description="CFG-Neuralese Demo")
    parser.add_argument("--act", type=int, choices=[1, 2, 3],
                       help="Run specific act (1=offline, 2=live, 3=demo)")
    parser.add_argument("--all", action="store_true",
                       help="Run all acts in sequence")

    args = parser.parse_args()

    print("🎭 CFG-Neuralese Demo")
    print("=" * 50)
    print("This demo shows the evolution of communication protocols.")
    print()

    if args.act:
        # Run specific act
        if args.act == 1:
            act1_offline_optimization()
        elif args.act == 2:
            if not check_prerequisites():
                return
            act2_live_process()
        elif args.act == 3:
            if not check_prerequisites():
                return
            act3_use_saved_language()

    elif args.all:
        # Run all acts in sequence
        act1_offline_optimization()

        if check_prerequisites():
            act2_live_process()
            act3_use_saved_language()
        else:
            print("\n❌ Cannot continue without artifacts from Act 1.")

    else:
        # Interactive mode
        print("Choose an act to run:")
        print("  1. Offline Optimization (generate best artifacts)")
        print("  2. Live Process (show evolution on stage)")
        print("  3. Use Saved Language (demonstrate results)")
        print("  4. Run all acts")
        print()

        choice = input("Enter your choice (1-4): ").strip()

        if choice == "1":
            act1_offline_optimization()
        elif choice == "2":
            if check_prerequisites():
                act2_live_process()
            else:
                print("❌ Run Act 1 first to generate artifacts.")
        elif choice == "3":
            if check_prerequisites():
                act3_use_saved_language()
            else:
                print("❌ Run Act 1 first to generate artifacts.")
        elif choice == "4":
            act1_offline_optimization()
            if check_prerequisites():
                act2_live_process()
                act3_use_saved_language()
        else:
            print("❌ Invalid choice.")


if __name__ == "__main__":
    main()
