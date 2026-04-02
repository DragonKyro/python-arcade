"""
Renderer for Klondike Solitaire.
All arcade.draw_* calls live here. No arcade.draw_text — uses arcade.Text on game.
No imports from games.*.
"""

import arcade
from utils.card import draw_card, draw_empty_slot, draw_card_back, CARD_WIDTH, CARD_HEIGHT

# Window / layout constants
WIDTH = 800
HEIGHT = 600
TOP_BAR_HEIGHT = 50
SCALE = 1.0

CARD_W = CARD_WIDTH * SCALE
CARD_H = CARD_HEIGHT * SCALE

TABLEAU_TOP_Y = HEIGHT - TOP_BAR_HEIGHT - 130
TABLEAU_X_START = 60
TABLEAU_X_GAP = 105
FOUNDATION_X_START = TABLEAU_X_START + 3 * TABLEAU_X_GAP
FOUNDATION_Y = HEIGHT - TOP_BAR_HEIGHT - 30
STOCK_X = TABLEAU_X_START
STOCK_Y = FOUNDATION_Y
WASTE_X = STOCK_X + TABLEAU_X_GAP
WASTE_Y = FOUNDATION_Y

FACE_DOWN_OFFSET = 20
FACE_UP_OFFSET = 30

# Colors
BG_COLOR = (35, 100, 60)         # green felt
BAR_COLOR = (40, 50, 40)
BTN_COLOR = arcade.color.DARK_SLATE_BLUE
BTN_GREEN = arcade.color.DARK_GREEN
BTN_GOLD = arcade.color.DARK_GOLDENROD
WIN_OVERLAY = (0, 0, 0, 160)


def draw(game):
    """Render the full Klondike Solitaire game state."""
    _draw_background()
    _draw_top_bar(game)
    _draw_stock(game)
    _draw_waste(game)
    _draw_foundations(game)
    _draw_tableau(game)
    _draw_dragged(game)
    if game.game_won:
        _draw_win_overlay(game)


# ------------------------------------------------------------------
# Background
# ------------------------------------------------------------------

def _draw_background():
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), BG_COLOR
    )


# ------------------------------------------------------------------
# Top bar with buttons
# ------------------------------------------------------------------

def _draw_top_bar(game):
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT), BAR_COLOR
    )

    # Back button
    _draw_button(55, bar_y, 90, 35, BTN_COLOR)
    game.txt_back.draw()

    # New Game button
    _draw_button(WIDTH - 65, bar_y, 110, 35, BTN_GREEN)
    game.txt_new_game.draw()

    # Help button
    _draw_button(WIDTH - 135, bar_y, 40, 40, BTN_COLOR)
    game.txt_help.draw()

    # Draw mode toggle button
    _draw_button(420, bar_y, 70, 35, BTN_GOLD)
    game.txt_draw_mode.draw()

    # Move counter and timer
    game.txt_moves.draw()
    game.txt_timer.draw()


def _draw_button(x, y, w, h, color):
    arcade.draw_rect_filled(arcade.XYWH(x, y, w, h), color)
    arcade.draw_rect_outline(arcade.XYWH(x, y, w, h), arcade.color.WHITE)


# ------------------------------------------------------------------
# Stock pile (top-left)
# ------------------------------------------------------------------

def _draw_stock(game):
    if game.stock:
        draw_card_back(STOCK_X, STOCK_Y, SCALE)
    else:
        draw_empty_slot(STOCK_X, STOCK_Y, SCALE)


# ------------------------------------------------------------------
# Waste pile (next to stock)
# ------------------------------------------------------------------

def _draw_waste(game):
    if not game.waste:
        draw_empty_slot(WASTE_X, WASTE_Y, SCALE)
        return

    # Show up to 3 fanned cards
    visible_count = min(len(game.waste), 3)
    start = len(game.waste) - visible_count
    for i in range(start, len(game.waste)):
        card = game.waste[i]
        # Skip if this card is currently being dragged
        if card in game.dragging:
            continue
        draw_card(card, card.x, card.y, SCALE)


# ------------------------------------------------------------------
# Foundations (top-right, 4 piles)
# ------------------------------------------------------------------

def _draw_foundations(game):
    for fi in range(4):
        fx = FOUNDATION_X_START + fi * TABLEAU_X_GAP
        pile = game.foundations[fi]
        if pile:
            top = pile[-1]
            if top not in game.dragging:
                draw_card(top, top.x, top.y, SCALE)
            elif len(pile) >= 2:
                second = pile[-2]
                draw_card(second, fx, FOUNDATION_Y, SCALE)
            else:
                draw_empty_slot(fx, FOUNDATION_Y, SCALE)
        else:
            draw_empty_slot(fx, FOUNDATION_Y, SCALE)


# ------------------------------------------------------------------
# Tableau (7 columns)
# ------------------------------------------------------------------

def _draw_tableau(game):
    for ti in range(7):
        pile = game.tableau[ti]
        tx = TABLEAU_X_START + ti * TABLEAU_X_GAP

        if not pile:
            draw_empty_slot(tx, TABLEAU_TOP_Y, SCALE)
            continue

        for card in pile:
            # Skip dragged cards
            if card in game.dragging:
                continue
            if card.face_up:
                draw_card(card, card.x, card.y, SCALE)
            else:
                draw_card_back(card.x, card.y, SCALE)


# ------------------------------------------------------------------
# Dragged cards (drawn on top of everything)
# ------------------------------------------------------------------

def _draw_dragged(game):
    for card in game.dragging:
        draw_card(card, card.x, card.y, SCALE)


# ------------------------------------------------------------------
# Win overlay
# ------------------------------------------------------------------

def _draw_win_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), WIN_OVERLAY
    )
    game.txt_win_title.draw()
    game.txt_win_hint.draw()
