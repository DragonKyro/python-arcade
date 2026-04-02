"""
Hearts AI player.
Pure game logic -- no arcade imports.

Strategy:
- Pass: dump Queen of Spades, high hearts, and high cards.
- Play: avoid taking hearts/QS. Dump high penalty cards when void.
- Shoot the moon if already ahead on penalty points mid-round.
"""

import random
from utils.card import RANK_VALUES
from utils.tricks import (
    trick_winner, can_follow_suit, get_valid_plays, sort_hand,
    count_points_hearts,
)


class HeartsAI:
    """AI player for Hearts."""

    def __init__(self, player_index):
        self.player_index = player_index

    # ------------------------------------------------------------------ passing

    def choose_pass_cards(self, hand, pass_direction):
        """Choose 3 cards to pass. Strategy: dump dangerous cards."""
        scored = []
        for card in hand:
            danger = 0
            # Queen of spades is top priority to dump
            if card.suit == "s" and card.rank == "q":
                danger = 100
            # High spades near queen are dangerous
            elif card.suit == "s" and card.value >= 11:
                danger = 40 + card.value
            # High hearts
            elif card.suit == "h":
                danger = 20 + card.value
            # Other high cards
            else:
                danger = card.value
            scored.append((danger, card))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:3]]

    # ------------------------------------------------------------------ play

    def choose_play(self, hand, valid_plays, current_trick, hearts_broken,
                    first_trick, round_points, tricks_taken):
        """Choose a card to play from valid_plays."""
        if len(valid_plays) == 1:
            return valid_plays[0]

        lead_suit = None
        if current_trick:
            lead_suit = current_trick[0][1].suit

        # Check if we might shoot the moon
        my_pts = round_points[self.player_index]
        other_pts = sum(round_points) - my_pts
        shooting_moon = my_pts >= 15 and other_pts == 0

        if lead_suit is None:
            return self._choose_lead(valid_plays, hearts_broken, shooting_moon)

        can_follow = any(c.suit == lead_suit for c in valid_plays)

        if can_follow:
            return self._choose_follow(valid_plays, current_trick, lead_suit, shooting_moon)
        else:
            return self._choose_discard(valid_plays, current_trick, first_trick, shooting_moon)

    def _choose_lead(self, valid_plays, hearts_broken, shooting_moon):
        """Choose a card to lead with."""
        if shooting_moon:
            # Lead high to win tricks
            return max(valid_plays, key=lambda c: c.value)

        # Prefer leading low non-heart cards
        non_hearts = [c for c in valid_plays if c.suit != "h"]
        candidates = non_hearts if non_hearts else valid_plays

        # Avoid leading spades if we hold high spades (might draw out QS onto us)
        safe = [c for c in candidates
                if not (c.suit == "s" and c.value >= 12)]
        if safe:
            candidates = safe

        return min(candidates, key=lambda c: c.value)

    def _choose_follow(self, valid_plays, current_trick, lead_suit, shooting_moon):
        """Follow suit. Try to win or duck depending on strategy."""
        following = [c for c in valid_plays if c.suit == lead_suit]
        if not following:
            following = valid_plays

        if shooting_moon:
            # Play high to win the trick
            return max(following, key=lambda c: c.value)

        # Check if the trick currently has penalty points
        trick_cards = [c for _, c in current_trick]
        has_penalty = any(c.suit == "h" or (c.suit == "s" and c.rank == "q")
                         for c in trick_cards)

        # Find current winning card value in lead suit
        best_lead_value = 0
        for _, c in current_trick:
            if c.suit == lead_suit and c.value > best_lead_value:
                best_lead_value = c.value

        if has_penalty or lead_suit == "h":
            # Try to duck under the current winner
            under = [c for c in following if c.value < best_lead_value]
            if under:
                return max(under, key=lambda c: c.value)  # highest safe card
            # Must play over -- play lowest
            return min(following, key=lambda c: c.value)
        else:
            # No penalty yet -- if we're last to play, we can play high safely
            if len(current_trick) == 3:
                # Safe to play high to win a clean trick
                return max(following, key=lambda c: c.value)
            # Otherwise play low
            return min(following, key=lambda c: c.value)

    def _choose_discard(self, valid_plays, current_trick, first_trick, shooting_moon):
        """Can't follow suit -- dump dangerous cards."""
        if shooting_moon:
            # Dump low cards
            return min(valid_plays, key=lambda c: c.value)

        # Priority: dump QS first
        qs = [c for c in valid_plays if c.suit == "s" and c.rank == "q"]
        if qs and not first_trick:
            return qs[0]

        # Dump high hearts
        hearts = [c for c in valid_plays if c.suit == "h"]
        if hearts and not first_trick:
            return max(hearts, key=lambda c: c.value)

        # Dump highest card from longest suit
        return max(valid_plays, key=lambda c: (c.value, c.suit))
