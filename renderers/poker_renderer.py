"""
Renderer for Texas Hold'em Poker.
All arcade.draw_* calls live here. No arcade.draw_text -- uses arcade.Text on game.
No imports from games.*.
"""

import arcade
from utils.card import draw_card, draw_card_back, draw_empty_slot, CARD_WIDTH, CARD_HEIGHT

# Window / layout constants
WIDTH = 800
HEIGHT = 600
TOP_BAR_HEIGHT = 50
SCALE = 0.9

CARD_W = CARD_WIDTH * SCALE
CARD_H = CARD_HEIGHT * SCALE
CARD_SPACING = 28
COMMUNITY_SPACING = 80

# Table positions
TABLE_CENTER_X = WIDTH // 2
TABLE_CENTER_Y = HEIGHT // 2 + 20
TABLE_RX = 300  # Ellipse radii
TABLE_RY = 180

# Community cards
COMMUNITY_Y = TABLE_CENTER_Y
COMMUNITY_START_X = TABLE_CENTER_X - 2 * COMMUNITY_SPACING

# Player seat positions (up to 6: human + 5 AI)
# Arranged around the table ellipse
SEAT_POSITIONS = [
    (WIDTH // 2, 80),           # 0: Human (bottom center)
    (100, 200),                 # 1: Left-bottom
    (80, 400),                  # 2: Left-top
    (WIDTH // 2, HEIGHT - 90),  # 3: Top center
    (720, 400),                 # 4: Right-top
    (700, 200),                 # 5: Right-bottom
]

# Colors
BG_COLOR = (35, 80, 55)
TABLE_COLOR = (25, 120, 60)
TABLE_BORDER = (60, 40, 20)
BAR_COLOR = (40, 50, 40)
BTN_COLOR = arcade.color.DARK_SLATE_BLUE
BTN_GREEN = arcade.color.DARK_GREEN
BTN_RED = (180, 50, 50)
BTN_GOLD = arcade.color.DARK_GOLDENROD
BTN_DISABLED = (80, 80, 80)
OVERLAY_COLOR = (0, 0, 0, 160)
ACTIVE_HIGHLIGHT = arcade.color.YELLOW
FOLD_DIM = (100, 100, 100, 128)
POT_COLOR = arcade.color.GOLD

# Action buttons
ACTION_BTN_W = 80
ACTION_BTN_H = 34
ACTION_BTN_Y = 38
ACTION_BTN_SPACING = 95

# Setup / bet controls
SETUP_BTN_W = 60
SETUP_BTN_H = 44


def draw(game):
    """Render the full Poker game state."""
    _draw_background()
    _draw_table_felt()
    _draw_top_bar(game)

    if game.phase == "setup":
        _draw_setup(game)
    else:
        _draw_community_cards(game)
        _draw_pot(game)
        _draw_players(game)
        _draw_action_buttons(game)
        if game.phase == "showdown":
            _draw_showdown_overlay(game)
        elif game.phase == "game_over":
            _draw_game_over(game)


# ------------------------------------------------------------------
# Background and table
# ------------------------------------------------------------------

def _draw_background():
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), BG_COLOR
    )


def _draw_table_felt():
    # Table border ellipse
    arcade.draw_ellipse_filled(
        TABLE_CENTER_X, TABLE_CENTER_Y,
        TABLE_RX * 2 + 20, TABLE_RY * 2 + 20,
        TABLE_BORDER,
    )
    # Table surface
    arcade.draw_ellipse_filled(
        TABLE_CENTER_X, TABLE_CENTER_Y,
        TABLE_RX * 2, TABLE_RY * 2,
        TABLE_COLOR,
    )


# ------------------------------------------------------------------
# Top bar
# ------------------------------------------------------------------

def _draw_top_bar(game):
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT), BAR_COLOR
    )
    _draw_button(55, bar_y, 90, 35, BTN_COLOR)
    game.txt_back.draw()
    _draw_button(WIDTH - 65, bar_y, 110, 35, BTN_GREEN)
    game.txt_new_game.draw()
    _draw_button(WIDTH - 135, bar_y, 40, 40, BTN_COLOR)
    game.txt_help.draw()
    game.txt_title.draw()


def _draw_button(x, y, w, h, color):
    arcade.draw_rect_filled(arcade.XYWH(x, y, w, h), color)
    arcade.draw_rect_outline(arcade.XYWH(x, y, w, h), arcade.color.WHITE)


# ------------------------------------------------------------------
# Setup phase
# ------------------------------------------------------------------

def _draw_setup(game):
    game.txt_setup_prompt.draw()
    for i in range(5):
        bx, by, bw, bh = game.setup_buttons[i]
        color = BTN_GOLD if game.pending_num_ai == (i + 1) else BTN_COLOR
        _draw_button(bx, by, bw, bh, color)
        game.txt_setup_labels[i].draw()
    if game.pending_num_ai > 0:
        _draw_button(WIDTH // 2, HEIGHT // 2 - 60, 140, 44, BTN_GREEN)
        game.txt_start_btn.draw()


# ------------------------------------------------------------------
# Community cards
# ------------------------------------------------------------------

def _draw_community_cards(game):
    for i in range(5):
        x = COMMUNITY_START_X + i * COMMUNITY_SPACING
        y = COMMUNITY_Y
        if i < len(game.community_cards):
            card = game.community_cards[i]
            draw_card(card, x, y, SCALE)
        else:
            draw_empty_slot(x, y, SCALE)


# ------------------------------------------------------------------
# Pot display
# ------------------------------------------------------------------

def _draw_pot(game):
    game.txt_pot.draw()


# ------------------------------------------------------------------
# Players around the table
# ------------------------------------------------------------------

def _draw_players(game):
    for pi, player in enumerate(game.players):
        if pi >= len(SEAT_POSITIONS):
            break
        sx, sy = SEAT_POSITIONS[pi]

        # Highlight active player
        is_active = (game.current_player_idx == pi and
                     game.phase in ("preflop", "flop", "turn", "river"))
        if is_active:
            arcade.draw_circle_filled(sx, sy + 20, 50, (*ACTIVE_HIGHLIGHT[:3], 40))

        # Draw hole cards
        cards = player.get("hole_cards", [])
        show_cards = (pi == 0) or game.phase == "showdown"
        folded = player.get("folded", False)

        if folded:
            # Dimmed empty slot for folded players
            draw_empty_slot(sx, sy + 20, SCALE * 0.8)
        elif cards:
            for ci, card in enumerate(cards):
                cx = sx + (ci - 0.5) * CARD_SPACING
                cy = sy + 20
                if show_cards and card.face_up:
                    draw_card(card, cx, cy, SCALE * 0.8)
                else:
                    draw_card_back(cx, cy, SCALE * 0.8)

        # Dealer button indicator
        if game.dealer_button == pi:
            game.txt_dealer_btn_markers[pi].draw()

        # Player info
        game.txt_player_names[pi].draw()
        game.txt_player_chips[pi].draw()
        if pi < len(game.txt_player_bets) and game.txt_player_bets[pi].text:
            game.txt_player_bets[pi].draw()
        if pi < len(game.txt_player_actions) and game.txt_player_actions[pi].text:
            game.txt_player_actions[pi].draw()


# ------------------------------------------------------------------
# Action buttons (for human player)
# ------------------------------------------------------------------

def _draw_action_buttons(game):
    if game.phase not in ("preflop", "flop", "turn", "river"):
        return
    if game.current_player_idx != 0:
        return
    if game.players[0].get("folded", False):
        return

    actions = game.get_available_actions()
    btn_defs = [
        ("Fold", "fold"), ("Check", "check"),
        ("Call", "call"), ("Raise", "raise"),
    ]
    num = len(btn_defs)
    total_w = (num - 1) * ACTION_BTN_SPACING
    start_x = WIDTH // 2 - total_w // 2

    for i, (label, action) in enumerate(btn_defs):
        bx = start_x + i * ACTION_BTN_SPACING
        enabled = action in actions
        color = BTN_GREEN if enabled else BTN_DISABLED
        _draw_button(bx, ACTION_BTN_Y, ACTION_BTN_W, ACTION_BTN_H, color)
        game.txt_action_btns[i].draw()

    # Raise amount display
    if "raise" in actions:
        game.txt_raise_amount.draw()
        # Raise +/- buttons
        rmx = WIDTH // 2 + 200
        _draw_button(rmx - 30, ACTION_BTN_Y, 28, 28, BTN_COLOR)
        _draw_button(rmx + 30, ACTION_BTN_Y, 28, 28, BTN_COLOR)
        game.txt_raise_minus.draw()
        game.txt_raise_plus.draw()


# ------------------------------------------------------------------
# Showdown overlay
# ------------------------------------------------------------------

def _draw_showdown_overlay(game):
    game.txt_winner_msg.draw()
    game.txt_hand_desc.draw()


# ------------------------------------------------------------------
# Game over
# ------------------------------------------------------------------

def _draw_game_over(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), OVERLAY_COLOR
    )
    game.txt_game_over.draw()
    game.txt_game_over_hint.draw()
