"""
Old Maid AI -- pure game logic, no arcade imports.

When offering its hand to the human, the AI shuffles the card order
so the human cannot track the Queen's position.
"""

import random
from typing import List


class OldMaidAI:
    """AI player for Old Maid."""

    def choose_card_from(self, hand: List) -> int:
        """
        Choose a random index from *hand* to draw from.

        Parameters
        ----------
        hand : list[Card]
            The hand being drawn from (previous player's hand).

        Returns
        -------
        int
            Index of the card to take.
        """
        return random.randint(0, len(hand) - 1)

    @staticmethod
    def shuffle_hand(hand: List) -> None:
        """
        Shuffle the hand in-place so the human cannot track card positions.
        Called before the human draws from an AI hand.
        """
        random.shuffle(hand)
