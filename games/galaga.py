"""
Galaga game view for Python Arcade 3.x.
Classic Galaga with bees, butterflies, boss Galaga, dive-bombing,
tractor beam capture, and dual fighter mechanics.
"""

import arcade
import random
import math
from pages.rules import RulesView
from renderers import galaga_renderer
from ai.galaga_ai import (
    BeeAI, ButterflyAI, BossGalagaAI,
    generate_formation_sway, generate_entry_path,
    pick_divers, get_ai_for_type,
)

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
BOTTOM_BAR_HEIGHT = 40
PLAY_TOP = HEIGHT - TOP_BAR_HEIGHT
PLAY_BOTTOM = BOTTOM_BAR_HEIGHT

# Colors
BG_COLOR = (0, 0, 10)
LINE_COLOR = (205, 214, 244)
BUTTON_COLOR = (69, 71, 90)
BUTTON_HOVER_COLOR = (88, 91, 112)
BUTTON_TEXT_COLOR = (205, 214, 244)
OVERLAY_COLOR = (0, 0, 0, 200)
SCORE_COLOR = (255, 255, 255)

# Player
PLAYER_Y = PLAY_BOTTOM + 30
PLAYER_SPEED = 280
PLAYER_WIDTH = 30
PLAYER_HEIGHT = 20
MAX_PLAYER_BULLETS = 2

# Bullets
PLAYER_BULLET_SPEED = 450
ENEMY_BULLET_SPEED = 220
BULLET_WIDTH = 3
BULLET_HEIGHT = 10

# Enemy formation grid
FORMATION_COLS = 10
FORMATION_ROWS = 4  # row 0 = bosses, 1 = butterflies, 2-3 = bees
FORMATION_H_SPACING = 50
FORMATION_V_SPACING = 38
FORMATION_TOP_Y = PLAY_TOP - 70
FORMATION_CENTER_X = WIDTH / 2

# Enemy sizes
ENEMY_WIDTH = 28
ENEMY_HEIGHT = 22
BOSS_WIDTH = 34
BOSS_HEIGHT = 28

# Tractor beam
TRACTOR_BEAM_WIDTH = 40
TRACTOR_BEAM_HEIGHT = 180

# Dive timing
DIVE_INTERVAL_BASE = 2.5  # seconds between dive waves
DIVE_MAX_SIMULTANEOUS = 2

# Scoring (formation / diving)
SCORE_TABLE = {
    'bee': (50, 100),
    'butterfly': (80, 160),
    'boss': (150, 400),
}


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


class GalagaView(arcade.View):
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

        # Starfield (persistent across stages)
        self.stars = [(random.uniform(0, WIDTH), random.uniform(0, HEIGHT),
                       random.uniform(0.5, 2.0)) for _ in range(120)]

        self._create_texts()
        self._init_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects."""
        self.txt_score = arcade.Text(
            "", 140, HEIGHT - 18, SCORE_COLOR,
            font_size=14, anchor_x="left", anchor_y="center",
        )
        self.txt_high_score = arcade.Text(
            "", 140, HEIGHT - 38, (180, 180, 180),
            font_size=11, anchor_x="left", anchor_y="center",
        )
        self.txt_stage = arcade.Text(
            "", WIDTH - 80, HEIGHT - 18, (200, 200, 255),
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
        self.txt_stage_intro = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2,
            (255, 255, 100), font_size=28,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_ready = arcade.Text(
            "READY", WIDTH // 2, HEIGHT // 2 - 40,
            (100, 200, 255), font_size=20,
            anchor_x="center", anchor_y="center",
        )
        self.txt_captured = arcade.Text(
            "FIGHTER CAPTURED", WIDTH // 2, HEIGHT // 2,
            (255, 100, 100), font_size=22,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_dual = arcade.Text(
            "DUAL FIGHTER!", WIDTH // 2, HEIGHT // 2,
            (100, 255, 100), font_size=22,
            anchor_x="center", anchor_y="center", bold=True,
        )

    def _init_game(self):
        """Initialize or reset all game state."""
        self.score = 0
        self.lives = 3
        self.stage = 1
        self.game_over = False
        self.game_time = 0.0

        # Player
        self.player_x = WIDTH / 2
        self.player_invincible = 0.0
        self.dual_fighter = False
        self.captured_ship = None  # reference to boss enemy dict holding captured ship

        # Stage intro
        self.stage_intro_timer = 2.0  # seconds to show stage number

        # Bullets
        self.player_bullets = []
        self.enemy_bullets = []

        # Explosions: list of {x, y, timer, max_time}
        self.explosions = []

        # Enemies
        self.enemies = []
        self._spawn_formation()

        # Dive control
        self.dive_timer = 3.0  # initial delay before first dive
        self.all_in_formation = False  # True once entry animation completes

        # Tractor beam capture state
        self.capture_msg_timer = 0.0
        self.dual_msg_timer = 0.0

    def _formation_pos(self, row, col):
        """Calculate the target formation position for a grid slot."""
        x = FORMATION_CENTER_X + (col - FORMATION_COLS / 2 + 0.5) * FORMATION_H_SPACING
        y = FORMATION_TOP_Y - row * FORMATION_V_SPACING
        return x, y

    def _spawn_formation(self):
        """Create the enemy grid for the current stage."""
        self.enemies = []
        entry_delay = 0.0
        group = 0

        for row in range(FORMATION_ROWS):
            for col in range(FORMATION_COLS):
                fx, fy = self._formation_pos(row, col)

                if row == 0:
                    etype = 'boss'
                    hp = 2
                elif row == 1:
                    etype = 'butterfly'
                    hp = 1
                else:
                    etype = 'bee'
                    hp = 1

                enemy = {
                    'type': etype,
                    'x': -50.0,  # start off-screen
                    'y': HEIGHT + 50.0,
                    'hp': hp,
                    'max_hp': hp,
                    'state': 'entering',  # entering | formation | diving | dead
                    'formation_row': row,
                    'formation_col': col,
                    'formation_x': fx,
                    'formation_y': fy,
                    'dive_path': None,
                    'dive_segment': 0,
                    'dive_t': 0.0,
                    'should_shoot': False,
                    'tractor_beam_active': False,
                    'tractor_beam_timer': 0.0,
                    'tractor_beam_used': False,
                    'shoot_cooldown': 0.0,
                    'stage': self.stage - 1,
                    'anim_timer': random.uniform(0, math.pi * 2),
                    # Entry animation
                    'entry_path': None,
                    'entry_segment': 0,
                    'entry_t': 0.0,
                    'entry_delay': entry_delay,
                    'entry_group': group,
                    # Captured ship attached to this boss
                    'has_captured_ship': False,
                }

                # Generate entry path
                enemy['entry_path'] = generate_entry_path(
                    fx, fy, group % 3, col, WIDTH, HEIGHT)

                self.enemies.append(enemy)
                entry_delay += 0.08  # stagger entries

            group += 1

        self.all_in_formation = False

    def _alive_enemies(self):
        return [e for e in self.enemies if e['state'] != 'dead']

    def _formation_enemies(self):
        return [e for e in self.enemies if e['state'] == 'formation']

    # -------------------------------------------------------------------
    # Update
    # -------------------------------------------------------------------

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_update(self, delta_time):
        dt = delta_time
        self.game_time += dt

        # Update starfield
        for i, (sx, sy, speed) in enumerate(self.stars):
            sy -= speed * 40 * dt
            if sy < 0:
                sy = HEIGHT
                sx = random.uniform(0, WIDTH)
            self.stars[i] = (sx, sy, speed)

        # Update explosions
        for exp in self.explosions:
            exp['timer'] -= dt
        self.explosions = [e for e in self.explosions if e['timer'] > 0]

        # Stage intro
        if self.stage_intro_timer > 0:
            self.stage_intro_timer -= dt
            return

        if self.game_over:
            return

        # Capture / dual fighter messages
        if self.capture_msg_timer > 0:
            self.capture_msg_timer -= dt
            return
        if self.dual_msg_timer > 0:
            self.dual_msg_timer -= dt
            return

        # Player movement
        if self.left_pressed:
            self.player_x -= PLAYER_SPEED * dt
        if self.right_pressed:
            self.player_x += PLAYER_SPEED * dt
        margin = PLAYER_WIDTH if self.dual_fighter else PLAYER_WIDTH / 2
        self.player_x = max(margin + 5, min(WIDTH - margin - 5, self.player_x))

        # Invincibility
        if self.player_invincible > 0:
            self.player_invincible -= dt

        # --- Update enemies ---
        all_entered = True
        for enemy in self.enemies:
            if enemy['state'] == 'dead':
                continue

            enemy['anim_timer'] += dt

            if enemy['state'] == 'entering':
                self._update_entering(enemy, dt)
                if enemy['state'] == 'entering':
                    all_entered = False

            elif enemy['state'] == 'formation':
                # Apply formation sway
                sway_dx, sway_dy = generate_formation_sway(
                    self.game_time, enemy['formation_col'], enemy['formation_row'])
                enemy['x'] = enemy['formation_x'] + sway_dx
                enemy['y'] = enemy['formation_y'] + sway_dy

            elif enemy['state'] == 'diving':
                self._update_diving(enemy, dt)

        if all_entered and not self.all_in_formation:
            self.all_in_formation = True

        # --- Dive control ---
        if self.all_in_formation:
            self.dive_timer -= dt
            if self.dive_timer <= 0:
                diving_count = sum(1 for e in self.enemies if e['state'] == 'diving')
                max_d = DIVE_MAX_SIMULTANEOUS + self.stage // 2
                if diving_count < max_d:
                    chosen = pick_divers(self.enemies, DIVE_MAX_SIMULTANEOUS, self.stage)
                    for idx in chosen:
                        e = self.enemies[idx]
                        e['state'] = 'diving'
                        e['dive_path'] = None
                        e['dive_segment'] = 0
                        e['dive_t'] = 0.0
                        e['tractor_beam_used'] = False
                        e['tractor_beam_active'] = False

                interval = max(0.8, DIVE_INTERVAL_BASE - self.stage * 0.15)
                self.dive_timer = random.uniform(interval * 0.7, interval * 1.3)

        # --- Update bullets ---
        for b in self.player_bullets:
            b['y'] += PLAYER_BULLET_SPEED * dt
        self.player_bullets = [b for b in self.player_bullets
                               if b['y'] < HEIGHT + 10]

        for b in self.enemy_bullets:
            b['y'] -= ENEMY_BULLET_SPEED * dt
        self.enemy_bullets = [b for b in self.enemy_bullets
                              if b['y'] > PLAY_BOTTOM - 10]

        # --- Enemy shooting ---
        for enemy in self.enemies:
            if enemy.get('should_shoot', False):
                enemy['should_shoot'] = False
                self.enemy_bullets.append({
                    'x': enemy['x'],
                    'y': enemy['y'] - 10,
                })

        # --- Collision detection ---
        self._check_collisions()

        # --- Tractor beam capture ---
        self._check_tractor_beam()

        # --- Check stage clear ---
        alive = [e for e in self.enemies if e['state'] != 'dead']
        if not alive:
            self.stage += 1
            self.stage_intro_timer = 2.0
            self.enemy_bullets.clear()
            self.dive_timer = 3.0
            self._spawn_formation()

        # Update high score
        if self.score > self.high_score:
            self.high_score = self.score

    def _update_entering(self, enemy, dt):
        """Animate an enemy entering the screen along its entry path."""
        enemy['entry_delay'] -= dt
        if enemy['entry_delay'] > 0:
            return

        path = enemy['entry_path']
        if path is None:
            enemy['state'] = 'formation'
            return

        enemy['entry_t'] += dt * 1.5  # entry speed

        seg_idx = enemy['entry_segment']
        if seg_idx >= len(path):
            enemy['state'] = 'formation'
            enemy['x'] = enemy['formation_x']
            enemy['y'] = enemy['formation_y']
            return

        from ai.galaga_ai import _bezier_cubic
        t = min(enemy['entry_t'], 1.0)
        seg = path[seg_idx]
        x, y = _bezier_cubic(*seg, t)
        enemy['x'] = x
        enemy['y'] = y

        if enemy['entry_t'] >= 1.0:
            enemy['entry_segment'] += 1
            enemy['entry_t'] = 0.0
            if enemy['entry_segment'] >= len(path):
                enemy['state'] = 'formation'
                enemy['x'] = enemy['formation_x']
                enemy['y'] = enemy['formation_y']

    def _update_diving(self, enemy, dt):
        """Update a diving enemy using its AI class."""
        ai_cls = get_ai_for_type(enemy['type'])
        done = ai_cls.update_diving(enemy, self.player_x, dt, WIDTH, HEIGHT)

        if done:
            # Return to formation
            enemy['state'] = 'formation'
            enemy['x'] = enemy['formation_x']
            enemy['y'] = enemy['formation_y']
            enemy['dive_path'] = None

    def _check_collisions(self):
        """Handle all collision detection."""
        # Player bullets vs enemies
        for b in self.player_bullets:
            if not b.get('alive', True):
                continue
            for enemy in self.enemies:
                if enemy['state'] == 'dead':
                    continue
                ew = BOSS_WIDTH if enemy['type'] == 'boss' else ENEMY_WIDTH
                eh = BOSS_HEIGHT if enemy['type'] == 'boss' else ENEMY_HEIGHT
                if (abs(b['x'] - enemy['x']) < ew / 2 + 2 and
                        abs(b['y'] - enemy['y']) < eh / 2 + 2):
                    b['alive'] = False
                    enemy['hp'] -= 1
                    if enemy['hp'] <= 0:
                        # Score: different points for formation vs diving
                        score_idx = 0 if enemy['state'] == 'formation' else 1
                        self.score += SCORE_TABLE[enemy['type']][score_idx]
                        enemy['state'] = 'dead'

                        # Explosion
                        self.explosions.append({
                            'x': enemy['x'], 'y': enemy['y'],
                            'timer': 0.4, 'max_time': 0.4,
                        })

                        # If boss had captured ship, free it
                        if enemy.get('has_captured_ship', False):
                            self._free_captured_ship(enemy)

                    break

        # Remove dead bullets
        self.player_bullets = [b for b in self.player_bullets if b.get('alive', True)]

        # Enemy bullets vs player
        if self.player_invincible <= 0:
            for b in self.enemy_bullets:
                pw = PLAYER_WIDTH * 2 if self.dual_fighter else PLAYER_WIDTH
                if (abs(b['x'] - self.player_x) < pw / 2 + 2 and
                        abs(b['y'] - PLAYER_Y) < PLAYER_HEIGHT / 2 + 2):
                    b['alive'] = False
                    self._player_hit()
                    break

        self.enemy_bullets = [b for b in self.enemy_bullets if b.get('alive', True)]

        # Enemy body vs player
        if self.player_invincible <= 0:
            for enemy in self.enemies:
                if enemy['state'] not in ('diving', 'entering'):
                    continue
                ew = BOSS_WIDTH if enemy['type'] == 'boss' else ENEMY_WIDTH
                pw = PLAYER_WIDTH * 2 if self.dual_fighter else PLAYER_WIDTH
                if (abs(enemy['x'] - self.player_x) < (ew + pw) / 2 and
                        abs(enemy['y'] - PLAYER_Y) < (ENEMY_HEIGHT + PLAYER_HEIGHT) / 2):
                    enemy['hp'] = 0
                    enemy['state'] = 'dead'
                    self.explosions.append({
                        'x': enemy['x'], 'y': enemy['y'],
                        'timer': 0.4, 'max_time': 0.4,
                    })
                    self._player_hit()
                    break

    def _check_tractor_beam(self):
        """Check if any boss's tractor beam captures the player."""
        if self.player_invincible > 0:
            return
        for enemy in self.enemies:
            if (enemy['state'] == 'diving' and enemy['type'] == 'boss' and
                    enemy.get('tractor_beam_active', False)):
                # Check if player is within beam
                beam_x = enemy['x']
                beam_top = enemy['y'] - BOSS_HEIGHT / 2
                beam_bottom = beam_top - TRACTOR_BEAM_HEIGHT
                if (abs(self.player_x - beam_x) < TRACTOR_BEAM_WIDTH / 2 + PLAYER_WIDTH / 2 and
                        PLAYER_Y > beam_bottom and PLAYER_Y < beam_top):
                    # Captured!
                    self._capture_player(enemy)
                    return

    def _capture_player(self, boss_enemy):
        """Handle the boss capturing the player's ship."""
        boss_enemy['has_captured_ship'] = True
        boss_enemy['tractor_beam_active'] = False
        self.captured_ship = boss_enemy

        if self.dual_fighter:
            # Lose dual fighter status
            self.dual_fighter = False
            self.capture_msg_timer = 1.5
        else:
            self.lives -= 1
            self.capture_msg_timer = 1.5
            self.player_invincible = 2.0
            if self.lives <= 0:
                self.game_over = True
                if self.score > self.high_score:
                    self.high_score = self.score

    def _free_captured_ship(self, boss_enemy):
        """When a boss holding a captured ship is destroyed, grant dual fighter."""
        boss_enemy['has_captured_ship'] = False
        if not self.game_over and self.lives > 0:
            self.dual_fighter = True
            self.dual_msg_timer = 1.5
            self.captured_ship = None

    def _player_hit(self):
        """Handle player taking damage."""
        if self.dual_fighter:
            self.dual_fighter = False
            self.player_invincible = 2.0
            self.explosions.append({
                'x': self.player_x + PLAYER_WIDTH, 'y': PLAYER_Y,
                'timer': 0.4, 'max_time': 0.4,
            })
        else:
            self.lives -= 1
            self.player_invincible = 2.0
            self.explosions.append({
                'x': self.player_x, 'y': PLAYER_Y,
                'timer': 0.4, 'max_time': 0.4,
            })
            if self.lives <= 0:
                self.game_over = True
                if self.score > self.high_score:
                    self.high_score = self.score

    # -------------------------------------------------------------------
    # Drawing
    # -------------------------------------------------------------------

    def on_draw(self):
        self.clear()
        galaga_renderer.draw(self)

    # -------------------------------------------------------------------
    # Input
    # -------------------------------------------------------------------

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
        if self.dual_fighter:
            # Two bullets side by side
            self.player_bullets.append({
                'x': self.player_x - 12,
                'y': PLAYER_Y + PLAYER_HEIGHT / 2 + 5,
                'alive': True,
            })
            self.player_bullets.append({
                'x': self.player_x + 12,
                'y': PLAYER_Y + PLAYER_HEIGHT / 2 + 5,
                'alive': True,
            })
        else:
            self.player_bullets.append({
                'x': self.player_x,
                'y': PLAYER_Y + PLAYER_HEIGHT / 2 + 5,
                'alive': True,
            })

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
                "Galaga", "galaga.txt", None,
                self.menu_view, existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return
