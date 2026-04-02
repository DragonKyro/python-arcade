"""
Crazy Eights AI -- pure Python, no arcade imports.
Plays matching cards (preferring non-8s), uses 8s as wild when needed,
and chooses the most common suit in hand when playing an 8.
"""

import random
from typing import List, Optional, Tuple


class CrazyEightsAI:
    """AI player for Crazy Eights."""

    def choose_play(
        self,
        hand: list,
        top_rank: str,
        top_suit: str,
        active_suit: str,
    ) -> Optional[int]:
        """
        Choose which card index to play from *hand*, or None to draw.

        Parameters
        ----------
        hand : list of card-like objects with .rank and .suit attributes
        top_rank : rank of the discard pile top card
        top_suit : suit of the discard pile top card
        active_suit : the currently active suit (may differ from top_suit
                      if an 8 was played and a new suit was chosen)

        Returns
        -------
        int index into hand, or None if no playable card.
        """
        matching = []
        eights = []

        for i, card in enumerate(hand):
            if card.rank == "8":
                eights.append(i)
            elif card.suit == active_suit or card.rank == top_rank:
                matching.append(i)

        # Prefer non-8 matching cards
        if matching:
            return random.choice(matching)

        # Fall back to an 8
        if eights:
            return eights[0]

        return None

    def choose_suit(self, hand: list) -> str:
        """
        After playing an 8, choose the best suit.
        Picks the most common suit remaining in hand.

        Parameters
        ----------
        hand : list of card-like objects with .suit attribute

        Returns
        -------
        str  one of 'c', 'd', 'h', 's'
        """
        if not hand:
            return random.choice(["c", "d", "h", "s"])

        counts = {}
        for card in hand:
            counts[card.suit] = counts.get(card.suit, 0) + 1

        return max(counts, key=counts.get)

    def should_play_drawn(
        self,
        card,
        top_rank: str,
        active_suit: str,
    ) -> bool:
        """
        After drawing a card, decide whether to play it immediately.

        Returns True if the drawn card is playable.
        """
        if card.rank == "8":
            return True
        return card.suit == active_suit or card.rank == top_rank
