import os
import random

import chess


def play_engine():
    board = chess.Board()
    print('-Game Started-')
    while not board.is_game_over():
        os.system('cls' if os.name == 'nt' else 'clear')  # clear terminal
        print(board)
        print(f"Turn: {'White' if board.turn == chess.WHITE else 'Black'}")
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
            print('Engine is thinking...')
            engine_move = random.choice(list(board.legal_moves))
            readable_move = board.san(engine_move)
            board.push(engine_move)
            print(f"Engine played: {readable_move}")


    print(f"Game over. Result: {board.result()}")


if __name__ == '__main__':
    play_engine()
