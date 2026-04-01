"""
Renderer for the Nim game view.
All arcade.draw_* calls for Nim are centralized here.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Drawing constants
STONE_RADIUS = 22
STONE_SPACING = 56
ROW_SPACING = 70
BOARD_TOP = HEIGHT - 140

# Colors
STONE_COLOR = (100, 160, 220)
STONE_OUTLINE = (60, 100, 160)
SELECTED_COLOR = (255, 90, 90)
SELECTED_OUTLINE = (180, 40, 40)
REMOVED_COLOR = (50, 50, 60)
OVERLAY_BG = (0, 0, 0, 170)

# Button dimensions
BUTTON_W = 100
BUTTON_H = 36
TAKE_BUTTON_W = 120
TAKE_BUTTON_H = 40

# Game states (needed by renderer for conditional drawing)
STATE_PLAYER_TURN = "player_turn"
STATE_AI_THINKING = "ai_thinking"
STATE_GAME_OVER = "game_over"


def draw(game):
    """Render the entire Nim game state."""
    _draw_buttons(game)
    _draw_turn_indicator(game)
    _draw_board(game)
    _draw_take_button(game)
    if game.state == STATE_GAME_OVER:
        _draw_overlay(game)


def _draw_buttons(game):
    # Back button (top-left)
    bx, by = 60, HEIGHT - 30
    arcade.draw_rect_filled(
        arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.DARK_GRAY
    )
    arcade.draw_rect_outline(
        arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.WHITE, 2
    )
    game.txt_btn_back.draw()

    # New Game button (top-right)
    nx, ny = WIDTH - 70, HEIGHT - 30
    arcade.draw_rect_filled(
        arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.DARK_GREEN
    )
    arcade.draw_rect_outline(
        arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.WHITE, 2
    )
    game.txt_btn_new_game.draw()

    # Help button
    game.help_button.draw()

    # Title
    game.txt_title.draw()


def _draw_turn_indicator(game):
    if game.state == STATE_PLAYER_TURN:
        msg = "Your turn - click stones to select, then Take"
        color = arcade.color.WHITE
    elif game.state == STATE_AI_THINKING:
        msg = "AI is thinking..."
        color = arcade.color.YELLOW
    else:
        msg = ""
        color = arcade.color.WHITE

    if msg:
        game.txt_turn.text = msg
        game.txt_turn.color = color
        game.txt_turn.draw()


def _draw_board(game):
    for r in range(len(game.max_rows)):
        for s in range(game.max_rows[r]):
            cx, cy = game._stone_center(r, s)
            if s >= game.rows[r]:
                # Removed stone -- dim placeholder
                arcade.draw_circle_filled(cx, cy, STONE_RADIUS, REMOVED_COLOR)
            elif (
                game.selected_row == r
                and game.selected_from >= 0
                and s >= game.selected_from
            ):
                # Selected stone
                arcade.draw_circle_filled(cx, cy, STONE_RADIUS, SELECTED_COLOR)
                arcade.draw_circle_outline(cx, cy, STONE_RADIUS, SELECTED_OUTLINE, 3)
            else:
                # Normal stone
                arcade.draw_circle_filled(cx, cy, STONE_RADIUS, STONE_COLOR)
                arcade.draw_circle_outline(cx, cy, STONE_RADIUS, STONE_OUTLINE, 2)

        # Row label
        label_x = (WIDTH - (game.max_rows[r] - 1) * STONE_SPACING) / 2 - 40
        label_y = BOARD_TOP - r * ROW_SPACING
        txt = game.txt_row_labels[r]
        txt.text = f"{game.rows[r]}"
        txt.x = label_x
        txt.y = label_y
        txt.draw()


def _draw_take_button(game):
    count = game._selection_count()
    if count <= 0 or game.state != STATE_PLAYER_TURN:
        return
    tx, ty = WIDTH // 2, 40
    arcade.draw_rect_filled(
        arcade.XYWH(tx, ty, TAKE_BUTTON_W, TAKE_BUTTON_H), arcade.color.DARK_RED
    )
    arcade.draw_rect_outline(
        arcade.XYWH(tx, ty, TAKE_BUTTON_W, TAKE_BUTTON_H), arcade.color.WHITE, 2
    )
    game.txt_take_btn.text = f"Take {count}"
    game.txt_take_btn.draw()


def _draw_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_BG
    )
    if game.winner == "player":
        msg = "You Win!"
        color = arcade.color.GREEN
    else:
        msg = "AI Wins!"
        color = arcade.color.RED

    game.txt_game_over_msg.text = msg
    game.txt_game_over_msg.color = color
    game.txt_game_over_msg.draw()

    game.txt_game_over_rule.draw()
    game.txt_game_over_hint.draw()
