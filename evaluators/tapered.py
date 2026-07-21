import chess

from abstracts.base_evaluator import BaseEvaluator
from .pst import MG_TABLES, EG_TABLES


class TaperedEvaluator(BaseEvaluator):
    def __init__(self, count_mobility: bool = False):
        self.count_mobility = count_mobility

        # Keep scores for Midgame and Endgame in a separate stacks to gain speed comparing to a single tuple stack
        self.mg_stack: list[int] = []
        self.eg_stack: list[int] = []

        self.mg_tables = MG_TABLES
        self.eg_tables = EG_TABLES
        self.phase_stack: list[int] = []  # Game Phase (0 to 24)
        self.phase_weights = {
            chess.KNIGHT: 1, chess.BISHOP: 1,
            chess.ROOK: 2, chess.QUEEN: 4,
            chess.PAWN: 0, chess.KING: 0
        }

    def _eval_tapered_pos_score(self, board: chess.Board) -> tuple[int, int, int]:
        # 1. Calculate Initial Phase Score
        phase = 0

        for piece_type, piece_value in self.phase_weights.items():
            phase += len(board.pieces(piece_type, chess.WHITE)) * piece_value
            phase += len(board.pieces(piece_type, chess.BLACK)) * piece_value

        # 2. Calculate Positional Scores for Midgame and Endgame
        mg_score = 0
        eg_score = 0

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                if piece.color == chess.WHITE:
                    mg_score += self.mg_tables[piece.piece_type][square]
                    eg_score += self.eg_tables[piece.piece_type][square]
                else:
                    mirrored_square = chess.square_mirror(square)
                    mg_score -= self.mg_tables[piece.piece_type][mirrored_square]
                    eg_score -= self.eg_tables[piece.piece_type][mirrored_square]

        return phase, mg_score, eg_score

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

    def start_search(self, board: chess.Board):
        phase, mg_score, eg_score = self._eval_tapered_pos_score(board)

        self.phase_stack = [phase]
        self.mg_stack = [mg_score]
        self.eg_stack = [eg_score]

    def push_move(self, board: chess.Board, move: chess.Move):
        mg_score = self.mg_stack[-1]
        eg_score = self.eg_stack[-1]
        current_phase = self.phase_stack[-1]

        actor = board.piece_at(move.from_square)
        captured = board.piece_at(move.to_square)

        actor_mg_pst = self.mg_tables[actor.piece_type]
        actor_eg_pst = self.eg_tables[actor.piece_type]

        # --- 1. Actor PST Delta (Normal Move) ---
        if actor.color == chess.WHITE:
            mg_score += actor_mg_pst[move.to_square] - actor_mg_pst[move.from_square]
            eg_score += actor_eg_pst[move.to_square] - actor_eg_pst[move.from_square]
        else:
            from_square = chess.square_mirror(move.from_square)
            to_square = chess.square_mirror(move.to_square)
            mg_score -= actor_mg_pst[to_square] - actor_mg_pst[from_square]
            eg_score -= actor_eg_pst[to_square] - actor_eg_pst[from_square]

        # --- 2. Edge Case: Castling (Rook Delta) ---
        if board.is_castling(move):
            rook_mg_pst = self.mg_tables[chess.ROOK]
            rook_eg_pst = self.eg_tables[chess.ROOK]
            mg_delta = 0
            eg_delta = 0
            match move.to_square:
                case chess.G1 | chess.G8:
                    mg_delta = rook_mg_pst[chess.F1] - rook_mg_pst[chess.H1]
                    eg_delta = rook_eg_pst[chess.F1] - rook_eg_pst[chess.H1]
                case chess.C1 | chess.C8:
                    mg_delta = rook_mg_pst[chess.D1] - rook_mg_pst[chess.A1]
                    eg_delta = rook_eg_pst[chess.D1] - rook_eg_pst[chess.A1]

            mg_score += mg_delta if actor.color == chess.WHITE else -mg_delta
            eg_score += eg_delta if actor.color == chess.WHITE else -eg_delta

            self.mg_stack.append(mg_score)
            self.eg_stack.append(eg_score)
            self.phase_stack.append(current_phase)
            return

        # --- 3. Edge Case: En Passant (Victim Delta) ---
        if board.is_en_passant(move):
            shift = -8 if actor.color == chess.WHITE else 8
            victim_position = move.to_square + shift

            if actor.color == chess.WHITE:
                victim_position = chess.square_mirror(victim_position)
                mg_score += self.mg_tables[chess.PAWN][victim_position]
                eg_score += self.eg_tables[chess.PAWN][victim_position]
            else:
                mg_score -= self.mg_tables[chess.PAWN][victim_position]
                eg_score -= self.eg_tables[chess.PAWN][victim_position]

            self.mg_stack.append(mg_score)
            self.eg_stack.append(eg_score)
            self.phase_stack.append(current_phase)
            return

        # --- 4. Edge Case: Promotion (Piece Transformation) ---
        if promoted := move.promotion:
            # Undo the Pawn's PST/Material and apply the Promoted piece's PST/Material
            if actor.color == chess.WHITE:
                mg_score -= actor_mg_pst[move.to_square]
                mg_score += self.mg_tables[promoted][move.to_square]
                eg_score -= actor_eg_pst[move.to_square]
                eg_score += self.eg_tables[promoted][move.to_square]

            else:
                to_square = chess.square_mirror(move.to_square)
                mg_score += actor_mg_pst[to_square]
                mg_score -= self.mg_tables[promoted][to_square]
                eg_score += actor_eg_pst[to_square]
                eg_score -= self.eg_tables[promoted][to_square]

            # Update Game Phase on promotion
            current_phase += self.phase_weights[promoted]

        # --- 5. Capture Delta (Victim Removal) ---
        if captured is None:
            self.mg_stack.append(mg_score)
            self.eg_stack.append(eg_score)
            self.phase_stack.append(current_phase)
            return

        if captured.color == chess.WHITE:
            mg_score -= self.mg_tables[captured.piece_type][move.to_square]
            eg_score -= self.eg_tables[captured.piece_type][move.to_square]
        else:
            to_square = chess.square_mirror(move.to_square)
            mg_score += self.mg_tables[captured.piece_type][to_square]
            eg_score += self.eg_tables[captured.piece_type][to_square]

        # Update Game Phase on capture
        current_phase -= self.phase_weights[captured.piece_type]

        self.mg_stack.append(mg_score)
        self.eg_stack.append(eg_score)
        self.phase_stack.append(current_phase)

    def pop_move(self, board: chess.Board):
        self.mg_stack.pop()
        self.eg_stack.pop()
        self.phase_stack.pop()

    def evaluate(self, board: chess.Board) -> int:
        mg_score = self.mg_stack[-1]
        eg_score = self.eg_stack[-1]
        current_phase = min(self.phase_stack[-1], 24)

        base_score = (mg_score * current_phase + eg_score * (24 - current_phase)) // 24

        if not self.count_mobility:
            return base_score

        mobility_score = self._eval_mobility_score(board)

        return base_score + mobility_score
