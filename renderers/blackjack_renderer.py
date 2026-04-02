"""
Renderer for Blackjack.
All arcade.draw_* calls live here. No arcade.draw_text -- uses arcade.Text on game.
No imports from games.*.
"""

import arcade
from utils.card import draw_card, draw_card_back, draw_empty_slot, CARD_WIDTH, CARD_HEIGHT

# Window / layout constants
WIDTH = 800
HEIGHT = 600
TOP_BAR_HEIGHT = 50
SCALE = 1.0

CARD_W = CARD_WIDTH * SCALE
CARD_H = CARD_HEIGHT * SCALE
CARD_SPACING = 30  # Horizontal overlap between cards in a hand

# Vertical positions
DEALER_Y = HEIGHT - TOP_BAR_HEIGHT - 90
PLAYER_AREA_TOP = 320
PLAYER_AREA_BOTTOM = 80

# Colors
BG_COLOR = (35, 100, 60)  # green felt
BAR_COLOR = (40, 50, 40)
BTN_COLOR = arcade.color.DARK_SLATE_BLUE
BTN_GREEN = arcade.color.DARK_GREEN
BTN_RED = (180, 50, 50)
BTN_GOLD = arcade.color.DARK_GOLDENROD
BTN_DISABLED = (80, 80, 80)
CHIP_COLOR = arcade.color.GOLD
OVERLAY_COLOR = (0, 0, 0, 160)

# Action button layout
ACTION_BTN_W = 90
ACTION_BTN_H = 36
ACTION_BTN_Y = 50
ACTION_BTN_SPACING = 100

# Bet selection layout
BET_BTN_W = 64
BET_BTN_H = 36
BET_BTN_Y = HEIGHT // 2 - 40
BET_BTN_SPACING = 80

# Setup button layout
SETUP_BTN_W = 60
SETUP_BTN_H = 44


def draw(game):
    """Render the full Blackjack game state."""
    _draw_background()
    _draw_top_bar(game)

    if game.phase == "setup":
        _draw_setup(game)
    elif game.phase == "betting":
        _draw_betting(game)
    else:
        _draw_table(game)
        _draw_action_buttons(game)
        if game.phase in ("result", "game_over"):
            _draw_result_overlay(game)


# ------------------------------------------------------------------
# Background
# ------------------------------------------------------------------

def _draw_background():
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), BG_COLOR
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
# Setup phase -- choose number of AI players
# ------------------------------------------------------------------

def _draw_setup(game):
    game.txt_setup_prompt.draw()
    for i in range(4):
        bx, by, bw, bh = game.setup_buttons[i]
        color = BTN_GOLD if game.pending_num_ai == i else BTN_COLOR
        _draw_button(bx, by, bw, bh, color)
        game.txt_setup_labels[i].draw()
    if game.pending_num_ai >= 0:
        _draw_button(WIDTH // 2, HEIGHT // 2 - 60, 140, 44, BTN_GREEN)
        game.txt_start_btn.draw()


# ------------------------------------------------------------------
# Betting phase
# ------------------------------------------------------------------

def _draw_betting(game):
    game.txt_bet_prompt.draw()
    game.txt_chips_display.draw()
    for i, txt in enumerate(game.txt_bet_labels):
        bx = WIDTH // 2 + (i - 2) * BET_BTN_SPACING
        by = BET_BTN_Y
        color = BTN_GOLD if game.selected_bet_index == i else BTN_COLOR
        _draw_button(bx, by, BET_BTN_W, BET_BTN_H, color)
        txt.draw()
    _draw_button(WIDTH // 2, BET_BTN_Y - 60, 120, 40, BTN_GREEN)
    game.txt_deal_btn.draw()


# ------------------------------------------------------------------
# Table -- dealer and player hands
# ------------------------------------------------------------------

def _draw_table(game):
    # Dealer hand
    _draw_hand(game.dealer_hand, WIDTH // 2, DEALER_Y, game.phase != "player_turn")
    game.txt_dealer_label.draw()
    game.txt_dealer_value.draw()

    # Player hands (human + AI)
    num_players = len(game.players)
    total_width = (num_players - 1) * 180
    start_x = WIDTH // 2 - total_width // 2

    for pi, player in enumerate(game.players):
        px = start_x + pi * 180
        py = 220

        # Draw each hand (player may have split hands)
        for hi, hand in enumerate(player["hands"]):
            hand_y = py - hi * 120
            active = (game.phase == "player_turn" and
                      game.current_player_idx == pi and
                      game.current_hand_idx == hi)
            if active:
                # Highlight active hand
                hw = len(hand["cards"]) * CARD_SPACING + CARD_W
                arcade.draw_rect_outline(
                    arcade.XYWH(px, hand_y, hw + 10, CARD_H + 10),
                    arcade.color.YELLOW, 2,
                )
            _draw_hand(hand["cards"], px, hand_y, False)

        # Player info texts
        game.txt_player_names[pi].draw()
        game.txt_player_chips[pi].draw()
        game.txt_player_values[pi].draw()
        if pi < len(game.txt_player_results) and game.txt_player_results[pi].text:
            game.txt_player_results[pi].draw()


def _draw_hand(cards, center_x, center_y, hide_first):
    """Draw a hand of cards, optionally hiding the first card."""
    if not cards:
        draw_empty_slot(center_x, center_y, SCALE)
        return
    total_width = (len(cards) - 1) * CARD_SPACING
    start_x = center_x - total_width / 2
    for i, card in enumerate(cards):
        x = start_x + i * CARD_SPACING
        if i == 0 and hide_first and not card.face_up:
            draw_card_back(x, center_y, SCALE)
        else:
            draw_card(card, x, center_y, SCALE)


# ------------------------------------------------------------------
# Action buttons
# ------------------------------------------------------------------

def _draw_action_buttons(game):
    if game.phase != "player_turn":
        return
    if game.current_player_idx != 0:
        return  # Don't show buttons during AI turn

    player = game.players[0]
    hand = player["hands"][game.current_hand_idx]
    actions = game.get_available_actions()

    btn_names = [("Hit", "hit"), ("Stand", "stand"), ("Double", "double"), ("Split", "split")]
    num_btns = len(btn_names)
    total_w = (num_btns - 1) * ACTION_BTN_SPACING
    start_x = WIDTH // 2 - total_w // 2

    for i, (label, action) in enumerate(btn_names):
        bx = start_x + i * ACTION_BTN_SPACING
        enabled = action in actions
        color = BTN_GREEN if enabled else BTN_DISABLED
        _draw_button(bx, ACTION_BTN_Y, ACTION_BTN_W, ACTION_BTN_H, color)
        game.txt_action_btns[i].draw()


# ------------------------------------------------------------------
# Result overlay
# ------------------------------------------------------------------

def _draw_result_overlay(game):
    if game.phase == "game_over":
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), OVERLAY_COLOR
        )
        game.txt_game_over.draw()
        game.txt_game_over_hint.draw()
    # Per-player results are drawn inline via txt_player_results
