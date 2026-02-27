from abc import abstractmethod, ABCMeta, ABC
from time import time

import chess


class MinimaxEngine(ABC):
    def __init__(self, depth: int, name: str):
        self.depth = depth
        self.name = name
        self.evaluation_count = 0

    @abstractmethod
    def evaluate(self, board: chess.Board):
        """
        Snapshot evaluation logic: Looks at the current board and returns a score.
        """
        raise NotImplementedError

    def _evaluate(self, board: chess.Board):
        """
        Core board evaluation logic: Checks for checkmate and returns a score.
        """
        self.evaluation_count += 1

        if board.is_checkmate():
            if board.turn == chess.WHITE:
                return -99999  # Black won
            else:
                return 99999  # White won

        return self.evaluate(board)

    def search(self, board: chess.Board, depth: int, is_maximizing: bool, alpha: int | float, beta: int | float):
        """
        The 'Brain' logic: Looks ahead using Minimax/Alpha-Beta.
        """
        if depth == 0 or board.is_game_over():
            return self._evaluate(board)

        if is_maximizing:
            best_score = -float('inf')  # White's turn
            for move in board.legal_moves:
                board.push(move)
                # Recursion: See what Black does in response
                score = self.search(board, depth - 1, False, alpha=alpha, beta=beta)
                board.pop()
                best_score = max(score, best_score)
                alpha = max(alpha, best_score)

                if best_score >= beta:
                    break
        else:
            best_score = float('inf')  # Black's turn
            for move in board.legal_moves:
                board.push(move)
                # Recursion: See what White does in response
                score = self.search(board, depth - 1, True, alpha=alpha, beta=beta)
                board.pop()
                best_score = min(score, best_score)
                beta = min(beta, best_score)

                if best_score <= alpha:
                    break

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
        alpha = -float('inf')
        beta = float('inf')

        for move in board.legal_moves:
            board.push(move)
            score = self.search(board, self.depth - 1, is_maximizing=not is_white, alpha=alpha, beta=beta)
            board.pop()

            if is_white:
                alpha = max(alpha, score)

                if score > best_score:
                    best_score = score
                    best_move = move

            else:
                beta = min(beta, score)

                if score < best_score:
                    best_score = score
                    best_move = move

        end_time = time()

        print(f"Engine thought for {end_time - start_time:.2f} seconds")
        print(f"Positions evaluated: {self.evaluation_count}")
        return best_move
