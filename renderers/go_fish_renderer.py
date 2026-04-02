"""
Renderer for Go Fish.
All arcade.draw_* calls live here.  No arcade.draw_text -- uses arcade.Text on game.
No imports from games.*.
"""

import arcade
from utils.card import (
    draw_card, draw_card_back, draw_empty_slot,
    CARD_WIDTH, CARD_HEIGHT,
)

# Window / layout constants
WIDTH = 800
HEIGHT = 600
TOP_BAR_HEIGHT = 50
SCALE = 1.0

CARD_W = CARD_WIDTH * SCALE
CARD_H = CARD_HEIGHT * SCALE

# Phases (duplicated to avoid importing from games)
PHASE_SETUP = "setup"
PHASE_SELECT_OPPONENT = "select_opponent"
PHASE_SELECT_RANK = "select_rank"
PHASE_RESULT = "result"
PHASE_AI_TURN = "ai_turn"
PHASE_GAME_OVER = "game_over"

# Layout
HAND_Y = 70
HAND_OVERLAP = 28

STOCK_X = WIDTH // 2
STOCK_Y = HEIGHT // 2 - 10

# AI positions (up to 3)
AI_POSITIONS = [
    (WIDTH // 2, HEIGHT - 100),
    (140, HEIGHT - 160),
    (WIDTH - 140, HEIGHT - 160),
]

# Book display area
BOOKS_Y = HEIGHT // 2 + 70
BOOKS_X_START = 60

# Colors
BG_COLOR = (30, 70, 120)
BAR_COLOR = (30, 40, 70)
BTN_COLOR = arcade.color.DARK_SLATE_BLUE
BTN_GREEN = arcade.color.DARK_GREEN
OVERLAY_BG = (0, 0, 0, 170)
BUTTON_W = 100
BUTTON_H = 36
HIGHLIGHT_COLOR = (255, 255, 100, 80)


def draw(game):
    """Render the full Go Fish game state."""
    _draw_background()
    _draw_top_bar(game)

    if game.phase == PHASE_SETUP:
        _draw_setup(game)
    elif game.phase == PHASE_GAME_OVER:
        _draw_table(game)
        _draw_game_over(game)
    else:
        _draw_table(game)


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
# Setup
# ------------------------------------------------------------------

def _draw_setup(game):
    game.txt_setup_prompt.draw()
    for i, (bx, by, bw, bh) in enumerate(game.setup_buttons):
        selected = (i + 1) == game.pending_num_ai
        bg = arcade.color.BLUE if selected else arcade.color.DARK_BLUE
        arcade.draw_rect_filled(arcade.XYWH(bx, by, bw, bh), bg)
        arcade.draw_rect_outline(arcade.XYWH(bx, by, bw, bh), arcade.color.WHITE, 2)
        game.txt_setup_labels[i].draw()

    if game.pending_num_ai > 0:
        sx, sy = WIDTH // 2, HEIGHT // 2 - 60
        arcade.draw_rect_filled(arcade.XYWH(sx, sy, 140, 44), BTN_GREEN)
        arcade.draw_rect_outline(arcade.XYWH(sx, sy, 140, 44), arcade.color.WHITE, 2)
        game.txt_start_btn.draw()


# ------------------------------------------------------------------
# Main table
# ------------------------------------------------------------------

def _draw_table(game):
    _draw_stock(game)
    _draw_books(game)
    _draw_status(game)
    _draw_human_hand(game)
    _draw_ai_areas(game)


def _draw_stock(game):
    if game.stock:
        draw_card_back(STOCK_X, STOCK_Y, SCALE)
    else:
        draw_empty_slot(STOCK_X, STOCK_Y, SCALE)
    game.txt_stock_count.draw()


def _draw_books(game):
    game.txt_books_label.draw()
    # Draw each player's book count
    for i, player in enumerate(game.players):
        books = player["books"]
        name = player["name"]
        txt = game.txt_book_counts[i]
        txt.text = f"{name}: {len(books)} books"
        txt.draw()


def _draw_status(game):
    game.txt_status.draw()


def _draw_human_hand(game):
    hand = game.players[0]["hand"]
    if not hand:
        return
    total_w = CARD_W + (len(hand) - 1) * HAND_OVERLAP
    start_x = WIDTH / 2 - total_w / 2 + CARD_W / 2
    for i, card in enumerate(hand):
        x = start_x + i * HAND_OVERLAP
        y = HAND_Y
        card.face_up = True

        # Highlight if selecting rank and card matches hovered or selected opponent
        if game.phase == PHASE_SELECT_RANK and game.selected_card_index == i:
            arcade.draw_rect_filled(
                arcade.XYWH(x, y, CARD_W + 6, CARD_H + 6), HIGHLIGHT_COLOR,
            )

        draw_card(card, x, y, SCALE)


def _draw_ai_areas(game):
    for ai_idx in range(len(game.players) - 1):
        if ai_idx >= len(AI_POSITIONS):
            break
        player = game.players[ai_idx + 1]
        px, py = AI_POSITIONS[ai_idx]
        hand = player["hand"]
        p_index = ai_idx + 1

        # Highlight selectable opponent
        if game.phase == PHASE_SELECT_OPPONENT and len(hand) > 0:
            arcade.draw_rect_filled(
                arcade.XYWH(px, py, 160, 90), (255, 255, 100, 40)
            )

        # Highlight selected opponent
        if game.selected_opponent == p_index:
            arcade.draw_rect_outline(
                arcade.XYWH(px, py, 160, 90), arcade.color.YELLOW, 3
            )

        # Name
        game.txt_ai_names[ai_idx].x = px
        game.txt_ai_names[ai_idx].y = py + 35
        game.txt_ai_names[ai_idx].draw()

        # Card count
        game.txt_ai_counts[ai_idx].x = px
        game.txt_ai_counts[ai_idx].y = py + 18
        game.txt_ai_counts[ai_idx].text = f"{len(hand)} cards"
        game.txt_ai_counts[ai_idx].draw()

        # Card backs fanned
        n = min(len(hand), 7)
        if n > 0:
            fan_w = CARD_W * 0.5 + (n - 1) * 18
            sx = px - fan_w / 2 + CARD_W * 0.25
            for j in range(n):
                draw_card_back(sx + j * 18, py - 15, SCALE * 0.65)


# ------------------------------------------------------------------
# Game over
# ------------------------------------------------------------------

def _draw_game_over(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), OVERLAY_BG
    )
    game.txt_game_over_msg.draw()
    game.txt_game_over_score.draw()
    game.txt_game_over_hint.draw()
