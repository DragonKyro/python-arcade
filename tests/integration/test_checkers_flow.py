"""Integration tests for Checkers: full game simulations using the AI module."""

import random

from ai.checkers_ai import (
    EMPTY,
    RED,
    BLACK,
    RED_KING,
    BLACK_KING,
    CheckersAI,
    initial_board,
    get_all_moves,
    apply_move,
    check_winner,
    count_pieces,
    get_captures,
)


def _play_game_ai_vs_random(rng, ai_depth=2, max_moves=200):
    """Play a full game: BLACK = AI, RED = random. Returns (winner, move_count)."""
    board = initial_board()
    ai = CheckersAI(depth=ai_depth)
    turn = BLACK  # Black typically starts
    move_count = 0

    for _ in range(max_moves):
        winner = check_winner(board)
        if winner is not None:
            return winner, move_count

        if turn == BLACK:
            move = ai.get_move(board, BLACK)
            if move is None:
                return RED, move_count  # AI has no moves, opponent wins
            board = apply_move(board, move)
        else:
            moves = get_all_moves(board, RED)
            if not moves:
                return BLACK, move_count  # Red has no moves
            move = rng.choice(moves)
            board = apply_move(board, move)

        turn = RED if turn == BLACK else BLACK
        move_count += 1

    # If we hit max_moves, declare it finished (prevent infinite game)
    return "max_moves", move_count


def test_ai_vs_random_5_games():
    """AI (black) vs random (red) over 5 games: all must terminate."""
    rng = random.Random(42)

    for i in range(5):
        winner, moves = _play_game_ai_vs_random(rng, ai_depth=2, max_moves=200)
        assert winner is not None, f"Game {i}: no winner determined"
        assert winner in (RED, BLACK, "draw", "max_moves"), (
            f"Game {i}: unexpected winner {winner}"
        )
        assert moves <= 200, f"Game {i}: exceeded 200 moves"


def test_mandatory_capture_enforced():
    """Verify that when captures are available, only captures are returned."""
    rng = random.Random(42)
    board = initial_board()
    ai = CheckersAI(depth=2)
    turn = BLACK

    for _ in range(200):
        winner = check_winner(board)
        if winner is not None:
            break

        moves = get_all_moves(board, turn)
        if not moves:
            break

        # Check: if any piece has captures, then ALL returned moves must be captures
        has_captures = False
        for r in range(8):
            for c in range(8):
                piece = board[r][c]
                if piece == EMPTY:
                    continue
                color = RED if piece in (RED, RED_KING) else BLACK
                if color == turn:
                    caps = get_captures(board, r, c)
                    if caps:
                        has_captures = True
                        break
            if has_captures:
                break

        if has_captures:
            # All moves should be captures (length > 2 means multi-step path)
            for move in moves:
                assert len(move) >= 2, "Capture move should have at least 2 positions"
                # Verify it's actually a capture: distance between steps is 2
                for j in range(1, len(move)):
                    dr = abs(move[j][0] - move[j - 1][0])
                    assert dr == 2, (
                        f"Expected capture (distance 2), got distance {dr} in move {move}"
                    )

        # Play the move
        if turn == BLACK:
            move = ai.get_move(board, BLACK)
            if move is None:
                break
            board = apply_move(board, move)
        else:
            move = rng.choice(moves)
            board = apply_move(board, move)

        turn = RED if turn == BLACK else BLACK


def test_multi_jump_handling():
    """Verify that multi-jump capture sequences work correctly."""
    # Set up a board where a multi-jump is possible
    board = [[EMPTY] * 8 for _ in range(8)]
    # Place a black piece that can double-jump
    board[0][1] = BLACK
    board[1][2] = RED
    board[3][4] = RED

    captures = get_captures(board, 0, 1)
    # There should be a multi-jump path: (0,1) -> (2,3) -> (4,5)
    has_multi = any(len(path) >= 3 for path in captures)
    assert has_multi, (
        f"Expected multi-jump capture but got: {captures}"
    )

    # Apply the multi-jump and verify both pieces are captured
    multi_move = [path for path in captures if len(path) >= 3][0]
    new_board = apply_move(board, multi_move)

    # Both red pieces should be gone
    assert new_board[1][2] == EMPTY, "First captured piece not removed"
    assert new_board[3][4] == EMPTY, "Second captured piece not removed"
    # Black piece should be at the final position
    final_r, final_c = multi_move[-1]
    assert new_board[final_r][final_c] in (BLACK, BLACK_KING), (
        "Black piece not at final position after multi-jump"
    )


def test_board_state_validity():
    """Verify board state is always valid: piece counts never increase illegally."""
    rng = random.Random(42)
    board = initial_board()
    ai = CheckersAI(depth=2)
    turn = BLACK

    prev_red, prev_black = count_pieces(board)
    assert prev_red == 12 and prev_black == 12, "Starting position should have 12 each"

    for _ in range(200):
        winner = check_winner(board)
        if winner is not None:
            break

        if turn == BLACK:
            move = ai.get_move(board, BLACK)
            if move is None:
                break
            board = apply_move(board, move)
        else:
            moves = get_all_moves(board, RED)
            if not moves:
                break
            move = rng.choice(moves)
            board = apply_move(board, move)

        red, black = count_pieces(board)

        # Piece counts should never increase (only decrease via captures or stay same)
        assert red <= prev_red, (
            f"Red pieces increased from {prev_red} to {red} after {'BLACK' if turn == BLACK else 'RED'} move"
        )
        assert black <= prev_black, (
            f"Black pieces increased from {prev_black} to {black} after {'BLACK' if turn == BLACK else 'RED'} move"
        )

        # Pieces should be on valid dark squares only
        for r in range(8):
            for c in range(8):
                if board[r][c] != EMPTY:
                    assert (r + c) % 2 == 1, (
                        f"Piece on light square ({r},{c}), value={board[r][c]}"
                    )

        prev_red, prev_black = red, black
        turn = RED if turn == BLACK else BLACK
