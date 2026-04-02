"""
Spades AI player.
Pure game logic -- no arcade imports.

Strategy:
- Bid: count high cards + spade length for trick estimate.
- Play: follow suit with lowest winner or dump low; lead strong suits;
  use trump strategically; protect nil-bidding partner.
"""

import random
from utils.card import RANK_VALUES
from utils.tricks import (
    trick_winner, can_follow_suit, get_valid_plays, sort_hand,
    hand_score_spades,
)


class SpadesAI:
    """AI player for Spades."""

    def __init__(self, player_index):
        self.player_index = player_index

    # ------------------------------------------------------------------ bidding

    def choose_bid(self, hand, current_bids):
        """Choose a bid based on hand strength.

        Count high cards and spades for a trick estimate.
        """
        tricks = 0

        # Count likely winners
        spades = [c for c in hand if c.suit == "s"]
        non_spades = [c for c in hand if c.suit != "s"]

        # High spades are almost certain winners
        for c in spades:
            if c.value >= 12:    # Q, K of spades
                tricks += 1
            elif c.value == 1:   # Ace of spades (value=1 in RANK_VALUES but it's high)
                tricks += 1
            elif c.value >= 10:  # 10, J of spades
                tricks += 0.6
            elif c.value >= 7:
                tricks += 0.3

        # Long spade suit gives extra tricks
        if len(spades) >= 5:
            tricks += len(spades) - 4

        # Aces of non-spade suits
        for c in non_spades:
            if c.value == 1:     # Ace
                tricks += 0.9
            elif c.value == 13:  # King
                tricks += 0.5
            elif c.value == 12:  # Queen
                tricks += 0.2

        # Short suits (voids/singletons) can be trumped
        suits_in_hand = {}
        for c in hand:
            suits_in_hand.setdefault(c.suit, []).append(c)
        for suit in ["c", "d", "h"]:
            count = len(suits_in_hand.get(suit, []))
            if count == 0 and len(spades) > 0:
                tricks += min(1.0, len(spades) * 0.3)
            elif count == 1 and len(spades) > 1:
                tricks += 0.3

        bid = max(1, round(tricks))
        bid = min(bid, 13)

        # Small chance of nil if hand is very weak
        non_face_count = sum(1 for c in hand if c.value <= 8 and c.value != 1)
        if non_face_count >= 10 and len(spades) <= 1:
            bid = 0  # Nil

        return bid

    # ------------------------------------------------------------------ play

    def choose_play(self, hand, valid_plays, current_trick, spades_broken,
                    bids, tricks_won):
        """Choose a card to play."""
        if len(valid_plays) == 1:
            return valid_plays[0]

        lead_suit = None
        if current_trick:
            lead_suit = current_trick[0][1].suit

        # Check if we bid nil
        my_bid = bids[self.player_index] if bids[self.player_index] is not None else 1
        bid_nil = my_bid == 0

        if bid_nil:
            return self._play_nil_strategy(valid_plays, current_trick, lead_suit)

        if lead_suit is None:
            return self._choose_lead(valid_plays, spades_broken, bids, tricks_won)

        can_follow = any(c.suit == lead_suit for c in valid_plays)

        if can_follow:
            return self._choose_follow(valid_plays, current_trick, lead_suit, bids, tricks_won)
        else:
            return self._choose_off_suit(valid_plays, current_trick, bids, tricks_won)

    def _play_nil_strategy(self, valid_plays, current_trick, lead_suit):
        """When we bid nil, avoid winning tricks at all costs."""
        if not current_trick:
            # Leading: play lowest card, prefer non-spades
            non_spades = [c for c in valid_plays if c.suit != "s"]
            candidates = non_spades if non_spades else valid_plays
            return min(candidates, key=lambda c: c.value)

        if lead_suit:
            following = [c for c in valid_plays if c.suit == lead_suit]
            if following:
                # Play lowest in lead suit to try to duck
                return min(following, key=lambda c: c.value)

        # Can't follow: dump highest non-spade, or lowest spade
        non_spades = [c for c in valid_plays if c.suit != "s"]
        if non_spades:
            return min(non_spades, key=lambda c: c.value)
        return min(valid_plays, key=lambda c: c.value)

    def _choose_lead(self, valid_plays, spades_broken, bids, tricks_won):
        """Choose a card to lead with."""
        my_bid = bids[self.player_index] if bids[self.player_index] is not None else 1
        my_tricks = tricks_won[self.player_index]
        need_tricks = max(0, my_bid - my_tricks)

        if need_tricks > 0:
            # Need tricks: lead with strong suits (aces, kings)
            # Prefer non-spade aces
            aces = [c for c in valid_plays if c.value == 1 and c.suit != "s"]
            if aces:
                return aces[0]
            kings = [c for c in valid_plays if c.value == 13 and c.suit != "s"]
            if kings:
                return kings[0]
            # Lead spades if broken and we have high ones
            if spades_broken:
                high_spades = [c for c in valid_plays if c.suit == "s" and (c.value >= 12 or c.value == 1)]
                if high_spades:
                    return max(high_spades, key=lambda c: c.value if c.value != 1 else 14)

        # Don't need more tricks or no strong cards: lead low
        non_spades = [c for c in valid_plays if c.suit != "s"]
        candidates = non_spades if non_spades else valid_plays
        return min(candidates, key=lambda c: c.value if c.value != 1 else 14)

    def _choose_follow(self, valid_plays, current_trick, lead_suit, bids, tricks_won):
        """Follow suit."""
        following = [c for c in valid_plays if c.suit == lead_suit]
        if not following:
            following = valid_plays

        my_bid = bids[self.player_index] if bids[self.player_index] is not None else 1
        my_tricks = tricks_won[self.player_index]
        need_tricks = max(0, my_bid - my_tricks)

        # Find current best card in lead suit
        best_value = 0
        has_trump = False
        for _, c in current_trick:
            if c.suit == "s" and lead_suit != "s":
                has_trump = True
            if c.suit == lead_suit:
                val = c.value if c.value != 1 else 14
                if val > best_value:
                    best_value = val

        if has_trump and lead_suit != "s":
            # Someone already trumped -- can't win by following suit
            # Play lowest
            return min(following, key=lambda c: c.value if c.value != 1 else 14)

        if need_tricks > 0:
            # Try to win with lowest winning card
            winners = [c for c in following
                       if (c.value if c.value != 1 else 14) > best_value]
            if winners:
                return min(winners, key=lambda c: c.value if c.value != 1 else 14)
            # Can't win -- play lowest
            return min(following, key=lambda c: c.value if c.value != 1 else 14)
        else:
            # Don't need tricks -- duck
            under = [c for c in following
                     if (c.value if c.value != 1 else 14) < best_value]
            if under:
                return max(under, key=lambda c: c.value if c.value != 1 else 14)
            return min(following, key=lambda c: c.value if c.value != 1 else 14)

    def _choose_off_suit(self, valid_plays, current_trick, bids, tricks_won):
        """Can't follow suit. Decide whether to trump."""
        my_bid = bids[self.player_index] if bids[self.player_index] is not None else 1
        my_tricks = tricks_won[self.player_index]
        need_tricks = max(0, my_bid - my_tricks)

        spades = [c for c in valid_plays if c.suit == "s"]
        non_spades = [c for c in valid_plays if c.suit != "s"]

        # Check if trick already trumped
        trick_has_trump = any(c.suit == "s" for _, c in current_trick)
        best_trump = 0
        if trick_has_trump:
            for _, c in current_trick:
                if c.suit == "s":
                    val = c.value if c.value != 1 else 14
                    if val > best_trump:
                        best_trump = val

        if need_tricks > 0 and spades:
            if trick_has_trump:
                # Need to over-trump
                over = [c for c in spades
                        if (c.value if c.value != 1 else 14) > best_trump]
                if over:
                    return min(over, key=lambda c: c.value if c.value != 1 else 14)
            else:
                # Trump with lowest spade
                return min(spades, key=lambda c: c.value if c.value != 1 else 14)

        # Dump lowest non-spade
        if non_spades:
            return min(non_spades, key=lambda c: c.value if c.value != 1 else 14)
        # Only spades left
        return min(valid_plays, key=lambda c: c.value if c.value != 1 else 14)
