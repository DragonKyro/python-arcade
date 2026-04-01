"""Renderer for Sokoban -- all drawing code lives here."""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout constants
TOP_BAR_HEIGHT = 50
CELL_SIZE = 40

# Game states
PLAYING = 0
WON = 1

# Tile types
FLOOR = 0
WALL = 1
GOAL = 2

# Colors
COLOR_WALL = (60, 60, 80)
COLOR_FLOOR = (180, 170, 150)
COLOR_GOAL = (220, 200, 100)
COLOR_PLAYER = (50, 120, 220)
COLOR_BOX = (180, 100, 50)
COLOR_BOX_ON_GOAL = (100, 200, 80)
COLOR_GRID_LINE = (140, 130, 110)
COLOR_PLAYER_EYE = arcade.color.WHITE


def grid_origin(level_width, level_height):
    """Return (ox, oy) for bottom-left of the grid, centered on screen."""
    grid_w = level_width * CELL_SIZE
    grid_h = level_height * CELL_SIZE
    play_area_h = HEIGHT - TOP_BAR_HEIGHT
    ox = (WIDTH - grid_w) / 2
    oy = (play_area_h - grid_h) / 2
    return ox, oy


def cell_center(col, row, ox, oy, level_height):
    """Return pixel center (cx, cy) for a cell. Row 0 = top row of level."""
    visual_row = (level_height - 1) - row
    cx = ox + col * CELL_SIZE + CELL_SIZE / 2
    cy = oy + visual_row * CELL_SIZE + CELL_SIZE / 2
    return cx, cy


def draw(game):
    """Render the entire Sokoban game state."""
    level = game.current_level()
    grid = level["grid"]
    level_h = len(grid)
    level_w = len(grid[0]) if grid else 0
    ox, oy = grid_origin(level_w, level_h)

    # Background
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        arcade.color.DARK_SLATE_GRAY,
    )

    # --- Top bar ---
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT),
        (50, 50, 50),
    )

    # Back button
    arcade.draw_rect_filled(
        arcade.XYWH(55, bar_y, 90, 35),
        arcade.color.DARK_SLATE_BLUE,
    )
    arcade.draw_rect_outline(
        arcade.XYWH(55, bar_y, 90, 35),
        arcade.color.WHITE,
    )
    game.txt_back.draw()

    # Move counter
    game.txt_moves.text = f"Moves: {game.move_count}"
    game.txt_moves.draw()

    # Level indicator
    game.txt_level.text = f"Level {game.level_index + 1}/{len(game.levels)}"
    game.txt_level.draw()

    # New Game button
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH - 65, bar_y, 110, 35),
        arcade.color.DARK_GREEN,
    )
    arcade.draw_rect_outline(
        arcade.XYWH(WIDTH - 65, bar_y, 110, 35),
        arcade.color.WHITE,
    )
    game.txt_new_game.draw()

    # Help button
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH - 135, bar_y, 40, 35),
        arcade.color.DARK_SLATE_BLUE,
    )
    arcade.draw_rect_outline(
        arcade.XYWH(WIDTH - 135, bar_y, 40, 35),
        arcade.color.WHITE,
    )
    game.txt_help.draw()

    # Undo hint
    game.txt_undo_hint.draw()

    # --- Grid ---
    for row in range(level_h):
        for col in range(level_w):
            cx, cy = cell_center(col, row, ox, oy, level_h)
            tile = grid[row][col]

            if tile == WALL:
                arcade.draw_rect_filled(
                    arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE),
                    COLOR_WALL,
                )
            elif tile == GOAL:
                arcade.draw_rect_filled(
                    arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE),
                    COLOR_FLOOR,
                )
                # Goal diamond
                arcade.draw_rect_filled(
                    arcade.XYWH(cx, cy, CELL_SIZE * 0.4, CELL_SIZE * 0.4),
                    COLOR_GOAL,
                    tilt_angle=45,
                )
            elif tile == FLOOR:
                arcade.draw_rect_filled(
                    arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE),
                    COLOR_FLOOR,
                )

            # Grid lines for non-wall tiles
            if tile != WALL:
                arcade.draw_rect_outline(
                    arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE),
                    COLOR_GRID_LINE,
                )

    # --- Boxes ---
    for (br, bc) in game.boxes:
        cx, cy = cell_center(bc, br, ox, oy, level_h)
        on_goal = grid[br][bc] == GOAL
        color = COLOR_BOX_ON_GOAL if on_goal else COLOR_BOX
        margin = 4
        arcade.draw_rect_filled(
            arcade.XYWH(cx, cy, CELL_SIZE - margin, CELL_SIZE - margin),
            color,
        )
        arcade.draw_rect_outline(
            arcade.XYWH(cx, cy, CELL_SIZE - margin, CELL_SIZE - margin),
            (255, 255, 255, 100),
            border_width=2,
        )
        # Cross on box
        s = CELL_SIZE * 0.15
        arcade.draw_rect_filled(
            arcade.XYWH(cx, cy, s * 2, 3),
            (255, 255, 255, 120),
        )
        arcade.draw_rect_filled(
            arcade.XYWH(cx, cy, 3, s * 2),
            (255, 255, 255, 120),
        )

    # --- Player ---
    pr, pc = game.player_pos
    px, py = cell_center(pc, pr, ox, oy, level_h)
    radius = CELL_SIZE * 0.35
    arcade.draw_circle_filled(px, py, radius, COLOR_PLAYER)
    arcade.draw_circle_outline(px, py, radius, (255, 255, 255, 100), 2)
    # Eyes
    eye_offset = radius * 0.3
    eye_r = 3
    arcade.draw_circle_filled(px - eye_offset, py + eye_offset * 0.5, eye_r, COLOR_PLAYER_EYE)
    arcade.draw_circle_filled(px + eye_offset, py + eye_offset * 0.5, eye_r, COLOR_PLAYER_EYE)

    # --- Win overlay ---
    if game.game_state == WON:
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
            (0, 0, 0, 150),
        )
        game.txt_you_win.draw()
        game.txt_win_details.text = f"Level {game.level_index + 1} complete in {game.move_count} moves!"
        game.txt_win_details.draw()

        # Next level button (if not last level)
        if game.level_index < len(game.levels) - 1:
            arcade.draw_rect_filled(
                arcade.XYWH(WIDTH / 2, HEIGHT / 2 - 70, 160, 40),
                arcade.color.DARK_GREEN,
            )
            arcade.draw_rect_outline(
                arcade.XYWH(WIDTH / 2, HEIGHT / 2 - 70, 160, 40),
                arcade.color.WHITE,
            )
            game.txt_next_level.draw()
