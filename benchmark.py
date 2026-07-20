"""Benchmark search speed from a handful of standard positions."""
import time

from board import Board, START_FEN
from search import Engine

POSITIONS = {
    "startpos": START_FEN,
    "kiwipete": "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "endgame": "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
}


def run(depth: int = 5):
    for name, fen in POSITIONS.items():
        board = Board(fen)
        engine = Engine()
        t0 = time.perf_counter()
        best_move, score, stats = engine.search(board, max_depth=depth)
        elapsed = time.perf_counter() - t0
        total_nodes = stats.nodes + stats.qnodes
        print(f"{name:10s} depth={depth} best={best_move} score={score:+6d}  "
              f"nodes={total_nodes:>9,} time={elapsed:6.2f}s  nps={total_nodes/elapsed:>10,.0f}")


if __name__ == "__main__":
    import sys
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    run(d)
