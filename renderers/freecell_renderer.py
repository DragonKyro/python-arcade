"""Renderer for FreeCell Solitaire — all drawing code lives here."""

import arcade
from utils.card import (
    CARD_WIDTH, CARD_HEIGHT, draw_card, draw_empty_slot, point_in_card,
)

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout constants
TOP_BAR_HEIGHT = 50
CARD_SCALE = 1.0
CARD_W = CARD_WIDTH * CARD_SCALE
CARD_H = CARD_HEIGHT * CARD_SCALE
CASCADE_OFFSET_Y = 22  # vertical overlap between cards in a column

# Top row positions
TOP_ROW_Y = HEIGHT - TOP_BAR_HEIGHT - 10 - CARD_H // 2
SLOT_SPACING = CARD_W + 10

# Free cells: 4 slots on the left
FREE_CELL_START_X = 30 + CARD_W // 2
# Foundations: 4 slots on the right
FOUNDATION_START_X = WIDTH - 30 - CARD_W // 2 - 3 * SLOT_SPACING

# Tableau: 8 columns
NUM_COLUMNS = 8
TABLEAU_START_X = 30 + CARD_W // 2
TABLEAU_SPACING = (WIDTH - 60) / NUM_COLUMNS
TABLEAU_TOP_Y = TOP_ROW_Y - CARD_H // 2 - 20 - CARD_H // 2

# Game states
PLAYING = 0
WON = 1

# Undo button
UNDO_BTN_X = WIDTH / 2 - 40
UNDO_BTN_Y = HEIGHT - TOP_BAR_HEIGHT / 2
UNDO_BTN_W = 60
UNDO_BTN_H = 30

# Colors
COLOR_BG = (30, 100, 50)
COLOR_BAR = (50, 50, 50)
COLOR_HIGHLIGHT = (255, 255, 0, 120)
COLOR_OVERLAY = (0, 0, 0, 160)


def _free_cell_pos(index):
    """Return (x, y) center for free cell slot at given index (0-3)."""
    x = FREE_CELL_START_X + index * SLOT_SPACING
    return x, TOP_ROW_Y


def _foundation_pos(index):
    """Return (x, y) center for foundation slot at given index (0-3)."""
    x = FOUNDATION_START_X + index * SLOT_SPACING
    return x, TOP_ROW_Y


def _tableau_card_pos(col, row):
    """Return (x, y) center for a card in tableau column col at depth row."""
    x = TABLEAU_START_X + col * TABLEAU_SPACING
    y = TABLEAU_TOP_Y - row * CASCADE_OFFSET_Y
    return x, y


def get_clicked_location(game, mx, my):
    """Determine what the player clicked on.

    Returns a tuple:
        ("free_cell", index)
        ("foundation", index)
        ("tableau", col, card_index)  -- card_index into game.tableau[col]
        None if nothing useful was clicked
    """
    # Check free cells
    for i in range(4):
        fx, fy = _free_cell_pos(i)
        if point_in_card(mx, my, fx, fy, CARD_SCALE):
            return ("free_cell", i)

    # Check foundations
    for i in range(4):
        fx, fy = _foundation_pos(i)
        if point_in_card(mx, my, fx, fy, CARD_SCALE):
            return ("foundation", i)

    # Check tableau columns (iterate bottom card upward so topmost card wins)
    for col in range(NUM_COLUMNS):
        column = game.tableau[col]
        if not column:
            # Click on empty column slot
            x, y = _tableau_card_pos(col, 0)
            if point_in_card(mx, my, x, y, CARD_SCALE):
                return ("tableau", col, -1)  # -1 signals empty column
            continue
        for row in range(len(column) - 1, -1, -1):
            cx, cy = _tableau_card_pos(col, row)
            if point_in_card(mx, my, cx, cy, CARD_SCALE):
                return ("tableau", col, row)
    return None


def draw(game):
    """Render the entire FreeCell game state."""
    # Background
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), COLOR_BG
    )

    # --- Top bar ---
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT), COLOR_BAR
    )

    # Back button
    bx, by, bw, bh = 55, bar_y, 90, 35
    arcade.draw_rect_filled(arcade.XYWH(bx, by, bw, bh), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(bx, by, bw, bh), arcade.color.WHITE)
    game.txt_back.draw()

    # Undo button
    has_history = len(game.undo_stack) > 0
    undo_color = arcade.color.DARK_SLATE_BLUE if has_history else (60, 60, 60)
    arcade.draw_rect_filled(
        arcade.XYWH(UNDO_BTN_X, UNDO_BTN_Y, UNDO_BTN_W, UNDO_BTN_H), undo_color
    )
    arcade.draw_rect_outline(
        arcade.XYWH(UNDO_BTN_X, UNDO_BTN_Y, UNDO_BTN_W, UNDO_BTN_H), arcade.color.WHITE
    )
    game.txt_undo.draw()

    # New Game button
    nx, ny, nw, nh = WIDTH - 65, bar_y, 110, 35
    arcade.draw_rect_filled(arcade.XYWH(nx, ny, nw, nh), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(nx, ny, nw, nh), arcade.color.WHITE)
    game.txt_new_game.draw()

    # Help button
    hx, hy, hw, hh = WIDTH - 135, bar_y, 40, 35
    arcade.draw_rect_filled(arcade.XYWH(hx, hy, hw, hh), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(hx, hy, hw, hh), arcade.color.WHITE)
    game.txt_help.draw()

    # --- Free cells (top-left) ---
    for i in range(4):
        fx, fy = _free_cell_pos(i)
        draw_empty_slot(fx, fy, CARD_SCALE)
        card = game.free_cells[i]
        if card is not None:
            draw_card(card, fx, fy, CARD_SCALE)
            # Highlight if selected
            if game.selected == ("free_cell", i):
                arcade.draw_rect_filled(
                    arcade.XYWH(fx, fy, CARD_W, CARD_H), COLOR_HIGHLIGHT
                )

    # --- Foundations (top-right) ---
    for i in range(4):
        fx, fy = _foundation_pos(i)
        draw_empty_slot(fx, fy, CARD_SCALE)
        pile = game.foundations[i]
        if pile:
            # Only draw top card
            draw_card(pile[-1], fx, fy, CARD_SCALE)

    # --- Tableau columns ---
    for col in range(NUM_COLUMNS):
        column = game.tableau[col]
        if not column:
            # Draw empty slot placeholder
            x, y = _tableau_card_pos(col, 0)
            draw_empty_slot(x, y, CARD_SCALE)
            continue
        for row, card in enumerate(column):
            cx, cy = _tableau_card_pos(col, row)
            draw_card(card, cx, cy, CARD_SCALE)
            # Highlight selected card or stack
            if game.selected is not None:
                sel = game.selected
                if sel[0] == "tableau" and sel[1] == col:
                    sel_row = sel[2]
                    if row >= sel_row:
                        arcade.draw_rect_filled(
                            arcade.XYWH(cx, cy, CARD_W, CARD_H), COLOR_HIGHLIGHT
                        )

    # --- Win overlay ---
    if game.game_state == WON:
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), COLOR_OVERLAY
        )
        game.txt_you_win.draw()
        game.txt_win_hint.draw()
