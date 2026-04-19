from unicodedata import mirrored

import chess
from core.minimax_engine import MinimaxEngine


class PositionalistEngine(MinimaxEngine):
    def __init__(self, depth: int, name: str = "Tuko"):
        super().__init__(depth, name)
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
        self.pst_table = {
            # Pawns: Encourage center control and promotion
            chess.PAWN: [
                0, 0, 0, 0, 0, 0, 0, 0,
                50, 50, 50, 50, 50, 50, 50, 50,
                10, 10, 20, 30, 30, 20, 10, 10,
                5, 5, 10, 25, 25, 10, 5, 5,
                0, 0, 0, 20, 20, 0, 0, 0,
                5, -5, -10, 0, 0, -10, -5, 5,
                5, 10, 10, -20, -20, 10, 10, 5,
                0, 0, 0, 0, 0, 0, 0, 0
            ],
            # Knights: "Knights on the rim are dim"
            chess.KNIGHT: [
                -50, -40, -30, -30, -30, -30, -40, -50,
                -40, -20, 0, 0, 0, 0, -20, -40,
                -30, 0, 10, 15, 15, 10, 0, -30,
                -30, 5, 15, 20, 20, 15, 5, -30,
                -30, 0, 15, 20, 20, 15, 0, -30,
                -30, 5, 10, 15, 15, 10, 5, -30,
                -40, -20, 0, 5, 5, 0, -20, -40,
                -50, -40, -30, -30, -30, -30, -40, -50
            ],
            # Bishops: Stay off the edges, stay active
            chess.BISHOP: [
                -20, -10, -10, -10, -10, -10, -10, -20,
                -10, 0, 0, 0, 0, 0, 0, -10,
                -10, 0, 5, 10, 10, 5, 0, -10,
                -10, 5, 5, 10, 10, 5, 5, -10,
                -10, 0, 10, 10, 10, 10, 0, -10,
                -10, 10, 10, 10, 10, 10, 10, -10,
                -10, 5, 0, 0, 0, 0, 5, -10,
                -20, -10, -10, -10, -10, -10, -10, -20
            ],
            # Rooks: Occupy the 7th rank and center files
            chess.ROOK: [
                0, 0, 0, 0, 0, 0, 0, 0,
                5, 10, 10, 10, 10, 10, 10, 5,
                -5, 0, 0, 0, 0, 0, 0, -5,
                -5, 0, 0, 0, 0, 0, 0, -5,
                -5, 0, 0, 0, 0, 0, 0, -5,
                -5, 0, 0, 0, 0, 0, 0, -5,
                -5, 0, 0, 0, 0, 0, 0, -5,
                0, 0, 0, 5, 5, 0, 0, 0
            ],
            # Queen: Don't bring her out too early, but keep her central
            chess.QUEEN: [
                -20, -10, -10, -5, -5, -10, -10, -20,
                -10, 0, 0, 0, 0, 0, 0, -10,
                -10, 0, 5, 5, 5, 5, 0, -10,
                -5, 0, 5, 5, 5, 5, 0, -5,
                0, 0, 5, 5, 5, 5, 0, -5,
                -10, 5, 5, 5, 5, 5, 0, -10,
                -10, 0, 5, 0, 0, 0, 0, -10,
                -20, -10, -10, -5, -5, -10, -10, -20
            ],
            # King (Early Game): Stay in the corner behind pawns
            chess.KING: [
                -30, -40, -40, -50, -50, -40, -40, -30,
                -30, -40, -40, -50, -50, -40, -40, -30,
                -30, -40, -40, -50, -50, -40, -40, -30,
                -30, -40, -40, -50, -50, -40, -40, -30,
                -20, -30, -30, -40, -40, -30, -30, -20,
                -10, -20, -20, -20, -20, -20, -20, -10,
                20, 20, 0, 0, 0, 0, 20, 20,
                20, 30, 10, 0, 0, 10, 30, 20
            ]
        }

    def _get_ordered_moves(self, board: chess.Board) -> list[chess.Move]:
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

    def _eval_material_score(self, board: chess.Board) -> int:
        material_score = 0

        for piece_type, piece_value in self.piece_values.items():
            material_score += len(board.pieces(piece_type, chess.WHITE)) * piece_value
            material_score -= len(board.pieces(piece_type, chess.BLACK)) * piece_value

        return material_score

    def _eval_positional_score(self, board: chess.Board) -> int:
        positional_score = 0

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                if piece.color == chess.WHITE:
                    positional_score += self.pst_table[piece.piece_type][square]
                else:
                    mirrored_square = chess.square_mirror(square)
                    positional_score -= self.pst_table[piece.piece_type][mirrored_square]

        return positional_score

    def _eval_mobility_score(self, board: chess.Board) -> int:

        your_color = board.turn
        opp_color = not your_color

        your_pieces = board.occupied_co[your_color]
        opp_pieces = board.occupied_co[opp_color]

        your_pawns_attacks = 0
        for square in board.pieces(chess.PAWN, your_color):
            your_pawns_attacks |= chess.BB_PAWN_ATTACKS[your_color][square]

        opp_pawns_attacks = 0
        for square in board.pieces(chess.PAWN, opp_color):
            opp_pawns_attacks |= chess.BB_PAWN_ATTACKS[opp_color][square]

        # Points per each safe square available
        weights = {
            chess.QUEEN: 0.3,
            chess.ROOK: 0.57,
            chess.BISHOP: 0.62,
            chess.KNIGHT: 2
        }

        def get_color_mobility(color: chess.Color, enemy_pawn_attacks_mask: chess.Bitboard,
                               friendly_mask: chess.Bitboard):
            total = 0

            for piece, weight in weights.items():
                # Logic: Attacks x Pin Restriction - Own Pieces - Enemy Pawn Attacks
                for sq in board.pieces(piece, color):
                    mask = board.attacks_mask(sq) & board.pin_mask(color, sq)
                    mask &= ~friendly_mask  # Disregard moves onto friendly pieces
                    mask &= ~enemy_pawn_attacks_mask  # Disregard moves into pawn fire

                    total += mask.bit_count() * weight

            return total

        your_mobility = get_color_mobility(your_color, opp_pawns_attacks, your_pieces)
        opp_mobility = get_color_mobility(opp_color, your_pawns_attacks, opp_pieces)

        relative_score = your_mobility - opp_mobility
        return relative_score if your_color == chess.WHITE else -relative_score

    def evaluate(self, board: chess.Board) -> int:
        material_score = self._eval_material_score(board)
        positional_score = self._eval_positional_score(board)
        mobility_score = self._eval_mobility_score(board)

        return material_score + positional_score + mobility_score
