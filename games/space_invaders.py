"""
Space Invaders game view for Python Arcade 3.x.
Classic Space Invaders with aliens, shields, UFO bonus, and wave progression.
"""

import arcade
import random
from pages.rules import RulesView
from renderers import space_invaders_renderer

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
PLAYER_COLOR = (100, 255, 100)
PLAYER_TURRET_COLOR = (150, 255, 150)
SHIELD_COLOR = (80, 200, 80)
BULLET_PLAYER_COLOR = (255, 255, 255)
BULLET_ALIEN_COLOR = (255, 100, 100)
UFO_COLOR = (255, 50, 50)

# Alien colors by row type
ALIEN_COLOR_SMALL = (255, 80, 80)       # top row, 30 pts
ALIEN_COLOR_MEDIUM = (100, 200, 255)    # middle 2 rows, 20 pts
ALIEN_COLOR_LARGE = (180, 255, 100)     # bottom 2 rows, 10 pts

# Alien grid
ALIEN_COLS = 11
ALIEN_ROWS = 5
ALIEN_WIDTH = 36
ALIEN_HEIGHT = 24
ALIEN_H_SPACING = 52
ALIEN_V_SPACING = 40
ALIEN_START_Y = PLAY_TOP - 60
ALIEN_START_X = 80

# Player
PLAYER_WIDTH = 44
PLAYER_HEIGHT = 20
PLAYER_TURRET_W = 6
PLAYER_TURRET_H = 10
PLAYER_Y = PLAY_BOTTOM + 30
PLAYER_SPEED = 300
MAX_PLAYER_BULLETS = 3

# Bullets
PLAYER_BULLET_SPEED = 400
ALIEN_BULLET_SPEED = 200
BULLET_WIDTH = 3
BULLET_HEIGHT = 10

# Shields
SHIELD_COUNT = 4
SHIELD_BLOCK_SIZE = 6
SHIELD_Y = PLAY_BOTTOM + 80

# UFO
UFO_WIDTH = 40
UFO_HEIGHT = 16
UFO_Y = PLAY_TOP - 20
UFO_SPEED = 120


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


class Alien:
    """Represents a single alien invader."""

    def __init__(self, row, col, x, y):
        self.row = row
        self.col = col
        self.x = x
        self.y = y
        self.alive = True
        # Assign type based on row
        if row == 0:
            self.alien_type = "small"
            self.points = 30
            self.color = ALIEN_COLOR_SMALL
        elif row <= 2:
            self.alien_type = "medium"
            self.points = 20
            self.color = ALIEN_COLOR_MEDIUM
        else:
            self.alien_type = "large"
            self.points = 10
            self.color = ALIEN_COLOR_LARGE

    def draw(self, frame):
        """Draw an alien using simple shapes. Frame alternates for animation."""
        x, y = self.x, self.y
        c = self.color
        dark = (max(0, c[0] - 60), max(0, c[1] - 60), max(0, c[2] - 60))

        if self.alien_type == "small":
            # Small alien: narrow body with antennae
            arcade.draw_rect_filled(arcade.XYWH(x, y, 16, 12), c)
            arcade.draw_rect_filled(arcade.XYWH(x, y + 10, 8, 6), c)
            # Eyes
            arcade.draw_rect_filled(arcade.XYWH(x - 4, y + 2, 3, 3), dark)
            arcade.draw_rect_filled(arcade.XYWH(x + 4, y + 2, 3, 3), dark)
            # Legs
            if frame % 2 == 0:
                arcade.draw_rect_filled(arcade.XYWH(x - 10, y - 6, 4, 4), c)
                arcade.draw_rect_filled(arcade.XYWH(x + 10, y - 6, 4, 4), c)
            else:
                arcade.draw_rect_filled(arcade.XYWH(x - 8, y - 8, 4, 4), c)
                arcade.draw_rect_filled(arcade.XYWH(x + 8, y - 8, 4, 4), c)
        elif self.alien_type == "medium":
            # Medium alien: wider body with horns
            arcade.draw_rect_filled(arcade.XYWH(x, y, 22, 14), c)
            arcade.draw_rect_filled(arcade.XYWH(x - 10, y + 8, 4, 6), c)
            arcade.draw_rect_filled(arcade.XYWH(x + 10, y + 8, 4, 6), c)
            # Eyes
            arcade.draw_rect_filled(arcade.XYWH(x - 5, y + 2, 4, 4), dark)
            arcade.draw_rect_filled(arcade.XYWH(x + 5, y + 2, 4, 4), dark)
            # Legs
            if frame % 2 == 0:
                arcade.draw_rect_filled(arcade.XYWH(x - 8, y - 10, 4, 4), c)
                arcade.draw_rect_filled(arcade.XYWH(x + 8, y - 10, 4, 4), c)
                arcade.draw_rect_filled(arcade.XYWH(x, y - 10, 4, 4), c)
            else:
                arcade.draw_rect_filled(arcade.XYWH(x - 12, y - 8, 4, 4), c)
                arcade.draw_rect_filled(arcade.XYWH(x + 12, y - 8, 4, 4), c)
        else:
            # Large alien: wide body
            arcade.draw_rect_filled(arcade.XYWH(x, y, 28, 14), c)
            arcade.draw_rect_filled(arcade.XYWH(x, y + 8, 18, 4), c)
            # Eyes
            arcade.draw_rect_filled(arcade.XYWH(x - 7, y + 2, 5, 4), dark)
            arcade.draw_rect_filled(arcade.XYWH(x + 7, y + 2, 5, 4), dark)
            # Legs
            if frame % 2 == 0:
                arcade.draw_rect_filled(arcade.XYWH(x - 12, y - 10, 6, 4), c)
                arcade.draw_rect_filled(arcade.XYWH(x + 12, y - 10, 6, 4), c)
            else:
                arcade.draw_rect_filled(arcade.XYWH(x - 8, y - 10, 6, 4), c)
                arcade.draw_rect_filled(arcade.XYWH(x + 8, y - 10, 6, 4), c)
                arcade.draw_rect_filled(arcade.XYWH(x, y - 10, 6, 4), c)


class Bullet:
    """A bullet (player or alien)."""

    def __init__(self, x, y, dy, color):
        self.x = x
        self.y = y
        self.dy = dy
        self.color = color
        self.alive = True

    def update(self, dt):
        self.y += self.dy * dt
        if self.y < PLAY_BOTTOM - 10 or self.y > PLAY_TOP + 10:
            self.alive = False

    def draw(self):
        arcade.draw_rect_filled(
            arcade.XYWH(self.x, self.y, BULLET_WIDTH, BULLET_HEIGHT), self.color
        )


class UFO:
    """Bonus UFO that flies across the top."""

    def __init__(self):
        self.active = False
        self.x = 0
        self.y = UFO_Y
        self.dx = 0
        self.points = 0

    def spawn(self):
        self.active = True
        self.points = random.choice([100, 150, 200, 250, 300])
        if random.random() < 0.5:
            self.x = -UFO_WIDTH
            self.dx = UFO_SPEED
        else:
            self.x = WIDTH + UFO_WIDTH
            self.dx = -UFO_SPEED

    def update(self, dt):
        if not self.active:
            return
        self.x += self.dx * dt
        if self.x < -UFO_WIDTH * 2 or self.x > WIDTH + UFO_WIDTH * 2:
            self.active = False

    def draw(self):
        if not self.active:
            return
        x, y = self.x, self.y
        # UFO body - dome + base
        arcade.draw_rect_filled(arcade.XYWH(x, y, UFO_WIDTH, 8), UFO_COLOR)
        arcade.draw_rect_filled(arcade.XYWH(x, y + 5, UFO_WIDTH // 2, 6), (255, 120, 120))
        # Lights
        arcade.draw_circle_filled(x - 10, y, 2, (255, 255, 100))
        arcade.draw_circle_filled(x, y, 2, (255, 255, 100))
        arcade.draw_circle_filled(x + 10, y, 2, (255, 255, 100))


def _create_shield_blocks(center_x, center_y):
    """Create a set of small blocks forming a shield shape (arch)."""
    blocks = []
    # Create a 5-wide by 4-tall block grid with top-center arch cutout
    layout = [
        # row 0 (bottom) - full
        [1, 1, 1, 1, 1],
        # row 1 - full
        [1, 1, 1, 1, 1],
        # row 2 - arch opening
        [1, 1, 0, 1, 1],
        # row 3 (top) - wider top
        [0, 1, 1, 1, 0],
    ]
    # Mirror and expand to make it wider
    for row_idx, row in enumerate(layout):
        for col_idx, val in enumerate(row):
            if val:
                bx = center_x + (col_idx - 2) * SHIELD_BLOCK_SIZE
                by = center_y + (row_idx - 1) * SHIELD_BLOCK_SIZE
                blocks.append([bx, by, True])
    # Add extra blocks for a wider shield
    extra_layout = [
        # Extra side columns
        ((-3, 0), True), ((-3, 1), True), ((3, 0), True), ((3, 1), True),
        # Extra top
        ((-1, 3), True), ((0, 3), True), ((1, 3), True),
    ]
    for (col_off, row_off), val in extra_layout:
        if val:
            bx = center_x + col_off * SHIELD_BLOCK_SIZE
            by = center_y + (row_off - 1) * SHIELD_BLOCK_SIZE
            blocks.append([bx, by, True])
    return blocks


class SpaceInvadersView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.mouse_x = 0
        self.mouse_y = 0
        self.high_score = 0

        # Buttons
        self.btn_back = _Button(60, HEIGHT - 25, 90, 34, "Back")
        self.btn_help = _Button(WIDTH - 30, HEIGHT - 25, 40, 40, "?")

        # Key tracking
        self.left_pressed = False
        self.right_pressed = False

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
            "", WIDTH - 80, HEIGHT - 18, (200, 200, 255),
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_lives_label = arcade.Text(
            "LIVES:", 10, BOTTOM_BAR_HEIGHT // 2, SCORE_COLOR,
            font_size=12, anchor_x="left", anchor_y="center",
        )
        self.txt_ufo_score = arcade.Text(
            "", 0, 0, (255, 255, 100),
            font_size=14, anchor_x="center", anchor_y="center", bold=True,
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
        self.victory = False
        self.paused = False

        # Player
        self.player_x = WIDTH / 2
        self.player_invincible = 0.0  # seconds of invincibility remaining

        # Bullets
        self.player_bullets = []
        self.alien_bullets = []

        # Aliens
        self._spawn_aliens(0)

        # Alien movement
        self.alien_direction = 1  # 1 = right, -1 = left
        self.alien_move_timer = 0.0
        self.alien_anim_frame = 0

        # Alien shooting
        self.alien_shoot_timer = 0.0

        # Shields
        self._create_shields()

        # UFO
        self.ufo = UFO()
        self.ufo_timer = 0.0
        self.ufo_score_display = None  # (x, y, points, timer) when UFO is hit
        self.ufo_score_timer = 0.0

    def _spawn_aliens(self, wave_offset):
        """Create the alien grid. wave_offset lowers start position each wave."""
        self.aliens = []
        drop = wave_offset * 20  # each wave aliens start lower
        for row in range(ALIEN_ROWS):
            for col in range(ALIEN_COLS):
                x = ALIEN_START_X + col * ALIEN_H_SPACING
                y = ALIEN_START_Y - row * ALIEN_V_SPACING - drop
                alien = Alien(row, col, x, y)
                self.aliens.append(alien)

    def _create_shields(self):
        """Create 4 shields evenly spaced."""
        self.shields = []
        spacing = WIDTH / (SHIELD_COUNT + 1)
        for i in range(SHIELD_COUNT):
            cx = spacing * (i + 1)
            blocks = _create_shield_blocks(cx, SHIELD_Y)
            self.shields.extend(blocks)

    def _alive_aliens(self):
        return [a for a in self.aliens if a.alive]

    def _alien_move_interval(self):
        """Movement interval decreases as aliens are destroyed."""
        alive = len(self._alive_aliens())
        total = ALIEN_ROWS * ALIEN_COLS
        if alive == 0:
            return 0.5
        # Base speed affected by wave
        base = max(0.4 - (self.wave - 1) * 0.05, 0.15)
        # Speed up as aliens die
        ratio = alive / total
        interval = base * ratio
        return max(interval, 0.03)

    def _alien_shoot_interval(self):
        """Aliens shoot more frequently as fewer remain."""
        alive = len(self._alive_aliens())
        total = ALIEN_ROWS * ALIEN_COLS
        if alive == 0:
            return 999
        ratio = alive / total
        return max(0.3, 1.2 * ratio)

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_update(self, delta_time):
        if self.game_over or self.paused:
            return

        dt = delta_time

        # Player movement
        if self.left_pressed:
            self.player_x -= PLAYER_SPEED * dt
        if self.right_pressed:
            self.player_x += PLAYER_SPEED * dt
        self.player_x = max(PLAYER_WIDTH / 2 + 5, min(WIDTH - PLAYER_WIDTH / 2 - 5, self.player_x))

        # Invincibility timer
        if self.player_invincible > 0:
            self.player_invincible -= dt

        # Update player bullets
        for b in self.player_bullets:
            b.update(dt)
        self.player_bullets = [b for b in self.player_bullets if b.alive]

        # Update alien bullets
        for b in self.alien_bullets:
            b.update(dt)
        self.alien_bullets = [b for b in self.alien_bullets if b.alive]

        # UFO score display timer
        if self.ufo_score_display:
            self.ufo_score_timer -= dt
            if self.ufo_score_timer <= 0:
                self.ufo_score_display = None

        # Alien movement
        alive_aliens = self._alive_aliens()
        if alive_aliens:
            self.alien_move_timer += dt
            if self.alien_move_timer >= self._alien_move_interval():
                self.alien_move_timer = 0.0
                self.alien_anim_frame += 1

                # Move all alive aliens sideways
                step_x = 8 * self.alien_direction

                # Check if any alien would go out of bounds
                needs_drop = False
                for a in alive_aliens:
                    new_x = a.x + step_x
                    if new_x < 20 or new_x > WIDTH - 20:
                        needs_drop = True
                        break

                if needs_drop:
                    # Drop down and reverse
                    self.alien_direction *= -1
                    for a in alive_aliens:
                        a.y -= 15
                else:
                    for a in alive_aliens:
                        a.x += step_x

            # Check if aliens reached player level
            for a in alive_aliens:
                if a.y - ALIEN_HEIGHT / 2 <= PLAYER_Y + PLAYER_HEIGHT / 2:
                    self.game_over = True
                    self.victory = False
                    if self.score > self.high_score:
                        self.high_score = self.score
                    return

            # Alien shooting
            self.alien_shoot_timer += dt
            if self.alien_shoot_timer >= self._alien_shoot_interval():
                self.alien_shoot_timer = 0.0
                # Pick a random alive alien from the bottom of each column
                bottom_aliens = {}
                for a in alive_aliens:
                    if a.col not in bottom_aliens or a.y < bottom_aliens[a.col].y:
                        bottom_aliens[a.col] = a
                if bottom_aliens:
                    shooter = random.choice(list(bottom_aliens.values()))
                    bullet = Bullet(shooter.x, shooter.y - ALIEN_HEIGHT / 2,
                                    -ALIEN_BULLET_SPEED, BULLET_ALIEN_COLOR)
                    self.alien_bullets.append(bullet)

        # UFO logic
        self.ufo.update(dt)
        if not self.ufo.active:
            self.ufo_timer += dt
            if self.ufo_timer > random.uniform(15, 30):
                self.ufo_timer = 0.0
                self.ufo.spawn()

        # --- Collision detection ---

        # Player bullets vs aliens
        for b in self.player_bullets:
            if not b.alive:
                continue
            for a in alive_aliens:
                if not a.alive:
                    continue
                if (abs(b.x - a.x) < ALIEN_WIDTH / 2 + 2 and
                        abs(b.y - a.y) < ALIEN_HEIGHT / 2 + 2):
                    b.alive = False
                    a.alive = False
                    self.score += a.points
                    break

        # Player bullets vs UFO
        if self.ufo.active:
            for b in self.player_bullets:
                if not b.alive:
                    continue
                if (abs(b.x - self.ufo.x) < UFO_WIDTH / 2 + 2 and
                        abs(b.y - self.ufo.y) < UFO_HEIGHT / 2 + 2):
                    b.alive = False
                    self.score += self.ufo.points
                    self.ufo_score_display = (self.ufo.x, self.ufo.y)
                    self.ufo_score_timer = 1.5
                    self.ufo.active = False
                    break

        # Bullets vs shields
        for b in self.player_bullets + self.alien_bullets:
            if not b.alive:
                continue
            for block in self.shields:
                if not block[2]:  # already destroyed
                    continue
                if (abs(b.x - block[0]) < (SHIELD_BLOCK_SIZE + BULLET_WIDTH) / 2 and
                        abs(b.y - block[1]) < (SHIELD_BLOCK_SIZE + BULLET_HEIGHT) / 2):
                    b.alive = False
                    block[2] = False
                    break

        # Alien bullets vs player
        if self.player_invincible <= 0:
            for b in self.alien_bullets:
                if not b.alive:
                    continue
                if (abs(b.x - self.player_x) < PLAYER_WIDTH / 2 + 2 and
                        abs(b.y - PLAYER_Y) < PLAYER_HEIGHT / 2 + PLAYER_TURRET_H / 2 + 2):
                    b.alive = False
                    self.lives -= 1
                    self.player_invincible = 2.0
                    if self.lives <= 0:
                        self.game_over = True
                        self.victory = False
                        if self.score > self.high_score:
                            self.high_score = self.score
                        return

        # Clean up bullets
        self.player_bullets = [b for b in self.player_bullets if b.alive]
        self.alien_bullets = [b for b in self.alien_bullets if b.alive]

        # Check wave clear
        if len(self._alive_aliens()) == 0 and not self.game_over:
            self.wave += 1
            self._spawn_aliens(self.wave - 1)
            self.alien_direction = 1
            self.alien_move_timer = 0.0
            self.alien_shoot_timer = 0.0
            self.alien_bullets.clear()
            self._create_shields()
            self.ufo.active = False
            self.ufo_timer = 0.0

        # Update high score
        if self.score > self.high_score:
            self.high_score = self.score

    def on_draw(self):
        self.clear()
        space_invaders_renderer.draw(self)

    def on_key_press(self, key, modifiers):
        if self.game_over:
            if key == arcade.key.RETURN or key == arcade.key.ENTER:
                self._init_game()
            return

        if key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
        elif key == arcade.key.SPACE:
            self._fire_player_bullet()

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False

    def _fire_player_bullet(self):
        if len(self.player_bullets) >= MAX_PLAYER_BULLETS:
            return
        bullet = Bullet(
            self.player_x,
            PLAYER_Y + PLAYER_HEIGHT / 2 + PLAYER_TURRET_H,
            PLAYER_BULLET_SPEED,
            BULLET_PLAYER_COLOR,
        )
        self.player_bullets.append(bullet)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        if self.btn_back.contains(x, y):
            self.window.show_view(self.menu_view)
            return

        if self.btn_help.contains(x, y):
            rules_view = RulesView(
                "Space Invaders", "space_invaders.txt", None,
                self.menu_view, existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return
