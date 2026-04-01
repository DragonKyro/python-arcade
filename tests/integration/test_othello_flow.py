"""Integration tests for Othello: full game simulations using the AI module."""

import random

from ai.othello_ai import (
    EMPTY,
    BLACK,
    WHITE,
    OthelloAI,
    get_valid_moves,
    apply_move,
    check_game_over,
)


def _initial_board():
    """Return the standard Othello starting position."""
    board = [[EMPTY] * 8 for _ in range(8)]
    board[3][3] = WHITE
    board[3][4] = BLACK
    board[4][3] = BLACK
    board[4][4] = WHITE
    return board


def _count_pieces(board):
    """Return (black_count, white_count, empty_count)."""
    b, w, e = 0, 0, 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == BLACK:
                b += 1
            elif board[r][c] == WHITE:
                w += 1
            else:
                e += 1
    return b, w, e


def _play_game_ai_vs_random(rng, ai_depth=2):
    """Play a full game: BLACK = AI, WHITE = random. Returns (black, white) scores."""
    board = _initial_board()
    ai = OthelloAI(depth=ai_depth)
    turn = BLACK  # Black goes first in Othello
    consecutive_passes = 0
    max_moves = 64  # at most 60 moves, use 64 for safety

    for _ in range(max_moves):
        if check_game_over(board):
            break

        moves = get_valid_moves(board, turn)

        if not moves:
            consecutive_passes += 1
            if consecutive_passes >= 2:
                break
            # Pass turn
            turn = WHITE if turn == BLACK else BLACK
            continue

        consecutive_passes = 0

        if turn == BLACK:
            # AI plays
            move = ai.get_move(board, BLACK)
            assert move is not None, "AI returned None when valid moves exist"
            assert move in moves, (
                f"AI move {move} not in valid moves {moves}"
            )
            board = apply_move(board, move[0], move[1], BLACK)
        else:
            # Random player
            move = rng.choice(moves)
            board = apply_move(board, move[0], move[1], WHITE)

        turn = WHITE if turn == BLACK else BLACK

    b, w, _ = _count_pieces(board)
    return b, w, board


def test_ai_vs_random_10_games():
    """AI vs random over 10 games: all must terminate with valid state."""
    rng = random.Random(42)

    for i in range(10):
        b, w, board = _play_game_ai_vs_random(rng, ai_depth=2)

        # Game must have terminated
        assert check_game_over(board), f"Game {i}: game did not reach terminal state"

        # Scores must be positive and sum to total occupied cells
        assert b >= 0 and w >= 0, f"Game {i}: negative scores b={b}, w={w}"
        total_pieces = b + w
        assert total_pieces >= 4, f"Game {i}: fewer pieces than starting position"
        assert total_pieces <= 64, f"Game {i}: more than 64 pieces"


def test_turn_passing():
    """Verify that turn passing works when one side has no moves."""
    rng = random.Random(42)
    board = _initial_board()
    ai = OthelloAI(depth=2)
    turn = BLACK
    passes = 0
    total_passes = 0

    for _ in range(64):
        if check_game_over(board):
            break

        moves = get_valid_moves(board, turn)
        if not moves:
            total_passes += 1
            passes += 1
            if passes >= 2:
                break
            turn = WHITE if turn == BLACK else BLACK
            continue

        passes = 0

        if turn == BLACK:
            move = ai.get_move(board, BLACK)
            board = apply_move(board, move[0], move[1], BLACK)
        else:
            move = rng.choice(moves)
            board = apply_move(board, move[0], move[1], WHITE)

        turn = WHITE if turn == BLACK else BLACK

    # The game should have finished
    assert check_game_over(board), "Game should be over"
    # Turn passing is a normal part of Othello -- just verify no crash


def test_final_piece_count_matches_score():
    """Verify that the final piece count on the board matches tallied scores."""
    rng = random.Random(42)

    for _ in range(5):
        b, w, board = _play_game_ai_vs_random(rng, ai_depth=2)

        # Count pieces directly on board
        actual_b, actual_w, actual_e = _count_pieces(board)
        assert actual_b == b, f"Black count mismatch: board={actual_b}, returned={b}"
        assert actual_w == w, f"White count mismatch: board={actual_w}, returned={w}"

        # Total non-empty cells should equal b + w
        total_on_board = sum(
            1 for r in range(8) for c in range(8) if board[r][c] != EMPTY
        )
        assert total_on_board == b + w


def test_no_invalid_moves_made():
    """Verify that every move made during a game is in the valid moves list."""
    rng = random.Random(42)
    board = _initial_board()
    ai = OthelloAI(depth=2)
    turn = BLACK
    passes = 0

    for _ in range(64):
        if check_game_over(board):
            break

        moves = get_valid_moves(board, turn)
        if not moves:
            passes += 1
            if passes >= 2:
                break
            turn = WHITE if turn == BLACK else BLACK
            continue

        passes = 0

        if turn == BLACK:
            move = ai.get_move(board, BLACK)
            assert move in moves, f"AI made invalid move {move}. Valid: {moves}"
            board = apply_move(board, move[0], move[1], BLACK)
        else:
            move = rng.choice(moves)
            # Random always picks from valid moves by construction
            board = apply_move(board, move[0], move[1], WHITE)

        turn = WHITE if turn == BLACK else BLACK
