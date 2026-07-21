from core.minimax_engine import MinimaxEngine
from core.move_picker import MovePicker
from evaluators.materialist import MaterialEvaluator
from evaluators.positionalist import PositionalEvaluator


def get_engine(engine_id: str, depth: int):
    engines = {
        'gen1': MinimaxEngine(evaluator=MaterialEvaluator(), move_picker=MovePicker(), depth=depth, name="Beansie"),
        'gen2': MinimaxEngine(evaluator=PositionalEvaluator(), move_picker=MovePicker(), depth=depth, name="Tuko"),
        'gen2.1': MinimaxEngine(evaluator=PositionalEvaluator(count_mobility=True), move_picker=MovePicker(), depth=depth, name="Tuko-coco"),
        'gen1': MinimaxEngine(evaluator=MaterialEvaluator(), move_picker=MovePicker(depth), depth=depth, name="Beansie"),
        'gen2': MinimaxEngine(evaluator=PositionalEvaluator(), move_picker=MovePicker(depth), depth=depth, name="Tuko"),
        'gen2.1': MinimaxEngine(evaluator=PositionalEvaluator(count_mobility=True), move_picker=MovePicker(depth), depth=depth, name="Tuko-coco"),
    }

    selected_engine = engines.get(engine_id)
    if not selected_engine:
        raise ValueError(f"Engine '{engine_id}' not found")

    return selected_engine
