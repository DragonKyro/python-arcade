"""Renderer for Minesweeper — all drawing code lives here."""

import arcade
from games.minesweeper import (
    WIDTH, HEIGHT, COLS, ROWS, MINE_COUNT, TOP_BAR_HEIGHT,
    CELL_SIZE, GRID_ORIGIN_X, GRID_ORIGIN_Y,
    NUMBER_COLORS, UNREVEALED, FLAGGED, REVEALED, LOST, WON,
)


def draw(game):
    """Render the entire Minesweeper game state."""
    # Background
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), arcade.color.DARK_SLATE_GRAY)

    # --- Top bar ---
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT), (50, 50, 50))

    # Back button
    back_bx, back_by, back_bw, back_bh = 55, bar_y, 90, 35
    arcade.draw_rect_filled(arcade.XYWH(back_bx, back_by, back_bw, back_bh), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(back_bx, back_by, back_bw, back_bh), arcade.color.WHITE)
    arcade.draw_text("Back", back_bx, back_by, arcade.color.WHITE,
                     font_size=14, anchor_x="center", anchor_y="center")

    # Mine counter
    mine_display = MINE_COUNT - game.flags_placed
    arcade.draw_text(f"Mines: {mine_display}", 200, bar_y,
                     arcade.color.YELLOW, font_size=16,
                     anchor_x="center", anchor_y="center")

    # Timer
    seconds = int(game.elapsed_time)
    arcade.draw_text(f"Time: {seconds}", 500, bar_y,
                     arcade.color.YELLOW, font_size=16,
                     anchor_x="center", anchor_y="center")

    # New Game button
    new_bx, new_by, new_bw, new_bh = WIDTH - 65, bar_y, 110, 35
    arcade.draw_rect_filled(arcade.XYWH(new_bx, new_by, new_bw, new_bh), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(new_bx, new_by, new_bw, new_bh), arcade.color.WHITE)
    arcade.draw_text("New Game", new_bx, new_by, arcade.color.WHITE,
                     font_size=14, anchor_x="center", anchor_y="center")

    # Help button
    help_bx, help_by, help_bw, help_bh = WIDTH - 135, bar_y, 40, 35
    arcade.draw_rect_filled(arcade.XYWH(help_bx, help_by, help_bw, help_bh), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(help_bx, help_by, help_bw, help_bh), arcade.color.WHITE)
    arcade.draw_text("?", help_bx, help_by, arcade.color.WHITE,
                     font_size=14, anchor_x="center", anchor_y="center")

    # --- Grid ---
    for row in range(ROWS):
        for col in range(COLS):
            cx, cy = game._cell_center(row, col)
            state = game.cell_states[row][col]

            if state == UNREVEALED:
                # Raised gray cell
                arcade.draw_rect_filled(arcade.XYWH(cx, cy, CELL_SIZE - 2, CELL_SIZE - 2), (180, 180, 180))
                # Highlight edges for raised look
                left = cx - CELL_SIZE / 2 + 1
                right = cx + CELL_SIZE / 2 - 1
                top = cy + CELL_SIZE / 2 - 1
                bottom = cy - CELL_SIZE / 2 + 1
                arcade.draw_line(left, bottom, left, top, (220, 220, 220), 2)
                arcade.draw_line(left, top, right, top, (220, 220, 220), 2)
                arcade.draw_line(right, top, right, bottom, (120, 120, 120), 2)
                arcade.draw_line(left, bottom, right, bottom, (120, 120, 120), 2)

            elif state == FLAGGED:
                # Same raised appearance as unrevealed
                arcade.draw_rect_filled(arcade.XYWH(cx, cy, CELL_SIZE - 2, CELL_SIZE - 2), (180, 180, 180))
                left = cx - CELL_SIZE / 2 + 1
                right = cx + CELL_SIZE / 2 - 1
                top = cy + CELL_SIZE / 2 - 1
                bottom = cy - CELL_SIZE / 2 + 1
                arcade.draw_line(left, bottom, left, top, (220, 220, 220), 2)
                arcade.draw_line(left, top, right, top, (220, 220, 220), 2)
                arcade.draw_line(right, top, right, bottom, (120, 120, 120), 2)
                arcade.draw_line(left, bottom, right, bottom, (120, 120, 120), 2)
                # Draw flag: red triangle + pole
                pole_x = cx
                pole_bottom = cy - CELL_SIZE * 0.25
                pole_top = cy + CELL_SIZE * 0.3
                arcade.draw_line(pole_x, pole_bottom, pole_x, pole_top,
                                 arcade.color.BLACK, 2)
                flag_size = CELL_SIZE * 0.3
                arcade.draw_triangle_filled(
                    pole_x, pole_top,
                    pole_x, pole_top - flag_size,
                    pole_x + flag_size, pole_top - flag_size / 2,
                    arcade.color.RED
                )

            elif state == REVEALED:
                # Flat white/light cell
                arcade.draw_rect_filled(arcade.XYWH(cx, cy, CELL_SIZE - 2, CELL_SIZE - 2), (220, 220, 220))
                arcade.draw_rect_outline(arcade.XYWH(cx, cy, CELL_SIZE - 2, CELL_SIZE - 2), (160, 160, 160), 1)

                if game.mines[row][col]:
                    # Draw mine as black circle
                    arcade.draw_circle_filled(cx, cy, CELL_SIZE * 0.3,
                                              arcade.color.BLACK)
                elif game.adjacent[row][col] > 0:
                    num = game.adjacent[row][col]
                    color = NUMBER_COLORS.get(num, arcade.color.BLACK)
                    arcade.draw_text(str(num), cx, cy, color,
                                     font_size=int(CELL_SIZE * 0.5),
                                     anchor_x="center", anchor_y="center",
                                     bold=True)

    # --- Game over / win overlay ---
    if game.game_state == LOST:
        arcade.draw_text("GAME OVER", WIDTH / 2, HEIGHT / 2 + 10,
                         arcade.color.RED, font_size=40,
                         anchor_x="center", anchor_y="center", bold=True)
        arcade.draw_text("Click 'New Game' to try again", WIDTH / 2, HEIGHT / 2 - 30,
                         arcade.color.WHITE, font_size=16,
                         anchor_x="center", anchor_y="center")
    elif game.game_state == WON:
        arcade.draw_text("YOU WIN!", WIDTH / 2, HEIGHT / 2 + 10,
                         arcade.color.YELLOW, font_size=40,
                         anchor_x="center", anchor_y="center", bold=True)
        arcade.draw_text(f"Time: {int(game.elapsed_time)} seconds", WIDTH / 2,
                         HEIGHT / 2 - 30, arcade.color.WHITE, font_size=16,
                         anchor_x="center", anchor_y="center")
