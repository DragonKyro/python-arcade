"""
Renderer for the Galaga game.
All drawing code. NO imports from games/*.
"""

import arcade
import math

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
BOTTOM_BAR_HEIGHT = 40
PLAY_TOP = HEIGHT - TOP_BAR_HEIGHT
PLAY_BOTTOM = BOTTOM_BAR_HEIGHT

# Player
PLAYER_Y = PLAY_BOTTOM + 30
PLAYER_WIDTH = 30
PLAYER_HEIGHT = 20

# Bullet
BULLET_WIDTH = 3
BULLET_HEIGHT = 10
PLAYER_BULLET_COLOR = (255, 255, 255)
ENEMY_BULLET_COLOR = (255, 100, 100)

# Enemy sizes
ENEMY_WIDTH = 28
ENEMY_HEIGHT = 22
BOSS_WIDTH = 34
BOSS_HEIGHT = 28

# Tractor beam
TRACTOR_BEAM_WIDTH = 40
TRACTOR_BEAM_HEIGHT = 180

# Colors
BG_COLOR = (0, 0, 10)
LINE_COLOR = (205, 214, 244)
OVERLAY_COLOR = (0, 0, 0, 200)
SCORE_COLOR = (255, 255, 255)

# Enemy colors
BEE_COLOR = (80, 160, 255)
BEE_WING_COLOR = (60, 120, 220)
BUTTERFLY_COLOR = (255, 80, 80)
BUTTERFLY_WING_COLOR = (220, 50, 80)
BOSS_COLOR = (80, 220, 80)
BOSS_ACCENT_COLOR = (60, 180, 60)
BOSS_HIT_COLOR = (120, 120, 220)  # after first hit

# Player colors
SHIP_COLOR = (200, 255, 255)
SHIP_ACCENT = (100, 200, 255)
SHIP_WING_COLOR = (80, 180, 220)

# Explosion colors
EXPLOSION_COLORS = [
    (255, 255, 100),
    (255, 200, 50),
    (255, 120, 30),
    (255, 60, 20),
]


def draw(game):
    """Render the entire Galaga game state."""
    # --- Starfield background ---
    _draw_starfield(game)

    # --- Enemies ---
    for enemy in game.enemies:
        if enemy['state'] == 'dead':
            continue
        _draw_enemy(enemy)

    # --- Tractor beams ---
    for enemy in game.enemies:
        if (enemy['state'] == 'diving' and enemy['type'] == 'boss' and
                enemy.get('tractor_beam_active', False)):
            _draw_tractor_beam(enemy)

    # --- Bullets ---
    for b in game.player_bullets:
        if b.get('alive', True):
            arcade.draw_rect_filled(
                arcade.XYWH(b['x'], b['y'], BULLET_WIDTH, BULLET_HEIGHT),
                PLAYER_BULLET_COLOR,
            )

    for b in game.enemy_bullets:
        if b.get('alive', True):
            arcade.draw_rect_filled(
                arcade.XYWH(b['x'], b['y'], BULLET_WIDTH, BULLET_HEIGHT),
                ENEMY_BULLET_COLOR,
            )

    # --- Player ---
    draw_player = True
    if game.player_invincible > 0:
        if int(game.player_invincible * 10) % 2 == 0:
            draw_player = False

    if draw_player and not game.game_over:
        _draw_player(game)

    # --- Explosions ---
    for exp in game.explosions:
        _draw_explosion(exp)

    # --- UI ---
    _draw_top_bar(game)
    _draw_bottom_bar(game)

    # --- Stage intro ---
    if game.stage_intro_timer > 0:
        _draw_stage_intro(game)

    # --- Capture / dual messages ---
    if game.capture_msg_timer > 0:
        _draw_capture_message(game)
    if game.dual_msg_timer > 0:
        _draw_dual_message(game)

    # --- Game over ---
    if game.game_over:
        _draw_game_over(game)


# -----------------------------------------------------------------------
# Starfield
# -----------------------------------------------------------------------

def _draw_starfield(game):
    """Draw scrolling star dots."""
    for sx, sy, brightness in game.stars:
        intensity = int(100 + brightness * 80)
        color = (intensity, intensity, intensity + 20)
        size = 1.0 + brightness * 0.6
        arcade.draw_circle_filled(sx, sy, size, color)


# -----------------------------------------------------------------------
# Enemies
# -----------------------------------------------------------------------

def _draw_enemy(enemy):
    """Draw an enemy based on its type."""
    etype = enemy['type']
    x, y = enemy['x'], enemy['y']
    frame = int(enemy.get('anim_timer', 0) * 4) % 2

    if etype == 'bee':
        _draw_bee(x, y, frame)
    elif etype == 'butterfly':
        _draw_butterfly(x, y, frame)
    elif etype == 'boss':
        hit = enemy.get('hp', 2) < enemy.get('max_hp', 2)
        _draw_boss(x, y, frame, hit, enemy.get('has_captured_ship', False))


def _draw_bee(x, y, frame):
    """Bee: compact body with small flapping wings. Blue tones."""
    # Body
    arcade.draw_rect_filled(arcade.XYWH(x, y, 12, 16), BEE_COLOR)
    # Head
    arcade.draw_circle_filled(x, y + 10, 5, BEE_COLOR)
    # Eyes
    arcade.draw_circle_filled(x - 2, y + 11, 1.5, (255, 255, 255))
    arcade.draw_circle_filled(x + 2, y + 11, 1.5, (255, 255, 255))

    # Wings (flap based on frame)
    if frame == 0:
        # Wings out
        wing_pts_l = [
            (x - 6, y + 4), (x - 16, y + 8), (x - 14, y - 2), (x - 6, y - 4)
        ]
        wing_pts_r = [
            (x + 6, y + 4), (x + 16, y + 8), (x + 14, y - 2), (x + 6, y - 4)
        ]
    else:
        # Wings folded
        wing_pts_l = [
            (x - 6, y + 4), (x - 12, y + 2), (x - 10, y - 4), (x - 6, y - 4)
        ]
        wing_pts_r = [
            (x + 6, y + 4), (x + 12, y + 2), (x + 10, y - 4), (x + 6, y - 4)
        ]

    # Draw wings as triangles (two triangles per wing for quad shape)
    arcade.draw_triangle_filled(
        wing_pts_l[0][0], wing_pts_l[0][1],
        wing_pts_l[1][0], wing_pts_l[1][1],
        wing_pts_l[2][0], wing_pts_l[2][1],
        BEE_WING_COLOR,
    )
    arcade.draw_triangle_filled(
        wing_pts_l[0][0], wing_pts_l[0][1],
        wing_pts_l[2][0], wing_pts_l[2][1],
        wing_pts_l[3][0], wing_pts_l[3][1],
        BEE_WING_COLOR,
    )
    arcade.draw_triangle_filled(
        wing_pts_r[0][0], wing_pts_r[0][1],
        wing_pts_r[1][0], wing_pts_r[1][1],
        wing_pts_r[2][0], wing_pts_r[2][1],
        BEE_WING_COLOR,
    )
    arcade.draw_triangle_filled(
        wing_pts_r[0][0], wing_pts_r[0][1],
        wing_pts_r[2][0], wing_pts_r[2][1],
        wing_pts_r[3][0], wing_pts_r[3][1],
        BEE_WING_COLOR,
    )

    # Bottom fin
    arcade.draw_triangle_filled(
        x - 4, y - 8, x + 4, y - 8, x, y - 14,
        BEE_COLOR,
    )


def _draw_butterfly(x, y, frame):
    """Butterfly: wider body with large colorful wings. Red tones."""
    # Body
    arcade.draw_rect_filled(arcade.XYWH(x, y, 10, 18), BUTTERFLY_COLOR)
    # Head
    arcade.draw_circle_filled(x, y + 12, 6, BUTTERFLY_COLOR)
    # Antennae
    arcade.draw_line(x - 3, y + 16, x - 8, y + 22, BUTTERFLY_COLOR, 1)
    arcade.draw_line(x + 3, y + 16, x + 8, y + 22, BUTTERFLY_COLOR, 1)
    # Eyes
    arcade.draw_circle_filled(x - 3, y + 13, 1.5, (255, 255, 200))
    arcade.draw_circle_filled(x + 3, y + 13, 1.5, (255, 255, 200))

    # Wings
    if frame == 0:
        # Wings spread wide
        # Upper wings
        arcade.draw_triangle_filled(
            x - 5, y + 6, x - 20, y + 14, x - 18, y - 2,
            BUTTERFLY_WING_COLOR,
        )
        arcade.draw_triangle_filled(
            x + 5, y + 6, x + 20, y + 14, x + 18, y - 2,
            BUTTERFLY_WING_COLOR,
        )
        # Lower wings
        arcade.draw_triangle_filled(
            x - 5, y - 2, x - 16, y - 4, x - 12, y - 14,
            (200, 60, 80),
        )
        arcade.draw_triangle_filled(
            x + 5, y - 2, x + 16, y - 4, x + 12, y - 14,
            (200, 60, 80),
        )
        # Wing spots
        arcade.draw_circle_filled(x - 14, y + 6, 2, (255, 200, 100))
        arcade.draw_circle_filled(x + 14, y + 6, 2, (255, 200, 100))
    else:
        # Wings partially folded
        arcade.draw_triangle_filled(
            x - 5, y + 6, x - 14, y + 10, x - 12, y - 4,
            BUTTERFLY_WING_COLOR,
        )
        arcade.draw_triangle_filled(
            x + 5, y + 6, x + 14, y + 10, x + 12, y - 4,
            BUTTERFLY_WING_COLOR,
        )
        arcade.draw_triangle_filled(
            x - 5, y - 2, x - 10, y - 6, x - 8, y - 12,
            (200, 60, 80),
        )
        arcade.draw_triangle_filled(
            x + 5, y - 2, x + 10, y - 6, x + 8, y - 12,
            (200, 60, 80),
        )

    # Bottom detail
    arcade.draw_triangle_filled(
        x - 3, y - 9, x + 3, y - 9, x, y - 16,
        BUTTERFLY_COLOR,
    )


def _draw_boss(x, y, frame, is_hit, has_captured):
    """Boss Galaga: larger, green. Changes color after first hit."""
    color = BOSS_HIT_COLOR if is_hit else BOSS_COLOR
    accent = (100, 100, 200) if is_hit else BOSS_ACCENT_COLOR

    # Main body (wider)
    arcade.draw_rect_filled(arcade.XYWH(x, y, 20, 22), color)
    # Head/crown
    arcade.draw_rect_filled(arcade.XYWH(x, y + 14, 16, 6), color)
    # Crown points
    arcade.draw_triangle_filled(
        x - 8, y + 17, x - 4, y + 17, x - 6, y + 24, accent,
    )
    arcade.draw_triangle_filled(
        x - 2, y + 17, x + 2, y + 17, x, y + 26, accent,
    )
    arcade.draw_triangle_filled(
        x + 4, y + 17, x + 8, y + 17, x + 6, y + 24, accent,
    )

    # Eyes (menacing)
    arcade.draw_rect_filled(arcade.XYWH(x - 5, y + 8, 5, 4), (255, 255, 200))
    arcade.draw_rect_filled(arcade.XYWH(x + 5, y + 8, 5, 4), (255, 255, 200))
    arcade.draw_rect_filled(arcade.XYWH(x - 5, y + 8, 2, 2), (0, 0, 0))
    arcade.draw_rect_filled(arcade.XYWH(x + 5, y + 8, 2, 2), (0, 0, 0))

    # Wings / shoulder armor
    if frame == 0:
        arcade.draw_triangle_filled(
            x - 10, y + 8, x - 22, y + 4, x - 18, y - 8, color,
        )
        arcade.draw_triangle_filled(
            x + 10, y + 8, x + 22, y + 4, x + 18, y - 8, color,
        )
    else:
        arcade.draw_triangle_filled(
            x - 10, y + 8, x - 18, y + 0, x - 14, y - 10, color,
        )
        arcade.draw_triangle_filled(
            x + 10, y + 8, x + 18, y + 0, x + 14, y - 10, color,
        )

    # Lower body
    arcade.draw_triangle_filled(
        x - 8, y - 11, x + 8, y - 11, x, y - 18, accent,
    )

    # Captured ship indicator (small ship shape below boss)
    if has_captured:
        cx, cy = x, y - 22
        arcade.draw_triangle_filled(
            cx - 6, cy - 4, cx + 6, cy - 4, cx, cy + 4,
            (200, 200, 255),
        )


# -----------------------------------------------------------------------
# Tractor beam
# -----------------------------------------------------------------------

def _draw_tractor_beam(enemy):
    """Draw the boss's tractor beam as a translucent cone."""
    x = enemy['x']
    top_y = enemy['y'] - BOSS_HEIGHT / 2
    bottom_y = top_y - TRACTOR_BEAM_HEIGHT
    top_half_w = TRACTOR_BEAM_WIDTH * 0.3
    bottom_half_w = TRACTOR_BEAM_WIDTH * 0.8

    # Beam body (semi-transparent layered triangles)
    for i, alpha in enumerate([40, 30, 20]):
        spread = i * 4
        color = (100, 200, 255, alpha)
        arcade.draw_triangle_filled(
            x - top_half_w - spread, top_y,
            x + top_half_w + spread, top_y,
            x - bottom_half_w - spread, bottom_y,
            color,
        )
        arcade.draw_triangle_filled(
            x + top_half_w + spread, top_y,
            x - bottom_half_w - spread, bottom_y,
            x + bottom_half_w + spread, bottom_y,
            color,
        )

    # Beam edges
    arcade.draw_line(x - top_half_w, top_y, x - bottom_half_w, bottom_y,
                     (100, 200, 255, 80), 1)
    arcade.draw_line(x + top_half_w, top_y, x + bottom_half_w, bottom_y,
                     (100, 200, 255, 80), 1)

    # Pulsing horizontal lines inside beam
    timer = enemy.get('tractor_beam_timer', 0)
    for i in range(6):
        frac = (i + 1) / 7
        ly = top_y + (bottom_y - top_y) * frac
        lw = top_half_w + (bottom_half_w - top_half_w) * frac
        pulse = math.sin(timer * 8 + i * 1.2) * 0.5 + 0.5
        alpha = int(30 + pulse * 40)
        arcade.draw_line(x - lw, ly, x + lw, ly, (150, 220, 255, alpha), 1)


# -----------------------------------------------------------------------
# Player
# -----------------------------------------------------------------------

def _draw_player(game):
    """Draw the player's ship (or dual fighter)."""
    px, py = game.player_x, PLAYER_Y

    if game.dual_fighter:
        # Two ships side by side
        _draw_single_ship(px - 12, py)
        _draw_single_ship(px + 12, py)
        # Connecting bar
        arcade.draw_rect_filled(arcade.XYWH(px, py - 4, 20, 3), SHIP_ACCENT)
    else:
        _draw_single_ship(px, py)


def _draw_single_ship(x, y):
    """Draw a single player ship — a classic arrow/fighter shape."""
    # Main body
    arcade.draw_rect_filled(arcade.XYWH(x, y, 8, 18), SHIP_COLOR)
    # Nose
    arcade.draw_triangle_filled(
        x - 4, y + 9, x + 4, y + 9, x, y + 20,
        SHIP_COLOR,
    )
    # Wings
    arcade.draw_triangle_filled(
        x - 4, y + 2, x - 4, y - 8, x - 14, y - 8,
        SHIP_WING_COLOR,
    )
    arcade.draw_triangle_filled(
        x + 4, y + 2, x + 4, y - 8, x + 14, y - 8,
        SHIP_WING_COLOR,
    )
    # Engine glow
    arcade.draw_rect_filled(arcade.XYWH(x, y - 10, 4, 4), (255, 150, 50))
    arcade.draw_rect_filled(arcade.XYWH(x, y - 13, 2, 3), (255, 255, 100))


# -----------------------------------------------------------------------
# Explosions
# -----------------------------------------------------------------------

def _draw_explosion(exp):
    """Draw an expanding explosion effect."""
    x, y = exp['x'], exp['y']
    progress = 1.0 - exp['timer'] / exp['max_time']

    # Multiple expanding rings/particles
    for i in range(8):
        angle = i * math.pi / 4 + progress * 0.5
        dist = progress * 30
        px = x + math.cos(angle) * dist
        py = y + math.sin(angle) * dist
        size = max(1, (1 - progress) * 5)
        cidx = min(int(progress * len(EXPLOSION_COLORS)), len(EXPLOSION_COLORS) - 1)
        arcade.draw_circle_filled(px, py, size, EXPLOSION_COLORS[cidx])

    # Central flash
    if progress < 0.3:
        flash_size = (1 - progress / 0.3) * 12
        arcade.draw_circle_filled(x, y, flash_size, (255, 255, 200))


# -----------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------

def _draw_top_bar(game):
    """Draw score, stage, and buttons."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT - TOP_BAR_HEIGHT // 2, WIDTH, TOP_BAR_HEIGHT),
        BG_COLOR,
    )
    arcade.draw_line(0, HEIGHT - TOP_BAR_HEIGHT, WIDTH, HEIGHT - TOP_BAR_HEIGHT,
                     LINE_COLOR, 1)

    game.txt_score.text = f"SCORE: {game.score}"
    game.txt_score.draw()
    game.txt_high_score.text = f"HI: {game.high_score}"
    game.txt_high_score.draw()

    game.txt_stage.text = f"STAGE {game.stage}"
    game.txt_stage.draw()

    hover_back = game.btn_back.contains(game.mouse_x, game.mouse_y)
    hover_help = game.btn_help.contains(game.mouse_x, game.mouse_y)
    game.btn_back.draw(hover=hover_back)
    game.btn_help.draw(hover=hover_help)


def _draw_bottom_bar(game):
    """Draw lives display."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, BOTTOM_BAR_HEIGHT // 2, WIDTH, BOTTOM_BAR_HEIGHT),
        BG_COLOR,
    )
    arcade.draw_line(0, BOTTOM_BAR_HEIGHT, WIDTH, BOTTOM_BAR_HEIGHT, LINE_COLOR, 1)

    game.txt_lives_label.draw()
    for i in range(game.lives):
        lx = 80 + i * 30
        ly = BOTTOM_BAR_HEIGHT // 2
        # Mini ship icon
        arcade.draw_triangle_filled(
            lx - 5, ly - 4, lx + 5, ly - 4, lx, ly + 6,
            SHIP_COLOR,
        )
        arcade.draw_triangle_filled(
            lx - 3, ly, lx - 3, ly - 5, lx - 8, ly - 5,
            SHIP_WING_COLOR,
        )
        arcade.draw_triangle_filled(
            lx + 3, ly, lx + 3, ly - 5, lx + 8, ly - 5,
            SHIP_WING_COLOR,
        )


# -----------------------------------------------------------------------
# Overlays
# -----------------------------------------------------------------------

def _draw_stage_intro(game):
    """Draw the stage intro overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_COLOR,
    )
    game.txt_stage_intro.text = f"STAGE {game.stage}"
    game.txt_stage_intro.draw()
    game.txt_ready.draw()


def _draw_capture_message(game):
    """Show 'FIGHTER CAPTURED' message."""
    game.txt_captured.draw()


def _draw_dual_message(game):
    """Show 'DUAL FIGHTER!' message."""
    game.txt_dual.draw()


def _draw_game_over(game):
    """Draw the game over overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_COLOR,
    )
    game.txt_game_over.draw()
    game.txt_final_score.text = f"Final Score: {game.score}  |  Stage: {game.stage}"
    game.txt_final_score.draw()
    game.txt_restart_hint.draw()
