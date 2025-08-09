Nice progress. Here’s how we might do Phase 2 quickly.

# Immediate next steps (in order)

1. **Wire a real OpenAI client** using the **Responses API**.
2. **Add the CFG “custom tool”** to constrain outputs (Lark or regex).
3. **Use that tool in Speaker/Listener calls.**
4. **Add the Proposer** that returns a JSON patch.
5. **Implement the mutation engine** to apply patches.

# 1) OpenAI client (Responses API)

Key ideas:

- Use `client.responses.create(...)`.
- Attach a **custom tool** whose `format` is a CFG (Lark/regex).
- Read back tool outputs from `response.output` (tool calls).
  OpenAI’s GPT-5 docs & Cookbook show CFG via custom tools and Responses API. ([OpenAI][1], [OpenAI Platform][2], [OpenAI Cookbook][3])

Minimal skeleton (Python-ish):

```python
from openai import OpenAI
client = OpenAI()  # reads OPENAI_API_KEY

def run_with_tool(messages, grammar_text):
    tool = {
        "type": "custom",
        "name": "emit_message",
        "description": "Emit a string that matches the grammar start rule.",
        "format": {"type": "grammar", "syntax": "lark", "definition": grammar_text}
    }
    r = client.responses.create(
        model="gpt-5",
        input=messages,
        tools=[tool],
        tool_choice={"type":"tool", "name":"emit_message"},  # force tool
        temperature=0.5
    )
    # extract the tool's plaintext result
    for item in r.output:
        if item.get("type") == "tool_call" and item.get("name") == "emit_message":
            return item.get("output_text", "").strip()
    raise RuntimeError("No tool output")
```

Notes: naming/shape mirrors OpenAI’s “custom tool + grammar” design for GPT-5; keep your code tolerant to minor schema differences across SDK versions. ([OpenAI][1], [OpenAI Platform][2])

# 2) Speaker / Listener call patterns

**Speaker**

- System: load `prompts/speaker.txt`.
- User content: the scene (target + distractors) and a reminder to be _short_.
- Attach grammar tool.
- Force the tool (`tool_choice`) so the output must match the CFG. ([OpenAI Cookbook][3])

**Listener**

- System: load `prompts/listener.txt`.
- User content: scene + **speaker’s message**.
- Attach the _same_ grammar so the model can parse/interpret consistently.
- Constrain final output to a simple regex grammar for `^[0-3]$` to avoid chatter. (Use a tiny regex grammar tool for the final index.) ([OpenAI Platform][2])

# 3) CFG tool payloads you can drop in now

**Baseline (your current Lark)**

```
start: msg
msg: phrase (";" phrase)*
phrase: slot ":" value
slot: "color" | "shape" | "size"
value: /[a-z]+/
```

If you see drift, simplify the grammar (fewer alternations) and keep terminals bounded. Complex Lark features can be brittle; Cookbook + forum threads recommend iterative simplification. ([OpenAI Cookbook][3], [OpenAI Community][4])

**Listener index grammar (regex)**

```
start: /[0-3]/
```

Attach as a second custom tool named `emit_index` and `tool_choice` it for the listener’s final answer. ([OpenAI][1])

# 4) Proposer (JSON patch)

Have the Proposer return a **strict JSON** patch you validate against `patch_schema.json`. Keep the prompt short and show:

- Current grammar text
- Metrics JSON (accuracy, avg length, collisions, parse fails, complexity)
- 2–3 fail examples
  Ask it to _only_ return JSON with `mutations[]` and optional `speaker_fewshot[]`, `listener_fewshot[]`. (This aligns with cookbook guidance to be explicit about tool formats / outputs.) ([OpenAI Cookbook][3])

# 5) Mutation engine ops (first 5 to implement)

- `rename_terminal(from,to)`
- `remove_separators()`
- `restrict_terminal(name, pattern)` (e.g., `[a-z0-9]`)
- `replace_rule(lhs,rhs)` (e.g., `msg -> C S Z`)
- `fix_length(symbol,n)` (for positional/fixed-width codes)

Validate after each patch: rebuild the tool with the new grammar; run a tiny smoke batch and ensure parse-fail < 5%.

# 6) Acceptance checks for “Phase 2 done”

- Baseline with **real calls** hits ≥ 97% accuracy on your readable grammar.
- Speaker/Listener both return via tool outputs (no free-text drift).
- One round of **manual** patch (e.g., drop separators) reduces avg length with accuracy ≥ 95%.
- Proposer returns a valid patch that your engine applies; the eval runs end-to-end.

# 7) Gotchas (save time)

- **Over-complex grammars** → higher latency & occasional non-conformance. Prefer small, LL-ish grammars; avoid lookarounds/greedy regex. ([OpenAI Cookbook][3], [OpenAI Platform][5])
- **Forcing tool use** → set `tool_choice` to your grammar tool; otherwise the model might answer in plain text. ([OpenAI][1])
- **Short outputs** → lower `temperature` and keep few-shots minimal but _matching_ the grammar exactly. ([OpenAI Cookbook][6])
- **SDK churn** → rely on the **official API docs / cookbook** for parameter names as they evolve. ([OpenAI Platform][7], [OpenAI Cookbook][3])

If you want, I can draft the concrete code for:

- `openai_client.py::run_with_tool`
- `speaker.py::speak`
- `listener.py::listen`
  so you can paste and run a real batch tonight.

[1]: https://openai.com/index/introducing-gpt-5-for-developers/?utm_source=chatgpt.com "Introducing GPT‑5 for developers - OpenAI"
[2]: https://platform.openai.com/docs/guides/latest-model?utm_source=chatgpt.com "Using GPT-5 - OpenAI API"
[3]: https://cookbook.openai.com/examples/gpt-5/gpt-5_new_params_and_tools?utm_source=chatgpt.com "GPT-5 New Params and Tools - OpenAI Cookbook"
[4]: https://community.openai.com/t/gpt-5-custom-lark-tool-outputs-are-not-guaranteed-to-conform-to-the-cfg/1337673?utm_source=chatgpt.com "Custom Lark tool outputs are not guaranteed to conform to the CFG?"
[5]: https://platform.openai.com/docs/guides/function-calling?utm_source=chatgpt.com "Function calling - OpenAI API"
[6]: https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide?utm_source=chatgpt.com "GPT-5 prompting guide - OpenAI Cookbook"
[7]: https://platform.openai.com/docs/api-reference/introduction?utm_source=chatgpt.com "API Reference - OpenAI Platform"
