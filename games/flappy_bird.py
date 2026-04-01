"""
Flappy Bird game view for Python Arcade 3.x.
Tap space or click to flap. Avoid pipes, pass through gaps to score.
"""

import arcade
import random
import math
from pages.rules import RulesView
from renderers import flappy_bird_renderer

# Window constants
WIDTH = 800
HEIGHT = 600

# Game states
WAITING = 0
PLAYING = 1
GAME_OVER = 2

# Layout
TOP_BAR_HEIGHT = 50
GROUND_HEIGHT = 60

# Bird
BIRD_X = 150
BIRD_RADIUS = 18
GRAVITY = -900
FLAP_VELOCITY = 340
MAX_FALL_SPEED = -500
BIRD_BOB_SPEED = 3.0
BIRD_BOB_AMPLITUDE = 12

# Pipes
PIPE_WIDTH = 60
PIPE_CAP_WIDTH = 72
PIPE_CAP_HEIGHT = 20
PIPE_GAP = 150
PIPE_SPEED = 200
PIPE_SPAWN_DISTANCE = 250
MIN_GAP_Y = GROUND_HEIGHT + 100
MAX_GAP_Y = HEIGHT - TOP_BAR_HEIGHT - 100

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
BUTTON_COLOR = (69, 71, 90)
BUTTON_HOVER_COLOR = (88, 91, 112)
LINE_COLOR = (205, 214, 244)
OVERLAY_COLOR = (0, 0, 0, 150)

# Restart delay after game over
RESTART_DELAY = 0.5


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
                self.label, self.cx, self.cy, LINE_COLOR,
                font_size=14, anchor_x="center", anchor_y="center",
            )
        self._txt_label.text = self.label
        self._txt_label.x = self.cx
        self._txt_label.y = self.cy
        self._txt_label.draw()


class FlappyBirdView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.mouse_x = 0
        self.mouse_y = 0

        # Buttons
        self.back_button = _Button(50, HEIGHT - 25, 70, 36, "Back")
        self.help_button = _Button(WIDTH - 50, HEIGHT - 25, 40, 40, "?")

        # High score (session)
        self.high_score = 0

        self._create_texts()

        # Clouds (decorative, persist across resets)
        self.clouds = []
        for _ in range(5):
            cx = random.randint(0, WIDTH)
            cy = random.randint(HEIGHT // 2, HEIGHT - TOP_BAR_HEIGHT - 40)
            cw = random.randint(60, 140)
            ch = random.randint(25, 50)
            speed = random.uniform(10, 30)
            self.clouds.append([cx, cy, cw, ch, speed])

        self._reset()

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        self.txt_start = arcade.Text(
            "Press Space to Start", WIDTH / 2, HEIGHT / 2 + 80,
            (255, 255, 255), font_size=22,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_start_shadow = arcade.Text(
            "Press Space to Start", WIDTH / 2 + 2, HEIGHT / 2 + 78,
            (0, 0, 0, 100), font_size=22,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_score_shadow = arcade.Text(
            "", WIDTH / 2 + 2, HEIGHT - 80 - 2,
            (0, 0, 0, 120), font_size=48,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_score = arcade.Text(
            "", WIDTH / 2, HEIGHT - 80,
            (255, 255, 255), font_size=48,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over = arcade.Text(
            "Game Over", WIDTH / 2, HEIGHT / 2 + 60,
            (255, 80, 80), font_size=40,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_score = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 + 10,
            (255, 255, 255), font_size=24,
            anchor_x="center", anchor_y="center",
        )
        self.txt_best_score = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 - 25,
            (249, 226, 175), font_size=20,
            anchor_x="center", anchor_y="center",
        )
        self.txt_restart_hint = arcade.Text(
            "Tap or press Space to play again",
            WIDTH / 2, HEIGHT / 2 - 70,
            (200, 200, 200), font_size=16,
            anchor_x="center", anchor_y="center",
        )

    def _reset(self):
        """Reset game state for a new round."""
        self.state = WAITING
        self.bird_y = HEIGHT / 2
        self.bird_vel = 0
        self.bob_time = 0.0

        # Pipes: list of (x, gap_center_y, scored)
        self.pipes = []
        self.next_pipe_x = WIDTH + 100  # where the next pipe spawns

        self.score = 0
        self.game_over_timer = 0.0

        # Ground scroll offset
        self.ground_offset = 0.0

    def _spawn_pipe(self):
        gap_y = random.randint(MIN_GAP_Y, MAX_GAP_Y)
        self.pipes.append([self.next_pipe_x, gap_y, False])
        self.next_pipe_x += PIPE_SPAWN_DISTANCE

    def _flap(self):
        if self.state == WAITING:
            self.state = PLAYING
            self.bird_vel = FLAP_VELOCITY
            # Seed initial pipes
            self.next_pipe_x = WIDTH + 100
            for _ in range(4):
                self._spawn_pipe()
        elif self.state == PLAYING:
            self.bird_vel = FLAP_VELOCITY
        elif self.state == GAME_OVER:
            if self.game_over_timer >= RESTART_DELAY:
                self._reset()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def on_update(self, delta_time):
        dt = min(delta_time, 0.05)  # clamp for stability

        # Clouds always drift
        for c in self.clouds:
            c[0] -= c[4] * dt
            if c[0] + c[2] / 2 < 0:
                c[0] = WIDTH + c[2] / 2
                c[1] = random.randint(HEIGHT // 2, HEIGHT - TOP_BAR_HEIGHT - 40)

        if self.state == WAITING:
            self.bob_time += dt
            self.bird_y = HEIGHT / 2 + math.sin(self.bob_time * BIRD_BOB_SPEED) * BIRD_BOB_AMPLITUDE
            return

        if self.state == GAME_OVER:
            self.game_over_timer += dt
            # Bird falls to ground
            if self.bird_y > GROUND_HEIGHT + BIRD_RADIUS:
                self.bird_vel += GRAVITY * dt
                self.bird_y += self.bird_vel * dt
                if self.bird_y < GROUND_HEIGHT + BIRD_RADIUS:
                    self.bird_y = GROUND_HEIGHT + BIRD_RADIUS
            return

        # --- PLAYING ---
        # Bird physics
        self.bird_vel += GRAVITY * dt
        if self.bird_vel < MAX_FALL_SPEED:
            self.bird_vel = MAX_FALL_SPEED
        self.bird_y += self.bird_vel * dt

        # Scroll pipes
        for pipe in self.pipes:
            pipe[0] -= PIPE_SPEED * dt

        # Ground scroll
        self.ground_offset = (self.ground_offset + PIPE_SPEED * dt) % 40

        # Remove off-screen pipes, spawn new ones
        self.pipes = [p for p in self.pipes if p[0] + PIPE_WIDTH / 2 > -50]
        while len(self.pipes) < 6:
            self._spawn_pipe()

        # Scoring
        for pipe in self.pipes:
            if not pipe[2] and pipe[0] + PIPE_WIDTH / 2 < BIRD_X:
                pipe[2] = True
                self.score += 1

        # Collision detection
        if self._check_collision():
            self.state = GAME_OVER
            self.game_over_timer = 0.0
            if self.score > self.high_score:
                self.high_score = self.score

    def _check_collision(self):
        # Ground or ceiling
        if self.bird_y - BIRD_RADIUS <= GROUND_HEIGHT:
            self.bird_y = GROUND_HEIGHT + BIRD_RADIUS
            return True
        if self.bird_y + BIRD_RADIUS >= HEIGHT:
            return True

        # Pipe collision (rectangular check against bird bounding box)
        bird_left = BIRD_X - BIRD_RADIUS
        bird_right = BIRD_X + BIRD_RADIUS
        bird_top = self.bird_y + BIRD_RADIUS
        bird_bottom = self.bird_y - BIRD_RADIUS

        for px, gap_y, _ in self.pipes:
            pipe_left = px - PIPE_WIDTH / 2
            pipe_right = px + PIPE_WIDTH / 2

            # Check horizontal overlap
            if bird_right > pipe_left and bird_left < pipe_right:
                gap_top = gap_y + PIPE_GAP / 2
                gap_bottom = gap_y - PIPE_GAP / 2
                # Bird must be fully inside gap vertically
                if bird_top > gap_top or bird_bottom < gap_bottom:
                    return True

        return False

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def on_draw(self):
        self.clear()
        flappy_bird_renderer.draw(self)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            self._flap()
        elif key == arcade.key.ESCAPE:
            self.window.show_view(self.menu_view)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Check buttons first
            if self.back_button.contains(x, y):
                self.window.show_view(self.menu_view)
                return
            if self.help_button.contains(x, y):
                rules_view = RulesView(
                    "Flappy Bird", "flappy_bird.txt", None,
                    self.menu_view, existing_game_view=self
                )
                self.window.show_view(rules_view)
                return
            # Otherwise flap
            self._flap()

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y
