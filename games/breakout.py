"""
Breakout game view for Python Arcade 3.x.
Classic brick-breaking game with paddle, ball, and colored brick rows.
"""

import arcade
import math
import random
from pages.rules import RulesView
from renderers import breakout_renderer

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
PADDLE_Y = 40
PADDLE_SPEED = 500  # pixels per second for keyboard

# Ball
BALL_RADIUS = 6
BALL_INITIAL_SPEED = 300
BALL_SPEED_INCREMENT = 10  # per brick cleared batch
BALL_MAX_SPEED = 600

# Bricks
BRICK_ROWS = 8
BRICK_COLS = 10
BRICK_WIDTH = 70
BRICK_HEIGHT = 20
BRICK_PADDING = 4
BRICK_TOP_OFFSET = PLAY_TOP - 40  # top of highest brick row

# Brick row configuration (from top): 2 yellow, 2 green, 2 orange, 2 red
# Stored as (color, point_value) per row from top (row 0 = top)
ROW_CONFIG = [
    ((240, 220, 50), 50),   # yellow - 50 pts
    ((240, 220, 50), 50),
    ((50, 200, 80), 30),    # green - 30 pts
    ((50, 200, 80), 30),
    ((230, 140, 40), 20),   # orange - 20 pts
    ((230, 140, 40), 20),
    ((220, 50, 50), 10),    # red - 10 pts
    ((220, 50, 50), 10),
]

# Colors
BG_COLOR = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
BUTTON_COLOR = (40, 40, 40)
BUTTON_HOVER_COLOR = (70, 70, 70)
BUTTON_TEXT_COLOR = (220, 220, 220)
OVERLAY_COLOR = (0, 0, 0, 180)

# Game states
STATE_READY = "ready"         # ball on paddle, waiting for launch
STATE_PLAYING = "playing"     # ball in motion
STATE_LEVEL_COMPLETE = "level_complete"
STATE_GAME_OVER = "game_over"

LEVEL_COMPLETE_DELAY = 2.0  # seconds to show level complete message


class _Button:
    """Simple rectangular button helper."""

    def __init__(self, cx, cy, w, h, label, color=BUTTON_COLOR,
                 hover_color=BUTTON_HOVER_COLOR, text_color=BUTTON_TEXT_COLOR,
                 font_size=14):
        self.cx = cx
        self.cy = cy
        self.w = w
        self.h = h
        self.label = label
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font_size = font_size

    def contains(self, x, y):
        return (abs(x - self.cx) <= self.w / 2) and (abs(y - self.cy) <= self.h / 2)

    def draw(self, hover=False):
        color = self.hover_color if hover else self.color
        arcade.draw_rect_filled(arcade.XYWH(self.cx, self.cy, self.w, self.h), color)
        arcade.draw_rect_outline(arcade.XYWH(self.cx, self.cy, self.w, self.h), WHITE, 2)
        if not hasattr(self, '_txt_label'):
            self._txt_label = arcade.Text(
                self.label, self.cx, self.cy, self.text_color,
                font_size=self.font_size, anchor_x="center", anchor_y="center",
            )
        self._txt_label.text = self.label
        self._txt_label.x = self.cx
        self._txt_label.y = self.cy
        self._txt_label.draw()


class BreakoutView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.mouse_x = WIDTH / 2
        self.mouse_y = 0

        # Top bar buttons
        self.btn_back = _Button(60, HEIGHT - 25, 90, 34, "Back")
        self.btn_help = _Button(140, HEIGHT - 25, 40, 34, "?")

        # Play again button (shown on game over)
        self.btn_play_again = _Button(WIDTH // 2, HEIGHT // 2 - 60, 160, 50,
                                      "Play Again", BUTTON_COLOR,
                                      BUTTON_HOVER_COLOR, WHITE, 18)

        # Movement keys held
        self.move_left = False
        self.move_right = False

        # Pre-create Text objects (no arcade.draw_text)
        self._create_texts()

        self._init_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        self.txt_score = arcade.Text(
            "Score: 0", 10, PLAY_TOP + 8, WHITE,
            font_size=16, anchor_x="left", anchor_y="bottom",
        )
        self.txt_lives = arcade.Text(
            "Lives: 3", WIDTH - 10, PLAY_TOP + 8, WHITE,
            font_size=16, anchor_x="right", anchor_y="bottom",
        )
        self.txt_level = arcade.Text(
            "Level 1", WIDTH / 2, PLAY_TOP + 8, WHITE,
            font_size=16, anchor_x="center", anchor_y="bottom",
        )
        self.txt_launch = arcade.Text(
            "Click or press Space to launch", WIDTH / 2, HEIGHT / 2, GRAY,
            font_size=18, anchor_x="center", anchor_y="center",
        )
        self.txt_game_over = arcade.Text(
            "GAME OVER", WIDTH / 2, HEIGHT / 2 + 40, WHITE,
            font_size=42, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_final_score = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2, GRAY,
            font_size=22, anchor_x="center", anchor_y="center",
        )
        self.txt_level_complete = arcade.Text(
            "Level Complete!", WIDTH / 2, PLAY_HEIGHT / 2, WHITE,
            font_size=36, anchor_x="center", anchor_y="center", bold=True,
        )

    def _init_game(self):
        """Reset all game state for a fresh game."""
        self.score = 0
        self.lives = 3
        self.level = 1

        # Paddle
        self.paddle_x = WIDTH / 2
        self.paddle_y = PADDLE_Y

        # Ball
        self.ball_x = self.paddle_x
        self.ball_y = self.paddle_y + PADDLE_HEIGHT / 2 + BALL_RADIUS
        self.ball_dx = 0.0
        self.ball_dy = 0.0
        self.ball_speed = BALL_INITIAL_SPEED

        # Bricks: list of dicts with x, y, color, points, alive
        self.bricks = []
        self._build_bricks()

        self.state = STATE_READY
        self.level_complete_timer = 0.0
        self.total_bricks_cleared = 0

    def _build_bricks(self):
        """Create the brick grid for the current level."""
        self.bricks = []
        total_grid_w = BRICK_COLS * (BRICK_WIDTH + BRICK_PADDING) - BRICK_PADDING
        start_x = (WIDTH - total_grid_w) / 2 + BRICK_WIDTH / 2

        for row in range(BRICK_ROWS):
            color, points = ROW_CONFIG[row]
            cy = BRICK_TOP_OFFSET - row * (BRICK_HEIGHT + BRICK_PADDING) - BRICK_HEIGHT / 2
            for col in range(BRICK_COLS):
                cx = start_x + col * (BRICK_WIDTH + BRICK_PADDING)
                self.bricks.append({
                    'x': cx,
                    'y': cy,
                    'color': color,
                    'points': points,
                    'alive': True,
                })

    def _reset_ball_to_paddle(self):
        """Place ball on paddle and stop it."""
        self.ball_x = self.paddle_x
        self.ball_y = self.paddle_y + PADDLE_HEIGHT / 2 + BALL_RADIUS
        self.ball_dx = 0.0
        self.ball_dy = 0.0
        self.state = STATE_READY

    def _launch_ball(self):
        """Launch ball from paddle at a slight random angle upward."""
        if self.state != STATE_READY:
            return
        angle = random.uniform(math.radians(50), math.radians(130))
        self.ball_dx = self.ball_speed * math.cos(angle)
        self.ball_dy = self.ball_speed * math.sin(angle)
        self.state = STATE_PLAYING

    def _next_level(self):
        """Advance to next level."""
        self.level += 1
        self.ball_speed = min(self.ball_speed + 30, BALL_MAX_SPEED)
        self._build_bricks()
        self._reset_ball_to_paddle()

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_update(self, delta_time):
        # Level complete delay
        if self.state == STATE_LEVEL_COMPLETE:
            self.level_complete_timer -= delta_time
            if self.level_complete_timer <= 0:
                self._next_level()
            return

        if self.state == STATE_GAME_OVER:
            return

        # Keyboard paddle movement
        if self.move_left:
            self.paddle_x -= PADDLE_SPEED * delta_time
        if self.move_right:
            self.paddle_x += PADDLE_SPEED * delta_time

        # Clamp paddle
        half_pw = PADDLE_WIDTH / 2
        self.paddle_x = max(half_pw, min(WIDTH - half_pw, self.paddle_x))

        if self.state == STATE_READY:
            # Ball follows paddle
            self.ball_x = self.paddle_x
            self.ball_y = self.paddle_y + PADDLE_HEIGHT / 2 + BALL_RADIUS
            return

        if self.state != STATE_PLAYING:
            return

        # Ball movement
        self.ball_x += self.ball_dx * delta_time
        self.ball_y += self.ball_dy * delta_time

        # Wall collisions (left, right, top)
        if self.ball_x - BALL_RADIUS <= 0:
            self.ball_x = BALL_RADIUS
            self.ball_dx = abs(self.ball_dx)
        elif self.ball_x + BALL_RADIUS >= WIDTH:
            self.ball_x = WIDTH - BALL_RADIUS
            self.ball_dx = -abs(self.ball_dx)

        if self.ball_y + BALL_RADIUS >= PLAY_TOP:
            self.ball_y = PLAY_TOP - BALL_RADIUS
            self.ball_dy = -abs(self.ball_dy)

        # Ball below screen - lose life
        if self.ball_y + BALL_RADIUS < 0:
            self.lives -= 1
            if self.lives <= 0:
                self.state = STATE_GAME_OVER
            else:
                self._reset_ball_to_paddle()
            return

        # Paddle collision
        if (self.ball_dy < 0 and
                self.ball_y - BALL_RADIUS <= self.paddle_y + PADDLE_HEIGHT / 2 and
                self.ball_y + BALL_RADIUS >= self.paddle_y - PADDLE_HEIGHT / 2 and
                self.paddle_x - half_pw <= self.ball_x <= self.paddle_x + half_pw):
            # Place ball above paddle
            self.ball_y = self.paddle_y + PADDLE_HEIGHT / 2 + BALL_RADIUS

            # Angle based on hit position: -1 (left edge) to 1 (right edge)
            hit_offset = (self.ball_x - self.paddle_x) / half_pw
            hit_offset = max(-1.0, min(1.0, hit_offset))

            # Map to angle: 150 deg (left) to 30 deg (right)
            angle = math.radians(90 + hit_offset * -60)
            self.ball_dx = self.ball_speed * math.cos(angle)
            self.ball_dy = self.ball_speed * math.sin(angle)

        # Brick collisions
        bricks_hit = 0
        for brick in self.bricks:
            if not brick['alive']:
                continue
            if self._ball_brick_collision(brick):
                brick['alive'] = False
                self.score += brick['points']
                bricks_hit += 1

        if bricks_hit > 0:
            self.total_bricks_cleared += bricks_hit
            # Speed up slightly every 10 bricks cleared
            if self.total_bricks_cleared % 10 == 0:
                self.ball_speed = min(self.ball_speed + BALL_SPEED_INCREMENT, BALL_MAX_SPEED)
                # Update current ball velocity magnitude
                current_speed = math.hypot(self.ball_dx, self.ball_dy)
                if current_speed > 0:
                    scale = self.ball_speed / current_speed
                    self.ball_dx *= scale
                    self.ball_dy *= scale

        # Check level complete
        alive_bricks = sum(1 for b in self.bricks if b['alive'])
        if alive_bricks == 0:
            self.state = STATE_LEVEL_COMPLETE
            self.level_complete_timer = LEVEL_COMPLETE_DELAY

    def _ball_brick_collision(self, brick):
        """Check and handle ball-brick collision. Returns True if hit."""
        bx, by = brick['x'], brick['y']
        hw = BRICK_WIDTH / 2
        hh = BRICK_HEIGHT / 2

        # Closest point on brick to ball center
        closest_x = max(bx - hw, min(self.ball_x, bx + hw))
        closest_y = max(by - hh, min(self.ball_y, by + hh))

        dx = self.ball_x - closest_x
        dy = self.ball_y - closest_y

        if dx * dx + dy * dy > BALL_RADIUS * BALL_RADIUS:
            return False

        # Determine which side was hit for bounce direction
        overlap_x = hw + BALL_RADIUS - abs(self.ball_x - bx)
        overlap_y = hh + BALL_RADIUS - abs(self.ball_y - by)

        if overlap_x < overlap_y:
            self.ball_dx = -self.ball_dx
        else:
            self.ball_dy = -self.ball_dy

        return True

    # ---- Drawing ----

    def on_draw(self):
        self.clear()
        breakout_renderer.draw(self)

    # ---- Input ----

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A):
            self.move_left = True
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.move_right = True
        elif key == arcade.key.SPACE:
            self._launch_ball()

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A):
            self.move_left = False
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.move_right = False

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y
        # Mouse controls paddle horizontal position
        if self.state in (STATE_READY, STATE_PLAYING):
            self.paddle_x = x
            half_pw = PADDLE_WIDTH / 2
            self.paddle_x = max(half_pw, min(WIDTH - half_pw, self.paddle_x))

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Top bar buttons
        if self.btn_back.contains(x, y):
            self.window.show_view(self.menu_view)
            return
        if self.btn_help.contains(x, y):
            rules_view = RulesView("Breakout", "breakout.txt", None, self.menu_view,
                                   existing_game_view=self)
            self.window.show_view(rules_view)
            return

        # Game over - play again
        if self.state == STATE_GAME_OVER:
            if self.btn_play_again.contains(x, y):
                self._init_game()
            return

        # Launch ball
        if self.state == STATE_READY:
            self._launch_ball()
