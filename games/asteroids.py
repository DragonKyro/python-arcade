"""
Asteroids game view for Python Arcade 3.x.
Classic Asteroids with ship, asteroids, bullets, wrap-around movement, and wave progression.
"""

import arcade
import math
import random
from pages.rules import RulesView
from renderers import asteroids_renderer

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
BOTTOM_BAR_HEIGHT = 40

# Play area
PLAY_TOP = HEIGHT - TOP_BAR_HEIGHT
PLAY_BOTTOM = BOTTOM_BAR_HEIGHT

# Colors
BG_COLOR = (0, 0, 0)
LINE_COLOR = (205, 214, 244)
BUTTON_COLOR = (69, 71, 90)
BUTTON_HOVER_COLOR = (88, 91, 112)
BUTTON_TEXT_COLOR = (205, 214, 244)
OVERLAY_COLOR = (0, 0, 0, 200)
SCORE_COLOR = (255, 255, 255)

# Ship
SHIP_TURN_SPEED = 200  # degrees per second
SHIP_THRUST = 300
SHIP_MAX_SPEED = 400
SHIP_DRAG = 0.98
SHIP_RADIUS = 15
INVINCIBILITY_DURATION = 2.5

# Bullets
BULLET_SPEED = 500
BULLET_LIFETIME = 0.8  # seconds
MAX_BULLETS = 5

# Asteroids
ASTEROID_SIZES = {
    "large": {"radius": 40, "speed_range": (40, 80), "points": 20},
    "medium": {"radius": 22, "speed_range": (60, 120), "points": 50},
    "small": {"radius": 12, "speed_range": (80, 160), "points": 100},
}
INITIAL_ASTEROIDS = 4


class _Button:
    """Simple rectangular button helper."""

    def __init__(self, cx, cy, w, h, label):
        self.cx = cx
        self.cy = cy
        self.w = w
        self.h = h
        self.label = label

    def contains(self, x, y):
        return (abs(x - self.cx) <= self.w / 2) and (abs(y - self.cy) <= self.h / 2)

    def draw(self, hover=False):
        color = BUTTON_HOVER_COLOR if hover else BUTTON_COLOR
        arcade.draw_rect_filled(arcade.XYWH(self.cx, self.cy, self.w, self.h), color)
        arcade.draw_rect_outline(arcade.XYWH(self.cx, self.cy, self.w, self.h), LINE_COLOR, 2)
        if not hasattr(self, '_txt_label'):
            self._txt_label = arcade.Text(
                self.label, self.cx, self.cy, BUTTON_TEXT_COLOR,
                font_size=14, anchor_x="center", anchor_y="center",
            )
        self._txt_label.text = self.label
        self._txt_label.x = self.cx
        self._txt_label.y = self.cy
        self._txt_label.draw()


def _generate_asteroid_vertices(radius, num_vertices=10):
    """Generate irregular polygon vertices for an asteroid shape."""
    vertices = []
    for i in range(num_vertices):
        angle = (2 * math.pi * i) / num_vertices
        r = radius * random.uniform(0.7, 1.3)
        vertices.append((math.cos(angle) * r, math.sin(angle) * r))
    return vertices


class Asteroid:
    """Represents an asteroid with position, velocity, size, and shape."""

    def __init__(self, x, y, size="large"):
        self.x = x
        self.y = y
        self.size = size
        info = ASTEROID_SIZES[size]
        self.radius = info["radius"]
        self.points = info["points"]
        self.alive = True

        # Random velocity
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(*info["speed_range"])
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed

        # Irregular polygon shape (offsets from center)
        self.vertices = _generate_asteroid_vertices(self.radius)

    def update(self, dt):
        self.x += self.dx * dt
        self.y += self.dy * dt
        # Wrap around
        self.x %= WIDTH
        self.y = PLAY_BOTTOM + ((self.y - PLAY_BOTTOM) % (PLAY_TOP - PLAY_BOTTOM))


class Bullet:
    """A bullet fired by the ship."""

    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        rad = math.radians(angle)
        self.dx = math.cos(rad) * BULLET_SPEED
        self.dy = math.sin(rad) * BULLET_SPEED
        self.alive = True
        self.lifetime = BULLET_LIFETIME

    def update(self, dt):
        self.x += self.dx * dt
        self.y += self.dy * dt
        # Wrap around
        self.x %= WIDTH
        self.y = PLAY_BOTTOM + ((self.y - PLAY_BOTTOM) % (PLAY_TOP - PLAY_BOTTOM))
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False


class AsteroidsView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.mouse_x = 0
        self.mouse_y = 0
        self.high_score = 0

        # Buttons
        self.btn_back = _Button(60, HEIGHT - 25, 90, 34, "Back")
        self.btn_new_game = _Button(WIDTH - 80, HEIGHT - 25, 120, 34, "New Game")
        self.btn_help = _Button(WIDTH - 30, HEIGHT - 25, 40, 40, "?")

        # Key tracking
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False

        self._create_texts()
        self._init_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        self.txt_score = arcade.Text(
            "", 140, HEIGHT - 18, SCORE_COLOR,
            font_size=14, anchor_x="left", anchor_y="center",
        )
        self.txt_high_score = arcade.Text(
            "", 140, HEIGHT - 38, (180, 180, 180),
            font_size=11, anchor_x="left", anchor_y="center",
        )
        self.txt_wave = arcade.Text(
            "", WIDTH // 2, HEIGHT - 25, (200, 200, 255),
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_lives_label = arcade.Text(
            "LIVES:", 10, BOTTOM_BAR_HEIGHT // 2, SCORE_COLOR,
            font_size=12, anchor_x="left", anchor_y="center",
        )
        self.txt_game_over = arcade.Text(
            "GAME OVER", WIDTH // 2, HEIGHT // 2 + 50,
            (255, 80, 80), font_size=36,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_final_score = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2, SCORE_COLOR,
            font_size=18, anchor_x="center", anchor_y="center",
        )
        self.txt_restart_hint = arcade.Text(
            "Press ENTER to play again", WIDTH // 2, HEIGHT // 2 - 45,
            (180, 180, 180), font_size=14,
            anchor_x="center", anchor_y="center",
        )

    def _init_game(self):
        """Initialize or reset all game state."""
        self.score = 0
        self.lives = 3
        self.wave = 1
        self.game_over = False

        # Ship state
        self.ship_x = WIDTH / 2
        self.ship_y = (PLAY_TOP + PLAY_BOTTOM) / 2
        self.ship_angle = 90  # degrees, 90 = pointing up
        self.ship_dx = 0.0
        self.ship_dy = 0.0
        self.ship_thrusting = False
        self.ship_invincible = 0.0
        self.ship_alive = True

        # Respawn timer
        self.respawn_timer = 0.0

        # Bullets
        self.bullets = []

        # Asteroids
        self.asteroids = []
        self._spawn_wave()

    def _spawn_wave(self):
        """Spawn asteroids for the current wave."""
        count = INITIAL_ASTEROIDS + (self.wave - 1)
        for _ in range(count):
            # Spawn away from the ship
            while True:
                x = random.uniform(0, WIDTH)
                y = random.uniform(PLAY_BOTTOM, PLAY_TOP)
                dist = math.hypot(x - self.ship_x, y - self.ship_y)
                if dist > 120:
                    break
            self.asteroids.append(Asteroid(x, y, "large"))

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_update(self, delta_time):
        if self.game_over:
            return

        dt = delta_time

        # Respawn timer
        if not self.ship_alive:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.ship_alive = True
                self.ship_x = WIDTH / 2
                self.ship_y = (PLAY_TOP + PLAY_BOTTOM) / 2
                self.ship_dx = 0.0
                self.ship_dy = 0.0
                self.ship_angle = 90
                self.ship_invincible = INVINCIBILITY_DURATION

        # Ship rotation
        if self.ship_alive:
            if self.left_pressed:
                self.ship_angle += SHIP_TURN_SPEED * dt
            if self.right_pressed:
                self.ship_angle -= SHIP_TURN_SPEED * dt

            # Ship thrust
            self.ship_thrusting = self.up_pressed
            if self.up_pressed:
                rad = math.radians(self.ship_angle)
                self.ship_dx += math.cos(rad) * SHIP_THRUST * dt
                self.ship_dy += math.sin(rad) * SHIP_THRUST * dt
                # Clamp speed
                speed = math.hypot(self.ship_dx, self.ship_dy)
                if speed > SHIP_MAX_SPEED:
                    scale = SHIP_MAX_SPEED / speed
                    self.ship_dx *= scale
                    self.ship_dy *= scale

            # Apply drag
            self.ship_dx *= SHIP_DRAG
            self.ship_dy *= SHIP_DRAG

            # Move ship
            self.ship_x += self.ship_dx * dt
            self.ship_y += self.ship_dy * dt

            # Wrap around
            self.ship_x %= WIDTH
            self.ship_y = PLAY_BOTTOM + ((self.ship_y - PLAY_BOTTOM) % (PLAY_TOP - PLAY_BOTTOM))

        # Invincibility timer
        if self.ship_invincible > 0:
            self.ship_invincible -= dt

        # Update bullets
        for b in self.bullets:
            b.update(dt)
        self.bullets = [b for b in self.bullets if b.alive]

        # Update asteroids
        for a in self.asteroids:
            if a.alive:
                a.update(dt)

        # --- Collision detection ---

        # Bullets vs asteroids
        for b in self.bullets:
            if not b.alive:
                continue
            for a in self.asteroids:
                if not a.alive:
                    continue
                dist = math.hypot(b.x - a.x, b.y - a.y)
                if dist < a.radius:
                    b.alive = False
                    a.alive = False
                    self.score += a.points
                    self._split_asteroid(a)
                    break

        # Ship vs asteroids
        if self.ship_alive and self.ship_invincible <= 0:
            for a in self.asteroids:
                if not a.alive:
                    continue
                dist = math.hypot(self.ship_x - a.x, self.ship_y - a.y)
                if dist < a.radius + SHIP_RADIUS:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over = True
                        self.ship_alive = False
                        if self.score > self.high_score:
                            self.high_score = self.score
                        return
                    else:
                        self.ship_alive = False
                        self.respawn_timer = 1.5
                    break

        # Clean up dead asteroids
        self.asteroids = [a for a in self.asteroids if a.alive]

        # Check wave clear
        if len(self.asteroids) == 0 and not self.game_over:
            self.wave += 1
            self._spawn_wave()

        # Update high score
        if self.score > self.high_score:
            self.high_score = self.score

    def _split_asteroid(self, asteroid):
        """Split an asteroid into smaller pieces."""
        if asteroid.size == "large":
            new_size = "medium"
        elif asteroid.size == "medium":
            new_size = "small"
        else:
            return  # small asteroids just disappear

        for _ in range(2):
            child = Asteroid(asteroid.x, asteroid.y, new_size)
            self.asteroids.append(child)

    def on_draw(self):
        self.clear()
        asteroids_renderer.draw(self)

    def on_key_press(self, key, modifiers):
        if self.game_over:
            if key == arcade.key.RETURN or key == arcade.key.ENTER:
                self._init_game()
            return

        if key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
        elif key == arcade.key.UP:
            self.up_pressed = True
        elif key == arcade.key.SPACE:
            self._fire_bullet()

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False
        elif key == arcade.key.UP:
            self.up_pressed = False

    def _fire_bullet(self):
        if not self.ship_alive:
            return
        if len(self.bullets) >= MAX_BULLETS:
            return
        rad = math.radians(self.ship_angle)
        nose_x = self.ship_x + math.cos(rad) * SHIP_RADIUS
        nose_y = self.ship_y + math.sin(rad) * SHIP_RADIUS
        self.bullets.append(Bullet(nose_x, nose_y, self.ship_angle))

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        if self.btn_back.contains(x, y):
            self.window.show_view(self.menu_view)
            return

        if self.btn_new_game.contains(x, y):
            self._init_game()
            return

        if self.btn_help.contains(x, y):
            rules_view = RulesView(
                "Asteroids", "asteroids.txt", None,
                self.menu_view, existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return
