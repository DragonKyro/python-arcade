"""
Renderer for the Tetris VS game.
All drawing code for split-screen competitive Tetris.
NO from games.* imports.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
CELL_SIZE = 20
BOARD_COLS = 10
BOARD_ROWS = 20

BOARD_PIXEL_W = BOARD_COLS * CELL_SIZE
BOARD_PIXEL_H = BOARD_ROWS * CELL_SIZE

# Board positions
MARGIN = 20
LEFT_BOARD_X = MARGIN + 20
RIGHT_BOARD_X = WIDTH - MARGIN - 20 - BOARD_PIXEL_W
BOARD_Y = (HEIGHT - TOP_BAR_HEIGHT - BOARD_PIXEL_H) // 2

# Colors
BG_COLOR = (30, 30, 46)
GRID_LINE_COLOR = (45, 45, 65)
LINE_COLOR = (205, 214, 244)
BUTTON_HOVER_COLOR = (88, 91, 112)
STATUS_TEXT_COLOR = (205, 214, 244)
SCORE_COLOR = (249, 226, 175)
BOARD_BG_COLOR = (24, 24, 37)
OVERLAY_COLOR = (30, 30, 46, 200)
GARBAGE_COLOR = (100, 100, 100)
GARBAGE_WARNING_COLOR = (243, 139, 168)

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

GHOST_ALPHA = 60

# Difficulty button colors
DIFF_BUTTON_COLORS = {
    'easy': (166, 227, 161),
    'medium': (249, 226, 175),
    'hard': (243, 139, 168),
}

# Preview piece size
PREVIEW_SIZE = 16

# Tetromino definitions (for next piece preview rendering)
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


def _cell_to_screen(board_x, col, row):
    """Convert board (col, row) to screen center (x, y). Row 0 is bottom."""
    x = board_x + col * CELL_SIZE + CELL_SIZE // 2
    y = BOARD_Y + row * CELL_SIZE + CELL_SIZE // 2
    return x, y


def _draw_board_bg(board_x):
    """Draw the dark board background."""
    cx = board_x + BOARD_PIXEL_W / 2
    cy = BOARD_Y + BOARD_PIXEL_H / 2
    arcade.draw_rect_filled(
        arcade.XYWH(cx, cy, BOARD_PIXEL_W, BOARD_PIXEL_H),
        BOARD_BG_COLOR,
    )


def _draw_grid_lines(board_x):
    """Draw faint grid lines on a board."""
    for c in range(BOARD_COLS + 1):
        x = board_x + c * CELL_SIZE
        arcade.draw_line(x, BOARD_Y, x, BOARD_Y + BOARD_PIXEL_H, GRID_LINE_COLOR, 1)
    for r in range(BOARD_ROWS + 1):
        y = BOARD_Y + r * CELL_SIZE
        arcade.draw_line(board_x, y, board_x + BOARD_PIXEL_W, y, GRID_LINE_COLOR, 1)


def _draw_board_outline(board_x):
    """Draw the board border."""
    cx = board_x + BOARD_PIXEL_W / 2
    cy = BOARD_Y + BOARD_PIXEL_H / 2
    arcade.draw_rect_outline(
        arcade.XYWH(cx, cy, BOARD_PIXEL_W, BOARD_PIXEL_H),
        LINE_COLOR, 2,
    )


def _draw_cell(board_x, col, row, color, outline_color=None):
    """Draw a single cell on a board."""
    x, y = _cell_to_screen(board_x, col, row)
    arcade.draw_rect_filled(
        arcade.XYWH(x, y, CELL_SIZE - 2, CELL_SIZE - 2),
        color,
    )
    if outline_color:
        arcade.draw_rect_outline(
            arcade.XYWH(x, y, CELL_SIZE - 2, CELL_SIZE - 2),
            outline_color, 1,
        )


def _draw_locked_cells(board_x, board_state):
    """Draw all locked cells on the board."""
    for r in range(BOARD_ROWS):
        for c in range(BOARD_COLS):
            color = board_state.board[r][c]
            if color is not None:
                outline = tuple(min(v + 40, 255) for v in color)
                _draw_cell(board_x, c, r, color, outline)


def _draw_current_piece(board_x, board_state):
    """Draw the currently falling piece."""
    color = PIECE_COLORS[board_state.current_type]
    outline = tuple(min(v + 40, 255) for v in color)
    for bc, br in board_state._get_cells(
        board_state.current_type, board_state.rotation,
        board_state.piece_col, board_state.piece_row
    ):
        if 0 <= br < BOARD_ROWS:
            _draw_cell(board_x, bc, br, color, outline)


def _draw_ghost(board_x, board_state):
    """Draw translucent ghost piece showing landing position."""
    ghost_r = board_state._ghost_row()
    if ghost_r == board_state.piece_row:
        return
    base_color = PIECE_COLORS[board_state.current_type]
    ghost_color = (base_color[0], base_color[1], base_color[2], GHOST_ALPHA)
    for bc, br in board_state._get_cells(
        board_state.current_type, board_state.rotation,
        board_state.piece_col, ghost_r
    ):
        if 0 <= br < BOARD_ROWS:
            x, y = _cell_to_screen(board_x, bc, br)
            arcade.draw_rect_filled(
                arcade.XYWH(x, y, CELL_SIZE - 2, CELL_SIZE - 2),
                ghost_color,
            )


def _draw_next_piece(px, py, piece_type):
    """Draw a next piece preview at position (px, py)."""
    shape = TETROMINOES[piece_type][0]
    color = PIECE_COLORS[piece_type]
    outline = tuple(min(v + 40, 255) for v in color)
    for dr, dc in shape:
        x = px + dc * PREVIEW_SIZE + PREVIEW_SIZE // 2
        y = py - dr * PREVIEW_SIZE - PREVIEW_SIZE // 2
        arcade.draw_rect_filled(
            arcade.XYWH(x, y, PREVIEW_SIZE - 2, PREVIEW_SIZE - 2),
            color,
        )
        arcade.draw_rect_outline(
            arcade.XYWH(x, y, PREVIEW_SIZE - 2, PREVIEW_SIZE - 2),
            outline, 1,
        )


def _draw_garbage_indicator(board_x, board_state, side):
    """Draw pending garbage indicator as red bars next to the board."""
    count = board_state.pending_garbage
    if count <= 0:
        return
    bar_w = 6
    if side == 'left':
        x = board_x - bar_w - 2
    else:
        x = board_x + BOARD_PIXEL_W + 2

    for i in range(min(count, BOARD_ROWS)):
        y = BOARD_Y + i * CELL_SIZE + CELL_SIZE // 2
        arcade.draw_rect_filled(
            arcade.XYWH(x + bar_w // 2, y, bar_w, CELL_SIZE - 2),
            GARBAGE_WARNING_COLOR,
        )


def _draw_single_board(board_x, board_state):
    """Draw one complete board with pieces."""
    _draw_board_bg(board_x)
    _draw_grid_lines(board_x)
    _draw_locked_cells(board_x, board_state)
    if not board_state.game_over:
        _draw_ghost(board_x, board_state)
        _draw_current_piece(board_x, board_state)
    _draw_board_outline(board_x)


def _draw_top_bar(game):
    """Draw the top bar with buttons."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT - TOP_BAR_HEIGHT / 2, WIDTH, TOP_BAR_HEIGHT),
        (30, 30, 46, 220),
    )
    game.btn_back.draw(game.btn_back.contains(game.mouse_x, game.mouse_y))
    game.btn_help.draw(game.btn_help.contains(game.mouse_x, game.mouse_y))


def _draw_difficulty_selection(game):
    """Draw the difficulty selection screen."""
    _draw_top_bar(game)
    game.txt_select_title.draw()
    game.txt_select_subtitle.draw()

    # Draw difficulty buttons with colored accents
    for btn, diff_key in [(game.btn_easy, 'easy'), (game.btn_medium, 'medium'), (game.btn_hard, 'hard')]:
        hover = btn.contains(game.mouse_x, game.mouse_y)
        btn.draw(hover)
        # Draw colored accent bar on left side of button
        accent_color = DIFF_BUTTON_COLORS[diff_key]
        bar_x = btn.cx - btn.w / 2 + 4
        arcade.draw_rect_filled(
            arcade.XYWH(bar_x, btn.cy, 4, btn.h - 8),
            accent_color,
        )


def _draw_game_state(game):
    """Draw the full game with both boards."""
    _draw_top_bar(game)

    # Draw both boards
    _draw_single_board(LEFT_BOARD_X, game.player)
    _draw_single_board(RIGHT_BOARD_X, game.ai_board)

    # Draw garbage indicators
    _draw_garbage_indicator(LEFT_BOARD_X, game.player, 'left')
    _draw_garbage_indicator(RIGHT_BOARD_X, game.ai_board, 'right')

    # Labels and scores
    game.txt_player_label.draw()
    game.txt_player_score.text = f"Score: {game.player.score}"
    game.txt_player_score.draw()
    game.txt_player_lines.text = f"Lines: {game.player.lines_cleared}"
    game.txt_player_lines.draw()

    game.txt_ai_label.draw()
    game.txt_ai_score.text = f"Score: {game.ai_board.score}"
    game.txt_ai_score.draw()
    game.txt_ai_lines.text = f"Lines: {game.ai_board.lines_cleared}"
    game.txt_ai_lines.draw()

    # Next piece previews
    game.txt_player_next.draw()
    preview_x = LEFT_BOARD_X + BOARD_PIXEL_W + 8
    preview_y = BOARD_Y + BOARD_PIXEL_H - 20
    _draw_next_piece(preview_x, preview_y, game.player.next_piece_type)

    game.txt_ai_next.draw()
    preview_x = RIGHT_BOARD_X - 78
    preview_y = BOARD_Y + BOARD_PIXEL_H - 20
    _draw_next_piece(preview_x, preview_y, game.ai_board.next_piece_type)

    # Garbage warning text
    if game.player.pending_garbage > 0:
        game.txt_player_garbage.text = f"!{game.player.pending_garbage}"
    else:
        game.txt_player_garbage.text = ""
    game.txt_player_garbage.draw()

    if game.ai_board.pending_garbage > 0:
        game.txt_ai_garbage.text = f"!{game.ai_board.pending_garbage}"
    else:
        game.txt_ai_garbage.text = ""
    game.txt_ai_garbage.draw()

    # VS text in center
    game.txt_vs.draw()

    # Difficulty indicator
    game.txt_difficulty.draw()


def _draw_result_overlay(game):
    """Draw win/lose overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        OVERLAY_COLOR,
    )

    if game.winner == 'player':
        game.txt_result.text = "YOU WIN!"
        game.txt_result.color = (166, 227, 161)
    else:
        game.txt_result.text = "AI WINS!"
        game.txt_result.color = (243, 139, 168)

    game.txt_result.draw()
    game.txt_result_hint.draw()


def draw(game):
    """Render the entire Tetris VS game state."""
    if game.selecting_difficulty:
        _draw_difficulty_selection(game)
        return

    _draw_game_state(game)

    if not game.game_active and game.winner is not None:
        _draw_result_overlay(game)
