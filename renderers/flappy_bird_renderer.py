"""
Renderer for the Flappy Bird game.
All drawing code extracted from games/flappy_bird.py.
"""

import arcade
import math

# Window constants
WIDTH = 800
HEIGHT = 600

# Game states
WAITING = 0
GAME_OVER = 2

# Layout
TOP_BAR_HEIGHT = 50
GROUND_HEIGHT = 60

# Bird
BIRD_X = 150
BIRD_RADIUS = 18

# Pipes
PIPE_WIDTH = 60
PIPE_CAP_WIDTH = 72
PIPE_CAP_HEIGHT = 20
PIPE_GAP = 150

# Colors
SKY_COLOR = (135, 206, 235)
GROUND_COLOR = (139, 119, 69)
GROUND_TOP_COLOR = (100, 180, 70)
PIPE_COLOR = (76, 153, 0)
PIPE_CAP_COLOR = (60, 130, 0)
PIPE_OUTLINE_COLOR = (40, 90, 0)
BIRD_BODY_COLOR = (255, 215, 0)
BIRD_BEAK_COLOR = (255, 140, 0)
BIRD_EYE_WHITE = (255, 255, 255)
BIRD_EYE_PUPIL = (0, 0, 0)
CLOUD_COLOR = (255, 255, 255, 180)
OVERLAY_COLOR = (0, 0, 0, 150)

# Restart delay after game over
RESTART_DELAY = 0.5


def draw(game):
    """Render the entire Flappy Bird game state."""
    # Sky background
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        SKY_COLOR
    )

    # Clouds
    for cx, cy, cw, ch, _ in game.clouds:
        arcade.draw_circle_filled(cx, cy, ch * 0.6, CLOUD_COLOR)
        arcade.draw_circle_filled(cx - cw * 0.25, cy - ch * 0.15, ch * 0.5, CLOUD_COLOR)
        arcade.draw_circle_filled(cx + cw * 0.25, cy - ch * 0.1, ch * 0.55, CLOUD_COLOR)

    # Pipes
    for px, gap_y, _ in game.pipes:
        _draw_pipe(px, gap_y)

    # Ground
    _draw_ground(game)

    # Bird
    _draw_bird(game)

    # Score
    _draw_score(game)

    # UI overlay for states
    if game.state == WAITING:
        arcade.draw_text(
            "Press Space to Start",
            WIDTH / 2, HEIGHT / 2 + 80,
            (255, 255, 255),
            font_size=22,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        # Shadow
        arcade.draw_text(
            "Press Space to Start",
            WIDTH / 2 + 2, HEIGHT / 2 + 78,
            (0, 0, 0, 100),
            font_size=22,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )

    if game.state == GAME_OVER:
        _draw_game_over(game)

    # Top bar buttons
    game.back_button.draw(hover=game.back_button.contains(game.mouse_x, game.mouse_y))
    game.help_button.draw(hover=game.help_button.contains(game.mouse_x, game.mouse_y))


def _draw_pipe(px, gap_y):
    """Draw a pipe pair at position px with gap centered at gap_y."""
    gap_top = gap_y + PIPE_GAP / 2
    gap_bottom = gap_y - PIPE_GAP / 2

    # Bottom pipe
    bottom_h = gap_bottom - GROUND_HEIGHT
    if bottom_h > 0:
        bottom_cy = GROUND_HEIGHT + bottom_h / 2
        arcade.draw_rect_filled(
            arcade.XYWH(px, bottom_cy, PIPE_WIDTH, bottom_h),
            PIPE_COLOR
        )
        arcade.draw_rect_outline(
            arcade.XYWH(px, bottom_cy, PIPE_WIDTH, bottom_h),
            PIPE_OUTLINE_COLOR, 2
        )
        # Cap
        cap_y = gap_bottom - PIPE_CAP_HEIGHT / 2
        arcade.draw_rect_filled(
            arcade.XYWH(px, cap_y, PIPE_CAP_WIDTH, PIPE_CAP_HEIGHT),
            PIPE_CAP_COLOR
        )
        arcade.draw_rect_outline(
            arcade.XYWH(px, cap_y, PIPE_CAP_WIDTH, PIPE_CAP_HEIGHT),
            PIPE_OUTLINE_COLOR, 2
        )

    # Top pipe
    top_h = HEIGHT - gap_top
    if top_h > 0:
        top_cy = gap_top + top_h / 2
        arcade.draw_rect_filled(
            arcade.XYWH(px, top_cy, PIPE_WIDTH, top_h),
            PIPE_COLOR
        )
        arcade.draw_rect_outline(
            arcade.XYWH(px, top_cy, PIPE_WIDTH, top_h),
            PIPE_OUTLINE_COLOR, 2
        )
        # Cap
        cap_y = gap_top + PIPE_CAP_HEIGHT / 2
        arcade.draw_rect_filled(
            arcade.XYWH(px, cap_y, PIPE_CAP_WIDTH, PIPE_CAP_HEIGHT),
            PIPE_CAP_COLOR
        )
        arcade.draw_rect_outline(
            arcade.XYWH(px, cap_y, PIPE_CAP_WIDTH, PIPE_CAP_HEIGHT),
            PIPE_OUTLINE_COLOR, 2
        )


def _draw_ground(game):
    """Draw scrolling ground strip."""
    # Main ground
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, GROUND_HEIGHT / 2, WIDTH, GROUND_HEIGHT),
        GROUND_COLOR
    )
    # Green top strip
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, GROUND_HEIGHT - 4, WIDTH, 8),
        GROUND_TOP_COLOR
    )
    # Scrolling hash marks for texture
    for i in range(-1, WIDTH // 40 + 2):
        x = i * 40 - game.ground_offset
        arcade.draw_rect_filled(
            arcade.XYWH(x, GROUND_HEIGHT / 2, 2, GROUND_HEIGHT),
            (120, 100, 55)
        )


def _draw_bird(game):
    """Draw the bird with rotation based on velocity."""
    if game.state == WAITING:
        angle = 0
    else:
        angle = max(-70, min(25, game.bird_vel / 8))

    bx = BIRD_X
    by = game.bird_y
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    def rotate(dx, dy):
        return bx + dx * cos_a - dy * sin_a, by + dx * sin_a + dy * cos_a

    # Body (yellow circle)
    arcade.draw_circle_filled(bx, by, BIRD_RADIUS, BIRD_BODY_COLOR)

    # Wing (slightly darker, offset)
    wing_x, wing_y = rotate(-4, -2)
    wing_r = BIRD_RADIUS * 0.55
    arcade.draw_circle_filled(wing_x, wing_y, wing_r, (230, 180, 0))

    # Beak (orange triangle pointing right)
    beak_tip = rotate(BIRD_RADIUS + 10, 0)
    beak_top = rotate(BIRD_RADIUS - 2, 5)
    beak_bot = rotate(BIRD_RADIUS - 2, -5)
    arcade.draw_triangle_filled(
        beak_tip[0], beak_tip[1],
        beak_top[0], beak_top[1],
        beak_bot[0], beak_bot[1],
        BIRD_BEAK_COLOR
    )

    # Eye (white circle with black pupil)
    eye_x, eye_y = rotate(6, 6)
    arcade.draw_circle_filled(eye_x, eye_y, 5, BIRD_EYE_WHITE)
    pupil_x, pupil_y = rotate(8, 6)
    arcade.draw_circle_filled(pupil_x, pupil_y, 2.5, BIRD_EYE_PUPIL)


def _draw_score(game):
    """Draw the current score centered near the top."""
    score_text = str(game.score)
    # Shadow
    arcade.draw_text(
        score_text,
        WIDTH / 2 + 2, HEIGHT - 80 - 2,
        (0, 0, 0, 120),
        font_size=48,
        anchor_x="center",
        anchor_y="center",
        bold=True,
    )
    # Main
    arcade.draw_text(
        score_text,
        WIDTH / 2, HEIGHT - 80,
        (255, 255, 255),
        font_size=48,
        anchor_x="center",
        anchor_y="center",
        bold=True,
    )


def _draw_game_over(game):
    """Draw the game over overlay."""
    # Dim overlay
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        OVERLAY_COLOR
    )

    # Game Over text
    arcade.draw_text(
        "Game Over",
        WIDTH / 2, HEIGHT / 2 + 60,
        (255, 80, 80),
        font_size=40,
        anchor_x="center",
        anchor_y="center",
        bold=True,
    )

    # Score
    arcade.draw_text(
        f"Score: {game.score}",
        WIDTH / 2, HEIGHT / 2 + 10,
        (255, 255, 255),
        font_size=24,
        anchor_x="center",
        anchor_y="center",
    )

    # High score
    arcade.draw_text(
        f"Best: {game.high_score}",
        WIDTH / 2, HEIGHT / 2 - 25,
        (249, 226, 175),
        font_size=20,
        anchor_x="center",
        anchor_y="center",
    )

    # Restart prompt
    if game.game_over_timer >= RESTART_DELAY:
        arcade.draw_text(
            "Tap or press Space to play again",
            WIDTH / 2, HEIGHT / 2 - 70,
            (200, 200, 200),
            font_size=16,
            anchor_x="center",
            anchor_y="center",
        )
