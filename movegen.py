from bitboard import (
    WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING,
    bit, sq, file_of, rank_of, iter_bits, RANK_2, RANK_7, RANK_4, RANK_5,
    FILE_A, FILE_H,
)
from attacks import KNIGHT_ATTACKS, KING_ATTACKS, PAWN_ATTACKS, bishop_attacks, rook_attacks, queen_attacks
from board import Board, Move, WK, WQ, BK, BQ

PROMO_PIECES = (QUEEN, ROOK, BISHOP, KNIGHT)


def _add_pawn_moves(board: Board, color: int, out: list):
    own = board.occupancy(color)
    opp = board.occupancy(1 - color)
    empty = ~(own | opp)
    pawns = board.bb[color][PAWN]
    forward = 8 if color == WHITE else -8
    start_rank = RANK_2 if color == WHITE else RANK_7
    promo_rank = RANK_7 if color == WHITE else RANK_2  # rank pawns promote FROM

    for frm in iter_bits(pawns):
        to1 = frm + forward
        if 0 <= to1 <= 63 and (bit(to1) & empty):
            if bit(frm) & promo_rank:
                for promo in PROMO_PIECES:
                    out.append(Move(frm, to1, PAWN, color, promo=promo))
            else:
                out.append(Move(frm, to1, PAWN, color))
                if bit(frm) & start_rank:
                    to2 = frm + 2 * forward
                    if bit(to2) & empty:
                        out.append(Move(frm, to2, PAWN, color, flag="double"))

        for att_sq in iter_bits(PAWN_ATTACKS[color][frm]):
            target_bit = bit(att_sq)
            if target_bit & opp:
                cap_color, cap_piece = board.piece_at(att_sq)
                if bit(frm) & promo_rank:
                    for promo in PROMO_PIECES:
                        out.append(Move(frm, att_sq, PAWN, color, cap_piece, cap_color, promo=promo))
                else:
                    out.append(Move(frm, att_sq, PAWN, color, cap_piece, cap_color))
            elif board.ep_square is not None and att_sq == board.ep_square:
                out.append(Move(frm, att_sq, PAWN, color, PAWN, 1 - color, flag="ep"))


def _add_piece_moves(board: Board, color: int, piece: int, attack_fn, out: list):
    own = board.occupancy(color)
    occ = board.occupancy()
    for frm in iter_bits(board.bb[color][piece]):
        if piece == KNIGHT:
            targets = KNIGHT_ATTACKS[frm] & ~own
        elif piece == KING:
            targets = KING_ATTACKS[frm] & ~own
        else:
            targets = attack_fn(frm, occ) & ~own
        for to in iter_bits(targets):
            cap = board.piece_at(to)
            if cap is not None:
                out.append(Move(frm, to, piece, color, cap[1], cap[0]))
            else:
                out.append(Move(frm, to, piece, color))


def _add_castling_moves(board: Board, color: int, out: list):
    occ = board.occupancy()
    opp = 1 - color
    if color == WHITE:
        if board.castling_rights & WK and not (occ & (bit(5) | bit(6))):
            if not any(board.is_square_attacked(s, opp) for s in (4, 5, 6)):
                out.append(Move(4, 6, KING, color, flag="castle_k"))
        if board.castling_rights & WQ and not (occ & (bit(1) | bit(2) | bit(3))):
            if not any(board.is_square_attacked(s, opp) for s in (4, 3, 2)):
                out.append(Move(4, 2, KING, color, flag="castle_q"))
    else:
        if board.castling_rights & BK and not (occ & (bit(61) | bit(62))):
            if not any(board.is_square_attacked(s, opp) for s in (60, 61, 62)):
                out.append(Move(60, 62, KING, color, flag="castle_k"))
        if board.castling_rights & BQ and not (occ & (bit(57) | bit(58) | bit(59))):
            if not any(board.is_square_attacked(s, opp) for s in (60, 59, 58)):
                out.append(Move(60, 58, KING, color, flag="castle_q"))


def pseudo_legal_moves(board: Board) -> list:
    color = board.side
    out: list = []
    _add_pawn_moves(board, color, out)
    _add_piece_moves(board, color, KNIGHT, None, out)
    _add_piece_moves(board, color, BISHOP, bishop_attacks, out)
    _add_piece_moves(board, color, ROOK, rook_attacks, out)
    _add_piece_moves(board, color, QUEEN, queen_attacks, out)
    _add_piece_moves(board, color, KING, None, out)
    _add_castling_moves(board, color, out)
    return out


def legal_moves(board: Board) -> list:
    color = board.side
    out = []
    for m in pseudo_legal_moves(board):
        board.make_move(m)
        if not board.is_square_attacked(board.king_square(color), board.side):
            out.append(m)
        board.unmake_move(m)
    return out
