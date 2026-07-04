import chess

from abstracts.base_evaluator import BaseEvaluator


class PositionalEvaluator(BaseEvaluator):
    def __init__(self, count_mobility: bool = False):
        self.count_mobility = count_mobility
        self.score_stack = []
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

        self._flip_pst_table()

    def _flip_pst_table(self):
        """
        Vertically mirrors the pst tables, so that python-chess square indexing corresponds our visual representation
        """
        for table in self.pst_table.values():
            for sqr_idx in range(len(table) // 2):
                row = sqr_idx // 8
                col = sqr_idx % 8
                mir_idx = (7 - row) * 8 + col
                mir = table[mir_idx]
                table[mir_idx] = table[sqr_idx]
                table[sqr_idx] = mir

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

    def start_search(self, board: chess.Board):
        material_score = self._eval_material_score(board)
        positional_score = self._eval_positional_score(board)

        self.score_stack = [material_score + positional_score]

    def push_move(self, board: chess.Board, move: chess.Move):
        current_score = self.score_stack[-1]

        actor = board.piece_at(move.from_square)
        captured = board.piece_at(move.to_square)

        actor_piece_pst = self.pst_table[actor.piece_type]

        # --- 1. Actor PST Delta (Normal Move) ---
        if actor.color == chess.WHITE:
            current_score += actor_piece_pst[move.to_square] - actor_piece_pst[move.from_square]
        else:
            from_square = chess.square_mirror(move.from_square)
            to_square = chess.square_mirror(move.to_square)
            current_score -= actor_piece_pst[to_square] - actor_piece_pst[from_square]

        # --- 2. Edge Case: Castling (Rook Delta) ---
        if board.is_castling(move):
            rook_pst = self.pst_table[chess.ROOK]
            delta = 0
            match move.to_square:
                case chess.G1 | chess.G8:
                    delta = rook_pst[chess.F1] - rook_pst[chess.H1]
                case chess.C1 | chess.C8:
                    delta = rook_pst[chess.D1] - rook_pst[chess.A1]

            current_score += delta if actor.color == chess.WHITE else -delta
            self.score_stack.append(current_score)
            return

        # --- 3. Edge Case: En Passant (Victim Delta) ---
        if board.is_en_passant(move):
            shift = -8 if actor.color == chess.WHITE else 8
            pawn_value = self.piece_values[chess.PAWN]
            victim_position = move.to_square + shift

            if actor.color == chess.WHITE:
                victim_position = chess.square_mirror(victim_position)
                current_score += pawn_value + self.pst_table[chess.PAWN][victim_position]
            else:
                current_score -= pawn_value + self.pst_table[chess.PAWN][victim_position]

            self.score_stack.append(current_score)
            return

        # --- 4. Edge Case: Promotion (Piece Transformation) ---
        if promoted := move.promotion:
            # Undo the Pawn's PST/Material and apply the Promoted piece's PST/Material
            if actor.color == chess.WHITE:
                current_score -= actor_piece_pst[move.to_square] + self.piece_values[chess.PAWN]
                current_score += self.pst_table[promoted][move.to_square] + self.piece_values[promoted]
            else:
                to_square = chess.square_mirror(move.to_square)
                current_score += actor_piece_pst[to_square] + self.piece_values[chess.PAWN]
                current_score -= self.pst_table[promoted][to_square] + self.piece_values[promoted]


        # --- 5. Capture Delta (Victim Removal) ---
        if captured is None:
            self.score_stack.append(current_score)
            return

        if captured.color == chess.WHITE:
            current_score -= self.pst_table[captured.piece_type][move.to_square]
            current_score -= self.piece_values[captured.piece_type]
        else:
            to_square = chess.square_mirror(move.to_square)
            current_score += self.pst_table[captured.piece_type][to_square]
            current_score += self.piece_values[captured.piece_type]

        self.score_stack.append(current_score)

    def pop_move(self, board: chess.Board):
        self.score_stack.pop()

    def evaluate(self, board: chess.Board) -> int:
        base_score = self.score_stack[-1]
        if not self.count_mobility:
            return base_score

        mobility_score = self._eval_mobility_score(board)

        return base_score + mobility_score
