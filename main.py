import chess

from core.factory import get_engine
from engines.materialist import MaterialistEngine


def play_engine():
    engine1 = get_engine('gen1', depth=5, name='Deep')
    engine2 = get_engine('gen1', depth=3, name='Flat')
    board = chess.Board()
    while not board.is_game_over():
        # subprocess.run(['cls' if os.name == 'nt' else 'clear'], shell=True)
        # print(f'+ Game against "{engine.name}" d={engine.depth} | Move: {board.fullmove_number} +')
        print(f'+ Game "{engine1.name}" vs "{engine2.name}" | Move: {board.fullmove_number} +')
        print(f"> {'White' if board.turn == chess.WHITE else 'Black'}", end='\n\n')
        print(board)
        if board.turn == chess.WHITE:
            # move_uci = input('Enter your move (SAN, e.g. e4, Nf3): ')
            # try:
            #     move = board.parse_san(move_uci)
            #     if move in board.legal_moves:
            #         board.push(move)
            #     else:
            #         print("Invalid move. Try again.")
            # except ValueError:
            #     print("Notation not recognized. Use 'e4', 'Nf3', etc.")
            print(f'"{engine1.name}" is thinking...')
            engine_move = engine1.get_best_move(board)
            print(f'"{engine1.name}" played: {board.san(engine_move)}')
            board.push(engine_move)
        else:
            print(f'"{engine2.name}" is thinking...')
            engine_move = engine2.get_best_move(board)
            print(f'"{engine2.name}" played: {board.san(engine_move)}')
            board.push(engine_move)

    print(f"Game over. Result: {board.result()}")


if __name__ == '__main__':
    play_engine()
