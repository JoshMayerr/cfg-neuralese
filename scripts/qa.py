#!/usr/bin/env python3
# scripts/fallback_act3_demo.py
"""
Fallback Act 3 Demo (no API needed)

Flow per round:
1) Show a scene (K objects).
2) Simulate Speaker call (spinner) → cryptic message.
3) Audience/user guesses the index.
4) Simulate Listener call (spinner) → correct guess.
"""

from __future__ import annotations
import argparse, random, sys, time
from typing import Dict, List, Tuple

# --- simple vocab ---
COLORS  = ["red","blue","green","yellow","black","white","purple","orange"]
SHAPES  = ["circle","square","triangle","star","hexagon","diamond"]
SIZES   = ["small","medium","large","huge"]

# --- secret alphabets (cryptic) ---
ALPHA_C = list("qwrtypsdfghjklzxcvbn")     # consonants for color
ALPHA_S = list("2468abcdfgh")              # digits+letters for shape
ALPHA_Z = list("mnpqrstuvwxyz01345")       # size-ish

# ---------------- UI niceties (fake API latency) ----------------

SPINNER_FRAMES = "|/-\\"

def _spinner(label: str, duration_ms: int, tick_ms: int = 80):
    """Tiny spinner to simulate an API call."""
    sys.stdout.write(label)
    sys.stdout.flush()
    elapsed = 0
    i = 0
    while elapsed < duration_ms:
        sys.stdout.write(" " + SPINNER_FRAMES[i % len(SPINNER_FRAMES)] + "\r")
        sys.stdout.flush()
        time.sleep(tick_ms / 1000.0)
        elapsed += tick_ms
        i += 1
        # reprint label each tick so it doesn't get erased
        sys.stdout.write(label)
        sys.stdout.flush()
    # finish line
    sys.stdout.write(label + " ✓\n")
    sys.stdout.flush()

def faux_call(label: str, base_ms: int, jitter_ms: int):
    """Simulate a call with small jitter."""
    if base_ms <= 0:
        print(label + " ✓")
        return
    rnd = random.Random()
    duration = max(0, int(rnd.uniform(base_ms - jitter_ms, base_ms + jitter_ms)))
    _spinner(label, duration)

# ---------------- core logic ----------------

def make_scene(k: int, seed: int | None = None) -> Dict:
    rnd = random.Random(seed)
    objs = set()
    def sample_obj():
        return (rnd.choice(COLORS), rnd.choice(SHAPES), rnd.choice(SIZES))
    while len(objs) < k:
        objs.add(sample_obj())
    obj_list = [{"color": c, "shape": s, "size": z} for (c, s, z) in objs]
    target_idx = rnd.randrange(k)
    return {"target_idx": target_idx, "objects": obj_list}

def build_secret_code(seed: int) -> Tuple[Dict[str,str], Dict[str,str], Dict[str,str]]:
    rnd = random.Random(seed)
    rnd.shuffle(ALPHA_C); rnd.shuffle(ALPHA_S); rnd.shuffle(ALPHA_Z)
    cmap = {c: ALPHA_C[i % len(ALPHA_C)] for i, c in enumerate(sorted(set(COLORS)))}
    smap = {s: ALPHA_S[i % len(ALPHA_S)] for i, s in enumerate(sorted(set(SHAPES)))}
    zmap = {z: ALPHA_Z[i % len(ALPHA_Z)] for i, z in enumerate(sorted(set(SIZES)))}
    return cmap, smap, zmap

def encode(obj: Dict[str,str], cmap: Dict[str,str], smap: Dict[str,str], zmap: Dict[str,str]) -> str:
    # Fixed-width “neuralese”: C S Z
    return f"{cmap[obj['color']]}{smap[obj['shape']]}{zmap[obj['size']]}"

def decode_find_index(scene: Dict, msg: str, cmap, smap, zmap) -> int:
    # Agent “decodes” by re-encoding each object and matching
    codes = [encode(o, cmap, smap, zmap) for o in scene["objects"]]
    matches = [i for i, c in enumerate(codes) if c == msg]
    if len(matches) == 1:
        return matches[0]
    return scene["target_idx"]

def print_scene(scene: Dict):
    print("Scene:")
    for i, o in enumerate(scene["objects"]):
        print(f"  {i}: color={o['color']}, shape={o['shape']}, size={o['size']}")

def prompt_guess(k: int) -> int | None:
    try:
        s = input(f"Your guess (0-{k-1}, or ENTER to skip): ").strip()
        if s == "": return None
        g = int(s)
        if 0 <= g < k: return g
    except Exception:
        pass
    print("  (invalid input — skipping)")
    return None

def main():
    ap = argparse.ArgumentParser(description="Fallback Act 3 Demo (no API).")
    ap.add_argument("--rounds", type=int, default=3, help="how many examples to play")
    ap.add_argument("--k", type=int, default=4, help="objects per scene")
    ap.add_argument("--seed", type=int, default=7, help="base seed (controls code + scenes)")
    ap.add_argument("--speaker-latency", type=int, default=600, help="ms to simulate Speaker API call (±20%)")
    ap.add_argument("--listener-latency", type=int, default=500, help="ms to simulate Listener API call (±20%)")
    ap.add_argument("--no-latency", action="store_true", help="disable simulated API latency")
    args = ap.parse_args()

    rnd = random.Random(args.seed)
    cmap, smap, zmap = build_secret_code(args.seed)

    print("🎬 Fallback Act 3 — Audience vs Agent")
    print("   (cryptic message uses a fixed hidden code for this session)\n")

    user_correct = 0
    for r in range(1, args.rounds + 1):
        scene = make_scene(args.k, seed=rnd.randrange(1_000_000))
        print(f"\n—— Example {r} ——")
        print_scene(scene)

        # Simulate Speaker API call
        if args.no_latency:
            print("Speaker generating message... ✓")
        else:
            faux_call("Speaker generating message...", args.speaker_latency, jitter_ms=int(args.speaker_latency*0.2))
        msg = encode(scene["objects"][scene["target_idx"]], cmap, smap, zmap)
        print(f"Speaker’s message: {msg!r}")

        # Audience guess
        g = prompt_guess(args.k)

        # Simulate Listener API call
        if args.no_latency:
            print("Listener decoding message... ✓")
        else:
            faux_call("Listener decoding message...", args.listener_latency, jitter_ms=int(args.listener_latency*0.2))
        agent_pred = decode_find_index(scene, msg, cmap, smap, zmap)

        result = "✅" if agent_pred == scene["target_idx"] else "❌"
        print(f"Agent guess → {agent_pred} {result}")
        print(f"Actual target index: {scene['target_idx']}")
        if g is not None:
            you = "✅" if g == scene["target_idx"] else "❌"
            if you == "✅": user_correct += 1
            print(f"Your guess → {g} {you}")

    print("\n—— Summary ——")
    print(f"You got {user_correct}/{args.rounds} correct.")
    print("The agent was correct every time (it knows the hidden code).")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
