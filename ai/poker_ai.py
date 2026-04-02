"""
Texas Hold'em Poker AI -- simple but playable opponent.
Pure game logic -- no arcade imports.
"""

import random


# Hand rank tiers (higher = better)
HIGH_CARD = 0
ONE_PAIR = 1
TWO_PAIR = 2
THREE_KIND = 3
STRAIGHT = 4
FLUSH = 5
FULL_HOUSE = 6
FOUR_KIND = 7
STRAIGHT_FLUSH = 8
ROYAL_FLUSH = 9

RANK_ORDER = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8,
    "9": 9, "10": 10, "j": 11, "q": 12, "k": 13, "a": 14,
}


def card_rank_val(card):
    """Get numeric rank value from a Card object."""
    return RANK_ORDER.get(card.rank, 0)


def evaluate_hand(cards):
    """
    Evaluate the best 5-card poker hand from a list of cards.

    Parameters
    ----------
    cards : list[Card]
        2-7 Card objects (hole cards + community cards).

    Returns
    -------
    tuple(int, list[int])
        (rank_tier, tiebreakers) where rank_tier is HIGH_CARD..ROYAL_FLUSH
        and tiebreakers is a list of values for comparison (higher = better).
    """
    if len(cards) < 5:
        # Not enough cards for a full hand -- evaluate what we have
        return _evaluate_partial(cards)

    best = None
    # Check all 5-card combinations
    from itertools import combinations
    for combo in combinations(cards, 5):
        result = _evaluate_five(list(combo))
        if best is None or result > best:
            best = result
    return best


def _evaluate_partial(cards):
    """Evaluate fewer than 5 cards (for pre-flop or early streets)."""
    vals = sorted([card_rank_val(c) for c in cards], reverse=True)
    suits = [c.suit for c in cards]

    counts = {}
    for v in vals:
        counts[v] = counts.get(v, 0) + 1

    groups = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)

    if len(groups) >= 1 and groups[0][1] >= 2:
        pair_val = groups[0][0]
        kickers = [v for v in vals if v != pair_val]
        return (ONE_PAIR, [pair_val] + kickers)

    return (HIGH_CARD, vals)


def _evaluate_five(cards):
    """Evaluate exactly 5 cards and return (rank_tier, tiebreakers)."""
    vals = sorted([card_rank_val(c) for c in cards], reverse=True)
    suits = [c.suit for c in cards]

    is_flush = len(set(suits)) == 1

    # Check straight
    is_straight = False
    straight_high = 0
    unique_vals = sorted(set(vals), reverse=True)
    if len(unique_vals) == 5:
        if unique_vals[0] - unique_vals[4] == 4:
            is_straight = True
            straight_high = unique_vals[0]
        # Ace-low straight (A-2-3-4-5)
        if unique_vals == [14, 5, 4, 3, 2]:
            is_straight = True
            straight_high = 5

    # Count ranks
    counts = {}
    for v in vals:
        counts[v] = counts.get(v, 0) + 1

    # Sort groups by (count desc, value desc)
    groups = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    group_pattern = tuple(g[1] for g in groups)

    # Determine hand rank
    if is_straight and is_flush:
        if straight_high == 14 and min(vals) == 10:
            return (ROYAL_FLUSH, [14])
        return (STRAIGHT_FLUSH, [straight_high])

    if group_pattern == (4, 1):
        return (FOUR_KIND, [groups[0][0], groups[1][0]])

    if group_pattern == (3, 2):
        return (FULL_HOUSE, [groups[0][0], groups[1][0]])

    if is_flush:
        return (FLUSH, vals)

    if is_straight:
        return (STRAIGHT, [straight_high])

    if group_pattern == (3, 1, 1):
        kickers = sorted([g[0] for g in groups[1:]], reverse=True)
        return (THREE_KIND, [groups[0][0]] + kickers)

    if group_pattern == (2, 2, 1):
        pairs = sorted([groups[0][0], groups[1][0]], reverse=True)
        kicker = groups[2][0]
        return (TWO_PAIR, pairs + [kicker])

    if group_pattern == (2, 1, 1, 1):
        pair_val = groups[0][0]
        kickers = sorted([g[0] for g in groups[1:]], reverse=True)
        return (ONE_PAIR, [pair_val] + kickers)

    return (HIGH_CARD, vals)


class PokerAI:
    """AI player for Texas Hold'em poker."""

    def __init__(self, style="balanced"):
        """
        Parameters
        ----------
        style : str
            "tight" (conservative), "balanced", or "aggressive".
        """
        self.style = style
        self.bluff_factor = {"tight": 0.05, "balanced": 0.15, "aggressive": 0.3}.get(
            style, 0.15
        )

    def decide(self, hole_cards, community_cards, pot, current_bet,
               my_bet_this_round, my_chips, min_raise, phase):
        """
        Decide an action for the current betting round.

        Parameters
        ----------
        hole_cards : list[Card]
            The AI's 2 hole cards.
        community_cards : list[Card]
            Current community cards (0-5).
        pot : int
            Total pot size.
        current_bet : int
            The current bet level this round.
        my_bet_this_round : int
            How much this AI has already bet this round.
        my_chips : int
            AI's remaining chip stack.
        min_raise : int
            Minimum raise amount.
        phase : str
            "preflop", "flop", "turn", or "river".

        Returns
        -------
        tuple
            ("fold",) or ("call",) or ("raise", amount) or ("check",)
        """
        to_call = current_bet - my_bet_this_round
        if to_call < 0:
            to_call = 0

        # Evaluate hand strength
        all_cards = hole_cards + community_cards
        hand_eval = evaluate_hand(all_cards)
        tier = hand_eval[0]

        # Calculate a strength score 0.0 - 1.0
        strength = self._hand_strength(tier, hole_cards, community_cards, phase)

        # Add randomness / bluff factor
        strength += random.uniform(-0.1, self.bluff_factor)
        strength = max(0.0, min(1.0, strength))

        # Decision logic
        if to_call == 0:
            # Can check for free
            if strength > 0.6 and my_chips >= min_raise:
                raise_amt = self._calc_raise(strength, pot, min_raise, my_chips)
                return ("raise", raise_amt)
            return ("check",)

        # Must pay to stay in
        pot_odds = to_call / (pot + to_call) if (pot + to_call) > 0 else 1.0

        if strength < 0.2 and to_call > 0:
            return ("fold",)

        if strength > pot_odds + 0.1:
            # Comfortable call, maybe raise
            if strength > 0.65 and my_chips >= to_call + min_raise:
                raise_amt = self._calc_raise(strength, pot, min_raise, my_chips - to_call)
                return ("raise", raise_amt)
            if my_chips >= to_call:
                return ("call",)
            return ("fold",)

        # Marginal -- call if cheap
        if to_call <= my_chips and to_call <= pot * 0.3:
            return ("call",)

        return ("fold",)

    def _hand_strength(self, tier, hole_cards, community_cards, phase):
        """Estimate hand strength as 0.0-1.0."""
        base = {
            HIGH_CARD: 0.1,
            ONE_PAIR: 0.3,
            TWO_PAIR: 0.5,
            THREE_KIND: 0.6,
            STRAIGHT: 0.7,
            FLUSH: 0.75,
            FULL_HOUSE: 0.85,
            FOUR_KIND: 0.95,
            STRAIGHT_FLUSH: 0.98,
            ROYAL_FLUSH: 1.0,
        }.get(tier, 0.1)

        # Pre-flop adjustments based on hole cards
        if phase == "preflop" and len(hole_cards) == 2:
            v1 = card_rank_val(hole_cards[0])
            v2 = card_rank_val(hole_cards[1])
            high = max(v1, v2)
            # High pairs
            if v1 == v2:
                base = 0.4 + (v1 / 14.0) * 0.4
            # High cards (AK, AQ, etc.)
            elif high >= 12:
                base = max(base, 0.25 + (high / 14.0) * 0.2)
            # Suited cards bonus
            if hole_cards[0].suit == hole_cards[1].suit:
                base += 0.05

        # Reduce confidence on later streets with weak hands
        if phase in ("turn", "river") and tier <= HIGH_CARD:
            base *= 0.7

        return min(1.0, base)

    def _calc_raise(self, strength, pot, min_raise, available):
        """Calculate raise amount based on hand strength."""
        if available <= min_raise:
            return available

        # Scale raise with strength
        if strength > 0.9:
            # Strong hand -- big raise
            amount = max(min_raise, int(pot * 0.75))
        elif strength > 0.7:
            amount = max(min_raise, int(pot * 0.5))
        else:
            amount = min_raise

        # Don't raise more than we have
        return min(amount, available)
