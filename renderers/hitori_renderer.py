"""
Renderer for the Hitori game.
All arcade.draw_* calls for Hitori live here.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Grid constants
GRID_SIZE = 6
CELL_SIZE = 65
GRID_PX = GRID_SIZE * CELL_SIZE

# Layout
GRID_ORIGIN_X = (WIDTH - GRID_PX) // 2
GRID_ORIGIN_Y = (HEIGHT - 50 - GRID_PX) // 2

# Top bar
TOP_BAR_HEIGHT = 50

# Colors
BG_COLOR = (40, 44, 52)
CELL_NORMAL_BG = (240, 240, 240)
CELL_SHADED_BG = (30, 30, 30)
CELL_CONFIRMED_BG = (220, 240, 220)
CELL_SELECTED_OUTLINE = (80, 150, 255)
GRID_LINE_COLOR = (100, 100, 100)
NUMBER_COLOR = (20, 20, 20)
SHADED_NUMBER_COLOR = (80, 80, 80)
CONFIRMED_CIRCLE_COLOR = (60, 160, 80)
CONFLICT_HIGHLIGHT = (255, 200, 200)
WIN_OVERLAY = (0, 0, 0, 160)

# Cell states
NORMAL = 0
SHADED = 1
CONFIRMED = 2

# Game states
PLAYING = "playing"
WON = "won"


def draw(game):
    """Render the entire Hitori game state."""
    _draw_background()
    _draw_top_bar(game)
    _draw_cells(game)
    _draw_grid_lines()
    _draw_numbers(game)
    if game.game_state == WON:
        _draw_win_overlay(game)


def _draw_background():
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), BG_COLOR)


def _draw_top_bar(game):
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT), (50, 50, 50))

    # Back button
    bx, by, bw, bh = 55, bar_y, 90, 35
    arcade.draw_rect_filled(arcade.XYWH(bx, by, bw, bh), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(bx, by, bw, bh), arcade.color.WHITE)
    game.txt_back.draw()

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

    # Timer
    mins = int(game.elapsed_time) // 60
    secs = int(game.elapsed_time) % 60
    game.txt_timer.text = f"{mins:02d}:{secs:02d}"
    game.txt_timer.draw()


def _draw_cells(game):
    """Draw cell backgrounds based on state."""
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            cx = GRID_ORIGIN_X + c * CELL_SIZE + CELL_SIZE / 2
            cy = GRID_ORIGIN_Y + (GRID_SIZE - 1 - r) * CELL_SIZE + CELL_SIZE / 2

            state = game.cell_states[r][c]
            if state == SHADED:
                bg = CELL_SHADED_BG
            elif state == CONFIRMED:
                bg = CELL_CONFIRMED_BG
            else:
                # Check for conflicts
                if game.conflicts[r][c]:
                    bg = CONFLICT_HIGHLIGHT
                else:
                    bg = CELL_NORMAL_BG

            arcade.draw_rect_filled(
                arcade.XYWH(cx, cy, CELL_SIZE - 2, CELL_SIZE - 2),
                bg
            )

            # Draw confirmed circle marker
            if state == CONFIRMED:
                arcade.draw_circle_outline(cx, cy, CELL_SIZE / 2 - 6, CONFIRMED_CIRCLE_COLOR, 3)

            # Draw selection outline
            if game.selected == (r, c):
                arcade.draw_rect_outline(
                    arcade.XYWH(cx, cy, CELL_SIZE - 2, CELL_SIZE - 2),
                    CELL_SELECTED_OUTLINE, border_width=3
                )


def _draw_grid_lines():
    """Draw grid lines."""
    for i in range(GRID_SIZE + 1):
        x = GRID_ORIGIN_X + i * CELL_SIZE
        y0 = GRID_ORIGIN_Y
        y1 = GRID_ORIGIN_Y + GRID_PX
        arcade.draw_line(x, y0, x, y1, GRID_LINE_COLOR, 2)

        y = GRID_ORIGIN_Y + i * CELL_SIZE
        x0 = GRID_ORIGIN_X
        x1 = GRID_ORIGIN_X + GRID_PX
        arcade.draw_line(x0, y, x1, y, GRID_LINE_COLOR, 2)


def _draw_numbers(game):
    """Draw numbers in cells."""
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            txt = game.txt_cells.get((r, c))
            if txt is None:
                continue
            val = game.board[r][c]
            txt.text = str(val)
            state = game.cell_states[r][c]
            if state == SHADED:
                txt.color = SHADED_NUMBER_COLOR
            else:
                txt.color = NUMBER_COLOR
            txt.draw()


def _draw_win_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        WIN_OVERLAY
    )
    game.txt_win_title.draw()
    game.txt_win_hint.draw()
