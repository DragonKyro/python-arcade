"""
Renderer for the Hashi (Bridges) game.
All arcade.draw_* calls for Hashi live here.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Grid constants
GRID_SIZE = 9
CELL_SIZE = 50
GRID_PX = GRID_SIZE * CELL_SIZE

# Layout
GRID_ORIGIN_X = (WIDTH - GRID_PX) // 2
GRID_ORIGIN_Y = (HEIGHT - 50 - GRID_PX) // 2

# Top bar
TOP_BAR_HEIGHT = 50

# Island dimensions
ISLAND_RADIUS = 18
BRIDGE_OFFSET = 4  # Offset for double bridges

# Colors
BG_COLOR = (40, 44, 52)
GRID_LINE_COLOR = (55, 60, 70)
ISLAND_COLOR = (70, 130, 200)
ISLAND_OUTLINE = (120, 180, 240)
ISLAND_SATISFIED_COLOR = (60, 160, 80)
ISLAND_SATISFIED_OUTLINE = (100, 200, 120)
ISLAND_OVER_COLOR = (200, 60, 60)
ISLAND_OVER_OUTLINE = (240, 100, 100)
ISLAND_TEXT_COLOR = (255, 255, 255)
BRIDGE_COLOR = (160, 180, 200)
HIGHLIGHT_COLOR = (255, 220, 100, 120)
WIN_OVERLAY = (0, 0, 0, 160)

# Game states
PLAYING = "playing"
WON = "won"


def draw(game):
    """Render the entire Hashi game state."""
    _draw_background()
    _draw_top_bar(game)
    _draw_grid_lines()
    _draw_bridges(game)
    _draw_islands(game)
    if game.selected_island is not None:
        _draw_selection(game)
    if game.game_state == WON:
        _draw_win_overlay(game)


def _draw_background():
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), BG_COLOR)


def _draw_top_bar(game):
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT), (50, 50, 50))

    # Back button
    bx, by, bw, bh = 55, bar_y, 90, 35
    arcade.draw_rect_filled(arcade.XYWH(bx, by, bw, bh), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(bx, by, bw, bh), arcade.color.WHITE)
    game.txt_back.draw()

    # New Game button
    nx, ny, nw, nh = WIDTH - 65, bar_y, 110, 35
    arcade.draw_rect_filled(arcade.XYWH(nx, ny, nw, nh), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(nx, ny, nw, nh), arcade.color.WHITE)
    game.txt_new_game.draw()

    # Help button
    hx, hy, hw, hh = WIDTH - 135, bar_y, 40, 40
    arcade.draw_rect_filled(arcade.XYWH(hx, hy, hw, hh), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(hx, hy, hw, hh), arcade.color.WHITE)
    game.txt_help.draw()

    # Timer
    mins = int(game.elapsed_time) // 60
    secs = int(game.elapsed_time) % 60
    game.txt_timer.text = f"{mins:02d}:{secs:02d}"
    game.txt_timer.draw()


def _draw_grid_lines():
    """Draw subtle grid lines."""
    for i in range(GRID_SIZE + 1):
        x = GRID_ORIGIN_X + i * CELL_SIZE
        y0 = GRID_ORIGIN_Y
        y1 = GRID_ORIGIN_Y + GRID_PX
        arcade.draw_line(x, y0, x, y1, GRID_LINE_COLOR, 1)

        y = GRID_ORIGIN_Y + i * CELL_SIZE
        x0 = GRID_ORIGIN_X
        x1 = GRID_ORIGIN_X + GRID_PX
        arcade.draw_line(x0, y, x1, y, GRID_LINE_COLOR, 1)


def _draw_bridges(game):
    """Draw all bridges between islands."""
    drawn = set()
    for key, count in game.bridges.items():
        if count == 0:
            continue
        (r1, c1), (r2, c2) = key
        if (r2, c2, r1, c1) in drawn:
            continue
        drawn.add((r1, c1, r2, c2))

        x1 = GRID_ORIGIN_X + c1 * CELL_SIZE + CELL_SIZE / 2
        y1 = GRID_ORIGIN_Y + (GRID_SIZE - 1 - r1) * CELL_SIZE + CELL_SIZE / 2
        x2 = GRID_ORIGIN_X + c2 * CELL_SIZE + CELL_SIZE / 2
        y2 = GRID_ORIGIN_Y + (GRID_SIZE - 1 - r2) * CELL_SIZE + CELL_SIZE / 2

        if count == 1:
            arcade.draw_line(x1, y1, x2, y2, BRIDGE_COLOR, 3)
        elif count == 2:
            # Draw two parallel lines
            if r1 == r2:  # Horizontal bridge
                arcade.draw_line(x1, y1 - BRIDGE_OFFSET, x2, y2 - BRIDGE_OFFSET, BRIDGE_COLOR, 3)
                arcade.draw_line(x1, y1 + BRIDGE_OFFSET, x2, y2 + BRIDGE_OFFSET, BRIDGE_COLOR, 3)
            else:  # Vertical bridge
                arcade.draw_line(x1 - BRIDGE_OFFSET, y1, x2 - BRIDGE_OFFSET, y2, BRIDGE_COLOR, 3)
                arcade.draw_line(x1 + BRIDGE_OFFSET, y1, x2 + BRIDGE_OFFSET, y2, BRIDGE_COLOR, 3)


def _draw_islands(game):
    """Draw all island circles with numbers."""
    for (r, c), value in game.islands.items():
        cx = GRID_ORIGIN_X + c * CELL_SIZE + CELL_SIZE / 2
        cy = GRID_ORIGIN_Y + (GRID_SIZE - 1 - r) * CELL_SIZE + CELL_SIZE / 2

        # Count current bridges
        bridge_count = game.get_island_bridge_count(r, c)

        if bridge_count == value:
            fill = ISLAND_SATISFIED_COLOR
            outline = ISLAND_SATISFIED_OUTLINE
        elif bridge_count > value:
            fill = ISLAND_OVER_COLOR
            outline = ISLAND_OVER_OUTLINE
        else:
            fill = ISLAND_COLOR
            outline = ISLAND_OUTLINE

        arcade.draw_circle_filled(cx, cy, ISLAND_RADIUS, fill)
        arcade.draw_circle_outline(cx, cy, ISLAND_RADIUS, outline, 2)

        txt = game.txt_islands.get((r, c))
        if txt:
            txt.text = str(value)
            txt.draw()


def _draw_selection(game):
    """Draw highlight on selected island and its possible connections."""
    r, c = game.selected_island
    cx = GRID_ORIGIN_X + c * CELL_SIZE + CELL_SIZE / 2
    cy = GRID_ORIGIN_Y + (GRID_SIZE - 1 - r) * CELL_SIZE + CELL_SIZE / 2
    arcade.draw_circle_filled(cx, cy, ISLAND_RADIUS + 4, HIGHLIGHT_COLOR)


def _draw_win_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        WIN_OVERLAY
    )
    game.txt_win_title.draw()
    game.txt_win_hint.draw()
