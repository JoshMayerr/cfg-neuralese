"""Save best artifacts from offline optimization runs."""

from .io import save_text, save_json
from typing import List, Dict, Any, Optional


def save_best(
    grammar_text: str,
    speaker_fs: List[Dict[str, Any]],
    listener_fs: List[Dict[str, Any]],
    showcase_scenes: Optional[List[Dict[str, Any]]] = None,
    storyboard: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save the best artifacts from an optimization run.

    Args:
        grammar_text: The evolved grammar text
        speaker_fs: Speaker few-shot examples
        listener_fs: Listener few-shot examples
        showcase_scenes: Optional showcase scenes for demos
        storyboard: Optional v0/mid/final message progression for one scene
    """
    # Save best grammar
    save_text("artifacts/best/grammar.lark", grammar_text)

    # Save few-shots
    save_json("artifacts/best/fewshots.json", {
        "speaker": speaker_fs,
        "listener": listener_fs
    })

    # Save optional showcase scenes
    if showcase_scenes is not None:
        save_json("artifacts/best/showcase_scenes.json", {
            "scenes": showcase_scenes
        })

    # Save optional storyboard
    if storyboard is not None:
        save_json("artifacts/best/storyboard.json", storyboard)

    print(f"💾 Best artifacts saved to artifacts/best/")
    print(f"  - Grammar: artifacts/best/grammar.lark")
    print(f"  - Few-shots: artifacts/best/fewshots.json")
    if showcase_scenes is not None:
        print(f"  - Showcase scenes: artifacts/best/showcase_scenes.json")
    if storyboard is not None:
        print(f"  - Storyboard: artifacts/best/storyboard.json")
