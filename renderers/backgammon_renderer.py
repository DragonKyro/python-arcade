"""
Renderer for the Backgammon game view.
All arcade.draw_* calls for Backgammon are centralized here.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Board layout
BOARD_LEFT = 50
BOARD_RIGHT = 750
BOARD_TOP = 540
BOARD_BOTTOM = 80
BOARD_WIDTH = BOARD_RIGHT - BOARD_LEFT
BOARD_HEIGHT = BOARD_TOP - BOARD_BOTTOM
BAR_WIDTH = 40
BAR_LEFT = (BOARD_LEFT + BOARD_RIGHT) // 2 - BAR_WIDTH // 2
BAR_RIGHT = BAR_LEFT + BAR_WIDTH

# Point (triangle) dimensions
POINT_WIDTH = (BOARD_WIDTH - BAR_WIDTH) // 12
HALF_HEIGHT = (BOARD_HEIGHT) // 2 - 10

# Checker
CHECKER_RADIUS = POINT_WIDTH // 2 - 2
CHECKER_STACK_OFFSET = CHECKER_RADIUS * 1.8

# Colors
BG_COLOR = (40, 60, 40)
BOARD_COLOR = (34, 100, 34)
DARK_POINT_COLOR = (139, 69, 19)
LIGHT_POINT_COLOR = (210, 180, 140)
BAR_COLOR = (80, 50, 20)
PLAYER_COLOR = (240, 240, 230)  # White
PLAYER_OUTLINE = (200, 200, 190)
AI_COLOR = (100, 60, 30)  # Brown
AI_OUTLINE = (70, 40, 20)
HIGHLIGHT_COLOR = (255, 255, 0, 120)
VALID_DEST_COLOR = (0, 255, 0, 100)

# Game states (needed by renderer for conditional drawing)
STATE_PLAYER_ROLL = "player_roll"
STATE_GAME_OVER = "game_over"


def draw(game):
    """Render the entire Backgammon game state."""
    _draw_board_bg()
    _draw_points(game)
    _draw_bar_area(game)
    _draw_checkers(game)
    _draw_bar_checkers(game)
    _draw_off_area(game)
    _draw_valid_destinations(game)
    _draw_dice_display(game)
    _draw_ui(game)
    _draw_message(game)

    if game.state == STATE_GAME_OVER:
        _draw_game_over(game)


def _draw_board_bg():
    # Main board background
    cx = (BOARD_LEFT + BOARD_RIGHT) / 2
    cy = (BOARD_BOTTOM + BOARD_TOP) / 2
    arcade.draw_rect_filled(arcade.XYWH(cx, cy, BOARD_WIDTH, BOARD_HEIGHT), BOARD_COLOR)
    arcade.draw_rect_outline(arcade.XYWH(cx, cy, BOARD_WIDTH, BOARD_HEIGHT), (20, 20, 20), 3)

    # Bar
    bar_cx = (BAR_LEFT + BAR_RIGHT) / 2
    arcade.draw_rect_filled(arcade.XYWH(bar_cx, cy, BAR_WIDTH, BOARD_HEIGHT), BAR_COLOR)


def _draw_points(game):
    """Draw 24 triangular points."""
    for i in range(24):
        x, base_y, tip_y, is_top = game._point_tip_xy(i)
        color = DARK_POINT_COLOR if i % 2 == 0 else LIGHT_POINT_COLOR

        half_w = POINT_WIDTH // 2 - 1
        if is_top:
            # Triangle pointing down
            arcade.draw_triangle_filled(
                x - half_w, base_y,
                x + half_w, base_y,
                x, tip_y,
                color
            )
        else:
            # Triangle pointing up
            arcade.draw_triangle_filled(
                x - half_w, base_y,
                x + half_w, base_y,
                x, tip_y,
                color
            )

        # Highlight selected point
        if game.selected_point == i:
            arcade.draw_triangle_filled(
                x - half_w, base_y,
                x + half_w, base_y,
                x, tip_y,
                HIGHLIGHT_COLOR
            )


def _draw_checkers(game):
    """Draw all checkers on the board points."""
    for i in range(24):
        count = game.board[i]
        if count == 0:
            continue

        num = abs(count)
        color = PLAYER_COLOR if count > 0 else AI_COLOR
        outline = PLAYER_OUTLINE if count > 0 else AI_OUTLINE

        # If more than 5, compress stacking
        display_count = min(num, 5)
        for s in range(display_count):
            cx, cy = game._checker_xy(i, s)
            arcade.draw_circle_filled(cx, cy, CHECKER_RADIUS, color)
            arcade.draw_circle_outline(cx, cy, CHECKER_RADIUS, outline, 2)

        # Show count if more than 5
        if num > 5:
            cx, cy = game._checker_xy(i, display_count - 1)
            txt = game.txt_checker_counts[i]
            txt.text = str(num)
            txt.x = cx
            txt.y = cy
            txt.draw()

    # Draw point numbers along edges for reference
    for i in range(24):
        game.txt_point_labels[i].draw()


def _draw_bar_area(game):
    """Draw the bar label."""
    game.txt_bar_label.draw()


def _draw_bar_checkers(game):
    """Draw checkers on the bar."""
    bar_cx = (BAR_LEFT + BAR_RIGHT) / 2

    # Player bar checkers (bottom half)
    for s in range(game.bar[0]):
        y = BOARD_BOTTOM + HALF_HEIGHT // 2 - 30 + s * CHECKER_STACK_OFFSET
        arcade.draw_circle_filled(bar_cx, y, CHECKER_RADIUS - 2, PLAYER_COLOR)
        arcade.draw_circle_outline(bar_cx, y, CHECKER_RADIUS - 2, PLAYER_OUTLINE, 2)

    # AI bar checkers (top half)
    for s in range(game.bar[1]):
        y = BOARD_TOP - HALF_HEIGHT // 2 + 30 - s * CHECKER_STACK_OFFSET
        arcade.draw_circle_filled(bar_cx, y, CHECKER_RADIUS - 2, AI_COLOR)
        arcade.draw_circle_outline(bar_cx, y, CHECKER_RADIUS - 2, AI_OUTLINE, 2)

    # Highlight bar if selected
    if game.selected_point == 'bar':
        bar_cy = BOARD_BOTTOM + HALF_HEIGHT // 2 - 10
        arcade.draw_rect_filled(arcade.XYWH(bar_cx, bar_cy, BAR_WIDTH - 4, 60), HIGHLIGHT_COLOR)


def _draw_off_area(game):
    """Draw bearing off tray on the right side."""
    off_x = BOARD_RIGHT + 20
    # Player off (bottom)
    game.txt_off_player_label.draw()
    if game.off[0] > 0:
        game.txt_off_player_count.text = str(game.off[0])
        game.txt_off_player_count.draw()
        # Draw small stack
        for s in range(min(game.off[0], 5)):
            y = BOARD_BOTTOM + 10 + s * 12
            arcade.draw_rect_filled(arcade.XYWH(off_x, y, 20, 10), PLAYER_COLOR)
            arcade.draw_rect_outline(arcade.XYWH(off_x, y, 20, 10), PLAYER_OUTLINE, 1)

    # AI off (top)
    game.txt_off_ai_label.draw()
    if game.off[1] > 0:
        game.txt_off_ai_count.text = str(game.off[1])
        game.txt_off_ai_count.draw()
        for s in range(min(game.off[1], 5)):
            y = BOARD_TOP - 10 - s * 12
            arcade.draw_rect_filled(arcade.XYWH(off_x, y, 20, 10), AI_COLOR)
            arcade.draw_rect_outline(arcade.XYWH(off_x, y, 20, 10), AI_OUTLINE, 1)


def _draw_valid_destinations(game):
    """Highlight valid destination points."""
    for dest in game.valid_destinations:
        if dest == 'off':
            off_x = BOARD_RIGHT + 20
            arcade.draw_rect_filled(arcade.XYWH(off_x, BOARD_BOTTOM + HALF_HEIGHT // 2 - 40, 30, 30), VALID_DEST_COLOR)
        else:
            x, base_y, tip_y, is_top = game._point_tip_xy(dest)
            half_w = POINT_WIDTH // 2 - 1
            arcade.draw_triangle_filled(
                x - half_w, base_y,
                x + half_w, base_y,
                x, tip_y,
                VALID_DEST_COLOR,
            )


def _draw_dice_display(game):
    """Draw dice values in the center."""
    if not game.dice:
        return
    remaining = game._remaining_dice()
    mid_x = (BOARD_LEFT + BOARD_RIGHT) / 2
    mid_y = (BOARD_BOTTOM + BOARD_TOP) / 2

    total = len(game.dice)
    start_x = mid_x - (total - 1) * 22

    for idx, die_val in enumerate(game.dice):
        dx = start_x + idx * 44
        dy = mid_y + 30

        # Count how many of this value are used vs total
        all_of_val = [j for j, d in enumerate(game.dice) if d == die_val]
        used_count = game.used_dice.count(die_val)
        # Mark first N of this die value as used
        rank_among_same = [j for j in all_of_val].index(idx) if idx in all_of_val else 0
        is_used = rank_among_same < used_count

        bg = (200, 200, 200) if not is_used else (100, 100, 100)
        fg = arcade.color.BLACK if not is_used else (60, 60, 60)

        arcade.draw_rect_filled(arcade.XYWH(dx, dy, 36, 36), bg)
        arcade.draw_rect_outline(arcade.XYWH(dx, dy, 36, 36), (50, 50, 50), 2)

        txt = game.txt_dice[idx]
        txt.text = str(die_val)
        txt.x = dx
        txt.y = dy
        txt.color = fg
        txt.draw()


def _draw_ui(game):
    """Draw buttons and labels."""
    # Title
    game.txt_title.draw()

    # Back button
    _draw_button(55, HEIGHT - 20, 90, 30, game.txt_btn_back, (60, 60, 100))

    # New Game button
    _draw_button(WIDTH - 65, HEIGHT - 20, 110, 30, game.txt_btn_new_game, (30, 100, 30))
    # Help button
    _draw_button(WIDTH - 135, HEIGHT - 20, 40, 30, game.txt_btn_help, arcade.color.DARK_SLATE_BLUE)

    # Roll Dice button
    if game.state == STATE_PLAYER_ROLL:
        _draw_button(WIDTH / 2, HEIGHT - 50, 120, 32, game.txt_btn_roll_dice, (150, 50, 50))

    # Player / AI labels
    game.txt_label_player.draw()
    game.txt_label_ai.draw()

    # Bar counts
    if game.bar[0] > 0:
        game.txt_bar_player.text = f"W:{game.bar[0]}"
        game.txt_bar_player.draw()
    if game.bar[1] > 0:
        game.txt_bar_ai.text = f"B:{game.bar[1]}"
        game.txt_bar_ai.draw()


def _draw_message(game):
    """Draw status message at the bottom."""
    game.txt_message.text = game.message
    game.txt_message.draw()


def _draw_button(cx, cy, w, h, txt_obj, color):
    arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), color)
    arcade.draw_rect_outline(arcade.XYWH(cx, cy, w, h), arcade.color.WHITE, 1)
    txt_obj.draw()


def _draw_game_over(game):
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 400, 120), (0, 0, 0, 200))
    arcade.draw_rect_outline(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 400, 120), arcade.color.WHITE, 2)
    if game.winner == "Player":
        msg = "You Win!"
        color = arcade.color.LIGHT_GREEN
    else:
        msg = "AI Wins!"
        color = arcade.color.LIGHT_CORAL

    game.txt_game_over_msg.text = msg
    game.txt_game_over_msg.color = color
    game.txt_game_over_msg.draw()

    game.txt_game_over_hint.draw()
