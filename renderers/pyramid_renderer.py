"""
Renderer for Pyramid Solitaire.
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
BG_COLOR = (34, 85, 51)
DIMMED_TINT = (160, 160, 160, 255)
SELECTED_BORDER = arcade.color.YELLOW
EXPOSED_BORDER = (200, 255, 200)
WIN_OVERLAY = (0, 0, 0, 160)

STOCK_X = 100
STOCK_Y = 80
WASTE_X = 200
WASTE_Y = 80


def draw(game):
    """Render the full Pyramid Solitaire view."""
    _draw_background()
    _draw_top_bar(game)
    _draw_pyramid(game)
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


def _draw_pyramid(game):
    """Draw the 7-row pyramid of cards."""
    for row in range(7):
        for col in range(row + 1):
            card = game.pyramid[row][col]
            if card is None:
                continue

            exposed = game.is_exposed(row, col)
            selected = False
            if game.selected is not None and game.selected != "waste":
                sr, sc = game.selected
                if sr == row and sc == col:
                    selected = True

            # Draw dimmed overlay for blocked cards
            if not exposed:
                # Draw card with dimmed tint
                arcade.draw_texture_rect(
                    card.texture,
                    arcade.XYWH(card.x, card.y, CARD_WIDTH, CARD_HEIGHT),
                    color=DIMMED_TINT,
                )
            else:
                draw_card(card, card.x, card.y)

            # Highlight selected card
            if selected:
                arcade.draw_rect_outline(
                    arcade.XYWH(card.x, card.y, CARD_WIDTH + 4, CARD_HEIGHT + 4),
                    SELECTED_BORDER, border_width=3,
                )


def _draw_stock(game):
    """Draw stock pile."""
    if game.stock:
        draw_card_back(STOCK_X, STOCK_Y)
    else:
        draw_empty_slot(STOCK_X, STOCK_Y)


def _draw_waste(game):
    """Draw waste pile."""
    if game.waste:
        card = game.waste[-1]
        draw_card(card, WASTE_X, WASTE_Y)
        # Highlight if selected
        if game.selected == "waste":
            arcade.draw_rect_outline(
                arcade.XYWH(WASTE_X, WASTE_Y, CARD_WIDTH + 4, CARD_HEIGHT + 4),
                SELECTED_BORDER, border_width=3,
            )
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
