# plan.md

## Goal

Evolve a CFG so GPT-5 (Speaker/Listener) communicates shorter legal messages without dropping below \~97% accuracy on held-out scenes, with GPT-5 (Proposer) proposing most rule changes.

## Loop

1. Generate batch of scenes (K=4 objects; attrs: color, shape, size).
2. Speaker (CFG-constrained) emits message.
3. Listener (CFG-constrained) picks target.
4. Compute metrics: accuracy, avg length, complexity, collisions, parse-fail, (later) robustness.
5. Proposer receives {grammar, metrics, examples} → returns JSON patch (mutations + few-shots).
6. Validate/apply patch; iterate with Top-K search.

## Initial Settings

- K=4; attrs: color×6, shape×6, size×4 (uniform).
- N=100 scenes/eval; fixed 1k held-out for periodic tests.
- Score = Acc − λ1·Len − λ2·Complexity + λ3·Robust − λ5·Collisions
  Defaults: λ1=0.02/char; λ2=0.5/prod + 0.1/RHS; λ3=0.5·(RobustAcc−Acc); λ5=5.0.

## Guards

- Accuracy floor 95% (reject).
- Parse-fail ≤ 5%.
- Diversity floor (message entropy ≥ ε).
- Max productions 40; max depth 8; max msg length 32.

## Phases

- **P1 (MVP)**: env + baseline grammar + eval loop (manual patches OK).
- **P2**: Proposer + JSON patch schema + Top-K search.
- **P3**: Fixed-length codes + noise + optional checksum mutation.
- **P4**: Multi-seed runs; plots/dashboards; 60-sec demo.

## Deliverables

- Plot: Accuracy vs Avg length over rounds.
- Table: v0 / mid / final messages for the same scene.
- Grammar diffs (before/after).
- README with “how to run”.

### starter contents

**configs/defaults.yaml**

```yaml
model: gpt-5
batch_size: 100
k_objects: 4
attributes:
  color: [red, blue, green, yellow, black, white]
  shape: [circle, square, triangle, star, hexagon, diamond]
  size: [small, medium, large, huge]
lambdas:
  len_per_char: 0.02
  complexity_per_prod: 0.5
  complexity_per_rhs_symbol: 0.1
  collisions: 5.0
  robust_factor: 0.5
guards:
  min_accuracy: 0.95
  max_parse_fail: 0.05
  max_productions: 40
  max_depth: 8
  max_msg_chars: 32
  min_entropy_bits: 2.0
```

**grammar/base_grammar.lark**

```
start: msg
msg: phrase (";" phrase)*
phrase: slot ":" value
slot: "color" | "shape" | "size"
value: /[a-z]+/
```

**prompts/speaker.txt**

```
You are the SPEAKER. Given a target object and distractors, emit the SHORTEST legal message under the attached grammar that lets a competent LISTENER uniquely identify the target. Output only the string that matches the grammar's start rule.
```

**prompts/listener.txt**

```
You are the LISTENER. Given a legal message (per the attached grammar) and the list of objects, determine which object the SPEAKER intended. Output only the zero-based index of the target.
```

**prompts/proposer.txt**

```
You are the PROPOSER. You will receive: (1) current grammar, (2) last metrics, (3) a few success/failure examples. Propose a JSON patch to the grammar to reduce average message length without allowing accuracy to drop below 95%, while avoiding parse failures and collisions. Return keys: mutations[], speaker_fewshot[], listener_fewshot[].
```

**.env.example**

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5
```

**src/types.py**

```python
from typing import Dict, List, TypedDict, Any

SceneObj = Dict[str, str]
class Scene(TypedDict):
    target_idx: int
    objects: List[SceneObj]

Metrics = Dict[str, Any]
```

**src/env/scenes.py**

```python
import random
from typing import List
from ..types import Scene, SceneObj

def make_scene(colors, shapes, sizes, k=4) -> Scene:
    # sample unique objects
    objs = set()
    def sample_obj():
        return (random.choice(colors), random.choice(shapes), random.choice(sizes))
    while len(objs) < k:
        objs.add(sample_obj())
    obj_list: List[SceneObj] = [{"color": c, "shape": s, "size": z} for (c,s,z) in objs]
    target_idx = random.randrange(k)
    return {"target_idx": target_idx, "objects": obj_list}
```

**src/env/scoring.py**

```python
def avg_len(messages):
    return sum(len(m) for m in messages) / max(1, len(messages))

def score_fn(acc, avg_chars, complexity, collisions, robust=None, lambdas=None):
    l = lambdas or {}
    s = acc - l.get("len_per_char",0.02)*avg_chars \
           - l.get("complexity_per_prod",0.5)*complexity.get("productions",0) \
           - l.get("complexity_per_rhs_symbol",0.1)*complexity.get("avg_rhs_symbols",0) \
           - l.get("collisions",5.0)*collisions
    if robust is not None:
        s += l.get("robust_factor",0.5)*(robust - acc)
    return s
```

**src/grammar/patch_schema.json**

```json
{
  "type": "object",
  "required": ["mutations"],
  "properties": {
    "mutations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["op"],
        "properties": {
          "op": { "type": "string" },
          "lhs": { "type": "string" },
          "rhs": { "type": "string" },
          "from": { "type": "string" },
          "to": { "type": "string" },
          "name": { "type": "string" },
          "pattern": { "type": "string" },
          "mapping": { "type": "object" }
        }
      }
    },
    "speaker_fewshot": { "type": "array" },
    "listener_fewshot": { "type": "array" }
  }
}
```

**src/agents/openai_client.py**

```python
import os

MODEL = os.getenv("OPENAI_MODEL","gpt-5")

def call_model(messages, tools=None):
    # placeholder: wire to OpenAI SDK in your env
    # return model response; ensure tool with grammar is attached when needed
    raise NotImplementedError
```

**src/loop/evaluate.py**

```python
from typing import Dict, List
from ..types import Scene
from ..env.scoring import avg_len

def evaluate(grammar:str, scenes:List[Scene]) -> Dict:
    # TODO: call speaker/listener via agents; collect messages/preds
    messages = []
    correct = 0
    collisions = 0
    parse_fail = 0
    # ...
    acc = correct / max(1, len(scenes))
    return {
        "accuracy": acc,
        "avg_msg_chars": avg_len(messages),
        "collisions": collisions/ max(1,len(scenes)),
        "parse_fail_rate": parse_fail/ max(1,len(scenes)),
        "grammar_complexity": {"productions": 0, "avg_rhs_symbols": 0},
        "examples": []
    }
```

**src/grammar/base_grammar.lark** (duplicate here for convenience)

```
start: msg
msg: phrase (";" phrase)*
phrase: slot ":" value
slot: "color" | "shape" | "size"
value: /[a-z]+/
```

---

want me to generate stub implementations for `speaker.py`, `listener.py`, and a minimal `main.py` that runs one evaluation with the baseline grammar?
