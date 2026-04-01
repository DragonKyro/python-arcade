"""
Renderer for the Liar's Dice game view.
All drawing calls for Liar's Dice are centralized here.
NO ``from games.*`` imports -- constants are defined locally.
"""

import arcade

# Window constants (must match the game view)
WIDTH = 800
HEIGHT = 600

# Game phases (duplicated here to avoid importing from games.liars_dice)
PHASE_SETUP = "setup"
PHASE_PLAYING = "playing"
PHASE_RESOLUTION = "resolution"
PHASE_ROUND_OVER = "round_over"
PHASE_GAME_OVER = "game_over"

# Layout constants
BUTTON_W = 100
BUTTON_H = 36

# Dice drawing
DIE_SIZE = 44
DIE_GAP = 8
DIE_RADIUS = 6
PIP_RADIUS = 4
DIE_BG = (240, 240, 240)
DIE_BORDER = (60, 60, 60)
DIE_HIDDEN_BG = (120, 120, 130)
DIE_HIDDEN_BORDER = (80, 80, 90)
PIP_COLOR = (30, 30, 30)

# Bid controls
BID_BUTTON_W = 100
BID_BUTTON_H = 40
LIAR_BUTTON_W = 100
LIAR_BUTTON_H = 40
SELECTOR_BTN_SIZE = 32

# Overlay
OVERLAY_BG = (0, 0, 0, 170)

# Player layout positions (cx, cy) for up to 4 AI players around the table
# Index 0 = top-center, 1 = top-left, 2 = top-right, 3 = left, 4 = right
AI_POSITIONS = [
    (WIDTH // 2, HEIGHT - 140),       # top center
    (160, HEIGHT - 200),              # upper left
    (WIDTH - 160, HEIGHT - 200),      # upper right
    (120, HEIGHT // 2),               # mid left
]

# Pip layouts for faces 1-6 as relative offsets from die center (fraction of half-size)
_S = 0.55  # spread factor
PIP_LAYOUTS = {
    1: [(0, 0)],
    2: [(-_S, _S), (_S, -_S)],
    3: [(-_S, _S), (0, 0), (_S, -_S)],
    4: [(-_S, _S), (_S, _S), (-_S, -_S), (_S, -_S)],
    5: [(-_S, _S), (_S, _S), (0, 0), (-_S, -_S), (_S, -_S)],
    6: [(-_S, _S), (_S, _S), (-_S, 0), (_S, 0), (-_S, -_S), (_S, -_S)],
}


def draw(game):
    """Render the entire Liar's Dice game state."""
    _draw_buttons(game)

    if game.phase == PHASE_SETUP:
        _draw_setup(game)
    elif game.phase in (PHASE_PLAYING, PHASE_RESOLUTION, PHASE_ROUND_OVER):
        _draw_playing(game)
    elif game.phase == PHASE_GAME_OVER:
        _draw_playing(game)
        _draw_game_over_overlay(game)


# ------------------------------------------------------------------ buttons

def _draw_buttons(game):
    # Back button (top-left)
    bx, by = 60, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.DARK_GRAY)
    arcade.draw_rect_outline(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.WHITE, 2)
    game.txt_btn_back.draw()

    # New Game button (top-right)
    nx, ny = WIDTH - 70, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.WHITE, 2)
    game.txt_btn_new_game.draw()

    # Help button
    game.help_button.draw()

    # Title
    game.txt_title.draw()


# ------------------------------------------------------------------ setup phase

def _draw_setup(game):
    game.txt_setup_prompt.draw()

    for i, btn_data in enumerate(game.setup_buttons):
        bx, by, bw, bh = btn_data
        selected = (i + 1) == game.pending_num_ai
        bg = arcade.color.DARK_BLUE if not selected else arcade.color.BLUE
        arcade.draw_rect_filled(arcade.XYWH(bx, by, bw, bh), bg)
        arcade.draw_rect_outline(arcade.XYWH(bx, by, bw, bh), arcade.color.WHITE, 2)
        game.txt_setup_btn_labels[i].draw()

    # Start button
    if game.pending_num_ai > 0:
        sx, sy = WIDTH // 2, HEIGHT // 2 - 60
        sw, sh = 140, 44
        arcade.draw_rect_filled(arcade.XYWH(sx, sy, sw, sh), arcade.color.DARK_GREEN)
        arcade.draw_rect_outline(arcade.XYWH(sx, sy, sw, sh), arcade.color.WHITE, 2)
        game.txt_start_btn.draw()


# ------------------------------------------------------------------ playing phase

def _draw_playing(game):
    _draw_turn_indicator(game)
    _draw_ai_players(game)
    _draw_human_player(game)
    _draw_current_bid(game)
    _draw_bid_history(game)

    if game.phase == PHASE_PLAYING and game.current_player_index == 0:
        _draw_bid_controls(game)

    if game.phase == PHASE_RESOLUTION:
        _draw_resolution(game)

    if game.phase == PHASE_ROUND_OVER:
        _draw_round_over(game)


def _draw_turn_indicator(game):
    game.txt_turn.draw()


def _draw_die(cx, cy, face, hidden=False):
    """Draw a single die at (cx, cy). If hidden, show gray with '?'."""
    half = DIE_SIZE // 2
    if hidden:
        arcade.draw_rect_filled(
            arcade.XYWH(cx, cy, DIE_SIZE, DIE_SIZE), DIE_HIDDEN_BG
        )
        arcade.draw_rect_outline(
            arcade.XYWH(cx, cy, DIE_SIZE, DIE_SIZE), DIE_HIDDEN_BORDER, 2
        )
        # Draw question mark (using a small filled circle as placeholder)
        arcade.draw_rect_filled(
            arcade.XYWH(cx, cy + 2, 4, 10), (200, 200, 210)
        )
        arcade.draw_circle_filled(cx, cy - 7, 2, (200, 200, 210))
    else:
        arcade.draw_rect_filled(
            arcade.XYWH(cx, cy, DIE_SIZE, DIE_SIZE), DIE_BG
        )
        arcade.draw_rect_outline(
            arcade.XYWH(cx, cy, DIE_SIZE, DIE_SIZE), DIE_BORDER, 2
        )
        # Draw pips
        if face in PIP_LAYOUTS:
            for px, py in PIP_LAYOUTS[face]:
                pip_x = cx + px * half
                pip_y = cy + py * half
                arcade.draw_circle_filled(pip_x, pip_y, PIP_RADIUS, PIP_COLOR)


def _draw_dice_row(cx, cy, dice_values, hidden=False):
    """Draw a row of dice centered at (cx, cy)."""
    count = len(dice_values)
    if count == 0:
        return
    total_w = count * DIE_SIZE + (count - 1) * DIE_GAP
    start_x = cx - total_w / 2 + DIE_SIZE / 2
    for i, val in enumerate(dice_values):
        dx = start_x + i * (DIE_SIZE + DIE_GAP)
        _draw_die(dx, cy, val, hidden=hidden)


def _draw_ai_players(game):
    """Draw AI player areas around the top/sides."""
    for ai_idx, player in enumerate(game.players[1:]):
        if ai_idx >= len(AI_POSITIONS):
            break
        px, py = AI_POSITIONS[ai_idx]

        # Name and dice count
        txt = game.txt_player_names[ai_idx + 1]
        txt.x = px
        txt.y = py + 30
        eliminated = len(player["dice"]) == 0 and game.phase != PHASE_SETUP
        if eliminated:
            txt.color = arcade.color.DARK_GRAY
        elif game.current_player_index == ai_idx + 1:
            txt.color = arcade.color.YELLOW
        else:
            txt.color = arcade.color.WHITE
        txt.draw()

        game.txt_player_dice_counts[ai_idx + 1].x = px
        game.txt_player_dice_counts[ai_idx + 1].y = py + 10
        game.txt_player_dice_counts[ai_idx + 1].text = (
            f"Dice: {len(player['dice'])}" if not eliminated else "Eliminated"
        )
        game.txt_player_dice_counts[ai_idx + 1].draw()

        # Dice (hidden during play, revealed during resolution)
        show_hidden = game.phase in (PHASE_PLAYING, PHASE_ROUND_OVER)
        dice_vals = player["dice"]
        if len(dice_vals) > 0:
            if show_hidden:
                _draw_dice_row(px, py - 20, dice_vals, hidden=True)
            else:
                _draw_dice_row(px, py - 20, dice_vals, hidden=False)


def _draw_human_player(game):
    """Draw the human player's area at the bottom."""
    player = game.players[0]
    px, py = WIDTH // 2, 80

    # Name
    txt_name = game.txt_player_names[0]
    txt_name.x = px
    txt_name.y = py + 50
    if game.current_player_index == 0:
        txt_name.color = arcade.color.YELLOW
    else:
        txt_name.color = arcade.color.WHITE
    txt_name.draw()

    # Dice count
    game.txt_player_dice_counts[0].x = px
    game.txt_player_dice_counts[0].y = py + 32
    game.txt_player_dice_counts[0].text = f"Dice: {len(player['dice'])}"
    game.txt_player_dice_counts[0].draw()

    # Show dice (face up)
    if len(player["dice"]) > 0:
        _draw_dice_row(px, py - 5, player["dice"], hidden=False)


def _draw_current_bid(game):
    """Draw the current bid in the center of the table."""
    game.txt_current_bid.draw()


def _draw_bid_history(game):
    """Draw the last few bids on the right side."""
    game.txt_history_title.draw()
    for txt in game.txt_history_lines:
        txt.draw()


def _draw_bid_controls(game):
    """Draw quantity/face selectors and Bid/Liar buttons for the human player."""
    base_y = 170

    # Quantity selector
    game.txt_qty_label.draw()
    # minus button
    qm_x, qm_y = WIDTH // 2 - 120, base_y
    arcade.draw_rect_filled(arcade.XYWH(qm_x, qm_y, SELECTOR_BTN_SIZE, SELECTOR_BTN_SIZE), arcade.color.DARK_GRAY)
    arcade.draw_rect_outline(arcade.XYWH(qm_x, qm_y, SELECTOR_BTN_SIZE, SELECTOR_BTN_SIZE), arcade.color.WHITE, 2)
    game.txt_qty_minus.draw()
    # value
    game.txt_qty_value.draw()
    # plus button
    qp_x, qp_y = WIDTH // 2 - 30, base_y
    arcade.draw_rect_filled(arcade.XYWH(qp_x, qp_y, SELECTOR_BTN_SIZE, SELECTOR_BTN_SIZE), arcade.color.DARK_GRAY)
    arcade.draw_rect_outline(arcade.XYWH(qp_x, qp_y, SELECTOR_BTN_SIZE, SELECTOR_BTN_SIZE), arcade.color.WHITE, 2)
    game.txt_qty_plus.draw()

    # Face selector
    game.txt_face_label.draw()
    fm_x, fm_y = WIDTH // 2 + 50, base_y
    arcade.draw_rect_filled(arcade.XYWH(fm_x, fm_y, SELECTOR_BTN_SIZE, SELECTOR_BTN_SIZE), arcade.color.DARK_GRAY)
    arcade.draw_rect_outline(arcade.XYWH(fm_x, fm_y, SELECTOR_BTN_SIZE, SELECTOR_BTN_SIZE), arcade.color.WHITE, 2)
    game.txt_face_minus.draw()
    game.txt_face_value.draw()
    fp_x, fp_y = WIDTH // 2 + 140, base_y
    arcade.draw_rect_filled(arcade.XYWH(fp_x, fp_y, SELECTOR_BTN_SIZE, SELECTOR_BTN_SIZE), arcade.color.DARK_GRAY)
    arcade.draw_rect_outline(arcade.XYWH(fp_x, fp_y, SELECTOR_BTN_SIZE, SELECTOR_BTN_SIZE), arcade.color.WHITE, 2)
    game.txt_face_plus.draw()

    # Die preview
    _draw_die(WIDTH // 2 + 115, base_y, game.selected_face)

    # Bid button
    bid_x, bid_y = WIDTH // 2 - 60, base_y - 45
    can_bid = game.can_human_bid()
    bg = arcade.color.DARK_BLUE if can_bid else (60, 60, 70)
    arcade.draw_rect_filled(arcade.XYWH(bid_x, bid_y, BID_BUTTON_W, BID_BUTTON_H), bg)
    arcade.draw_rect_outline(arcade.XYWH(bid_x, bid_y, BID_BUTTON_W, BID_BUTTON_H), arcade.color.WHITE, 2)
    game.txt_bid_btn.draw()

    # Liar button (only if there is a current bid)
    if game.current_bid is not None:
        liar_x, liar_y = WIDTH // 2 + 60, base_y - 45
        arcade.draw_rect_filled(
            arcade.XYWH(liar_x, liar_y, LIAR_BUTTON_W, LIAR_BUTTON_H), arcade.color.DARK_RED
        )
        arcade.draw_rect_outline(
            arcade.XYWH(liar_x, liar_y, LIAR_BUTTON_W, LIAR_BUTTON_H), arcade.color.WHITE, 2
        )
        game.txt_liar_btn.draw()


def _draw_resolution(game):
    """Draw resolution overlay showing all dice and result."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH - 40, 200), (20, 20, 40, 220)
    )
    arcade.draw_rect_outline(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH - 40, 200), arcade.color.WHITE, 2
    )
    game.txt_resolution_title.draw()
    game.txt_resolution_detail.draw()
    game.txt_resolution_result.draw()


def _draw_round_over(game):
    """Show round-over message."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH - 40, 120), (20, 20, 40, 220)
    )
    arcade.draw_rect_outline(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH - 40, 120), arcade.color.WHITE, 2
    )
    game.txt_round_over.draw()
    game.txt_round_continue.draw()


def _draw_game_over_overlay(game):
    """Final game-over overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_BG
    )
    game.txt_game_over_msg.draw()
    game.txt_game_over_hint.draw()
