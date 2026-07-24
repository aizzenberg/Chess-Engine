import random
from contextlib import contextmanager
from time import time

import chess

from abstracts.base_evaluator import BaseEvaluator
from core.move_picker import MovePicker


class MinimaxEngine:
    def __init__(self, evaluator: BaseEvaluator, move_picker: MovePicker, default_depth: int, name: str,
                 uci_mode: bool = False):
        self.default_depth = default_depth
        self.ply = 0  # Distance from the root of the search
        self.name = name
        self.mp = move_picker
        self.eval = evaluator
        self.uci_mode = uci_mode
        self.stopped = False  # Abort toggle for UCI Handler

        # Performance Counters
        self.nodes_count = 0  # Total search nodes visited
        self.eval_count = 0  # Leaf evaluations called
        self.beta_cutoffs = 0  # Total beta cutoffs
        self.first_move_cutoffs = 0  # Cutoffs on index 0
        self.avg_first_move_cutoffs = 0  # Avg accumulator for first move cutoffs
        self.nodes_at_depth = {}  # EBF Tracking: Node counts indexed by depth reached

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

    def get_best_move(self, board: chess.Board, depth: int = None) -> tuple[chess.Move, float]:
        """
        The Main API Method.
        The UI (Terminal or App) calls this.
        """
        if depth is None:
            depth = self.default_depth

        # Reset counters for the new search
        self.nodes_count = 0
        self.eval_count = 0
        self.beta_cutoffs = 0
        self.first_move_cutoffs = 0

        start_time = time()
        self.eval.start_search(board)

        # History aging
        self.mp.halve_history()

        is_white = board.turn == chess.WHITE
        best_move = None
        best_score = -float('inf') if is_white else float('inf')
        alpha = -float('inf')
        beta = float('inf')

        # Root level count
        self.nodes_count += 1
        if not self.uci_mode:
            self._log_node_at_depth(self.ply)

        for move in self.mp.get_moves(board, self.ply):
            # 1. Break the root loop instantly if stopped
            if self.stopped:
                break

            with self._simulate_move(board, move):
                score = self._search(board, depth - 1, is_maximizing=not is_white, alpha=alpha, beta=beta)

            # 2. If the search was aborted mid-evaluation, DO NOT trust or record the returned score!
            if self.stopped:
                break

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

        # 3. CRITICAL SAFETY FALLBACK: If stopped before move 0 finished, default to the first legal move
        if best_move is None and board.legal_moves:
            try:
                best_move = next(iter(board.legal_moves))
                best_score = 0.0
            except StopIteration:
                best_move = None

        end_time = time()

        thinking_time = end_time - start_time

        # Standard engine NPS uses total nodes visited
        nps = int(self.nodes_count / thinking_time)
        self.nps_stack.append(nps)
        self.time_stack.append(thinking_time)

        if not self.uci_mode:
            evals_per_sec = int(self.eval_count / thinking_time)
            self._print_summary(thinking_time=thinking_time, nps=nps, evals_per_sec=evals_per_sec,
                                best_score=best_score,
                                show_ebf=True)

        return best_move, best_score

    def _print_summary(self, thinking_time, nps, best_score, evals_per_sec, show_ebf):
        cutoff_rate = (self.first_move_cutoffs / self.beta_cutoffs * 100) if self.beta_cutoffs > 0 else 0.0
        self.avg_first_move_cutoffs += (cutoff_rate - self.avg_first_move_cutoffs) / len(self.nps_stack)

        print(f"\n--- Search Summary [{self.name}] ---")
        print(f"Time:                {thinking_time:.2f}s")
        print(f"Nodes searched:      {self.nodes_count:,}")
        print(f"Leaf evaluations:    {self.eval_count:,}")
        print(f"NPS (Total Nodes):   ~{nps:,} | avg: ~{sum(self.nps_stack) // len(self.nps_stack):,}")
        print(f"Leaf Evals / sec:    ~{evals_per_sec:,}")
        print(
            f"First-move Cutoffs:  {cutoff_rate:.1f}% ({self.first_move_cutoffs:,}/{self.beta_cutoffs:,})"
            f" | avg: {self.avg_first_move_cutoffs:.1f}%"
        )

        if show_ebf:
            # Log EBF per depth layer
            print("Depth Breakdown & EBF:")
            sorted_depths = sorted(self.nodes_at_depth.keys())
            for d in sorted_depths:
                nodes = self.nodes_at_depth[d]
                prev_nodes = self.nodes_at_depth.get(d - 1, None)

                if prev_nodes and prev_nodes > 0:
                    ebf = nodes / prev_nodes
                    print(f"  Ply {d:2d} | Nodes: {nodes:10,} | EBF: {ebf:.2f}")
                else:
                    print(f"  Ply {d:2d} | Nodes: {nodes:10,} | EBF: N/A (Root/Top)")

        print(f"Evaluation:          {self._format_score(best_score)}", end="\n---\n")

    def _format_score(self, score: float):
        if score > 99000:
            ply = 100_000 - score
            moves = ply // 2
            return f'+M{moves}'
        elif score < -99000:
            ply = 100_000 - abs(score)
            moves = ply // 2
            return f'-M{moves}'

        return f'{score / 100:+.2f}'

    def _log_node_at_depth(self, depth: int):
        """Track nodes encountered at each depth layer"""
        self.nodes_at_depth[depth] = self.nodes_at_depth.get(depth, 0) + 1

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
        # 1. Abort immediately if interrupted by UCI Handler
        # Check for stop signal only every 2,048 nodes to preserve Python loop speed
        if (self.nodes_count & 2047 == 0) and self.stopped:
            return 0

        # Count every node visited upon entering search
        self.nodes_count += 1
        if not self.uci_mode:
            self._log_node_at_depth(self.ply)

        if board.is_repetition(2) or board.is_fifty_moves():
            return 0

        if depth == 0 or board.is_game_over():
            return self._quiescence_search(board, is_maximizing, alpha, beta)

        if is_maximizing:
            best_score = -float('inf')  # White's turn
            for idx, move in enumerate(self.mp.get_moves(board, self.ply)):
                with self._simulate_move(board, move):
                    # Recursion: See what Black does in response
                    score = self._search(board, depth - 1, False, alpha, beta)
                best_score = max(score, best_score)
                alpha = max(alpha, best_score)

                if best_score >= beta:
                    self.beta_cutoffs += 1
                    if idx == 0:
                        self.first_move_cutoffs += 1
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
                    self.beta_cutoffs += 1
                    if idx == 0:
                        self.first_move_cutoffs += 1
                    self.mp.record_cutoff(move, depth, self.ply, board.is_capture(move))
                    break

        return best_score

    def _quiescence_search(self, board: chess.Board, is_maximizing: bool, alpha: int | float,
                           beta: int | float):
        # 1. Abort immediately if interrupted by UCI Handler
        # Check for stop signal only every 2,048 nodes to preserve Python loop speed
        if (self.nodes_count & 2047 == 0) and self.stopped:
            return 0

        # Count every node visited upon entering search
        self.nodes_count += 1

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
            standing_pat = self._evaluate(board)

        if is_maximizing:
            # If the current board is already better than opponent can let us get, no need to capture more
            if standing_pat >= beta:
                # No move tried, so we don't count cutoff at all
                return beta

            alpha = max(alpha, standing_pat)

            for idx, move in enumerate(moves):
                with self._simulate_move(board, move):
                    # Recursion: See what Black does in response
                    score = self._quiescence_search(board, False, alpha=alpha, beta=beta)

                alpha = max(alpha, score)

                if alpha >= beta:
                    self.beta_cutoffs += 1
                    if idx == 0:
                        self.first_move_cutoffs += 1
                    break

            return alpha
        else:
            # If the current board is already better than opponent can let us get, no need to capture more
            if standing_pat <= alpha:
                self.beta_cutoffs += 1  # Cutoff occurred, but no move was tried
                return alpha

            beta = min(beta, standing_pat)

            for idx, move in enumerate(moves):
                with self._simulate_move(board, move):
                    # Recursion: See what White does in response
                    score = self._quiescence_search(board, True, alpha=alpha, beta=beta)

                beta = min(beta, score)

                if beta <= alpha:
                    self.beta_cutoffs += 1
                    if idx == 0:
                        self.first_move_cutoffs += 1
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

    def _evaluate(self, board: chess.Board):
        """
        Core board evaluation logic: Checks for checkmate and returns a score.
        """
        self.eval_count += 1

        # If the board physically has no mating material left, the score is exactly 0
        if board.is_insufficient_material():
            return 0

        if board.is_checkmate():
            return self._get_mate_score(board.turn, self.ply)

        return self.eval.evaluate(board)
