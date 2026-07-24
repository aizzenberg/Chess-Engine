import sys
import threading
import chess

from core.factory import get_engine


class UCIHandler:
    def __init__(self, engine_id: str, default_depth: int):
        self.engine_id = engine_id
        self.default_depth = default_depth

        # Enable UCI mode immediately to suppress ASCII logs and boost NPS
        self.engine = get_engine(self.engine_id, self.default_depth, uci_mode=True)

        self.board = chess.Board()
        self.search_thread: threading.Thread | None = None
        self.game_in_progress = False

    def listen(self):
        for line in sys.stdin:
            tokens = line.strip().split()
            if not tokens:
                continue

            cmd = tokens[0]

            if cmd == "uci":
                self._handle_uci()
            elif cmd == "isready":
                print("readyok", flush=True)
            elif cmd == "setoption":
                self._handle_setoption(tokens)
            elif cmd == "ucinewgame":
                self._handle_ucinewgame()
            elif cmd == "position":
                self._handle_position(tokens)
            elif cmd == "go":
                self._handle_go(tokens)
            elif cmd == "stop":
                self._stop_search()
            elif cmd == "quit":
                self._stop_search()
                break

    def _handle_uci(self):
        print(f"id name {self.engine.name}", flush=True)
        print("id author aizzenberg", flush=True)
        print(f"option name EngineType type combo default {self.engine_id} var gen1 var gen2 var gen2.1 var gen3",
              flush=True)
        print(f"option name Depth type spin default {self.default_depth} min 1 max 8", flush=True)
        print("uciok", flush=True)

    def _handle_setoption(self, tokens: list[str]):
        if self.game_in_progress or self._is_searching():
            return

        if "name" in tokens and "value" in tokens:
            name_idx = tokens.index("name") + 1
            val_idx = tokens.index("value") + 1
            opt_name = tokens[name_idx].lower()
            opt_val = tokens[val_idx]

            if opt_name == "enginetype" and opt_val in ['gen1', 'gen2', 'gen2.1', 'gen3']:
                self.engine_id = opt_val
                self.engine = get_engine(self.engine_id, self.default_depth, uci_mode=True)
            elif opt_name == "depth":
                try:
                    self.default_depth = int(opt_val)
                    self.engine = get_engine(self.engine_id, self.default_depth, uci_mode=True)
                except ValueError:
                    pass

    def _handle_ucinewgame(self):
        self._stop_search()
        self.board.reset()
        self.game_in_progress = False

        if hasattr(self.engine.mp, "clear_memory"):
            self.engine.mp.clear_memory()
        if hasattr(self.engine.eval, "clear_memory"):
            self.engine.eval.clear_memory()

    def _handle_position(self, tokens: list[str]):
        if self._is_searching():
            return

        self.game_in_progress = True

        try:
            idx = 1
            if tokens[idx] == "startpos":
                self.board.reset()
                idx += 1
            elif tokens[idx] == "fen":
                fen_str = " ".join(tokens[idx + 1: idx + 7])
                self.board = chess.Board(fen_str)
                idx += 7

            if idx < len(tokens) and tokens[idx] == "moves":
                for move_str in tokens[idx + 1:]:
                    self.board.push_uci(move_str)
        except Exception:
            pass

    def _handle_go(self, tokens: list[str]):
        self._stop_search()
        self.game_in_progress = True

        search_depth = self.default_depth
        if "depth" in tokens:
            try:
                search_depth = int(tokens[tokens.index("depth") + 1])
            except (IndexError, ValueError):
                pass

        search_board = self.board.copy()
        self.search_thread = threading.Thread(
            target=self._run_search,
            args=(search_board, search_depth),
            daemon=True
        )
        self.search_thread.start()

    def _run_search(self, board: chess.Board, depth: int):
        self.engine.stopped = False

        best_move, best_score = self.engine.get_best_move(board, depth)

        if best_move:
            # Retrieve the newly populated metrics from the engine
            time_ms = int(self.engine.time_stack[-1] * 1000) if self.engine.time_stack else 0
            nps = self.engine.nps_stack[-1] if self.engine.nps_stack else 0
            nodes = self.engine.nodes_count

            uci_score = self._format_uci_score(best_score)

            print(
                f"info depth {depth} {uci_score} nodes {nodes} nps {nps} time {time_ms} pv {best_move.uci()}",
                flush=True
            )
            print(f"bestmove {best_move.uci()}", flush=True)

    def _format_uci_score(self, score: float) -> str:
        if abs(score) > 99_000:
            moves = max(1, int((100_000 - abs(score)) // 2))
            mate_val = moves if score > 0 else -moves
            return f"score mate {mate_val}"
        else:
            return f"score cp {int(score)}"

    def _stop_search(self):
        if self._is_searching():
            self.engine.stopped = True
            self.search_thread.join()

    def _is_searching(self) -> bool:
        return self.search_thread is not None and self.search_thread.is_alive()
