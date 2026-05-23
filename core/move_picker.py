import chess


class MovePicker:
    def __init__(self):
        # "Rough estimates" for piece values strictly used for move ordering
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
        self.history = [[0 for _ in range(64)] for _ in range(64)]

    def halve_history(self) -> None:
        """Divide all history scores by 2 to favor recent search results"""
        for f in range(64):
            for t in range(64):
                self.history[f][t] >>= 1

    def record_cutoff(self, move: chess.Move, depth: int) -> None:
        """Record the move which caused a Beta cutoff"""
        self.history[move.from_square][move.to_square] += depth * depth

    def get_moves(self, board: chess.Board) -> list[chess.Move]:
        moves = list(board.legal_moves)

        # We use a lambda to calculate the score for each move
        # reverse=True ensures the HIGH scores are checked first
        moves.sort(key=lambda move: self._score_move(board, move), reverse=True)

        return moves

    def _score_move(self, board: chess.Board, move: chess.Move) -> int:
        # 1. Handle Captures
        if board.is_capture(move):
            # Default value for en passant victims (always a pawn)
            victim_type = chess.PAWN

            # Check what is actually on the square
            victim_piece = board.piece_at(move.to_square)
            if victim_piece:
                victim_type = victim_piece.piece_type

            attacker_type = board.piece_at(move.from_square).piece_type

            # MVV-LVA Formula
            return 100000 + (self.piece_values[victim_type] * 10) - self.piece_values[attacker_type]

        # 2. Handle Promotions
        if move.promotion:
            return 90000 + self.piece_values[move.promotion]

        # 3. Check the History Table for "Quiet" moves
        return self.history[move.from_square][move.to_square]