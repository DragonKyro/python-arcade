"""
Renderer for the Tetris game.
All drawing code extracted from games/tetris.py.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
CELL_SIZE = 25
BOARD_COLS = 10
BOARD_ROWS = 20

# Board positioning
BOARD_PIXEL_W = BOARD_COLS * CELL_SIZE
BOARD_PIXEL_H = BOARD_ROWS * CELL_SIZE
BOARD_ORIGIN_X = (WIDTH // 2 - BOARD_PIXEL_W) // 2 + 40
BOARD_ORIGIN_Y = (HEIGHT - TOP_BAR_HEIGHT - BOARD_PIXEL_H) // 2

# Side panel
PANEL_X = BOARD_ORIGIN_X + BOARD_PIXEL_W + 40

# Colors
GRID_LINE_COLOR = (45, 45, 65)
LINE_COLOR = (205, 214, 244)
BUTTON_HOVER_COLOR = (88, 91, 112)
STATUS_TEXT_COLOR = (205, 214, 244)
SCORE_COLOR = (249, 226, 175)
BOARD_BG_COLOR = (24, 24, 37)
OVERLAY_COLOR = (30, 30, 46, 200)

# Piece colors
PIECE_COLORS = {
    "I": (6, 214, 250),
    "O": (249, 226, 175),
    "T": (203, 166, 247),
    "S": (166, 227, 161),
    "Z": (243, 139, 168),
    "J": (137, 180, 250),
    "L": (250, 179, 135),
}

# Ghost piece alpha
GHOST_ALPHA = 60

# Tetromino definitions (needed for next piece preview)
TETROMINOES = {
    "I": [
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 1), (1, 1), (2, 1), (3, 1)],
    ],
    "O": [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
    ],
    "T": [
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 1)],
        [(0, 1), (1, 0), (1, 1), (2, 1)],
    ],
    "S": [
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
    ],
    "Z": [
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
    ],
    "J": [
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (0, 2), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 0), (2, 1)],
    ],
    "L": [
        [(0, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (1, 2), (2, 0)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
    ],
}


def _cell_to_screen(col, row):
    """Convert board (col, row) to screen center (x, y). Row 0 is bottom."""
    x = BOARD_ORIGIN_X + col * CELL_SIZE + CELL_SIZE // 2
    y = BOARD_ORIGIN_Y + row * CELL_SIZE + CELL_SIZE // 2
    return x, y


def draw(game):
    """Render the entire Tetris game state."""
    _draw_board_bg()
    _draw_grid_lines()
    _draw_locked_cells(game)
    if not game.game_over:
        _draw_ghost(game)
        _draw_current_piece(game)
    _draw_board_outline()
    _draw_side_panel(game)
    _draw_top_bar(game)

    if game.game_over:
        _draw_game_over(game)


def _draw_board_bg():
    """Draw the dark board background."""
    cx = BOARD_ORIGIN_X + BOARD_PIXEL_W / 2
    cy = BOARD_ORIGIN_Y + BOARD_PIXEL_H / 2
    arcade.draw_rect_filled(
        arcade.XYWH(cx, cy, BOARD_PIXEL_W, BOARD_PIXEL_H),
        BOARD_BG_COLOR,
    )


def _draw_grid_lines():
    """Draw faint grid lines on the board."""
    for c in range(BOARD_COLS + 1):
        x = BOARD_ORIGIN_X + c * CELL_SIZE
        arcade.draw_line(
            x, BOARD_ORIGIN_Y,
            x, BOARD_ORIGIN_Y + BOARD_PIXEL_H,
            GRID_LINE_COLOR, 1,
        )
    for r in range(BOARD_ROWS + 1):
        y = BOARD_ORIGIN_Y + r * CELL_SIZE
        arcade.draw_line(
            BOARD_ORIGIN_X, y,
            BOARD_ORIGIN_X + BOARD_PIXEL_W, y,
            GRID_LINE_COLOR, 1,
        )


def _draw_board_outline():
    """Draw the board border."""
    cx = BOARD_ORIGIN_X + BOARD_PIXEL_W / 2
    cy = BOARD_ORIGIN_Y + BOARD_PIXEL_H / 2
    arcade.draw_rect_outline(
        arcade.XYWH(cx, cy, BOARD_PIXEL_W, BOARD_PIXEL_H),
        LINE_COLOR, 2,
    )


def _draw_cell(col, row, color, outline_color=None):
    """Draw a single cell on the board."""
    x, y = _cell_to_screen(col, row)
    arcade.draw_rect_filled(
        arcade.XYWH(x, y, CELL_SIZE - 2, CELL_SIZE - 2),
        color,
    )
    if outline_color:
        arcade.draw_rect_outline(
            arcade.XYWH(x, y, CELL_SIZE - 2, CELL_SIZE - 2),
            outline_color, 1,
        )


def _draw_locked_cells(game):
    """Draw all locked cells on the board."""
    for r in range(BOARD_ROWS):
        for c in range(BOARD_COLS):
            color = game.board[r][c]
            if color is not None:
                outline = tuple(min(v + 40, 255) for v in color)
                _draw_cell(c, r, color, outline)


def _draw_current_piece(game):
    """Draw the currently falling piece."""
    color = PIECE_COLORS[game.current_type]
    outline = tuple(min(v + 40, 255) for v in color)
    for bc, br in game._get_cells(game.current_type, game.rotation, game.piece_col, game.piece_row):
        if 0 <= br < BOARD_ROWS:
            _draw_cell(bc, br, color, outline)


def _draw_ghost(game):
    """Draw translucent ghost piece showing landing position."""
    ghost_r = game._ghost_row()
    if ghost_r == game.piece_row:
        return
    base_color = PIECE_COLORS[game.current_type]
    ghost_color = (base_color[0], base_color[1], base_color[2], GHOST_ALPHA)
    for bc, br in game._get_cells(game.current_type, game.rotation, game.piece_col, ghost_r):
        if 0 <= br < BOARD_ROWS:
            x, y = _cell_to_screen(bc, br)
            arcade.draw_rect_filled(
                arcade.XYWH(x, y, CELL_SIZE - 2, CELL_SIZE - 2),
                ghost_color,
            )
            arcade.draw_rect_outline(
                arcade.XYWH(x, y, CELL_SIZE - 2, CELL_SIZE - 2),
                ghost_color, 1,
            )


def _draw_side_panel(game):
    """Draw next piece preview, score, level, and lines on the right."""
    x = PANEL_X
    top_y = BOARD_ORIGIN_Y + BOARD_PIXEL_H

    # Title
    arcade.draw_text(
        "TETRIS",
        x, top_y + 10,
        SCORE_COLOR,
        font_size=22,
        bold=True,
        anchor_x="left",
        anchor_y="bottom",
    )

    # Next piece label
    y = top_y - 20
    arcade.draw_text("NEXT", x, y, STATUS_TEXT_COLOR, font_size=14, anchor_x="left", anchor_y="top")

    # Draw next piece preview
    preview_y = y - 25
    shape = TETROMINOES[game.next_piece_type][0]
    color = PIECE_COLORS[game.next_piece_type]
    outline = tuple(min(v + 40, 255) for v in color)
    preview_size = 20
    for dr, dc in shape:
        px = x + dc * preview_size + preview_size // 2
        py = preview_y - dr * preview_size - preview_size // 2
        arcade.draw_rect_filled(
            arcade.XYWH(px, py, preview_size - 2, preview_size - 2),
            color,
        )
        arcade.draw_rect_outline(
            arcade.XYWH(px, py, preview_size - 2, preview_size - 2),
            outline, 1,
        )

    # Stats
    stats_y = preview_y - 110
    arcade.draw_text("SCORE", x, stats_y, STATUS_TEXT_COLOR, font_size=13, anchor_x="left", anchor_y="top")
    arcade.draw_text(
        str(game.score), x, stats_y - 20, SCORE_COLOR,
        font_size=18, bold=True, anchor_x="left", anchor_y="top",
    )

    stats_y -= 60
    arcade.draw_text("LEVEL", x, stats_y, STATUS_TEXT_COLOR, font_size=13, anchor_x="left", anchor_y="top")
    arcade.draw_text(
        str(game.level), x, stats_y - 20, SCORE_COLOR,
        font_size=18, bold=True, anchor_x="left", anchor_y="top",
    )

    stats_y -= 60
    arcade.draw_text("LINES", x, stats_y, STATUS_TEXT_COLOR, font_size=13, anchor_x="left", anchor_y="top")
    arcade.draw_text(
        str(game.lines_cleared), x, stats_y - 20, SCORE_COLOR,
        font_size=18, bold=True, anchor_x="left", anchor_y="top",
    )

    # Controls hint
    stats_y -= 80
    controls = [
        "CONTROLS",
        "<< >>  Move",
        "^    Rotate",
        "v    Soft Drop",
        "Space Hard Drop",
    ]
    for i, line in enumerate(controls):
        fs = 11 if i > 0 else 12
        c = STATUS_TEXT_COLOR if i > 0 else SCORE_COLOR
        arcade.draw_text(
            line, x, stats_y - i * 18, c,
            font_size=fs, anchor_x="left", anchor_y="top",
        )


def _draw_top_bar(game):
    """Draw buttons on the top bar."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT - TOP_BAR_HEIGHT / 2, WIDTH, TOP_BAR_HEIGHT),
        (30, 30, 46, 220),
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

    arcade.draw_text(
        "GAME OVER",
        WIDTH / 2, HEIGHT / 2 + 30,
        (243, 139, 168),
        font_size=36,
        bold=True,
        anchor_x="center",
        anchor_y="center",
    )
    arcade.draw_text(
        f"Score: {game.score}",
        WIDTH / 2, HEIGHT / 2 - 15,
        SCORE_COLOR,
        font_size=20,
        anchor_x="center",
        anchor_y="center",
    )
    arcade.draw_text(
        "Press ENTER or click New Game to play again",
        WIDTH / 2, HEIGHT / 2 - 50,
        STATUS_TEXT_COLOR,
        font_size=13,
        anchor_x="center",
        anchor_y="center",
    )
