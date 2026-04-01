"""
Renderer for the Snake game.
All arcade.draw_* calls for Snake live here.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
CELL_SIZE = 25

# Grid dimensions (play area below top bar)
GRID_COLS = WIDTH // CELL_SIZE
GRID_ROWS = (HEIGHT - TOP_BAR_HEIGHT) // CELL_SIZE
GRID_ORIGIN_X = (WIDTH - GRID_COLS * CELL_SIZE) // 2
GRID_ORIGIN_Y = (HEIGHT - TOP_BAR_HEIGHT - GRID_ROWS * CELL_SIZE) // 2

# Colors (Catppuccin-ish palette to match other games)
BG_COLOR = (30, 30, 46)
GRID_LINE_COLOR = (45, 45, 65)
SNAKE_HEAD_COLOR = (64, 160, 64)
SNAKE_BODY_COLOR = (116, 199, 116)
FOOD_COLOR = (243, 139, 168)
LINE_COLOR = (205, 214, 244)
BUTTON_COLOR = (69, 71, 90)
BUTTON_HOVER_COLOR = (88, 91, 112)
BUTTON_TEXT_COLOR = (205, 214, 244)
OVERLAY_COLOR = (30, 30, 46, 200)
STATUS_TEXT_COLOR = (205, 214, 244)
SCORE_COLOR = (249, 226, 175)


def _cell_to_screen(col, row):
    """Convert grid (col, row) to screen center (x, y)."""
    x = GRID_ORIGIN_X + col * CELL_SIZE + CELL_SIZE // 2
    y = GRID_ORIGIN_Y + row * CELL_SIZE + CELL_SIZE // 2
    return x, y


def draw(game):
    """Render the entire Snake game state."""
    _draw_grid()
    _draw_food(game)
    _draw_snake(game)
    _draw_play_area_border()
    _draw_top_bar(game)
    _draw_buttons(game)
    if game.game_over:
        _draw_game_over_overlay(game)


def _draw_grid():
    """Draw faint grid lines."""
    for c in range(GRID_COLS + 1):
        x = GRID_ORIGIN_X + c * CELL_SIZE
        arcade.draw_line(x, GRID_ORIGIN_Y, x, GRID_ORIGIN_Y + GRID_ROWS * CELL_SIZE, GRID_LINE_COLOR, 1)
    for r in range(GRID_ROWS + 1):
        y = GRID_ORIGIN_Y + r * CELL_SIZE
        arcade.draw_line(GRID_ORIGIN_X, y, GRID_ORIGIN_X + GRID_COLS * CELL_SIZE, y, GRID_LINE_COLOR, 1)


def _draw_food(game):
    """Draw the food item."""
    if game.food:
        fx, fy = _cell_to_screen(*game.food)
        arcade.draw_rect_filled(
            arcade.XYWH(fx, fy, CELL_SIZE - 2, CELL_SIZE - 2),
            FOOD_COLOR,
        )


def _draw_snake(game):
    """Draw the snake body and head."""
    for i, segment in enumerate(game.snake):
        sx, sy = _cell_to_screen(*segment)
        is_head = (i == len(game.snake) - 1)
        color = SNAKE_HEAD_COLOR if is_head else SNAKE_BODY_COLOR
        arcade.draw_rect_filled(
            arcade.XYWH(sx, sy, CELL_SIZE - 2, CELL_SIZE - 2),
            color,
        )


def _draw_play_area_border():
    """Draw the border around the play area."""
    bx = GRID_ORIGIN_X + (GRID_COLS * CELL_SIZE) / 2
    by = GRID_ORIGIN_Y + (GRID_ROWS * CELL_SIZE) / 2
    arcade.draw_rect_outline(
        arcade.XYWH(bx, by, GRID_COLS * CELL_SIZE, GRID_ROWS * CELL_SIZE),
        LINE_COLOR,
        2,
    )


def _draw_top_bar(game):
    """Draw the top status bar with score."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT - TOP_BAR_HEIGHT // 2, WIDTH, TOP_BAR_HEIGHT),
        BG_COLOR,
    )
    arcade.draw_line(0, HEIGHT - TOP_BAR_HEIGHT, WIDTH, HEIGHT - TOP_BAR_HEIGHT, LINE_COLOR, 2)

    game.txt_score.text = f"Score: {game.score}"
    game.txt_score.draw()
    game.txt_high_score.text = f"High: {game.high_score}"
    game.txt_high_score.draw()


def _draw_buttons(game):
    """Draw the top bar buttons."""
    hover_back = game.btn_back.contains(game.mouse_x, game.mouse_y)
    hover_new = game.btn_new.contains(game.mouse_x, game.mouse_y)
    hover_help = game.btn_help.contains(game.mouse_x, game.mouse_y)
    game.btn_back.draw(hover=hover_back)
    game.btn_new.draw(hover=hover_new)
    game.btn_help.draw(hover=hover_help)


def _draw_game_over_overlay(game):
    """Draw the game over overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT),
        OVERLAY_COLOR,
    )
    game.txt_game_over.draw()
    game.txt_game_over_score.text = f"Score: {game.score}"
    game.txt_game_over_score.draw()
    game.txt_game_over_hint.draw()
