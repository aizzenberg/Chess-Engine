from abc import ABC, abstractmethod
import chess


class BaseEvaluator(ABC):

    @abstractmethod
    def evaluate(self, board: chess.Board) -> int:
        """
        Snapshot evaluation logic: Looks at the current board and returns a score.
        """
        raise NotImplementedError

    def start_search(self, board: chess.Board):
        """Called once at the very beginning of get_best_move."""
        pass

    def push_move(self, board: chess.Board, move: chess.Move):
        """Called right BEFORE board.push(move). Good for calculating deltas!"""
        pass

    def pop_move(self, board: chess.Board):
        """Called right AFTER board.pop(). Good for reverting state!"""
        pass
