import random
from typing import List
from ..types import Scene, SceneObj

def make_scene(colors: List[str], shapes: List[str], sizes: List[str], k: int = 4) -> Scene:
    """Generate a scene with k unique objects and a random target."""
    # Sample unique objects
    objs = set()

    def sample_obj():
        return (random.choice(colors), random.choice(shapes), random.choice(sizes))

    # Keep sampling until we have k unique objects
    while len(objs) < k:
        objs.add(sample_obj())

    # Convert to list of dicts
    obj_list: List[SceneObj] = [
        {"color": c, "shape": s, "size": z}
        for (c, s, z) in objs
    ]

    # Pick random target
    target_idx = random.randrange(k)

    return {"target_idx": target_idx, "objects": obj_list}

def make_batch(colors: List[str], shapes: List[str], sizes: List[str],
               batch_size: int, k: int = 4) -> List[Scene]:
    """Generate a batch of unique scenes."""
    return [make_scene(colors, shapes, sizes, k) for _ in range(batch_size)]
