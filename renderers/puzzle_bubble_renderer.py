"""
Renderer for the Puzzle Bubble (Bust-a-Move) game.
All drawing code extracted from games/puzzle_bubble.py.
"""

import arcade
import math

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
PLAY_AREA_LEFT = 100
PLAY_AREA_RIGHT = 700
PLAY_AREA_TOP = HEIGHT - TOP_BAR_HEIGHT - 10
PLAY_AREA_BOTTOM = 60

# Grid
BUBBLE_RADIUS = 18
BUBBLE_DIAMETER = BUBBLE_RADIUS * 2
GRID_COLS = 12
GRID_ROWS = 15
GRID_ORIGIN_X = PLAY_AREA_LEFT + BUBBLE_RADIUS
GRID_ORIGIN_Y = PLAY_AREA_TOP - BUBBLE_RADIUS

# Shooter
SHOOTER_X = WIDTH // 2
SHOOTER_Y = PLAY_AREA_BOTTOM + 20

# Danger line
DANGER_LINE_Y = PLAY_AREA_BOTTOM + 80

# Colors
BG_COLOR = (20, 20, 35)
GRID_DOT_COLOR = (50, 50, 70, 40)
LINE_COLOR = (205, 214, 244)
OVERLAY_COLOR = (20, 20, 35, 200)
STATUS_TEXT_COLOR = (205, 214, 244)
SCORE_COLOR = (249, 226, 175)
DANGER_COLOR = (243, 139, 168, 100)
SHOOTER_COLOR = (160, 170, 200)
SHOOTER_OUTLINE = (205, 214, 244)
AIM_DOT_COLOR = (205, 214, 244, 120)

# Bubble colors (must match game module)
BUBBLE_COLORS = {
    "red": (243, 80, 80),
    "blue": (80, 140, 250),
    "green": (80, 220, 120),
    "yellow": (250, 220, 80),
    "purple": (180, 100, 240),
    "orange": (250, 160, 60),
}

# Shine highlight colors (lighter version for the specular highlight)
BUBBLE_SHINE = {
    "red": (255, 180, 180, 100),
    "blue": (180, 210, 255, 100),
    "green": (180, 255, 200, 100),
    "yellow": (255, 245, 180, 100),
    "purple": (230, 200, 255, 100),
    "orange": (255, 220, 180, 100),
}


def grid_to_screen(col, row):
    """Convert grid (col, row) to screen center (x, y)."""
    offset = BUBBLE_RADIUS if row % 2 == 1 else 0
    x = GRID_ORIGIN_X + col * BUBBLE_DIAMETER + offset
    y = GRID_ORIGIN_Y - row * (BUBBLE_DIAMETER * 0.866)
    return x, y


def _draw_bubble(x, y, color_name):
    """Draw a single bubble with shine effect."""
    color = BUBBLE_COLORS.get(color_name, (200, 200, 200))
    shine = BUBBLE_SHINE.get(color_name, (255, 255, 255, 100))

    # Main filled circle
    arcade.draw_circle_filled(x, y, BUBBLE_RADIUS - 1, color)

    # Outline (slightly darker)
    outline = tuple(max(v - 40, 0) for v in color[:3])
    arcade.draw_circle_outline(x, y, BUBBLE_RADIUS - 1, outline, 1.5)

    # Shine highlight (small circle offset up-left)
    arcade.draw_circle_filled(x - 5, y + 5, BUBBLE_RADIUS * 0.35, shine)


def _draw_bubble_raw(x, y, color_tuple):
    """Draw a bubble given a raw RGB color tuple (for preview/shooter)."""
    arcade.draw_circle_filled(x, y, BUBBLE_RADIUS - 1, color_tuple)
    outline = tuple(max(v - 40, 0) for v in color_tuple[:3])
    arcade.draw_circle_outline(x, y, BUBBLE_RADIUS - 1, outline, 1.5)
    arcade.draw_circle_filled(x - 5, y + 5, BUBBLE_RADIUS * 0.35, (255, 255, 255, 90))


def draw(game):
    """Render the entire Puzzle Bubble game state."""
    _draw_play_area_bg()
    _draw_grid_dots(game)
    _draw_danger_line()
    _draw_grid_bubbles(game)
    _draw_aim_line(game)
    _draw_shooter(game)

    if game.flying:
        _draw_flying_bubble(game)

    _draw_next_preview(game)
    _draw_side_panel(game)
    _draw_top_bar(game)

    if game.game_over:
        _draw_game_over(game)
    elif game.level_clear:
        _draw_level_clear(game)


def _draw_play_area_bg():
    """Draw the play area background."""
    cx = (PLAY_AREA_LEFT + PLAY_AREA_RIGHT) / 2
    cy = (PLAY_AREA_BOTTOM + PLAY_AREA_TOP) / 2
    w = PLAY_AREA_RIGHT - PLAY_AREA_LEFT
    h = PLAY_AREA_TOP - PLAY_AREA_BOTTOM
    arcade.draw_rect_filled(
        arcade.XYWH(cx, cy, w, h),
        (15, 15, 28),
    )
    arcade.draw_rect_outline(
        arcade.XYWH(cx, cy, w, h),
        (50, 50, 70), 2,
    )


def _draw_grid_dots(game):
    """Draw subtle dots at grid positions to show the hex grid."""
    for row in range(GRID_ROWS):
        max_cols = GRID_COLS - (1 if row % 2 == 1 else 0)
        for col in range(max_cols):
            x, y = grid_to_screen(col, row)
            if PLAY_AREA_BOTTOM < y < PLAY_AREA_TOP:
                arcade.draw_circle_filled(x, y, 1.5, GRID_DOT_COLOR)


def _draw_danger_line():
    """Draw the danger line indicator."""
    arcade.draw_line(
        PLAY_AREA_LEFT + 5, DANGER_LINE_Y,
        PLAY_AREA_RIGHT - 5, DANGER_LINE_Y,
        DANGER_COLOR, 2,
    )
    # Draw small warning triangles along the line
    for tx in range(int(PLAY_AREA_LEFT) + 30, int(PLAY_AREA_RIGHT) - 20, 60):
        arcade.draw_triangle_filled(
            tx - 5, DANGER_LINE_Y + 2,
            tx + 5, DANGER_LINE_Y + 2,
            tx, DANGER_LINE_Y + 10,
            DANGER_COLOR,
        )


def _draw_grid_bubbles(game):
    """Draw all bubbles currently on the grid."""
    for (col, row), color_name in game.grid.items():
        x, y = grid_to_screen(col, row)
        _draw_bubble(x, y, color_name)


def _draw_shooter(game):
    """Draw the shooter at the bottom center."""
    x = SHOOTER_X
    y = SHOOTER_Y

    # Base platform (rectangle)
    arcade.draw_rect_filled(
        arcade.XYWH(x, y - 12, 60, 12),
        SHOOTER_COLOR,
    )
    arcade.draw_rect_outline(
        arcade.XYWH(x, y - 12, 60, 12),
        SHOOTER_OUTLINE, 1.5,
    )

    # Cannon barrel (rotatable triangle/arrow)
    barrel_len = 35
    tip_x = x + math.cos(game.aim_angle) * barrel_len
    tip_y = y + math.sin(game.aim_angle) * barrel_len

    # Perpendicular direction for barrel width
    perp_angle = game.aim_angle + math.pi / 2
    half_w = 8
    base_x1 = x + math.cos(perp_angle) * half_w
    base_y1 = y + math.sin(perp_angle) * half_w
    base_x2 = x - math.cos(perp_angle) * half_w
    base_y2 = y - math.sin(perp_angle) * half_w

    arcade.draw_triangle_filled(
        base_x1, base_y1,
        base_x2, base_y2,
        tip_x, tip_y,
        SHOOTER_COLOR,
    )
    arcade.draw_triangle_outline(
        base_x1, base_y1,
        base_x2, base_y2,
        tip_x, tip_y,
        SHOOTER_OUTLINE, 1.5,
    )

    # Draw the current bubble at the shooter position
    color_name = game.current_bubble
    _draw_bubble(x, y, color_name)


def _draw_aim_line(game):
    """Draw a dotted aim line showing trajectory."""
    if game.flying or game.game_over or game.level_clear:
        return

    points = game.get_aim_trajectory()
    if len(points) < 2:
        return

    # Draw as dotted line (every other segment)
    dot_spacing = 12
    total_drawn = 0
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        seg_len = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        if seg_len < 1:
            continue
        dx = (x2 - x1) / seg_len
        dy = (y2 - y1) / seg_len
        dist = 0
        while dist < seg_len:
            px = x1 + dx * dist
            py = y1 + dy * dist
            # Skip dots near the shooter
            if total_drawn + dist > 30:
                # Alternate: draw dot every other spacing
                idx = int((total_drawn + dist) / dot_spacing)
                if idx % 2 == 0:
                    arcade.draw_circle_filled(px, py, 2, AIM_DOT_COLOR)
            dist += 3
        total_drawn += seg_len


def _draw_flying_bubble(game):
    """Draw the currently flying bubble."""
    _draw_bubble(game.fly_x, game.fly_y, game.fly_color)


def _draw_next_preview(game):
    """Draw the next bubble preview on the side panel."""
    nx = PLAY_AREA_RIGHT + 55
    ny = PLAY_AREA_TOP - 170
    _draw_bubble(nx, ny, game.next_bubble)


def _draw_side_panel(game):
    """Draw score, level, and controls on the side."""
    game.txt_score_label.draw()
    game.txt_score_value.text = str(game.score)
    game.txt_score_value.draw()

    game.txt_level_label.draw()
    game.txt_level_value.text = str(game.level)
    game.txt_level_value.draw()

    game.txt_next_label.draw()

    for t in game.txt_controls:
        t.draw()


def _draw_top_bar(game):
    """Draw buttons and title on the top bar."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT - TOP_BAR_HEIGHT / 2, WIDTH, TOP_BAR_HEIGHT),
        (20, 20, 35, 220),
    )

    game.btn_back.draw(game.btn_back.contains(game.mouse_x, game.mouse_y))
    game.btn_new.draw(game.btn_new.contains(game.mouse_x, game.mouse_y))
    game.btn_help.draw(game.btn_help.contains(game.mouse_x, game.mouse_y))


def _draw_game_over(game):
    """Draw game over overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        OVERLAY_COLOR,
    )
    game.txt_game_over.draw()
    game.txt_game_over_score.text = f"Score: {game.score}"
    game.txt_game_over_score.draw()
    game.txt_game_over_hint.draw()


def _draw_level_clear(game):
    """Draw level clear overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        (20, 20, 35, 180),
    )
    game.txt_level_clear.draw()
    game.txt_level_clear_hint.draw()
