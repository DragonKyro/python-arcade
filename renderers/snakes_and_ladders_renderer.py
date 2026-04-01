"""
Renderer for the Snakes & Ladders game view.
All drawing calls are centralized here.
NO ``from games.*`` imports -- constants are defined locally.
"""

import arcade
import math

# Window constants
WIDTH = 800
HEIGHT = 600

# Game phases
PHASE_SETUP = "setup"
PHASE_PLAYING = "playing"
PHASE_GAME_OVER = "game_over"

# Board layout
BOARD_SIZE = 10
BOARD_LEFT = 50
BOARD_BOTTOM = 50
CELL_SIZE = 50
BOARD_RIGHT = BOARD_LEFT + BOARD_SIZE * CELL_SIZE
BOARD_TOP = BOARD_BOTTOM + BOARD_SIZE * CELL_SIZE

# Button layout
BUTTON_W = 100
BUTTON_H = 36
ROLL_BTN_W = 120
ROLL_BTN_H = 44
ROLL_BTN_X = 660
ROLL_BTN_Y = 400

# Player piece radius
PIECE_RADIUS = 10

# Sidebar
SIDEBAR_X = 620

# Colors for up to 6 players
PLAYER_COLORS = [
    arcade.color.RED,
    arcade.color.BLUE,
    arcade.color.GREEN,
    arcade.color.YELLOW,
    arcade.color.PURPLE,
    arcade.color.ORANGE,
]

PLAYER_COLOR_NAMES = ["Red", "Blue", "Green", "Yellow", "Purple", "Orange"]

# Board cell colors
CELL_LIGHT = (240, 230, 210)
CELL_DARK = (210, 195, 170)

# Snakes and ladders (defined here as constants for rendering)
LADDERS = {
    2: 38, 7: 14, 8: 31, 15: 26,
    21: 42, 28: 84, 36: 44, 51: 67,
}
SNAKES = {
    16: 6, 46: 25, 49: 11, 62: 19,
    64: 60, 74: 53, 89: 68, 95: 75,
    99: 80,
}

LADDER_COLOR = (34, 139, 34)
SNAKE_COLOR = (178, 34, 34)


def square_to_xy(square):
    """Convert a board square (1-100) to pixel (cx, cy)."""
    idx = square - 1
    row = idx // BOARD_SIZE
    col = idx % BOARD_SIZE
    # Snaking path: even rows left-to-right, odd rows right-to-left
    if row % 2 == 1:
        col = BOARD_SIZE - 1 - col
    x = BOARD_LEFT + col * CELL_SIZE + CELL_SIZE / 2
    y = BOARD_BOTTOM + row * CELL_SIZE + CELL_SIZE / 2
    return x, y


def draw(game):
    """Render the entire Snakes & Ladders game state."""
    _draw_buttons(game)

    if game.phase == PHASE_SETUP:
        _draw_setup(game)
    elif game.phase in (PHASE_PLAYING, PHASE_GAME_OVER):
        _draw_board(game)
        _draw_snakes_and_ladders()
        _draw_pieces(game)
        _draw_sidebar(game)
        if game.phase == PHASE_GAME_OVER:
            _draw_game_over(game)


def _draw_buttons(game):
    """Draw top bar buttons."""
    # Back
    bx, by = 60, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.DARK_GRAY)
    arcade.draw_rect_outline(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.WHITE, 2)
    game.txt_btn_back.draw()

    # New Game
    nx, ny = WIDTH - 70, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.WHITE, 2)
    game.txt_btn_new_game.draw()

    # Help
    hx, hy = WIDTH - 145, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(hx, hy, 40, BUTTON_H), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(hx, hy, 40, BUTTON_H), arcade.color.WHITE, 2)
    game.txt_btn_help.draw()

    # Title
    game.txt_title.draw()


def _draw_setup(game):
    """Draw the player count selection screen."""
    game.txt_setup_prompt.draw()

    for i in range(5):
        bx = WIDTH // 2 - 160 + i * 80
        by = HEIGHT // 2 + 20
        selected = (i + 2) == game.pending_num_players
        bg = arcade.color.BLUE if selected else arcade.color.DARK_BLUE
        arcade.draw_rect_filled(arcade.XYWH(bx, by, 60, 44), bg)
        arcade.draw_rect_outline(arcade.XYWH(bx, by, 60, 44), arcade.color.WHITE, 2)
        game.txt_setup_btn_labels[i].draw()

    if game.pending_num_players > 0:
        # Player color preview
        py = HEIGHT // 2 - 40
        game.txt_color_preview.draw()
        for i in range(game.pending_num_players):
            cx = WIDTH // 2 - (game.pending_num_players - 1) * 30 + i * 60
            color = PLAYER_COLORS[i]
            arcade.draw_circle_filled(cx, py - 30, 14, color)
            arcade.draw_circle_outline(cx, py - 30, 14, arcade.color.WHITE, 2)
            label = "You" if i == 0 else f"AI {i}"
            game.txt_color_labels[i].text = label
            game.txt_color_labels[i].x = cx
            game.txt_color_labels[i].y = py - 55
            game.txt_color_labels[i].draw()

        # Start button
        sx, sy = WIDTH // 2, HEIGHT // 2 - 120
        arcade.draw_rect_filled(arcade.XYWH(sx, sy, 140, 44), arcade.color.DARK_GREEN)
        arcade.draw_rect_outline(arcade.XYWH(sx, sy, 140, 44), arcade.color.WHITE, 2)
        game.txt_start_btn.draw()


def _draw_board(game):
    """Draw the 10x10 grid."""
    for sq in range(1, 101):
        idx = sq - 1
        row = idx // BOARD_SIZE
        col = idx % BOARD_SIZE
        if row % 2 == 1:
            col = BOARD_SIZE - 1 - col
        x = BOARD_LEFT + col * CELL_SIZE
        y = BOARD_BOTTOM + row * CELL_SIZE
        color = CELL_LIGHT if (row + col) % 2 == 0 else CELL_DARK
        arcade.draw_rect_filled(
            arcade.XYWH(x + CELL_SIZE / 2, y + CELL_SIZE / 2, CELL_SIZE, CELL_SIZE), color
        )
        arcade.draw_rect_outline(
            arcade.XYWH(x + CELL_SIZE / 2, y + CELL_SIZE / 2, CELL_SIZE, CELL_SIZE),
            (150, 140, 120), 1
        )
        # Square number
        game.txt_square_numbers[sq - 1].x = x + CELL_SIZE / 2
        game.txt_square_numbers[sq - 1].y = y + CELL_SIZE / 2
        game.txt_square_numbers[sq - 1].draw()


def _draw_snakes_and_ladders():
    """Draw ladder and snake connections on the board."""
    for bottom, top in LADDERS.items():
        x1, y1 = square_to_xy(bottom)
        x2, y2 = square_to_xy(top)
        # Draw ladder as two parallel lines
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            continue
        nx = -dy / length * 6
        ny = dx / length * 6
        arcade.draw_line(x1 + nx, y1 + ny, x2 + nx, y2 + ny, LADDER_COLOR, 3)
        arcade.draw_line(x1 - nx, y1 - ny, x2 - nx, y2 - ny, LADDER_COLOR, 3)
        # Rungs
        steps = max(2, int(length / 25))
        for s in range(1, steps):
            t = s / steps
            rx = x1 + dx * t
            ry = y1 + dy * t
            arcade.draw_line(rx + nx, ry + ny, rx - nx, ry - ny, LADDER_COLOR, 2)

    for head, tail in SNAKES.items():
        x1, y1 = square_to_xy(head)
        x2, y2 = square_to_xy(tail)
        # Draw snake as a thick wavy line
        arcade.draw_line(x1, y1, x2, y2, SNAKE_COLOR, 4)
        # Snake head indicator
        arcade.draw_circle_filled(x1, y1, 5, SNAKE_COLOR)
        # Snake tail indicator
        arcade.draw_circle_filled(x2, y2, 3, (200, 80, 80))


def _draw_pieces(game):
    """Draw all player pieces on the board."""
    # Count pieces per square for offset
    square_counts = {}
    for i, pos in enumerate(game.positions):
        if pos < 1:
            continue
        if pos not in square_counts:
            square_counts[pos] = []
        square_counts[pos].append(i)

    for sq, player_indices in square_counts.items():
        bx, by = square_to_xy(sq)
        n = len(player_indices)
        for k, pi in enumerate(player_indices):
            # Offset pieces so they don't overlap
            if n == 1:
                ox, oy = 0, 0
            else:
                angle = 2 * math.pi * k / n
                ox = math.cos(angle) * 12
                oy = math.sin(angle) * 12
            color = PLAYER_COLORS[pi % len(PLAYER_COLORS)]
            arcade.draw_circle_filled(bx + ox, by + oy, PIECE_RADIUS, color)
            arcade.draw_circle_outline(bx + ox, by + oy, PIECE_RADIUS, arcade.color.WHITE, 2)


def _draw_sidebar(game):
    """Draw the sidebar with turn info, dice, and player positions."""
    x = SIDEBAR_X

    # Turn indicator
    game.txt_turn.draw()

    # Dice result
    if game.dice_result > 0:
        _draw_die(x + 50, 450, game.dice_result)
        game.txt_dice_label.draw()

    # Roll button (only on human turn, game not over)
    if game.phase == PHASE_PLAYING and game.current_player == 0 and not game.waiting_for_animation:
        bx, by = ROLL_BTN_X, ROLL_BTN_Y
        arcade.draw_rect_filled(arcade.XYWH(bx, by, ROLL_BTN_W, ROLL_BTN_H), arcade.color.DARK_BLUE)
        arcade.draw_rect_outline(arcade.XYWH(bx, by, ROLL_BTN_W, ROLL_BTN_H), arcade.color.WHITE, 2)
        game.txt_roll_btn.draw()

    # Player list
    for i in range(game.num_players):
        py = 320 - i * 50
        color = PLAYER_COLORS[i % len(PLAYER_COLORS)]

        # Color circle
        arcade.draw_circle_filled(x, py, 10, color)
        arcade.draw_circle_outline(x, py, 10, arcade.color.WHITE, 2)

        # Name and position
        game.txt_player_infos[i].x = x + 20
        game.txt_player_infos[i].y = py
        name = "You" if i == 0 else f"AI {i}"
        pos = game.positions[i]
        pos_str = "Start" if pos < 1 else str(pos)
        game.txt_player_infos[i].text = f"{name}: {pos_str}"
        if i == game.current_player and game.phase == PHASE_PLAYING:
            game.txt_player_infos[i].color = arcade.color.YELLOW
        else:
            game.txt_player_infos[i].color = arcade.color.WHITE
        game.txt_player_infos[i].draw()


def _draw_die(cx, cy, face):
    """Draw a single die showing the given face value."""
    size = 50
    half = size // 2
    arcade.draw_rect_filled(arcade.XYWH(cx, cy, size, size), (240, 240, 240))
    arcade.draw_rect_outline(arcade.XYWH(cx, cy, size, size), (60, 60, 60), 2)

    pip_r = 5
    pip_c = (30, 30, 30)
    s = 0.55

    pip_layouts = {
        1: [(0, 0)],
        2: [(-s, s), (s, -s)],
        3: [(-s, s), (0, 0), (s, -s)],
        4: [(-s, s), (s, s), (-s, -s), (s, -s)],
        5: [(-s, s), (s, s), (0, 0), (-s, -s), (s, -s)],
        6: [(-s, s), (s, s), (-s, 0), (s, 0), (-s, -s), (s, -s)],
    }

    if face in pip_layouts:
        for px, py in pip_layouts[face]:
            arcade.draw_circle_filled(cx + px * half, cy + py * half, pip_r, pip_c)


def _draw_game_over(game):
    """Draw game over overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, 420, 140), (0, 0, 0, 200)
    )
    arcade.draw_rect_outline(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, 420, 140), arcade.color.WHITE, 2
    )
    game.txt_game_over_msg.draw()
    game.txt_game_over_hint.draw()
