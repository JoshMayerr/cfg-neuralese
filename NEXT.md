At this point, moving to the **Proposer** will:

- Let the model start making those `rename_terminal` and `remove_separators` changes itself.
- Start testing JSON patch generation + mutation application.
- Show whether it can chain safe optimizations without human intervention.

If we go straight to the Proposer now, I’d recommend:

### Proposer MVP scope

- **Inputs:**

  - Current grammar text
  - Metrics from last eval
  - 3–5 example (scene, message, pred, correct?)

- **Output:**

  - JSON patch with `mutations[]` (from the 3–4 safe ops you already have working)
  - Optional few-shot examples for Speaker/Listener

- **Ops to support in the first run:**

  - `rename_terminal`
  - `remove_separators`
  - `restrict_terminal`
  - `replace_rule`

- Keep the schema strict so you can `json.loads` it without cleanup.

### Immediate plan

1. Write `proposer.py::propose(grammar, metrics, examples) -> patch_dict` using your OpenAI client’s `emit_json`.
2. In `mutations.py`, make sure those 3–4 ops are implemented.
3. Write a `proposer_test.py` that:

   - Feeds it a frozen grammar + fake metrics
   - Confirms it outputs valid JSON that passes your patch validator

4. Hook the proposer call into your eval loop for a 1-round “model-suggested mutation” run.

Once that works, you can decide whether to plug it straight into a Top-K loop or do a few single-parent → single-child rounds to watch the behavior.
