"""
Renderer for the Sudoku game.
All arcade.draw_* calls for Sudoku live here.
"""

import arcade

from games.sudoku import (
    WIDTH, HEIGHT,
    GRID_SIZE, CELL_SIZE, GRID_PX, GRID_ORIGIN_X, GRID_ORIGIN_Y,
    TOP_BAR_HEIGHT,
    BG_COLOR, GRID_BG, CELL_HIGHLIGHT, SELECTED_COLOR, CONFLICT_COLOR,
    GIVEN_TEXT_COLOR, PLAYER_TEXT_COLOR, CONFLICT_TEXT_COLOR,
    THIN_LINE_COLOR, THICK_LINE_COLOR, WIN_OVERLAY,
)


def draw(game):
    """Render the entire Sudoku game state."""
    _draw_background()
    _draw_top_bar(game)
    _draw_difficulty_buttons(game)
    _draw_grid_background()
    _draw_cell_highlights(game)
    _draw_numbers(game)
    _draw_grid_lines()
    if game.game_won:
        _draw_win_overlay(game)


def _draw_background():
    """Draw the full background."""
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), BG_COLOR)


def _draw_top_bar(game):
    """Draw the top bar with Back, Timer, New Game, and Help buttons."""
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT), (50, 50, 50))

    # Back button
    bx, by, bw, bh = 55, bar_y, 90, 35
    arcade.draw_rect_filled(arcade.XYWH(bx, by, bw, bh), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(bx, by, bw, bh), arcade.color.WHITE)
    arcade.draw_text("Back", bx, by, arcade.color.WHITE,
                     font_size=14, anchor_x="center", anchor_y="center")

    # Timer
    mins = int(game.elapsed_time) // 60
    secs = int(game.elapsed_time) % 60
    arcade.draw_text(f"{mins:02d}:{secs:02d}", WIDTH / 2, bar_y, arcade.color.WHITE,
                     font_size=16, anchor_x="center", anchor_y="center", bold=True)

    # Difficulty label
    arcade.draw_text(game.difficulty, WIDTH / 2, bar_y - 15, arcade.color.LIGHT_GRAY,
                     font_size=10, anchor_x="center", anchor_y="center")

    # New Game button
    nx, ny, nw, nh = WIDTH - 65, bar_y, 110, 35
    arcade.draw_rect_filled(arcade.XYWH(nx, ny, nw, nh), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(nx, ny, nw, nh), arcade.color.WHITE)
    arcade.draw_text("New Game", nx, ny, arcade.color.WHITE,
                     font_size=14, anchor_x="center", anchor_y="center")

    # Help button
    hx, hy, hw, hh = WIDTH - 135, bar_y, 40, 40
    arcade.draw_rect_filled(arcade.XYWH(hx, hy, hw, hh), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(hx, hy, hw, hh), arcade.color.WHITE)
    arcade.draw_text("?", hx, hy, arcade.color.WHITE,
                     font_size=16, anchor_x="center", anchor_y="center", bold=True)


def _draw_difficulty_buttons(game):
    """Draw the difficulty selector buttons."""
    diff_y = HEIGHT - TOP_BAR_HEIGHT - 20
    for i, diff in enumerate(["Easy", "Medium", "Hard"]):
        dx = GRID_ORIGIN_X + i * 65
        color = arcade.color.DARK_GREEN if diff == game.difficulty else (80, 80, 80)
        arcade.draw_rect_filled(arcade.XYWH(dx + 30, diff_y, 58, 22), color)
        arcade.draw_rect_outline(arcade.XYWH(dx + 30, diff_y, 58, 22), arcade.color.WHITE)
        arcade.draw_text(diff, dx + 30, diff_y, arcade.color.WHITE,
                         font_size=10, anchor_x="center", anchor_y="center")


def _draw_grid_background():
    """Draw the white grid background."""
    arcade.draw_rect_filled(
        arcade.XYWH(GRID_ORIGIN_X + GRID_PX / 2, GRID_ORIGIN_Y + GRID_PX / 2, GRID_PX, GRID_PX),
        GRID_BG
    )


def _draw_cell_highlights(game):
    """Draw cell highlights for selection, conflicts, and selected cell outline."""
    if game.selected is not None:
        sr, sc = game.selected
        sbr, sbc = 3 * (sr // 3), 3 * (sc // 3)
        for r in range(9):
            for c in range(9):
                if r == sr or c == sc or (3 * (r // 3) == sbr and 3 * (c // 3) == sbc):
                    cx, cy = game._cell_center(r, c)
                    arcade.draw_rect_filled(
                        arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE),
                        CELL_HIGHLIGHT
                    )

        # Conflict cells
        for r in range(9):
            for c in range(9):
                if game.conflicts[r][c]:
                    cx, cy = game._cell_center(r, c)
                    arcade.draw_rect_filled(
                        arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE),
                        CONFLICT_COLOR
                    )

        # Selected cell bold highlight
        cx, cy = game._cell_center(sr, sc)
        arcade.draw_rect_outline(
            arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE),
            SELECTED_COLOR, border_width=3
        )


def _draw_numbers(game):
    """Draw all numbers on the board."""
    for r in range(9):
        for c in range(9):
            val = game.board[r][c]
            if val == 0:
                continue
            cx, cy = game._cell_center(r, c)
            if game.conflicts[r][c]:
                color = CONFLICT_TEXT_COLOR
            elif game.given[r][c]:
                color = GIVEN_TEXT_COLOR
            else:
                color = PLAYER_TEXT_COLOR
            arcade.draw_text(
                str(val), cx, cy, color,
                font_size=20 if game.given[r][c] else 18,
                anchor_x="center", anchor_y="center",
                bold=game.given[r][c]
            )


def _draw_grid_lines():
    """Draw the thin and thick grid lines."""
    for i in range(10):
        x0 = GRID_ORIGIN_X + i * CELL_SIZE
        y0 = GRID_ORIGIN_Y
        y1 = GRID_ORIGIN_Y + GRID_PX
        lw = 3 if i % 3 == 0 else 1
        col = THICK_LINE_COLOR if i % 3 == 0 else THIN_LINE_COLOR
        arcade.draw_line(x0, y0, x0, y1, col, lw)

        y_h = GRID_ORIGIN_Y + i * CELL_SIZE
        x1 = GRID_ORIGIN_X + GRID_PX
        arcade.draw_line(GRID_ORIGIN_X, y_h, x1, y_h, col, lw)


def _draw_win_overlay(game):
    """Draw the win congratulations overlay."""
    mins = int(game.elapsed_time) // 60
    secs = int(game.elapsed_time) % 60
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        WIN_OVERLAY
    )
    arcade.draw_text(
        "Congratulations!", WIDTH / 2, HEIGHT / 2 + 30,
        arcade.color.GOLD, font_size=36,
        anchor_x="center", anchor_y="center", bold=True
    )
    arcade.draw_text(
        f"Completed in {mins:02d}:{secs:02d}",
        WIDTH / 2, HEIGHT / 2 - 20,
        arcade.color.WHITE, font_size=20,
        anchor_x="center", anchor_y="center"
    )
    arcade.draw_text(
        "Click New Game to play again",
        WIDTH / 2, HEIGHT / 2 - 60,
        arcade.color.LIGHT_GRAY, font_size=14,
        anchor_x="center", anchor_y="center"
    )
