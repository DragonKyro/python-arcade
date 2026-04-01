"""
Renderer for the Frogger game.
All drawing code extracted from games/frogger.py.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
BOTTOM_BAR_HEIGHT = 40
CELL_SIZE = 40
COLS = WIDTH // CELL_SIZE
ROWS = 13

# Play area origin
GRID_ORIGIN_Y = BOTTOM_BAR_HEIGHT

# Colors
BG_COLOR = (30, 30, 46)
GRASS_COLOR = (34, 120, 34)
ROAD_COLOR = (60, 60, 60)
MEDIAN_COLOR = (34, 120, 34)
WATER_COLOR = (30, 80, 180)
HOME_ROW_COLOR = (20, 70, 20)
SIDEWALK_COLOR = (100, 100, 80)
LINE_COLOR = (205, 214, 244)
OVERLAY_COLOR = (30, 30, 46, 200)
SCORE_COLOR = (249, 226, 175)
FROG_COLOR = (50, 200, 50)
FROG_EYE_COLOR = (255, 255, 255)
FROG_PUPIL_COLOR = (0, 0, 0)
LILY_PAD_COLOR = (30, 160, 30)
LANE_MARKER_COLOR = (200, 200, 50)
TIMER_BG_COLOR = (60, 60, 60)
TIMER_FG_COLOR = (50, 200, 50)
TIMER_LOW_COLOR = (220, 50, 50)

# Timing
TIMER_DURATION = 30.0

# Home slot positions
HOME_SLOT_COLS = [2, 6, 10, 14, 18]


def draw(game):
    """Render the entire Frogger game state."""
    # Draw row backgrounds
    _draw_row_backgrounds()

    # Draw lane markings on road
    _draw_lane_markings()

    # Draw home slots
    _draw_home_slots()

    # Draw lane objects
    for obj in game.lane_objects:
        obj.draw()

    # Draw frog
    if not game.game_over:
        _draw_frog(game)

    # Draw filled homes
    _draw_filled_homes(game)

    # Draw UI
    _draw_top_bar(game)
    _draw_bottom_bar(game)

    # Game over overlay
    if game.game_over:
        _draw_game_over(game)


def _draw_row_backgrounds():
    """Draw background color for each row."""
    for row in range(ROWS):
        y = GRID_ORIGIN_Y + row * CELL_SIZE + CELL_SIZE / 2

        if row == 0:
            color = SIDEWALK_COLOR
        elif 1 <= row <= 5:
            color = ROAD_COLOR
        elif row == 6:
            color = MEDIAN_COLOR
        elif 7 <= row <= 11:
            color = WATER_COLOR
        elif row == 12:
            color = HOME_ROW_COLOR
        else:
            color = BG_COLOR

        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, y, WIDTH, CELL_SIZE), color
        )


def _draw_lane_markings():
    """Draw dashed lane markings on roads."""
    for row in range(1, 5):
        y = GRID_ORIGIN_Y + (row + 1) * CELL_SIZE
        for x in range(0, WIDTH, 40):
            arcade.draw_line(x, y, x + 20, y, LANE_MARKER_COLOR, 1)


def _draw_home_slots():
    """Draw the 5 home slot indicators."""
    y = GRID_ORIGIN_Y + 12 * CELL_SIZE + CELL_SIZE / 2
    for col in HOME_SLOT_COLS:
        x = col * CELL_SIZE + CELL_SIZE / 2
        # Dark alcove
        arcade.draw_rect_filled(
            arcade.XYWH(x, y, CELL_SIZE - 2, CELL_SIZE - 2),
            (10, 50, 10),
        )
        # Lily pad circle
        arcade.draw_circle_filled(x, y, CELL_SIZE / 2 - 4, LILY_PAD_COLOR)
        arcade.draw_circle_filled(x, y, CELL_SIZE / 2 - 8, (40, 130, 40))


def _draw_filled_homes(game):
    """Draw small frogs in filled home slots."""
    y = GRID_ORIGIN_Y + 12 * CELL_SIZE + CELL_SIZE / 2
    for i, filled in enumerate(game.homes_filled):
        if filled:
            col = HOME_SLOT_COLS[i]
            x = col * CELL_SIZE + CELL_SIZE / 2
            # Mini frog
            arcade.draw_circle_filled(x, y, 10, FROG_COLOR)
            arcade.draw_circle_filled(x - 4, y + 5, 3, FROG_EYE_COLOR)
            arcade.draw_circle_filled(x + 4, y + 5, 3, FROG_EYE_COLOR)
            arcade.draw_circle_filled(x - 4, y + 5, 1.5, FROG_PUPIL_COLOR)
            arcade.draw_circle_filled(x + 4, y + 5, 1.5, FROG_PUPIL_COLOR)


def _draw_frog(game):
    """Draw the frog at its current position."""
    x = game.frog_col * CELL_SIZE + CELL_SIZE / 2
    y = GRID_ORIGIN_Y + game.frog_row * CELL_SIZE + CELL_SIZE / 2

    # Body
    arcade.draw_rect_filled(
        arcade.XYWH(x, y, CELL_SIZE - 6, CELL_SIZE - 6),
        FROG_COLOR,
    )

    # Body rounded look
    arcade.draw_circle_filled(x, y + (CELL_SIZE / 2 - 5), 10, FROG_COLOR)
    arcade.draw_circle_filled(x, y - (CELL_SIZE / 2 - 5), 8, FROG_COLOR)

    # Eyes (on top portion)
    eye_y = y + 8
    for dx in (-7, 7):
        arcade.draw_circle_filled(x + dx, eye_y, 5, FROG_EYE_COLOR)
        arcade.draw_circle_filled(x + dx, eye_y, 2.5, FROG_PUPIL_COLOR)

    # Legs (small bumps)
    for dx in (-12, 12):
        arcade.draw_circle_filled(x + dx, y + 5, 4, FROG_COLOR)
        arcade.draw_circle_filled(x + dx, y - 8, 4, FROG_COLOR)


def _draw_top_bar(game):
    """Draw the top bar with buttons and score."""
    # Background
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT - TOP_BAR_HEIGHT / 2, WIDTH, TOP_BAR_HEIGHT),
        BG_COLOR,
    )
    arcade.draw_line(0, HEIGHT - TOP_BAR_HEIGHT, WIDTH, HEIGHT - TOP_BAR_HEIGHT, LINE_COLOR, 1)

    # Buttons
    game.btn_back.draw(game.btn_back.contains(game.mouse_x, game.mouse_y))
    game.btn_help.draw(game.btn_help.contains(game.mouse_x, game.mouse_y))
    game.btn_new.draw(game.btn_new.contains(game.mouse_x, game.mouse_y))

    # Score in center
    arcade.draw_text(
        f"Score: {game.score}",
        WIDTH / 2,
        HEIGHT - 25,
        SCORE_COLOR,
        font_size=16,
        anchor_x="center",
        anchor_y="center",
        bold=True,
    )


def _draw_bottom_bar(game):
    """Draw bottom bar with lives, level, timer, and high score."""
    # Background
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, BOTTOM_BAR_HEIGHT / 2, WIDTH, BOTTOM_BAR_HEIGHT),
        BG_COLOR,
    )
    arcade.draw_line(0, BOTTOM_BAR_HEIGHT, WIDTH, BOTTOM_BAR_HEIGHT, LINE_COLOR, 1)

    # Lives (small frog icons)
    arcade.draw_text("Lives:", 10, 20, LINE_COLOR, font_size=12, anchor_x="left", anchor_y="center")
    for i in range(game.lives):
        lx = 70 + i * 25
        arcade.draw_circle_filled(lx, 20, 8, FROG_COLOR)
        arcade.draw_circle_filled(lx - 2, 24, 2, FROG_EYE_COLOR)
        arcade.draw_circle_filled(lx + 2, 24, 2, FROG_EYE_COLOR)

    # Level
    arcade.draw_text(
        f"Level: {game.level}",
        200,
        20,
        LINE_COLOR,
        font_size=12,
        anchor_x="left",
        anchor_y="center",
    )

    # Timer bar
    timer_x = 320
    timer_w = 200
    timer_h = 14
    timer_y = 20
    # Background
    arcade.draw_rect_filled(
        arcade.XYWH(timer_x + timer_w / 2, timer_y, timer_w, timer_h),
        TIMER_BG_COLOR,
    )
    # Fill
    frac = max(0, game.timer / TIMER_DURATION)
    fill_w = timer_w * frac
    fill_color = TIMER_FG_COLOR if frac > 0.3 else TIMER_LOW_COLOR
    if fill_w > 0:
        arcade.draw_rect_filled(
            arcade.XYWH(timer_x + fill_w / 2, timer_y, fill_w, timer_h),
            fill_color,
        )
    arcade.draw_rect_outline(
        arcade.XYWH(timer_x + timer_w / 2, timer_y, timer_w, timer_h),
        LINE_COLOR, 1,
    )
    arcade.draw_text("TIME", timer_x - 35, 20, LINE_COLOR, font_size=10, anchor_x="left", anchor_y="center")

    # High score
    arcade.draw_text(
        f"Hi: {game.high_score}",
        WIDTH - 10,
        20,
        SCORE_COLOR,
        font_size=12,
        anchor_x="right",
        anchor_y="center",
    )


def _draw_game_over(game):
    """Draw game over overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        OVERLAY_COLOR,
    )
    arcade.draw_text(
        "GAME OVER",
        WIDTH / 2,
        HEIGHT / 2 + 40,
        (220, 50, 50),
        font_size=36,
        anchor_x="center",
        anchor_y="center",
        bold=True,
    )
    arcade.draw_text(
        f"Final Score: {game.score}",
        WIDTH / 2,
        HEIGHT / 2 - 10,
        SCORE_COLOR,
        font_size=20,
        anchor_x="center",
        anchor_y="center",
    )
    arcade.draw_text(
        "Press SPACE or click New Game to restart",
        WIDTH / 2,
        HEIGHT / 2 - 50,
        LINE_COLOR,
        font_size=14,
        anchor_x="center",
        anchor_y="center",
    )
