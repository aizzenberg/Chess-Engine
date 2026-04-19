from abc import abstractmethod, ABCMeta, ABC
from time import time

import chess


class MinimaxEngine(ABC):
    def __init__(self, depth: int, name: str):
        self.depth = depth
        self.name = name
        self.evaluation_count = 0
        self.history = [[0 for _ in range(64)] for _ in range(64)]

    @abstractmethod
    def evaluate(self, board: chess.Board) -> int:
        """
        Snapshot evaluation logic: Looks at the current board and returns a score.
        """
        raise NotImplementedError

    def get_best_move(self, board: chess.Board):
        """
        The Main API Method.
        The UI (Terminal or App) calls this.
        """
        # Reset counter for this move
        self.evaluation_count = 0
        start_time = time()

        # --- AGING LOGIC START ---
        # Divide all history scores by 2 to favor recent search results
        for f in range(64):
            for t in range(64):
                self.history[f][t] >>= 1
        # --- AGING LOGIC END ---

        is_white = board.turn == chess.WHITE
        best_move = None
        best_score = -float('inf') if is_white else float('inf')
        alpha = -float('inf')
        beta = float('inf')

        for move in self._get_ordered_moves(board):
            board.push(move)
            score = self._search(board, self.depth - 1, is_maximizing=not is_white, alpha=alpha, beta=beta)
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
        print(f"Evaluation: {best_score}")
        return best_move

    def _search(self, board: chess.Board, depth: int, is_maximizing: bool, alpha: int | float,
                beta: int | float) -> int:
        """
        The 'Brain' logic: Looks ahead using Minimax/Alpha-Beta.
        """
        if board.is_repetition(3):
            return 0

        if depth == 0 or board.is_game_over():
            return self._quiescence_search(board, depth, is_maximizing, alpha, beta)

        if is_maximizing:
            best_score = -float('inf')  # White's turn
            for move in self._get_ordered_moves(board):
                board.push(move)
                # Recursion: See what Black does in response
                score = self._search(board, depth - 1, False, alpha, beta)
                board.pop()
                best_score = max(score, best_score)
                alpha = max(alpha, best_score)

                if best_score >= beta:
                    self.history[move.from_square][move.to_square] += depth * depth
                    break
        else:
            best_score = float('inf')  # Black's turn
            for move in self._get_ordered_moves(board):
                board.push(move)
                # Recursion: See what White does in response
                score = self._search(board, depth - 1, True, alpha, beta)
                board.pop()
                best_score = min(score, best_score)
                beta = min(beta, best_score)

                if best_score <= alpha:
                    self.history[move.from_square][move.to_square] += depth * depth
                    break

        return best_score

    def _quiescence_search(self, board: chess.Board, depth: int, is_maximizing: bool, alpha: int | float,
                           beta: int | float):
        standing_pat = self._evaluate(board, depth)

        moves = [move for move in self._get_ordered_moves(board) if board.is_capture(move)]

        if is_maximizing:
            # If the current board is already better than opponent can let us get, no need to capture more
            if standing_pat >= beta:
                return beta
            alpha = max(alpha, standing_pat)

            for move in moves:
                board.push(move)
                # Recursion: See what Black does in response
                score = self._quiescence_search(board, depth, False, alpha=alpha, beta=beta)
                board.pop()
                alpha = max(alpha, score)

                if alpha >= beta:
                    break

            return alpha
        else:
            # If the current board is already better than opponent can let us get, no need to capture more
            if standing_pat <= alpha:
                return alpha
            beta = min(beta, standing_pat)

            for move in moves:
                board.push(move)
                # Recursion: See what White does in response
                score = self._quiescence_search(board, depth, True, alpha=alpha, beta=beta)
                board.pop()
                beta = min(beta, score)

                if beta <= alpha:
                    break

            return beta

    def _evaluate(self, board: chess.Board, depth: int):
        """
        Core board evaluation logic: Checks for checkmate and returns a score.
        """
        self.evaluation_count += 1

        if board.is_checkmate():
            # Subtracting depth makes the score smaller (worse) the deeper we find it
            mate_score = 99999 + depth
            if board.turn == chess.WHITE:
                return -mate_score  # Black won
            else:
                return mate_score  # White won

        return self.evaluate(board)

    def _get_ordered_moves(self, board: chess.Board) -> list[chess.Move]:
        return list(board.legal_moves)
