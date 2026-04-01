"""
Renderer for the Yahtzee game view.
All drawing calls for Yahtzee are centralized here.
NO ``from games.*`` imports -- constants are defined locally.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Phases (duplicated to avoid importing from games.yahtzee)
PHASE_SETUP = "setup"
PHASE_ROLLING = "rolling"
PHASE_SCORING = "scoring"
PHASE_AI_TURN = "ai_turn"
PHASE_GAME_OVER = "game_over"

# Layout constants
BUTTON_W = 100
BUTTON_H = 36
ROLL_BTN_W = 120
ROLL_BTN_H = 40
SCORE_BTN_W = 120
SCORE_BTN_H = 40

# Dice drawing
DIE_SIZE = 64
DIE_GAP = 14
PIP_RADIUS = 5
DIE_BG = (240, 240, 240)
DIE_BG_KEPT = (180, 220, 255)
DIE_BORDER = (60, 60, 60)
DIE_BORDER_KEPT = (40, 100, 200)
PIP_COLOR = (30, 30, 30)

# Dice area
DICE_AREA_Y = 480
DICE_START_X = 240

# Scorecard layout
CARD_LEFT = 20
CARD_TOP = 390
CARD_ROW_H = 22
CARD_LABEL_W = 130
CARD_COL_W = 70
CARD_HEADER_H = 28

# Category display names
CATEGORY_NAMES = {
    "ones": "Ones",
    "twos": "Twos",
    "threes": "Threes",
    "fours": "Fours",
    "fives": "Fives",
    "sixes": "Sixes",
    "three_of_kind": "3 of a Kind",
    "four_of_kind": "4 of a Kind",
    "full_house": "Full House",
    "small_straight": "Sm Straight",
    "large_straight": "Lg Straight",
    "yahtzee": "Yahtzee",
    "chance": "Chance",
}

CATEGORIES = [
    "ones", "twos", "threes", "fours", "fives", "sixes",
    "three_of_kind", "four_of_kind", "full_house",
    "small_straight", "large_straight", "yahtzee", "chance",
]

UPPER_CATEGORIES = ["ones", "twos", "threes", "fours", "fives", "sixes"]

# Overlay
OVERLAY_BG = (0, 0, 0, 170)

# Pip layouts for faces 1-6 as relative offsets from die center (fraction of half-size)
_S = 0.55
PIP_LAYOUTS = {
    1: [(0, 0)],
    2: [(-_S, _S), (_S, -_S)],
    3: [(-_S, _S), (0, 0), (_S, -_S)],
    4: [(-_S, _S), (_S, _S), (-_S, -_S), (_S, -_S)],
    5: [(-_S, _S), (_S, _S), (0, 0), (-_S, -_S), (_S, -_S)],
    6: [(-_S, _S), (_S, _S), (-_S, 0), (_S, 0), (-_S, -_S), (_S, -_S)],
}

# Setup buttons
SETUP_BTN_W = 60
SETUP_BTN_H = 44


def draw(game):
    """Render the entire Yahtzee game state."""
    _draw_buttons(game)

    if game.phase == PHASE_SETUP:
        _draw_setup(game)
    elif game.phase in (PHASE_ROLLING, PHASE_SCORING, PHASE_AI_TURN):
        _draw_playing(game)
    elif game.phase == PHASE_GAME_OVER:
        _draw_playing(game)
        _draw_game_over_overlay(game)


# ------------------------------------------------------------------ buttons

def _draw_buttons(game):
    # Back button
    bx, by = 60, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.DARK_GRAY)
    arcade.draw_rect_outline(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.WHITE, 2)
    game.txt_btn_back.draw()

    # New Game button
    nx, ny = WIDTH - 70, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.WHITE, 2)
    game.txt_btn_new_game.draw()

    # Help button
    game.help_button.draw()

    # Title
    game.txt_title.draw()


# ------------------------------------------------------------------ setup

def _draw_setup(game):
    game.txt_setup_prompt.draw()

    for i in range(4):
        bx = WIDTH // 2 - 120 + i * 80
        by = HEIGHT // 2 + 20
        selected = (i + 1) == game.pending_num_players
        bg = arcade.color.DARK_BLUE if not selected else arcade.color.BLUE
        arcade.draw_rect_filled(arcade.XYWH(bx, by, SETUP_BTN_W, SETUP_BTN_H), bg)
        arcade.draw_rect_outline(arcade.XYWH(bx, by, SETUP_BTN_W, SETUP_BTN_H), arcade.color.WHITE, 2)
        game.txt_setup_btn_labels[i].draw()

    if game.pending_num_players > 0:
        sx, sy = WIDTH // 2, HEIGHT // 2 - 60
        arcade.draw_rect_filled(arcade.XYWH(sx, sy, 140, 44), arcade.color.DARK_GREEN)
        arcade.draw_rect_outline(arcade.XYWH(sx, sy, 140, 44), arcade.color.WHITE, 2)
        game.txt_start_btn.draw()


# ------------------------------------------------------------------ playing

def _draw_playing(game):
    _draw_dice_area(game)
    _draw_action_buttons(game)
    _draw_scorecard(game)
    _draw_info_bar(game)


def _draw_info_bar(game):
    """Draw current player indicator and round counter."""
    game.txt_round_info.draw()
    game.txt_current_player.draw()
    game.txt_rolls_left.draw()


def _draw_die(cx, cy, face, kept=False):
    """Draw a single die at (cx, cy)."""
    half = DIE_SIZE // 2
    bg = DIE_BG_KEPT if kept else DIE_BG
    border = DIE_BORDER_KEPT if kept else DIE_BORDER
    border_width = 3 if kept else 2

    arcade.draw_rect_filled(arcade.XYWH(cx, cy, DIE_SIZE, DIE_SIZE), bg)
    arcade.draw_rect_outline(arcade.XYWH(cx, cy, DIE_SIZE, DIE_SIZE), border, border_width)

    if face in PIP_LAYOUTS:
        for px, py in PIP_LAYOUTS[face]:
            pip_x = cx + px * half
            pip_y = cy + py * half
            arcade.draw_circle_filled(pip_x, pip_y, PIP_RADIUS, PIP_COLOR)


def _draw_dice_area(game):
    """Draw the 5 dice with keep/active indication."""
    if not game.dice:
        return

    for i in range(5):
        dx = DICE_START_X + i * (DIE_SIZE + DIE_GAP)
        dy = DICE_AREA_Y
        kept = i in game.kept_indices
        _draw_die(dx, dy, game.dice[i], kept=kept)

    # Draw "kept" label under kept dice
    for i in range(5):
        if i in game.kept_indices:
            dx = DICE_START_X + i * (DIE_SIZE + DIE_GAP)
            game.txt_kept_labels[i].x = dx
            game.txt_kept_labels[i].y = DICE_AREA_Y - DIE_SIZE // 2 - 12
            game.txt_kept_labels[i].draw()


def _draw_action_buttons(game):
    """Draw Roll and Score buttons."""
    is_human_turn = game.current_player_index == 0
    in_play_phase = game.phase in (PHASE_ROLLING, PHASE_SCORING)

    # Roll button
    roll_x, roll_y = 660, DICE_AREA_Y + 20
    can_roll = is_human_turn and game.roll_number < 3 and in_play_phase
    bg = arcade.color.DARK_BLUE if can_roll else (60, 60, 70)
    arcade.draw_rect_filled(arcade.XYWH(roll_x, roll_y, ROLL_BTN_W, ROLL_BTN_H), bg)
    arcade.draw_rect_outline(arcade.XYWH(roll_x, roll_y, ROLL_BTN_W, ROLL_BTN_H), arcade.color.WHITE, 2)
    game.txt_roll_btn.x = roll_x
    game.txt_roll_btn.y = roll_y
    game.txt_roll_btn.draw()

    # Score button (visible after at least 1 roll)
    if game.roll_number >= 1:
        score_x, score_y = 660, DICE_AREA_Y - 30
        can_score = is_human_turn and game.selected_category is not None and in_play_phase
        bg = arcade.color.DARK_GREEN if can_score else (60, 60, 70)
        arcade.draw_rect_filled(arcade.XYWH(score_x, score_y, SCORE_BTN_W, SCORE_BTN_H), bg)
        arcade.draw_rect_outline(arcade.XYWH(score_x, score_y, SCORE_BTN_W, SCORE_BTN_H), arcade.color.WHITE, 2)
        game.txt_score_btn.x = score_x
        game.txt_score_btn.y = score_y
        game.txt_score_btn.draw()


def _draw_scorecard(game):
    """Draw the scorecard table with categories and player columns."""
    num_players = len(game.players)
    card_width = CARD_LABEL_W + num_players * CARD_COL_W
    x0 = CARD_LEFT
    y0 = CARD_TOP

    # Background
    total_rows = len(CATEGORIES) + 4  # categories + upper bonus + upper total + lower total + grand total
    card_height = CARD_HEADER_H + total_rows * CARD_ROW_H + 10
    arcade.draw_rect_filled(
        arcade.XYWH(x0 + card_width // 2, y0 - card_height // 2 + CARD_HEADER_H // 2,
                     card_width + 4, card_height + 4),
        (30, 30, 50, 200)
    )

    # Header row
    hy = y0
    arcade.draw_rect_filled(
        arcade.XYWH(x0 + card_width // 2, hy, card_width, CARD_HEADER_H),
        (50, 50, 80)
    )
    game.txt_card_header.x = x0 + CARD_LABEL_W // 2
    game.txt_card_header.y = hy
    game.txt_card_header.draw()

    for p_idx in range(num_players):
        col_x = x0 + CARD_LABEL_W + p_idx * CARD_COL_W + CARD_COL_W // 2
        game.txt_player_headers[p_idx].x = col_x
        game.txt_player_headers[p_idx].y = hy
        # Highlight current player
        if p_idx == game.current_player_index and game.phase != PHASE_GAME_OVER:
            game.txt_player_headers[p_idx].color = arcade.color.YELLOW
        else:
            game.txt_player_headers[p_idx].color = arcade.color.WHITE
        game.txt_player_headers[p_idx].draw()

    # Category rows
    row_y = y0 - CARD_HEADER_H
    for cat_idx, cat in enumerate(CATEGORIES):
        ry = row_y - cat_idx * CARD_ROW_H
        display_name = CATEGORY_NAMES[cat]

        # Row highlight if this category is selected by human
        if (game.selected_category == cat and game.current_player_index == 0
                and game.phase in (PHASE_ROLLING, PHASE_SCORING)):
            arcade.draw_rect_filled(
                arcade.XYWH(x0 + card_width // 2, ry, card_width, CARD_ROW_H),
                (80, 80, 40, 150)
            )

        # Separator after upper section
        if cat_idx == 6:
            sep_y = ry + CARD_ROW_H // 2
            arcade.draw_line(x0, sep_y, x0 + card_width, sep_y, arcade.color.GRAY, 1)

        # Category label
        game.txt_cat_labels[cat_idx].x = x0 + 5
        game.txt_cat_labels[cat_idx].y = ry
        game.txt_cat_labels[cat_idx].text = display_name

        # If this is a clickable row for the human (available), color differently
        is_available = cat not in game.players[game.current_player_index]["scores_used"]
        if (game.current_player_index == 0 and is_available
                and game.roll_number >= 1 and game.phase in (PHASE_ROLLING, PHASE_SCORING)):
            game.txt_cat_labels[cat_idx].color = arcade.color.LIGHT_BLUE
        else:
            game.txt_cat_labels[cat_idx].color = arcade.color.LIGHT_GRAY

        game.txt_cat_labels[cat_idx].draw()

        # Player scores in columns
        for p_idx in range(num_players):
            col_x = x0 + CARD_LABEL_W + p_idx * CARD_COL_W + CARD_COL_W // 2
            player = game.players[p_idx]
            txt = game.txt_scores[cat_idx][p_idx]
            txt.x = col_x
            txt.y = ry

            if cat in player["scores_used"]:
                score_val = player["scores"].get(cat, 0)
                txt.text = str(score_val)
                txt.color = arcade.color.WHITE
            elif (p_idx == game.current_player_index and game.roll_number >= 1
                  and game.phase in (PHASE_ROLLING, PHASE_SCORING) and p_idx == 0):
                # Show potential score for human
                from ai.yahtzee_ai import calculate_score
                potential = calculate_score(game.dice, cat)
                txt.text = str(potential)
                txt.color = (150, 150, 100)
            else:
                txt.text = ""

            txt.draw()

    # Summary rows: upper bonus, upper total, lower total, grand total
    summary_start_y = row_y - len(CATEGORIES) * CARD_ROW_H - 5

    # Divider line
    arcade.draw_line(x0, summary_start_y + CARD_ROW_H // 2 + 5,
                     x0 + card_width, summary_start_y + CARD_ROW_H // 2 + 5,
                     arcade.color.WHITE, 1)

    summary_labels = ["Upper Bonus", "Upper Total", "Lower Total", "Grand Total"]
    for s_idx, label in enumerate(summary_labels):
        sy = summary_start_y - s_idx * CARD_ROW_H
        game.txt_summary_labels[s_idx].x = x0 + 5
        game.txt_summary_labels[s_idx].y = sy
        game.txt_summary_labels[s_idx].text = label
        game.txt_summary_labels[s_idx].draw()

        for p_idx in range(num_players):
            col_x = x0 + CARD_LABEL_W + p_idx * CARD_COL_W + CARD_COL_W // 2
            player = game.players[p_idx]
            txt = game.txt_summary_scores[s_idx][p_idx]
            txt.x = col_x
            txt.y = sy

            upper_total = sum(player["scores"].get(c, 0) for c in UPPER_CATEGORIES)
            lower_cats = [c for c in CATEGORIES if c not in UPPER_CATEGORIES]
            lower_total = sum(player["scores"].get(c, 0) for c in lower_cats)
            bonus = 35 if upper_total >= 63 else 0

            if s_idx == 0:
                txt.text = str(bonus)
                txt.color = arcade.color.GREEN if bonus > 0 else arcade.color.GRAY
            elif s_idx == 1:
                txt.text = str(upper_total)
                txt.color = arcade.color.WHITE
            elif s_idx == 2:
                txt.text = str(lower_total)
                txt.color = arcade.color.WHITE
            elif s_idx == 3:
                txt.text = str(upper_total + lower_total + bonus)
                txt.color = arcade.color.YELLOW if game.phase == PHASE_GAME_OVER else arcade.color.WHITE

            txt.draw()


# ------------------------------------------------------------------ game over

def _draw_game_over_overlay(game):
    """Draw the game over overlay with winner and final scores."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_BG
    )

    game.txt_game_over_title.draw()
    game.txt_game_over_winner.draw()

    # Final scores
    for i, txt in enumerate(game.txt_game_over_scores):
        if i < len(game.players):
            txt.draw()

    game.txt_game_over_hint.draw()
