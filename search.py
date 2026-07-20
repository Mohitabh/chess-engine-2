import time

from bitboard import WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING
from board import Board, Move
from movegen import legal_moves
from evaluate import evaluate, PIECE_VALUES

MATE_SCORE = 1_000_000
INF = 10_000_000

EXACT, LOWER, UPPER = 0, 1, 2


class SearchStats:
    __slots__ = ("nodes", "start_time", "qnodes")

    def __init__(self):
        self.nodes = 0
        self.qnodes = 0
        self.start_time = time.perf_counter()

    def elapsed(self) -> float:
        return time.perf_counter() - self.start_time

    def nps(self) -> float:
        e = self.elapsed()
        return (self.nodes + self.qnodes) / e if e > 0 else 0.0


class Engine:
    """Iterative-deepening negamax + alpha-beta search with a transposition
    table and MVV-LVA move ordering."""

    def __init__(self, tt_size: int = 1 << 20):
        self.tt = {}
        self.tt_size = tt_size
        self.killers = {}  # depth -> [move, move]  (quiet moves that caused a beta cutoff)
        self.stats = SearchStats()

    def _order_moves(self, board: Board, moves, tt_move, depth):
        killers = self.killers.get(depth, (None, None))

        def score(m: Move):
            if tt_move is not None and m == tt_move:
                return 1_000_000
            if m.captured is not None:
                victim = PIECE_VALUES[m.captured]
                attacker = PIECE_VALUES[m.piece]
                return 100_000 + victim * 10 - attacker
            if m == killers[0] or m == killers[1]:
                return 90_000
            return 0

        return sorted(moves, key=score, reverse=True)

    def quiescence(self, board: Board, alpha: int, beta: int) -> int:
        self.stats.qnodes += 1
        stand_pat = evaluate(board) * (1 if board.side == WHITE else -1)
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        moves = [m for m in legal_moves(board) if m.captured is not None]
        moves = self._order_moves(board, moves, None, -1)
        for m in moves:
            board.make_move(m)
            score = -self.quiescence(board, -beta, -alpha)
            board.unmake_move(m)
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha

    def negamax(self, board: Board, depth: int, alpha: int, beta: int, ply: int) -> int:
        self.stats.nodes += 1
        alpha_orig = alpha

        key = board.zobrist
        tt_entry = self.tt.get(key)
        tt_move = None
        if tt_entry is not None:
            e_depth, e_score, e_flag, e_move = tt_entry
            tt_move = e_move
            if e_depth >= depth:
                if e_flag == EXACT:
                    return e_score
                elif e_flag == LOWER:
                    alpha = max(alpha, e_score)
                elif e_flag == UPPER:
                    beta = min(beta, e_score)
                if alpha >= beta:
                    return e_score

        moves = legal_moves(board)
        if not moves:
            if board.in_check():
                return -MATE_SCORE + ply  # checkmated; prefer slower mates less
            return 0  # stalemate

        if depth == 0:
            return self.quiescence(board, alpha, beta)

        moves = self._order_moves(board, moves, tt_move, depth)
        best_score = -INF
        best_move = None

        for m in moves:
            board.make_move(m)
            score = -self.negamax(board, depth - 1, -beta, -alpha, ply + 1)
            board.unmake_move(m)

            if score > best_score:
                best_score = score
                best_move = m
            if best_score > alpha:
                alpha = best_score
            if alpha >= beta:
                if m.captured is None:
                    k = self.killers.setdefault(depth, [None, None])
                    if k[0] != m:
                        k[1] = k[0]
                        k[0] = m
                break

        flag = EXACT
        if best_score <= alpha_orig:
            flag = UPPER
        elif best_score >= beta:
            flag = LOWER
        if len(self.tt) < self.tt_size:
            self.tt[key] = (depth, best_score, flag, best_move)

        return best_score

    def search(self, board: Board, max_depth: int, time_limit: float = None):
        """Iterative deepening. Returns (best_move, score, stats)."""
        self.stats = SearchStats()
        best_move = None
        best_score = 0

        for depth in range(1, max_depth + 1):
            alpha, beta = -INF, INF
            moves = legal_moves(board)
            if not moves:
                break
            moves = self._order_moves(board, moves, best_move, depth)

            cur_best_score = -INF
            cur_best_move = moves[0]
            for m in moves:
                board.make_move(m)
                score = -self.negamax(board, depth - 1, -beta, -alpha, 1)
                board.unmake_move(m)
                if score > cur_best_score:
                    cur_best_score = score
                    cur_best_move = m
                if cur_best_score > alpha:
                    alpha = cur_best_score

            best_move, best_score = cur_best_move, cur_best_score

            if time_limit is not None and self.stats.elapsed() > time_limit:
                break
            if abs(best_score) > MATE_SCORE - 1000:
                break

        return best_move, best_score, self.stats
