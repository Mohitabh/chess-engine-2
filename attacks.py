"""
Precomputed attack tables.

Knight/king/pawn attacks are simple fixed patterns, precomputed once per
square. Sliding piece (bishop/rook/queen) attacks use the classical
"ray + nearest blocker" technique: for each square and each of the 8
compass directions we precompute the full ray to the board edge, then at
query time intersect it with the current occupancy and clip the ray at the
first blocker. This avoids any per-move loop over individual squares.
"""

from bitboard import (
    file_of, rank_of, sq, bit, ALL_SQUARES, FILE_A, FILE_H, FILE_AB, FILE_GH,
    RANK_1, RANK_8, WHITE, BLACK,
)

N, S, E, W, NE, NW, SE, SW = range(8)
_POS_DIRS = (N, E, NE, NW)   # increasing square index -> nearest blocker = LSB
_NEG_DIRS = (S, W, SE, SW)   # decreasing square index -> nearest blocker = MSB


def _ray(square: int, direction: int) -> int:
    f, r = file_of(square), rank_of(square)
    out = 0
    df, dr = {
        N: (0, 1), S: (0, -1), E: (1, 0), W: (-1, 0),
        NE: (1, 1), NW: (-1, 1), SE: (1, -1), SW: (-1, -1),
    }[direction]
    nf, nr = f + df, r + dr
    while 0 <= nf <= 7 and 0 <= nr <= 7:
        out |= bit(sq(nf, nr))
        nf += df
        nr += dr
    return out


RAYS = [[_ray(s, d) for s in range(64)] for d in range(8)]


def _knight_attacks(square: int) -> int:
    f, r = file_of(square), rank_of(square)
    out = 0
    for df, dr in ((1, 2), (2, 1), (2, -1), (1, -2),
                   (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
        nf, nr = f + df, r + dr
        if 0 <= nf <= 7 and 0 <= nr <= 7:
            out |= bit(sq(nf, nr))
    return out


def _king_attacks(square: int) -> int:
    f, r = file_of(square), rank_of(square)
    out = 0
    for df in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if df == 0 and dr == 0:
                continue
            nf, nr = f + df, r + dr
            if 0 <= nf <= 7 and 0 <= nr <= 7:
                out |= bit(sq(nf, nr))
    return out


def _pawn_attacks(square: int, color: int) -> int:
    f, r = file_of(square), rank_of(square)
    out = 0
    dr = 1 if color == WHITE else -1
    for df in (-1, 1):
        nf, nr = f + df, r + dr
        if 0 <= nf <= 7 and 0 <= nr <= 7:
            out |= bit(sq(nf, nr))
    return out


KNIGHT_ATTACKS = [_knight_attacks(s) for s in range(64)]
KING_ATTACKS = [_king_attacks(s) for s in range(64)]
PAWN_ATTACKS = [[_pawn_attacks(s, WHITE) for s in range(64)],
                 [_pawn_attacks(s, BLACK) for s in range(64)]]


def _lsb_square(bb: int) -> int:
    return (bb & -bb).bit_length() - 1


def _msb_square(bb: int) -> int:
    return bb.bit_length() - 1


def _sliding_attacks(square: int, occupancy: int, directions) -> int:
    attacks = 0
    for d in directions:
        ray = RAYS[d][square]
        blockers = ray & occupancy
        if blockers:
            if d in _POS_DIRS:
                blocker_sq = _lsb_square(blockers)
            else:
                blocker_sq = _msb_square(blockers)
            ray ^= RAYS[d][blocker_sq]  # remove squares beyond (and incl.) the blocker's ray
        attacks |= ray
    return attacks


_BISHOP_DIRS = (NE, NW, SE, SW)
_ROOK_DIRS = (N, S, E, W)


def bishop_attacks(square: int, occupancy: int) -> int:
    return _sliding_attacks(square, occupancy, _BISHOP_DIRS)


def rook_attacks(square: int, occupancy: int) -> int:
    return _sliding_attacks(square, occupancy, _ROOK_DIRS)


def queen_attacks(square: int, occupancy: int) -> int:
    return bishop_attacks(square, occupancy) | rook_attacks(square, occupancy)
