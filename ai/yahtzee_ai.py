"""
Yahtzee AI -- pure Python, no arcade imports.
Evaluates expected value for dice-keeping decisions and picks highest-scoring category.
"""

import random
from itertools import combinations
from collections import Counter


# All 13 scoring categories
CATEGORIES = [
    "ones", "twos", "threes", "fours", "fives", "sixes",
    "three_of_kind", "four_of_kind", "full_house",
    "small_straight", "large_straight", "yahtzee", "chance",
]

UPPER_CATEGORIES = ["ones", "twos", "threes", "fours", "fives", "sixes"]


def calculate_score(dice, category):
    """
    Calculate the score for a given set of 5 dice in the specified category.

    Parameters
    ----------
    dice : list[int]
        Five dice values (1-6).
    category : str
        One of the 13 category strings.

    Returns
    -------
    int
        Score for that category (0 if requirements not met).
    """
    counts = Counter(dice)
    sorted_dice = sorted(dice)
    total = sum(dice)

    if category == "ones":
        return counts.get(1, 0) * 1
    elif category == "twos":
        return counts.get(2, 0) * 2
    elif category == "threes":
        return counts.get(3, 0) * 3
    elif category == "fours":
        return counts.get(4, 0) * 4
    elif category == "fives":
        return counts.get(5, 0) * 5
    elif category == "sixes":
        return counts.get(6, 0) * 6
    elif category == "three_of_kind":
        if any(c >= 3 for c in counts.values()):
            return total
        return 0
    elif category == "four_of_kind":
        if any(c >= 4 for c in counts.values()):
            return total
        return 0
    elif category == "full_house":
        vals = sorted(counts.values())
        if vals == [2, 3]:
            return 25
        # Yahtzee counts as full house (5 of a kind)
        if vals == [5]:
            return 25
        return 0
    elif category == "small_straight":
        unique = set(sorted_dice)
        for start in [1, 2, 3]:
            if {start, start + 1, start + 2, start + 3}.issubset(unique):
                return 30
        return 0
    elif category == "large_straight":
        if sorted_dice == [1, 2, 3, 4, 5] or sorted_dice == [2, 3, 4, 5, 6]:
            return 40
        return 0
    elif category == "yahtzee":
        if len(counts) == 1:
            return 50
        return 0
    elif category == "chance":
        return total
    return 0


class YahtzeeAI:
    """AI player for Yahtzee."""

    def choose_dice_to_keep(self, dice, scores_used, roll_number):
        """
        Decide which dice to keep before a reroll.

        Parameters
        ----------
        dice : list[int]
            Current 5 dice values.
        scores_used : set[str]
            Set of category strings already used.
        roll_number : int
            Current roll number (1 or 2). After roll 3, must score.

        Returns
        -------
        list[int]
            Indices (0-4) of dice to keep.
        """
        available = [c for c in CATEGORIES if c not in scores_used]
        if not available:
            return list(range(5))

        best_keep = list(range(5))  # default: keep all
        best_value = -1

        # Try all possible subsets of dice to keep (2^5 = 32 combos)
        for mask in range(32):
            keep_indices = [i for i in range(5) if mask & (1 << i)]
            kept_values = [dice[i] for i in keep_indices]
            num_reroll = 5 - len(keep_indices)

            if num_reroll == 0:
                # No reroll -- evaluate as-is
                ev = self._best_available_score(dice, available)
            else:
                # Estimate expected value by sampling random rerolls
                ev = self._estimate_expected_value(kept_values, num_reroll, available)

            if ev > best_value:
                best_value = ev
                best_keep = keep_indices

        return best_keep

    def choose_category(self, dice, scores_used):
        """
        Choose the best available scoring category for the given dice.

        Parameters
        ----------
        dice : list[int]
            Final 5 dice values.
        scores_used : set[str]
            Categories already used.

        Returns
        -------
        str
            The chosen category string.
        """
        available = [c for c in CATEGORIES if c not in scores_used]
        if not available:
            return CATEGORIES[0]

        best_cat = available[0]
        best_score = -1

        for cat in available:
            score = calculate_score(dice, cat)
            # Prefer higher scores; break ties by preferring lower categories
            # to save upper section for potential bonus
            if score > best_score:
                best_score = score
                best_cat = cat

        # If the best score is 0, pick the least damaging category to waste
        if best_score == 0:
            best_cat = self._pick_least_damaging(dice, available)

        return best_cat

    def _best_available_score(self, dice, available):
        """Return the best score achievable from available categories."""
        return max(calculate_score(dice, c) for c in available)

    def _estimate_expected_value(self, kept_values, num_reroll, available, samples=40):
        """
        Estimate expected best score by sampling random outcomes for the
        rerolled dice.
        """
        total = 0.0
        for _ in range(samples):
            rerolled = [random.randint(1, 6) for _ in range(num_reroll)]
            full_dice = kept_values + rerolled
            total += self._best_available_score(full_dice, available)
        return total / samples

    def _pick_least_damaging(self, dice, available):
        """
        When all available scores are 0, pick the category where we lose
        the least expected future value. Prefer to waste yahtzee (if unlikely)
        or the upper category with the lowest face value.
        """
        # Priority: waste the category with the lowest maximum possible score
        waste_priority = [
            "yahtzee", "large_straight", "full_house", "small_straight",
            "four_of_kind", "three_of_kind",
            "ones", "twos", "threes", "fours", "fives", "sixes", "chance",
        ]
        for cat in waste_priority:
            if cat in available:
                return cat
        return available[0]
