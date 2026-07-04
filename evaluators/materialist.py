import chess

from abstracts.base_evaluator import BaseEvaluator


class MaterialEvaluator(BaseEvaluator):
    def __init__(self):
        self.score_stack = []
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

    def start_search(self, board: chess.Board):
        material_score = 0

        for piece_type, piece_value in self.piece_values.items():
            material_score += len(board.pieces(piece_type, chess.WHITE)) * piece_value
            material_score -= len(board.pieces(piece_type, chess.BLACK)) * piece_value

        self.score_stack = [material_score]

    def push_move(self, board: chess.Board, move: chess.Move):
        current_score = self.score_stack[-1]

        actor = board.piece_at(move.from_square)
        captured = board.piece_at(move.to_square)

        # --- 1. En Passant ---
        if board.is_en_passant(move):
            if actor.color == chess.WHITE:
                current_score += self.piece_values[chess.PAWN]
            else:
                current_score -= self.piece_values[chess.PAWN]

            self.score_stack.append(current_score)
            return

        # --- 2. Promotion (Piece Transformation) ---
        if promoted := move.promotion:
            # Undo the Pawn's Material and apply the Promoted piece's Material
            if actor.color == chess.WHITE:
                current_score += self.piece_values[promoted] - self.piece_values[chess.PAWN]
            else:
                current_score -= self.piece_values[promoted] - self.piece_values[chess.PAWN]

        # --- 5. Capture Delta (Victim Removal) ---
        if captured is None:
            self.score_stack.append(current_score)
            return

        captured_val = self.piece_values[captured.piece_type]
        current_score -= captured_val if captured.color == chess.WHITE else -captured_val

        self.score_stack.append(current_score)

    def pop_move(self, board: chess.Board):
        self.score_stack.pop()

    def evaluate(self, board: chess.Board):
        return self.score_stack[-1]
