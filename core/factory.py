from engines.materialist import MaterialistEngine


def get_engine(id: str, depth: int, name: str = None):
    engines = {
        'gen1': MaterialistEngine
    }

    selected_engine = engines.get(id)
    if not selected_engine:
        raise ValueError(f"Engine '{id}' not found")

    return selected_engine(depth, name)
