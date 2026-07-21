import chess


class MovePicker:
    def __init__(self, max_depth: int):
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
        # Killer moves: 2 killer move slots per ply
        self.killers = [[None, None] for _ in range(max_depth)]

    def halve_history(self) -> None:
        """Divide all history scores by 2 to favor recent search results"""
        for f in range(64):
            for t in range(64):
                self.history[f][t] >>= 1

    def record_cutoff(self, move: chess.Move, depth: int, ply: int, is_capture: bool) -> None:
        """Record the move which caused a Beta cutoff"""
        if is_capture:
            return  # Captures rely on MVV-LVA, don't pollute history/killers

        # 1. Update Killer Moves (only for quiet moves)
        if ply < len(self.killers) and self.killers[ply][0] != move:
            self.killers[ply][1] = self.killers[ply][0]  # Demote old killer
            self.killers[ply][0] = move  # Newest killer in slot 0

        # 2. Update History Table (cap at 500,000 so it never beats captures)
        inc = depth * depth
        current = self.history[move.from_square][move.to_square]
        self.history[move.from_square][move.to_square] = max(current + inc, 500_000)

    def get_moves(self, board: chess.Board, ply: int) -> list[chess.Move]:
        moves = list(board.legal_moves)

        # We use a lambda to calculate the score for each move
        # reverse=True ensures the HIGH scores are checked first
        moves.sort(key=lambda move: self._score_move(board, move, ply), reverse=True)

        return moves

    def _score_move(self, board: chess.Board, move: chess.Move, ply: int) -> int:
        # TIER 1: Captures (1,000,000+)
        if board.is_capture(move):
            # Default value for en passant victims (always a pawn)
            victim_type = chess.PAWN

            # Check what is actually on the square
            victim_piece = board.piece_at(move.to_square)
            if victim_piece:
                victim_type = victim_piece.piece_type

            attacker_type = board.piece_at(move.from_square).piece_type

            # MVV-LVA Formula
            return 1000_000 + (self.piece_values[victim_type] * 10) - self.piece_values[attacker_type]

        # TIER 2: Promotions (900,000+)
        if move.promotion:
            return 900_000 + self.piece_values[move.promotion]

        # TIER 3: Killer Moves (800,000+ and 700,000+)
        if ply < len(self.killers):
            if move == self.killers[ply][0]:
                return 800_000
            if move == self.killers[ply][1]:
                return 700_000

        # TIER 4: Quiet Moves via History Table (0 to 500,000)
        return self.history[move.from_square][move.to_square]
