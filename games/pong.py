"""
Pong game view for Python Arcade 3.x.
Classic Pong with AI opponent and difficulty selection.
"""

import arcade
import math
import random
from ai.pong_ai import PongAI
from pages.rules import RulesView

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50

# Play area
PLAY_TOP = HEIGHT - TOP_BAR_HEIGHT
PLAY_HEIGHT = PLAY_TOP  # from 0 to PLAY_TOP

# Paddle
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 80
PADDLE_MARGIN = 40  # distance from edge to paddle center-x
PADDLE_SPEED = 400  # pixels per second for player

# Ball
BALL_SIZE = 10
BALL_INITIAL_SPEED = 300  # pixels per second
BALL_SPEED_INCREMENT = 15  # speed increase per paddle hit
BALL_MAX_SPEED = 700

# Scoring
WIN_SCORE = 10
SERVE_DELAY = 1.0  # seconds pause after scoring

# Colors
BG_COLOR = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (50, 50, 50)
BUTTON_COLOR = (40, 40, 40)
BUTTON_HOVER_COLOR = (70, 70, 70)
BUTTON_TEXT_COLOR = (220, 220, 220)
OVERLAY_COLOR = (0, 0, 0, 180)

# Difficulty button colors
EASY_COLOR = (30, 120, 50)
EASY_HOVER = (40, 160, 65)
MEDIUM_COLOR = (160, 130, 20)
MEDIUM_HOVER = (200, 165, 30)
HARD_COLOR = (160, 30, 30)
HARD_HOVER = (200, 45, 45)


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
        arcade.draw_text(
            self.label,
            self.cx,
            self.cy,
            self.text_color,
            font_size=self.font_size,
            anchor_x="center",
            anchor_y="center",
        )


class PongView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.mouse_x = 0
        self.mouse_y = 0

        # Top bar buttons
        self.btn_back = _Button(60, HEIGHT - 25, 90, 34, "Back")
        self.btn_new = _Button(WIDTH - 80, HEIGHT - 25, 110, 34, "New Game")
        self.btn_help = _Button(WIDTH - 150, HEIGHT - 25, 40, 40, "?")

        # Difficulty selection buttons
        btn_y = HEIGHT // 2
        self.btn_easy = _Button(WIDTH // 2 - 150, btn_y, 120, 50, "Easy",
                                EASY_COLOR, EASY_HOVER, WHITE, 18)
        self.btn_medium = _Button(WIDTH // 2, btn_y, 120, 50, "Medium",
                                  MEDIUM_COLOR, MEDIUM_HOVER, WHITE, 18)
        self.btn_hard = _Button(WIDTH // 2 + 150, btn_y, 120, 50, "Hard",
                                HARD_COLOR, HARD_HOVER, WHITE, 18)
        self.difficulty_buttons = [self.btn_easy, self.btn_medium, self.btn_hard]

        # Game state
        self.state = "select"  # "select", "playing", "serve", "gameover"
        self.ai = None

        # Movement keys held
        self.move_up = False
        self.move_down = False

        self._init_game()

    def _init_game(self):
        """Reset all game state (but not difficulty selection)."""
        # Paddles (center positions)
        self.player_x = PADDLE_MARGIN
        self.player_y = PLAY_HEIGHT / 2
        self.ai_x = WIDTH - PADDLE_MARGIN
        self.ai_y = PLAY_HEIGHT / 2

        # Ball
        self.ball_x = WIDTH / 2
        self.ball_y = PLAY_HEIGHT / 2
        self.ball_dx = 0.0
        self.ball_dy = 0.0
        self.ball_speed = BALL_INITIAL_SPEED

        # Score
        self.player_score = 0
        self.ai_score = 0

        # Serve state
        self.serve_timer = 0.0
        self.serve_direction = 1  # 1 = toward AI, -1 = toward player

        # Winner text
        self.winner_text = ""

        # Play again button (shown on game over)
        self.btn_play_again = _Button(WIDTH // 2, HEIGHT // 2 - 40, 160, 50,
                                      "Play Again", BUTTON_COLOR,
                                      BUTTON_HOVER_COLOR, WHITE, 18)

        self.move_up = False
        self.move_down = False

    def _start_game(self, difficulty):
        """Start a new game with the chosen difficulty."""
        self._init_game()
        self.ai = PongAI(difficulty)
        self.state = "serve"
        self.serve_timer = SERVE_DELAY
        self.serve_direction = random.choice([-1, 1])

    def _serve_ball(self):
        """Launch ball from center in the serve direction."""
        self.ball_x = WIDTH / 2
        self.ball_y = PLAY_HEIGHT / 2
        self.ball_speed = BALL_INITIAL_SPEED
        # Random angle between -45 and 45 degrees
        angle = random.uniform(-math.pi / 4, math.pi / 4)
        self.ball_dx = self.ball_speed * math.cos(angle) * self.serve_direction
        self.ball_dy = self.ball_speed * math.sin(angle)
        self.state = "playing"

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_update(self, delta_time):
        if self.state == "serve":
            self.serve_timer -= delta_time
            if self.serve_timer <= 0:
                self._serve_ball()
            return

        if self.state != "playing":
            return

        # --- Player paddle movement ---
        if self.move_up:
            self.player_y += PADDLE_SPEED * delta_time
        if self.move_down:
            self.player_y -= PADDLE_SPEED * delta_time

        # Clamp player paddle
        half_p = PADDLE_HEIGHT / 2
        self.player_y = max(half_p, min(PLAY_HEIGHT - half_p, self.player_y))

        # --- AI paddle movement ---
        if self.ai:
            target_y = self.ai.get_move(
                self.ai_y,
                self.ball_x, self.ball_y,
                self.ball_dx, self.ball_dy,
                PLAY_HEIGHT, PADDLE_HEIGHT,
            )
            # Apply the target with delta_time scaling
            # The AI's max_speed is per-frame at 60fps, so scale accordingly
            diff = target_y - self.ai_y
            max_move = self.ai.settings['max_speed'] * 60 * delta_time
            if abs(diff) > max_move:
                self.ai_y += max_move * (1 if diff > 0 else -1)
            else:
                self.ai_y = target_y
            self.ai_y = max(half_p, min(PLAY_HEIGHT - half_p, self.ai_y))

        # --- Ball movement ---
        self.ball_x += self.ball_dx * delta_time
        self.ball_y += self.ball_dy * delta_time

        half_ball = BALL_SIZE / 2

        # Top/bottom wall bounce
        if self.ball_y - half_ball <= 0:
            self.ball_y = half_ball
            self.ball_dy = abs(self.ball_dy)
        elif self.ball_y + half_ball >= PLAY_HEIGHT:
            self.ball_y = PLAY_HEIGHT - half_ball
            self.ball_dy = -abs(self.ball_dy)

        # --- Paddle collisions ---
        # Player paddle (left)
        if (self.ball_dx < 0 and
                self.ball_x - half_ball <= self.player_x + PADDLE_WIDTH / 2 and
                self.ball_x + half_ball >= self.player_x - PADDLE_WIDTH / 2 and
                self.player_y - PADDLE_HEIGHT / 2 <= self.ball_y <= self.player_y + PADDLE_HEIGHT / 2):
            self._bounce_off_paddle(self.player_x + PADDLE_WIDTH / 2, self.player_y, 1)

        # AI paddle (right)
        if (self.ball_dx > 0 and
                self.ball_x + half_ball >= self.ai_x - PADDLE_WIDTH / 2 and
                self.ball_x - half_ball <= self.ai_x + PADDLE_WIDTH / 2 and
                self.ai_y - PADDLE_HEIGHT / 2 <= self.ball_y <= self.ai_y + PADDLE_HEIGHT / 2):
            self._bounce_off_paddle(self.ai_x - PADDLE_WIDTH / 2, self.ai_y, -1)

        # --- Scoring ---
        if self.ball_x < -BALL_SIZE:
            self.ai_score += 1
            self._after_score(serve_dir=1)  # serve toward AI (away from scorer)
        elif self.ball_x > WIDTH + BALL_SIZE:
            self.player_score += 1
            self._after_score(serve_dir=-1)

    def _bounce_off_paddle(self, paddle_edge_x, paddle_center_y, direction):
        """Bounce ball off a paddle. direction: 1 = going right, -1 = going left."""
        # Place ball just outside the paddle
        half_ball = BALL_SIZE / 2
        self.ball_x = paddle_edge_x + direction * half_ball

        # Calculate bounce angle based on where ball hit the paddle
        # hit_offset: -1 (bottom edge) to 1 (top edge)
        hit_offset = (self.ball_y - paddle_center_y) / (PADDLE_HEIGHT / 2)
        hit_offset = max(-1.0, min(1.0, hit_offset))

        # Max bounce angle: 60 degrees
        bounce_angle = hit_offset * (math.pi / 3)

        # Speed up
        self.ball_speed = min(self.ball_speed + BALL_SPEED_INCREMENT, BALL_MAX_SPEED)

        self.ball_dx = self.ball_speed * math.cos(bounce_angle) * direction
        self.ball_dy = self.ball_speed * math.sin(bounce_angle)

    def _after_score(self, serve_dir):
        """Handle post-score: check for win or set up serve."""
        if self.player_score >= WIN_SCORE:
            self.state = "gameover"
            self.winner_text = "You Win!"
        elif self.ai_score >= WIN_SCORE:
            self.state = "gameover"
            self.winner_text = "AI Wins!"
        else:
            self.state = "serve"
            self.serve_timer = SERVE_DELAY
            self.serve_direction = serve_dir
            self.ball_x = WIDTH / 2
            self.ball_y = PLAY_HEIGHT / 2
            self.ball_dx = 0
            self.ball_dy = 0

    # ---- Drawing ----

    def on_draw(self):
        self.clear()

        if self.state == "select":
            self._draw_top_bar()
            self._draw_difficulty_select()
            return

        # Draw play area
        self._draw_court()
        self._draw_paddles()
        self._draw_ball()
        self._draw_scores()
        self._draw_top_bar()

        if self.state == "serve":
            self._draw_serve_message()
        elif self.state == "gameover":
            self._draw_gameover()

    def _draw_top_bar(self):
        """Draw the top bar with Back, New Game, and Help buttons."""
        # Dark bar background
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT - TOP_BAR_HEIGHT / 2, WIDTH, TOP_BAR_HEIGHT),
            (20, 20, 20),
        )
        arcade.draw_line(0, PLAY_TOP, WIDTH, PLAY_TOP, GRAY, 1)

        self.btn_back.draw(self.btn_back.contains(self.mouse_x, self.mouse_y))
        self.btn_new.draw(self.btn_new.contains(self.mouse_x, self.mouse_y))
        self.btn_help.draw(self.btn_help.contains(self.mouse_x, self.mouse_y))

    def _draw_court(self):
        """Draw the center dashed line and border."""
        # Center dashed line
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

    def _draw_paddles(self):
        """Draw player and AI paddles."""
        # Player paddle
        arcade.draw_rect_filled(
            arcade.XYWH(self.player_x, self.player_y, PADDLE_WIDTH, PADDLE_HEIGHT),
            WHITE,
        )
        # AI paddle
        arcade.draw_rect_filled(
            arcade.XYWH(self.ai_x, self.ai_y, PADDLE_WIDTH, PADDLE_HEIGHT),
            WHITE,
        )

    def _draw_ball(self):
        """Draw the ball."""
        arcade.draw_circle_filled(self.ball_x, self.ball_y, BALL_SIZE / 2, WHITE)

    def _draw_scores(self):
        """Draw scores at top of play area."""
        arcade.draw_text(
            str(self.player_score),
            WIDTH / 4,
            PLAY_HEIGHT - 50,
            WHITE,
            font_size=36,
            anchor_x="center",
            anchor_y="center",
        )
        arcade.draw_text(
            str(self.ai_score),
            3 * WIDTH / 4,
            PLAY_HEIGHT - 50,
            WHITE,
            font_size=36,
            anchor_x="center",
            anchor_y="center",
        )

    def _draw_difficulty_select(self):
        """Draw difficulty selection screen."""
        arcade.draw_text(
            "PONG",
            WIDTH / 2,
            HEIGHT / 2 + 100,
            WHITE,
            font_size=48,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        arcade.draw_text(
            "Select Difficulty",
            WIDTH / 2,
            HEIGHT / 2 + 50,
            GRAY,
            font_size=20,
            anchor_x="center",
            anchor_y="center",
        )
        for btn in self.difficulty_buttons:
            btn.draw(btn.contains(self.mouse_x, self.mouse_y))

    def _draw_serve_message(self):
        """Draw a brief 'Get Ready' message during serve delay."""
        arcade.draw_text(
            "Get Ready...",
            WIDTH / 2,
            PLAY_HEIGHT / 2,
            GRAY,
            font_size=24,
            anchor_x="center",
            anchor_y="center",
        )

    def _draw_gameover(self):
        """Draw the game over overlay."""
        # Semi-transparent overlay
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, PLAY_HEIGHT / 2, WIDTH, PLAY_HEIGHT),
            OVERLAY_COLOR,
        )
        arcade.draw_text(
            self.winner_text,
            WIDTH / 2,
            PLAY_HEIGHT / 2 + 40,
            WHITE,
            font_size=42,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        arcade.draw_text(
            f"{self.player_score} - {self.ai_score}",
            WIDTH / 2,
            PLAY_HEIGHT / 2 + 0,
            GRAY,
            font_size=24,
            anchor_x="center",
            anchor_y="center",
        )
        self.btn_play_again.draw(
            self.btn_play_again.contains(self.mouse_x, self.mouse_y)
        )

    # ---- Input ----

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.W, arcade.key.UP):
            self.move_up = True
        elif key in (arcade.key.S, arcade.key.DOWN):
            self.move_down = True

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.W, arcade.key.UP):
            self.move_up = False
        elif key in (arcade.key.S, arcade.key.DOWN):
            self.move_down = False

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Top bar buttons (available in all states)
        if self.btn_back.contains(x, y):
            self.window.show_view(self.menu_view)
            return
        if self.btn_new.contains(x, y):
            self._init_game()
            self.state = "select"
            return
        if self.btn_help.contains(x, y):
            rules_view = RulesView("Pong", "pong.txt", None, self.menu_view,
                                   existing_game_view=self)
            self.window.show_view(rules_view)
            return

        # Difficulty selection
        if self.state == "select":
            if self.btn_easy.contains(x, y):
                self._start_game('easy')
            elif self.btn_medium.contains(x, y):
                self._start_game('medium')
            elif self.btn_hard.contains(x, y):
                self._start_game('hard')
            return

        # Game over - play again
        if self.state == "gameover":
            if self.btn_play_again.contains(x, y):
                difficulty = self.ai.difficulty if self.ai else 'medium'
                self._start_game(difficulty)
            return
