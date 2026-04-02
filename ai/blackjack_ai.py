"""
Blackjack AI -- basic strategy player.
Pure game logic -- no arcade imports.
"""

import random


class BlackjackAI:
    """AI player using simplified basic strategy."""

    def decide(self, hand_value, num_cards, dealer_upcard_value, can_split, can_double):
        """
        Decide the next action for this AI player.

        Parameters
        ----------
        hand_value : int
            Current total value of the AI's hand.
        num_cards : int
            Number of cards in hand.
        dealer_upcard_value : int
            The dealer's visible card value (1-11).
        can_split : bool
            Whether the hand is a splittable pair.
        can_double : bool
            Whether double-down is allowed (2 cards, enough chips).

        Returns
        -------
        str
            One of "hit", "stand", "double", "split".
        """
        # Double down on 10 or 11 with 2 cards
        if can_double and num_cards == 2 and hand_value in (10, 11):
            return "double"

        # Split aces or 8s
        if can_split and num_cards == 2:
            # We don't know the exact rank, but if value is 12 (two aces counted
            # as 1+11) or 16 (two 8s), split
            if hand_value in (12, 16):
                if random.random() < 0.8:
                    return "split"

        # Basic strategy: hit below 17, stand on 17+
        if hand_value < 17:
            return "hit"

        return "stand"


def choose_bet(chips, min_bet=10):
    """
    Choose a bet amount for the AI player.

    Parameters
    ----------
    chips : int
        Current chip count.
    min_bet : int
        Minimum bet allowed.

    Returns
    -------
    int
        Bet amount.
    """
    if chips <= 0:
        return 0
    # Bet between min_bet and 10% of stack, with some randomness
    max_bet = max(min_bet, chips // 10)
    bet = random.choice([min_bet, min_bet * 2, max_bet])
    return min(bet, chips)
