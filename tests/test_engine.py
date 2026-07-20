import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from board import Board, START_FEN
from movegen import legal_moves
from perft import perft
from search import Engine


class TestPerft(unittest.TestCase):
    def test_startpos_depth3(self):
        board = Board(START_FEN)
        self.assertEqual(perft(board, 1), 20)
        self.assertEqual(perft(board, 2), 400)
        self.assertEqual(perft(board, 3), 8902)

    def test_kiwipete_depth2(self):
        fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
        board = Board(fen)
        self.assertEqual(perft(board, 1), 48)
        self.assertEqual(perft(board, 2), 2039)


class TestMoveGen(unittest.TestCase):
    def test_startpos_move_count(self):
        board = Board(START_FEN)
        self.assertEqual(len(legal_moves(board)), 20)

    def test_castling_available(self):
        fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
        board = Board(fen)
        moves = {m.uci() for m in legal_moves(board)}
        self.assertIn("e1g1", moves)  # kingside castle
        self.assertIn("e1c1", moves)  # queenside castle

    def test_no_castle_through_check(self):
        # Black rook on e8-e-file style check isn't relevant; use a rook
        # attacking f1 so white can't castle kingside (king would pass
        # through an attacked square).
        fen = "4k3/8/8/8/8/8/8/R3K2r w Q - 0 1"
        board = Board(fen)
        moves = {m.uci() for m in legal_moves(board)}
        self.assertNotIn("e1g1", moves)

    def test_en_passant(self):
        board = Board("rnbqkbnr/pppp1ppp/8/8/3Pp3/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1")
        moves = {m.uci() for m in legal_moves(board)}
        self.assertIn("e4d3", moves)

    def test_promotion(self):
        board = Board("8/P7/8/8/8/8/8/k1K5 w - - 0 1")
        moves = {m.uci() for m in legal_moves(board)}
        self.assertIn("a7a8q", moves)
        self.assertIn("a7a8n", moves)


class TestSearch(unittest.TestCase):
    def test_finds_mate_in_one(self):
        board = Board("6k1/5ppp/8/8/8/8/8/3Q2K1 w - - 0 1")
        engine = Engine()
        move, score, stats = engine.search(board, max_depth=3)
        self.assertEqual(move.uci(), "d1d8")
        self.assertGreater(score, 900_000)

    def test_prefers_free_material(self):
        # White rook on a1 can capture a hanging bishop on a2 for free.
        board = Board("4k3/8/8/8/8/8/b7/R3K3 w Q - 0 1")
        engine = Engine()
        move, score, stats = engine.search(board, max_depth=2)
        self.assertEqual(move.uci(), "a1a2")


if __name__ == "__main__":
    unittest.main()
