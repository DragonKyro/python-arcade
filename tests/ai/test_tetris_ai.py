"""Tests for ai.tetris_ai module."""

import pytest
from ai.tetris_ai import TetrisAI, get_all_placements, TETROMINOES, BOARD_COLS, BOARD_ROWS


def empty_board():
    return [[None] * BOARD_COLS for _ in range(BOARD_ROWS)]


@pytest.fixture(params=['easy', 'medium', 'hard'])
def ai(request):
    return TetrisAI(difficulty=request.param)


class TestGetPlacement:
    def test_returns_column_and_rotation(self, ai):
        board = empty_board()
        result = ai.get_placement(board, 'T')
        assert result is not None
        col, rotation = result
        assert isinstance(col, int)
        assert isinstance(rotation, int)
        assert 0 <= rotation < 4

    def test_column_within_bounds(self, ai):
        board = empty_board()
        for piece in TETROMINOES:
            result = ai.get_placement(board, piece)
            if result is not None:
                col, rotation = result
                shape = TETROMINOES[piece][rotation]
                for dr, dc in shape:
                    assert 0 <= col + dc < BOARD_COLS

    def test_returns_none_for_full_board(self, ai):
        board = [[(200, 200, 200)] * BOARD_COLS for _ in range(BOARD_ROWS)]
        result = ai.get_placement(board, 'O')
        assert result is None

    @pytest.mark.parametrize("piece", list(TETROMINOES.keys()))
    def test_each_piece_on_empty_board(self, ai, piece):
        board = empty_board()
        result = ai.get_placement(board, piece)
        assert result is not None


class TestGetAllPlacements:
    @pytest.mark.parametrize("piece", list(TETROMINOES.keys()))
    def test_nonempty_for_each_piece(self, piece):
        board = empty_board()
        placements = get_all_placements(board, piece)
        assert len(placements) > 0

    def test_placement_structure(self):
        board = empty_board()
        placements = get_all_placements(board, 'I')
        for col, rotation, resulting_board, lines_cleared in placements:
            assert isinstance(col, int)
            assert isinstance(rotation, int)
            assert isinstance(lines_cleared, int)
            assert len(resulting_board) == BOARD_ROWS
            assert len(resulting_board[0]) == BOARD_COLS

    def test_o_piece_has_one_rotation(self):
        board = empty_board()
        placements = get_all_placements(board, 'O')
        rotations_used = set(rot for _, rot, _, _ in placements)
        assert rotations_used == {0}

    def test_no_placements_on_full_board(self):
        board = [[(200, 200, 200)] * BOARD_COLS for _ in range(BOARD_ROWS)]
        placements = get_all_placements(board, 'T')
        assert len(placements) == 0


class TestAIDoesNotCrash:
    def test_with_partially_filled_board(self, ai):
        board = empty_board()
        # Fill bottom 2 rows partially
        for c in range(0, BOARD_COLS, 2):
            board[0][c] = (100, 100, 100)
            board[1][c] = (100, 100, 100)
        result = ai.get_placement(board, 'T')
        assert result is not None

    def test_with_next_piece_hard(self):
        ai = TetrisAI('hard')
        board = empty_board()
        result = ai.get_placement(board, 'T', next_piece='I')
        assert result is not None

    def test_tick_rate_property(self):
        for diff in ('easy', 'medium', 'hard'):
            ai = TetrisAI(diff)
            assert isinstance(ai.tick_rate, float)
