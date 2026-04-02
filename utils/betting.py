"""
Shared betting utilities for card games with chips/money.

Used by: Blackjack, Poker, and any future betting card games.
"""


class BettingPlayer:
    """A player with a chip balance who can bet."""

    __slots__ = ("name", "chips", "current_bet", "is_human", "is_active")

    def __init__(self, name, chips=1000, is_human=False):
        self.name = name
        self.chips = chips
        self.current_bet = 0
        self.is_human = is_human
        self.is_active = True

    def place_bet(self, amount):
        """Place a bet, deducting from chips. Returns actual amount bet."""
        amount = min(amount, self.chips)
        self.chips -= amount
        self.current_bet += amount
        return amount

    def win_bet(self, multiplier=2.0):
        """Win the current bet. Returns payout amount."""
        payout = int(self.current_bet * multiplier)
        self.chips += payout
        winnings = payout
        self.current_bet = 0
        return winnings

    def push_bet(self):
        """Push (tie) — return bet to player."""
        self.chips += self.current_bet
        self.current_bet = 0

    def lose_bet(self):
        """Lose the current bet."""
        self.current_bet = 0

    def can_bet(self, amount):
        return self.chips >= amount

    @property
    def is_broke(self):
        return self.chips <= 0 and self.current_bet <= 0


BET_AMOUNTS = [10, 25, 50, 100, 250]


def format_chips(amount):
    """Format chip amount with comma separators."""
    return f"${amount:,}"
