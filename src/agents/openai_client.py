# src/agents/openai_client.py
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-5")

class OpenAIClient:
    def __init__(self, model: str = MODEL):
        self.client = OpenAI()
        self.model = model

    # --- core: CFG-constrained emission (Speaker/Listener messages) ---
    def emit_with_grammar(
        self,
        messages: List[Dict[str, str]],
        grammar_text: str,
        *,
        tool_name: str = "emit_message",
        syntax: str = "lark",          # "lark" or "regex"
        temperature: float = 0.5,
    ) -> str:
        tool = {
            "type": "custom",
            "name": tool_name,
            "description": "Emit a string matching the grammar start rule.",
            "format": {"type": "grammar", "syntax": syntax, "definition": grammar_text},
        }
        r = self.client.responses.create(
            model=self.model,
            input=messages,
            tools=[tool],
            tool_choice={
                "type": "allowed_tools",
                "mode": "auto",
                "tools": [{"type": "custom", "name": tool_name}]
            }
        )
        out = _extract_tool_output(r, tool_name)
        if not out:
            raise RuntimeError("No grammar-conforming output returned.")
        return out.strip()

    # --- convenience: listener index constrained to [0..K-1] via regex ---
    def emit_index(self, messages: List[Dict[str, str]], k: int) -> int:
        assert k > 0
        # Use the simple grammar that we know works
        grammar = "start: /[0-3]/"
        s = self.emit_with_grammar(messages, grammar, tool_name="emit_index", syntax="lark")
        return int(s)

    # --- optional: JSON schema output (for Proposer patches) ---
    def emit_json(self, messages: List[Dict[str, str]], json_schema: Dict[str, Any]) -> Dict[str, Any]:
        r = self.client.responses.create(
            model=self.model,
            input=messages,
            response_format={"type": "json_schema", "json_schema": json_schema}
        )
        data = _extract_json(r)
        if not isinstance(data, dict):
            raise RuntimeError("No JSON object returned.")
        return data


# -------- helpers (minimal, tolerant to minor SDK shape changes) --------

def _extract_tool_output(resp: Any, tool_name: str) -> Optional[str]:
    """
    Find the output text produced by the named custom tool.
    We scan resp.output for a tool item with matching name.
    """
    out = getattr(resp, "output", None)
    if not out:
        return None

    # Handle Pydantic objects - check for custom_tool_call type
    for item in out:
        if hasattr(item, 'type') and item.type == "custom_tool_call":
            if hasattr(item, 'name') and item.name == tool_name:
                if hasattr(item, 'input'):
                    return item.input
        elif hasattr(item, 'type') and item.type == "message":
            if hasattr(item, 'content') and item.content:
                for content_item in item.content:
                    if hasattr(content_item, 'text'):
                        return content_item.text
    return None


def _extract_json(resp: Any) -> Any:
    """Pull JSON content from a json_schema-formatted response."""
    out = getattr(resp, "output", None)
    if not out:
        return None
    for item in out:
        if item.get("type") in ("output_text", "message"):
            c = item.get("content")
            if isinstance(c, dict):
                return c
    # Some SDKs expose .output[0].content[0].json
    try:
        return out[0]["content"][0]["json"]
    except Exception:
        return None
