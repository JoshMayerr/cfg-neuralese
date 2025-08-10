import os
from typing import Dict, Any
from pathlib import Path
import json

def load_base_grammar() -> str:
    """Load the base grammar from file."""
    grammar_path = os.path.join(os.path.dirname(__file__), "base_grammar.lark")
    with open(grammar_path, "r") as f:
        return f.read()

def validate_grammar(grammar: str) -> bool:
    """Basic validation of grammar syntax."""
    # Simple checks for now
    lines = grammar.strip().split('\n')

    # Check for start rule
    has_start = any('start:' in line for line in lines)
    if not has_start:
        return False

    # Check basic syntax
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' not in line:
            return False

    return True

def grammar_stats(grammar: str) -> Dict[str, Any]:
    """Get basic statistics about a grammar."""
    lines = grammar.strip().split('\n')
    non_empty_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]

    rules = [line for line in non_empty_lines if ':' in line]

    return {
        "total_lines": len(lines),
        "non_empty_lines": len(non_empty_lines),
        "rules": len(rules),
        "characters": len(grammar)
    }

def load_grammar(path: str) -> str:
    return Path(path).read_text()

def save_grammar(text: str, path: str) -> None:
    Path(path).write_text(text)

def load_fewshots(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists(): return {"speaker": [], "listener": []}
    return json.loads(p.read_text())
