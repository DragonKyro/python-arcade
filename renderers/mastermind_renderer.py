"""Renderer for Mastermind — all drawing code lives here."""

import arcade
from games.mastermind import (
    WIDTH, HEIGHT, NUM_SLOTS, MAX_ATTEMPTS, NUM_COLORS,
    CODE_COLORS, BOARD_LEFT, SLOT_RADIUS, SLOT_SPACING,
    FEEDBACK_OFFSET_X, FEEDBACK_PEG_RADIUS, FEEDBACK_PEG_SPACING,
    PALETTE_Y, PALETTE_SPACING, PALETTE_RADIUS,
    EMPTY_COLOR, HIGHLIGHT_COLOR,
)


def draw(game):
    """Render the entire Mastermind game state."""
    # Title
    arcade.draw_text(
        "Mastermind",
        WIDTH / 2, HEIGHT - 30,
        arcade.color.WHITE,
        font_size=28,
        anchor_x="center",
        anchor_y="center",
        bold=True,
    )

    # Back button
    _draw_button(60, HEIGHT - 30, 90, 36, "Back", arcade.color.DARK_SLATE_BLUE)

    # New Game button
    _draw_button(WIDTH - 70, HEIGHT - 30, 110, 36, "New Game", arcade.color.DARK_GREEN)

    # Help button
    _draw_button(WIDTH - 140, HEIGHT - 30, 40, 36, "?", arcade.color.DARK_SLATE_BLUE)

    # Draw the guess board
    _draw_board(game)

    # Draw color palette
    _draw_palette(game)

    # Draw submit button
    if not game.game_over:
        all_filled = all(c is not None for c in game.current_guess)
        btn_color = arcade.color.DARK_BLUE if all_filled else (60, 60, 80)
        _draw_button(WIDTH - 70, game._row_y(game.current_row), 100, 32, "Submit", btn_color)

    # Draw win/lose message
    if game.game_over:
        _draw_game_over_message(game)


def _draw_button(cx, cy, w, h, text, color):
    arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), color)
    arcade.draw_rect_outline(arcade.XYWH(cx, cy, w, h), arcade.color.WHITE)
    arcade.draw_text(
        text, cx, cy, arcade.color.WHITE,
        font_size=14, anchor_x="center", anchor_y="center",
    )


def _draw_board(game):
    for row in range(MAX_ATTEMPTS):
        y = game._row_y(row)

        # Row number label
        arcade.draw_text(
            str(row + 1), BOARD_LEFT - 40, y,
            arcade.color.LIGHT_GRAY, font_size=12,
            anchor_x="center", anchor_y="center",
        )

        for slot in range(NUM_SLOTS):
            x = game._slot_x(slot)

            if row < len(game.guesses):
                # Completed guess row
                color = CODE_COLORS[game.guesses[row][slot]]
                arcade.draw_circle_filled(x, y, SLOT_RADIUS, color)
                arcade.draw_circle_outline(x, y, SLOT_RADIUS, arcade.color.WHITE, 2)
            elif row == game.current_row and not game.game_over:
                # Current guess row
                if game.current_guess[slot] is not None:
                    color = CODE_COLORS[game.current_guess[slot]]
                    arcade.draw_circle_filled(x, y, SLOT_RADIUS, color)
                    arcade.draw_circle_outline(x, y, SLOT_RADIUS, HIGHLIGHT_COLOR, 2)
                else:
                    arcade.draw_circle_filled(x, y, SLOT_RADIUS, EMPTY_COLOR)
                    arcade.draw_circle_outline(x, y, SLOT_RADIUS, arcade.color.LIGHT_GRAY, 1)
            else:
                # Empty future row
                arcade.draw_circle_filled(x, y, SLOT_RADIUS, EMPTY_COLOR)
                arcade.draw_circle_outline(x, y, SLOT_RADIUS, (100, 100, 100), 1)

        # Draw feedback pegs for completed rows
        if row < len(game.feedback):
            black_pegs, white_pegs = game.feedback[row]
            fb_x_start = game._slot_x(NUM_SLOTS - 1) + FEEDBACK_OFFSET_X - 140
            peg_index = 0
            for _ in range(black_pegs):
                px = fb_x_start + (peg_index % 2) * FEEDBACK_PEG_SPACING
                py = y + (peg_index // 2) * FEEDBACK_PEG_SPACING - FEEDBACK_PEG_SPACING / 2
                arcade.draw_circle_filled(px, py, FEEDBACK_PEG_RADIUS, arcade.color.BLACK)
                arcade.draw_circle_outline(px, py, FEEDBACK_PEG_RADIUS, arcade.color.WHITE, 1)
                peg_index += 1
            for _ in range(white_pegs):
                px = fb_x_start + (peg_index % 2) * FEEDBACK_PEG_SPACING
                py = y + (peg_index // 2) * FEEDBACK_PEG_SPACING - FEEDBACK_PEG_SPACING / 2
                arcade.draw_circle_filled(px, py, FEEDBACK_PEG_RADIUS, arcade.color.WHITE)
                arcade.draw_circle_outline(px, py, FEEDBACK_PEG_RADIUS, arcade.color.GRAY, 1)
                peg_index += 1

    # If game lost, reveal the secret code at the top
    if game.game_over and not game.won:
        secret_y = game._row_y(MAX_ATTEMPTS) + 10
        arcade.draw_text(
            "Secret:", BOARD_LEFT - 40, secret_y,
            arcade.color.LIGHT_CORAL, font_size=12,
            anchor_x="center", anchor_y="center",
        )
        for slot in range(NUM_SLOTS):
            x = game._slot_x(slot)
            color = CODE_COLORS[game.secret_code[slot]]
            arcade.draw_circle_filled(x, secret_y, SLOT_RADIUS, color)
            arcade.draw_circle_outline(x, secret_y, SLOT_RADIUS, arcade.color.LIGHT_CORAL, 2)


def _draw_palette(game):
    palette_start_x = WIDTH / 2 - (NUM_COLORS - 1) * PALETTE_SPACING / 2
    for i, color in enumerate(CODE_COLORS):
        x = palette_start_x + i * PALETTE_SPACING
        arcade.draw_circle_filled(x, PALETTE_Y, PALETTE_RADIUS, color)
        if i == game.selected_color:
            arcade.draw_circle_outline(x, PALETTE_Y, PALETTE_RADIUS + 4, HIGHLIGHT_COLOR, 3)
        else:
            arcade.draw_circle_outline(x, PALETTE_Y, PALETTE_RADIUS, (160, 160, 160), 1)

    # Label
    arcade.draw_text(
        "Select a color:", WIDTH / 2, PALETTE_Y + 35,
        arcade.color.LIGHT_GRAY, font_size=12,
        anchor_x="center", anchor_y="center",
    )


def _draw_game_over_message(game):
    # Semi-transparent overlay
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 400, 120), (0, 0, 0, 180))
    arcade.draw_rect_outline(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 400, 120), arcade.color.WHITE, 2)
    if game.won:
        msg = f"You Win! Guessed in {len(game.guesses)} attempt(s)!"
        color = arcade.color.LIGHT_GREEN
    else:
        msg = "Game Over! You ran out of attempts."
        color = arcade.color.LIGHT_CORAL
    arcade.draw_text(
        msg, WIDTH / 2, HEIGHT / 2 + 15,
        color, font_size=20,
        anchor_x="center", anchor_y="center", bold=True,
    )
    arcade.draw_text(
        "Click 'New Game' to play again.",
        WIDTH / 2, HEIGHT / 2 - 25,
        arcade.color.LIGHT_GRAY, font_size=14,
        anchor_x="center", anchor_y="center",
    )
