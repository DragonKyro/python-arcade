"""Renderer for Towers of Hanoi -- all drawing code lives here."""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout constants
TOP_BAR_HEIGHT = 50
BOTTOM_BAR_HEIGHT = 60

# Game states
PLAYING = 0
WON = 1

# Peg layout
PEG_Y_BASE = 100
PEG_HEIGHT = 250
PEG_WIDTH = 10
PEG_SPACING = 240
PEG_START_X = 160

# Disk constants
MAX_DISK_WIDTH = 180
MIN_DISK_WIDTH = 60
DISK_HEIGHT = 28
DISK_GAP = 2

# Disk colors by size index (0 = smallest)
DISK_COLORS = [
    (230, 80, 80),     # red
    (230, 160, 50),    # orange
    (230, 230, 60),    # yellow
    (80, 200, 80),     # green
    (60, 160, 230),    # blue
    (130, 80, 220),    # purple
    (220, 100, 180),   # pink
]

# Config button layout
CONFIG_Y = HEIGHT - TOP_BAR_HEIGHT - 30
CONFIG_BTN_SIZE = 30


def peg_base_x(peg_index):
    """Return the x center of a peg."""
    return PEG_START_X + peg_index * PEG_SPACING


def disk_width(disk_size, num_disks):
    """Return pixel width for a disk of given size (1=smallest, num_disks=largest)."""
    if num_disks <= 1:
        return MAX_DISK_WIDTH
    frac = (disk_size - 1) / (num_disks - 1)
    return MIN_DISK_WIDTH + frac * (MAX_DISK_WIDTH - MIN_DISK_WIDTH)


def disk_color(disk_size):
    """Return color for a disk by size (1-based)."""
    return DISK_COLORS[(disk_size - 1) % len(DISK_COLORS)]


def peg_disk_position(peg_index, stack_index, num_disks):
    """Return (cx, cy) for a disk on a peg at given stack index (0=bottom)."""
    cx = peg_base_x(peg_index)
    cy = PEG_Y_BASE + (stack_index + 0.5) * (DISK_HEIGHT + DISK_GAP)
    return cx, cy


def draw(game):
    """Render the Towers of Hanoi game state."""
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

    # Minimum moves
    min_moves = (2 ** game.num_disks) - 1
    game.txt_min_moves.text = f"Min: {min_moves}"
    game.txt_min_moves.draw()

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

    # --- Disk count selector ---
    for i, n in enumerate(range(3, 8)):
        bx = 250 + i * (CONFIG_BTN_SIZE + 10)
        by = CONFIG_Y
        selected = (n == game.num_disks)
        color = (80, 140, 220) if selected else (70, 70, 80)
        arcade.draw_rect_filled(
            arcade.XYWH(bx, by, CONFIG_BTN_SIZE, CONFIG_BTN_SIZE),
            color,
        )
        arcade.draw_rect_outline(
            arcade.XYWH(bx, by, CONFIG_BTN_SIZE, CONFIG_BTN_SIZE),
            arcade.color.WHITE,
        )
        game.txt_disk_counts[i].draw()

    game.txt_disks_label.draw()

    # --- Base platform ---
    platform_y = PEG_Y_BASE - 10
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, platform_y, 700, 12),
        (100, 80, 60),
    )

    # --- Pegs ---
    for i in range(3):
        px = peg_base_x(i)
        arcade.draw_rect_filled(
            arcade.XYWH(px, PEG_Y_BASE + PEG_HEIGHT / 2, PEG_WIDTH, PEG_HEIGHT),
            (140, 110, 80),
        )

    # --- Disks on pegs ---
    for peg_idx in range(3):
        for stack_idx, d_size in enumerate(game.pegs[peg_idx]):
            cx, cy = peg_disk_position(peg_idx, stack_idx, game.num_disks)
            dw = disk_width(d_size, game.num_disks)
            dc = disk_color(d_size)
            arcade.draw_rect_filled(
                arcade.XYWH(cx, cy, dw, DISK_HEIGHT),
                dc,
            )
            arcade.draw_rect_outline(
                arcade.XYWH(cx, cy, dw, DISK_HEIGHT),
                (255, 255, 255, 80),
                border_width=2,
            )

    # --- Selected disk (floating above peg) ---
    if game.selected_peg is not None and game.pegs[game.selected_peg]:
        d_size = game.pegs[game.selected_peg][-1]
        cx = peg_base_x(game.selected_peg)
        cy = PEG_Y_BASE + PEG_HEIGHT + 30
        dw = disk_width(d_size, game.num_disks)
        dc = disk_color(d_size)
        arcade.draw_rect_filled(
            arcade.XYWH(cx, cy, dw, DISK_HEIGHT),
            dc,
        )
        arcade.draw_rect_outline(
            arcade.XYWH(cx, cy, dw, DISK_HEIGHT),
            arcade.color.WHITE,
            border_width=2,
        )

    # --- Peg click zones (subtle highlight) ---
    if game.game_state == PLAYING:
        for i in range(3):
            px = peg_base_x(i)
            if game.selected_peg == i:
                arcade.draw_rect_filled(
                    arcade.XYWH(px, PEG_Y_BASE + PEG_HEIGHT / 2,
                                MAX_DISK_WIDTH + 20, PEG_HEIGHT + 60),
                    (255, 255, 255, 20),
                )

    # --- Win overlay ---
    if game.game_state == WON:
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
            (0, 0, 0, 150),
        )
        game.txt_you_win.draw()
        game.txt_win_details.text = (
            f"Solved in {game.move_count} moves  (minimum: {(2 ** game.num_disks) - 1})"
        )
        game.txt_win_details.draw()
