"""
Renderer for the Breakout game.
All drawing code extracted from games/breakout.py.
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
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 15

# Ball
BALL_RADIUS = 6

# Brick
BRICK_WIDTH = 70
BRICK_HEIGHT = 20

# Colors
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (60, 60, 60)
PADDLE_COLOR = (220, 220, 230)
OVERLAY_COLOR = (0, 0, 0, 180)
BRICK_OUTLINE_COLOR = (30, 30, 30)


def draw(game):
    """Render the entire Breakout game state."""
    _draw_bricks(game)
    _draw_paddle(game)
    _draw_ball(game)
    _draw_top_bar(game)
    _draw_hud(game)

    if game.state == "ready":
        game.txt_launch.draw()
    elif game.state == "level_complete":
        _draw_level_complete(game)
    elif game.state == "game_over":
        _draw_game_over(game)


def _draw_top_bar(game):
    """Draw the top bar with Back and Help buttons."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT - TOP_BAR_HEIGHT / 2, WIDTH, TOP_BAR_HEIGHT),
        (20, 20, 20),
    )
    arcade.draw_line(0, PLAY_TOP, WIDTH, PLAY_TOP, GRAY, 1)

    game.btn_back.draw(game.btn_back.contains(game.mouse_x, game.mouse_y))
    game.btn_help.draw(game.btn_help.contains(game.mouse_x, game.mouse_y))


def _draw_hud(game):
    """Draw score, lives, and level text in the top bar."""
    game.txt_score.text = f"Score: {game.score}"
    game.txt_score.draw()

    game.txt_lives.text = f"Lives: {game.lives}"
    game.txt_lives.draw()

    game.txt_level.text = f"Level {game.level}"
    game.txt_level.draw()


def _draw_paddle(game):
    """Draw the player paddle."""
    arcade.draw_rect_filled(
        arcade.XYWH(game.paddle_x, game.paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT),
        PADDLE_COLOR,
    )


def _draw_ball(game):
    """Draw the ball."""
    arcade.draw_circle_filled(game.ball_x, game.ball_y, BALL_RADIUS, WHITE)


def _draw_bricks(game):
    """Draw all alive bricks with outlines."""
    for brick in game.bricks:
        if not brick['alive']:
            continue
        bx, by = brick['x'], brick['y']
        color = brick['color']

        # Filled brick with slight border for a clean look
        arcade.draw_rect_filled(
            arcade.XYWH(bx, by, BRICK_WIDTH, BRICK_HEIGHT),
            color,
        )
        arcade.draw_rect_outline(
            arcade.XYWH(bx, by, BRICK_WIDTH, BRICK_HEIGHT),
            BRICK_OUTLINE_COLOR,
            1,
        )


def _draw_level_complete(game):
    """Draw level complete overlay message."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, PLAY_HEIGHT / 2, WIDTH, PLAY_HEIGHT),
        OVERLAY_COLOR,
    )
    game.txt_level_complete.text = f"Level {game.level} Complete!"
    game.txt_level_complete.draw()


def _draw_game_over(game):
    """Draw the game over overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, PLAY_HEIGHT / 2, WIDTH, PLAY_HEIGHT),
        OVERLAY_COLOR,
    )
    game.txt_game_over.draw()
    game.txt_final_score.text = f"Final Score: {game.score}"
    game.txt_final_score.draw()
    game.btn_play_again.draw(
        game.btn_play_again.contains(game.mouse_x, game.mouse_y)
    )
