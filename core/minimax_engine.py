import random
from contextlib import contextmanager
from time import time

import chess

from abstracts.base_evaluator import BaseEvaluator
from core.move_picker import MovePicker


class MinimaxEngine:
    def __init__(self, evaluator: BaseEvaluator, move_picker: MovePicker, depth: int, name: str):
        self.depth = depth
        self.ply = 0  # Distance from the root of the search
        self.name = name
        self.mp = move_picker
        self.eval = evaluator
        self.evaluation_count = 0
        self.nps_stack = []
        self.time_stack = []

    def draw_nps_stack(self, ax1, ax2):

        Y = self.nps_stack
        X = [n for n in range(1, len(Y) + 1)]
        colors = ['red', 'blue', 'green', 'purple', 'gold', 'coral']
        clr = random.choice(colors)
        average = sum(self.nps_stack) // len(self.nps_stack)
        full_time = int(sum(self.time_stack) * 1000)

        def format_time(total_ms):
            # Calculate hours, minutes, and remaining seconds
            total_seconds, ms = divmod(total_ms, 1000)
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            # Conditional formatting based on hour count
            if hours > 0:
                return f"{hours}h {minutes:02d}m {seconds:02d}s"
            elif minutes > 0:
                return f"{minutes:02d}m {seconds:02d}s"
            else:
                return f"{seconds}.{ms // 10:02d}s"

        line_nps, = ax1.plot(X, Y, marker='o', linestyle='-', color=clr, label=f'NPS Curve "{self.name}"')
        ax1.axhline(y=average, color='grey', linestyle=':', label=f'Avg "{self.name}" ({average:.2f})', alpha=0.6)
        ax1.text(x=X[-1], y=average, s=f' {average:.2f}', color='grey', va='bottom', ha='left', fontweight='bold')

        time_Y = self.time_stack
        line_time, = ax2.plot(X, time_Y, color=clr, linestyle='--', linewidth=1.5,
                              label=f'Move Time "{self.name}" | total - {format_time(full_time)}')

        return [line_nps, line_time]

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
        self.time_stack.append(thinking_time)

        print(f"Engine thought for {thinking_time:.2f} seconds")
        print(f"Positions evaluated: {self.evaluation_count}")
        print(f"NPS: ~{nps} | avg: ~{sum(self.nps_stack) // len(self.nps_stack)}")
        print(f"Evaluation: {self._format_score(best_score)}")
        return best_move

    def _format_score(self, score: float):
        if score > 99000:
            ply = 100_000 - score
            moves = ply // 2
            return f'+M{moves}'
        elif score < -99000:
            ply = 100_000 - abs(score)
            moves = ply // 2
            return f'-M{moves}'

        return f'{score / 100:+.1f}'

    @contextmanager
    def _simulate_move(self, board: chess.Board, move: chess.Move):
        self.eval.push_move(board, move)
        board.push(move)
        self.ply += 1  # Step forward from root
        try:
            yield
        finally:
            self.ply -= 1  # Step backward
            board.pop()
            self.eval.pop_move(board)

    def _search(self, board: chess.Board, depth: int, is_maximizing: bool, alpha: int | float,
                beta: int | float) -> int:
        """
        The 'Brain' logic: Looks ahead using Minimax/Alpha-Beta.
        """
        if board.is_repetition(2) or board.is_fifty_moves():
            return 0

        if depth == 0 or board.is_game_over():
            return self._quiescence_search(board, depth, is_maximizing, alpha, beta)

        if is_maximizing:
            best_score = -float('inf')  # White's turn
            for idx, move in enumerate(self.mp.get_moves(board, self.ply)):
                with self._simulate_move(board, move):
                    # Recursion: See what Black does in response
                    score = self._search(board, depth - 1, False, alpha, beta)

                best_score = max(score, best_score)
                alpha = max(alpha, best_score)

                if best_score >= beta:
                    self.mp.record_cutoff(move, depth)
                    self.mp.record_cutoff(move, depth, self.ply, board.is_capture(move))
                    break
        else:
            best_score = float('inf')  # Black's turn
            for idx, move in enumerate(self.mp.get_moves(board, self.ply)):
                with self._simulate_move(board, move):
                    # Recursion: See what White does in response
                    score = self._search(board, depth - 1, True, alpha, beta)

                best_score = min(score, best_score)
                beta = min(beta, best_score)

                if best_score <= alpha:
                    self.mp.record_cutoff(move, depth)
                    self.mp.record_cutoff(move, depth, self.ply, board.is_capture(move))
                    break

        return best_score

    def _quiescence_search(self, board: chess.Board, depth: int, is_maximizing: bool, alpha: int | float,
                           beta: int | float):
        is_check = board.is_check()
        legal_moves = self.mp.get_moves(board, self.ply)

        if not legal_moves:
            if is_check:
                # That's checkmate
                return self._get_mate_score(is_maximizing, self.ply)
            else:
                # That's stalemate
                return 0

        if is_check:
            # Looking through all legal moves to escape check
            moves = legal_moves
            standing_pat = -float('inf') if is_maximizing else float('inf')
        else:
            # Looking only through captures to get quiescence position
            moves = [move for move in legal_moves if board.is_capture(move)]
            standing_pat = self._evaluate(board, depth)

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

    def _get_mate_score(self, mated_color: chess.Color, ply: int) -> int:
        # Subtracting distance from the root makes the score smaller (worse) the deeper we find it
        # This guarantees that closer mates always have a higher absolute value than distant mates
        mate_score = 99999 - ply
        if mated_color == chess.WHITE:
            return -mate_score  # Black won
        else:
            return mate_score  # White won

    def _evaluate(self, board: chess.Board, depth: int):
        """
        Core board evaluation logic: Checks for checkmate and returns a score.
        """
        self.evaluation_count += 1

        if board.is_checkmate():
            return self._get_mate_score(board.turn, self.ply)

        return self.eval.evaluate(board)
