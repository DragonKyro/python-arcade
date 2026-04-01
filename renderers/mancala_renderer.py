"""
Renderer for the Mancala game view.
All arcade.draw_* calls for Mancala are centralized here.
"""

import arcade
import math

# Window constants
WIDTH = 800
HEIGHT = 600

# Board layout constants
BOARD_CX = WIDTH / 2
BOARD_CY = HEIGHT / 2
BOARD_W = 700
BOARD_H = 260
BOARD_CORNER = 60

STORE_W = 70
STORE_H = 180
PIT_RADIUS = 36
PIT_SPACING = 85
PITS_START_X = BOARD_CX - 2.5 * PIT_SPACING

PLAYER_ROW_Y = BOARD_CY - 55
AI_ROW_Y = BOARD_CY + 55
STORE_Y = BOARD_CY

LEFT_STORE_X = BOARD_CX - BOARD_W / 2 + STORE_W / 2 + 15
RIGHT_STORE_X = BOARD_CX + BOARD_W / 2 - STORE_W / 2 - 15

STONE_RADIUS = 5
STONE_COLOR = (180, 140, 100)

BOARD_COLOR = (101, 67, 33)
BOARD_OUTLINE_COLOR = (60, 40, 20)
PIT_COLOR = (70, 45, 20)
PIT_HIGHLIGHT_COLOR = (140, 200, 140)
STORE_COLOR = (80, 50, 25)

PLAYER_SIDE = 0
AI_SIDE = 1


def draw(game):
    """Render the entire Mancala game state."""
    # Title
    game.txt_title.draw()

    # Buttons
    _draw_button(60, HEIGHT - 30, 90, 36, game.txt_btn_back, arcade.color.DARK_SLATE_BLUE)
    _draw_button(WIDTH - 70, HEIGHT - 30, 110, 36, game.txt_btn_new_game, arcade.color.DARK_GREEN)
    _draw_button(WIDTH - 140, HEIGHT - 30, 40, 36, game.txt_btn_help, arcade.color.DARK_SLATE_BLUE)

    _draw_board()
    _draw_pits(game)
    _draw_stores(game)
    _draw_labels(game)

    if game.extra_turn_timer > 0:
        game.txt_extra_turn.text = game.extra_turn_text
        game.txt_extra_turn.draw()

    if game.game_over:
        _draw_game_over(game)


def _draw_button(cx, cy, w, h, txt_obj, color):
    arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), color)
    arcade.draw_rect_outline(arcade.XYWH(cx, cy, w, h), arcade.color.WHITE)
    txt_obj.draw()


def _draw_board():
    """Draw the rounded board background."""
    arcade.draw_rect_filled(arcade.XYWH(BOARD_CX, BOARD_CY, BOARD_W, BOARD_H), BOARD_COLOR)
    arcade.draw_rect_outline(arcade.XYWH(BOARD_CX, BOARD_CY, BOARD_W, BOARD_H), BOARD_OUTLINE_COLOR, 3)
    # Rounded ends (circles at left/right)
    arcade.draw_circle_filled(BOARD_CX - BOARD_W / 2, BOARD_CY, BOARD_H / 2, BOARD_COLOR)
    arcade.draw_circle_filled(BOARD_CX + BOARD_W / 2, BOARD_CY, BOARD_H / 2, BOARD_COLOR)
    arcade.draw_circle_outline(BOARD_CX - BOARD_W / 2, BOARD_CY, BOARD_H / 2, BOARD_OUTLINE_COLOR, 3)
    arcade.draw_circle_outline(BOARD_CX + BOARD_W / 2, BOARD_CY, BOARD_H / 2, BOARD_OUTLINE_COLOR, 3)


def _draw_pits(game):
    """Draw all 12 pits with stones."""
    for i in range(6):
        px = game._pit_x(i)

        # --- Player pit (bottom row) ---
        is_valid = (
            game.player_turn
            and not game.game_over
            and game.pits[PLAYER_SIDE][i] > 0
        )
        is_hovered = is_valid and game.hovered_pit == i
        pit_col = PIT_HIGHLIGHT_COLOR if is_hovered else (PIT_COLOR if not is_valid else (90, 65, 35))
        outline_col = arcade.color.LIGHT_GREEN if is_valid else BOARD_OUTLINE_COLOR

        arcade.draw_circle_filled(px, PLAYER_ROW_Y, PIT_RADIUS, pit_col)
        arcade.draw_circle_outline(px, PLAYER_ROW_Y, PIT_RADIUS, outline_col, 2)
        _draw_stones_in_pit(game, px, PLAYER_ROW_Y, game.pits[PLAYER_SIDE][i], i, is_player=True)

        # --- AI pit (top row, mirrored: AI pit 0 is above player pit 5) ---
        ai_display_index = 5 - i
        ai_px = game._pit_x(i)
        arcade.draw_circle_filled(ai_px, AI_ROW_Y, PIT_RADIUS, PIT_COLOR)
        arcade.draw_circle_outline(ai_px, AI_ROW_Y, PIT_RADIUS, BOARD_OUTLINE_COLOR, 2)
        _draw_stones_in_pit(game, ai_px, AI_ROW_Y, game.pits[AI_SIDE][ai_display_index], i, is_player=False)


def _draw_stones_in_pit(game, cx, cy, count, pit_index, is_player):
    """Draw stone count and small circles if count <= 10."""
    if count <= 0:
        return

    # Draw small stone circles for counts up to 10
    if count <= 10:
        positions = _stone_positions(cx, cy, count)
        for sx, sy in positions:
            arcade.draw_circle_filled(sx, sy, STONE_RADIUS, STONE_COLOR)
            arcade.draw_circle_outline(sx, sy, STONE_RADIUS, (120, 90, 60), 1)

    # Always draw count text
    if is_player:
        txt = game.txt_pit_counts[pit_index]
    else:
        txt = game.txt_ai_pit_counts[pit_index]
    txt.text = str(count)
    txt.x = cx
    txt.y = cy - PIT_RADIUS - 12
    txt.draw()


def _stone_positions(cx, cy, count):
    """Return a list of (x, y) positions to draw stones in a pit."""
    positions = []
    if count == 1:
        positions.append((cx, cy))
    elif count <= 4:
        offsets = [(-8, -8), (8, -8), (-8, 8), (8, 8)]
        for k in range(count):
            positions.append((cx + offsets[k][0], cy + offsets[k][1]))
    elif count <= 10:
        # Arrange in a circle
        radius = min(18, PIT_RADIUS - STONE_RADIUS - 4)
        for k in range(count):
            angle = 2 * math.pi * k / count - math.pi / 2
            sx = cx + radius * math.cos(angle)
            sy = cy + radius * math.sin(angle)
            positions.append((sx, sy))
    return positions


def _draw_stores(game):
    """Draw the two stores on left and right ends."""
    # AI store (left)
    arcade.draw_rect_filled(arcade.XYWH(LEFT_STORE_X, STORE_Y, STORE_W, STORE_H), STORE_COLOR)
    arcade.draw_rect_outline(arcade.XYWH(LEFT_STORE_X, STORE_Y, STORE_W, STORE_H), BOARD_OUTLINE_COLOR, 2)
    game.txt_ai_store_count.text = str(game.stores[AI_SIDE])
    game.txt_ai_store_count.draw()
    game.txt_ai_store_label.draw()

    # Player store (right)
    arcade.draw_rect_filled(arcade.XYWH(RIGHT_STORE_X, STORE_Y, STORE_W, STORE_H), STORE_COLOR)
    arcade.draw_rect_outline(arcade.XYWH(RIGHT_STORE_X, STORE_Y, STORE_W, STORE_H), BOARD_OUTLINE_COLOR, 2)
    game.txt_player_store_count.text = str(game.stores[PLAYER_SIDE])
    game.txt_player_store_count.draw()
    game.txt_player_store_label.draw()


def _draw_labels(game):
    """Draw row labels and turn indicator."""
    # Turn indicator
    if not game.game_over:
        if game.player_turn:
            turn_text = "Your turn -- click a highlighted pit"
        else:
            turn_text = "AI is thinking..."
        game.txt_turn.text = turn_text
        game.txt_turn.draw()

    # Pit index labels for player
    for i in range(6):
        game.txt_pit_index_labels[i].draw()


def _draw_game_over(game):
    """Draw game over overlay."""
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 420, 140), (0, 0, 0, 200))
    arcade.draw_rect_outline(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 420, 140), arcade.color.WHITE, 2)

    if game.winner == "Tie":
        msg = "It's a tie!"
        color = arcade.color.LIGHT_STEEL_BLUE
    elif game.winner == "Player":
        msg = "You win!"
        color = arcade.color.LIGHT_GREEN
    else:
        msg = "AI wins!"
        color = arcade.color.LIGHT_CORAL

    score_msg = f"You: {game.stores[PLAYER_SIDE]}  --  AI: {game.stores[AI_SIDE]}"

    game.txt_game_over_msg.text = msg
    game.txt_game_over_msg.color = color
    game.txt_game_over_msg.draw()

    game.txt_game_over_score.text = score_msg
    game.txt_game_over_score.draw()

    game.txt_game_over_hint.draw()
