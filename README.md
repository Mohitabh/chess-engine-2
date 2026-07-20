# Chess Engine (Python · Bitboards · Minimax + Alpha-Beta)

A from-scratch chess engine: 64-bit bitboard board representation, full
legal move generation (castling, en passant, promotion, check detection),
and a negamax search with alpha-beta pruning, iterative deepening, a
transposition table, and quiescence search.

## Architecture

```
bitboard.py   square numbering, bit-manipulation helpers (popcount, lsb, ...)
attacks.py    precomputed attack tables: knight/king/pawn patterns, and
              classical ray+nearest-blocker sliding attacks for bishop/rook/queen
board.py      Board class: 12 bitboards (6 piece types x 2 colors),
              make_move/unmake_move, Zobrist hashing, FEN import/export
movegen.py    pseudo-legal move generation + legality filter (king safety)
evaluate.py   material + piece-square-table static evaluation
search.py     negamax + alpha-beta, iterative deepening, transposition
              table, MVV-LVA move ordering, killer moves, quiescence search
perft.py      move-generator correctness/performance test ("perft")
benchmark.py  search speed benchmark (nodes/sec) from standard positions
cli.py        play a game against the engine from the terminal
```

## Correctness

Move generation is verified against the standard published `perft` node
counts (see `perft.py`), which is the conventional way chess engines prove
their move generator handles every edge case (castling rights, en passant,
promotions, discovered/double check, etc.) correctly:

```
$ python3 perft.py 4
[OK] depth=1 expected=       20 actual=       20 ...
[OK] depth=2 expected=      400 actual=      400 ...
[OK] depth=3 expected=     8902 actual=     8902 ...
[OK] depth=4 expected=   197281 actual=   197281 ...     (startpos)
[OK] depth=4 expected= 4085603 actual= 4085603 ...       (Kiwipete)
```

Kiwipete is the standard stress-test position that heavily exercises
castling, en passant, and promotions — matching it exactly at depth 4
(4,085,603 nodes) is a strong signal the generator is fully correct, not
just correct for quiet positions.

## Performance — measured, not assumed

Pure-Python raw move generation (`perft`, no evaluation) sustains roughly
**~110,000–120,000 nodes/sec** on this machine. Full alpha-beta search
(with evaluation, transposition table lookups, and move ordering per node)
runs at roughly **7,000–10,000 nodes/sec**, since every node does much more
work than perft's plain "generate and recurse."

Being direct about this: a pure-Python engine assessing **1M+ positions/sec**
isn't realistic — CPython's per-operation overhead is the bottleneck, not
the algorithm. Engines that hit that range (Stockfish, etc.) are C/C++ with
magic-bitboard sliding attacks, SIMD, and no per-node heap allocation. If
that resume number matters, the credible ways to actually get there are:
1. Run under **PyPy** instead of CPython (routinely 5–20x on this kind of
   code with no source changes).
2. Rewrite the hot path (move gen + make/unmake) as a **C extension**
   (ctypes/cffi/Cython) — this is what real ~1M+ nps engines do.
3. Report the number perft actually measures honestly (a well-optimized
   pure-Python bitboard perft in the 1–5M nps range is achievable with
   magic bitboards + numpy vectorization, but this implementation uses the
   simpler classical ray-attack method for clarity).

I'd recommend either matching the resume bullet to the measured number, or
noting it as a target/theoretical ceiling for a C-accelerated build rather
than what pure Python delivers.

## Usage

```bash
# Verify move generation correctness
python3 perft.py 4

# Benchmark search speed
python3 benchmark.py 5

# Play a game (you play White by default, engine plays Black at depth 4)
python3 cli.py --depth 4

# Watch the engine play both sides against itself, or set colors explicitly
python3 cli.py --engine-color white --depth 5
```

No third-party dependencies — everything is Python 3 standard library.

## What's implemented vs. not

Implemented: bitboard representation, full legal move generation (perft
verified through depth 4 on two positions, including all special moves),
negamax/alpha-beta, iterative deepening, transposition table (Zobrist
hashing), MVV-LVA capture ordering, killer-move heuristic, quiescence
search, material + piece-square evaluation, a playable CLI.

Not implemented (worth knowing if asked about this project): magic
bitboards for sliding attacks (classical ray method is used instead — 
correct, but slower), opening book, endgame tablebases, null-move pruning,
late-move reductions, and a UCI protocol adapter for use with a GUI like
Arena or a Lichess bot.
