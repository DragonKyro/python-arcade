"""
Renderer for the Old Maid game view.
All drawing calls are centralized here.
NO ``from games.*`` imports -- constants are defined locally.
"""

import arcade
from utils.card import (
    draw_card, draw_card_back, draw_empty_slot,
    CARD_WIDTH, CARD_HEIGHT,
)

# Window constants
WIDTH = 800
HEIGHT = 600

# Game phases (duplicated to avoid importing from games.old_maid)
PHASE_SETUP = "setup"
PHASE_HUMAN_DRAW = "human_draw"
PHASE_AI_TURN = "ai_turn"
PHASE_GAME_OVER = "game_over"

# Layout
BUTTON_W = 100
BUTTON_H = 36

OVERLAY_BG = (0, 0, 0, 170)


def draw(game):
    """Render the entire Old Maid game state."""
    _draw_buttons(game)

    if game.phase == PHASE_SETUP:
        _draw_setup(game)
    elif game.phase in (PHASE_HUMAN_DRAW, PHASE_AI_TURN):
        _draw_playing(game)
    elif game.phase == PHASE_GAME_OVER:
        _draw_playing(game)
        _draw_game_over_overlay(game)


# ------------------------------------------------------------------ buttons

def _draw_buttons(game):
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
    game.help_button.draw()

    # Title
    game.txt_title.draw()


# ------------------------------------------------------------------ setup

def _draw_setup(game):
    game.txt_setup_prompt.draw()

    for i, btn_data in enumerate(game.setup_buttons):
        bx, by, bw, bh = btn_data
        selected = (i + 1) == game.pending_num_ai
        bg = arcade.color.DARK_BLUE if not selected else arcade.color.BLUE
        arcade.draw_rect_filled(arcade.XYWH(bx, by, bw, bh), bg)
        arcade.draw_rect_outline(arcade.XYWH(bx, by, bw, bh), arcade.color.WHITE, 2)
        game.txt_setup_btn_labels[i].draw()

    if game.pending_num_ai > 0:
        sx, sy = WIDTH // 2, HEIGHT // 2 - 60
        sw, sh = 140, 44
        arcade.draw_rect_filled(arcade.XYWH(sx, sy, sw, sh), arcade.color.DARK_GREEN)
        arcade.draw_rect_outline(arcade.XYWH(sx, sy, sw, sh), arcade.color.WHITE, 2)
        game.txt_start_btn.draw()


# ------------------------------------------------------------------ playing

def _draw_playing(game):
    game.txt_turn.draw()
    game.txt_message.draw()

    _draw_human_hand(game)
    _draw_opponent_area(game)
    _draw_side_info(game)


def _draw_human_hand(game):
    """Draw the human's hand face-up at the bottom."""
    if not game.hands:
        return
    hand = game.hands[0]
    positions = game.get_human_hand_positions()
    for i, card in enumerate(hand):
        if i < len(positions):
            cx, cy = positions[i]
            card.face_up = True
            draw_card(card, cx, cy)


def _draw_opponent_area(game):
    """Draw the opponent's hand as card backs when it's human's turn to draw."""
    if game.phase == PHASE_HUMAN_DRAW:
        opp = game.opponent_hand_index
        if opp < 0 or opp >= game.num_players:
            return
        opp_hand = game.hands[opp]
        positions = game._get_opponent_fan_positions(opp)

        # Label
        lbl = game.txt_player_labels[opp] if opp < len(game.txt_player_labels) else None
        if lbl and positions:
            lbl.text = f"{game.player_names[opp]}'s hand ({len(opp_hand)} cards)"
            lbl.x = WIDTH // 2
            lbl.y = HEIGHT - 120
            lbl.color = arcade.color.YELLOW
            lbl.draw()

        for i in range(len(opp_hand)):
            if i < len(positions):
                cx, cy = positions[i]
                # Highlight hovered card
                if i == game.hover_card_index:
                    arcade.draw_rect_filled(
                        arcade.XYWH(cx, cy, CARD_WIDTH + 6, CARD_HEIGHT + 6),
                        arcade.color.YELLOW,
                    )
                draw_card_back(cx, cy)

    elif game.phase == PHASE_AI_TURN:
        # Show which AI is drawing (just a label)
        idx = game.current_turn
        if 0 < idx < len(game.txt_player_labels):
            lbl = game.txt_player_labels[idx]
            lbl.text = f"{game.player_names[idx]} is drawing..."
            lbl.x = WIDTH // 2
            lbl.y = HEIGHT - 150
            lbl.color = arcade.color.YELLOW
            lbl.draw()


def _draw_side_info(game):
    """Draw player card counts along the right side."""
    if not game.player_names:
        return

    sx = 710
    sy = HEIGHT // 2 + 100
    for i in range(game.num_players):
        name = game.player_names[i]
        count = len(game.hands[i])
        is_out = i in game.out_players

        idx = min(i, len(game.txt_player_labels) - 1)
        lbl = game.txt_player_labels[idx]

        if is_out:
            lbl.text = f"{name}: SAFE"
            lbl.color = arcade.color.GREEN
        else:
            lbl.text = f"{name}: {count}"
            if i == game.current_turn:
                lbl.color = arcade.color.YELLOW
            else:
                lbl.color = arcade.color.WHITE
        lbl.x = sx
        lbl.y = sy - i * 30
        lbl.draw()

    # Discard count
    discard_count = len(game.discard_pile)
    if discard_count > 0:
        # Reuse a label slot temporarily -- draw it manually
        # We'll just position below the player list
        dy = sy - game.num_players * 30 - 20
        # We can reuse the last label if we're careful; better to just
        # use txt_message area or create a small hack.  Since we already
        # drew txt_player_labels above, we use index 3 if free.
        if game.num_players < 4:
            lbl = game.txt_player_labels[3]
            lbl.text = f"Pairs removed: {discard_count // 2}"
            lbl.color = arcade.color.LIGHT_GRAY
            lbl.x = sx
            lbl.y = dy
            lbl.draw()


# ------------------------------------------------------------------ game over

def _draw_game_over_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_BG
    )
    game.txt_game_over_msg.draw()
    game.txt_game_over_hint.draw()
