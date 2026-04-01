"""
Renderer for the Wordle game.
All arcade.draw_* calls for Wordle live here.
"""

import arcade
import time

from games.wordle import (
    WIDTH, HEIGHT,
    MAX_GUESSES, WORD_LENGTH,
    GREEN, YELLOW, DARK_GRAY, EMPTY_CELL, CELL_BORDER, CELL_ACTIVE_BORDER,
    CELL_SIZE, CELL_GAP, GRID_TOP,
    KB_ROWS, KB_KEY_W, KB_KEY_H, KB_KEY_GAP, KB_Y_START,
    KEY_BG, KEY_TEXT,
)


def draw(game):
    """Render the entire Wordle game state."""
    _draw_title()
    _draw_button(60, HEIGHT - 30, 90, 36, "Back", (50, 50, 70))
    _draw_button(WIDTH - 70, HEIGHT - 30, 110, 36, "New Game", (30, 100, 50))
    _draw_button(WIDTH - 145, HEIGHT - 30, 40, 40, "?", (50, 50, 70))
    _draw_grid(game)
    _draw_keyboard(game)
    _draw_message(game)


def _draw_title():
    """Draw the game title."""
    arcade.draw_text(
        "Wordle", WIDTH / 2, HEIGHT - 30,
        arcade.color.WHITE, font_size=28,
        anchor_x="center", anchor_y="center", bold=True,
    )


def _draw_button(cx, cy, w, h, text, color):
    """Draw a generic button."""
    arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), color)
    arcade.draw_rect_outline(arcade.XYWH(cx, cy, w, h), arcade.color.WHITE)
    arcade.draw_text(
        text, cx, cy, arcade.color.WHITE,
        font_size=14, anchor_x="center", anchor_y="center",
    )


def _cell_xy(row, col):
    """Return center (x, y) for grid cell at (row, col)."""
    total_w = WORD_LENGTH * (CELL_SIZE + CELL_GAP) - CELL_GAP
    total_h = MAX_GUESSES * (CELL_SIZE + CELL_GAP) - CELL_GAP
    start_x = WIDTH / 2 - total_w / 2 + CELL_SIZE / 2
    start_y = GRID_TOP - CELL_SIZE / 2
    x = start_x + col * (CELL_SIZE + CELL_GAP)
    y = start_y - row * (CELL_SIZE + CELL_GAP)
    return x, y


def _draw_grid(game):
    """Draw the letter grid."""
    for row in range(MAX_GUESSES):
        for col in range(WORD_LENGTH):
            x, y = _cell_xy(row, col)

            if row < len(game.guesses):
                # Submitted row - colored
                color = game.guess_colors[row][col]
                letter = game.guesses[row][col]
                arcade.draw_rect_filled(
                    arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE), color,
                )
                arcade.draw_rect_outline(
                    arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE), color, 2,
                )
                arcade.draw_text(
                    letter, x, y, arcade.color.WHITE,
                    font_size=28, anchor_x="center", anchor_y="center",
                    bold=True,
                )
            elif row == len(game.guesses) and not game.game_over:
                # Current input row
                letter = game.current_input[col] if col < len(game.current_input) else ""
                border = CELL_ACTIVE_BORDER if letter else CELL_BORDER
                arcade.draw_rect_filled(
                    arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE), EMPTY_CELL,
                )
                arcade.draw_rect_outline(
                    arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE), border, 2,
                )
                if letter:
                    arcade.draw_text(
                        letter, x, y, arcade.color.WHITE,
                        font_size=28, anchor_x="center",
                        anchor_y="center", bold=True,
                    )
            else:
                # Empty future row
                arcade.draw_rect_filled(
                    arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE), EMPTY_CELL,
                )
                arcade.draw_rect_outline(
                    arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE), CELL_BORDER, 2,
                )


def _draw_keyboard(game):
    """Draw the on-screen keyboard."""
    for r, row_letters in enumerate(KB_ROWS):
        row_width = len(row_letters) * (KB_KEY_W + KB_KEY_GAP) - KB_KEY_GAP
        if r == 2:
            row_width += 2 * (KB_KEY_W * 1.5 + KB_KEY_GAP)
        start_x = WIDTH / 2 - row_width / 2 + KB_KEY_W / 2
        y = KB_Y_START - r * (KB_KEY_H + KB_KEY_GAP)

        if r == 2:
            # Draw ENTER key
            enter_w = KB_KEY_W * 1.5
            ex = start_x
            arcade.draw_rect_filled(
                arcade.XYWH(ex, y, enter_w, KB_KEY_H), KEY_BG,
            )
            arcade.draw_text(
                "ENT", ex, y, KEY_TEXT,
                font_size=11, anchor_x="center", anchor_y="center", bold=True,
            )
            start_x += enter_w + KB_KEY_GAP

        for i, letter in enumerate(row_letters):
            x = start_x + i * (KB_KEY_W + KB_KEY_GAP)
            color = game.key_colors.get(letter, KEY_BG)
            arcade.draw_rect_filled(
                arcade.XYWH(x, y, KB_KEY_W, KB_KEY_H), color,
            )
            arcade.draw_text(
                letter, x, y, KEY_TEXT,
                font_size=14, anchor_x="center", anchor_y="center",
                bold=True,
            )

        if r == 2:
            # Draw BACK key
            back_w = KB_KEY_W * 1.5
            bx = start_x + len(row_letters) * (KB_KEY_W + KB_KEY_GAP)
            arcade.draw_rect_filled(
                arcade.XYWH(bx, y, back_w, KB_KEY_H), KEY_BG,
            )
            arcade.draw_text(
                "DEL", bx, y, KEY_TEXT,
                font_size=11, anchor_x="center", anchor_y="center", bold=True,
            )


def _draw_message(game):
    """Draw the toast message (invalid word, win, lose)."""
    if game.message:
        elapsed = time.time() - game.message_time
        if elapsed < 2.0 or game.game_over:
            arcade.draw_rect_filled(
                arcade.XYWH(WIDTH / 2, HEIGHT / 2 + 40, 300, 50),
                (255, 255, 255),
            )
            arcade.draw_text(
                game.message, WIDTH / 2, HEIGHT / 2 + 40,
                (0, 0, 0), font_size=16,
                anchor_x="center", anchor_y="center", bold=True,
            )
        else:
            game.message = ""
