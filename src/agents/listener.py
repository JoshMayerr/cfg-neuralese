from typing import Dict, List, Optional
from .openai_client import OpenAIClient

# Inline prompt - no external file dependency
LISTENER_PROMPT = """You are the LISTENER. Given a legal message (per the attached grammar) and the list of objects, determine which object the SPEAKER intended. Output only the zero-based index of the target.

Output only the zero-based index digit."""

def _fewshot_blocks_listener(items: Optional[List[Dict]]) -> List[Dict[str,str]]:
    if not items: return []
    blocks = []
    for ex in items:
        blocks.append({"role":"user","content": f"Message: {ex['message']}\nOutput only the index."})
        blocks.append({"role":"assistant","content": str(ex["answer"])})
    return blocks

def listen(scene: Dict, message: str, k: int, *, fewshots: Optional[List[Dict]]=None, temperature: float=0.2) -> int:
    client = OpenAIClient()
    objs = [f"{i}: color={o['color']}, shape={o['shape']}, size={o['size']}" for i,o in enumerate(scene["objects"])]
    messages = [
        {"role":"system", "content": LISTENER_PROMPT},
        *_fewshot_blocks_listener(fewshots),
        {"role":"user","content": "Objects:\n" + "\n".join(objs) + f"\nMessage: " + message + "\nOutput only the zero-based index."}
    ]
    return client.emit_index(messages, k=k, temperature=temperature)
