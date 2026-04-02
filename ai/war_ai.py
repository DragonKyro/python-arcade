"""
War AI -- pure game logic, no arcade imports.

War has no meaningful decisions; the AI simply flips its top card.
This module exists for consistency with the project convention.
"""


class WarAI:
    """AI player for War (no real decisions)."""

    def should_flip(self) -> bool:
        """Always returns True -- the AI is always ready to flip."""
        return True
