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
    def emit_index(self, messages: List[Dict[str, str]], k: int, *, temperature: float = 0.2) -> int:
        assert k > 0
        # Use the simple grammar that we know works
        grammar = "start: /[0-3]/"
        s = self.emit_with_grammar(messages, grammar, tool_name="emit_index", syntax="lark", temperature=temperature)
        return int(s)

    # --- freeform output via custom tool (for Proposer patches) ---
    def emit_freeform(
        self,
        messages: List[Dict[str, str]],
        *,
        tool_name: str = "propose_patch",
    ) -> str:
        """
        Ask the model to output any freeform text via a custom tool.
        Useful for JSON patches without schema enforcement.
        """
        tool = {
            "type": "custom",
            "name": tool_name,
            "description": "Propose a patch in JSON format for CFG mutations.",
            "format": {"type": "text"}
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
        return _extract_tool_text(r, tool_name)

    # --- optional: JSON schema output (for Proposer patches) ---
    def emit_json(
        self,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any],
        *,
        schema_name: str = "grammar_patch",
    ) -> dict[str, Any]:
        """
        Send messages and require the model to output JSON that validates against `json_schema`.
        Uses the GPT-5 Responses API `text.format` pattern.
        Returns the parsed JSON object.
        """
        resp = self.client.responses.create(
            model=self.model,
            input=messages,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": json_schema,
                    "strict": True
                }
            }
        )

        # The SDK returns a list of output items; find the JSON
        for item in getattr(resp, "output", []):
            # In structured output, the schema-matching content is often in item["content"]
            if "content" in item and isinstance(item["content"], list):
                for part in item["content"]:
                    if "json" in part:
                        return part["json"]

        raise RuntimeError(f"Could not extract JSON from response: {resp}")


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


def _extract_tool_text(resp: Any, tool_name: str) -> str:
    """
    Extract text content from a custom tool response.
    Similar to _extract_tool_output but specifically for text format tools.
    """
    out = getattr(resp, "output", None)
    if not out:
        raise RuntimeError("No output found in response")

    # Look for custom tool call with the specified name
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

    raise RuntimeError(f"Could not extract text from tool {tool_name}")


def _extract_json(resp: Any) -> Any:
    """Pull JSON content from a responses API response."""
    out = getattr(resp, "output", None)
    if not out:
        return None

    # Look for text content that might contain JSON
    for item in out:
        if hasattr(item, 'type') and item.type == "message":
            if hasattr(item, 'content') and item.content:
                for content_item in item.content:
                    if hasattr(content_item, 'text'):
                        try:
                            # Try to parse the text as JSON
                            import json
                            return json.loads(content_item.text)
                        except json.JSONDecodeError:
                            continue
        elif hasattr(item, 'type') and item.type == "output_text":
            if hasattr(item, 'text'):
                try:
                    import json
                    return json.loads(item.text)
                except json.JSONDecodeError:
                    continue

    return None
