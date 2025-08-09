from typing import Dict, List, TypedDict, Any

SceneObj = Dict[str, str]

class Scene(TypedDict):
    target_idx: int
    objects: List[SceneObj]

Metrics = Dict[str, Any]
