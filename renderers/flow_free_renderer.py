"""Renderer for Flow Free — all drawing code lives here."""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout constants
TOP_BAR_HEIGHT = 50
MAX_GRID_AREA = 520
GAP = 2

# Game states
PLAYING = 0
WON = 1

# Flow colors (index matches color_id 1..10)
FLOW_COLORS = [
    (220, 50, 50),     # 1 red
    (50, 120, 220),    # 2 blue
    (50, 200, 50),     # 3 green
    (240, 200, 40),    # 4 yellow
    (240, 140, 30),    # 5 orange
    (160, 40, 200),    # 6 purple
    (0, 200, 200),     # 7 cyan
    (200, 60, 130),    # 8 maroon/pink
    (255, 255, 255),   # 9 white
    (140, 80, 40),     # 10 brown
]

DOT_RADIUS_RATIO = 0.35
PATH_WIDTH_RATIO = 0.45
BG_COLOR = (30, 30, 40)
GRID_BG_COLOR = (50, 50, 60)
CELL_EMPTY_COLOR = (40, 40, 50)
CELL_BORDER_COLOR = (70, 70, 80)


def grid_metrics(grid_size):
    """Compute cell_size, grid_width, grid_height, origin_x, origin_y."""
    cell_size = min(MAX_GRID_AREA // grid_size, 90)
    grid_w = grid_size * cell_size
    grid_h = grid_size * cell_size
    origin_x = (WIDTH - grid_w) / 2
    origin_y = (HEIGHT - TOP_BAR_HEIGHT - grid_h) / 2
    return cell_size, grid_w, grid_h, origin_x, origin_y


def cell_center(row, col, grid_size):
    """Pixel center of a cell. Row 0 is top row visually."""
    cell_size, gw, gh, ox, oy = grid_metrics(grid_size)
    visual_row = (grid_size - 1) - row
    cx = ox + col * cell_size + cell_size / 2
    cy = oy + visual_row * cell_size + cell_size / 2
    return cx, cy


def _flow_color(color_id):
    if 1 <= color_id <= len(FLOW_COLORS):
        return FLOW_COLORS[color_id - 1]
    return (128, 128, 128)


def draw(game):
    """Render the entire Flow Free game state."""
    # Background
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), BG_COLOR,
    )

    # --- Top bar ---
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT), (50, 50, 50),
    )

    # Back button
    arcade.draw_rect_filled(arcade.XYWH(55, bar_y, 90, 35), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(55, bar_y, 90, 35), arcade.color.WHITE)
    game.txt_back.draw()

    # Puzzle info
    game.txt_info.draw()

    # New Game button
    arcade.draw_rect_filled(arcade.XYWH(WIDTH - 65, bar_y, 110, 35), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(WIDTH - 65, bar_y, 110, 35), arcade.color.WHITE)
    game.txt_new_game.draw()

    # Help button
    arcade.draw_rect_filled(arcade.XYWH(WIDTH - 135, bar_y, 40, 35), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(WIDTH - 135, bar_y, 40, 35), arcade.color.WHITE)
    game.txt_help.draw()

    # --- Grid ---
    gs = game.grid_size
    cell_size, gw, gh, ox, oy = grid_metrics(gs)

    # Grid background
    arcade.draw_rect_filled(
        arcade.XYWH(ox + gw / 2, oy + gh / 2, gw, gh), GRID_BG_COLOR,
    )

    # Draw cells
    for r in range(gs):
        for c in range(gs):
            cx, cy = cell_center(r, c, gs)
            color_id = game.cell_colors[r][c]
            if color_id > 0:
                fc = _flow_color(color_id)
                fill = (fc[0] // 3, fc[1] // 3, fc[2] // 3)
            else:
                fill = CELL_EMPTY_COLOR
            arcade.draw_rect_filled(
                arcade.XYWH(cx, cy, cell_size - GAP, cell_size - GAP), fill,
            )
            arcade.draw_rect_outline(
                arcade.XYWH(cx, cy, cell_size - GAP, cell_size - GAP), CELL_BORDER_COLOR,
            )

    # Draw paths
    pw = cell_size * PATH_WIDTH_RATIO
    for color_id, path in game.paths.items():
        if len(path) < 2:
            continue
        fc = _flow_color(color_id)
        for i in range(len(path) - 1):
            r1, c1 = path[i]
            r2, c2 = path[i + 1]
            x1, y1 = cell_center(r1, c1, gs)
            x2, y2 = cell_center(r2, c2, gs)
            arcade.draw_line(x1, y1, x2, y2, fc, pw)

    # Draw endpoint dots
    for color_id, endpoints in game.endpoints.items():
        fc = _flow_color(color_id)
        dr = cell_size * DOT_RADIUS_RATIO
        for r, c in endpoints:
            cx, cy = cell_center(r, c, gs)
            arcade.draw_circle_filled(cx, cy, dr, fc)
            arcade.draw_circle_outline(cx, cy, dr, (255, 255, 255, 100), 2)

    # Draw current dragging path highlight
    if game.drawing_color > 0 and len(game.current_path) >= 1:
        fc = _flow_color(game.drawing_color)
        bright = (min(fc[0] + 60, 255), min(fc[1] + 60, 255), min(fc[2] + 60, 255))
        for r, c in game.current_path:
            cx, cy = cell_center(r, c, gs)
            arcade.draw_rect_filled(
                arcade.XYWH(cx, cy, cell_size * 0.3, cell_size * 0.3),
                (*bright, 120),
            )

    # --- Win overlay ---
    if game.game_state == WON:
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (0, 0, 0, 150),
        )
        game.txt_you_win.draw()
        game.txt_win_details.draw()
