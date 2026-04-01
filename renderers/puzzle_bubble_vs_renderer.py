"""
Renderer for the Puzzle Bubble VS mode.
All drawing code -- no imports from games.*.
"""

import arcade
import math

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
BOARD_WIDTH = 350
BOARD_GAP = 20
BOARD_LEFT_X = (WIDTH / 2 - BOARD_GAP / 2 - BOARD_WIDTH)
BOARD_RIGHT_X = (WIDTH / 2 + BOARD_GAP / 2)
BOARD_TOP = HEIGHT - TOP_BAR_HEIGHT - 10
BOARD_BOTTOM = 50

# Grid
BUBBLE_RADIUS = 12
BUBBLE_DIAMETER = BUBBLE_RADIUS * 2
GRID_COLS = 8
GRID_ROWS = 18

# Shooter
SHOOTER_Y_OFFSET = 30

# Danger line
DANGER_LINE_OFFSET = 70

# Colors
BG_COLOR = (20, 20, 35)
BOARD_BG_COLOR = (15, 15, 28)
BOARD_OUTLINE_COLOR = (50, 50, 70)
LINE_COLOR = (205, 214, 244)
OVERLAY_COLOR = (20, 20, 35, 200)
DANGER_COLOR = (243, 139, 168, 100)
SHOOTER_COLOR = (160, 170, 200)
SHOOTER_OUTLINE = (205, 214, 244)
AIM_DOT_COLOR = (205, 214, 244, 120)
GRID_DOT_COLOR = (50, 50, 70, 40)
VS_COLOR = (243, 139, 168)
SCORE_COLOR = (249, 226, 175)
STATUS_TEXT_COLOR = (205, 214, 244)
JUNK_WARN_COLOR = (243, 139, 168)

# Bubble colors (must match game module)
BUBBLE_COLORS = {
    "red": (243, 80, 80),
    "blue": (80, 140, 250),
    "green": (80, 220, 120),
    "yellow": (250, 220, 80),
    "purple": (180, 100, 240),
    "orange": (250, 160, 60),
    "gray": (140, 140, 150),
}

BUBBLE_SHINE = {
    "red": (255, 180, 180, 100),
    "blue": (180, 210, 255, 100),
    "green": (180, 255, 200, 100),
    "yellow": (255, 245, 180, 100),
    "purple": (230, 200, 255, 100),
    "orange": (255, 220, 180, 100),
    "gray": (200, 200, 210, 80),
}


def grid_to_screen(col, row, board_left):
    """Convert grid (col, row) to screen center (x, y) for a board."""
    origin_x = board_left + BUBBLE_RADIUS + 10
    origin_y = BOARD_TOP - BUBBLE_RADIUS
    offset = BUBBLE_RADIUS if row % 2 == 1 else 0
    x = origin_x + col * BUBBLE_DIAMETER + offset
    y = origin_y - row * (BUBBLE_DIAMETER * 0.866)
    return x, y


def shooter_pos(board_left):
    """Return (x, y) of the shooter for a board."""
    x = board_left + BOARD_WIDTH / 2
    y = BOARD_BOTTOM + SHOOTER_Y_OFFSET
    return x, y


def danger_line_y():
    """Return the y position of the danger line."""
    return BOARD_BOTTOM + DANGER_LINE_OFFSET


# ------------------------------------------------------------------
# Bubble drawing
# ------------------------------------------------------------------

def _draw_bubble(x, y, color_name):
    """Draw a single bubble with shine effect."""
    color = BUBBLE_COLORS.get(color_name, (200, 200, 200))
    shine = BUBBLE_SHINE.get(color_name, (255, 255, 255, 80))

    arcade.draw_circle_filled(x, y, BUBBLE_RADIUS - 1, color)
    outline = tuple(max(v - 40, 0) for v in color[:3])
    arcade.draw_circle_outline(x, y, BUBBLE_RADIUS - 1, outline, 1.5)
    arcade.draw_circle_filled(x - 3, y + 3, BUBBLE_RADIUS * 0.3, shine)


# ------------------------------------------------------------------
# Main draw entry point
# ------------------------------------------------------------------

def draw(game):
    """Render the entire Puzzle Bubble VS game state."""
    if game.state == "select":
        _draw_select_screen(game)
        _draw_top_bar(game)
        return

    _draw_board_bg(BOARD_LEFT_X)
    _draw_board_bg(BOARD_RIGHT_X)

    if game.player_board:
        _draw_board(game, game.player_board, is_player=True)
    if game.ai_board:
        _draw_board(game, game.ai_board, is_player=False)

    _draw_center_vs(game)
    _draw_scores(game)
    _draw_top_bar(game)

    if game.state == "gameover":
        _draw_game_over(game)


# ------------------------------------------------------------------
# Selection screen
# ------------------------------------------------------------------

def _draw_select_screen(game):
    """Draw the difficulty selection screen."""
    game.txt_title.draw()
    game.txt_select.draw()
    for btn in game.difficulty_buttons:
        btn.draw(btn.contains(game.mouse_x, game.mouse_y))


# ------------------------------------------------------------------
# Board drawing
# ------------------------------------------------------------------

def _draw_board_bg(board_left):
    """Draw background rectangle for one board."""
    cx = board_left + BOARD_WIDTH / 2
    cy = (BOARD_BOTTOM + BOARD_TOP) / 2
    w = BOARD_WIDTH
    h = BOARD_TOP - BOARD_BOTTOM
    arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), BOARD_BG_COLOR)
    arcade.draw_rect_outline(arcade.XYWH(cx, cy, w, h), BOARD_OUTLINE_COLOR, 2)


def _draw_board(game, board, is_player):
    """Draw all elements for one board."""
    bl = board.board_left

    # Danger line
    dl = danger_line_y()
    arcade.draw_line(bl + 5, dl, bl + BOARD_WIDTH - 5, dl, DANGER_COLOR, 2)

    # Grid dots
    for row in range(GRID_ROWS):
        max_cols = GRID_COLS - (1 if row % 2 == 1 else 0)
        for col in range(max_cols):
            x, y = grid_to_screen(col, row, bl)
            if BOARD_BOTTOM < y < BOARD_TOP:
                arcade.draw_circle_filled(x, y, 1, GRID_DOT_COLOR)

    # Grid bubbles
    for (col, row), color_name in board.grid.items():
        x, y = grid_to_screen(col, row, bl)
        _draw_bubble(x, y, color_name)

    # Aim line (player only -- AI aim is hidden or briefly shown)
    if is_player and not board.flying and not board.lost:
        _draw_aim_line(board)

    # Shooter
    _draw_shooter(board)

    # Flying bubble
    if board.flying:
        _draw_bubble(board.fly_x, board.fly_y, board.fly_color)

    # Pending junk indicator
    if board.pending_junk > 0:
        txt = game.txt_player_junk if is_player else game.txt_ai_junk
        txt.text = f"+{board.pending_junk} junk"
        txt.draw()

    # Label
    if is_player:
        game.txt_player_label.draw()
    else:
        game.txt_ai_label.draw()


def _draw_shooter(board):
    """Draw the shooter at the bottom center of a board."""
    sx, sy = shooter_pos(board.board_left)

    # Base platform
    arcade.draw_rect_filled(
        arcade.XYWH(sx, sy - 8, 40, 8), SHOOTER_COLOR,
    )
    arcade.draw_rect_outline(
        arcade.XYWH(sx, sy - 8, 40, 8), SHOOTER_OUTLINE, 1,
    )

    # Barrel
    barrel_len = 22
    tip_x = sx + math.cos(board.aim_angle) * barrel_len
    tip_y = sy + math.sin(board.aim_angle) * barrel_len

    perp_angle = board.aim_angle + math.pi / 2
    half_w = 5
    bx1 = sx + math.cos(perp_angle) * half_w
    by1 = sy + math.sin(perp_angle) * half_w
    bx2 = sx - math.cos(perp_angle) * half_w
    by2 = sy - math.sin(perp_angle) * half_w

    arcade.draw_triangle_filled(bx1, by1, bx2, by2, tip_x, tip_y, SHOOTER_COLOR)
    arcade.draw_triangle_outline(bx1, by1, bx2, by2, tip_x, tip_y, SHOOTER_OUTLINE, 1)

    # Current bubble at shooter
    if board.current_bubble:
        _draw_bubble(sx, sy, board.current_bubble)

    # Next bubble preview (small, to the side)
    if board.next_bubble:
        nx = sx + 30
        ny = sy - 5
        color = BUBBLE_COLORS.get(board.next_bubble, (200, 200, 200))
        arcade.draw_circle_filled(nx, ny, BUBBLE_RADIUS * 0.6, color)
        outline = tuple(max(v - 40, 0) for v in color[:3])
        arcade.draw_circle_outline(nx, ny, BUBBLE_RADIUS * 0.6, outline, 1)


def _draw_aim_line(board):
    """Draw a dotted aim line showing trajectory."""
    points = board.get_aim_trajectory()
    if len(points) < 2:
        return

    dot_spacing = 10
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
            if total_drawn + dist > 20:
                idx = int((total_drawn + dist) / dot_spacing)
                if idx % 2 == 0:
                    arcade.draw_circle_filled(px, py, 1.5, AIM_DOT_COLOR)
            dist += 3
        total_drawn += seg_len


# ------------------------------------------------------------------
# Center / scores / top bar
# ------------------------------------------------------------------

def _draw_center_vs(game):
    """Draw the VS indicator in the center gap."""
    game.txt_vs.draw()

    # Difficulty label
    if game.ai:
        game.txt_difficulty_label.text = game.ai.difficulty.upper()
        game.txt_difficulty_label.draw()


def _draw_scores(game):
    """Draw scores at the bottom of each board."""
    if game.player_board:
        game.txt_player_score.text = str(game.player_board.score)
        game.txt_player_score.draw()
    if game.ai_board:
        game.txt_ai_score.text = str(game.ai_board.score)
        game.txt_ai_score.draw()


def _draw_top_bar(game):
    """Draw top bar with buttons."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT - TOP_BAR_HEIGHT / 2, WIDTH, TOP_BAR_HEIGHT),
        (20, 20, 35, 220),
    )
    game.btn_back.draw(game.btn_back.contains(game.mouse_x, game.mouse_y))
    game.btn_help.draw(game.btn_help.contains(game.mouse_x, game.mouse_y))


# ------------------------------------------------------------------
# Game over overlay
# ------------------------------------------------------------------

def _draw_game_over(game):
    """Draw win/lose overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        OVERLAY_COLOR,
    )
    if game.winner == "player":
        game.txt_winner.text = "YOU WIN!"
        game.txt_winner.color = (166, 227, 161)
    else:
        game.txt_winner.text = "AI WINS!"
        game.txt_winner.color = (243, 139, 168)
    game.txt_winner.draw()
    game.txt_restart_hint.draw()
