import chess

from abstracts.base_evaluator import BaseEvaluator


class MaterialistEvaluator(BaseEvaluator):
    def __init__(self):
        super().__init__()
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

    def evaluate(self, board: chess.Board):
        material_score = 0

        for piece_type, piece_value in self.piece_values.items():
            material_score += len(board.pieces(piece_type, chess.WHITE)) * piece_value
            material_score -= len(board.pieces(piece_type, chess.BLACK)) * piece_value

        return material_score
