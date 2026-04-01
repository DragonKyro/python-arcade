"""
Renderer for the Pong game.
All drawing code extracted from games/pong.py.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
PLAY_TOP = HEIGHT - TOP_BAR_HEIGHT
PLAY_HEIGHT = PLAY_TOP

# Paddle
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 80

# Ball
BALL_SIZE = 10

# Colors
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (50, 50, 50)
OVERLAY_COLOR = (0, 0, 0, 180)


def draw(game):
    """Render the entire Pong game state."""
    if game.state == "select":
        _draw_top_bar(game)
        _draw_difficulty_select(game)
        return

    # Draw play area
    _draw_court()
    _draw_paddles(game)
    _draw_ball(game)
    _draw_scores(game)
    _draw_top_bar(game)

    if game.state == "serve":
        _draw_serve_message(game)
    elif game.state == "gameover":
        _draw_gameover(game)


def _draw_top_bar(game):
    """Draw the top bar with Back, New Game, and Help buttons."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT - TOP_BAR_HEIGHT / 2, WIDTH, TOP_BAR_HEIGHT),
        (20, 20, 20),
    )
    arcade.draw_line(0, PLAY_TOP, WIDTH, PLAY_TOP, GRAY, 1)

    game.btn_back.draw(game.btn_back.contains(game.mouse_x, game.mouse_y))
    game.btn_new.draw(game.btn_new.contains(game.mouse_x, game.mouse_y))
    game.btn_help.draw(game.btn_help.contains(game.mouse_x, game.mouse_y))


def _draw_court():
    """Draw the center dashed line and border."""
    dash_height = 12
    gap = 10
    y = 0
    while y < PLAY_HEIGHT:
        top = min(y + dash_height, PLAY_HEIGHT)
        mid_y = (y + top) / 2
        h = top - y
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, mid_y, 3, h),
            DARK_GRAY,
        )
        y += dash_height + gap


def _draw_paddles(game):
    """Draw player and AI paddles."""
    arcade.draw_rect_filled(
        arcade.XYWH(game.player_x, game.player_y, PADDLE_WIDTH, PADDLE_HEIGHT),
        WHITE,
    )
    arcade.draw_rect_filled(
        arcade.XYWH(game.ai_x, game.ai_y, PADDLE_WIDTH, PADDLE_HEIGHT),
        WHITE,
    )


def _draw_ball(game):
    """Draw the ball."""
    arcade.draw_circle_filled(game.ball_x, game.ball_y, BALL_SIZE / 2, WHITE)


def _draw_scores(game):
    """Draw scores at top of play area."""
    game.txt_player_score.text = str(game.player_score)
    game.txt_player_score.draw()
    game.txt_ai_score.text = str(game.ai_score)
    game.txt_ai_score.draw()


def _draw_difficulty_select(game):
    """Draw difficulty selection screen."""
    game.txt_title.draw()
    game.txt_select_difficulty.draw()
    for btn in game.difficulty_buttons:
        btn.draw(btn.contains(game.mouse_x, game.mouse_y))


def _draw_serve_message(game):
    """Draw a brief 'Get Ready' message during serve delay."""
    game.txt_serve.draw()


def _draw_gameover(game):
    """Draw the game over overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, PLAY_HEIGHT / 2, WIDTH, PLAY_HEIGHT),
        OVERLAY_COLOR,
    )
    game.txt_winner.text = game.winner_text
    game.txt_winner.draw()
    game.txt_final_score.text = f"{game.player_score} - {game.ai_score}"
    game.txt_final_score.draw()
    game.btn_play_again.draw(
        game.btn_play_again.contains(game.mouse_x, game.mouse_y)
    )
