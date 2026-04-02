"""
Renderer for TriPeaks Solitaire.
All drawing calls live here.  NO arcade.draw_text(), NO from games.* imports.
"""

import arcade
from utils.card import (
    draw_card, draw_card_back, draw_empty_slot,
    point_in_card, CARD_WIDTH, CARD_HEIGHT,
)

# Window / layout constants
WIDTH = 800
HEIGHT = 600
TOP_BAR_HEIGHT = 50

# Colors
BG_COLOR = (34, 70, 85)
PLAYABLE_BORDER = (100, 255, 100)
WIN_OVERLAY = (0, 0, 0, 160)

STOCK_X = 100
STOCK_Y = 80
WASTE_X = 200
WASTE_Y = 80


def draw(game):
    """Render the full TriPeaks Solitaire view."""
    _draw_background()
    _draw_top_bar(game)
    _draw_peaks(game)
    _draw_stock(game)
    _draw_waste(game)
    if game.game_won:
        _draw_win_overlay(game)
    elif game.game_over:
        _draw_lose_overlay(game)


def _draw_background():
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), BG_COLOR,
    )


def _draw_top_bar(game):
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT), (50, 50, 50),
    )

    # Back button
    bx, by, bw, bh = 55, bar_y, 90, 35
    arcade.draw_rect_filled(arcade.XYWH(bx, by, bw, bh), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(bx, by, bw, bh), arcade.color.WHITE)
    game.txt_back.draw()

    # Score
    game.txt_score.text = f"Score: {game.score}"
    game.txt_score.draw()

    # Streak
    game.txt_streak.text = f"Streak: {game.streak}"
    game.txt_streak.draw()

    # New Game button
    nx, ny, nw, nh = WIDTH - 65, bar_y, 110, 35
    arcade.draw_rect_filled(arcade.XYWH(nx, ny, nw, nh), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(nx, ny, nw, nh), arcade.color.WHITE)
    game.txt_new_game.draw()

    # Help button
    hx, hy, hw, hh = WIDTH - 135, bar_y, 40, 40
    arcade.draw_rect_filled(arcade.XYWH(hx, hy, hw, hh), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(hx, hy, hw, hh), arcade.color.WHITE)
    game.txt_help.draw()


def _draw_peaks(game):
    """Draw all peak cards, bottom rows first for correct overlap."""
    # Sort by row descending so bottom cards draw first (back-to-front)
    sorted_peaks = sorted(game.peaks, key=lambda p: -p["row"])
    for p in sorted_peaks:
        if p["removed"]:
            continue
        card = p["card"]
        exposed = game.is_exposed(p)

        if card.face_up:
            draw_card(card, card.x, card.y)
            # Highlight playable cards (exposed and adjacent to waste top)
            if exposed and game.waste:
                waste_val = game.waste[-1].value
                if game._ranks_adjacent(card.value, waste_val):
                    arcade.draw_rect_outline(
                        arcade.XYWH(card.x, card.y, CARD_WIDTH + 4, CARD_HEIGHT + 4),
                        PLAYABLE_BORDER, border_width=2,
                    )
        else:
            draw_card_back(card.x, card.y)


def _draw_stock(game):
    """Draw stock pile."""
    if game.stock:
        draw_card_back(STOCK_X, STOCK_Y)
    else:
        draw_empty_slot(STOCK_X, STOCK_Y)


def _draw_waste(game):
    """Draw waste pile top card."""
    if game.waste:
        card = game.waste[-1]
        draw_card(card, WASTE_X, WASTE_Y)
    else:
        draw_empty_slot(WASTE_X, WASTE_Y)


def _draw_win_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), WIN_OVERLAY,
    )
    game.txt_win_title.draw()
    game.txt_win_hint.draw()


def _draw_lose_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), WIN_OVERLAY,
    )
    game.txt_lose_title.draw()
    game.txt_lose_hint.draw()
