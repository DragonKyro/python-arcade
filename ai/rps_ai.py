"""
Rock Paper Scissors AI using simple frequency analysis.
Pure logic module -- no arcade imports.
"""

import random
from collections import Counter


# What beats what: value beats key
COUNTERS = {
    "rock": "paper",
    "paper": "scissors",
    "scissors": "rock",
}

VALID_MOVES = list(COUNTERS.keys())


class RPSAI:
    """AI opponent that tracks the player's history and counters the most
    frequent move.  Falls back to a random choice when there is no history."""

    def get_move(self, history: list[str]) -> str:
        """Return 'rock', 'paper', or 'scissors'.

        Parameters
        ----------
        history : list[str]
            The player's past moves (oldest first).
        """
        if not history:
            return random.choice(VALID_MOVES)

        counts = Counter(history)
        most_common_move = counts.most_common(1)[0][0]
        return COUNTERS[most_common_move]
