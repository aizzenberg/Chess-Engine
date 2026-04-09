from typing import Optional

from engines.materialist import MaterialistEngine
from engines.positionalist import PositionalistEngine


def get_engine(id: str, depth: int, **kwargs):
    engines = {
        'gen1': MaterialistEngine,
        'gen2': PositionalistEngine
    }

    selected_engine = engines.get(id)
    if not selected_engine:
        raise ValueError(f"Engine '{id}' not found")

    return selected_engine(depth, **kwargs)
