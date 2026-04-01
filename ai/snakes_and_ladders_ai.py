"""
AI for Snakes & Ladders.
Pure Python, no arcade imports.

There are no decisions in Snakes & Ladders (just dice rolls),
so this module simply provides the auto-roll trigger for AI players.
"""

import random


class SnakesAndLaddersAI:
    """AI player that automatically rolls the dice."""

    def roll_dice(self):
        """Return a dice roll result (1-6)."""
        return random.randint(1, 6)
