"""
Shared trick-taking utilities for card games.

Used by: Hearts, Spades, and any future trick-taking games.
"""

from utils.card import RANK_VALUES


def trick_winner(trick, lead_suit, trump_suit=None):
    """Determine the winner of a trick.

    Args:
        trick: list of (player_index, Card) tuples in play order
        lead_suit: the suit of the first card played
        trump_suit: optional trump suit that beats all others

    Returns:
        player_index of the winning player
    """
    best_player = trick[0][0]
    best_card = trick[0][1]
    best_is_trump = trump_suit and best_card.suit == trump_suit

    for player_idx, card in trick[1:]:
        is_trump = trump_suit and card.suit == trump_suit

        if is_trump and not best_is_trump:
            # Trump beats non-trump
            best_player = player_idx
            best_card = card
            best_is_trump = True
        elif is_trump and best_is_trump:
            # Both trump — higher value wins
            if card.value > best_card.value:
                best_player = player_idx
                best_card = card
        elif not is_trump and not best_is_trump:
            # Neither trump — must follow lead suit, higher value wins
            if card.suit == lead_suit and (
                best_card.suit != lead_suit or card.value > best_card.value
            ):
                best_player = player_idx
                best_card = card

    return best_player


def can_follow_suit(hand, lead_suit):
    """Check if a hand contains any cards of the lead suit."""
    return any(c.suit == lead_suit for c in hand)


def get_valid_plays(hand, lead_suit, must_follow=True):
    """Get valid cards to play from a hand.

    Args:
        hand: list of Cards
        lead_suit: suit that was led (None if leading)
        must_follow: if True, must follow suit when possible

    Returns:
        list of playable Cards
    """
    if lead_suit is None or not must_follow:
        return list(hand)

    following = [c for c in hand if c.suit == lead_suit]
    if following:
        return following
    return list(hand)  # Can play anything if can't follow


def sort_hand(hand, trump_suit=None):
    """Sort a hand by suit then rank. Trump suit first if specified."""
    suit_order = {"s": 0, "h": 1, "d": 2, "c": 3}
    if trump_suit:
        suit_order[trump_suit] = -1

    hand.sort(key=lambda c: (suit_order.get(c.suit, 4), c.value))


def count_points_hearts(trick_cards):
    """Count penalty points in a Hearts trick."""
    points = 0
    for card in trick_cards:
        if card.suit == "h":
            points += 1
        if card.suit == "s" and card.rank == "q":
            points += 13
    return points


def hand_score_spades(tricks_won, bid):
    """Calculate Spades score for a round.

    Returns (score, bags)
    """
    if bid == 0:
        # Nil bid
        if tricks_won == 0:
            return 100, 0
        else:
            return -100, 0

    if tricks_won >= bid:
        bags = tricks_won - bid
        score = bid * 10 + bags
        return score, bags
    else:
        return -bid * 10, 0
