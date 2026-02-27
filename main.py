import os
import subprocess

import chess

from basic_engine import BasicEngine


def play_engine():
    engine = BasicEngine(depth=5)
    board = chess.Board()
    while not board.is_game_over():
        # subprocess.run(['cls' if os.name == 'nt' else 'clear'], shell=True)
        print(f'+ Game against "{engine.name}" d={engine.depth} | Move: {board.fullmove_number} +')
        print(f"> {'White' if board.turn == chess.WHITE else 'Black'}", end='\n\n')
        print(board)
        if board.turn == chess.WHITE:
            move_uci = input('Enter your move (SAN, e.g. e4, Nf3): ')
            try:
                move = board.parse_san(move_uci)
                if move in board.legal_moves:
                    board.push(move)
                else:
                    print("Invalid move. Try again.")
            except ValueError:
                print("Notation not recognized. Use 'e4', 'Nf3', etc.")
        else:
            print(f'"{engine.name}" is thinking...')
            engine_move = engine.get_best_move(board)
            print(f'"{engine.name}" played: {board.san(engine_move)}')
            board.push(engine_move)

    print(f"Game over. Result: {board.result()}")


if __name__ == '__main__':
    play_engine()
