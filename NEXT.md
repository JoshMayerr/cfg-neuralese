# What to do next (in order)

1. **Swap in real model calls**

- Use the tiny client we wrote:

  - Speaker → `emit_with_grammar(..., grammar_text, syntax="lark")`
  - Listener → `emit_index(..., k=4)` (regex CFG so it returns just `0–3`)

- Target: `N=100` → **≥97% accuracy**, parse-fail <1%.

2. **Add the first two mutations (manual to start)**

- `rename_terminal(color→c, shape→s, size→z)`
- `remove_separators()` (drop `:`, `;`)
- Expect: shorter messages (aim ≤ 10–12 chars), **accuracy ≥95%**.

3. **Wire the Proposer**

- Input: `{ grammar_text, metrics, 3–5 examples }`
- Output (strict JSON): `{"mutations":[...], "speaker_fewshot":[...], "listener_fewshot":[...]}`
- Validate JSON, apply, re-eval.

4. **Top-K loop (small)**

- Keep **K=3** parents, **M=2** children each → 6 evals/round.
- Score: `Acc − 0.02·AvgLen − (0.5·prods + 0.1·avgRHS) − 5.0·Collisions`
- Guards: accuracy floor 95%, parse-fail ≤5%, length ≤32, entropy floor.

# Drop-in call shapes

**Speaker**

```python
msg = client.emit_with_grammar(
    messages=[
      {"role":"system", "content": open("prompts/speaker.txt").read()},
      {"role":"user", "content": scene_text}  # your formatted scene + target idx
    ],
    grammar_text=open("src/grammar/base_grammar.lark").read(),
    syntax="lark",
    temperature=0.5,
)
```

**Listener (index only)**

```python
pred = client.emit_index(
    messages=[
      {"role":"system", "content": open("prompts/listener.txt").read()},
      {"role":"user", "content": scene_plus_message_text}
    ],
    k=4, temperature=0.2
)
```

# Quick acceptance checks

- **Baseline (real calls):** N=100 → Acc ≥0.97; AvgLen \~15–30 chars.
- **After manual 2-mutation patch:** Acc ≥0.95; AvgLen ≤12 chars; collisions \~0.
- **Proposer on (3 rounds):** AvgLen continues dropping; parse-fail \~0.

# First target mutation (phase change)

Ask the Proposer to try:

- `replace_rule(msg -> C S Z)`
- `restrict_terminal(C:[a-f], S:[a-f], Z:[a-d])`
  This usually triggers the big drop (toward 3–6 char codes).

# Minimal logs per round

```
round, acc, avg_len, prods, avg_rhs, collisions, parse_fail, score
```
