"""
Go Fish AI -- pure Python, no arcade imports.
Asks for ranks it holds, preferring those with 2-3 cards.
Remembers ranks that other players have asked for.
"""

import random
from typing import List, Tuple, Optional


class GoFishAI:
    """AI player for Go Fish."""

    def __init__(self):
        # Track what ranks each player has asked for: {player_index: set(rank)}
        self.memory: dict[int, set] = {}

    def observe_ask(self, player_index: int, rank: str):
        """Record that a player asked for a given rank (they must hold it)."""
        if player_index not in self.memory:
            self.memory[player_index] = set()
        self.memory[player_index].add(rank)

    def observe_book(self, player_index: int, rank: str):
        """A book was completed -- remove rank from memory."""
        for s in self.memory.values():
            s.discard(rank)

    def choose_target_and_rank(
        self,
        my_index: int,
        hand: list,
        num_players: int,
        active_players: List[int],
    ) -> Tuple[int, str]:
        """
        Choose which opponent to ask and which rank to request.

        Parameters
        ----------
        my_index : this AI's player index
        hand : list of card-like objects (.rank, .suit)
        num_players : total number of players
        active_players : list of player indices that still have cards

        Returns
        -------
        (target_index, rank)
        """
        opponents = [i for i in active_players if i != my_index]
        if not opponents:
            opponents = [i for i in range(num_players) if i != my_index]

        # Count ranks in hand
        rank_counts: dict[str, int] = {}
        for card in hand:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1

        if not rank_counts:
            # Shouldn't happen, but fallback
            return (random.choice(opponents), "a")

        # Prefer ranks with 2-3 cards (closer to completing a book)
        best_ranks = sorted(rank_counts.keys(), key=lambda r: rank_counts[r], reverse=True)
        preferred = [r for r in best_ranks if rank_counts[r] >= 2]
        if not preferred:
            preferred = best_ranks

        rank = preferred[0]

        # Pick an opponent -- prefer one we remember asking for this rank
        target = None
        for opp in opponents:
            if opp in self.memory and rank in self.memory[opp]:
                target = opp
                break

        if target is None:
            target = random.choice(opponents)

        return (target, rank)
