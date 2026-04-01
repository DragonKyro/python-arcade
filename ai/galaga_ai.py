"""
Galaga AI — pure Python enemy behavior logic.
No arcade imports. Each AI class provides dive path generation and formation sway.
"""

import math
import random


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bezier_quadratic(p0, p1, p2, t):
    """Evaluate a quadratic Bezier curve at parameter t in [0,1]."""
    u = 1.0 - t
    x = u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0]
    y = u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]
    return x, y


def _bezier_cubic(p0, p1, p2, p3, t):
    """Evaluate a cubic Bezier curve at parameter t in [0,1]."""
    u = 1.0 - t
    x = (u ** 3 * p0[0] + 3 * u ** 2 * t * p1[0] +
         3 * u * t ** 2 * p2[0] + t ** 3 * p3[0])
    y = (u ** 3 * p0[1] + 3 * u ** 2 * t * p1[1] +
         3 * u * t ** 2 * p2[1] + t ** 3 * p3[1])
    return x, y


def generate_formation_sway(time, col, row, amplitude=3.0, frequency=0.8):
    """Return (dx, dy) offsets for gentle formation sway.

    Each column/row gets a slight phase offset so the formation ripples.
    """
    phase = col * 0.3 + row * 0.15
    dx = math.sin(time * frequency + phase) * amplitude
    dy = math.cos(time * frequency * 0.6 + phase) * amplitude * 0.3
    return dx, dy


# ---------------------------------------------------------------------------
# Dive path generators
# ---------------------------------------------------------------------------

def generate_bee_dive_path(start_x, start_y, player_x, screen_w, screen_h):
    """Return a list of cubic Bezier control-point tuples for a bee dive.

    Bee path: slight curve down toward the player, loops under the screen,
    then arcs back up to re-enter from the top.
    """
    # Pick a side bias based on position relative to player
    bias = 1 if start_x < player_x else -1
    mid_x = start_x + bias * random.uniform(40, 100)
    bottom_y = -40  # below screen

    # Segment 1: swoop down toward player area
    seg1 = (
        (start_x, start_y),
        (start_x + bias * 30, start_y - 80),
        (mid_x, start_y - 200),
        (player_x + bias * random.uniform(-30, 30), bottom_y),
    )

    # Segment 2: loop back up off-screen and return to formation altitude
    re_enter_x = random.uniform(100, screen_w - 100)
    seg2 = (
        (player_x + bias * 30, bottom_y),
        (player_x + bias * 120, bottom_y - 60),
        (re_enter_x + bias * 80, screen_h + 40),
        (re_enter_x, screen_h + 40),
    )

    return [seg1, seg2]


def generate_butterfly_dive_path(start_x, start_y, player_x, screen_w, screen_h):
    """Butterfly: aggressive S-curve swoops with wider lateral movement."""
    bias = 1 if random.random() > 0.5 else -1
    s_width = random.uniform(100, 180)

    # First S-curve leg
    seg1 = (
        (start_x, start_y),
        (start_x + bias * s_width, start_y - 60),
        (start_x - bias * s_width * 0.5, start_y - 180),
        (player_x + bias * random.uniform(-20, 60), start_y - 300),
    )

    # Second S-curve leg going lower
    low_y = -50
    seg2 = (
        (player_x + bias * 60, start_y - 300),
        (player_x - bias * s_width, start_y - 400),
        (player_x + bias * s_width * 0.7, low_y),
        (player_x, low_y),
    )

    # Return arc
    re_x = random.uniform(150, screen_w - 150)
    seg3 = (
        (player_x, low_y),
        (player_x - bias * 140, low_y - 80),
        (re_x + bias * 100, screen_h + 60),
        (re_x, screen_h + 60),
    )

    return [seg1, seg2, seg3]


def generate_boss_dive_path(start_x, start_y, player_x, screen_w, screen_h):
    """Boss Galaga: slow, deliberate dive — mostly straight down with a
    slight weave, pausing mid-screen for a tractor beam opportunity."""
    bias = 1 if start_x < player_x else -1
    mid_y = screen_h * 0.45  # tractor beam altitude

    # Slow descent to tractor beam position
    seg1 = (
        (start_x, start_y),
        (start_x + bias * 20, start_y - 40),
        (player_x + bias * 10, mid_y + 60),
        (player_x, mid_y),
    )

    # After tractor beam: continue dive down and loop back
    low_y = -50
    seg2 = (
        (player_x, mid_y),
        (player_x + bias * 60, mid_y - 100),
        (player_x - bias * 80, low_y + 40),
        (player_x - bias * 40, low_y),
    )

    # Return
    re_x = random.uniform(120, screen_w - 120)
    seg3 = (
        (player_x - bias * 40, low_y),
        (player_x - bias * 150, low_y - 80),
        (re_x - bias * 60, screen_h + 50),
        (re_x, screen_h + 50),
    )

    return [seg1, seg2, seg3]


# ---------------------------------------------------------------------------
# Entry path generators (enemies swooping onto screen at stage start)
# ---------------------------------------------------------------------------

def generate_entry_path(target_x, target_y, wave_group, index, screen_w, screen_h):
    """Generate a swooping entry path for an enemy entering the formation.

    wave_group: 0 = enters from top-right, 1 = top-left, 2 = bottom sides.
    index: position in the group (affects timing offset).
    Returns list of bezier segment tuples.
    """
    if wave_group == 0:
        # Enter from top-right, swoop left then settle
        sx = screen_w + 30
        sy = screen_h * 0.7
        seg = (
            (sx, sy),
            (screen_w * 0.7, screen_h + 20),
            (screen_w * 0.3, screen_h * 0.8),
            (target_x, target_y),
        )
    elif wave_group == 1:
        # Enter from top-left, swoop right then settle
        sx = -30
        sy = screen_h * 0.7
        seg = (
            (sx, sy),
            (screen_w * 0.3, screen_h + 20),
            (screen_w * 0.7, screen_h * 0.8),
            (target_x, target_y),
        )
    else:
        # Enter from bottom, loop up
        side = 1 if index % 2 == 0 else -1
        sx = screen_w / 2 + side * (screen_w * 0.4)
        sy = -30
        seg = (
            (sx, sy),
            (sx, screen_h * 0.3),
            (target_x + side * 60, screen_h * 0.7),
            (target_x, target_y),
        )

    return [seg]


# ---------------------------------------------------------------------------
# AI behavior classes
# ---------------------------------------------------------------------------

class BeeAI:
    """Simple dive pattern — slight curve toward player, loops back."""

    DIVE_SPEED = 1.0  # How fast we traverse the bezier (1.0 = base speed)

    @staticmethod
    def update_diving(enemy, player_x, dt, screen_w=800, screen_h=600):
        """Advance the bee along its dive path.

        enemy is a dict with keys: x, y, dive_path, dive_segment, dive_t, ...
        Returns True when the dive is complete.
        """
        if 'dive_path' not in enemy or enemy['dive_path'] is None:
            enemy['dive_path'] = generate_bee_dive_path(
                enemy['x'], enemy['y'], player_x, screen_w, screen_h)
            enemy['dive_segment'] = 0
            enemy['dive_t'] = 0.0

        speed = BeeAI.DIVE_SPEED * (1.0 + enemy.get('stage', 0) * 0.05)
        enemy['dive_t'] += dt * speed

        seg_idx = enemy['dive_segment']
        path = enemy['dive_path']

        if seg_idx >= len(path):
            return True  # dive complete

        t = min(enemy['dive_t'], 1.0)
        seg = path[seg_idx]
        x, y = _bezier_cubic(*seg, t)
        enemy['x'] = x
        enemy['y'] = y

        if enemy['dive_t'] >= 1.0:
            enemy['dive_segment'] += 1
            enemy['dive_t'] = 0.0
            if enemy['dive_segment'] >= len(path):
                return True

        # Bees don't shoot during dives (simple enemy)
        enemy['should_shoot'] = False
        return False


class ButterflyAI:
    """Aggressive S-curve swoops, may shoot during dive."""

    DIVE_SPEED = 1.2

    @staticmethod
    def update_diving(enemy, player_x, dt, screen_w=800, screen_h=600):
        if 'dive_path' not in enemy or enemy['dive_path'] is None:
            enemy['dive_path'] = generate_butterfly_dive_path(
                enemy['x'], enemy['y'], player_x, screen_w, screen_h)
            enemy['dive_segment'] = 0
            enemy['dive_t'] = 0.0
            enemy['shoot_cooldown'] = 0.0

        speed = ButterflyAI.DIVE_SPEED * (1.0 + enemy.get('stage', 0) * 0.05)
        enemy['dive_t'] += dt * speed

        seg_idx = enemy['dive_segment']
        path = enemy['dive_path']

        if seg_idx >= len(path):
            return True

        t = min(enemy['dive_t'], 1.0)
        seg = path[seg_idx]
        x, y = _bezier_cubic(*seg, t)
        enemy['x'] = x
        enemy['y'] = y

        if enemy['dive_t'] >= 1.0:
            enemy['dive_segment'] += 1
            enemy['dive_t'] = 0.0
            if enemy['dive_segment'] >= len(path):
                return True

        # Butterflies shoot during the first dive segment
        enemy['shoot_cooldown'] = enemy.get('shoot_cooldown', 0) - dt
        if seg_idx == 0 and t > 0.4 and enemy['shoot_cooldown'] <= 0:
            enemy['should_shoot'] = True
            enemy['shoot_cooldown'] = random.uniform(0.5, 1.0)
        else:
            enemy['should_shoot'] = False

        return False


class BossGalagaAI:
    """Slow dive with tractor beam attack. Takes 2 hits. May capture player."""

    DIVE_SPEED = 0.7
    TRACTOR_BEAM_DURATION = 2.0  # seconds the beam stays active

    @staticmethod
    def update_diving(enemy, player_x, dt, screen_w=800, screen_h=600):
        if 'dive_path' not in enemy or enemy['dive_path'] is None:
            enemy['dive_path'] = generate_boss_dive_path(
                enemy['x'], enemy['y'], player_x, screen_w, screen_h)
            enemy['dive_segment'] = 0
            enemy['dive_t'] = 0.0
            enemy['tractor_beam_active'] = False
            enemy['tractor_beam_timer'] = 0.0
            enemy['tractor_beam_used'] = False
            enemy['shoot_cooldown'] = 0.0

        # If tractor beam is active, pause dive and run beam timer
        if enemy.get('tractor_beam_active', False):
            enemy['tractor_beam_timer'] -= dt
            if enemy['tractor_beam_timer'] <= 0:
                enemy['tractor_beam_active'] = False
            enemy['should_shoot'] = False
            return False

        speed = BossGalagaAI.DIVE_SPEED * (1.0 + enemy.get('stage', 0) * 0.03)
        enemy['dive_t'] += dt * speed

        seg_idx = enemy['dive_segment']
        path = enemy['dive_path']

        if seg_idx >= len(path):
            return True

        t = min(enemy['dive_t'], 1.0)
        seg = path[seg_idx]
        x, y = _bezier_cubic(*seg, t)
        enemy['x'] = x
        enemy['y'] = y

        # Activate tractor beam at end of first segment (hovering over player)
        if seg_idx == 0 and t >= 0.95 and not enemy.get('tractor_beam_used', False):
            # Only activate if roughly above the player
            if abs(enemy['x'] - player_x) < 60:
                enemy['tractor_beam_active'] = True
                enemy['tractor_beam_timer'] = BossGalagaAI.TRACTOR_BEAM_DURATION
                enemy['tractor_beam_used'] = True

        if enemy['dive_t'] >= 1.0:
            enemy['dive_segment'] += 1
            enemy['dive_t'] = 0.0
            if enemy['dive_segment'] >= len(path):
                return True

        # Boss shoots occasionally during dive
        enemy['shoot_cooldown'] = enemy.get('shoot_cooldown', 0) - dt
        if seg_idx == 0 and t > 0.3 and enemy['shoot_cooldown'] <= 0:
            enemy['should_shoot'] = True
            enemy['shoot_cooldown'] = random.uniform(0.8, 1.5)
        else:
            enemy['should_shoot'] = False

        return False


# ---------------------------------------------------------------------------
# Dive selection logic
# ---------------------------------------------------------------------------

def pick_divers(enemies, max_divers, stage):
    """Choose which formation enemies should start diving.

    Returns a list of enemy indices. Higher stages = more simultaneous divers.
    """
    candidates = [
        i for i, e in enumerate(enemies)
        if e['state'] == 'formation' and e.get('hp', 1) > 0
    ]
    if not candidates:
        return []

    # More divers at higher stages
    count = min(len(candidates), max_divers + stage // 3)

    # Weight bosses and butterflies to dive more at higher stages
    weights = []
    for i in candidates:
        etype = enemies[i]['type']
        if etype == 'boss':
            weights.append(1.0 + stage * 0.2)
        elif etype == 'butterfly':
            weights.append(1.5 + stage * 0.1)
        else:
            weights.append(2.0)

    chosen = []
    cands = list(candidates)
    ws = list(weights)
    for _ in range(count):
        if not cands:
            break
        total = sum(ws)
        r = random.uniform(0, total)
        cumulative = 0
        for j, (idx, w) in enumerate(zip(cands, ws)):
            cumulative += w
            if r <= cumulative:
                chosen.append(idx)
                cands.pop(j)
                ws.pop(j)
                break

    return chosen


def get_ai_for_type(enemy_type):
    """Return the AI class for a given enemy type string."""
    if enemy_type == 'bee':
        return BeeAI
    elif enemy_type == 'butterfly':
        return ButterflyAI
    elif enemy_type == 'boss':
        return BossGalagaAI
    return BeeAI
