"""
Minimal text CLI. Moves are entered/printed in UCI form (e.g. e2e4, e7e8q).

Usage:
    python3 cli.py                 # play White vs engine, engine thinks to depth 4
    python3 cli.py --depth 5
    python3 cli.py --engine-color white   # watch engine play White against you as Black
"""
import argparse

from bitboard import WHITE, BLACK, PIECE_NAMES
from board import Board, START_FEN
from movegen import legal_moves
from search import Engine


def print_board(board: Board):
    for rank in range(7, -1, -1):
        row = f"{rank + 1} "
        for file in range(8):
            s = rank * 8 + file
            p = board.piece_at(s)
            if p is None:
                row += ". "
            else:
                color, piece = p
                c = PIECE_NAMES[piece]
                row += (c if color == WHITE else c.lower()) + " "
        print(row)
    print("  a b c d e f g h")
    print(f"side to move: {'white' if board.side == WHITE else 'black'}   fen: {board.fen()}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--engine-color", choices=["white", "black"], default="black")
    ap.add_argument("--fen", default=START_FEN)
    args = ap.parse_args()

    board = Board(args.fen)
    engine = Engine()
    engine_color = WHITE if args.engine_color == "white" else BLACK

    while True:
        print_board(board)
        moves = legal_moves(board)
        if not moves:
            print("Checkmate!" if board.in_check() else "Stalemate.")
            break

        if board.side == engine_color:
            move, score, stats = engine.search(board, max_depth=args.depth, time_limit=10)
            total_nodes = stats.nodes + stats.qnodes
            print(f"engine plays {move.uci()}  (score {score:+d}cp, "
                  f"{total_nodes:,} nodes, {stats.nps():,.0f} nps)")
            board.make_move(move)
        else:
            legal_uci = {m.uci() for m in moves}
            move_str = input("your move (uci, or 'quit'): ").strip()
            if move_str in ("quit", "exit"):
                break
            if move_str not in legal_uci:
                print("illegal move, try again")
                continue
            m = next(m for m in moves if m.uci() == move_str)
            board.make_move(m)


if __name__ == "__main__":
    main()
