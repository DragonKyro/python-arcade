"""Integration tests for Mancala: full game simulations using the AI module."""

import random

from ai.mancala_ai import MancalaAI, sow


TOTAL_STONES = 48  # 6 pits x 4 stones x 2 sides


def _initial_state():
    """Return the standard Mancala starting state."""
    pits = [[4, 4, 4, 4, 4, 4], [4, 4, 4, 4, 4, 4]]
    stores = [0, 0]
    return pits, stores


def _total_stones(pits, stores):
    """Return the total number of stones in play."""
    return sum(pits[0]) + sum(pits[1]) + stores[0] + stores[1]


def _is_game_over(pits):
    """Check if one side is completely empty."""
    return all(s == 0 for s in pits[0]) or all(s == 0 for s in pits[1])


def _get_valid_pits(pits, side):
    """Return list of pit indices that have stones."""
    return [i for i in range(6) if pits[side][i] > 0]


def _play_game_ai_vs_random(rng, ai_depth=4):
    """Play a full game: side 0 = random, side 1 = AI. Returns final stores."""
    pits, stores = _initial_state()
    ai = MancalaAI()
    ai.DEPTH_LIMIT = ai_depth
    ai_side = 1
    player_side = 0
    current_side = 0  # side 0 goes first
    max_turns = 200

    for _ in range(max_turns):
        if _is_game_over(pits):
            break

        valid = _get_valid_pits(pits, current_side)
        if not valid:
            # No moves: switch side
            current_side = 1 - current_side
            continue

        if current_side == ai_side:
            pit = ai.get_move(pits, stores, ai_side)
            assert pit is not None, "AI returned None when valid moves exist"
            assert 0 <= pit <= 5, f"AI pit {pit} out of range"
            assert pits[ai_side][pit] > 0, f"AI chose empty pit {pit}"
        else:
            pit = rng.choice(valid)

        new_pits, new_stores, extra_turn, _ = sow(pits, stores, current_side, pit)

        # Stone conservation check after every sow
        assert _total_stones(new_pits, new_stores) == TOTAL_STONES, (
            f"Stone conservation violated: had {TOTAL_STONES}, "
            f"now {_total_stones(new_pits, new_stores)} after side {current_side} "
            f"sowed pit {pit}"
        )

        pits, stores = new_pits, new_stores

        if extra_turn:
            # Same side goes again
            pass
        else:
            current_side = 1 - current_side

    # End of game: remaining stones go to their side's store
    final_stores = list(stores)
    for side in range(2):
        final_stores[side] += sum(pits[side])

    assert sum(final_stores) == TOTAL_STONES, (
        f"Final stone count {sum(final_stores)} != {TOTAL_STONES}"
    )

    return final_stores


def test_ai_vs_random_10_games():
    """AI vs random over 10 games: all terminate with valid stone counts."""
    rng = random.Random(42)

    for i in range(10):
        final_stores = _play_game_ai_vs_random(rng, ai_depth=4)
        assert final_stores[0] >= 0, f"Game {i}: negative player store"
        assert final_stores[1] >= 0, f"Game {i}: negative AI store"
        assert sum(final_stores) == TOTAL_STONES, (
            f"Game {i}: stones not conserved. Stores: {final_stores}"
        )


def test_stone_conservation():
    """Verify that total stones are always 48 throughout a game."""
    rng = random.Random(42)
    pits, stores = _initial_state()
    ai = MancalaAI()
    ai.DEPTH_LIMIT = 4
    current_side = 0

    assert _total_stones(pits, stores) == TOTAL_STONES

    for _ in range(200):
        if _is_game_over(pits):
            break

        valid = _get_valid_pits(pits, current_side)
        if not valid:
            current_side = 1 - current_side
            continue

        if current_side == 1:
            pit = ai.get_move(pits, stores, 1)
        else:
            pit = rng.choice(valid)

        pits, stores, extra_turn, _ = sow(pits, stores, current_side, pit)

        total = _total_stones(pits, stores)
        assert total == TOTAL_STONES, (
            f"Stone conservation failed: {total} != {TOTAL_STONES} "
            f"after side {current_side} sowed pit {pit}"
        )

        if not extra_turn:
            current_side = 1 - current_side


def test_extra_turns():
    """Verify that extra turns are granted when last stone lands in own store."""
    # Set up a scenario where sowing pit 0 (with 6 stones on side 0) lands in store
    pits = [[6, 0, 0, 0, 0, 0], [4, 4, 4, 4, 4, 4]]
    stores = [0, 0]

    new_pits, new_stores, extra_turn, _ = sow(pits, stores, 0, 0)
    # Pit 0 has 6 stones: sow into pits 1-5 (5 stones) + store (1 stone) = lands in store
    assert extra_turn is True, "Should get extra turn when last stone lands in own store"
    assert new_stores[0] == 1, f"Store should be 1, got {new_stores[0]}"

    # Verify stone conservation
    assert _total_stones(new_pits, new_stores) == _total_stones(pits, stores)


def test_game_ends_when_side_empty():
    """Verify game ends when one side's pits are all empty."""
    # Set up a near-end state where side 0 has only 1 stone left
    pits = [[0, 0, 0, 0, 0, 1], [0, 0, 0, 0, 0, 0]]
    stores = [23, 24]

    # Side 0 sows their last stone
    new_pits, new_stores, extra_turn, _ = sow(pits, stores, 0, 5)

    # After sowing, side 0 should be empty (the stone went to store)
    assert all(s == 0 for s in new_pits[0]), (
        f"Side 0 should be empty after sowing last stone, got {new_pits[0]}"
    )

    # Verify the game-over condition
    assert _is_game_over(new_pits), "Game should be over when one side is empty"

    # Stone conservation
    total_before = sum(pits[0]) + sum(pits[1]) + stores[0] + stores[1]
    total_after = _total_stones(new_pits, new_stores)
    assert total_after == total_before


def test_capture_mechanism():
    """Verify that capture works: last stone in empty own pit captures opposite."""
    # Side 0, pit 0 has 1 stone. Pit 1 is empty. Opposite of pit 1 (side 1, pit 4) has 5.
    pits = [[0, 0, 0, 0, 0, 0], [4, 4, 4, 4, 5, 4]]
    stores = [0, 0]
    # Side 0, pit 0 should be set so last stone lands in empty pit 1
    pits[0][0] = 1

    new_pits, new_stores, extra_turn, capture = sow(pits, stores, 0, 0)

    # Last stone goes from pit 0 to pit 1 (which was empty) -> capture
    assert capture is True, "Capture should have happened"
    # Captured stones: 1 (landing) + 5 (opposite) = 6 go to side 0's store
    assert new_stores[0] == 6, f"Expected store=6, got {new_stores[0]}"
    assert new_pits[0][1] == 0, "Landing pit should be empty after capture"
    assert new_pits[1][4] == 0, "Opposite pit should be empty after capture"

    # Stone conservation
    total_before = sum(pits[0]) + sum(pits[1]) + stores[0] + stores[1]
    total_after = _total_stones(new_pits, new_stores)
    assert total_after == total_before
