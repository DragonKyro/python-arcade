"""Renderer for Peg Solitaire — all drawing code lives here."""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout constants
TOP_BAR_HEIGHT = 50
CELL_SPACING = 50
PEG_RADIUS = 18
HOLE_RADIUS = 10

# Board is 7x7; center it in the available area below the top bar
BOARD_COLS = 7
BOARD_ROWS = 7
BOARD_WIDTH = (BOARD_COLS - 1) * CELL_SPACING
BOARD_HEIGHT = (BOARD_ROWS - 1) * CELL_SPACING
BOARD_ORIGIN_X = (WIDTH - BOARD_WIDTH) // 2
BOARD_ORIGIN_Y = (HEIGHT - TOP_BAR_HEIGHT - BOARD_HEIGHT) // 2

# Undo button position (below the board, left side)
UNDO_BTN_X = WIDTH / 2 + 150
UNDO_BTN_Y = BOARD_ORIGIN_Y - 35
UNDO_BTN_W = 70
UNDO_BTN_H = 30

# Game states
PLAYING = 0
WON = 1
LOST = 2

# Valid board positions (English cross shape)
_VALID_POSITIONS = set()
for _r in range(7):
    for _c in range(7):
        if _r in (0, 1, 5, 6) and _c not in (2, 3, 4):
            continue
        _VALID_POSITIONS.add((_r, _c))

# Colors
COLOR_BG = (60, 90, 60)
COLOR_BOARD_BG = (139, 90, 43)
COLOR_BOARD_BORDER = (100, 60, 20)
COLOR_HOLE = (50, 30, 10)
COLOR_PEG_BASE = (180, 140, 100)
COLOR_PEG_HIGHLIGHT = (240, 220, 190)
COLOR_PEG_SHADOW = (120, 80, 50)
COLOR_SELECTED_RING = (255, 255, 0)
COLOR_VALID_DEST = (0, 200, 80, 140)
COLOR_OVERLAY = (0, 0, 0, 160)


def _cell_center(row, col):
    """Get pixel center for a board position."""
    cx = BOARD_ORIGIN_X + col * CELL_SPACING
    cy = BOARD_ORIGIN_Y + row * CELL_SPACING
    return cx, cy


def _draw_board_background():
    """Draw the wooden board background shape (cross outline)."""
    # Draw a filled cross shape as the board surface
    # Horizontal bar (rows 2-4, cols 0-6)
    hx = BOARD_ORIGIN_X + 3 * CELL_SPACING
    hy = BOARD_ORIGIN_Y + 3 * CELL_SPACING
    hw = 7 * CELL_SPACING + PEG_RADIUS * 2
    hh = 3 * CELL_SPACING + PEG_RADIUS * 2
    arcade.draw_rect_filled(arcade.XYWH(hx, hy, hw, hh), COLOR_BOARD_BG)
    arcade.draw_rect_outline(arcade.XYWH(hx, hy, hw, hh), COLOR_BOARD_BORDER, 2)

    # Vertical bar (rows 0-6, cols 2-4)
    vw = 3 * CELL_SPACING + PEG_RADIUS * 2
    vh = 7 * CELL_SPACING + PEG_RADIUS * 2
    arcade.draw_rect_filled(arcade.XYWH(hx, hy, vw, vh), COLOR_BOARD_BG)
    arcade.draw_rect_outline(arcade.XYWH(hx, hy, vw, vh), COLOR_BOARD_BORDER, 2)


def _draw_hole(cx, cy):
    """Draw an empty hole on the board."""
    arcade.draw_circle_filled(cx, cy, HOLE_RADIUS, COLOR_HOLE)
    arcade.draw_circle_outline(cx, cy, HOLE_RADIUS + 1, (30, 15, 5), 1)


def _draw_peg(cx, cy, selected=False):
    """Draw a peg with a 3D effect (shadow, base, highlight)."""
    # Shadow (offset down-right)
    arcade.draw_circle_filled(cx + 2, cy - 2, PEG_RADIUS, COLOR_PEG_SHADOW)
    # Base
    arcade.draw_circle_filled(cx, cy, PEG_RADIUS, COLOR_PEG_BASE)
    # Highlight (upper-left for 3D look)
    arcade.draw_circle_filled(cx - 4, cy + 4, PEG_RADIUS * 0.55, COLOR_PEG_HIGHLIGHT)
    # Rim
    arcade.draw_circle_outline(cx, cy, PEG_RADIUS, COLOR_PEG_SHADOW, 2)

    if selected:
        arcade.draw_circle_outline(cx, cy, PEG_RADIUS + 4, COLOR_SELECTED_RING, 3)


def _draw_valid_destination(cx, cy):
    """Draw a green indicator showing a valid jump destination."""
    arcade.draw_circle_filled(cx, cy, HOLE_RADIUS + 4, COLOR_VALID_DEST)
    arcade.draw_circle_outline(cx, cy, HOLE_RADIUS + 4, (0, 255, 100), 2)


def draw(game):
    """Render the entire Peg Solitaire game state."""
    # Background
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), COLOR_BG
    )

    # --- Top bar ---
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT), (50, 50, 50)
    )

    # Back button
    bx, by, bw, bh = 55, bar_y, 90, 35
    arcade.draw_rect_filled(arcade.XYWH(bx, by, bw, bh), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(bx, by, bw, bh), arcade.color.WHITE)
    game.txt_back.draw()

    # Move counter
    game.txt_moves.text = f"Moves: {game.move_count}"
    game.txt_moves.draw()

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

    # --- Board ---
    _draw_board_background()

    # Collect valid jump destinations for quick lookup
    valid_dests = set()
    if game.selected is not None:
        for dest_r, dest_c, _, _ in game.valid_jumps:
            valid_dests.add((dest_r, dest_c))

    # Draw all positions
    for pos in _VALID_POSITIONS:
        row, col = pos
        cx, cy = _cell_center(row, col)

        if game.board[pos]:
            is_selected = (game.selected == pos)
            _draw_peg(cx, cy, selected=is_selected)
        else:
            if pos in valid_dests:
                _draw_valid_destination(cx, cy)
            else:
                _draw_hole(cx, cy)

    # --- Undo button ---
    has_history = len(game.move_history) > 0
    undo_color = arcade.color.DARK_SLATE_BLUE if has_history else (60, 60, 60)
    arcade.draw_rect_filled(
        arcade.XYWH(UNDO_BTN_X, UNDO_BTN_Y, UNDO_BTN_W, UNDO_BTN_H), undo_color
    )
    arcade.draw_rect_outline(
        arcade.XYWH(UNDO_BTN_X, UNDO_BTN_Y, UNDO_BTN_W, UNDO_BTN_H), arcade.color.WHITE
    )
    game.txt_undo.draw()

    # --- Win / Lose overlay ---
    if game.game_state in (WON, LOST):
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), COLOR_OVERLAY
        )
        if game.game_state == WON:
            game.txt_you_win.draw()
            game.txt_win_hint.draw()
        else:
            remaining = sum(1 for v in game.board.values() if v)
            game.txt_game_over.draw()
            game.txt_game_over_hint.text = f"{remaining} pegs remaining. Click 'New Game' or undo."
            game.txt_game_over_hint.draw()
