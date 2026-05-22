import chess

from core.factory import get_engine
from engines.materialist import MaterialistEngine


def play_engine():
    engine = get_engine('gen2', depth=5)
    # engine1 = get_engine('gen1', depth=5)
    # engine2 = get_engine('gen2', depth=5)
    # fen = "r5kr/pp2p2p/2pp2p1/2nn1qP1/2BQ4/5P2/PP1B4/2K3RR w - - 0 1"
    # board = chess.Board(fen)

    board = chess.Board()
    while not board.is_game_over():
        # subprocess.run(['cls' if os.name == 'nt' else 'clear'], shell=True)
        print(f'+ Game against "{engine.name}" d={engine.depth} | Move: {board.fullmove_number} +')
        # print(f'+ Game "{engine1.name}" vs "{engine2.name}" | Move: {board.fullmove_number} +')
        print(f"> {'White' if board.turn == chess.WHITE else 'Black'}", end='\n\n')
        print(board)
        if board.turn == chess.WHITE:
            # print(f'"{engine.name}" is thinking...')
            # engine_move = engine.get_best_move(board)
            # print(f'"{engine.name}" played: {board.san(engine_move)}')
            # board.push(engine_move)
            move_uci = input('Enter your move (SAN, e.g. e4, Nf3): ')
            try:
                move = board.parse_san(move_uci)
                if move in board.legal_moves:
                    board.push(move)
                else:
                    print("Invalid move. Try again.")
            except ValueError:
                print("Notation not recognized. Use 'e4', 'Nf3', etc.")
            # print(f'"{engine1.name}" is thinking...')
            # engine_move = engine1.get_best_move(board)
            # print(f'"{engine1.name}" played: {board.san(engine_move)}')
            # board.push(engine_move)
        else:
            # move_uci = input('Enter your move (SAN, e.g. e4, Nf3): ')
            # try:
            #     move = board.parse_san(move_uci)
            #     if move in board.legal_moves:
            #         board.push(move)
            #     else:
            #         print("Invalid move. Try again.")
            # except ValueError:
            #     print("Notation not recognized. Use 'e4', 'Nf3', etc.")
            print(f'"{engine.name}" is thinking...')
            engine_move = engine.get_best_move(board)
            print(f'"{engine.name}" played: {board.san(engine_move)}')
            board.push(engine_move)
            # print(f'"{engine2.name}" is thinking...')
            # engine_move = engine2.get_best_move(board)
            # print(f'"{engine2.name}" played: {board.san(engine_move)}')
            # board.push(engine_move)

    print(f"Game over. Result: {board.result()}")


if __name__ == '__main__':
    play_engine()
