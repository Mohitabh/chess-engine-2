"""
Board state: bitboards + make/unmake move.

Move/unmake (rather than copy-on-make) is used so search can explore deep
trees without allocating a new board object at every node — this is the
single biggest performance lever available in a pure-Python engine.
"""

import random
from dataclasses import dataclass, field
from typing import Optional, List

from bitboard import (
    WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING, PIECE_NAMES,
    bit, sq, file_of, rank_of, iter_bits, lsb_index,
    NAME_TO_SQUARE, SQUARE_NAMES, RANK_1, RANK_8,
)
from attacks import KNIGHT_ATTACKS, KING_ATTACKS, PAWN_ATTACKS, bishop_attacks, rook_attacks

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# Castling right bits
WK, WQ, BK, BQ = 1, 2, 4, 8

# ---------------------------------------------------------------------
# Move encoding: a plain tuple is faster to create than an object in
# CPython, so Move is (from_sq, to_sq, piece, color, captured, capture_color,
# promotion, flag).
# flag: '' normal, 'ep' en-passant capture, 'castle_k'/'castle_q', 'double'
# ---------------------------------------------------------------------


class Move:
    __slots__ = ("frm", "to", "piece", "color", "captured", "cap_color",
                 "promo", "flag")

    def __init__(self, frm, to, piece, color, captured=None, cap_color=None,
                 promo=None, flag=""):
        self.frm = frm
        self.to = to
        self.piece = piece
        self.color = color
        self.captured = captured
        self.cap_color = cap_color
        self.promo = promo
        self.flag = flag

    def uci(self) -> str:
        s = SQUARE_NAMES[self.frm] + SQUARE_NAMES[self.to]
        if self.promo is not None:
            s += PIECE_NAMES[self.promo].lower()
        return s

    def __repr__(self):
        return f"Move({self.uci()})"

    def __eq__(self, other):
        return isinstance(other, Move) and self.uci() == other.uci() and self.flag == other.flag

    def __hash__(self):
        return hash((self.frm, self.to, self.promo, self.flag))


@dataclass
class _UndoInfo:
    castling_rights: int
    ep_square: Optional[int]
    halfmove_clock: int
    zobrist: int


# ---------------------------------------------------------------------
# Zobrist hashing, for the transposition table.
# ---------------------------------------------------------------------
_rng = random.Random(0xC0FFEE)
ZOBRIST_PIECES = [[[_rng.getrandbits(64) for _ in range(64)] for _ in range(6)] for _ in range(2)]
ZOBRIST_SIDE = _rng.getrandbits(64)
ZOBRIST_CASTLING = [_rng.getrandbits(64) for _ in range(16)]
ZOBRIST_EP_FILE = [_rng.getrandbits(64) for _ in range(8)]


class Board:
    def __init__(self, fen: str = START_FEN):
        self.bb = [[0] * 6 for _ in range(2)]  # bb[color][piece] -> bitboard
        self.side = WHITE
        self.castling_rights = 0
        self.ep_square: Optional[int] = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.zobrist = 0
        self._history: List[_UndoInfo] = []
        self.set_fen(fen)

    # -- setup ----------------------------------------------------------

    def set_fen(self, fen: str):
        self.bb = [[0] * 6 for _ in range(2)]
        parts = fen.split()
        placement, side, castling, ep, halfmove, fullmove = (
            parts[0], parts[1], parts[2], parts[3],
            parts[4] if len(parts) > 4 else "0",
            parts[5] if len(parts) > 5 else "1",
        )
        rank = 7
        file = 0
        for c in placement:
            if c == "/":
                rank -= 1
                file = 0
            elif c.isdigit():
                file += int(c)
            else:
                color = WHITE if c.isupper() else BLACK
                piece = PIECE_NAMES.index(c.upper())
                self.bb[color][piece] |= bit(sq(file, rank))
                file += 1
        self.side = WHITE if side == "w" else BLACK
        self.castling_rights = 0
        if "K" in castling:
            self.castling_rights |= WK
        if "Q" in castling:
            self.castling_rights |= WQ
        if "k" in castling:
            self.castling_rights |= BK
        if "q" in castling:
            self.castling_rights |= BQ
        self.ep_square = NAME_TO_SQUARE[ep] if ep != "-" else None
        self.halfmove_clock = int(halfmove)
        self.fullmove_number = int(fullmove)
        self._history = []
        self.zobrist = self._compute_zobrist()

    def _compute_zobrist(self) -> int:
        h = 0
        for color in (WHITE, BLACK):
            for piece in range(6):
                for s in iter_bits(self.bb[color][piece]):
                    h ^= ZOBRIST_PIECES[color][piece][s]
        if self.side == BLACK:
            h ^= ZOBRIST_SIDE
        h ^= ZOBRIST_CASTLING[self.castling_rights]
        if self.ep_square is not None:
            h ^= ZOBRIST_EP_FILE[file_of(self.ep_square)]
        return h

    def fen(self) -> str:
        rows = []
        for rank in range(7, -1, -1):
            row = ""
            empty = 0
            for file in range(8):
                s = sq(file, rank)
                p = self.piece_at(s)
                if p is None:
                    empty += 1
                else:
                    if empty:
                        row += str(empty)
                        empty = 0
                    color, piece = p
                    c = PIECE_NAMES[piece]
                    row += c if color == WHITE else c.lower()
            if empty:
                row += str(empty)
            rows.append(row)
        placement = "/".join(rows)
        side = "w" if self.side == WHITE else "b"
        castling = "".join([
            "K" if self.castling_rights & WK else "",
            "Q" if self.castling_rights & WQ else "",
            "k" if self.castling_rights & BK else "",
            "q" if self.castling_rights & BQ else "",
        ]) or "-"
        ep = SQUARE_NAMES[self.ep_square] if self.ep_square is not None else "-"
        return f"{placement} {side} {castling} {ep} {self.halfmove_clock} {self.fullmove_number}"

    # -- queries ----------------------------------------------------------

    def occupancy(self, color: Optional[int] = None) -> int:
        if color is None:
            return self.occupancy(WHITE) | self.occupancy(BLACK)
        occ = 0
        for p in range(6):
            occ |= self.bb[color][p]
        return occ

    def piece_at(self, square: int):
        b = bit(square)
        for color in (WHITE, BLACK):
            for piece in range(6):
                if self.bb[color][piece] & b:
                    return color, piece
        return None

    def king_square(self, color: int) -> int:
        return lsb_index(self.bb[color][KING])

    def is_square_attacked(self, square: int, by_color: int) -> bool:
        occ = self.occupancy()
        if KNIGHT_ATTACKS[square] & self.bb[by_color][KNIGHT]:
            return True
        if KING_ATTACKS[square] & self.bb[by_color][KING]:
            return True
        # Attacked by a pawn of by_color means: a by_color pawn sits on a
        # square that attacks `square`, i.e. `square` is in the pawn's
        # attack set. Equivalent: square attacked via the *opposite*
        # color's pawn-attack table centered on `square`.
        opp = 1 - by_color
        if PAWN_ATTACKS[opp][square] & self.bb[by_color][PAWN]:
            return True
        if bishop_attacks(square, occ) & (self.bb[by_color][BISHOP] | self.bb[by_color][QUEEN]):
            return True
        if rook_attacks(square, occ) & (self.bb[by_color][ROOK] | self.bb[by_color][QUEEN]):
            return True
        return False

    def in_check(self, color: Optional[int] = None) -> bool:
        color = self.side if color is None else color
        return self.is_square_attacked(self.king_square(color), 1 - color)

    # -- make / unmake ----------------------------------------------------

    def make_move(self, m: Move):
        self._history.append(_UndoInfo(self.castling_rights, self.ep_square,
                                        self.halfmove_clock, self.zobrist))

        color, piece = m.color, m.piece
        frm_bit, to_bit = bit(m.frm), bit(m.to)

        # Remove moving piece from source.
        self.bb[color][piece] ^= frm_bit
        self.zobrist ^= ZOBRIST_PIECES[color][piece][m.frm]

        # Handle captures (including en passant).
        if m.flag == "ep":
            cap_sq = m.to + (-8 if color == WHITE else 8)
            self.bb[m.cap_color][m.captured] ^= bit(cap_sq)
            self.zobrist ^= ZOBRIST_PIECES[m.cap_color][m.captured][cap_sq]
        elif m.captured is not None:
            self.bb[m.cap_color][m.captured] ^= to_bit
            self.zobrist ^= ZOBRIST_PIECES[m.cap_color][m.captured][m.to]

        # Place moving piece (or its promotion) on destination.
        placed_piece = m.promo if m.promo is not None else piece
        self.bb[color][placed_piece] |= to_bit
        self.zobrist ^= ZOBRIST_PIECES[color][placed_piece][m.to]

        # Castling: move the rook too.
        if m.flag == "castle_k":
            rook_from, rook_to = (7, 5) if color == WHITE else (63, 61)
            self.bb[color][ROOK] ^= bit(rook_from) | bit(rook_to)
            self.zobrist ^= ZOBRIST_PIECES[color][ROOK][rook_from]
            self.zobrist ^= ZOBRIST_PIECES[color][ROOK][rook_to]
        elif m.flag == "castle_q":
            rook_from, rook_to = (0, 3) if color == WHITE else (56, 59)
            self.bb[color][ROOK] ^= bit(rook_from) | bit(rook_to)
            self.zobrist ^= ZOBRIST_PIECES[color][ROOK][rook_from]
            self.zobrist ^= ZOBRIST_PIECES[color][ROOK][rook_to]

        # Update castling rights.
        self.zobrist ^= ZOBRIST_CASTLING[self.castling_rights]
        if piece == KING:
            self.castling_rights &= ~(WK | WQ) if color == WHITE else ~(BK | BQ)
        for s, mask in ((0, WQ), (7, WK), (56, BQ), (63, BK)):
            if m.frm == s or m.to == s:
                self.castling_rights &= ~mask
        self.zobrist ^= ZOBRIST_CASTLING[self.castling_rights]

        # En passant target square.
        if self.ep_square is not None:
            self.zobrist ^= ZOBRIST_EP_FILE[file_of(self.ep_square)]
        self.ep_square = None
        if m.flag == "double":
            self.ep_square = (m.frm + m.to) // 2
            self.zobrist ^= ZOBRIST_EP_FILE[file_of(self.ep_square)]

        # Halfmove clock (50-move rule bookkeeping).
        if piece == PAWN or m.captured is not None:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        if color == BLACK:
            self.fullmove_number += 1

        self.side = 1 - self.side
        self.zobrist ^= ZOBRIST_SIDE

    def unmake_move(self, m: Move):
        self.side = 1 - self.side
        color, piece = m.color, m.piece
        frm_bit, to_bit = bit(m.frm), bit(m.to)

        placed_piece = m.promo if m.promo is not None else piece
        self.bb[color][placed_piece] ^= to_bit
        self.bb[color][piece] |= frm_bit

        if m.flag == "ep":
            cap_sq = m.to + (-8 if color == WHITE else 8)
            self.bb[m.cap_color][m.captured] |= bit(cap_sq)
        elif m.captured is not None:
            self.bb[m.cap_color][m.captured] |= to_bit

        if m.flag == "castle_k":
            rook_from, rook_to = (7, 5) if color == WHITE else (63, 61)
            self.bb[color][ROOK] ^= bit(rook_from) | bit(rook_to)
        elif m.flag == "castle_q":
            rook_from, rook_to = (0, 3) if color == WHITE else (56, 59)
            self.bb[color][ROOK] ^= bit(rook_from) | bit(rook_to)

        info = self._history.pop()
        self.castling_rights = info.castling_rights
        self.ep_square = info.ep_square
        self.halfmove_clock = info.halfmove_clock
        self.zobrist = info.zobrist

        if color == BLACK:
            self.fullmove_number -= 1
