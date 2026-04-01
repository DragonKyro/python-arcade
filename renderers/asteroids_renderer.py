"""
Renderer for the Asteroids game.
All drawing code extracted from games/asteroids.py.
"""

import arcade
import math

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
BOTTOM_BAR_HEIGHT = 40

# Colors
BG_COLOR = (0, 0, 0)
LINE_COLOR = (205, 214, 244)
OVERLAY_COLOR = (0, 0, 0, 200)
SCORE_COLOR = (255, 255, 255)
SHIP_COLOR = (200, 220, 255)
SHIP_THRUST_COLOR = (255, 160, 50)
ASTEROID_COLOR = (170, 160, 140)
ASTEROID_OUTLINE_COLOR = (210, 200, 180)
BULLET_COLOR = (255, 255, 255)
LIVES_SHIP_COLOR = (200, 220, 255)

# Ship drawing
SHIP_RADIUS = 15

# Bullet drawing
BULLET_RADIUS = 2


def draw(game):
    """Render the entire Asteroids game state."""
    # --- Draw play area ---

    # Asteroids
    for a in game.asteroids:
        if a.alive:
            _draw_asteroid(a)

    # Bullets
    for b in game.bullets:
        if b.alive:
            arcade.draw_circle_filled(b.x, b.y, BULLET_RADIUS, BULLET_COLOR)

    # Ship
    if game.ship_alive:
        draw_ship = True
        if game.ship_invincible > 0:
            if int(game.ship_invincible * 10) % 2 == 0:
                draw_ship = False
        if draw_ship:
            _draw_ship(game)

    # --- Top bar ---
    _draw_top_bar(game)

    # --- Bottom bar ---
    _draw_bottom_bar(game)

    # --- Overlays ---
    if game.game_over:
        _draw_game_over(game)


def _draw_ship(game):
    """Draw the player's ship as a triangle pointing in ship_angle direction."""
    x, y = game.ship_x, game.ship_y
    angle = game.ship_angle
    rad = math.radians(angle)

    # Triangle points: nose, left wing, right wing
    nose_x = x + math.cos(rad) * SHIP_RADIUS
    nose_y = y + math.sin(rad) * SHIP_RADIUS

    left_rad = math.radians(angle + 140)
    left_x = x + math.cos(left_rad) * SHIP_RADIUS
    left_y = y + math.sin(left_rad) * SHIP_RADIUS

    right_rad = math.radians(angle - 140)
    right_x = x + math.cos(right_rad) * SHIP_RADIUS
    right_y = y + math.sin(right_rad) * SHIP_RADIUS

    # Ship body
    arcade.draw_triangle_filled(
        nose_x, nose_y, left_x, left_y, right_x, right_y, SHIP_COLOR
    )
    arcade.draw_triangle_outline(
        nose_x, nose_y, left_x, left_y, right_x, right_y, (255, 255, 255), 1
    )

    # Thrust flame
    if game.ship_thrusting:
        back_rad = math.radians(angle + 180)
        flame_x = x + math.cos(back_rad) * (SHIP_RADIUS * 1.4)
        flame_y = y + math.sin(back_rad) * (SHIP_RADIUS * 1.4)

        fl_left_rad = math.radians(angle + 160)
        fl_left_x = x + math.cos(fl_left_rad) * (SHIP_RADIUS * 0.6)
        fl_left_y = y + math.sin(fl_left_rad) * (SHIP_RADIUS * 0.6)

        fl_right_rad = math.radians(angle - 160)
        fl_right_x = x + math.cos(fl_right_rad) * (SHIP_RADIUS * 0.6)
        fl_right_y = y + math.sin(fl_right_rad) * (SHIP_RADIUS * 0.6)

        arcade.draw_triangle_filled(
            flame_x, flame_y, fl_left_x, fl_left_y, fl_right_x, fl_right_y,
            SHIP_THRUST_COLOR,
        )


def _draw_asteroid(asteroid):
    """Draw an asteroid as an irregular polygon."""
    x, y = asteroid.x, asteroid.y
    verts = asteroid.vertices
    n = len(verts)

    # Draw filled triangles from center to each edge
    for i in range(n):
        x1 = x + verts[i][0]
        y1 = y + verts[i][1]
        x2 = x + verts[(i + 1) % n][0]
        y2 = y + verts[(i + 1) % n][1]
        arcade.draw_triangle_filled(x, y, x1, y1, x2, y2, ASTEROID_COLOR)

    # Draw outline
    for i in range(n):
        x1 = x + verts[i][0]
        y1 = y + verts[i][1]
        x2 = x + verts[(i + 1) % n][0]
        y2 = y + verts[(i + 1) % n][1]
        arcade.draw_line(x1, y1, x2, y2, ASTEROID_OUTLINE_COLOR, 1)


def _draw_top_bar(game):
    """Draw the top bar with score, wave, and buttons."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT - TOP_BAR_HEIGHT // 2, WIDTH, TOP_BAR_HEIGHT),
        BG_COLOR,
    )
    arcade.draw_line(0, HEIGHT - TOP_BAR_HEIGHT, WIDTH, HEIGHT - TOP_BAR_HEIGHT, LINE_COLOR, 1)

    # Score
    game.txt_score.text = f"SCORE: {game.score}"
    game.txt_score.draw()
    game.txt_high_score.text = f"HI: {game.high_score}"
    game.txt_high_score.draw()

    # Wave number
    game.txt_wave.text = f"WAVE {game.wave}"
    game.txt_wave.draw()

    # Buttons
    hover_back = game.btn_back.contains(game.mouse_x, game.mouse_y)
    hover_new = game.btn_new_game.contains(game.mouse_x, game.mouse_y)
    hover_help = game.btn_help.contains(game.mouse_x, game.mouse_y)
    game.btn_back.draw(hover=hover_back)
    game.btn_new_game.draw(hover=hover_new)
    game.btn_help.draw(hover=hover_help)


def _draw_bottom_bar(game):
    """Draw the bottom bar with lives."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, BOTTOM_BAR_HEIGHT // 2, WIDTH, BOTTOM_BAR_HEIGHT),
        BG_COLOR,
    )
    arcade.draw_line(0, BOTTOM_BAR_HEIGHT, WIDTH, BOTTOM_BAR_HEIGHT, LINE_COLOR, 1)

    # Lives label
    game.txt_lives_label.draw()

    # Lives as small ship icons
    for i in range(game.lives):
        lx = 80 + i * 30
        ly = BOTTOM_BAR_HEIGHT // 2
        # Small upward-pointing triangle
        arcade.draw_triangle_filled(
            lx, ly + 8,       # nose (top)
            lx - 6, ly - 6,   # left wing
            lx + 6, ly - 6,   # right wing
            LIVES_SHIP_COLOR,
        )


def _draw_game_over(game):
    """Draw the game over overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_COLOR
    )
    game.txt_game_over.draw()
    game.txt_final_score.text = f"Final Score: {game.score}  |  Wave: {game.wave}"
    game.txt_final_score.draw()
    game.txt_restart_hint.draw()
