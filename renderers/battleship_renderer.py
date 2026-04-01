"""
Renderer for the Battleship game view.
All arcade.draw_* calls for Battleship are centralized here.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Grid / cell constants
GRID_SIZE = 10
CELL_SIZE = 28
GRID_PIXEL = GRID_SIZE * CELL_SIZE  # 280

# Layout positions
PLAYER_GRID_LEFT = 30
AI_GRID_LEFT = WIDTH - GRID_PIXEL - 30
GRID_TOP = HEIGHT - 80

# Ship sizes for a standard game
SHIP_SIZES = [5, 4, 3, 3, 2]
SHIP_NAMES = ["Carrier (5)", "Battleship (4)", "Cruiser (3)", "Submarine (3)", "Destroyer (2)"]

# Colors
COLOR_WATER = (173, 216, 230)
COLOR_SHIP = (128, 128, 128)
COLOR_HIT = (220, 50, 50)
COLOR_MISS_DOT = (255, 255, 255)
COLOR_GRID_LINE = (60, 60, 80)
COLOR_PREVIEW_VALID = (100, 200, 100, 120)
COLOR_PREVIEW_INVALID = (200, 100, 100, 120)
COLOR_SUNK = (180, 40, 40)

# Button geometry
BTN_W = 90
BTN_H = 30

AI_SHOT_DELAY = 0.5  # seconds


def draw(game):
    """Render the entire Battleship game state."""
    _draw_background()
    _draw_buttons(game)

    if game.phase == "placement":
        _draw_grid(game, PLAYER_GRID_LEFT, game.player_board, show_ships=True, use_player_labels=True)
        _draw_placement_preview(game)
        _draw_ship_list(game)
    else:
        _draw_grid(game, PLAYER_GRID_LEFT, game.player_board, show_ships=True, use_player_labels=True)
        _draw_ai_grid(game)
        _draw_labels(game)

    _draw_message(game)


def _draw_background():
    arcade.draw_rect_filled(arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), (30, 30, 50))


def _draw_buttons(game):
    # Back button
    bx, by = 55, HEIGHT - 22
    arcade.draw_rect_filled(arcade.XYWH(bx, by, BTN_W, BTN_H), (80, 80, 100))
    arcade.draw_rect_outline(arcade.XYWH(bx, by, BTN_W, BTN_H), arcade.color.WHITE)
    game.txt_btn_back.draw()

    # New Game button
    nx, ny = WIDTH - 55, HEIGHT - 22
    arcade.draw_rect_filled(arcade.XYWH(nx, ny, BTN_W, BTN_H), (80, 80, 100))
    arcade.draw_rect_outline(arcade.XYWH(nx, ny, BTN_W, BTN_H), arcade.color.WHITE)
    game.txt_btn_new_game.draw()

    # Help button
    hx, hy = WIDTH - 140, HEIGHT - 22
    arcade.draw_rect_filled(arcade.XYWH(hx, hy, 40, 30), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(hx, hy, 40, 30), arcade.color.WHITE)
    game.txt_btn_help.draw()


def _draw_grid(game, left, board, show_ships=False, use_player_labels=False):
    """Draw a 10x10 grid from a 2D board array."""
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x, y = game._grid_to_screen(left, row, col)
            val = board[row][col]

            # Background
            if val == 1 and show_ships:
                color = COLOR_SHIP
            elif val == 2:
                color = COLOR_HIT
            elif val == 3:
                color = COLOR_WATER
            else:
                color = COLOR_WATER

            arcade.draw_rect_filled(arcade.XYWH(x, y, CELL_SIZE - 1, CELL_SIZE - 1), color)
            arcade.draw_rect_outline(arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE), COLOR_GRID_LINE)

            # Miss dot
            if val == 3:
                arcade.draw_circle_filled(x, y, 5, COLOR_MISS_DOT)

            # Hit X
            if val == 2:
                hs = CELL_SIZE // 2 - 4
                arcade.draw_line(x - hs, y - hs, x + hs, y + hs, (255, 255, 255), 2)
                arcade.draw_line(x - hs, y + hs, x + hs, y - hs, (255, 255, 255), 2)

    # Column / row labels
    if use_player_labels:
        for i in range(GRID_SIZE):
            game.txt_player_col_labels[i].draw()
            game.txt_player_row_labels[i].draw()


def _draw_ai_grid(game):
    """Draw the AI grid showing only the player's shots (and sunk ships)."""
    left = AI_GRID_LEFT
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x, y = game._grid_to_screen(left, row, col)
            val = game.player_shot_board[row][col]

            if (row, col) in game.ai_ships_sunk_cells:
                color = COLOR_SUNK
            elif val == 2:
                color = COLOR_HIT
            elif val == 3:
                color = COLOR_WATER
            else:
                # In game-over, reveal AI ships
                if game.phase == "gameover" and game.ai.board[row][col] in (1,):
                    color = COLOR_SHIP
                else:
                    color = COLOR_WATER

            arcade.draw_rect_filled(arcade.XYWH(x, y, CELL_SIZE - 1, CELL_SIZE - 1), color)
            arcade.draw_rect_outline(arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE), COLOR_GRID_LINE)

            if val == 3:
                arcade.draw_circle_filled(x, y, 5, COLOR_MISS_DOT)
            if val == 2:
                hs = CELL_SIZE // 2 - 4
                arcade.draw_line(x - hs, y - hs, x + hs, y + hs, (255, 255, 255), 2)
                arcade.draw_line(x - hs, y + hs, x + hs, y - hs, (255, 255, 255), 2)

    # Labels
    for i in range(GRID_SIZE):
        game.txt_ai_col_labels[i].draw()
        game.txt_ai_row_labels[i].draw()


def _draw_placement_preview(game):
    """Show translucent preview of ship being placed."""
    if game.hover_cell is None:
        return
    if game.placement_index >= len(SHIP_SIZES):
        return
    row, col = game.hover_cell
    cells = game._placement_cells(row, col)
    valid = game._placement_valid(cells)
    color = COLOR_PREVIEW_VALID if valid else COLOR_PREVIEW_INVALID

    if cells is None:
        # Show partial preview even when out of bounds
        size = SHIP_SIZES[game.placement_index]
        cells = []
        for i in range(size):
            r = row if game.placement_horizontal else row + i
            c = col + i if game.placement_horizontal else col
            if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                cells.append((r, c))
        color = COLOR_PREVIEW_INVALID

    for r, c in cells:
        x, y = game._grid_to_screen(PLAYER_GRID_LEFT, r, c)
        arcade.draw_rect_filled(arcade.XYWH(x, y, CELL_SIZE - 1, CELL_SIZE - 1), color)


def _draw_ship_list(game):
    """Draw the list of ships during placement phase."""
    game.txt_ship_list_header.draw()
    for i, name in enumerate(SHIP_NAMES):
        color = (100, 200, 100) if i < game.placement_index else (200, 200, 200)
        prefix = "[x] " if i < game.placement_index else "[ ] "
        if i == game.placement_index:
            prefix = ">>> "
            color = (255, 255, 100)
        txt = game.txt_ship_list_items[i]
        txt.text = prefix + name
        txt.color = color
        txt.draw()


def _draw_labels(game):
    """Draw grid titles during battle phase."""
    game.txt_label_your_board.draw()
    game.txt_label_enemy_board.draw()


def _draw_message(game):
    """Draw status message at the bottom."""
    game.txt_message.text = game.message
    game.txt_message.draw()
