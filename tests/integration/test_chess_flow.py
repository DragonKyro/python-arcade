"""Integration tests for Chess: full game simulations using the AI module."""

import random

from ai.chess_ai import (
    ChessAI,
    initial_board,
    initial_castling_rights,
    apply_move,
    get_all_legal_moves,
    is_checkmate,
    is_stalemate,
    is_in_check,
    find_king,
)


def _play_game_ai_white_vs_random_black(rng, max_moves=200):
    """
    Play a full game: AI (white, depth=2) vs random legal moves (black).

    Returns
    -------
    tuple
        (result, move_count) where result is 'white', 'black', 'draw', or 'max_moves'.
    """
    board = initial_board()
    castling = initial_castling_rights()
    en_passant = None
    ai = ChessAI(depth=2)
    current = "white"
    move_count = 0

    for _ in range(max_moves):
        legal = get_all_legal_moves(board, current, castling, en_passant)

        if len(legal) == 0:
            if is_in_check(board, current):
                # Checkmate: the other side wins
                winner = "black" if current == "white" else "white"
                return winner, move_count
            else:
                return "draw", move_count  # Stalemate

        if current == "white":
            result = ai.get_move(board, "white", castling, en_passant)
            assert result is not None, "AI returned None when legal moves exist"
            from_sq, to_sq, promo = result
            move = (from_sq[0], from_sq[1], to_sq[0], to_sq[1], promo)
        else:
            move = rng.choice(legal)

        # Verify the move is legal
        assert move in legal, (
            f"Move {move} by {current} is not in legal moves list"
        )

        board, castling, en_passant, captured = apply_move(
            board, move, castling, en_passant
        )
        move_count += 1

        # Both kings must still exist
        assert find_king(board, "white") is not None, "White king disappeared"
        assert find_king(board, "black") is not None, "Black king disappeared"

        current = "black" if current == "white" else "white"

    return "max_moves", move_count


def test_ai_vs_random_3_games():
    """Simulate 3 games of AI (white) vs random (black). All must terminate cleanly."""
    rng = random.Random(42)
    for i in range(3):
        result, move_count = _play_game_ai_white_vs_random_black(rng)
        assert result in ("white", "black", "draw", "max_moves"), (
            f"Game {i}: unexpected result '{result}'"
        )
        assert move_count <= 200, f"Game {i}: exceeded 200 moves"
        assert move_count > 0, f"Game {i}: no moves were made"


def test_no_illegal_moves_in_game():
    """Verify that every move made during a game is in the legal moves list."""
    rng = random.Random(42)
    board = initial_board()
    castling = initial_castling_rights()
    en_passant = None
    ai = ChessAI(depth=2)
    current = "white"

    for _ in range(200):
        legal = get_all_legal_moves(board, current, castling, en_passant)
        if len(legal) == 0:
            break

        if current == "white":
            result = ai.get_move(board, "white", castling, en_passant)
            if result is None:
                break
            from_sq, to_sq, promo = result
            move = (from_sq[0], from_sq[1], to_sq[0], to_sq[1], promo)
        else:
            move = rng.choice(legal)

        assert move in legal, (
            f"Illegal move {move} attempted by {current}. "
            f"Legal moves count: {len(legal)}"
        )

        board, castling, en_passant, _ = apply_move(
            board, move, castling, en_passant
        )
        current = "black" if current == "white" else "white"


def test_checkmate_detection():
    """Verify checkmate is correctly detected via is_checkmate."""
    # Fool's mate position: white is checkmated
    board = initial_board()
    castling = initial_castling_rights()

    # 1. f3 (white pawn f2->f3)
    move = (6, 5, 5, 5, None)
    board, castling, ep, _ = apply_move(board, move, castling, None)

    # 1... e5 (black pawn e7->e5)
    move = (1, 4, 3, 4, None)
    board, castling, ep, _ = apply_move(board, move, castling, ep)

    # 2. g4 (white pawn g2->g4)
    move = (6, 6, 4, 6, None)
    board, castling, ep, _ = apply_move(board, move, castling, ep)

    # 2... Qh4# (black queen d8->h4)
    move = (0, 3, 4, 7, None)
    board, castling, ep, _ = apply_move(board, move, castling, ep)

    assert is_checkmate(board, "white", castling, ep), (
        "Fool's mate position should be checkmate for white"
    )
    assert is_in_check(board, "white"), "White should be in check"
    assert not is_stalemate(board, "white", castling, ep), (
        "This should not be stalemate"
    )


def test_scholars_mate_sequence():
    """Simulate Scholar's mate and verify checkmate is detected."""
    board = initial_board()
    castling = initial_castling_rights()
    ep = None

    # 1. e4
    move = (6, 4, 4, 4, None)
    board, castling, ep, _ = apply_move(board, move, castling, ep)

    # 1... e5
    move = (1, 4, 3, 4, None)
    board, castling, ep, _ = apply_move(board, move, castling, ep)

    # 2. Bc4 (bishop f1 -> c4)
    move = (7, 5, 4, 2, None)
    board, castling, ep, _ = apply_move(board, move, castling, ep)

    # 2... Nc6 (knight b8 -> c6)
    move = (0, 1, 2, 2, None)
    board, castling, ep, _ = apply_move(board, move, castling, ep)

    # 3. Qh5 (queen d1 -> h5)
    move = (7, 3, 3, 7, None)
    board, castling, ep, _ = apply_move(board, move, castling, ep)

    # 3... Nf6 (knight g8 -> f6)
    move = (0, 6, 2, 5, None)
    board, castling, ep, _ = apply_move(board, move, castling, ep)

    # 4. Qxf7# (queen h5 -> f7, capturing pawn)
    move = (3, 7, 1, 5, None)
    board, castling, ep, _ = apply_move(board, move, castling, ep)

    assert is_in_check(board, "black"), "Black should be in check after Qxf7"
    assert is_checkmate(board, "black", castling, ep), (
        "Scholar's mate should be checkmate for black"
    )


def test_stalemate_detection():
    """Verify stalemate is detected in a known stalemate position."""
    # Minimal stalemate: black king on a8, white queen on b6, white king on c1
    board = [[None] * 8 for _ in range(8)]
    board[0][0] = "k"  # a8 -> row 0, col 0
    board[2][1] = "Q"  # b6 -> row 2, col 1
    board[7][2] = "K"  # c1 -> row 7, col 2

    castling = {"K": False, "Q": False, "k": False, "q": False}

    assert not is_in_check(board, "black"), "Black should NOT be in check"
    assert is_stalemate(board, "black", castling, None), (
        "Position should be stalemate for black"
    )
    assert not is_checkmate(board, "black", castling, None), (
        "Position should NOT be checkmate"
    )
