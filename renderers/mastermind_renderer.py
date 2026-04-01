"""Renderer for Mastermind — all drawing code lives here."""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Game constants (needed for rendering)
NUM_SLOTS = 4
MAX_ATTEMPTS = 10
NUM_COLORS = 6

# The 6 code colors
CODE_COLORS = [
    arcade.color.RED,
    arcade.color.BLUE,
    arcade.color.GREEN,
    arcade.color.YELLOW,
    arcade.color.ORANGE,
    arcade.color.PURPLE,
]

# Layout constants
BOARD_LEFT = 200
BOARD_TOP = 540
ROW_HEIGHT = 40
SLOT_RADIUS = 14
SLOT_SPACING = 50
FEEDBACK_OFFSET_X = 240
FEEDBACK_PEG_RADIUS = 6
FEEDBACK_PEG_SPACING = 16

PALETTE_Y = 40
PALETTE_SPACING = 60
PALETTE_RADIUS = 20

EMPTY_COLOR = (80, 80, 80)
HIGHLIGHT_COLOR = arcade.color.WHITE


def draw(game):
    """Render the entire Mastermind game state."""
    # Title
    game.txt_title.draw()

    # Back button
    _draw_button(game, 60, HEIGHT - 30, 90, 36, "back")

    # New Game button
    _draw_button(game, WIDTH - 70, HEIGHT - 30, 110, 36, "new_game")

    # Help button
    _draw_button(game, WIDTH - 140, HEIGHT - 30, 40, 36, "help")

    # Draw the guess board
    _draw_board(game)

    # Draw color palette
    _draw_palette(game)

    # Draw submit button
    if not game.game_over:
        all_filled = all(c is not None for c in game.current_guess)
        btn_color = arcade.color.DARK_BLUE if all_filled else (60, 60, 80)
        row_y = game._row_y(game.current_row)
        arcade.draw_rect_filled(arcade.XYWH(WIDTH - 70, row_y, 100, 32), btn_color)
        arcade.draw_rect_outline(arcade.XYWH(WIDTH - 70, row_y, 100, 32), arcade.color.WHITE)
        game.txt_submit.y = row_y
        game.txt_submit.draw()

    # Draw win/lose message
    if game.game_over:
        _draw_game_over_message(game)


def _draw_button(game, cx, cy, w, h, btn_key):
    arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), {
        "back": arcade.color.DARK_SLATE_BLUE,
        "new_game": arcade.color.DARK_GREEN,
        "help": arcade.color.DARK_SLATE_BLUE,
    }[btn_key])
    arcade.draw_rect_outline(arcade.XYWH(cx, cy, w, h), arcade.color.WHITE)
    txt_obj = {
        "back": game.txt_back,
        "new_game": game.txt_new_game,
        "help": game.txt_help,
    }[btn_key]
    txt_obj.draw()


def _draw_board(game):
    for row in range(MAX_ATTEMPTS):
        y = game._row_y(row)

        # Row number label
        game.txt_row_numbers[row].draw()

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
        game.txt_secret_label.y = secret_y
        game.txt_secret_label.draw()
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
    game.txt_select_color.draw()


def _draw_game_over_message(game):
    # Semi-transparent overlay
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 400, 120), (0, 0, 0, 180))
    arcade.draw_rect_outline(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 400, 120), arcade.color.WHITE, 2)
    if game.won:
        game.txt_game_over_msg.text = f"You Win! Guessed in {len(game.guesses)} attempt(s)!"
        game.txt_game_over_msg.color = arcade.color.LIGHT_GREEN
    else:
        game.txt_game_over_msg.text = "Game Over! You ran out of attempts."
        game.txt_game_over_msg.color = arcade.color.LIGHT_CORAL
    game.txt_game_over_msg.draw()
    game.txt_game_over_hint.draw()
