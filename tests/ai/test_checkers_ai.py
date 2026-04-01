"""Tests for Checkers AI module."""

import pytest

from ai.checkers_ai import (
    EMPTY, RED, BLACK, RED_KING, BLACK_KING,
    initial_board, get_all_moves, apply_move, get_captures,
    check_winner, count_pieces, _promote_if_needed, CheckersAI,
)


# ---------- initial_board tests ----------

class TestInitialBoard:
    def test_correct_piece_count(self):
        board = initial_board()
        red, black = count_pieces(board)
        assert red == 12
        assert black == 12

    def test_black_in_top_rows(self):
        board = initial_board()
        for r in range(3):
            for c in range(8):
                if (r + c) % 2 == 1:
                    assert board[r][c] == BLACK
                else:
                    assert board[r][c] == EMPTY

    def test_red_in_bottom_rows(self):
        board = initial_board()
        for r in range(5, 8):
            for c in range(8):
                if (r + c) % 2 == 1:
                    assert board[r][c] == RED
                else:
                    assert board[r][c] == EMPTY

    def test_middle_rows_empty(self):
        board = initial_board()
        for r in range(3, 5):
            for c in range(8):
                assert board[r][c] == EMPTY


# ---------- get_all_moves tests ----------

class TestGetAllMoves:
    def test_initial_red_moves(self):
        board = initial_board()
        moves = get_all_moves(board, RED)
        # Red pieces in row 5 can move up (row 4); 4 pieces have 2 diag options
        # except edge pieces which have 1
        assert len(moves) > 0
        # All moves should be simple (length 2)
        for m in moves:
            assert len(m) == 2

    def test_initial_black_moves(self):
        board = initial_board()
        moves = get_all_moves(board, BLACK)
        assert len(moves) > 0

    def test_mandatory_capture_enforced(self):
        """When captures are available, simple moves should not be returned."""
        board = [[EMPTY] * 8 for _ in range(8)]
        board[4][3] = RED
        board[3][4] = BLACK  # can be jumped by red
        # Red can jump from (4,3) over (3,4) to (2,5)
        moves = get_all_moves(board, RED)
        # All returned moves must be captures (length > 2)
        assert len(moves) > 0
        for m in moves:
            assert len(m) > 2 or (abs(m[1][0] - m[0][0]) == 2)

    def test_no_moves_returns_empty(self):
        board = [[EMPTY] * 8 for _ in range(8)]
        board[0][1] = RED  # Red at top corner, no forward moves (row -1)
        moves = get_all_moves(board, RED)
        assert moves == []


# ---------- apply_move tests ----------

class TestApplyMove:
    def test_simple_move(self):
        board = [[EMPTY] * 8 for _ in range(8)]
        board[4][3] = RED
        move = [(4, 3), (3, 4)]
        new_board = apply_move(board, move)
        assert new_board[4][3] == EMPTY
        assert new_board[3][4] == RED

    def test_capture_removes_jumped_piece(self):
        board = [[EMPTY] * 8 for _ in range(8)]
        board[4][3] = RED
        board[3][4] = BLACK
        move = [(4, 3), (2, 5)]
        new_board = apply_move(board, move)
        assert new_board[4][3] == EMPTY
        assert new_board[3][4] == EMPTY  # captured
        assert new_board[2][5] == RED

    def test_does_not_mutate_original(self):
        board = [[EMPTY] * 8 for _ in range(8)]
        board[4][3] = RED
        apply_move(board, [(4, 3), (3, 4)])
        assert board[4][3] == RED  # unchanged

    def test_king_promotion_on_move(self):
        board = [[EMPTY] * 8 for _ in range(8)]
        board[1][0] = RED  # Red moving to row 0 should promote
        move = [(1, 0), (0, 1)]
        new_board = apply_move(board, move)
        assert new_board[0][1] == RED_KING

    def test_black_king_promotion(self):
        board = [[EMPTY] * 8 for _ in range(8)]
        board[6][1] = BLACK
        move = [(6, 1), (7, 0)]
        new_board = apply_move(board, move)
        assert new_board[7][0] == BLACK_KING


# ---------- get_captures tests ----------

class TestGetCaptures:
    def test_single_jump(self):
        board = [[EMPTY] * 8 for _ in range(8)]
        board[4][3] = RED
        board[3][4] = BLACK
        captures = get_captures(board, 4, 3)
        assert len(captures) >= 1
        # Each capture path should start at (4,3) and land at (2,5)
        for path in captures:
            assert path[0] == (4, 3)
            assert path[-1] == (2, 5)

    def test_multi_jump_chain(self):
        board = [[EMPTY] * 8 for _ in range(8)]
        board[6][1] = RED
        board[5][2] = BLACK
        board[3][4] = BLACK
        # Red jumps (6,1)->(4,3)->(2,5)
        captures = get_captures(board, 6, 1)
        assert len(captures) >= 1
        # Find the multi-jump path
        multi = [p for p in captures if len(p) == 3]
        assert len(multi) >= 1
        assert multi[0] == [(6, 1), (4, 3), (2, 5)]

    def test_no_captures_available(self):
        board = [[EMPTY] * 8 for _ in range(8)]
        board[4][3] = RED
        captures = get_captures(board, 4, 3)
        assert captures == []

    def test_empty_square_returns_empty(self):
        board = [[EMPTY] * 8 for _ in range(8)]
        assert get_captures(board, 4, 3) == []


# ---------- king promotion helper ----------

class TestPromoteIfNeeded:
    def test_red_promotes_at_row_0(self):
        assert _promote_if_needed(RED, 0) == RED_KING

    def test_red_no_promote_mid_board(self):
        assert _promote_if_needed(RED, 4) == RED

    def test_black_promotes_at_row_7(self):
        assert _promote_if_needed(BLACK, 7) == BLACK_KING

    def test_black_no_promote_mid_board(self):
        assert _promote_if_needed(BLACK, 3) == BLACK

    def test_king_stays_king(self):
        assert _promote_if_needed(RED_KING, 5) == RED_KING
        assert _promote_if_needed(BLACK_KING, 2) == BLACK_KING


# ---------- AI behaviour tests ----------

class TestCheckersAI:
    def setup_method(self):
        self.ai = CheckersAI(depth=3)

    def test_ai_returns_valid_move(self):
        board = initial_board()
        move = self.ai.get_move(board, BLACK)
        assert move is not None
        all_moves = get_all_moves(board, BLACK)
        assert move in all_moves

    def test_ai_returns_none_when_no_moves(self):
        board = [[EMPTY] * 8 for _ in range(8)]
        # No black pieces
        board[0][1] = RED
        move = self.ai.get_move(board, BLACK)
        assert move is None

    def test_ai_captures_when_available(self):
        """When a capture is available, AI should return a capture move."""
        board = [[EMPTY] * 8 for _ in range(8)]
        board[3][4] = BLACK
        board[4][3] = RED
        # Black can jump over red
        move = self.ai.get_move(board, BLACK)
        assert move is not None
        assert len(move) > 2 or (abs(move[1][0] - move[0][0]) == 2)

    def test_ai_does_not_crash_on_sparse_board(self):
        board = [[EMPTY] * 8 for _ in range(8)]
        board[0][1] = BLACK
        board[7][0] = RED
        move = self.ai.get_move(board, BLACK)
        # Either returns a valid move or None
        if move is not None:
            all_moves = get_all_moves(board, BLACK)
            assert move in all_moves
