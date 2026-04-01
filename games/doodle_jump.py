"""
Doodle Jump game view for Python Arcade 3.x.
Endless vertical platformer. Bounce upward, avoid falling off the bottom.
"""

import arcade
import random
from pages.rules import RulesView
from renderers import doodle_jump_renderer

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
GRAVITY = -900
BOUNCE_VELOCITY = 550
MOVE_SPEED = 400

# Platform constants
PLATFORM_WIDTH = 70
PLATFORM_HEIGHT = 14
PLATFORM_SPACING_MIN = 60
PLATFORM_SPACING_MAX = 120
BLUE_MOVE_SPEED = 100
BLUE_MOVE_RANGE = 120
WHITE_FADE_TIME = 1.0
BROWN_FALL_SPEED = 400

# Platform types
PLAT_GREEN = "green"
PLAT_BLUE = "blue"
PLAT_BROWN = "brown"
PLAT_WHITE = "white"

# Colors
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


class DoodleJumpView(arcade.View):
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
        self._reset()

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        self.txt_start = arcade.Text(
            "Press Space to Start", WIDTH / 2, HEIGHT / 2 + 80,
            (80, 80, 80), font_size=22,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_score = arcade.Text(
            "", 15, HEIGHT - 25,
            (80, 80, 80), font_size=16,
            anchor_x="left", anchor_y="center", bold=True,
        )
        self.txt_high_score = arcade.Text(
            "", WIDTH / 2, HEIGHT - 25,
            (150, 120, 50), font_size=14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_game_over = arcade.Text(
            "Game Over", WIDTH / 2, HEIGHT / 2 + 60,
            (200, 60, 60), font_size=40,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_score = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 + 10,
            (80, 80, 80), font_size=24,
            anchor_x="center", anchor_y="center",
        )
        self.txt_best_score = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 - 25,
            (150, 120, 50), font_size=20,
            anchor_x="center", anchor_y="center",
        )
        self.txt_restart_hint = arcade.Text(
            "Press Space to play again",
            WIDTH / 2, HEIGHT / 2 - 70,
            (120, 120, 120), font_size=16,
            anchor_x="center", anchor_y="center",
        )

    def _reset(self):
        """Reset game state for a new round."""
        self.state = WAITING

        # Player state
        self.player_x = WIDTH / 2
        self.player_y = 80
        self.player_vel_x = 0
        self.player_vel_y = 0
        self.facing_right = True

        # Camera
        self.camera_y = 0

        # Score
        self.score = 0
        self.max_height = 0

        # Game over timer
        self.game_over_timer = 0.0

        # Input tracking
        self.left_pressed = False
        self.right_pressed = False

        # Platforms: list of dicts
        # {type, x, y, active, move_dir, timer, vel_y}
        self.platforms = []
        self._generate_initial_platforms()

    def _generate_initial_platforms(self):
        """Create starting platforms."""
        # Ground platform (always green, centered)
        self.platforms.append({
            "type": PLAT_GREEN,
            "x": WIDTH / 2,
            "y": 40,
            "active": True,
            "move_dir": 1,
            "timer": 0.0,
            "vel_y": 0.0,
        })

        # Generate platforms upward
        y = 40
        while y < HEIGHT * 2:
            y += random.randint(PLATFORM_SPACING_MIN, PLATFORM_SPACING_MAX)
            plat = self._make_platform(y)
            self.platforms.append(plat)

    def _make_platform(self, y):
        """Create a random platform at given y."""
        x = random.randint(int(PLATFORM_WIDTH / 2) + 10, int(WIDTH - PLATFORM_WIDTH / 2) - 10)
        roll = random.random()
        if roll < 0.55:
            ptype = PLAT_GREEN
        elif roll < 0.75:
            ptype = PLAT_BLUE
        elif roll < 0.90:
            ptype = PLAT_BROWN
        else:
            ptype = PLAT_WHITE
        return {
            "type": ptype,
            "x": x,
            "y": y,
            "active": True,
            "move_dir": random.choice([-1, 1]),
            "timer": 0.0,
            "vel_y": 0.0,
        }

    def _generate_platforms_above(self):
        """Generate more platforms above the current highest one."""
        if not self.platforms:
            return
        highest_y = max(p["y"] for p in self.platforms)
        target_y = self.camera_y + HEIGHT * 2
        y = highest_y
        while y < target_y:
            y += random.randint(PLATFORM_SPACING_MIN, PLATFORM_SPACING_MAX)
            plat = self._make_platform(y)
            self.platforms.append(plat)

    def _remove_offscreen_platforms(self):
        """Remove platforms far below the camera."""
        cutoff = self.camera_y - 200
        self.platforms = [p for p in self.platforms if p["y"] > cutoff or not p["active"]]
        # Also remove inactive platforms that fell far below
        self.platforms = [p for p in self.platforms if p["y"] > cutoff - 400]

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def on_update(self, delta_time):
        dt = min(delta_time, 0.05)

        if self.state == WAITING:
            return

        if self.state == GAME_OVER:
            self.game_over_timer += dt
            return

        # --- PLAYING ---

        # Horizontal movement
        self.player_vel_x = 0
        if self.left_pressed:
            self.player_vel_x = -MOVE_SPEED
            self.facing_right = False
        if self.right_pressed:
            self.player_vel_x = MOVE_SPEED
            self.facing_right = True

        self.player_x += self.player_vel_x * dt

        # Screen wrap
        if self.player_x < -PLAYER_WIDTH / 2:
            self.player_x = WIDTH + PLAYER_WIDTH / 2
        elif self.player_x > WIDTH + PLAYER_WIDTH / 2:
            self.player_x = -PLAYER_WIDTH / 2

        # Gravity
        self.player_vel_y += GRAVITY * dt
        self.player_y += self.player_vel_y * dt

        # Platform collision (only when falling)
        if self.player_vel_y <= 0:
            player_bottom = self.player_y - PLAYER_HEIGHT / 2
            player_left = self.player_x - PLAYER_WIDTH / 2
            player_right = self.player_x + PLAYER_WIDTH / 2

            for plat in self.platforms:
                if not plat["active"]:
                    continue

                plat_left = plat["x"] - PLATFORM_WIDTH / 2
                plat_right = plat["x"] + PLATFORM_WIDTH / 2
                plat_top = plat["y"] + PLATFORM_HEIGHT / 2
                plat_bottom = plat["y"] - PLATFORM_HEIGHT / 2

                # Check horizontal overlap
                if player_right > plat_left and player_left < plat_right:
                    # Check if feet are at platform level
                    if player_bottom <= plat_top and player_bottom >= plat_bottom - 15:
                        self._land_on_platform(plat)

        # Update platform behaviors
        for plat in self.platforms:
            if plat["type"] == PLAT_BLUE and plat["active"]:
                plat["x"] += BLUE_MOVE_SPEED * plat["move_dir"] * dt
                if plat["x"] > WIDTH - PLATFORM_WIDTH / 2:
                    plat["move_dir"] = -1
                elif plat["x"] < PLATFORM_WIDTH / 2:
                    plat["move_dir"] = 1

            if plat["type"] == PLAT_WHITE and plat["timer"] > 0:
                plat["timer"] += dt
                if plat["timer"] >= WHITE_FADE_TIME:
                    plat["active"] = False

            if plat["type"] == PLAT_BROWN and not plat["active"]:
                plat["vel_y"] -= BROWN_FALL_SPEED * dt
                plat["y"] += plat["vel_y"] * dt

        # Update score based on max height
        current_height = int(self.player_y)
        if current_height > self.max_height:
            self.max_height = current_height
        self.score = self.max_height

        # Camera follows player upward
        target_camera = self.player_y - HEIGHT / 3
        if target_camera > self.camera_y:
            self.camera_y = target_camera

        # Generate new platforms above
        self._generate_platforms_above()

        # Clean up off-screen platforms
        self._remove_offscreen_platforms()

        # Game over: fell below camera
        if self.player_y < self.camera_y - 50:
            self.state = GAME_OVER
            self.game_over_timer = 0.0
            if self.score > self.high_score:
                self.high_score = self.score

    def _land_on_platform(self, plat):
        """Handle landing on a platform."""
        if plat["type"] == PLAT_BROWN:
            # Brown breaks immediately
            plat["active"] = False
            # Still give a small bounce
            self.player_vel_y = BOUNCE_VELOCITY * 0.3
            return

        if plat["type"] == PLAT_WHITE:
            # Start fade timer on first contact
            if plat["timer"] == 0:
                plat["timer"] = 0.01

        # Bounce
        self.player_y = plat["y"] + PLATFORM_HEIGHT / 2 + PLAYER_HEIGHT / 2
        self.player_vel_y = BOUNCE_VELOCITY

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def on_draw(self):
        self.clear()
        doodle_jump_renderer.draw(self)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            if self.state == WAITING:
                self.state = PLAYING
                self.player_vel_y = BOUNCE_VELOCITY
            elif self.state == GAME_OVER and self.game_over_timer >= RESTART_DELAY:
                self._reset()
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True
        elif key == arcade.key.ESCAPE:
            self.window.show_view(self.menu_view)

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.back_button.contains(x, y):
                self.window.show_view(self.menu_view)
                return
            if self.help_button.contains(x, y):
                rules_view = RulesView(
                    "Doodle Jump", "doodle_jump.txt", None,
                    self.menu_view, existing_game_view=self
                )
                self.window.show_view(rules_view)
                return
            if self.state == WAITING:
                self.state = PLAYING
                self.player_vel_y = BOUNCE_VELOCITY
            elif self.state == GAME_OVER and self.game_over_timer >= RESTART_DELAY:
                self._reset()

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y
