"""Tests for Yahtzee AI module."""

import random
import pytest

from ai.yahtzee_ai import calculate_score, CATEGORIES, YahtzeeAI


# ---------------------------------------------------------------------------
# calculate_score
# ---------------------------------------------------------------------------

class TestCalculateScore:
    # Upper section
    def test_ones(self):
        assert calculate_score([1, 1, 3, 4, 5], "ones") == 2

    def test_twos(self):
        assert calculate_score([2, 2, 2, 4, 5], "twos") == 6

    def test_threes(self):
        assert calculate_score([3, 3, 3, 3, 5], "threes") == 12

    def test_fours(self):
        assert calculate_score([4, 4, 1, 2, 3], "fours") == 8

    def test_fives(self):
        assert calculate_score([5, 5, 5, 5, 5], "fives") == 25

    def test_sixes(self):
        assert calculate_score([6, 6, 1, 2, 3], "sixes") == 12

    def test_ones_none(self):
        assert calculate_score([2, 3, 4, 5, 6], "ones") == 0

    # Three of a kind
    def test_three_of_kind_valid(self):
        assert calculate_score([3, 3, 3, 4, 5], "three_of_kind") == 18

    def test_three_of_kind_invalid(self):
        assert calculate_score([1, 2, 3, 4, 5], "three_of_kind") == 0

    # Four of a kind
    def test_four_of_kind_valid(self):
        assert calculate_score([2, 2, 2, 2, 5], "four_of_kind") == 13

    def test_four_of_kind_invalid(self):
        assert calculate_score([2, 2, 2, 3, 5], "four_of_kind") == 0

    # Full house
    def test_full_house_valid(self):
        assert calculate_score([3, 3, 5, 5, 5], "full_house") == 25

    def test_full_house_invalid(self):
        assert calculate_score([3, 3, 5, 5, 6], "full_house") == 0

    def test_full_house_yahtzee_counts(self):
        """Five of a kind counts as full house."""
        assert calculate_score([4, 4, 4, 4, 4], "full_house") == 25

    # Small straight
    def test_small_straight_1234(self):
        assert calculate_score([1, 2, 3, 4, 6], "small_straight") == 30

    def test_small_straight_2345(self):
        assert calculate_score([2, 3, 4, 5, 1], "small_straight") == 30

    def test_small_straight_3456(self):
        assert calculate_score([3, 4, 5, 6, 1], "small_straight") == 30

    def test_small_straight_invalid(self):
        assert calculate_score([1, 2, 3, 5, 6], "small_straight") == 0

    # Large straight
    def test_large_straight_low(self):
        assert calculate_score([1, 2, 3, 4, 5], "large_straight") == 40

    def test_large_straight_high(self):
        assert calculate_score([2, 3, 4, 5, 6], "large_straight") == 40

    def test_large_straight_invalid(self):
        assert calculate_score([1, 2, 3, 4, 6], "large_straight") == 0

    # Yahtzee
    def test_yahtzee_valid(self):
        assert calculate_score([6, 6, 6, 6, 6], "yahtzee") == 50

    def test_yahtzee_invalid(self):
        assert calculate_score([6, 6, 6, 6, 5], "yahtzee") == 0

    # Chance
    def test_chance(self):
        assert calculate_score([1, 2, 3, 4, 5], "chance") == 15

    def test_chance_all_sixes(self):
        assert calculate_score([6, 6, 6, 6, 6], "chance") == 30


# ---------------------------------------------------------------------------
# choose_dice_to_keep
# ---------------------------------------------------------------------------

class TestChooseDiceToKeep:
    def test_returns_valid_indices(self):
        random.seed(42)
        ai = YahtzeeAI()
        dice = [1, 2, 3, 4, 5]
        keep = ai.choose_dice_to_keep(dice, set(), 1)
        assert isinstance(keep, list)
        for idx in keep:
            assert 0 <= idx <= 4

    def test_keeps_yahtzee(self):
        """If already have yahtzee and it's available, keep all."""
        random.seed(42)
        ai = YahtzeeAI()
        dice = [5, 5, 5, 5, 5]
        keep = ai.choose_dice_to_keep(dice, set(), 1)
        assert sorted(keep) == [0, 1, 2, 3, 4]

    def test_no_duplicates_in_keep(self):
        random.seed(42)
        ai = YahtzeeAI()
        dice = [3, 3, 4, 4, 5]
        keep = ai.choose_dice_to_keep(dice, set(), 1)
        assert len(keep) == len(set(keep))

    def test_all_categories_used_keeps_all(self):
        random.seed(42)
        ai = YahtzeeAI()
        dice = [1, 2, 3, 4, 5]
        all_used = set(CATEGORIES)
        keep = ai.choose_dice_to_keep(dice, all_used, 1)
        assert sorted(keep) == [0, 1, 2, 3, 4]


# ---------------------------------------------------------------------------
# choose_category
# ---------------------------------------------------------------------------

class TestChooseCategory:
    def test_returns_valid_category(self):
        random.seed(42)
        ai = YahtzeeAI()
        dice = [3, 3, 3, 4, 5]
        cat = ai.choose_category(dice, set())
        assert cat in CATEGORIES

    def test_does_not_pick_used_category(self):
        random.seed(42)
        ai = YahtzeeAI()
        dice = [3, 3, 3, 4, 5]
        used = {"three_of_kind", "threes"}
        cat = ai.choose_category(dice, used)
        assert cat not in used

    def test_picks_yahtzee_for_five_of_kind(self):
        random.seed(42)
        ai = YahtzeeAI()
        dice = [4, 4, 4, 4, 4]
        cat = ai.choose_category(dice, set())
        assert cat == "yahtzee"

    def test_picks_large_straight(self):
        random.seed(42)
        ai = YahtzeeAI()
        dice = [1, 2, 3, 4, 5]
        cat = ai.choose_category(dice, set())
        assert cat == "large_straight"

    def test_all_zero_scores_picks_least_damaging(self):
        """When no category scores positive, pick least damaging."""
        random.seed(42)
        ai = YahtzeeAI()
        dice = [1, 2, 3, 4, 6]
        # Use all categories except yahtzee and large_straight (both score 0 for this dice)
        used = set(CATEGORIES) - {"yahtzee", "large_straight"}
        cat = ai.choose_category(dice, used)
        assert cat in {"yahtzee", "large_straight"}

    def test_with_almost_all_used(self):
        """Only one category left."""
        random.seed(42)
        ai = YahtzeeAI()
        dice = [1, 1, 1, 1, 1]
        used = set(CATEGORIES) - {"chance"}
        cat = ai.choose_category(dice, used)
        assert cat == "chance"

    def test_choose_category_never_crashes(self):
        """Run through several dice combos and used sets."""
        random.seed(42)
        ai = YahtzeeAI()
        test_cases = [
            ([1, 1, 1, 1, 1], set()),
            ([6, 6, 6, 6, 6], {"yahtzee"}),
            ([1, 2, 3, 4, 5], {"large_straight", "small_straight"}),
            ([2, 2, 3, 3, 3], {"full_house"}),
        ]
        for dice, used in test_cases:
            cat = ai.choose_category(dice, used)
            assert cat in CATEGORIES
            assert cat not in used
