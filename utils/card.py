"""
Shared card utilities for card games.

Provides a Card class, deck creation, shuffling, and texture loading
for the PNG card assets in assets/cards/.

Card image naming: {rank}{suit}.png
  rank: a, 2-10, j, q, k
  suit: c (clubs), d (diamonds), h (hearts), s (spades)
  back: cardback.png
"""

import os
import random
import arcade

# Card constants
SUITS = ["c", "d", "h", "s"]
SUIT_NAMES = {"c": "clubs", "d": "diamonds", "h": "hearts", "s": "spades"}
SUIT_COLORS = {"c": "black", "d": "red", "h": "red", "s": "black"}
RANKS = ["a", "2", "3", "4", "5", "6", "7", "8", "9", "10", "j", "q", "k"]
RANK_VALUES = {
    "a": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
    "8": 8, "9": 9, "10": 10, "j": 11, "q": 12, "k": 13,
}

# Default card display size
CARD_WIDTH = 71
CARD_HEIGHT = 96

# Asset paths
_CARDS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "cards")

# Texture cache (loaded once, shared across games)
_texture_cache = {}


def get_card_texture(rank, suit):
    """Get the arcade texture for a card face."""
    key = f"{rank}{suit}"
    if key not in _texture_cache:
        path = os.path.join(_CARDS_DIR, f"{key}.png")
        _texture_cache[key] = arcade.load_texture(path)
    return _texture_cache[key]


def get_back_texture():
    """Get the arcade texture for the card back."""
    if "back" not in _texture_cache:
        path = os.path.join(_CARDS_DIR, "cardback.png")
        _texture_cache["back"] = arcade.load_texture(path)
    return _texture_cache["back"]


class Card:
    """Represents a single playing card."""

    __slots__ = ("rank", "suit", "face_up", "x", "y")

    def __init__(self, rank, suit, face_up=False):
        self.rank = rank
        self.suit = suit
        self.face_up = face_up
        self.x = 0.0
        self.y = 0.0

    @property
    def value(self):
        return RANK_VALUES[self.rank]

    @property
    def color(self):
        return SUIT_COLORS[self.suit]

    @property
    def is_red(self):
        return self.color == "red"

    @property
    def is_black(self):
        return self.color == "black"

    @property
    def texture(self):
        if self.face_up:
            return get_card_texture(self.rank, self.suit)
        return get_back_texture()

    def flip(self):
        self.face_up = not self.face_up

    def __repr__(self):
        rank_display = self.rank.upper() if self.rank in ("a", "j", "q", "k") else self.rank
        suit_symbol = {"c": "♣", "d": "♦", "h": "♥", "s": "♠"}[self.suit]
        return f"{rank_display}{suit_symbol}"


def create_deck(shuffled=True):
    """Create a standard 52-card deck."""
    deck = [Card(rank, suit) for suit in SUITS for rank in RANKS]
    if shuffled:
        random.shuffle(deck)
    return deck


def draw_card(card, x, y, scale=1.0):
    """Draw a card at the given position."""
    card.x = x
    card.y = y
    w = CARD_WIDTH * scale
    h = CARD_HEIGHT * scale
    arcade.draw_texture_rect(card.texture, arcade.XYWH(x, y, w, h))


def draw_card_back(x, y, scale=1.0):
    """Draw just the card back at a position."""
    tex = get_back_texture()
    w = CARD_WIDTH * scale
    h = CARD_HEIGHT * scale
    arcade.draw_texture_rect(tex, arcade.XYWH(x, y, w, h))


def draw_empty_slot(x, y, scale=1.0):
    """Draw an empty card placeholder (rounded outline)."""
    w = CARD_WIDTH * scale
    h = CARD_HEIGHT * scale
    arcade.draw_rect_outline(arcade.XYWH(x, y, w, h), (100, 100, 100, 128), 2)


def point_in_card(px, py, card_x, card_y, scale=1.0):
    """Check if a point (px, py) is within a card at (card_x, card_y)."""
    w = CARD_WIDTH * scale / 2
    h = CARD_HEIGHT * scale / 2
    return abs(px - card_x) <= w and abs(py - card_y) <= h
