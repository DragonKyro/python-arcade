"""
Flappy Bird game view for Python Arcade 3.x.
Tap space or click to flap. Avoid pipes, pass through gaps to score.
"""

import arcade
import random
import math
from pages.rules import RulesView

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
        arcade.draw_text(
            self.label,
            self.cx,
            self.cy,
            LINE_COLOR,
            font_size=14,
            anchor_x="center",
            anchor_y="center",
        )


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

        # Sky background
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
            SKY_COLOR
        )

        # Clouds
        for cx, cy, cw, ch, _ in self.clouds:
            arcade.draw_circle_filled(cx, cy, ch * 0.6, CLOUD_COLOR)
            arcade.draw_circle_filled(cx - cw * 0.25, cy - ch * 0.15, ch * 0.5, CLOUD_COLOR)
            arcade.draw_circle_filled(cx + cw * 0.25, cy - ch * 0.1, ch * 0.55, CLOUD_COLOR)

        # Pipes
        for px, gap_y, _ in self.pipes:
            self._draw_pipe(px, gap_y)

        # Ground
        self._draw_ground()

        # Bird
        self._draw_bird()

        # Score
        self._draw_score()

        # UI overlay for states
        if self.state == WAITING:
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

        if self.state == GAME_OVER:
            self._draw_game_over()

        # Top bar buttons
        self.back_button.draw(hover=self.back_button.contains(self.mouse_x, self.mouse_y))
        self.help_button.draw(hover=self.help_button.contains(self.mouse_x, self.mouse_y))

    def _draw_pipe(self, px, gap_y):
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

    def _draw_ground(self):
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
            x = i * 40 - self.ground_offset
            arcade.draw_rect_filled(
                arcade.XYWH(x, GROUND_HEIGHT / 2, 2, GROUND_HEIGHT),
                (120, 100, 55)
            )

    def _draw_bird(self):
        """Draw the bird with rotation based on velocity."""
        # Compute visual rotation angle (degrees)
        if self.state == WAITING:
            angle = 0
        else:
            # Map velocity to angle: flap up = +25 deg, fall = -70 deg
            angle = max(-70, min(25, self.bird_vel / 8))

        bx = BIRD_X
        by = self.bird_y
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

    def _draw_score(self):
        """Draw the current score centered near the top."""
        score_text = str(self.score)
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

    def _draw_game_over(self):
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
            f"Score: {self.score}",
            WIDTH / 2, HEIGHT / 2 + 10,
            (255, 255, 255),
            font_size=24,
            anchor_x="center",
            anchor_y="center",
        )

        # High score
        arcade.draw_text(
            f"Best: {self.high_score}",
            WIDTH / 2, HEIGHT / 2 - 25,
            (249, 226, 175),
            font_size=20,
            anchor_x="center",
            anchor_y="center",
        )

        # Restart prompt
        if self.game_over_timer >= RESTART_DELAY:
            arcade.draw_text(
                "Tap or press Space to play again",
                WIDTH / 2, HEIGHT / 2 - 70,
                (200, 200, 200),
                font_size=16,
                anchor_x="center",
                anchor_y="center",
            )

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
