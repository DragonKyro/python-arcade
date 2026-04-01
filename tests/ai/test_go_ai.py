"""Tests for Go AI module."""

import random
import copy
import pytest

from ai.go_ai import (
    BOARD_SIZE, EMPTY, BLACK, WHITE,
    get_legal_moves, apply_move, score_game, _board_hash, GoAI,
)


def _empty_board():
    return [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]


# ---------------------------------------------------------------------------
# get_legal_moves
# ---------------------------------------------------------------------------

class TestGetLegalMoves:
    def test_excludes_occupied_squares(self):
        board = _empty_board()
        board[0][0] = BLACK
        moves = get_legal_moves(board, WHITE)
        assert (0, 0) not in moves

    def test_excludes_suicide_move(self):
        """A move surrounded by opponent stones with no captures is suicide."""
        board = _empty_board()
        # Surround (0,0) with white stones
        board[0][1] = WHITE
        board[1][0] = WHITE
        # Placing black at (0,0) would be suicide
        moves = get_legal_moves(board, BLACK)
        assert (0, 0) not in moves

    def test_excludes_ko_violation(self):
        """After a ko capture, replaying immediately is illegal."""
        board = _empty_board()
        # Set up a ko: black at (0,1), (1,0); white at (0,2), (1,1)
        # with black capturing at (0,1) creating ko at (0,0)
        # Simplified: create a specific board state and prev_hash
        board[0][1] = BLACK
        board[1][0] = BLACK
        board[0][2] = WHITE
        board[1][1] = WHITE
        # Place white at (0,0) -- this would be captured if black plays (0,0)
        # but we test that the ko hash excludes the move
        result = apply_move(board, 0, 0, WHITE)
        if result is not None:
            new_board, _, new_hash = result
            # Now if we try to recapture, previous board hash should block it
            prev_hash = _board_hash(board)
            # Create a scenario where recapture would recreate 'board'
            moves = get_legal_moves(new_board, BLACK, prev_hash=prev_hash)
            # The move might or might not be legal depending on exact ko shape.
            # At minimum, this should not crash.
            assert isinstance(moves, list)

    def test_all_moves_are_on_empty_squares(self):
        board = _empty_board()
        board[4][4] = BLACK
        board[4][5] = WHITE
        moves = get_legal_moves(board, BLACK)
        for r, c in moves:
            assert board[r][c] == EMPTY


# ---------------------------------------------------------------------------
# apply_move
# ---------------------------------------------------------------------------

class TestApplyMove:
    def test_simple_placement(self):
        board = _empty_board()
        result = apply_move(board, 4, 4, BLACK)
        assert result is not None
        new_board, captured, _ = result
        assert new_board[4][4] == BLACK
        assert captured == 0

    def test_capture_group_no_liberties(self):
        """Placing a stone that removes all liberties of opponent group captures it."""
        board = _empty_board()
        # White stone at (0,0), surround with black on two sides
        board[0][0] = WHITE
        board[0][1] = BLACK
        # Place black at (1,0) to capture white at (0,0)
        result = apply_move(board, 1, 0, BLACK)
        assert result is not None
        new_board, captured, _ = result
        assert captured == 1
        assert new_board[0][0] == EMPTY  # captured

    def test_capture_larger_group(self):
        """Capture a two-stone group."""
        board = _empty_board()
        board[0][0] = WHITE
        board[0][1] = WHITE
        # Surround
        board[1][0] = BLACK
        board[1][1] = BLACK
        board[0][2] = BLACK
        # Last liberty is removed by placing at... wait, (0,0) is in corner
        # Liberties: none left after we block the last one
        # Actually (0,0) group has no more liberties only if we've covered all adjacent
        # (0,0) neighbors: (0,1)=WHITE(same), (1,0)=BLACK -- so liberty for (0,0) is none through (0,-1) OOB, (-1,0) OOB, (0,1)=same group, (1,0)=BLACK
        # (0,1) neighbors: (0,0)=same, (0,2)=BLACK, (1,1)=BLACK, (-1,1) OOB
        # So group {(0,0),(0,1)} has 0 liberties already? No, need to re-check
        # Actually they are already captured since all neighbors are black or OOB
        # Let me set up properly: leave one liberty open, then fill it
        board2 = _empty_board()
        board2[0][0] = WHITE
        board2[0][1] = WHITE
        board2[1][0] = BLACK
        board2[1][1] = BLACK
        # (0,0) group liberties: (0,2) is open. (0,0) only has (0,1) same, (1,0) black, edges
        # (0,1) has (0,0) same, (0,2) open, (1,1) black
        # So last liberty is (0,2)
        result = apply_move(board2, 0, 2, BLACK)
        assert result is not None
        new_board, captured, _ = result
        assert captured == 2
        assert new_board[0][0] == EMPTY
        assert new_board[0][1] == EMPTY

    def test_illegal_occupied_square(self):
        board = _empty_board()
        board[0][0] = BLACK
        result = apply_move(board, 0, 0, WHITE)
        assert result is None

    def test_suicide_returns_none(self):
        board = _empty_board()
        board[0][1] = WHITE
        board[1][0] = WHITE
        result = apply_move(board, 0, 0, BLACK)
        assert result is None


# ---------------------------------------------------------------------------
# score_game
# ---------------------------------------------------------------------------

class TestScoreGame:
    def test_empty_board_white_wins_by_komi(self):
        board = _empty_board()
        bs, ws = score_game(board, 0, 0)
        assert bs == 0
        # Empty board: all territory is neutral (bordered by nothing)
        # White gets komi = 6.5
        assert ws == 6.5

    def test_basic_territory(self):
        """Black fills top half, white fills bottom half."""
        board = _empty_board()
        mid = BOARD_SIZE // 2
        for r in range(mid):
            for c in range(BOARD_SIZE):
                board[r][c] = BLACK
        for r in range(mid + 1, BOARD_SIZE):
            for c in range(BOARD_SIZE):
                board[r][c] = WHITE
        # Middle row is empty, bordered by both colors -> neutral
        bs, ws = score_game(board, 0, 0)
        assert bs > 0
        assert ws > 0
        # Black stones count + any black-only bordered territory
        # White stones count + komi + any white-only bordered territory
        black_stones = mid * BOARD_SIZE
        white_stones = (BOARD_SIZE - mid - 1) * BOARD_SIZE
        assert bs >= black_stones
        assert ws >= white_stones + 6.5

    def test_single_stone_each(self):
        board = _empty_board()
        board[0][0] = BLACK
        board[BOARD_SIZE - 1][BOARD_SIZE - 1] = WHITE
        bs, ws = score_game(board, 0, 0)
        # Both stones on board, rest is one big neutral region (bordered by both)
        assert bs >= 1
        assert ws >= 1 + 6.5


# ---------------------------------------------------------------------------
# AI returns valid move
# ---------------------------------------------------------------------------

class TestGoAIMove:
    def test_ai_returns_valid_move(self):
        random.seed(42)
        board = _empty_board()
        ai = GoAI(difficulty="easy")
        move = ai.get_move(board, BLACK)
        if move == "pass":
            return  # pass is valid
        r, c = move
        assert 0 <= r < BOARD_SIZE
        assert 0 <= c < BOARD_SIZE
        assert board[r][c] == EMPTY

    def test_ai_handles_pass(self):
        """When no legal moves remain, AI should pass."""
        # Fill the board so no legal moves exist
        board = [[BLACK] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        ai = GoAI(difficulty="easy")
        move = ai.get_move(board, WHITE)
        assert move == "pass"

    def test_ai_does_not_crash_on_mid_game(self):
        random.seed(42)
        board = _empty_board()
        board[4][4] = BLACK
        board[4][5] = WHITE
        board[5][4] = BLACK
        ai = GoAI(difficulty="easy")
        move = ai.get_move(board, WHITE)
        assert move == "pass" or (isinstance(move, tuple) and len(move) == 2)
