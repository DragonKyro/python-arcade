"""Integration tests for Connect Four: full game simulations using the AI module."""

import random

from ai.connect4_ai import (
    ROWS,
    COLS,
    EMPTY,
    PLAYER_PIECE,
    AI_PIECE,
    Connect4AI,
    check_winner,
    get_valid_columns,
    get_next_open_row,
    drop_piece,
)


def _empty_board():
    return [[EMPTY] * COLS for _ in range(ROWS)]


def _play_game_ai_vs_random(rng, ai_depth=3):
    """Play a full game: PLAYER = random, AI = minimax. Returns the result."""
    board = _empty_board()
    ai = Connect4AI()
    # Monkey-patch depth for speed
    import ai.connect4_ai as c4_module
    original_depth = c4_module.DEPTH_LIMIT
    c4_module.DEPTH_LIMIT = ai_depth

    turn = PLAYER_PIECE  # player goes first
    moves_made = 0
    max_moves = ROWS * COLS  # 42

    try:
        for _ in range(max_moves):
            result = check_winner(board)
            if result is not None:
                return result, moves_made

            valid_cols = get_valid_columns(board)
            assert len(valid_cols) > 0, "No valid columns but game not over"

            if turn == PLAYER_PIECE:
                col = rng.choice(valid_cols)
                row = get_next_open_row(board, col)
                assert row >= 0, f"Column {col} was valid but no open row"
                board = drop_piece(board, row, col, PLAYER_PIECE)
                turn = AI_PIECE
            else:
                col = ai.get_move(board, AI_PIECE, PLAYER_PIECE)
                assert col in valid_cols, (
                    f"AI chose column {col} which is not valid. Valid: {valid_cols}"
                )
                row = get_next_open_row(board, col)
                assert row >= 0, f"AI column {col} has no open row"
                board = drop_piece(board, row, col, AI_PIECE)
                turn = PLAYER_PIECE

            moves_made += 1

        result = check_winner(board)
        assert result is not None, "Game did not terminate after filling the board"
        return result, moves_made
    finally:
        c4_module.DEPTH_LIMIT = original_depth


def test_ai_vs_random_20_games():
    """AI vs random over 20 games: all games must terminate with valid results."""
    rng = random.Random(42)
    results = {PLAYER_PIECE: 0, AI_PIECE: 0, "draw": 0}

    for i in range(20):
        result, moves = _play_game_ai_vs_random(rng, ai_depth=3)
        assert result in (PLAYER_PIECE, AI_PIECE, "draw"), (
            f"Game {i}: unexpected result {result}"
        )
        results[result] += 1
        # Verify game terminates in a reasonable number of moves
        assert moves <= ROWS * COLS, f"Game {i}: too many moves ({moves})"

    # AI with depth-3 should win most games against random
    assert results[AI_PIECE] > results[PLAYER_PIECE], (
        f"AI should win more than random. Results: {results}"
    )


def test_no_invalid_moves():
    """Verify AI never picks a full column or out-of-bounds column."""
    rng = random.Random(99)
    board = _empty_board()
    ai = Connect4AI()

    import ai.connect4_ai as c4_module
    original_depth = c4_module.DEPTH_LIMIT
    c4_module.DEPTH_LIMIT = 3

    try:
        turn = AI_PIECE
        for _ in range(ROWS * COLS):
            result = check_winner(board)
            if result is not None:
                break

            valid_cols = get_valid_columns(board)
            if not valid_cols:
                break

            if turn == AI_PIECE:
                col = ai.get_move(board, AI_PIECE, PLAYER_PIECE)
                assert 0 <= col < COLS, f"AI column {col} out of bounds"
                assert col in valid_cols, f"AI picked full column {col}"
                row = get_next_open_row(board, col)
                board = drop_piece(board, row, col, AI_PIECE)
                turn = PLAYER_PIECE
            else:
                col = rng.choice(valid_cols)
                row = get_next_open_row(board, col)
                board = drop_piece(board, row, col, PLAYER_PIECE)
                turn = AI_PIECE
    finally:
        c4_module.DEPTH_LIMIT = original_depth


def test_ai_vs_ai():
    """Two AIs playing each other should produce a valid game."""
    board = _empty_board()
    ai = Connect4AI()

    import ai.connect4_ai as c4_module
    original_depth = c4_module.DEPTH_LIMIT
    c4_module.DEPTH_LIMIT = 3

    try:
        turn = AI_PIECE
        for move_num in range(ROWS * COLS):
            result = check_winner(board)
            if result is not None:
                assert result in (PLAYER_PIECE, AI_PIECE, "draw"), (
                    f"Invalid result: {result}"
                )
                return

            valid_cols = get_valid_columns(board)
            if not valid_cols:
                break

            if turn == AI_PIECE:
                col = ai.get_move(board, AI_PIECE, PLAYER_PIECE)
                row = get_next_open_row(board, col)
                board = drop_piece(board, row, col, AI_PIECE)
                turn = PLAYER_PIECE
            else:
                col = ai.get_move(board, PLAYER_PIECE, AI_PIECE)
                row = get_next_open_row(board, col)
                board = drop_piece(board, row, col, PLAYER_PIECE)
                turn = AI_PIECE

        result = check_winner(board)
        assert result is not None, "Board full but no result"
        assert result in (PLAYER_PIECE, AI_PIECE, "draw")
    finally:
        c4_module.DEPTH_LIMIT = original_depth


def test_winner_detection_correctness():
    """Verify that check_winner correctly identifies winners."""
    # Horizontal win for AI
    board = _empty_board()
    for c in range(4):
        board[ROWS - 1][c] = AI_PIECE
    assert check_winner(board) == AI_PIECE

    # Vertical win for player
    board = _empty_board()
    for r in range(ROWS - 4, ROWS):
        board[r][0] = PLAYER_PIECE
    assert check_winner(board) == PLAYER_PIECE

    # No winner on empty board
    board = _empty_board()
    assert check_winner(board) is None
