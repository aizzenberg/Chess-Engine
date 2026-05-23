from core.minimax_engine import MinimaxEngine
from core.move_picker import MovePicker
from evaluators.materialist import MaterialistEvaluator
from evaluators.positionalist import PositionalistEvaluator


def get_engine(engine_id: str, depth: int):
    engines = {
        'gen1': MinimaxEngine(evaluator=MaterialistEvaluator(), move_picker=MovePicker(), depth=depth, name="Beansie"),
        'gen2': MinimaxEngine(evaluator=PositionalistEvaluator(), move_picker=MovePicker(), depth=depth, name="Tuko"),
    }

    selected_engine = engines.get(engine_id)
    if not selected_engine:
        raise ValueError(f"Engine '{engine_id}' not found")

    return selected_engine
