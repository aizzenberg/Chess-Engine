from contextlib import contextmanager
from time import time

import chess

from abstracts.base_evaluator import BaseEvaluator
from core.move_picker import MovePicker


class MinimaxEngine:
    def __init__(self, evaluator: BaseEvaluator, move_picker: MovePicker, depth: int, name: str):
        self.depth = depth
        self.name = name
        self.mp = move_picker
        self.eval = evaluator
        self.evaluation_count = 0
        self.nps_stack = []

    def get_best_move(self, board: chess.Board):
        """
        The Main API Method.
        The UI (Terminal or App) calls this.
        """
        # Reset counter for this move
        self.evaluation_count = 0
        start_time = time()
        self.eval.start_search(board)

        # History aging
        self.mp.halve_history()

        is_white = board.turn == chess.WHITE
        best_move = None
        best_score = -float('inf') if is_white else float('inf')
        alpha = -float('inf')
        beta = float('inf')

        for move in self.mp.get_moves(board):
            self.eval.push_move(board, move)
            board.push(move)
            score = self._search(board, self.depth - 1, is_maximizing=not is_white, alpha=alpha, beta=beta)
            board.pop()
            self.eval.pop_move(board)

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

        thinking_time = end_time - start_time
        nps = self.evaluation_count // thinking_time
        self.nps_stack.append(nps)

        print(f"Engine thought for {thinking_time:.2f} seconds")
        print(f"Positions evaluated: {self.evaluation_count}")
        print(f"NPS: ~{nps} | avg: ~{sum(self.nps_stack) // len(self.nps_stack)}")
        print(f"Evaluation: {best_score}")
        return best_move

    @contextmanager
    def _simulate_move(self, board: chess.Board, move: chess.Move):
        self.eval.push_move(board, move)
        board.push(move)
        try:
            yield
        finally:
            board.pop()
            self.eval.pop_move(board)

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
            for move in self.mp.get_moves(board):
                with self._simulate_move(board, move):
                    # Recursion: See what Black does in response
                    score = self._search(board, depth - 1, False, alpha, beta)

                best_score = max(score, best_score)
                alpha = max(alpha, best_score)

                if best_score >= beta:
                    self.mp.record_cutoff(move, depth)
                    break
        else:
            best_score = float('inf')  # Black's turn
            for move in self.mp.get_moves(board):
                with self._simulate_move(board, move):
                    # Recursion: See what White does in response
                    score = self._search(board, depth - 1, True, alpha, beta)

                best_score = min(score, best_score)
                beta = min(beta, best_score)

                if best_score <= alpha:
                    self.mp.record_cutoff(move, depth)
                    break

        return best_score

    def _quiescence_search(self, board: chess.Board, depth: int, is_maximizing: bool, alpha: int | float,
                           beta: int | float):
        standing_pat = self._evaluate(board, depth)

        moves = [move for move in self.mp.get_moves(board) if board.is_capture(move)]

        if is_maximizing:
            # If the current board is already better than opponent can let us get, no need to capture more
            if standing_pat >= beta:
                return beta
            alpha = max(alpha, standing_pat)

            for move in moves:
                with self._simulate_move(board, move):
                    # Recursion: See what Black does in response
                    score = self._quiescence_search(board, depth, False, alpha=alpha, beta=beta)

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
                with self._simulate_move(board, move):
                    # Recursion: See what White does in response
                    score = self._quiescence_search(board, depth, True, alpha=alpha, beta=beta)

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

        return self.eval.evaluate(board)
