"""
Renderer for the Kakuro game.
All arcade.draw_* calls for Kakuro live here.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Grid constants
CELL_SIZE = 60
MAX_GRID = 10  # max rows/cols for text pre-creation

# Centered for a 6x6 grid by default; actual origin recalculated in draw
GRID_ORIGIN_X = (WIDTH - 6 * CELL_SIZE) // 2
GRID_ORIGIN_Y = (HEIGHT - 50 - 6 * CELL_SIZE) // 2

# Top bar
TOP_BAR_HEIGHT = 50

# Cell types (must match game module)
BLACK = "black"
CLUE = "clue"
WHITE = "white"

# Colors
BG_COLOR = (40, 44, 52)
GRID_BG = (255, 255, 255)
BLACK_CELL_COLOR = (30, 30, 30)
CLUE_CELL_COLOR = (50, 50, 50)
SELECTED_COLOR = (100, 149, 237)
CONFLICT_COLOR = (255, 180, 180)
CONFLICT_TEXT_COLOR = (220, 40, 40)
PLAYER_TEXT_COLOR = (50, 100, 220)
LINE_COLOR = (80, 80, 80)
WIN_OVERLAY = (0, 0, 0, 160)
DIAGONAL_COLOR = (120, 120, 120)


def draw(game):
    """Render the entire Kakuro game state."""
    _draw_background()
    _draw_top_bar(game)
    _draw_cells(game)
    _draw_grid_lines(game)
    if game.game_won:
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

    # Title
    game.txt_title.draw()
    game.txt_puzzle_num.text = f"Puzzle {game.puzzle_index + 1}"
    game.txt_puzzle_num.draw()

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


def _draw_cells(game):
    """Draw all cells: black, clue, and white."""
    rows = game.rows
    cols = game.cols

    for r in range(rows):
        for c in range(cols):
            cx, cy = game._cell_center(r, c)
            cell = game.grid_def[r][c]

            if cell == BLACK:
                arcade.draw_rect_filled(
                    arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE), BLACK_CELL_COLOR
                )
            elif isinstance(cell, tuple) and cell[0] == CLUE:
                # Clue cell with diagonal
                arcade.draw_rect_filled(
                    arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE), CLUE_CELL_COLOR
                )
                # Draw diagonal line from top-left to bottom-right
                half = CELL_SIZE / 2
                arcade.draw_line(
                    cx - half, cy + half, cx + half, cy - half,
                    DIAGONAL_COLOR, 1
                )
                # Across clue (bottom-right)
                across_sum = cell[1]
                if across_sum > 0:
                    txt = game.txt_clue_across.get((r, c))
                    if txt:
                        txt.x = cx + CELL_SIZE * 0.15
                        txt.y = cy - CELL_SIZE * 0.15
                        txt.text = str(across_sum)
                        txt.draw()
                # Down clue (top-left)
                down_sum = cell[2]
                if down_sum > 0:
                    txt = game.txt_clue_down.get((r, c))
                    if txt:
                        txt.x = cx - CELL_SIZE * 0.15
                        txt.y = cy + CELL_SIZE * 0.15
                        txt.text = str(down_sum)
                        txt.draw()
            else:
                # White cell
                if game.conflicts[r][c]:
                    arcade.draw_rect_filled(
                        arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE), CONFLICT_COLOR
                    )
                else:
                    arcade.draw_rect_filled(
                        arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE), GRID_BG
                    )

                # Selected highlight
                if game.selected == (r, c):
                    arcade.draw_rect_outline(
                        arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE),
                        SELECTED_COLOR, border_width=3
                    )

                # Player number
                val = game.values[r][c]
                if val != 0:
                    txt = game.txt_cells.get((r, c))
                    if txt:
                        txt.x = cx
                        txt.y = cy
                        txt.text = str(val)
                        txt.color = CONFLICT_TEXT_COLOR if game.conflicts[r][c] else PLAYER_TEXT_COLOR
                        txt.draw()


def _draw_grid_lines(game):
    """Draw grid lines."""
    rows = game.rows
    cols = game.cols
    grid_w = cols * CELL_SIZE
    grid_h = rows * CELL_SIZE
    ox = GRID_ORIGIN_X
    oy = GRID_ORIGIN_Y

    # Use game's cell_center for proper alignment
    # Draw lines based on grid origin
    for i in range(rows + 1):
        y = oy + i * CELL_SIZE
        arcade.draw_line(ox, y, ox + grid_w, y, LINE_COLOR, 1)
    for j in range(cols + 1):
        x = ox + j * CELL_SIZE
        arcade.draw_line(x, oy, x, oy + grid_h, LINE_COLOR, 1)


def _draw_win_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), WIN_OVERLAY
    )
    game.txt_win_title.draw()
    game.txt_win_hint.draw()
