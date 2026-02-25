import random
from time import sleep, time

import chess


class BasicEngine():
    def __init__(self, depth: int, name: str = "Beansie"):
        self.name = name
        self.depth = depth
        self.evaluation_count = 0
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

    def evaluate(self, board: chess.Board):
        """
        Snapshot logic: Just looks at the current board and returns a number.
        """
        self.evaluation_count += 1

        if board.is_checkmate():
            if board.turn == chess.WHITE:
                return -99999  # Black won
            else:
                return 99999  # White won

        material_score = 0

        for piece_type, piece_value in self.piece_values.items():
            material_score += len(board.pieces(piece_type, chess.WHITE)) * piece_value
            material_score -= len(board.pieces(piece_type, chess.BLACK)) * piece_value

        return material_score

    def search(self, board: chess.Board, depth: int, is_maximizing: bool):
        """
        The 'Brain' logic: Looks ahead using Minimax/Alpha-Beta.
        """
        if depth == 0 or board.is_game_over():
            return self.evaluate(board)

        if is_maximizing:
            best_score = -float('inf')  # White's turn
            for move in board.legal_moves:
                board.push(move)
                score = self.search(board, depth - 1, True)
                board.pop()
                best_score = max(score, best_score)
        else:
            best_score = float('inf')  # Black's turn
            for move in board.legal_moves:
                board.push(move)
                score = self.search(board, depth - 1, False)
                board.pop()
                best_score = min(score, best_score)

        return best_score

    def get_best_move(self, board: chess.Board):
        """
        The Main API Method.
        The UI (Terminal or App) calls this.
        """
        # Reset counter for this move
        self.evaluation_count = 0
        start_time = time()

        is_white = board.turn == chess.WHITE
        best_move = None
        best_score = -float('inf') if is_white else float('inf')
        for move in board.legal_moves:
            board.push(move)
            score = self.search(board, self.depth - 1, is_maximizing=is_white)
            board.pop()

            if is_white:
                if score > best_score:
                    best_score = score
                    best_move = move
            else:
                if score < best_score:
                    best_score = score
                    best_move = move

        end_time = time()

        print(f"Engine thought for {end_time - start_time:.2f} seconds")
        print(f"Positions evaluated: {self.evaluation_count}")
        return best_move
