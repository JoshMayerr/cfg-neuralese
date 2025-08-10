"""Artifact I/O helpers for saving and loading demo artifacts."""

from pathlib import Path
import json
import csv
from typing import Dict, Any, List


def save_text(path: str, text: str) -> None:
    """Save text content to a file, creating directories as needed."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text)


def load_text(path: str) -> str:
    """Load text content from a file."""
    return Path(path).read_text()


def save_json(path: str, obj: Dict[str, Any]) -> None:
    """Save JSON object to a file, creating directories as needed."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2))


def load_json(path: str) -> Dict[str, Any]:
    """Load JSON object from a file."""
    return json.loads(Path(path).read_text())


def append_csv(path: str, row: Dict[str, Any], header: List[str]) -> None:
    """Append a row to a CSV file, creating header if file doesn't exist."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    file_exists = Path(path).exists()

    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        if not file_exists:
            w.writeheader()
        w.writerow(row)
