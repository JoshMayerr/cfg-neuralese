from typing import Dict, List, Optional
from .openai_client import OpenAIClient

# Inline prompt - no external file dependency
SPEAKER_PROMPT = """You are the SPEAKER. Given a target object and distractors, emit the SHORTEST legal message under the attached grammar that lets a competent LISTENER uniquely identify the target. Output only the string that matches the grammar's start rule.

Use only terminals allowed by the grammar. Do not emit English words or slot names unless present in the grammar."""

def _fewshot_blocks_speaker(items: Optional[List[Dict]]) -> List[Dict[str,str]]:
    if not items: return []
    blocks = []
    for ex in items:
        # The fewshots data has scene nested under "scene" key
        scene_data = ex["scene"]
        objects_desc = []
        for i, obj in enumerate(scene_data["objects"]):
            objects_desc.append(f"{i}: color={obj['color']}, shape={obj['shape']}, size={obj['size']}")

        scene_text = "\n".join(objects_desc)
        blocks.append({"role":"user","content": f"Objects:\n{scene_text}\nTarget index: {scene_data['target_idx']}\nOutput only the message."})
        blocks.append({"role":"assistant","content": ex["message"]})
    return blocks

def speak(scene: Dict, grammar_text: str, *, fewshots: Optional[List[Dict]]=None, temperature: float=0.4) -> str:
    client = OpenAIClient()
    objs = [f"{i}: color={o['color']}, shape={o['shape']}, size={o['size']}" for i,o in enumerate(scene["objects"])]
    target = scene["target_idx"]
    messages = [
        {"role":"system", "content": SPEAKER_PROMPT},
        * _fewshot_blocks_speaker(fewshots),
        {"role":"user","content": "Objects:\n" + "\n".join(objs) + f"\nTarget index: {target}\nOutput only the message."}
    ]
    return client.emit_with_grammar(messages, grammar_text, syntax="lark", temperature=temperature)
