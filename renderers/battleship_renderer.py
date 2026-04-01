"""
Renderer for the Battleship game view.
All arcade.draw_* calls for Battleship are centralized here.
"""

import arcade

from games.battleship import (
    WIDTH, HEIGHT, GRID_SIZE, CELL_SIZE, GRID_PIXEL,
    PLAYER_GRID_LEFT, AI_GRID_LEFT, GRID_TOP,
    SHIP_SIZES, SHIP_NAMES,
    COLOR_WATER, COLOR_SHIP, COLOR_HIT, COLOR_MISS_DOT,
    COLOR_GRID_LINE, COLOR_PREVIEW_VALID, COLOR_PREVIEW_INVALID,
    COLOR_SUNK, BTN_W, BTN_H,
)


def draw(game):
    """Render the entire Battleship game state."""
    _draw_background()
    _draw_buttons()

    if game.phase == "placement":
        _draw_grid(game, PLAYER_GRID_LEFT, game.player_board, show_ships=True)
        _draw_placement_preview(game)
        _draw_ship_list(game)
    else:
        _draw_grid(game, PLAYER_GRID_LEFT, game.player_board, show_ships=True)
        _draw_ai_grid(game)
        _draw_labels()

    _draw_message(game)


def _draw_background():
    arcade.draw_rect_filled(arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), (30, 30, 50))


def _draw_buttons():
    # Back button
    bx, by = 55, HEIGHT - 22
    arcade.draw_rect_filled(arcade.XYWH(bx, by, BTN_W, BTN_H), (80, 80, 100))
    arcade.draw_rect_outline(arcade.XYWH(bx, by, BTN_W, BTN_H), arcade.color.WHITE)
    arcade.draw_text("Back", bx, by, arcade.color.WHITE, 13, anchor_x="center", anchor_y="center")

    # New Game button
    nx, ny = WIDTH - 55, HEIGHT - 22
    arcade.draw_rect_filled(arcade.XYWH(nx, ny, BTN_W, BTN_H), (80, 80, 100))
    arcade.draw_rect_outline(arcade.XYWH(nx, ny, BTN_W, BTN_H), arcade.color.WHITE)
    arcade.draw_text("New Game", nx, ny, arcade.color.WHITE, 13, anchor_x="center", anchor_y="center")

    # Help button
    hx, hy = WIDTH - 140, HEIGHT - 22
    arcade.draw_rect_filled(arcade.XYWH(hx, hy, 40, 30), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(hx, hy, 40, 30), arcade.color.WHITE)
    arcade.draw_text("?", hx, hy, arcade.color.WHITE, 13, anchor_x="center", anchor_y="center")


def _draw_grid(game, left, board, show_ships=False):
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
    for i in range(GRID_SIZE):
        lx = left + i * CELL_SIZE + CELL_SIZE // 2
        ly_top = GRID_TOP + 10
        arcade.draw_text(str(i), lx, ly_top, arcade.color.WHITE, 10, anchor_x="center", anchor_y="center")
        lx_side = left - 12
        ly_side = GRID_TOP - i * CELL_SIZE - CELL_SIZE // 2
        arcade.draw_text(chr(65 + i), lx_side, ly_side, arcade.color.WHITE, 10, anchor_x="center", anchor_y="center")


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
        lx = left + i * CELL_SIZE + CELL_SIZE // 2
        arcade.draw_text(str(i), lx, GRID_TOP + 10, arcade.color.WHITE, 10, anchor_x="center", anchor_y="center")
        ly_side = GRID_TOP - i * CELL_SIZE - CELL_SIZE // 2
        arcade.draw_text(chr(65 + i), left - 12, ly_side, arcade.color.WHITE, 10, anchor_x="center", anchor_y="center")


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
    sx = PLAYER_GRID_LEFT + GRID_PIXEL + 40
    sy = GRID_TOP - 10
    arcade.draw_text("Ships:", sx, sy, arcade.color.WHITE, 14, bold=True)
    for i, name in enumerate(SHIP_NAMES):
        color = (100, 200, 100) if i < game.placement_index else (200, 200, 200)
        prefix = "[x] " if i < game.placement_index else "[ ] "
        if i == game.placement_index:
            prefix = ">>> "
            color = (255, 255, 100)
        arcade.draw_text(prefix + name, sx, sy - 25 - i * 22, color, 12)


def _draw_labels():
    """Draw grid titles during battle phase."""
    px = PLAYER_GRID_LEFT + GRID_PIXEL // 2
    ax = AI_GRID_LEFT + GRID_PIXEL // 2
    label_y = GRID_TOP + 26
    arcade.draw_text("Your Board", px, label_y, arcade.color.WHITE, 14, anchor_x="center", bold=True)
    arcade.draw_text("Enemy Board", ax, label_y, arcade.color.WHITE, 14, anchor_x="center", bold=True)


def _draw_message(game):
    """Draw status message at the bottom."""
    arcade.draw_text(game.message, WIDTH // 2, 30, arcade.color.YELLOW, 15, anchor_x="center", anchor_y="center")
