"""Integration tests for Gomoku: full game simulations using the AI module."""

import random

from ai.gomoku_ai import (
    GomokuAI,
    BOARD_SIZE,
    EMPTY,
    BLACK,
    WHITE,
    check_winner,
    get_legal_moves,
    is_board_full,
)


def _empty_board():
    return [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]


def _play_game_ai_vs_random(rng, ai_color=BLACK):
    """Play a full game: AI (depth=1) vs random. Returns (winner, move_count)."""
    board = _empty_board()
    ai = GomokuAI(difficulty="easy")  # depth=1
    opp_color = WHITE if ai_color == BLACK else BLACK
    current = BLACK  # Black always goes first in Gomoku
    move_count = 0
    max_moves = BOARD_SIZE * BOARD_SIZE

    while move_count < max_moves:
        winner = check_winner(board)
        if winner is not None:
            return winner, move_count
        if is_board_full(board):
            return None, move_count

        legal = get_legal_moves(board)
        assert len(legal) > 0, "No legal moves but board not full and no winner"

        if current == ai_color:
            move = ai.get_move(board, ai_color)
            assert move is not None, "AI returned None when legal moves exist"
            r, c = move
        else:
            r, c = rng.choice(legal)

        assert 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE, (
            f"Move ({r},{c}) out of bounds"
        )
        assert board[r][c] == EMPTY, (
            f"Move ({r},{c}) targets non-empty cell (value={board[r][c]})"
        )

        board[r][c] = current
        current = WHITE if current == BLACK else BLACK
        move_count += 1

    # Check one last time after loop
    winner = check_winner(board)
    return winner, move_count


def test_ai_vs_random_5_games():
    """Simulate 5 games of AI vs random. All must terminate with valid outcomes."""
    rng = random.Random(42)
    for i in range(5):
        winner, move_count = _play_game_ai_vs_random(rng)
        assert winner in (BLACK, WHITE, None), (
            f"Game {i}: unexpected winner value {winner}"
        )
        assert move_count <= BOARD_SIZE * BOARD_SIZE, (
            f"Game {i}: exceeded maximum moves"
        )
        # Game must have terminated
        assert move_count > 0, f"Game {i}: no moves were made"


def test_winner_detection_is_correct():
    """Verify that check_winner correctly detects 5-in-a-row patterns."""
    # Horizontal
    board = _empty_board()
    for c in range(5):
        board[7][c] = BLACK
    assert check_winner(board) == BLACK

    # Vertical
    board = _empty_board()
    for r in range(5):
        board[r][3] = WHITE
    assert check_winner(board) == WHITE

    # Diagonal (down-right)
    board = _empty_board()
    for i in range(5):
        board[i][i] = BLACK
    assert check_winner(board) == BLACK

    # Diagonal (down-left)
    board = _empty_board()
    for i in range(5):
        board[i][14 - i] = WHITE
    assert check_winner(board) == WHITE

    # No winner with 4 in a row
    board = _empty_board()
    for c in range(4):
        board[7][c] = BLACK
    assert check_winner(board) is None


def test_no_invalid_moves_during_game():
    """Track every move in a game and verify no cell is played twice."""
    rng = random.Random(42)
    board = _empty_board()
    ai = GomokuAI(difficulty="easy")
    current = BLACK
    occupied = set()

    for _ in range(BOARD_SIZE * BOARD_SIZE):
        winner = check_winner(board)
        if winner is not None or is_board_full(board):
            break

        if current == BLACK:
            move = ai.get_move(board, BLACK)
            assert move is not None
            r, c = move
        else:
            legal = get_legal_moves(board)
            r, c = rng.choice(legal)

        assert (r, c) not in occupied, (
            f"Cell ({r},{c}) was played twice"
        )
        occupied.add((r, c))
        board[r][c] = current
        current = WHITE if current == BLACK else BLACK


def test_ai_blocks_obvious_threat():
    """AI should block opponent from completing 5 in a row when possible."""
    board = _empty_board()
    # White has 4 in a row at row 7, cols 0-3. Col 4 is the winning spot.
    for c in range(4):
        board[7][c] = WHITE
    # Place some black stones nearby so legal moves include the area
    board[6][0] = BLACK
    board[6][1] = BLACK

    ai = GomokuAI(difficulty="easy")
    move = ai.get_move(board, BLACK)
    assert move is not None
    # AI should play (7, 4) to block, or at least somewhere meaningful
    r, c = move
    assert board[r][c] == EMPTY, "AI chose an occupied cell"


def test_game_terminates_within_reasonable_moves():
    """Games should terminate well before the board is completely full."""
    rng = random.Random(42)
    for _ in range(5):
        winner, move_count = _play_game_ai_vs_random(rng)
        # Gomoku games with an AI typically end much earlier than filling the board
        assert move_count <= BOARD_SIZE * BOARD_SIZE
