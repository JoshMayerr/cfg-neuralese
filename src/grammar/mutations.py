"""
Simple grammar mutation functions for manual testing.

These functions apply specific, targeted changes to the grammar
to test compression while maintaining functionality.
"""

from pathlib import Path
from typing import Dict, List, Tuple


def rename_terminal(grammar_text: str, old: str, new: str) -> str:
    """
    Rename a terminal in the slot rule.
    Example: "color" -> "c"
    """
    return grammar_text.replace(f'"{old}"', f'"{new}"')


def remove_separators(grammar_text: str) -> str:
    """
    Change msg rule from semicolon-separated to whitespace-separated phrases.
    Keeps colons between slot and value.
    """
    return grammar_text.replace(
        'msg: phrase (";" phrase)*',
        'msg: phrase (/[ \\t]+/ phrase)*'
    )


def restrict_value_length(grammar_text: str, length: int) -> str:
    """
    Restrict value terminal to exact length.
    Example: /[a-z]+/ -> /[a-z]{3}/
    """
    return grammar_text.replace('/[a-z]+/', f'/[a-z]{{{length}}}/')


def simplify_message_rule(grammar_text: str) -> str:
    """
    Simplify msg rule to single phrase instead of multiple.
    """
    return grammar_text.replace(
        'msg: phrase (";" phrase)*',
        'msg: phrase'
    )


def apply_mutations_to_grammar(grammar_text: str, mutations: List[Dict]) -> Tuple[str, bool]:
    """
    Apply a list of mutations to a grammar.

    Args:
        grammar_text: Original Lark grammar text
        mutations: List of mutation dictionaries with 'type' and parameters

    Returns:
        Tuple of (new_grammar_text, success)
    """
    result = grammar_text

    for mutation in mutations:
        mutation_type = mutation['type']

        try:
            if mutation_type == "rename_terminal":
                result = rename_terminal(result, mutation['old'], mutation['new'])
            elif mutation_type == "remove_separators":
                result = remove_separators(result)
            elif mutation_type == "restrict_value_length":
                result = restrict_value_length(result, mutation['length'])
            elif mutation_type == "simplify_message_rule":
                result = simplify_message_rule(result)
            else:
                print(f"Unknown mutation type: {mutation_type}")
                continue

        except Exception as e:
            print(f"Mutation {mutation_type} failed: {e}")
            return grammar_text, False

    return result, True


if __name__ == "__main__":
    # Example usage for manual patching
    grammar_path = Path("src/grammar/base_grammar.lark")
    grammar_text = grammar_path.read_text()

    print("Original grammar:")
    print(grammar_text)
    print()

    # 1) Rename terminals
    print("1. Renaming terminals...")
    grammar_text = rename_terminal(grammar_text, "color", "c")
    grammar_text = rename_terminal(grammar_text, "shape", "s")
    grammar_text = rename_terminal(grammar_text, "size", "z")
    print(grammar_text)
    print()

    # 2) Remove separators
    print("2. Removing separators...")
    grammar_text = remove_separators(grammar_text)
    print(grammar_text)
    print()

    # 3) Restrict value length
    print("3. Restricting value length to 3 chars...")
    grammar_text = restrict_value_length(grammar_text, 3)
    print(grammar_text)
    print()

    # Save as new version
    new_path = Path("src/grammar/manual_patch.lark")
    new_path.write_text(grammar_text)
    print(f"Manual grammar patch saved to {new_path}")
