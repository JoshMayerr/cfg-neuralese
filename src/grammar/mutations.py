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


def add_rule_alternative(grammar_text: str, rule: str, alternative: str) -> str:
    """
    Add an alternative to an existing rule.
    Example: add_rule_alternative("phrase", "slot value")
    changes "phrase: slot ':' value" to "phrase: slot ':' value | slot value"
    """
    lines = grammar_text.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{rule}:"):
            # Add the alternative with a pipe separator
            lines[i] = f"{line.strip()} | {alternative}"
            break
    return '\n'.join(lines)


def replace_rule(grammar_text: str, rule_name: str, new_definition: str) -> str:
    """
    Replace an entire rule definition.
    Example: replace_rule("slot", '"c" | "h" | "z"')
    changes "slot: "color" | "shape" | "size"" to "slot: "c" | "h" | "z""
    """
    lines = grammar_text.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{rule_name}:"):
            # Replace the entire rule definition
            lines[i] = f"{rule_name}: {new_definition}"
            break
    return '\n'.join(lines)


def apply_mutations_to_grammar(grammar_text: str, mutations: List[Dict]) -> Tuple[str, bool]:
    """
    Apply a list of mutations to a grammar.

    Args:
        grammar_text: Original Lark grammar text
        mutations: List of mutation dictionaries with 'op' and parameters

    Returns:
        Tuple of (new_grammar_text, success)
    """
    result = grammar_text

    for mutation in mutations:
        op = mutation['op']

        try:
            if op == "rename":
                result = rename_terminal(result, mutation['from'], mutation['to'])
            elif op == "remove_separators":
                result = remove_separators(result)
            elif op == "restrict_length":
                result = restrict_value_length(result, mutation['length'])
            elif op == "simplify_message_rule":
                result = simplify_message_rule(result)
            elif op == "add_rule_alternative":
                result = add_rule_alternative(result, mutation['lhs'], mutation['rhs'])
            elif op == "replace_rule":
                # Handle both 'name' and 'rule' parameters for compatibility
                rule_name = mutation.get('name') or mutation.get('rule')
                # Handle both 'definition' and 'value' parameters for compatibility
                rule_def = mutation.get('definition') or mutation.get('value')
                if rule_name and rule_def:
                    result = replace_rule(result, rule_name, rule_def)
                else:
                    print(f"replace_rule missing parameters: {mutation}")
                    continue
            else:
                print(f"Unknown operation: {op}")
                continue

        except Exception as e:
            print(f"Mutation {op} failed: {e}")
            return grammar_text, False

    return result, True


def apply_patch(grammar_text: str, patch: dict) -> str:
    """
    Apply a patch to grammar text. Intentionally simple and robust.

    Args:
        grammar_text: Original grammar text
        patch: Dictionary with 'mutations' list

    Returns:
        Modified grammar text
    """
    g = grammar_text
    for m in patch.get("mutations", []):
        op = m.get("op")
        if op == "rename_terminal":
            g = g.replace(f"\"{m['from']}\"", f"\"{m['to']}\"")
        elif op == "remove_separators":
            g = g.replace('msg: phrase (";" phrase)*', 'msg: phrase (/[ \\t]+/ phrase)*')
        elif op == "restrict_terminal":
            # expects m["name"] to be a rule name (e.g., value/C/S/Z)
            # naive replace: add a new definition or tighten an existing one
            g = g.replace(f"{m['name']}: /", f"{m['name']}: /").replace("/\n", "/\n")
            # If the rule doesn't exist, append it:
            if f"{m['name']}:" not in g:
                g += f"\n{m['name']}: /{m['pattern']}/\n"
            else:
                # crude: replace any existing regex body for that rule
                import re
                g = re.sub(rf"({m['name']}\s*:\s*/)[^/]+(/)", rf"\1{m['pattern']}\2", g)
        elif op == "replace_rule":
            # Replace exact rule line: 'rule: ...' with 'rule: definition'
            import re
            rule_name = m.get('rule') or m.get('lhs')
            rule_def = m.get('definition') or m.get('rhs')
            if rule_name and rule_def:
                g = re.sub(rf"^{rule_name}\s*:\s*.*$", f"{rule_name}: {rule_def}", g, flags=re.MULTILINE)
            else:
                print(f"replace_rule missing parameters: {m}")
                continue
        else:
            # ignore unknown ops safely
            continue
    return g


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
