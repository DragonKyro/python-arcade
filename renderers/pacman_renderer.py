"""
Renderer for the Pac-Man game.
All drawing code -- NO imports from games.*.
"""

import arcade
import math

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout constants (must match games/pacman.py)
TILE_SIZE = 18
MAZE_COLS = 28
MAZE_ROWS = 31
MAZE_OFFSET_X = (WIDTH - MAZE_COLS * TILE_SIZE) // 2
MAZE_OFFSET_Y = 30
TOP_BAR_HEIGHT = 50

# Colors
BG_COLOR = (0, 0, 0)
WALL_COLOR = (33, 33, 222)
WALL_OUTLINE = (33, 33, 255)
DOT_COLOR = (255, 255, 255)
PELLET_COLOR = (255, 255, 255)
PACMAN_COLOR = (255, 255, 0)
GHOST_FRIGHTENED_COLOR = (33, 33, 255)
GHOST_FRIGHTENED_END_COLOR = (255, 255, 255)
GHOST_EATEN_EYE_COLOR = (255, 255, 255)
GHOST_EYE_WHITE = (255, 255, 255)
GHOST_EYE_BLUE = (33, 33, 222)
PEN_GATE_COLOR = (255, 184, 174)
FRUIT_COLOR = (255, 0, 0)
FRUIT_STEM_COLOR = (0, 180, 0)
LINE_COLOR = (205, 214, 244)
SCORE_COLOR = (255, 255, 255)
OVERLAY_COLOR = (0, 0, 0, 180)

# Ghost body colors
GHOST_COLORS = {
    "blinky": (255, 0, 0),
    "pinky": (255, 184, 255),
    "inky": (0, 255, 255),
    "clyde": (255, 184, 82),
}


def _tile_to_pixel(col, row):
    """Convert tile coords to pixel center."""
    px = MAZE_OFFSET_X + col * TILE_SIZE + TILE_SIZE / 2
    py = MAZE_OFFSET_Y + row * TILE_SIZE + TILE_SIZE / 2
    return px, py


def draw(game):
    """Render the entire Pac-Man game."""
    _draw_maze(game)
    _draw_dots(game)
    _draw_fruit(game)
    _draw_ghosts(game)
    _draw_pacman(game)
    _draw_score_popup(game)
    _draw_top_bar(game)
    _draw_bottom_bar(game)

    if game.ready_timer > 0 and not game.level_clear:
        game.txt_ready.draw()
    if game.level_clear:
        _draw_level_clear_overlay(game)
    if game.game_over:
        _draw_game_over_overlay(game)


# ------------------------------------------------------------------
# Maze
# ------------------------------------------------------------------

def _draw_maze(game):
    """Draw maze walls from the raw grid."""
    raw = game.raw_maze
    for row_idx in range(len(raw)):
        for col_idx in range(len(raw[row_idx])):
            val = raw[row_idx][col_idx]
            px, py = _tile_to_pixel(col_idx, row_idx)

            if val == 1:
                # Wall tile -- draw filled with outline
                arcade.draw_rect_filled(
                    arcade.XYWH(px, py, TILE_SIZE, TILE_SIZE),
                    WALL_COLOR,
                )
                # Draw edges where adjacent to non-wall to create the outline effect
                _draw_wall_edges(raw, col_idx, row_idx, px, py)

            elif val == 4:
                # Ghost pen wall
                arcade.draw_rect_filled(
                    arcade.XYWH(px, py, TILE_SIZE, TILE_SIZE),
                    WALL_COLOR,
                )

            elif val == 6:
                # Ghost pen gate
                arcade.draw_rect_filled(
                    arcade.XYWH(px, py, TILE_SIZE, TILE_SIZE / 3),
                    PEN_GATE_COLOR,
                )


def _draw_wall_edges(raw, col, row, px, py):
    """Draw bright border lines on sides of wall tiles adjacent to paths."""
    rows = len(raw)
    cols = len(raw[0])
    half = TILE_SIZE / 2

    neighbors = [
        (col, row + 1, px - half, py + half, px + half, py + half),  # top
        (col, row - 1, px - half, py - half, px + half, py - half),  # bottom
        (col - 1, row, px - half, py - half, px - half, py + half),  # left
        (col + 1, row, px + half, py - half, px + half, py + half),  # right
    ]

    for nc, nr, x1, y1, x2, y2 in neighbors:
        if 0 <= nr < rows and 0 <= nc < cols:
            if raw[nr][nc] != 1 and raw[nr][nc] != 4:
                arcade.draw_line(x1, y1, x2, y2, WALL_OUTLINE, 2)
        elif nr < 0 or nr >= rows or nc < 0 or nc >= cols:
            arcade.draw_line(x1, y1, x2, y2, WALL_OUTLINE, 2)


# ------------------------------------------------------------------
# Dots and pellets
# ------------------------------------------------------------------

def _draw_dots(game):
    """Draw remaining dots and power pellets."""
    for (col, row) in game.dots:
        px, py = _tile_to_pixel(col, row)
        arcade.draw_circle_filled(px, py, 2, DOT_COLOR)

    # Power pellets flash
    show_pellet = math.sin(game.pellet_flash_timer * 6) > -0.3
    if show_pellet:
        for (col, row) in game.pellets:
            px, py = _tile_to_pixel(col, row)
            arcade.draw_circle_filled(px, py, 5, PELLET_COLOR)


# ------------------------------------------------------------------
# Pac-Man
# ------------------------------------------------------------------

def _draw_pacman(game):
    """Draw Pac-Man as a yellow circle with animated mouth."""
    if game.game_over:
        return

    px = MAZE_OFFSET_X + game.pac_col * TILE_SIZE + TILE_SIZE / 2
    py = MAZE_OFFSET_Y + game.pac_row * TILE_SIZE + TILE_SIZE / 2
    radius = TILE_SIZE * 0.55

    # Mouth angle: 0 = closed, 1 = fully open (45 degrees)
    mouth_half_angle = game.pac_mouth_angle * 45.0

    # Direction to angle mapping
    dir_angles = {
        (1, 0): 0,
        (-1, 0): 180,
        (0, 1): 90,
        (0, -1): 270,
    }
    base_angle = dir_angles.get(game.pac_dir, 0)

    if mouth_half_angle < 1:
        # Mouth nearly closed - just draw circle
        arcade.draw_circle_filled(px, py, radius, PACMAN_COLOR)
    else:
        # Draw pac-man as a filled arc using polygon approximation
        start_angle = base_angle + mouth_half_angle
        end_angle = base_angle + 360 - mouth_half_angle
        points = [(px, py)]  # center point for the "pie slice"
        num_segments = 24
        for i in range(num_segments + 1):
            angle = math.radians(start_angle + (end_angle - start_angle) * i / num_segments)
            x = px + radius * math.cos(angle)
            y = py + radius * math.sin(angle)
            points.append((x, y))

        if len(points) >= 3:
            # Draw as triangle fan from center
            for i in range(1, len(points) - 1):
                arcade.draw_triangle_filled(
                    points[0][0], points[0][1],
                    points[i][0], points[i][1],
                    points[i + 1][0], points[i + 1][1],
                    PACMAN_COLOR,
                )


# ------------------------------------------------------------------
# Ghosts
# ------------------------------------------------------------------

def _draw_ghosts(game):
    """Draw all four ghosts."""
    for ghost in game.ghosts:
        _draw_single_ghost(game, ghost)


def _draw_single_ghost(game, ghost):
    """Draw one ghost with body, wavy bottom, and eyes."""
    px = MAZE_OFFSET_X + ghost.col * TILE_SIZE + TILE_SIZE / 2
    py = MAZE_OFFSET_Y + ghost.row * TILE_SIZE + TILE_SIZE / 2
    r = TILE_SIZE * 0.55
    half = r

    if ghost.eaten:
        # Just draw eyes heading back to pen
        _draw_ghost_eyes(px, py, r, ghost.direction, GHOST_EYE_WHITE, GHOST_EYE_BLUE)
        return

    # Determine body color
    if ghost.mode == "frightened":
        # Flash near end
        if game.frightened_timer < 2.0:
            flash = math.sin(game.frightened_timer * 10) > 0
            body_color = GHOST_FRIGHTENED_END_COLOR if flash else GHOST_FRIGHTENED_COLOR
        else:
            body_color = GHOST_FRIGHTENED_COLOR
    else:
        body_color = GHOST_COLORS.get(ghost.name, (255, 0, 0))

    # Ghost body: rounded top (semicircle) + rectangle + wavy bottom
    # Top semicircle
    num_seg = 12
    for i in range(num_seg):
        a1 = math.radians(180 * i / num_seg)
        a2 = math.radians(180 * (i + 1) / num_seg)
        x1 = px + half * math.cos(a1)
        y1 = py + half * math.sin(a1)
        x2 = px + half * math.cos(a2)
        y2 = py + half * math.sin(a2)
        arcade.draw_triangle_filled(px, py, x1, y1, x2, y2, body_color)

    # Rectangle body
    arcade.draw_rect_filled(
        arcade.XYWH(px, py - half / 2, half * 2, half),
        body_color,
    )

    # Wavy bottom edge (3 bumps)
    bottom_y = py - half
    wave_w = (half * 2) / 3
    for i in range(3):
        cx = px - half + wave_w * i + wave_w / 2
        arcade.draw_triangle_filled(
            cx - wave_w / 2, bottom_y,
            cx, bottom_y - wave_w * 0.4,
            cx + wave_w / 2, bottom_y,
            body_color,
        )

    # Eyes
    if ghost.mode == "frightened":
        _draw_frightened_face(px, py, r)
    else:
        _draw_ghost_eyes(px, py, r, ghost.direction, GHOST_EYE_WHITE, GHOST_EYE_BLUE)


def _draw_ghost_eyes(px, py, r, direction, white_color, pupil_color):
    """Draw two eyes looking in the ghost's direction."""
    eye_spacing = r * 0.5
    eye_r = r * 0.3
    pupil_r = eye_r * 0.55
    eye_y = py + r * 0.15

    # Pupil offset based on direction
    dir_offsets = {
        (1, 0): (pupil_r * 0.6, 0),
        (-1, 0): (-pupil_r * 0.6, 0),
        (0, 1): (0, pupil_r * 0.6),
        (0, -1): (0, -pupil_r * 0.6),
    }
    pdx, pdy = dir_offsets.get(direction, (0, 0))

    for side in (-1, 1):
        ex = px + side * eye_spacing
        # White of eye
        arcade.draw_circle_filled(ex, eye_y, eye_r, white_color)
        # Pupil
        arcade.draw_circle_filled(ex + pdx, eye_y + pdy, pupil_r, pupil_color)


def _draw_frightened_face(px, py, r):
    """Frightened ghost: small squiggly mouth and simple dot eyes."""
    eye_y = py + r * 0.15
    eye_spacing = r * 0.4
    # Dot eyes
    for side in (-1, 1):
        arcade.draw_circle_filled(px + side * eye_spacing, eye_y, 2, (255, 255, 255))

    # Wavy mouth
    mouth_y = py - r * 0.2
    mouth_w = r * 0.8
    seg = 4
    seg_w = mouth_w * 2 / seg
    for i in range(seg):
        x1 = px - mouth_w + i * seg_w
        x2 = x1 + seg_w
        mid_y = mouth_y + (3 if i % 2 == 0 else -3)
        arcade.draw_line(x1, mouth_y, (x1 + x2) / 2, mid_y, (255, 255, 255), 1)
        arcade.draw_line((x1 + x2) / 2, mid_y, x2, mouth_y, (255, 255, 255), 1)


# ------------------------------------------------------------------
# Fruit
# ------------------------------------------------------------------

def _draw_fruit(game):
    """Draw fruit bonus item (cherry)."""
    if not game.fruit_active:
        return
    fc, fr = 13, 14  # FRUIT_POS from game
    px, py = _tile_to_pixel(fc, fr)
    # Cherry: two red circles + green stem
    arcade.draw_circle_filled(px - 3, py - 2, 4, FRUIT_COLOR)
    arcade.draw_circle_filled(px + 3, py - 2, 4, FRUIT_COLOR)
    arcade.draw_line(px - 2, py + 1, px, py + 6, FRUIT_STEM_COLOR, 2)
    arcade.draw_line(px + 2, py + 1, px, py + 6, FRUIT_STEM_COLOR, 2)


# ------------------------------------------------------------------
# Score popup
# ------------------------------------------------------------------

def _draw_score_popup(game):
    """Draw floating score popup when ghost/fruit eaten."""
    if game.score_popup_timer > 0:
        game.txt_score_popup.text = str(game.score_popup_value)
        game.txt_score_popup.x = game.score_popup_x
        game.txt_score_popup.y = game.score_popup_y
        game.txt_score_popup.draw()


# ------------------------------------------------------------------
# UI bars
# ------------------------------------------------------------------

def _draw_top_bar(game):
    """Draw top bar with score, high score, and buttons."""
    # Background
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT - TOP_BAR_HEIGHT / 2, WIDTH, TOP_BAR_HEIGHT),
        BG_COLOR,
    )
    arcade.draw_line(0, HEIGHT - TOP_BAR_HEIGHT, WIDTH, HEIGHT - TOP_BAR_HEIGHT, LINE_COLOR, 1)

    # Buttons
    game.btn_back.draw(game.btn_back.contains(game.mouse_x, game.mouse_y))
    game.btn_help.draw(game.btn_help.contains(game.mouse_x, game.mouse_y))
    game.btn_new.draw(game.btn_new.contains(game.mouse_x, game.mouse_y))

    # Score
    game.txt_score.text = f"Score: {game.score}"
    game.txt_score.draw()

    game.txt_high_score.text = f"High: {game.high_score}"
    game.txt_high_score.draw()


def _draw_bottom_bar(game):
    """Draw bottom bar with lives and level indicator."""
    # Background
    bar_h = MAZE_OFFSET_Y
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, bar_h / 2, WIDTH, bar_h),
        BG_COLOR,
    )

    # Lives as small Pac-Man icons
    game.txt_lives_label.draw()
    for i in range(game.lives):
        lx = 65 + i * 22
        ly = 12
        r = 7
        # Small pac-man icon (mouth open to the right)
        points = [(lx, ly)]
        for seg in range(20):
            angle = math.radians(30 + (300) * seg / 19)
            points.append((lx + r * math.cos(angle), ly + r * math.sin(angle)))
        if len(points) >= 3:
            for j in range(1, len(points) - 1):
                arcade.draw_triangle_filled(
                    points[0][0], points[0][1],
                    points[j][0], points[j][1],
                    points[j + 1][0], points[j + 1][1],
                    PACMAN_COLOR,
                )

    # Level
    game.txt_level_label.text = f"Level {game.level}"
    game.txt_level_label.draw()


# ------------------------------------------------------------------
# Overlays
# ------------------------------------------------------------------

def _draw_game_over_overlay(game):
    """Game over overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        OVERLAY_COLOR,
    )
    game.txt_game_over.draw()
    game.txt_restart_hint.draw()


def _draw_level_clear_overlay(game):
    """Level clear overlay with flashing maze."""
    # Flash the maze walls
    if game.ready_timer > -1.5:
        game.txt_level_clear.draw()
