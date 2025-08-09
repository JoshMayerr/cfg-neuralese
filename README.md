# Project Overview: CFG-Evolving “Neuralese” Game (GPT-5, no finetuning)

## Objectives

- Evolve a **context-free grammar (CFG)** so GPT-5 (Speaker/Listener) communicates **shorter, legal** messages while keeping **high accuracy** (target ≥ 97% on held-out).
- Let GPT-5 (Proposer) **self-optimize** the protocol by proposing grammar patches + few-shots each round.
- Deliver a **small demo** showing before/after messages for the same scene and a **plot of Accuracy vs Length**.

---

# System Architecture (at a glance)

**Roles**

- **Speaker**: sees target + distractors → emits **message** under CFG.
- **Listener**: sees distractors + message → outputs **target index**.
- **Proposer**: sees **metrics + a few examples + current CFG** → returns **grammar patch + few-shots**.

**Loop**

1. Generate a batch of scenes
2. Speaker → messages (CFG-constrained)
3. Listener → guesses
4. Score → accuracy, length, complexity, collisions, parse-fails, robustness
5. Proposer → JSON patch (mutations + new few-shots)
6. Validate/apply patch → next round (optionally keep **Top-K** best grammars)

---

# Data Flow

**Input**: `Scene = { target_idx, objects: [{color, shape, size}, …] }`
**Speaker out**: `message: str` (must match CFG `start`)
**Listener out**: `pred_idx: int`
**Evaluator out**: `metrics: {accuracy, avg_msg_chars, collisions, parse_fail_rate, grammar_complexity, robustness?}`
**Proposer in**: `{grammar, metrics, examples}` → **Proposer out**: `patch: {mutations[], speaker_fewshot[], listener_fewshot[]}`

---

# Repo Layout

```
cfg-neuralese/
├─ README.md
├─ plan.md
├─ tasks.md
├─ pyproject.toml
├─ .env.example
├─ configs/
│  └─ defaults.yaml
├─ prompts/
│  ├─ speaker.txt
│  ├─ listener.txt
│  └─ proposer.txt
├─ src/
│  ├─ main.py
│  ├─ types.py
│  ├─ env/
│  │  ├─ scenes.py         # scene generator (K, vocab)
│  │  └─ scoring.py        # accuracy, length, collisions, robustness
│  ├─ grammar/
│  │  ├─ base_grammar.lark # human-readable starter
│  │  ├─ mutations.py      # apply ops to grammar text
│  │  ├─ patch_schema.json # JSON schema for proposer patches
│  │  └─ utils.py          # complexity counters, validators
│  ├─ agents/
│  │  ├─ openai_client.py  # single place to call GPT-5
│  │  ├─ speaker.py
│  │  ├─ listener.py
│  │  └─ proposer.py
│  ├─ loop/
│  │  ├─ evaluate.py       # run N scenes → metrics
│  │  ├─ search.py         # Top-K evolutionary loop
│  │  └─ guards.py         # parse-fail gate, diversity floor
│  └─ dashboards/
│     └─ plots.py          # Accuracy vs Length, etc.
├─ tests/
│  ├─ test_scenes.py
│  ├─ test_mutations.py
│  └─ test_evaluate.py
└─ scripts/
   ├─ run_round.py
   └─ quick_demo.py
```

---

# Core Components & Responsibilities

## 1) Scene Generator (`src/env/scenes.py`)

- **Inputs**: vocab sizes from `configs/defaults.yaml`
- **Outputs**: batch of scenes with 1 target + (K-1) distractors (no duplicates)
- Start with 3 attrs: `color×6, shape×6, size×4`, K=4

## 2) Baseline CFG (`src/grammar/base_grammar.lark`)

Human-readable to stabilize early behavior:

```
start: msg
msg: phrase (";" phrase)*
phrase: slot ":" value
slot: "color" | "shape" | "size"
value: /[a-z]+/
```

## 3) Speaker (`src/agents/speaker.py`)

- Prompt: “Emit the **shortest** legal message under the attached grammar that lets a competent listener uniquely identify the target.”
- Uses GPT-5 with the CFG tool → returns `message` (must match `start`)

## 4) Listener (`src/agents/listener.py`)

- Prompt: “Given the legal message and objects, **parse under the grammar** and output only the target’s index.”
- Uses same CFG tool → returns `pred_idx`

## 5) Evaluator (`src/loop/evaluate.py`)

- Runs Speaker/Listener on N scenes
- Computes metrics:

  - **accuracy** = correct / N
  - **avg_msg_chars**
  - **grammar_complexity** (productions, avg RHS length, terminal set sizes)
  - **collisions** (same msg for different scenes)
  - **parse_fail_rate**
  - **robust_accuracy** (optional, apply noise flips)

## 6) Proposer (`src/agents/proposer.py`)

- Input: serialized grammar text, metrics JSON, \~5 example successes/failures
- Output: **strict JSON** patch: `mutations[]`, optional `speaker_fewshot[]`, `listener_fewshot[]`
- You validate JSON against `patch_schema.json`

## 7) Mutation Engine (`src/grammar/mutations.py`)

Supported MVP ops:

- `rename_terminal(from,to)`
- `restrict_terminal(name, pattern)` (e.g., `[a-z0-9]`)
- `remove_separators()`
- `replace_rule(lhs, rhs)` (e.g., `msg -> C S Z`)
- `add_rule(lhs, rhs)` / `drop_rule(lhs)`
- `fix_length(symbol, n)` (enforce fixed-width)
- `map_vocab(slot, mapping)` (attribute → codebook)
- `add_checksum(mod_base)` (optional robustness)

## 8) Search Loop (`src/loop/search.py`)

- Keep **Top-K** grammars (K=5).
- For each parent, request M=2 proposer patches → evaluate children → keep best K by score.
- Score function:

  ```
  Score = Acc
          − λ1·AvgLen
          − λ2·Complexity
          − λ5·Collisions
          + λ3·(RobustAcc − Acc)
          − λ4·Latency   # optional
  ```

- Defaults: λ1=0.02/char; λ2=0.5/prod + 0.1/RHS; λ3=0.5; λ5=5.0

## 9) Guards (`src/loop/guards.py`)

- Reject if `parse_fail_rate > 5%`
- Diversity floor: entropy(messages) ≥ ε (prevents 1-string collapse)
- Hard caps: `max productions=40`, `max depth=8`, `max msg length=32`

## 10) Dashboard (`src/dashboards/plots.py`)

- Accuracy vs Avg Length (rounds)
- Robustness vs Length (if enabled)
- Show **v0 / mid / final** messages for the **same scene**

---

# Prompts (short & effective)

**Speaker**

> You are the SPEAKER. Given a target and distractors, emit the **shortest legal message** under the attached grammar that uniquely identifies the target. Output only the string that matches the grammar’s start rule.

**Listener**

> You are the LISTENER. Given a **legal message** and the objects, **parse per the grammar** and output only the zero-based **target index**.

**Proposer**

> You are the PROPOSER. You will receive the **current grammar**, **metrics**, and several **success/failure examples**. Return a **JSON patch** proposing **grammar mutations** (and optional few-shots) to **reduce average message length** while keeping **accuracy ≥ 95%**, avoiding parse failures and collisions. Return only JSON with keys: `mutations[]`, `speaker_fewshot[]`, `listener_fewshot[]`.

---

# Configuration (`configs/defaults.yaml`) — Suggested Defaults

- `model: gpt-5`
- `batch_size (N): 100`
- `k_objects: 4`
- `attributes: color[6], shape[6], size[4]`
- `lambdas: len_per_char=0.02; complexity_per_prod=0.5; complexity_per_rhs_symbol=0.1; robust_factor=0.5; collisions=5.0`
- `guards: min_accuracy=0.95; max_parse_fail=0.05; max_productions=40; max_depth=8; max_msg_chars=32; min_entropy_bits=2.0`

---

# Implementation Overview (how to build it)

## Phase 1 — MVP (baseline loop)

1. **Scene generator** + **baseline grammar**
2. **Speaker/Listener** single calls using CFG tool
3. **Evaluator** over N scenes → print metrics
4. CLI `main.py` runs one evaluation

**Exit criteria**: Accuracy > 97%, readable messages, metrics logging stable.

## Phase 2 — Self-optimization

1. Add **Proposer** + **patch schema**
2. Implement **mutation engine** + validators
3. Implement **Top-K** search loop (parents→children)
4. Run 10–20 rounds; verify **Accuracy vs Length** curve

**Exit criteria**: Messages shrink (e.g., 30→10 chars) with accuracy ≥ 95%.

## Phase 3 — Compression & robustness

1. Enable **positional grammar** (`msg -> C S Z`) / **fixed length**
2. Add **noise injection** & **checksum op**
3. Plot **Robustness vs Length**

**Exit criteria**: Observe **phase change** (big length drop), checksum recovers noisy accuracy.

## Phase 4 — Demo polish

- Multi-seed runs (different starting grammars)
- Show v0/mid/final messages for the same scene
- Clean README + quick `scripts/quick_demo.py`

---

# Risks & Mitigations

- **Degenerate one-string messages** → diversity floor + collision penalty.
- **Ambiguous/broken grammars** → parse-fail gate and patch validator.
- **Latency/cost** → small N (100), compact grammars, limit alternations.
- **Overfitting prompts** → rotate few-shots; hold-out test split every few rounds.

---
