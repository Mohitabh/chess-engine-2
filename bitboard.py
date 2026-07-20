"""
Bitboard primitives.

Squares are numbered 0..63 in "little-endian rank-file" order, the standard
convention used by most bitboard engines:

    a1=0, b1=1, ..., h1=7, a2=8, ..., h8=63

Each bitboard is a plain 64-bit Python int where bit i (1 << i) means
"square i is occupied / attacked / etc."
"""

WHITE, BLACK = 0, 1

PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = range(6)
PIECE_NAMES = "PNBRQK"

FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
FILE_AB = FILE_A | (FILE_A << 1)
FILE_GH = FILE_H | (FILE_H >> 1)
RANK_1 = 0x00000000000000FF
RANK_2 = RANK_1 << 8
RANK_4 = RANK_1 << 24
RANK_5 = RANK_1 << 32
RANK_7 = RANK_1 << 48
RANK_8 = RANK_1 << 56

ALL_SQUARES = 0xFFFFFFFFFFFFFFFF

SQUARE_NAMES = [f + r for r in "12345678" for f in "abcdefgh"]
NAME_TO_SQUARE = {name: i for i, name in enumerate(SQUARE_NAMES)}


def sq(file_idx: int, rank_idx: int) -> int:
    """file_idx, rank_idx in 0..7 (0='a'/rank1) -> square index."""
    return rank_idx * 8 + file_idx


def file_of(square: int) -> int:
    return square & 7


def rank_of(square: int) -> int:
    return square >> 3


def popcount(bb: int) -> int:
    return bb.bit_count()


def lsb_index(bb: int) -> int:
    """Index of the least-significant set bit. bb must be nonzero."""
    return (bb & -bb).bit_length() - 1


def iter_bits(bb: int):
    """Yield the index of each set bit in bb, low to high."""
    while bb:
        b = bb & -bb
        yield b.bit_length() - 1
        bb ^= b


def bit(square: int) -> int:
    return 1 << square


def square_name(square: int) -> str:
    return SQUARE_NAMES[square]
