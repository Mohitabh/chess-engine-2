# Python Bitboard Chess Engine

A lightweight, from-scratch chess engine implemented in pure Python. It uses a **64-bit bitboard** board representation, features a fully legal **move generator** (supporting castling, en passant, promotions, and double check/pin detection), and utilizes a robust **Negamax search with Alpha-Beta pruning** and advanced search heuristics.

---

## 🚀 Features

### 1. Board Representation
*   **64-Bit Bitboards**: Efficient board representation tracking pieces using unsigned 64-bit integers.
*   **Zobrist Hashing**: Transposition table keys computed incrementally during move generation for state caching.
*   **FEN Parser**: Import and export standard Forsyth-Edwards Notation (FEN) strings.

### 2. Move Generation
*   **Full Legality Filter**: Strictly generates legal moves by validating king safety against attacks/pins.
*   **Special Moves**: Full support for castling rights, en passant captures, and pawn promotions.
*   **Correctness Verified**: Validated against standard chess `perft` depths and stress-tested using the famous *Kiwipete* position.

### 3. Search & Evaluation
*   **Negamax with Alpha-Beta Pruning**: Efficient tree searching by pruning non-viable branches.
*   **Iterative Deepening**: Dynamically increases search depth for robust time management and improved transposition table efficiency.
*   **Quiescence Search**: Prevents the horizon effect by searching tactical captures until a quiet position is reached.
*   **Move Ordering**:
    *   **MVV-LVA**: Most Valuable Victim - Least Valuable Aggressor ordering for captures.
    *   **Transposition Table (TT)**: Retrieves best moves from previous iterations to guide search.
    *   **Killer Move Heuristic**: Records non-captures that caused a beta cutoff to prioritize them in sibling nodes.
*   **Static Evaluation**: Combines material valuations with positional **Piece-Square Tables (PST)**.

---

## 📂 Project Structure

| File | Description |
| :--- | :--- |
| [`bitboard.py`](file:///Users/mohitabhbhanu/Downloads/chess_engine/bitboard.py) | Defines the bitboard layout, square coordinates, and bitwise helper utilities. |
| [`attacks.py`](file:///Users/mohitabhbhanu/Downloads/chess_engine/attacks.py) | Precomputes sliding (ray-based) and non-sliding (knight, king, pawn) attack tables. |
| [`board.py`](file:///Users/mohitabhbhanu/Downloads/chess_engine/board.py) | The core `Board` class managing 12 bitboards, Zobrist hashing, and FEN state. |
| [`movegen.py`](file:///Users/mohitabhbhanu/Downloads/chess_engine/movegen.py) | Generates pseudo-legal moves and filters them for strict check/king legality. |
| [`evaluate.py`](file:///Users/mohitabhbhanu/Downloads/chess_engine/evaluate.py) | Evaluates board positions using material weightings and Piece-Square Tables. |
| [`search.py`](file:///Users/mohitabhbhanu/Downloads/chess_engine/search.py) | Negamax engine, transposition tables, move ordering, and quiescence search. |
| [`cli.py`](file:///Users/mohitabhbhanu/Downloads/chess_engine/cli.py) | Command-line interface to play against the engine or watch engine matches. |
| [`perft.py`](file:///Users/mohitabhbhanu/Downloads/chess_engine/perft.py) | Correctness utility measuring total leaf nodes at specific depths. |
| [`benchmark.py`](file:///Users/mohitabhbhanu/Downloads/chess_engine/benchmark.py) | Benchmarks search speed (nodes per second) on standard test positions. |
| [`tests/`](file:///Users/mohitabhbhanu/Downloads/chess_engine/tests) | Unit tests verifying move generation rules, search intelligence, and mate scenarios. |

---

## 🎮 How to Play & Run

This project uses the Python 3 standard library and has **zero third-party dependencies**.

### Play Against the Engine
Start a game from the terminal. By default, you play White, and the engine plays Black at search depth 4:
```bash
python3 cli.py --depth 4
```

To watch the engine play against itself, or to play as Black:
```bash
# Engine plays both sides
python3 cli.py --engine-color white --depth 4

# Play as Black
python3 cli.py --engine-color white --depth 4
```

### Run Benchmarks
Measure search nodes per second (NPS) across different search depths:
```bash
python3 benchmark.py 3
```

### Run Perft Verification
Verify the move generator's correctness against standard perft node counts:
```bash
python3 perft.py 4
```

### Run Unit Tests
Execute the test suite to verify the movegen rules and search stability:
```bash
python3 -m unittest discover -s tests
```

---

## 📈 Performance & Optimization Notes

In pure CPython, this engine achieves:
*   **Move Generation (Perft):** ~110,000–120,000 nodes/second
*   **Full Search (with Evaluation):** ~10,000–18,000 nodes/second

### Optimizing Beyond CPython
Since Python has significant per-operation overhead, the following paths are recommended to boost speed:
1.  **PyPy Interpreter**: Running this code under PyPy typically yields a **5x to 20x speedup** out-of-the-box without any code modifications.
2.  **C Extension Hooking**: For performance matching modern compiled engines, hot paths like `make_move`/`unmake_move` and move generation can be ported to C (via Cython or ctypes).

---

## 🗺️ Roadmap
*   [ ] **Magic Bitboards**: Replace classical ray-attacks with magic bitboards to optimize sliding-piece attacks (Bishop, Rook, Queen).
*   [ ] **UCI Protocol Compliance**: Add UCI (Universal Chess Interface) capability to hook the engine into graphical interfaces (e.g., Arena, Lichess, or ChessBase).
*   [ ] **Advanced Pruning Techniques**: Implement Null-Move Pruning (NMP), Late Move Reductions (LMR), and Principal Variation Search (PVS) to search deeper.
