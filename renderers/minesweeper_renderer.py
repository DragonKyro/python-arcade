"""Renderer for Minesweeper — all drawing code lives here."""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Grid constants
COLS = 16
ROWS = 12
MINE_COUNT = 30

# Layout constants
TOP_BAR_HEIGHT = 50
GRID_PADDING = 10

# Calculate cell size to fit the grid nicely in the available space
AVAILABLE_WIDTH = WIDTH - 2 * GRID_PADDING
AVAILABLE_HEIGHT = HEIGHT - TOP_BAR_HEIGHT - 2 * GRID_PADDING
CELL_SIZE = min(AVAILABLE_WIDTH // COLS, AVAILABLE_HEIGHT // ROWS, 35)

# Grid origin (bottom-left corner of the grid), centered horizontally
GRID_WIDTH = COLS * CELL_SIZE
GRID_HEIGHT = ROWS * CELL_SIZE
GRID_ORIGIN_X = (WIDTH - GRID_WIDTH) // 2
GRID_ORIGIN_Y = (HEIGHT - TOP_BAR_HEIGHT - GRID_HEIGHT) // 2

# Number colors: index 1-8
NUMBER_COLORS = {
    1: arcade.color.BLUE,
    2: arcade.color.GREEN,
    3: arcade.color.RED,
    4: arcade.color.DARK_BLUE,
    5: arcade.color.DARK_RED,
    6: arcade.color.TEAL,
    7: arcade.color.BLACK,
    8: arcade.color.GRAY,
}

# Cell states
UNREVEALED = 0
REVEALED = 1
FLAGGED = 2

# Game states
PLAYING = 0
WON = 1
LOST = 2


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
    game.txt_back.draw()

    # Mine counter
    mine_display = MINE_COUNT - game.flags_placed
    game.txt_mines.text = f"Mines: {mine_display}"
    game.txt_mines.draw()

    # Timer
    seconds = int(game.elapsed_time)
    game.txt_timer.text = f"Time: {seconds}"
    game.txt_timer.draw()

    # New Game button
    new_bx, new_by, new_bw, new_bh = WIDTH - 65, bar_y, 110, 35
    arcade.draw_rect_filled(arcade.XYWH(new_bx, new_by, new_bw, new_bh), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(new_bx, new_by, new_bw, new_bh), arcade.color.WHITE)
    game.txt_new_game.draw()

    # Help button
    help_bx, help_by, help_bw, help_bh = WIDTH - 135, bar_y, 40, 35
    arcade.draw_rect_filled(arcade.XYWH(help_bx, help_by, help_bw, help_bh), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(help_bx, help_by, help_bw, help_bh), arcade.color.WHITE)
    game.txt_help.draw()

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
                    txt_obj = game.txt_cell_numbers[(row, col)]
                    txt_obj.text = str(num)
                    txt_obj.color = color
                    txt_obj.draw()

    # --- Game over / win overlay ---
    if game.game_state == LOST:
        game.txt_game_over.draw()
        game.txt_game_over_hint.draw()
    elif game.game_state == WON:
        game.txt_you_win.draw()
        game.txt_win_time.text = f"Time: {int(game.elapsed_time)} seconds"
        game.txt_win_time.draw()
