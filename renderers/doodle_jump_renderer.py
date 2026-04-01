"""
Renderer for the Doodle Jump game.
All drawing code. No imports from games.*.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Game states
WAITING = 0
PLAYING = 1
GAME_OVER = 2

# Layout
TOP_BAR_HEIGHT = 50

# Player constants
PLAYER_WIDTH = 30
PLAYER_HEIGHT = 36
PLAYER_HEAD_RADIUS = 10

# Platform constants
PLATFORM_WIDTH = 70
PLATFORM_HEIGHT = 14
WHITE_FADE_TIME = 1.0

# Platform types
PLAT_GREEN = "green"
PLAT_BLUE = "blue"
PLAT_BROWN = "brown"
PLAT_WHITE = "white"

# Colors
BG_COLOR = (245, 245, 240)
GRID_COLOR = (210, 220, 230, 80)
GRID_COLOR_ACCENT = (190, 200, 215, 100)

PLAYER_BODY_COLOR = (90, 180, 90)
PLAYER_HEAD_COLOR = (100, 200, 100)
PLAYER_EYE_WHITE = (255, 255, 255)
PLAYER_EYE_PUPIL = (30, 30, 30)
PLAYER_FEET_COLOR = (70, 140, 70)
PLAYER_NOSE_COLOR = (130, 210, 130)

PLAT_GREEN_COLOR = (80, 190, 60)
PLAT_GREEN_TOP = (100, 210, 80)
PLAT_BLUE_COLOR = (70, 140, 220)
PLAT_BLUE_TOP = (100, 170, 240)
PLAT_BROWN_COLOR = (160, 110, 60)
PLAT_BROWN_TOP = (180, 130, 80)
PLAT_BROWN_CRACK = (120, 80, 40)
PLAT_WHITE_COLOR = (230, 230, 230)
PLAT_WHITE_TOP = (245, 245, 245)

OVERLAY_COLOR = (255, 255, 255, 180)
RESTART_DELAY = 0.5


def draw(game):
    """Render the entire Doodle Jump game state."""
    # Background
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        BG_COLOR,
    )

    # Grid lines (graph paper look)
    _draw_grid(game)

    # Platforms
    for plat in game.platforms:
        _draw_platform(plat, game.camera_y)

    # Player
    _draw_player(game)

    # Score (top area)
    _draw_score_bar(game)

    # State overlays
    if game.state == WAITING:
        game.txt_start.draw()

    if game.state == GAME_OVER:
        _draw_game_over(game)

    # Buttons
    game.back_button.draw(hover=game.back_button.contains(game.mouse_x, game.mouse_y))
    game.help_button.draw(hover=game.help_button.contains(game.mouse_x, game.mouse_y))


def _draw_grid(game):
    """Draw faint graph-paper grid lines that scroll with the camera."""
    spacing = 40
    cam = game.camera_y

    # Vertical lines (static)
    for x in range(0, WIDTH + spacing, spacing):
        arcade.draw_line(x, 0, x, HEIGHT, GRID_COLOR, 1)

    # Horizontal lines (scroll with camera)
    offset = cam % spacing
    for i in range(-1, HEIGHT // spacing + 2):
        y = i * spacing - offset
        if 0 <= y <= HEIGHT:
            arcade.draw_line(0, y, WIDTH, y, GRID_COLOR, 1)

    # Accent lines every 5th
    accent_spacing = spacing * 5
    offset_a = cam % accent_spacing
    for i in range(-1, HEIGHT // accent_spacing + 2):
        y = i * accent_spacing - offset_a
        if 0 <= y <= HEIGHT:
            arcade.draw_line(0, y, WIDTH, y, GRID_COLOR_ACCENT, 1)
    for x in range(0, WIDTH + accent_spacing, accent_spacing):
        arcade.draw_line(x, 0, x, HEIGHT, GRID_COLOR_ACCENT, 1)


def _draw_platform(plat, camera_y):
    """Draw a single platform, offset by camera."""
    screen_y = plat["y"] - camera_y

    # Skip if off screen
    if screen_y < -PLATFORM_HEIGHT or screen_y > HEIGHT + PLATFORM_HEIGHT:
        return

    x = plat["x"]
    ptype = plat["type"]
    active = plat["active"]

    if ptype == PLAT_GREEN:
        _draw_plat_rect(x, screen_y, PLAT_GREEN_COLOR, PLAT_GREEN_TOP)

    elif ptype == PLAT_BLUE:
        _draw_plat_rect(x, screen_y, PLAT_BLUE_COLOR, PLAT_BLUE_TOP)
        # Small arrows to indicate movement
        arrow_y = screen_y
        arcade.draw_triangle_filled(
            x - PLATFORM_WIDTH / 2 - 6, arrow_y,
            x - PLATFORM_WIDTH / 2 + 2, arrow_y + 4,
            x - PLATFORM_WIDTH / 2 + 2, arrow_y - 4,
            PLAT_BLUE_COLOR,
        )
        arcade.draw_triangle_filled(
            x + PLATFORM_WIDTH / 2 + 6, arrow_y,
            x + PLATFORM_WIDTH / 2 - 2, arrow_y + 4,
            x + PLATFORM_WIDTH / 2 - 2, arrow_y - 4,
            PLAT_BLUE_COLOR,
        )

    elif ptype == PLAT_BROWN:
        if active:
            _draw_plat_rect(x, screen_y, PLAT_BROWN_COLOR, PLAT_BROWN_TOP)
            # Crack lines
            arcade.draw_line(
                x - 10, screen_y + 2,
                x + 5, screen_y - 2,
                PLAT_BROWN_CRACK, 1,
            )
            arcade.draw_line(
                x + 8, screen_y + 3,
                x + 18, screen_y - 1,
                PLAT_BROWN_CRACK, 1,
            )
        else:
            # Broken pieces falling
            half_w = PLATFORM_WIDTH / 4
            piece_h = PLATFORM_HEIGHT * 0.7
            arcade.draw_rect_filled(
                arcade.XYWH(x - half_w, screen_y + 2, half_w * 1.6, piece_h),
                PLAT_BROWN_COLOR,
            )
            arcade.draw_rect_filled(
                arcade.XYWH(x + half_w, screen_y - 3, half_w * 1.4, piece_h),
                PLAT_BROWN_COLOR,
            )

    elif ptype == PLAT_WHITE:
        if active:
            timer = plat["timer"]
            if timer > 0:
                # Fading: reduce alpha as timer progresses
                progress = min(timer / WHITE_FADE_TIME, 1.0)
                alpha = int(255 * (1.0 - progress * 0.7))
                fade_color = (230, 230, 230, alpha)
                fade_top = (245, 245, 245, alpha)
                _draw_plat_rect_alpha(x, screen_y, fade_color, fade_top)
            else:
                _draw_plat_rect(x, screen_y, PLAT_WHITE_COLOR, PLAT_WHITE_TOP)
            # Dashed outline to distinguish from bg
            arcade.draw_rect_outline(
                arcade.XYWH(x, screen_y, PLATFORM_WIDTH, PLATFORM_HEIGHT),
                (180, 180, 180), 1,
            )


def _draw_plat_rect(x, y, body_color, top_color):
    """Draw a platform rectangle with a highlighted top edge."""
    arcade.draw_rect_filled(
        arcade.XYWH(x, y, PLATFORM_WIDTH, PLATFORM_HEIGHT),
        body_color,
    )
    # Bright top strip
    arcade.draw_rect_filled(
        arcade.XYWH(x, y + PLATFORM_HEIGHT / 2 - 2, PLATFORM_WIDTH, 4),
        top_color,
    )


def _draw_plat_rect_alpha(x, y, body_color, top_color):
    """Draw a platform rectangle with alpha colors."""
    arcade.draw_rect_filled(
        arcade.XYWH(x, y, PLATFORM_WIDTH, PLATFORM_HEIGHT),
        body_color,
    )
    arcade.draw_rect_filled(
        arcade.XYWH(x, y + PLATFORM_HEIGHT / 2 - 2, PLATFORM_WIDTH, 4),
        top_color,
    )


def _draw_player(game):
    """Draw the doodler character."""
    x = game.player_x
    screen_y = game.player_y - game.camera_y
    facing = 1 if game.facing_right else -1

    # Body (rectangle)
    arcade.draw_rect_filled(
        arcade.XYWH(x, screen_y, PLAYER_WIDTH, PLAYER_HEIGHT - PLAYER_HEAD_RADIUS),
        PLAYER_BODY_COLOR,
    )

    # Head (circle on top)
    head_y = screen_y + PLAYER_HEIGHT / 2 - PLAYER_HEAD_RADIUS / 2
    arcade.draw_circle_filled(x, head_y, PLAYER_HEAD_RADIUS, PLAYER_HEAD_COLOR)

    # Eyes
    eye_x = x + facing * 4
    eye_y = head_y + 2
    arcade.draw_circle_filled(eye_x, eye_y, 4, PLAYER_EYE_WHITE)
    arcade.draw_circle_filled(eye_x + facing * 1.5, eye_y, 2, PLAYER_EYE_PUPIL)

    # Second eye (further back)
    eye2_x = x - facing * 2
    arcade.draw_circle_filled(eye2_x, eye_y, 3.5, PLAYER_EYE_WHITE)
    arcade.draw_circle_filled(eye2_x + facing * 1, eye_y, 1.8, PLAYER_EYE_PUPIL)

    # Nose / snout
    nose_x = x + facing * (PLAYER_HEAD_RADIUS - 2)
    nose_y = head_y - 1
    arcade.draw_circle_filled(nose_x, nose_y, 3, PLAYER_NOSE_COLOR)

    # Feet (two small rectangles at bottom)
    foot_y = screen_y - PLAYER_HEIGHT / 2 + 4
    arcade.draw_rect_filled(
        arcade.XYWH(x - 7, foot_y, 10, 6),
        PLAYER_FEET_COLOR,
    )
    arcade.draw_rect_filled(
        arcade.XYWH(x + 7, foot_y, 10, 6),
        PLAYER_FEET_COLOR,
    )


def _draw_score_bar(game):
    """Draw score display at the top of the screen."""
    if game.state == PLAYING or game.state == GAME_OVER:
        game.txt_score.text = f"Score: {game.score}"
        game.txt_score.draw()

    if game.high_score > 0:
        game.txt_high_score.text = f"HI: {game.high_score}"
        game.txt_high_score.draw()


def _draw_game_over(game):
    """Draw game over overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        OVERLAY_COLOR,
    )

    game.txt_game_over.draw()

    game.txt_game_over_score.text = f"Score: {game.score}"
    game.txt_game_over_score.draw()

    game.txt_best_score.text = f"Best: {game.high_score}"
    game.txt_best_score.draw()

    if game.game_over_timer >= RESTART_DELAY:
        game.txt_restart_hint.draw()
