"""Integration tests for Tic-Tac-Toe: full game simulations using the AI module."""

import random

from ai.tictactoe_ai import TicTacToeAI, check_winner


def _empty_board():
    return [[None, None, None] for _ in range(3)]


def _get_empty_cells(board):
    cells = []
    for r in range(3):
        for c in range(3):
            if board[r][c] is None:
                cells.append((r, c))
    return cells


def _play_game_ai_vs_random(rng):
    """Play a full game: X = random, O = AI. Returns the result string."""
    board = _empty_board()
    ai = TicTacToeAI()
    turn = "X"  # X goes first

    for _ in range(9):  # max 9 moves in tic-tac-toe
        result = check_winner(board)
        if result is not None:
            return result

        if turn == "X":
            empty = _get_empty_cells(board)
            r, c = rng.choice(empty)
            board[r][c] = "X"
            turn = "O"
        else:
            move = ai.get_move(board)
            assert move is not None, "AI returned None when board is not full"
            r, c = move
            assert board[r][c] is None, f"AI tried to overwrite cell ({r},{c})"
            board[r][c] = "O"
            turn = "X"

    result = check_winner(board)
    assert result is not None, "Game did not terminate after 9 moves"
    return result


def test_ai_vs_random_100_games():
    """AI (O) vs random (X) over 100 games: AI should never lose."""
    rng = random.Random(42)
    results = {"X": 0, "O": 0, "draw": 0}

    for i in range(100):
        result = _play_game_ai_vs_random(rng)
        assert result in ("X", "O", "draw"), f"Unexpected result: {result}"
        results[result] += 1

    # With perfect minimax, AI (O) should never lose
    assert results["X"] == 0, (
        f"AI lost {results['X']} games out of 100 — minimax should never lose. "
        f"Results: {results}"
    )


def test_ai_vs_ai_always_draws():
    """Two minimax AIs playing against each other should always draw."""
    board = _empty_board()
    ai_o = TicTacToeAI()  # plays O
    # For X, we also use minimax but flip perspective
    ai_x = TicTacToeAI()
    # ai_x plays as X, so swap its markers
    ai_x.ai_marker = "X"
    ai_x.human_marker = "O"

    turn = "X"

    for _ in range(9):
        result = check_winner(board)
        if result is not None:
            break

        if turn == "X":
            move = ai_x.get_move(board)
            assert move is not None
            r, c = move
            assert board[r][c] is None
            board[r][c] = "X"
            turn = "O"
        else:
            move = ai_o.get_move(board)
            assert move is not None
            r, c = move
            assert board[r][c] is None
            board[r][c] = "O"
            turn = "X"

    result = check_winner(board)
    assert result == "draw", f"AI vs AI should draw, got: {result}"


def test_board_validity_throughout_game():
    """Verify board state is always valid throughout a game."""
    rng = random.Random(42)
    board = _empty_board()
    ai = TicTacToeAI()
    turn = "X"

    x_count = 0
    o_count = 0

    for _ in range(9):
        result = check_winner(board)
        if result is not None:
            break

        if turn == "X":
            empty = _get_empty_cells(board)
            r, c = rng.choice(empty)
            board[r][c] = "X"
            x_count += 1
            turn = "O"
        else:
            move = ai.get_move(board)
            r, c = move
            board[r][c] = "O"
            o_count += 1
            turn = "X"

        # After each move, validate board state
        actual_x = sum(1 for r in range(3) for c in range(3) if board[r][c] == "X")
        actual_o = sum(1 for r in range(3) for c in range(3) if board[r][c] == "O")
        assert actual_x == x_count, "X count mismatch"
        assert actual_o == o_count, "O count mismatch"
        # X always goes first, so x_count >= o_count
        assert x_count - o_count in (0, 1), "Turn order violated"
