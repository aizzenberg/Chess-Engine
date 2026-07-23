from core.minimax_engine import MinimaxEngine
from core.move_picker import MovePicker
from evaluators.materialist import MaterialEvaluator
from evaluators.positionalist import PositionalEvaluator
from evaluators.tapered import TaperedEvaluator


def get_engine(engine_id: str, depth: int, **kwargs) -> MinimaxEngine:
    factories = {
        'gen1': lambda d: MinimaxEngine(
            evaluator=MaterialEvaluator(),
            move_picker=MovePicker(max_depth=max(d, 64)),
            default_depth=d,
            name="Beansie",
            **kwargs
        ),
        'gen2': lambda d: MinimaxEngine(
            evaluator=PositionalEvaluator(),
            move_picker=MovePicker(max_depth=max(d, 64)),
            default_depth=d,
            name="Tuko",
            **kwargs
        ),
        'gen2.1': lambda d: MinimaxEngine(
            evaluator=PositionalEvaluator(count_mobility=True),
            move_picker=MovePicker(max_depth=max(d, 64)),
            default_depth=d,
            name="Tuko-coco",
            **kwargs
        ),
        'gen3': lambda d: MinimaxEngine(
            evaluator=TaperedEvaluator(),
            move_picker=MovePicker(max_depth=max(d, 64)),
            default_depth=d,
            name="Coco",
            **kwargs
        ),
    }

    if engine_id not in factories:
        valid_ids = ", ".join(factories.keys())
        raise ValueError(f"Engine '{engine_id}' not found. Available options: {valid_ids}")

    return factories[engine_id](depth)
