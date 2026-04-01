"""
Renderer for the Chess game.
All arcade drawing calls for Chess live here.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Board drawing constants
BOARD_SIZE = 8
CELL_SIZE = 62
BOARD_PIXEL = BOARD_SIZE * CELL_SIZE  # 496
BOARD_LEFT = (WIDTH - BOARD_PIXEL) // 2
BOARD_BOTTOM = 30

# Colors
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
SELECT_HIGHLIGHT = (255, 255, 0, 120)
VALID_MOVE_COLOR = (0, 180, 0, 140)
VALID_CAPTURE_COLOR = (220, 50, 50, 140)
LAST_MOVE_COLOR = (170, 162, 58, 100)
CHECK_COLOR = (255, 0, 0, 150)
OVERLAY_BG = (0, 0, 0, 180)
SIDEBAR_BG = (40, 40, 40)

# Button dimensions
BUTTON_W = 100
BUTTON_H = 36

# Game states
STATE_DIFFICULTY = "difficulty"
STATE_PLAYER_TURN = "player_turn"
STATE_AI_THINKING = "ai_thinking"
STATE_PROMOTION = "promotion"
STATE_GAME_OVER = "game_over"

# Unicode chess pieces
UNICODE_PIECES = {
    'K': '\u2654', 'Q': '\u2655', 'R': '\u2656', 'B': '\u2657', 'N': '\u2658', 'P': '\u2659',
    'k': '\u265A', 'q': '\u265B', 'r': '\u265C', 'b': '\u265D', 'n': '\u265E', 'p': '\u265F',
}

# Piece order for captured display
PIECE_ORDER = {'Q': 0, 'R': 1, 'B': 2, 'N': 3, 'P': 4,
               'q': 0, 'r': 1, 'b': 2, 'n': 3, 'p': 4}


def board_to_screen(row, col):
    """Convert board coordinates (row, col) to screen pixel center."""
    x = BOARD_LEFT + col * CELL_SIZE + CELL_SIZE // 2
    y = BOARD_BOTTOM + (7 - row) * CELL_SIZE + CELL_SIZE // 2
    return x, y


def screen_to_board(x, y):
    """Convert screen pixel to board coordinates. Returns (row, col) or None."""
    col = (x - BOARD_LEFT) // CELL_SIZE
    row = 7 - (y - BOARD_BOTTOM) // CELL_SIZE
    if 0 <= row < 8 and 0 <= col < 8:
        return int(row), int(col)
    return None


def draw(game):
    """Render the entire Chess game state."""
    if game.state == STATE_DIFFICULTY:
        _draw_difficulty_screen(game)
        return

    _draw_sidebar(game)
    _draw_board(game)
    _draw_highlights(game)
    _draw_pieces(game)
    _draw_buttons(game)

    if game.state == STATE_PROMOTION:
        _draw_promotion_picker(game)
    if game.state == STATE_GAME_OVER:
        _draw_overlay(game)


def _draw_difficulty_screen(game):
    """Draw the difficulty selection screen."""
    game.txt_diff_title.draw()
    game.txt_diff_subtitle.draw()

    for key in ['easy', 'medium', 'hard']:
        bx, by = game.diff_buttons[key]
        color = {'easy': arcade.color.DARK_GREEN, 'medium': arcade.color.DARK_GOLDENROD,
                 'hard': arcade.color.DARK_RED}[key]
        arcade.draw_rect_filled(arcade.XYWH(bx, by, 180, 50), color)
        arcade.draw_rect_outline(arcade.XYWH(bx, by, 180, 50), arcade.color.WHITE, 2)
        game.txt_diff_buttons[key].draw()


def _draw_sidebar(game):
    """Draw captured pieces on the sides."""
    # Left sidebar: pieces captured by white (black pieces)
    sidebar_x = BOARD_LEFT - 50
    arcade.draw_rect_filled(
        arcade.XYWH(sidebar_x, HEIGHT // 2, 60, BOARD_PIXEL),
        SIDEBAR_BG,
    )
    game.txt_captured_white_label.draw()
    cap_white, cap_black = game.captured_by_white, game.captured_by_black
    _draw_captured_list(cap_white, sidebar_x, BOARD_BOTTOM + BOARD_PIXEL - 60, is_white_pieces=False)

    # Right sidebar: pieces captured by black (white pieces)
    sidebar_x2 = BOARD_LEFT + BOARD_PIXEL + 50
    arcade.draw_rect_filled(
        arcade.XYWH(sidebar_x2, HEIGHT // 2, 60, BOARD_PIXEL),
        SIDEBAR_BG,
    )
    game.txt_captured_black_label.draw()
    _draw_captured_list(cap_black, sidebar_x2, BOARD_BOTTOM + BOARD_PIXEL - 60, is_white_pieces=True)


def _draw_captured_list(pieces, cx, start_y, is_white_pieces):
    """Draw a vertical list of captured pieces."""
    sorted_pieces = sorted(pieces, key=lambda p: PIECE_ORDER.get(p, 5))
    y = start_y
    for piece in sorted_pieces:
        char = UNICODE_PIECES.get(piece, '?')
        color = arcade.color.WHITE if is_white_pieces else arcade.color.BLACK
        t = arcade.Text(char, cx, y, color, 22, anchor_x="center", anchor_y="center")
        t.draw()
        y -= 24


def _draw_board(game):
    """Draw the 8x8 chess board."""
    for row in range(8):
        for col in range(8):
            x, y = board_to_screen(row, col)
            is_light = (row + col) % 2 == 0
            color = LIGHT_SQUARE if is_light else DARK_SQUARE
            arcade.draw_rect_filled(
                arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE),
                color,
            )

    # Rank and file labels
    for i in range(8):
        # File labels (a-h) at bottom
        x = BOARD_LEFT + i * CELL_SIZE + CELL_SIZE // 2
        y = BOARD_BOTTOM - 12
        game.file_labels[i].draw()
        # Rank labels (1-8) on left
        game.rank_labels[i].draw()


def _draw_highlights(game):
    """Draw selection highlight, valid moves, last move, and check indicators."""
    # Last move highlight
    if game.last_move:
        for sq in game.last_move:
            x, y = board_to_screen(sq[0], sq[1])
            arcade.draw_rect_filled(
                arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE),
                LAST_MOVE_COLOR,
            )

    # Selected piece highlight
    if game.selected is not None:
        x, y = board_to_screen(game.selected[0], game.selected[1])
        arcade.draw_rect_filled(
            arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE),
            SELECT_HIGHLIGHT,
        )

    # Valid move dots/highlights
    for dest_r, dest_c, promo in game.valid_moves:
        x, y = board_to_screen(dest_r, dest_c)
        target = game.board[dest_r][dest_c]
        if target is not None:
            # Capture: highlight square
            arcade.draw_rect_filled(
                arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE),
                VALID_CAPTURE_COLOR,
            )
        else:
            # Empty: draw dot
            arcade.draw_circle_filled(x, y, 8, VALID_MOVE_COLOR)

    # Check highlight
    if game.in_check and game.state != STATE_GAME_OVER and game.check_square:
        x, y = board_to_screen(game.check_square[0], game.check_square[1])
        arcade.draw_rect_filled(
            arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE),
            CHECK_COLOR,
        )


def _draw_pieces(game):
    """Draw all pieces on the board using unicode characters."""
    for row in range(8):
        for col in range(8):
            piece = game.board[row][col]
            if piece is None:
                continue
            x, y = board_to_screen(row, col)
            char = UNICODE_PIECES.get(piece, '?')
            # Use white/cream for white pieces, black for black pieces with outline effect
            if piece.isupper():
                # White piece: draw with dark outline
                for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                    t = arcade.Text(char, x + dx, y + dy, (50, 50, 50), 38,
                                    anchor_x="center", anchor_y="center")
                    t.draw()
                t = arcade.Text(char, x, y, (255, 255, 240), 38,
                                anchor_x="center", anchor_y="center")
                t.draw()
            else:
                # Black piece: draw with light outline
                for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                    t = arcade.Text(char, x + dx, y + dy, (200, 200, 200), 38,
                                    anchor_x="center", anchor_y="center")
                    t.draw()
                t = arcade.Text(char, x, y, (30, 30, 30), 38,
                                anchor_x="center", anchor_y="center")
                t.draw()


def _draw_buttons(game):
    """Draw Back, New Game buttons and title/status."""
    # Back button
    bx, by = 60, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.DARK_GRAY)
    arcade.draw_rect_outline(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.WHITE, 2)
    game.txt_back.draw()

    # New Game button
    nx, ny = WIDTH - 70, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.WHITE, 2)
    game.txt_new_game.draw()

    # Title
    game.txt_title.draw()

    # Turn indicator
    if game.state == STATE_PLAYER_TURN:
        game.txt_turn_player.draw()
    elif game.state == STATE_AI_THINKING:
        game.txt_turn_ai.draw()


def _draw_promotion_picker(game):
    """Draw promotion piece selection overlay."""
    # Semi-transparent background
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT),
        (0, 0, 0, 120),
    )

    # Picker box
    box_w, box_h = 280, 80
    bx, by = WIDTH // 2, HEIGHT // 2
    arcade.draw_rect_filled(arcade.XYWH(bx, by, box_w, box_h), (60, 60, 60))
    arcade.draw_rect_outline(arcade.XYWH(bx, by, box_w, box_h), arcade.color.WHITE, 2)

    game.txt_promo_title.draw()

    promo_pieces = ['Q', 'R', 'B', 'N']
    start_x = bx - 90
    for i, p in enumerate(promo_pieces):
        px = start_x + i * 60
        py = by - 5
        char = UNICODE_PIECES[p]
        # Highlight on hover
        arcade.draw_rect_filled(arcade.XYWH(px, py, 50, 50), (80, 80, 80))
        arcade.draw_rect_outline(arcade.XYWH(px, py, 50, 50), arcade.color.WHITE, 1)
        t = arcade.Text(char, px, py, (255, 255, 240), 32,
                        anchor_x="center", anchor_y="center")
        t.draw()


def _draw_overlay(game):
    """Draw game over overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT),
        OVERLAY_BG,
    )
    game.txt_game_over.draw()
    game.txt_game_over_sub.draw()

    # Play Again button
    bx, by = WIDTH // 2, HEIGHT // 2 - 60
    arcade.draw_rect_filled(arcade.XYWH(bx, by, 160, 44), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(bx, by, 160, 44), arcade.color.WHITE, 2)
    game.txt_play_again.draw()
