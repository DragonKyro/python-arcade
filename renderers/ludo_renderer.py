"""
Renderer for the Ludo game view.
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
PHASE_ROLL = "roll"
PHASE_PICK = "pick"
PHASE_ANIMATING = "animating"
PHASE_GAME_OVER = "game_over"

# Button layout
BUTTON_W = 100
BUTTON_H = 36
ROLL_BTN_W = 120
ROLL_BTN_H = 44
ROLL_BTN_X = 690
ROLL_BTN_Y = 300

# Board layout
BOARD_CX = 300
BOARD_CY = 300
CELL_SIZE = 36
BOARD_CELLS = 15  # 15x15 grid
BOARD_LEFT = BOARD_CX - (BOARD_CELLS * CELL_SIZE) // 2
BOARD_BOTTOM = BOARD_CY - (BOARD_CELLS * CELL_SIZE) // 2

# Piece size
PIECE_RADIUS = 12

# Sidebar
SIDEBAR_X = 640

# Player colors
PLAYER_COLORS = {
    0: arcade.color.RED,
    1: arcade.color.BLUE,
    2: arcade.color.GREEN,
    3: arcade.color.YELLOW,
}
PLAYER_COLOR_NAMES = {0: "Red", 1: "Blue", 2: "Green", 3: "Yellow"}
PLAYER_LIGHT_COLORS = {
    0: (255, 180, 180),
    1: (180, 180, 255),
    2: (180, 255, 180),
    3: (255, 255, 180),
}

# The main track: 52 squares arranged around the cross-shaped board.
# Each entry is (grid_col, grid_row) on the 15x15 grid (0-indexed from bottom-left).
# The track goes clockwise: right along bottom, up on right, left along top, down on left.
TRACK_COORDS = [
    # Bottom-left to right (player 0 / Red entry zone)
    (1, 6), (2, 6), (3, 6), (4, 6), (5, 6),
    # Up the right-of-center column
    (6, 5), (6, 4), (6, 3), (6, 2), (6, 1), (6, 0),
    # Cross to right column
    (7, 0), (8, 0),
    # Down on the far right
    (8, 1), (8, 2), (8, 3), (8, 4), (8, 5),
    # Right to left along upper portion (player 1 / Blue entry zone)
    (9, 6), (10, 6), (11, 6), (12, 6), (13, 6), (14, 6),
    # Up to top
    (14, 7), (14, 8),
    # Left along top
    (13, 8), (12, 8), (11, 8), (10, 8), (9, 8),
    # Top-center column upward (player 2 / Green entry zone)
    (8, 9), (8, 10), (8, 11), (8, 12), (8, 13), (8, 14),
    # Cross to left column
    (7, 14), (6, 14),
    # Down on the far left side
    (6, 13), (6, 12), (6, 11), (6, 10), (6, 9),
    # Left along lower portion (player 3 / Yellow entry zone)
    (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8),
    # Down to bottom
    (0, 7), (0, 6),
]

# Entry points: track index where each player enters
PLAYER_ENTRY = {0: 0, 1: 13, 2: 26, 3: 39}

# Finish lane coords for each player (6 cells leading to center)
FINISH_LANES = {
    0: [(1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7)],
    1: [(7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6)],
    2: [(13, 7), (12, 7), (11, 7), (10, 7), (9, 7), (8, 7)],
    3: [(7, 13), (7, 12), (7, 11), (7, 10), (7, 9), (7, 8)],
}

# Home base centers (grid coords for the 6x6 home area corners)
HOME_BASES = {
    0: (3, 3),    # bottom-left
    1: (12, 3),   # bottom-right (was top-right, corrected for Blue)
    2: (12, 12),  # top-right (was bottom-right, corrected for Green)
    3: (3, 12),   # top-left
}

# Safe squares (track indices)
SAFE_SQUARES = {0, 8, 13, 21, 26, 34, 39, 47}

# Pip layouts for dice rendering
_S = 0.55
PIP_LAYOUTS = {
    1: [(0, 0)],
    2: [(-_S, _S), (_S, -_S)],
    3: [(-_S, _S), (0, 0), (_S, -_S)],
    4: [(-_S, _S), (_S, _S), (-_S, -_S), (_S, -_S)],
    5: [(-_S, _S), (_S, _S), (0, 0), (-_S, -_S), (_S, -_S)],
    6: [(-_S, _S), (_S, _S), (-_S, 0), (_S, 0), (-_S, -_S), (_S, -_S)],
}


def grid_to_pixel(col, row):
    """Convert grid coords to pixel center."""
    x = BOARD_LEFT + col * CELL_SIZE + CELL_SIZE / 2
    y = BOARD_BOTTOM + row * CELL_SIZE + CELL_SIZE / 2
    return x, y


def draw(game):
    """Render the entire Ludo game state."""
    _draw_buttons(game)

    if game.phase == PHASE_SETUP:
        _draw_setup(game)
    else:
        _draw_board(game)
        _draw_home_bases(game)
        _draw_finish_lanes(game)
        _draw_pieces(game)
        _draw_sidebar(game)
        if game.phase == PHASE_GAME_OVER:
            _draw_game_over(game)


def _draw_buttons(game):
    """Draw top bar buttons."""
    bx, by = 60, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.DARK_GRAY)
    arcade.draw_rect_outline(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.WHITE, 2)
    game.txt_btn_back.draw()

    nx, ny = WIDTH - 70, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.WHITE, 2)
    game.txt_btn_new_game.draw()

    hx, hy = WIDTH - 145, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(hx, hy, 40, BUTTON_H), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(hx, hy, 40, BUTTON_H), arcade.color.WHITE, 2)
    game.txt_btn_help.draw()

    game.txt_title.draw()


def _draw_setup(game):
    """Draw player count selection."""
    game.txt_setup_prompt.draw()

    for i in range(3):
        bx = WIDTH // 2 - 80 + i * 80
        by = HEIGHT // 2 + 20
        num = i + 2
        selected = num == game.pending_num_players
        bg = arcade.color.BLUE if selected else arcade.color.DARK_BLUE
        arcade.draw_rect_filled(arcade.XYWH(bx, by, 60, 44), bg)
        arcade.draw_rect_outline(arcade.XYWH(bx, by, 60, 44), arcade.color.WHITE, 2)
        game.txt_setup_btn_labels[i].draw()

    if game.pending_num_players > 0:
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

        sx, sy = WIDTH // 2, HEIGHT // 2 - 120
        arcade.draw_rect_filled(arcade.XYWH(sx, sy, 140, 44), arcade.color.DARK_GREEN)
        arcade.draw_rect_outline(arcade.XYWH(sx, sy, 140, 44), arcade.color.WHITE, 2)
        game.txt_start_btn.draw()


def _draw_board(game):
    """Draw the Ludo cross-shaped board."""
    # Draw background
    arcade.draw_rect_filled(
        arcade.XYWH(BOARD_CX, BOARD_CY, BOARD_CELLS * CELL_SIZE + 4, BOARD_CELLS * CELL_SIZE + 4),
        (60, 60, 60)
    )

    # Draw track cells
    for i, (col, row) in enumerate(TRACK_COORDS):
        x, y = grid_to_pixel(col, row)
        color = (220, 220, 220)
        # Color safe squares
        if i in SAFE_SQUARES:
            color = (200, 200, 240)
        arcade.draw_rect_filled(arcade.XYWH(x, y, CELL_SIZE - 1, CELL_SIZE - 1), color)
        arcade.draw_rect_outline(arcade.XYWH(x, y, CELL_SIZE - 1, CELL_SIZE - 1), (100, 100, 100), 1)

    # Color entry squares
    for player_id, entry_idx in PLAYER_ENTRY.items():
        if player_id < game.num_players:
            col, row = TRACK_COORDS[entry_idx]
            x, y = grid_to_pixel(col, row)
            arcade.draw_rect_filled(
                arcade.XYWH(x, y, CELL_SIZE - 1, CELL_SIZE - 1),
                PLAYER_LIGHT_COLORS[player_id]
            )
            arcade.draw_rect_outline(
                arcade.XYWH(x, y, CELL_SIZE - 1, CELL_SIZE - 1),
                PLAYER_COLORS[player_id], 2
            )

    # Center square
    cx, cy = grid_to_pixel(7, 7)
    arcade.draw_rect_filled(arcade.XYWH(cx, cy, CELL_SIZE * 2, CELL_SIZE * 2), (180, 180, 180))
    arcade.draw_rect_outline(arcade.XYWH(cx, cy, CELL_SIZE * 2, CELL_SIZE * 2), (100, 100, 100), 2)


def _draw_home_bases(game):
    """Draw the four home bases."""
    for player_id in range(game.num_players):
        center_col, center_row = HOME_BASES[player_id]
        cx, cy = grid_to_pixel(center_col, center_row)
        color = PLAYER_LIGHT_COLORS[player_id]
        border = PLAYER_COLORS[player_id]
        size = CELL_SIZE * 5
        arcade.draw_rect_filled(arcade.XYWH(cx, cy, size, size), color)
        arcade.draw_rect_outline(arcade.XYWH(cx, cy, size, size), border, 3)

        # Draw home spots (4 circles for pieces)
        offsets = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
        for k, (dx, dy) in enumerate(offsets):
            sx = cx + dx * CELL_SIZE * 1.2
            sy = cy + dy * CELL_SIZE * 1.2
            arcade.draw_circle_filled(sx, sy, PIECE_RADIUS + 2, (255, 255, 255, 100))
            arcade.draw_circle_outline(sx, sy, PIECE_RADIUS + 2, border, 2)


def _draw_finish_lanes(game):
    """Draw the finish lanes for each player."""
    for player_id in range(game.num_players):
        color = PLAYER_LIGHT_COLORS[player_id]
        border = PLAYER_COLORS[player_id]
        for col, row in FINISH_LANES[player_id]:
            x, y = grid_to_pixel(col, row)
            arcade.draw_rect_filled(arcade.XYWH(x, y, CELL_SIZE - 1, CELL_SIZE - 1), color)
            arcade.draw_rect_outline(arcade.XYWH(x, y, CELL_SIZE - 1, CELL_SIZE - 1), border, 2)


def _draw_pieces(game):
    """Draw all player pieces."""
    # Collect positions to handle stacking
    track_positions = {}  # (col, row) -> list of (player_id, piece_idx)

    for player_id in range(game.num_players):
        for piece_idx, piece in enumerate(game.pieces[player_id]):
            state = piece["state"]
            if state == "home":
                _draw_home_piece(game, player_id, piece_idx)
            elif state == "track":
                track_pos = piece["track_pos"]
                col, row = TRACK_COORDS[track_pos % len(TRACK_COORDS)]
                key = (col, row)
                if key not in track_positions:
                    track_positions[key] = []
                track_positions[key].append((player_id, piece_idx))
            elif state == "finish_lane":
                fp = piece["finish_pos"]
                if 0 <= fp < len(FINISH_LANES[player_id]):
                    col, row = FINISH_LANES[player_id][fp]
                    key = (col, row)
                    if key not in track_positions:
                        track_positions[key] = []
                    track_positions[key].append((player_id, piece_idx))
            # "finished" pieces are not drawn on the board

    # Draw track/finish pieces with offset for stacking
    for (col, row), occupants in track_positions.items():
        x, y = grid_to_pixel(col, row)
        n = len(occupants)
        for k, (player_id, piece_idx) in enumerate(occupants):
            if n == 1:
                ox, oy = 0, 0
            else:
                angle = 2 * math.pi * k / n
                ox = math.cos(angle) * 8
                oy = math.sin(angle) * 8
            color = PLAYER_COLORS[player_id]
            # Highlight selectable pieces
            is_selectable = (
                game.phase == PHASE_PICK
                and game.current_player == 0
                and player_id == 0
                and piece_idx in game.valid_moves
            )
            arcade.draw_circle_filled(x + ox, y + oy, PIECE_RADIUS, color)
            outline = arcade.color.WHITE
            thickness = 2
            if is_selectable:
                outline = arcade.color.YELLOW
                thickness = 3
            arcade.draw_circle_outline(x + ox, y + oy, PIECE_RADIUS, outline, thickness)


def _draw_home_piece(game, player_id, piece_idx):
    """Draw a piece in its home base."""
    center_col, center_row = HOME_BASES[player_id]
    cx, cy = grid_to_pixel(center_col, center_row)
    offsets = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
    dx, dy = offsets[piece_idx]
    px = cx + dx * CELL_SIZE * 1.2
    py = cy + dy * CELL_SIZE * 1.2
    color = PLAYER_COLORS[player_id]

    is_selectable = (
        game.phase == PHASE_PICK
        and game.current_player == 0
        and player_id == 0
        and piece_idx in game.valid_moves
    )

    arcade.draw_circle_filled(px, py, PIECE_RADIUS, color)
    outline = arcade.color.WHITE
    thickness = 2
    if is_selectable:
        outline = arcade.color.YELLOW
        thickness = 3
    arcade.draw_circle_outline(px, py, PIECE_RADIUS, outline, thickness)


def _draw_sidebar(game):
    """Draw sidebar with turn info, dice, and player status."""
    x = SIDEBAR_X

    # Turn indicator
    game.txt_turn.draw()

    # Dice
    if game.dice_result > 0:
        _draw_die(x + 50, 420, game.dice_result)
        game.txt_dice_label.draw()

    # Roll button
    show_roll = (
        game.phase == PHASE_ROLL
        and game.current_player == 0
    )
    if show_roll:
        bx, by = ROLL_BTN_X, ROLL_BTN_Y
        arcade.draw_rect_filled(arcade.XYWH(bx, by, ROLL_BTN_W, ROLL_BTN_H), arcade.color.DARK_BLUE)
        arcade.draw_rect_outline(arcade.XYWH(bx, by, ROLL_BTN_W, ROLL_BTN_H), arcade.color.WHITE, 2)
        game.txt_roll_btn.draw()

    # Pick instruction
    if game.phase == PHASE_PICK and game.current_player == 0:
        game.txt_pick_instr.draw()

    # Player status
    for i in range(game.num_players):
        py = 230 - i * 60
        color = PLAYER_COLORS[i]

        arcade.draw_circle_filled(x, py, 10, color)
        arcade.draw_circle_outline(x, py, 10, arcade.color.WHITE, 2)

        game.txt_player_infos[i].x = x + 20
        game.txt_player_infos[i].y = py + 8
        name = "You" if i == 0 else f"AI {i}"
        finished = sum(1 for p in game.pieces[i] if p["state"] == "finished")
        game.txt_player_infos[i].text = f"{name} ({PLAYER_COLOR_NAMES[i]})"
        if i == game.current_player and game.phase != PHASE_GAME_OVER:
            game.txt_player_infos[i].color = arcade.color.YELLOW
        else:
            game.txt_player_infos[i].color = arcade.color.WHITE
        game.txt_player_infos[i].draw()

        game.txt_player_finished[i].x = x + 20
        game.txt_player_finished[i].y = py - 10
        game.txt_player_finished[i].text = f"Finished: {finished}/4"
        game.txt_player_finished[i].draw()

    # Consecutive sixes warning
    if game.consecutive_sixes > 0 and game.phase != PHASE_GAME_OVER:
        game.txt_sixes_warning.text = f"Consecutive 6s: {game.consecutive_sixes}"
        game.txt_sixes_warning.draw()


def _draw_die(cx, cy, face):
    """Draw a single die."""
    size = 50
    half = size // 2
    arcade.draw_rect_filled(arcade.XYWH(cx, cy, size, size), (240, 240, 240))
    arcade.draw_rect_outline(arcade.XYWH(cx, cy, size, size), (60, 60, 60), 2)

    pip_r = 5
    pip_c = (30, 30, 30)

    if face in PIP_LAYOUTS:
        for px, py in PIP_LAYOUTS[face]:
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
