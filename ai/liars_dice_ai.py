"""
Liar's Dice AI with three difficulty levels.
Pure game logic -- no arcade imports.
"""

import random
from math import comb
from typing import List, Optional, Tuple, Union


# Return types for decide()
BidAction = Tuple[str, int, int]       # ('bid', quantity, face)
LiarAction = Tuple[str]                # ('liar',)
Action = Union[BidAction, LiarAction]


class LiarsDiceAI:
    """AI player for Liar's Dice."""

    def __init__(self, difficulty: str = "medium"):
        self.difficulty = difficulty  # 'easy', 'medium', 'hard'

    def decide(
        self,
        own_dice: List[int],
        num_total_dice: int,
        current_bid: Optional[Tuple[int, int]],
        num_players_remaining: int,
    ) -> Action:
        """
        Decide whether to raise the bid or call liar.

        Parameters
        ----------
        own_dice : list[int]
            The AI's own dice values (1-6).
        num_total_dice : int
            Total number of dice still in play across all players.
        current_bid : tuple(int, int) or None
            The current bid as (quantity, face), or None if this is the first bid.
        num_players_remaining : int
            Number of players still in the round.

        Returns
        -------
        ('bid', quantity, face)  or  ('liar',)
        """
        if current_bid is None:
            return self._make_opening_bid(own_dice, num_total_dice)

        bid_qty, bid_face = current_bid
        prob = self._estimate_probability(own_dice, num_total_dice, bid_qty, bid_face)

        # Decide call-liar thresholds per difficulty
        if self.difficulty == "easy":
            call_threshold = 0.40  # calls liar when bid is >60 % unlikely
        elif self.difficulty == "hard":
            call_threshold = 0.20  # very aggressive, rarely calls
        else:
            call_threshold = 0.30  # medium

        if prob < call_threshold:
            return ("liar",)

        return self._raise_bid(own_dice, num_total_dice, current_bid)

    # ------------------------------------------------------------------ helpers

    def _count_matching(self, own_dice: List[int], face: int) -> int:
        """Count dice in own hand matching *face* (1s are wild)."""
        if face == 1:
            return sum(1 for d in own_dice if d == 1)
        return sum(1 for d in own_dice if d == face or d == 1)

    def _estimate_probability(
        self, own_dice: List[int], num_total_dice: int, qty: int, face: int
    ) -> float:
        """
        Estimate the probability that at least *qty* dice of *face* exist
        among all dice in play, given what we know about our own hand.

        Uses binomial model for the unknown dice.  1s are wild (match any face).
        """
        own_matching = self._count_matching(own_dice, face)
        needed = qty - own_matching
        if needed <= 0:
            return 1.0

        unknown = num_total_dice - len(own_dice)
        if unknown <= 0:
            return 0.0

        # Probability a single unknown die matches: face itself + 1 (wild) / 6
        if face == 1:
            p = 1 / 6
        else:
            p = 2 / 6  # face or 1

        # P(X >= needed) where X ~ Binomial(unknown, p)
        prob = 0.0
        for k in range(needed, unknown + 1):
            prob += comb(unknown, k) * (p ** k) * ((1 - p) ** (unknown - k))
        return prob

    def _make_opening_bid(
        self, own_dice: List[int], num_total_dice: int
    ) -> BidAction:
        """Make the first bid of the round."""
        # Find the face we have the most of (prefer non-1 faces)
        counts = {}
        for d in own_dice:
            counts[d] = counts.get(d, 0) + 1

        best_face = max(
            (f for f in counts if f != 1), key=lambda f: counts[f], default=1
        )
        own_count = self._count_matching(own_dice, best_face)

        if self.difficulty == "easy":
            qty = max(1, own_count)
        elif self.difficulty == "hard":
            # Aggressive: bid higher than what we have
            qty = own_count + random.randint(1, max(1, num_total_dice // 4))
        else:
            qty = max(1, own_count + random.randint(0, 1))

        qty = max(1, min(qty, num_total_dice))
        return ("bid", qty, best_face)

    def _raise_bid(
        self,
        own_dice: List[int],
        num_total_dice: int,
        current_bid: Tuple[int, int],
    ) -> BidAction:
        """
        Raise the current bid.  A valid raise is either:
          - same face, higher quantity
          - higher face, same or higher quantity
          - any face, higher quantity
        We use the simplest rule: increase quantity by 1 on same face,
        or switch to a face we hold more of.
        """
        bid_qty, bid_face = current_bid

        # Gather candidates: same face +1 qty, or same qty with higher face
        candidates: list[Tuple[int, int, float]] = []

        # Option 1: same face, qty + 1
        new_qty = bid_qty + 1
        if new_qty <= num_total_dice:
            prob = self._estimate_probability(own_dice, num_total_dice, new_qty, bid_face)
            candidates.append((new_qty, bid_face, prob))

        # Option 2: higher face, same quantity
        for face in range(bid_face + 1, 7):
            prob = self._estimate_probability(own_dice, num_total_dice, bid_qty, face)
            candidates.append((bid_qty, face, prob))

        # Option 3: for hard difficulty, consider bluff bids
        if self.difficulty == "hard":
            bluff_face = random.randint(2, 6)
            bluff_qty = bid_qty + random.randint(1, 2)
            if bluff_qty <= num_total_dice:
                prob = self._estimate_probability(
                    own_dice, num_total_dice, bluff_qty, bluff_face
                )
                candidates.append((bluff_qty, bluff_face, prob + 0.15))

        if not candidates:
            # No valid raise possible -- must call liar
            return ("liar",)

        # Pick the candidate with the best probability
        if self.difficulty == "easy":
            # Conservative: pick highest probability
            candidates.sort(key=lambda c: c[2], reverse=True)
        elif self.difficulty == "hard":
            # Aggressive: mix probability with randomness
            random.shuffle(candidates)
            candidates.sort(key=lambda c: c[2] + random.uniform(-0.1, 0.2), reverse=True)
        else:
            candidates.sort(key=lambda c: c[2], reverse=True)

        qty, face, _ = candidates[0]
        qty = max(1, min(qty, num_total_dice))
        return ("bid", qty, face)
