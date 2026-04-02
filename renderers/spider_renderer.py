"""
Renderer for the Spider Solitaire game view.
All arcade.draw_* calls for Spider Solitaire are centralized here.
No arcade.draw_text() calls -- all text uses pre-created arcade.Text objects.
"""

import arcade
from utils.card import (
    draw_card, draw_card_back, draw_empty_slot, point_in_card,
    CARD_WIDTH, CARD_HEIGHT,
)

# Layout constants (must match spider.py)
WIDTH = 800
HEIGHT = 600
NUM_COLUMNS = 10
CARD_SCALE = 0.85
COL_SPACING = 74
COL_START_X = 42
TOP_Y = HEIGHT - 80
CARD_Y_OVERLAP_FACE_DOWN = 18
CARD_Y_OVERLAP_FACE_UP = 24
STOCK_X = WIDTH - 50
STOCK_Y = 40
COMPLETED_X = 50
COMPLETED_Y = 40

# Colors
BG_COLOR = (30, 80, 50)
BUTTON_COLOR = (60, 60, 60)
BUTTON_HOVER = (80, 80, 80)
DIFFICULTY_BOX_COLOR = (40, 100, 60)
DIFFICULTY_HIGHLIGHT = (60, 140, 80)


def draw(game):
    """Render the entire Spider Solitaire game state."""
    # Background
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), BG_COLOR
    )

    if game.choosing_difficulty:
        _draw_difficulty_screen(game)
        return

    # Title
    game.txt_title.draw()

    # Back button
    arcade.draw_rect_filled(
        arcade.XYWH(60, HEIGHT - 30, 80, 30), BUTTON_COLOR
    )
    game.txt_back.draw()

    # New Game button
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH - 70, HEIGHT - 30, 100, 30), BUTTON_COLOR
    )
    game.txt_new_game.draw()

    # Tableau columns
    _draw_tableau(game)

    # Stock pile
    _draw_stock(game)

    # Completed runs indicator
    _draw_completed(game)

    # Score and moves
    game.txt_score.draw()
    game.txt_moves.draw()

    # Dragging cards on top
    _draw_dragging(game)

    # Win overlay
    if game.game_won:
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
            (0, 0, 0, 150),
        )
        game.txt_win.draw()


def _draw_difficulty_screen(game):
    """Draw the difficulty selection screen."""
    game.txt_choose.draw()

    # 1 Suit button
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2 + 20, 240, 36), DIFFICULTY_BOX_COLOR
    )
    game.txt_1suit.draw()

    # 2 Suits button
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2 - 30, 240, 36), DIFFICULTY_BOX_COLOR
    )
    game.txt_2suits.draw()

    # 4 Suits button
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2 - 80, 240, 36), DIFFICULTY_BOX_COLOR
    )
    game.txt_4suits.draw()


def _draw_tableau(game):
    """Draw the 10 tableau columns with overlapping cards."""
    for col_idx in range(NUM_COLUMNS):
        col = game.tableau[col_idx]
        x = COL_START_X + col_idx * COL_SPACING

        if not col:
            draw_empty_slot(x, TOP_Y, CARD_SCALE)
            continue

        for card_idx, card in enumerate(col):
            # Skip cards being dragged (they render on top)
            if card in game.dragging_cards:
                continue
            draw_card(card, card.x, card.y, CARD_SCALE)


def _draw_stock(game):
    """Draw the stock pile indicator."""
    if game.stock:
        # Draw stacked backs to indicate remaining deals
        num_deals = len(game.stock) // 10
        for i in range(min(num_deals, 5)):
            draw_card_back(STOCK_X - i * 3, STOCK_Y, CARD_SCALE)
    else:
        draw_empty_slot(STOCK_X, STOCK_Y, CARD_SCALE)
    game.txt_stock_count.draw()


def _draw_completed(game):
    """Draw the completed runs counter area."""
    if game.completed_runs > 0:
        # Show small stacked card backs for each completed run
        for i in range(game.completed_runs):
            offset_x = i * 6
            draw_card_back(COMPLETED_X + offset_x, COMPLETED_Y, CARD_SCALE * 0.7)
    else:
        draw_empty_slot(COMPLETED_X, COMPLETED_Y, CARD_SCALE * 0.7)
    game.txt_completed.draw()


def _draw_dragging(game):
    """Draw cards currently being dragged."""
    for card in game.dragging_cards:
        draw_card(card, card.x, card.y, CARD_SCALE)
