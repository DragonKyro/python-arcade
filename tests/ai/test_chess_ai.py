"""Tests for Chess AI module."""

import random
import pytest

from ai.chess_ai import (
    initial_board, initial_castling_rights,
    get_all_legal_moves, is_in_check, is_checkmate, is_stalemate,
    apply_move, ChessAI,
)


# ---------------------------------------------------------------------------
# get_all_legal_moves
# ---------------------------------------------------------------------------

class TestGetAllLegalMoves:
    def test_starting_position_white_has_20_moves(self):
        board = initial_board()
        castling = initial_castling_rights()
        moves = get_all_legal_moves(board, 'white', castling)
        # 16 pawn moves (8 single + 8 double) + 4 knight moves = 20
        assert len(moves) == 20

    def test_starting_position_black_has_20_moves(self):
        board = initial_board()
        castling = initial_castling_rights()
        moves = get_all_legal_moves(board, 'black', castling)
        assert len(moves) == 20

    def test_no_legal_moves_when_checkmated(self):
        # Scholar's mate position
        board = [[None] * 8 for _ in range(8)]
        board[0] = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']
        board[1] = ['p', 'p', 'p', 'p', None, 'p', 'p', 'p']
        board[3] = [None, None, None, None, 'p', None, None, None]
        board[4] = [None, None, None, None, None, None, 'P', None]
        # White queen on h5 (row 3, col 7) and bishop on c4 (row 4, col 2)
        board[3][7] = 'Q'
        board[4][2] = 'B'
        # White needs to be in a proper state too
        board[6] = ['P', 'P', 'P', 'P', 'P', 'P', None, 'P']
        board[7] = ['R', 'N', 'B', None, 'K', None, 'N', 'R']
        # Actually let me set up a proper scholar's mate
        # After 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6?? 4.Qxf7#
        board2 = [[None] * 8 for _ in range(8)]
        board2[0] = ['r', None, 'b', 'q', 'k', 'b', None, 'r']
        board2[1] = ['p', 'p', 'p', 'p', None, 'Q', 'p', 'p']
        board2[2] = [None, None, 'n', None, None, 'n', None, None]
        board2[3] = [None, None, None, None, 'p', None, None, None]
        board2[4] = [None, None, 'B', None, 'P', None, None, None]
        board2[6] = ['P', 'P', 'P', 'P', None, 'P', 'P', 'P']
        board2[7] = ['R', 'N', 'B', None, 'K', None, 'N', 'R']
        moves = get_all_legal_moves(board2, 'black')
        assert len(moves) == 0


# ---------------------------------------------------------------------------
# is_in_check
# ---------------------------------------------------------------------------

class TestIsInCheck:
    def test_not_in_check_starting_position(self):
        board = initial_board()
        assert is_in_check(board, 'white') is False
        assert is_in_check(board, 'black') is False

    def test_king_in_check_by_rook(self):
        board = [[None] * 8 for _ in range(8)]
        board[0][4] = 'k'
        board[0][0] = 'R'  # White rook attacking black king
        assert is_in_check(board, 'black') is True

    def test_king_in_check_by_knight(self):
        board = [[None] * 8 for _ in range(8)]
        board[4][4] = 'K'
        board[2][3] = 'n'  # Black knight attacking white king
        assert is_in_check(board, 'white') is True

    def test_king_not_in_check_blocked_by_piece(self):
        board = [[None] * 8 for _ in range(8)]
        board[7][4] = 'K'
        board[0][4] = 'r'  # Black rook on same file
        board[3][4] = 'P'  # But blocked by white pawn
        assert is_in_check(board, 'white') is False


# ---------------------------------------------------------------------------
# is_checkmate
# ---------------------------------------------------------------------------

class TestIsCheckmate:
    def test_scholars_mate(self):
        board = [[None] * 8 for _ in range(8)]
        board[0] = ['r', None, 'b', 'q', 'k', 'b', None, 'r']
        board[1] = ['p', 'p', 'p', 'p', None, 'Q', 'p', 'p']
        board[2] = [None, None, 'n', None, None, 'n', None, None]
        board[3] = [None, None, None, None, 'p', None, None, None]
        board[4] = [None, None, 'B', None, 'P', None, None, None]
        board[6] = ['P', 'P', 'P', 'P', None, 'P', 'P', 'P']
        board[7] = ['R', 'N', 'B', None, 'K', None, 'N', 'R']
        assert is_checkmate(board, 'black') is True

    def test_not_checkmate_starting_position(self):
        board = initial_board()
        assert is_checkmate(board, 'white') is False
        assert is_checkmate(board, 'black') is False


# ---------------------------------------------------------------------------
# is_stalemate
# ---------------------------------------------------------------------------

class TestIsStalemate:
    def test_basic_stalemate(self):
        """King in corner with no legal moves but not in check."""
        board = [[None] * 8 for _ in range(8)]
        board[0][0] = 'k'  # Black king in corner
        board[1][2] = 'Q'  # White queen covers b8, a7
        board[2][1] = 'K'  # White king covers a7, b7, b6
        # Black king at a8: can go to a7 (attacked by Q and K), b8 (attacked by Q), b7 (attacked by K)
        assert is_stalemate(board, 'black') is True

    def test_not_stalemate_when_in_check(self):
        board = [[None] * 8 for _ in range(8)]
        board[0][0] = 'k'
        board[0][7] = 'R'  # Rook gives check
        board[2][1] = 'K'
        assert is_stalemate(board, 'black') is False

    def test_not_stalemate_starting_position(self):
        board = initial_board()
        assert is_stalemate(board, 'white') is False


# ---------------------------------------------------------------------------
# apply_move
# ---------------------------------------------------------------------------

class TestApplyMove:
    def test_pawn_move(self):
        board = initial_board()
        castling = initial_castling_rights()
        # e2-e4: pawn from (6,4) to (4,4)
        move = (6, 4, 4, 4, None)
        new_board, new_castling, new_ep, captured = apply_move(board, move, castling)
        assert new_board[4][4] == 'P'
        assert new_board[6][4] is None
        assert captured is None
        # En passant target should be set
        assert new_ep == (5, 4)

    def test_capture(self):
        board = [[None] * 8 for _ in range(8)]
        board[4][4] = 'P'
        board[3][5] = 'p'  # Black pawn to capture
        board[7][4] = 'K'
        board[0][4] = 'k'
        castling = {'K': False, 'Q': False, 'k': False, 'q': False}
        move = (4, 4, 3, 5, None)  # Pawn captures
        new_board, _, _, captured = apply_move(board, move, castling)
        assert new_board[3][5] == 'P'
        assert new_board[4][4] is None
        assert captured == 'p'

    def test_kingside_castling(self):
        board = [[None] * 8 for _ in range(8)]
        board[7][4] = 'K'
        board[7][7] = 'R'
        board[0][4] = 'k'
        castling = {'K': True, 'Q': False, 'k': False, 'q': False}
        move = (7, 4, 7, 6, None)  # Kingside castle
        new_board, new_castling, _, _ = apply_move(board, move, castling)
        assert new_board[7][6] == 'K'
        assert new_board[7][5] == 'R'
        assert new_board[7][4] is None
        assert new_board[7][7] is None
        assert new_castling['K'] is False
        assert new_castling['Q'] is False

    def test_queenside_castling(self):
        board = [[None] * 8 for _ in range(8)]
        board[7][4] = 'K'
        board[7][0] = 'R'
        board[0][4] = 'k'
        castling = {'K': False, 'Q': True, 'k': False, 'q': False}
        move = (7, 4, 7, 2, None)
        new_board, _, _, _ = apply_move(board, move, castling)
        assert new_board[7][2] == 'K'
        assert new_board[7][3] == 'R'
        assert new_board[7][4] is None
        assert new_board[7][0] is None


# ---------------------------------------------------------------------------
# ChessAI returns valid move
# ---------------------------------------------------------------------------

class TestChessAIMove:
    def test_ai_returns_valid_move_starting_position(self):
        board = initial_board()
        castling = initial_castling_rights()
        ai = ChessAI(depth=2)
        result = ai.get_move(board, 'white', castling)
        assert result is not None
        (fr, fc), (tr, tc), promo = result
        legal = get_all_legal_moves(board, 'white', castling)
        legal_tuples = [((m[0], m[1]), (m[2], m[3]), m[4]) for m in legal]
        assert ((fr, fc), (tr, tc), promo) in legal_tuples

    def test_ai_takes_free_piece(self):
        """AI should capture a hanging queen."""
        board = [[None] * 8 for _ in range(8)]
        board[7][4] = 'K'
        board[0][4] = 'k'
        board[4][4] = 'R'  # White rook
        board[4][7] = 'q'  # Unprotected black queen on same rank
        castling = {'K': False, 'Q': False, 'k': False, 'q': False}
        ai = ChessAI(depth=2)
        result = ai.get_move(board, 'white', castling)
        assert result is not None
        (fr, fc), (tr, tc), promo = result
        # Should capture the queen
        assert (tr, tc) == (4, 7)

    def test_ai_returns_none_when_no_moves(self):
        """When checkmated, AI returns None."""
        board = [[None] * 8 for _ in range(8)]
        board[0] = ['r', None, 'b', 'q', 'k', 'b', None, 'r']
        board[1] = ['p', 'p', 'p', 'p', None, 'Q', 'p', 'p']
        board[2] = [None, None, 'n', None, None, 'n', None, None]
        board[3] = [None, None, None, None, 'p', None, None, None]
        board[4] = [None, None, 'B', None, 'P', None, None, None]
        board[6] = ['P', 'P', 'P', 'P', None, 'P', 'P', 'P']
        board[7] = ['R', 'N', 'B', None, 'K', None, 'N', 'R']
        ai = ChessAI(depth=2)
        result = ai.get_move(board, 'black')
        assert result is None
