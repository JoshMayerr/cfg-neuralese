awesome—that’s a great flow. here’s a tight plan + the core hooks you need so you can (a) precompute a strong protocol offline, then (b) demo the process live, and (c) “use” the saved language for audience guessing.

# Demo plan (3 acts)

**Act 1 — Precomputation (offline, before the talk)**

- Run a longer optimization (many rounds) until you get a compact, accurate CFG.
- Save: final grammar, tiny few-shots, and a handful of “showcase scenes.”
- Keep a run log (CSV) + a short “storyboard” (v0 → mid → final messages for one scene).

**Act 2 — Live experiment (short)**

- Do 3–4 quick proposer rounds on stage with a fresh baseline grammar.
- Show logs updating (accuracy, avg length, chosen mutations).
- Stop early; this part is just to show the _process_, not reach the best code.

**Act 3 — Use the saved language**

- Load the precomputed CFG + few-shots.
- Run 3–4 Speaker→Listener rounds on random scenes.
- Let the audience guess the target from the cryptic message; reveal Listener’s correct pick.

---

# Artifacts you’ll save (offline run)

```
artifacts/
  best/
    grammar.lark               # final evolved grammar
    fewshots.json              # {speaker:[], listener:[]}
    showcase_scenes.json       # 5-10 scenes to reuse in demos (optional)
    storyboard.json            # v0/mid/final messages for one scene (optional)
  runs/
    run_YYYYMMDD_HHMM/
      round_log.csv            # per-round metrics + notes
      grammars/
        round_000.lark
        round_005.lark
        ...
```

---

# Core code you need (small, focused)

## 1) Artifact I/O helpers

```python
# src/artifacts/io.py
from pathlib import Path
import json, csv
from typing import Dict, Any, List

def save_text(path: str, text: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text)

def load_text(path: str) -> str:
    return Path(path).read_text()

def save_json(path: str, obj: Dict[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2))

def load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text())

def append_csv(path: str, row: Dict[str, Any], header: List[str]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    file_exists = Path(path).exists()
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        if not file_exists: w.writeheader()
        w.writerow(row)
```

## 2) Saving “best” from the offline run

Call this when your long run finishes (or whenever you detect a new best score):

```python
# src/artifacts/save_best.py
from .io import save_text, save_json
def save_best(grammar_text: str, speaker_fs, listener_fs, showcase_scenes=None):
    save_text("artifacts/best/grammar.lark", grammar_text)
    save_json("artifacts/best/fewshots.json", {"speaker": speaker_fs, "listener": listener_fs})
    if showcase_scenes is not None:
        save_json("artifacts/best/showcase_scenes.json", {"scenes": showcase_scenes})
```

## 3) Live mini-experiment loop (short & verbose)

Use your existing Phase-2 loop, but with a small number of rounds and chatty logging.

```python
# scripts/live_process.py (or in main with a --live flag)
from src.agents.proposer import propose
from src.grammar.mutations import apply_patch
from src.loop.evaluate import evaluate
from src.artifacts.io import append_csv, save_text
import time

def live_process(grammar_text: str, rounds=3, batch=50):
    log_header = ["round","accuracy","avg_len","productions","collisions","parse_fail","note"]
    for r in range(rounds):
        metrics, examples = evaluate(grammar_text, batch_size=batch, return_examples=True)
        print(f"[r{r}] acc={metrics['accuracy']:.3f} len={metrics['avg_msg_chars']:.2f} "
              f"prods={metrics['grammar_complexity']['productions']} coll={metrics['collisions']:.3f}")
        append_csv("artifacts/runs/live/round_log.csv", {
            "round": r,
            "accuracy": metrics["accuracy"],
            "avg_len": metrics["avg_msg_chars"],
            "productions": metrics["grammar_complexity"]["productions"],
            "collisions": metrics["collisions"],
            "parse_fail": metrics["parse_fail_rate"],
            "note": "live"
        }, header=log_header)

        patch = propose(grammar_text, metrics, examples[:5])
        grammar_candidate = apply_patch(grammar_text, patch)

        # quick guard
        smoke, _ = evaluate(grammar_candidate, batch_size=20, return_examples=False)
        if smoke["parse_fail_rate"] <= 0.05 and smoke["accuracy"] >= 0.90:
            grammar_text = grammar_candidate
            save_text(f"artifacts/runs/live/grammars/round_{r:03d}.lark", grammar_text)
        else:
            print("⛔ rejecting patch (guard failed)")
        time.sleep(0.2)  # keeps logs readable
    return grammar_text
```

## 4) “Use” the saved language (audience guessing)

Just load your precomputed assets and call Speaker→Listener a few times.

```python
# src/run/use_language.py
from src.artifacts.io import load_text, load_json
from src.agents.speaker import speak
from src.agents.listener import listen
from src.env.scenes import make_scene

def use_saved_language(n=3, k=4):
    g = load_text("artifacts/best/grammar.lark")
    fs = load_json("artifacts/best/fewshots.json")
    colors=["red","blue","green","yellow","black","white"]
    shapes=["circle","square","triangle","star","hexagon","diamond"]
    sizes=["small","medium","large","huge"]

    for i in range(n):
        scene = make_scene(colors, shapes, sizes, k=k)
        msg = speak(scene, g, fewshots=fs.get("speaker"))
        pred = listen(scene, msg, k=k, fewshots=fs.get("listener"))
        print(f"[use {i+1}] msg={repr(msg)} → guess={pred} {'✅' if pred==scene['target_idx'] else '❌'}")
```

---

# How you’ll run it on demo day

1. **(Already done offline)**

   - `artifacts/best/grammar.lark` and `artifacts/best/fewshots.json` exist.

2. **Act 2 — live process (short):**

```bash
uv run python -c "from scripts.live_process import live_process; import pathlib; g=pathlib.Path('src/grammar/base_grammar.lark').read_text(); live_process(g, rounds=3, batch=50)"
```

3. **Act 3 — use the saved language:**

```bash
uv run python -c "from src.run.use_language import use_saved_language; use_saved_language(n=3, k=4)"
```

(If you want CLI flags instead, wire these as subcommands in `main.py`, but the above is the minimal change.)

---

## One last tip

Keep **few-shots tiny (2–3)** and **final CFG stable**. Before the talk, run “use_saved_language” a few times to ensure outputs are consistent at your chosen temperatures (Speaker \~0.4–0.5, Listener \~0.2).

This gives you your exact ideal demo with minimal new code: show the _process_, then actually _use_ the evolved language.
