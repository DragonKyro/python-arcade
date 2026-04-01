"""Renderer for Ricochet Robots — all drawing code lives here."""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout constants
TOP_BAR_HEIGHT = 50
GRID_SIZE = 16
CELL_SIZE = 32

# Grid origin centered in window
GRID_WIDTH = GRID_SIZE * CELL_SIZE
GRID_HEIGHT = GRID_SIZE * CELL_SIZE
GRID_ORIGIN_X = (WIDTH - GRID_WIDTH) // 2
GRID_ORIGIN_Y = (HEIGHT - TOP_BAR_HEIGHT - GRID_HEIGHT) // 2

# Game states
PLAYING = 0
WON = 1

# Robot colors
COLOR_RED = (220, 50, 50)
COLOR_BLUE = (50, 100, 220)
COLOR_GREEN = (50, 180, 50)
COLOR_YELLOW = (220, 200, 50)

WALL_THICKNESS = 3
WALL_COLOR = (200, 180, 140)


def draw(game):
    """Render the entire Ricochet Robots game state."""
    # Background
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (30, 35, 45))

    # --- Top bar ---
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT), (50, 50, 50))

    # Back button
    arcade.draw_rect_filled(arcade.XYWH(55, bar_y, 90, 35), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(55, bar_y, 90, 35), arcade.color.WHITE)
    game.txt_back.draw()

    # Moves counter
    game.txt_moves.text = f"Moves: {game.moves}"
    game.txt_moves.draw()

    # Target info
    if hasattr(game, 'target_robot') and game.target_robot is not None:
        robot_names = ["Red", "Blue", "Green", "Yellow"]
        name = robot_names[game.target_robot]
        game.txt_target_info.text = f"Target: {name}"
        game.txt_target_info.color = [COLOR_RED, COLOR_BLUE, COLOR_GREEN, COLOR_YELLOW][game.target_robot]
        game.txt_target_info.draw()

    # Reset button
    arcade.draw_rect_filled(arcade.XYWH(WIDTH - 200, bar_y, 70, 35), arcade.color.DARK_RED)
    arcade.draw_rect_outline(arcade.XYWH(WIDTH - 200, bar_y, 70, 35), arcade.color.WHITE)
    game.txt_reset.draw()

    # New Game button
    arcade.draw_rect_filled(arcade.XYWH(WIDTH - 65, bar_y, 110, 35), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(WIDTH - 65, bar_y, 110, 35), arcade.color.WHITE)
    game.txt_new_game.draw()

    # Help button
    arcade.draw_rect_filled(arcade.XYWH(WIDTH - 135, bar_y, 40, 35), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(WIDTH - 135, bar_y, 40, 35), arcade.color.WHITE)
    game.txt_help.draw()

    # --- Grid background ---
    grid_cx = GRID_ORIGIN_X + GRID_WIDTH / 2
    grid_cy = GRID_ORIGIN_Y + GRID_HEIGHT / 2
    arcade.draw_rect_filled(
        arcade.XYWH(grid_cx, grid_cy, GRID_WIDTH, GRID_HEIGHT), (60, 65, 75)
    )

    # Grid lines
    for i in range(GRID_SIZE + 1):
        x = GRID_ORIGIN_X + i * CELL_SIZE
        arcade.draw_line(x, GRID_ORIGIN_Y, x, GRID_ORIGIN_Y + GRID_HEIGHT, (80, 85, 95), 1)
    for i in range(GRID_SIZE + 1):
        y = GRID_ORIGIN_Y + i * CELL_SIZE
        arcade.draw_line(GRID_ORIGIN_X, y, GRID_ORIGIN_X + GRID_WIDTH, y, (80, 85, 95), 1)

    # --- Target cell ---
    if hasattr(game, 'target'):
        tr, tc = game.target
        tx = GRID_ORIGIN_X + tc * CELL_SIZE + CELL_SIZE / 2
        ty = GRID_ORIGIN_Y + tr * CELL_SIZE + CELL_SIZE / 2
        target_color = [COLOR_RED, COLOR_BLUE, COLOR_GREEN, COLOR_YELLOW][game.target_robot]
        # Draw target as a diamond/marker
        faded = tuple(c // 3 for c in target_color)
        arcade.draw_rect_filled(arcade.XYWH(tx, ty, CELL_SIZE - 2, CELL_SIZE - 2), faded)
        arcade.draw_circle_outline(tx, ty, CELL_SIZE * 0.35, target_color, 2)
        # Inner dot
        arcade.draw_circle_filled(tx, ty, CELL_SIZE * 0.12, target_color)

    # --- Walls ---
    # Draw internal walls (skip border walls as they're implicit from the grid outline)
    for (row, col), side in game.walls:
        if row < 0 or row >= GRID_SIZE or col < 0 or col >= GRID_SIZE:
            continue
        bx = GRID_ORIGIN_X + col * CELL_SIZE
        by = GRID_ORIGIN_Y + row * CELL_SIZE

        if side == 'N' and row < GRID_SIZE - 1:
            arcade.draw_line(bx, by + CELL_SIZE, bx + CELL_SIZE, by + CELL_SIZE,
                             WALL_COLOR, WALL_THICKNESS)
        elif side == 'S' and row > 0:
            arcade.draw_line(bx, by, bx + CELL_SIZE, by,
                             WALL_COLOR, WALL_THICKNESS)
        elif side == 'E' and col < GRID_SIZE - 1:
            arcade.draw_line(bx + CELL_SIZE, by, bx + CELL_SIZE, by + CELL_SIZE,
                             WALL_COLOR, WALL_THICKNESS)
        elif side == 'W' and col > 0:
            arcade.draw_line(bx, by, bx, by + CELL_SIZE,
                             WALL_COLOR, WALL_THICKNESS)

    # Border outline
    arcade.draw_rect_outline(
        arcade.XYWH(grid_cx, grid_cy, GRID_WIDTH, GRID_HEIGHT), WALL_COLOR, WALL_THICKNESS
    )

    # --- Robots ---
    for i, robot in enumerate(game.robots):
        rx = GRID_ORIGIN_X + robot['col'] * CELL_SIZE + CELL_SIZE / 2
        ry = GRID_ORIGIN_Y + robot['row'] * CELL_SIZE + CELL_SIZE / 2
        color = robot['color']

        # Selection highlight
        if game.selected_robot == i:
            arcade.draw_circle_filled(rx, ry, CELL_SIZE * 0.45, (255, 255, 255, 80))

        # Robot body
        arcade.draw_circle_filled(rx, ry, CELL_SIZE * 0.35, color)
        outline = tuple(min(255, c + 80) for c in color)
        arcade.draw_circle_outline(rx, ry, CELL_SIZE * 0.35, outline, 2)

    # --- Selected robot info ---
    if game.selected_robot is not None:
        robot = game.robots[game.selected_robot]
        game.txt_selected.text = f"Selected: {robot['name']} (arrow keys or click to slide)"
        game.txt_selected.draw()

    # --- Win overlay ---
    if game.game_state == WON:
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
            (0, 0, 0, 150)
        )
        game.txt_you_win.draw()
        game.txt_win_info.text = f"Solved in {game.moves} moves! Click 'New Game' for a new puzzle."
        game.txt_win_info.draw()
