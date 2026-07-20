"""
Perft ("performance test") counts the number of leaf nodes in the full
legal move tree to a given depth. From the standard starting position the
correct counts are well known, so perft doubles as a move-generator
correctness test: any bug in castling, en passant, promotion, or check
detection almost always shows up as a wrong perft number.
"""
import time

from board import Board, START_FEN
from movegen import legal_moves

# https://www.chessprogramming.org/Perft_Results
KNOWN_PERFT = {
    START_FEN: {1: 20, 2: 400, 3: 8902, 4: 197281, 5: 4865609},
    # "Kiwipete" - a standard perft stress position exercising castling,
    # en passant and promotions heavily.
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1": {
        1: 48, 2: 2039, 3: 97862, 4: 4085603,
    },
}


def perft(board: Board, depth: int) -> int:
    if depth == 0:
        return 1
    count = 0
    for m in legal_moves(board):
        board.make_move(m)
        count += perft(board, depth - 1)
        board.unmake_move(m)
    return count


def divide(board: Board, depth: int):
    """Per-move breakdown, useful for finding exactly which branch of the
    move tree has a bug when a perft total doesn't match."""
    total = 0
    for m in legal_moves(board):
        board.make_move(m)
        n = perft(board, depth - 1)
        board.unmake_move(m)
        print(f"{m.uci():6s} {n}")
        total += n
    print(f"total: {total}")
    return total


def run_suite(max_depth: int = 4, verbose: bool = True):
    all_ok = True
    for fen, depths in KNOWN_PERFT.items():
        board = Board(fen)
        for depth, expected in depths.items():
            if depth > max_depth:
                continue
            start = time.perf_counter()
            actual = perft(board, depth)
            elapsed = time.perf_counter() - start
            ok = actual == expected
            all_ok &= ok
            if verbose:
                nps = actual / elapsed if elapsed > 0 else float("inf")
                status = "OK" if ok else "FAIL"
                print(f"[{status}] depth={depth} expected={expected:>9} "
                      f"actual={actual:>9} ({elapsed:6.2f}s, {nps:,.0f} nps)  {fen[:30]}")
    return all_ok


if __name__ == "__main__":
    import sys
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    ok = run_suite(max_depth=depth)
    sys.exit(0 if ok else 1)
