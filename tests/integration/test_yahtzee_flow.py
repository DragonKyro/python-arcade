"""Integration tests for Yahtzee: full game simulations using the AI module."""

import random

from ai.yahtzee_ai import YahtzeeAI, CATEGORIES, calculate_score


def _roll_dice(rng, count=5):
    """Roll `count` dice using the given RNG."""
    return [rng.randint(1, 6) for _ in range(count)]


def _play_full_game(rng):
    """
    Play a full 13-round Yahtzee game for one AI player.

    Returns
    -------
    dict
        Mapping of category -> score for each of the 13 rounds.
    """
    ai = YahtzeeAI()
    scores_used = set()
    scorecard = {}

    for round_num in range(13):
        # Roll 1
        dice = _roll_dice(rng)

        # Roll 2: AI chooses which to keep, reroll the rest
        keep_indices = ai.choose_dice_to_keep(dice, scores_used, 1)
        assert all(0 <= idx <= 4 for idx in keep_indices), (
            f"Round {round_num + 1}, roll 1: invalid keep index in {keep_indices}"
        )
        new_dice = [dice[i] for i in keep_indices]
        new_dice += _roll_dice(rng, 5 - len(new_dice))
        dice = new_dice

        # Roll 3: AI chooses again
        keep_indices = ai.choose_dice_to_keep(dice, scores_used, 2)
        assert all(0 <= idx < len(dice) for idx in keep_indices), (
            f"Round {round_num + 1}, roll 2: invalid keep index in {keep_indices}"
        )
        new_dice = [dice[i] for i in keep_indices]
        new_dice += _roll_dice(rng, 5 - len(new_dice))
        dice = new_dice

        assert len(dice) == 5, f"Round {round_num + 1}: dice count is {len(dice)}, expected 5"
        assert all(1 <= d <= 6 for d in dice), (
            f"Round {round_num + 1}: invalid dice values {dice}"
        )

        # Choose category
        category = ai.choose_category(dice, scores_used)
        assert category in CATEGORIES, (
            f"Round {round_num + 1}: AI chose invalid category '{category}'"
        )
        assert category not in scores_used, (
            f"Round {round_num + 1}: AI reused category '{category}'"
        )

        score = calculate_score(dice, category)
        assert score >= 0, (
            f"Round {round_num + 1}: negative score {score} for {category}"
        )

        scorecard[category] = score
        scores_used.add(category)

    return scorecard


def test_full_game_2_ai_players():
    """Simulate a full 13-round game with 2 AI players."""
    rng = random.Random(42)

    for player_id in range(2):
        scorecard = _play_full_game(rng)

        # All 13 categories must be used
        assert len(scorecard) == 13, (
            f"Player {player_id + 1}: used {len(scorecard)} categories, expected 13"
        )

        # Every category must appear exactly once
        used_categories = set(scorecard.keys())
        assert used_categories == set(CATEGORIES), (
            f"Player {player_id + 1}: category mismatch. "
            f"Missing: {set(CATEGORIES) - used_categories}, "
            f"Extra: {used_categories - set(CATEGORIES)}"
        )

        # All scores must be non-negative
        for cat, score in scorecard.items():
            assert score >= 0, (
                f"Player {player_id + 1}: negative score {score} in '{cat}'"
            )

        total = sum(scorecard.values())
        assert total >= 0, f"Player {player_id + 1}: total score {total} is negative"


def test_no_category_used_twice():
    """Verify that the AI never selects a category that has already been used."""
    rng = random.Random(42)
    ai = YahtzeeAI()
    scores_used = set()

    for round_num in range(13):
        dice = _roll_dice(rng)

        keep_indices = ai.choose_dice_to_keep(dice, scores_used, 1)
        new_dice = [dice[i] for i in keep_indices]
        new_dice += _roll_dice(rng, 5 - len(new_dice))
        dice = new_dice

        keep_indices = ai.choose_dice_to_keep(dice, scores_used, 2)
        new_dice = [dice[i] for i in keep_indices]
        new_dice += _roll_dice(rng, 5 - len(new_dice))
        dice = new_dice

        category = ai.choose_category(dice, scores_used)
        assert category not in scores_used, (
            f"Round {round_num + 1}: category '{category}' was already used. "
            f"Used so far: {scores_used}"
        )
        scores_used.add(category)

    assert len(scores_used) == 13, f"Only {len(scores_used)} categories used"


def test_all_scores_non_negative():
    """Verify that calculate_score never returns negative for any valid input."""
    rng = random.Random(42)
    for _ in range(100):
        dice = _roll_dice(rng)
        for cat in CATEGORIES:
            score = calculate_score(dice, cat)
            assert score >= 0, (
                f"Negative score {score} for dice={dice}, category='{cat}'"
            )


def test_game_completes_with_different_seeds():
    """Run full games with multiple seeds to confirm robustness."""
    for seed in [42, 123, 999, 0, 7]:
        rng = random.Random(seed)
        scorecard = _play_full_game(rng)
        assert len(scorecard) == 13, (
            f"Seed {seed}: game did not complete all 13 rounds"
        )


def test_choose_dice_to_keep_returns_valid_indices():
    """Verify that choose_dice_to_keep always returns valid index lists."""
    rng = random.Random(42)
    ai = YahtzeeAI()

    for _ in range(50):
        dice = _roll_dice(rng)
        scores_used = set(rng.sample(CATEGORIES, rng.randint(0, 12)))
        for roll_number in [1, 2]:
            keep = ai.choose_dice_to_keep(dice, scores_used, roll_number)
            assert isinstance(keep, list), f"Expected list, got {type(keep)}"
            assert all(isinstance(i, int) for i in keep), (
                f"Non-integer index in {keep}"
            )
            assert all(0 <= i <= 4 for i in keep), (
                f"Index out of range in {keep}"
            )
            assert len(keep) == len(set(keep)), (
                f"Duplicate indices in {keep}"
            )
