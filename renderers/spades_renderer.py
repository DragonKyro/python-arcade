"""
Renderer for the Spades game view.
All drawing calls for Spades are centralized here.
NO ``from games.*`` imports -- constants are defined locally.
"""

import arcade
from utils.card import draw_card, draw_card_back, CARD_WIDTH, CARD_HEIGHT

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
BUTTON_W = 100
BUTTON_H = 36

# Phases (duplicated to avoid importing from games.spades)
PHASE_BID = "bid"
PHASE_PLAY = "play"
PHASE_TRICK_DONE = "trick_done"
PHASE_ROUND_OVER = "round_over"
PHASE_GAME_OVER = "game_over"

# Trick card positions per player seat
TRICK_POSITIONS = [
    (WIDTH // 2, HEIGHT // 2 - 55),   # bottom (human)
    (WIDTH // 2 - 80, HEIGHT // 2),    # left (opponent)
    (WIDTH // 2, HEIGHT // 2 + 55),    # top (partner)
    (WIDTH // 2 + 80, HEIGHT // 2),    # right (opponent)
]

# AI card-back anchors
AI_HAND_ANCHORS = [
    None,
    (30, HEIGHT // 2 + 60),
    (WIDTH // 2 - 160, HEIGHT - 55),
    (WIDTH - 30, HEIGHT // 2 + 60),
]

TABLE_COLOR = (25, 60, 100)
TABLE_BORDER = (15, 40, 70)
OVERLAY_BG = (0, 0, 0, 180)

CARD_SCALE = 0.85


def draw(game):
    """Render the entire Spades game state."""
    _draw_table(game)
    _draw_buttons(game)
    _draw_scores(game)
    _draw_hands(game)

    if game.phase == PHASE_BID:
        _draw_bid_ui(game)
    elif game.phase in (PHASE_PLAY, PHASE_TRICK_DONE):
        _draw_trick(game)
        _draw_bid_info(game)
        _draw_tricks_won_info(game)
        if game.phase == PHASE_TRICK_DONE:
            _draw_trick_result(game)
    elif game.phase == PHASE_ROUND_OVER:
        _draw_round_over(game)
    elif game.phase == PHASE_GAME_OVER:
        _draw_game_over(game)

    game.txt_phase_info.draw()


# ------------------------------------------------------------------ table

def _draw_table(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, 380, 280), TABLE_COLOR
    )
    arcade.draw_rect_outline(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, 380, 280), TABLE_BORDER, 2
    )


# ------------------------------------------------------------------ buttons

def _draw_buttons(game):
    bx, by = 60, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.DARK_GRAY)
    arcade.draw_rect_outline(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.WHITE, 2)
    game.txt_btn_back.draw()

    nx, ny = WIDTH - 70, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.WHITE, 2)
    game.txt_btn_new_game.draw()

    game.help_button.draw()
    game.txt_title.draw()


# ------------------------------------------------------------------ scores

def _draw_scores(game):
    game.txt_score_header.draw()
    for t in game.txt_team_scores:
        t.draw()
    for t in game.txt_bags_info:
        t.draw()
    for t in game.txt_player_names:
        t.draw()


# ------------------------------------------------------------------ hands

def _draw_hands(game):
    _draw_human_hand(game)
    for p in range(1, 4):
        _draw_ai_hand(game, p)


def _draw_human_hand(game):
    hand = game.hands[0]
    n = len(hand)
    if n == 0:
        return
    spacing = min(55, (WIDTH - 200) / max(n, 1))
    start_x = WIDTH / 2 - (n - 1) * spacing / 2
    cy = 70

    for i, card in enumerate(hand):
        cx = start_x + i * spacing
        highlight = False
        if game.phase == PHASE_PLAY and game.current_player == 0:
            valid = game._get_valid_plays_for(0)
            if card in valid:
                highlight = True
        if highlight:
            draw_card(card, cx, cy + 4, CARD_SCALE)
        else:
            draw_card(card, cx, cy, CARD_SCALE)


def _draw_ai_hand(game, player):
    hand = game.hands[player]
    n = len(hand)
    if n == 0:
        return

    anchor = AI_HAND_ANCHORS[player]
    if anchor is None:
        return

    ax, ay = anchor
    scale = 0.5

    if player == 2:
        spacing = min(28, 300 / max(n, 1))
        start_x = ax
        for i in range(n):
            draw_card_back(start_x + i * spacing, ay, scale)
    elif player == 1:
        spacing = min(20, 200 / max(n, 1))
        for i in range(n):
            draw_card_back(ax, ay - i * spacing, scale)
    else:
        spacing = min(20, 200 / max(n, 1))
        for i in range(n):
            draw_card_back(ax, ay - i * spacing, scale)


# ------------------------------------------------------------------ trick

def _draw_trick(game):
    for player_idx, card in game.current_trick:
        tx, ty = TRICK_POSITIONS[player_idx]
        card.face_up = True
        draw_card(card, tx, ty, CARD_SCALE)


# ------------------------------------------------------------------ bid UI

def _draw_bid_ui(game):
    """Draw bidding controls and current bids."""
    # Show all bid labels
    for t in game.txt_bid_labels:
        t.draw()

    if game.current_player == 0:
        by_val = HEIGHT // 2 - 60
        # Minus button
        mx, my = WIDTH // 2 - 40, by_val
        arcade.draw_rect_filled(arcade.XYWH(mx, my, 32, 32), arcade.color.DARK_GRAY)
        arcade.draw_rect_outline(arcade.XYWH(mx, my, 32, 32), arcade.color.WHITE, 2)
        game.txt_bid_minus.draw()

        # Value
        game.txt_bid_value.text = "Nil" if game.human_bid_value == 0 else str(game.human_bid_value)
        game.txt_bid_value.draw()

        # Plus button
        px, py = WIDTH // 2 + 40, by_val
        arcade.draw_rect_filled(arcade.XYWH(px, py, 32, 32), arcade.color.DARK_GRAY)
        arcade.draw_rect_outline(arcade.XYWH(px, py, 32, 32), arcade.color.WHITE, 2)
        game.txt_bid_plus.draw()

        game.txt_bid_prompt.draw()

        # Submit button
        sx, sy = WIDTH // 2, HEIGHT // 2 - 100
        arcade.draw_rect_filled(arcade.XYWH(sx, sy, 120, 36), arcade.color.DARK_BLUE)
        arcade.draw_rect_outline(arcade.XYWH(sx, sy, 120, 36), arcade.color.WHITE, 2)
        game.txt_bid_submit.draw()


# ------------------------------------------------------------------ bid info during play

def _draw_bid_info(game):
    for t in game.txt_bid_labels:
        t.draw()


def _draw_tricks_won_info(game):
    """Show tricks won near each player name."""
    positions = [
        (WIDTH // 2 + 60, 155),
        (65, HEIGHT // 2 - 35),
        (WIDTH // 2 + 60, HEIGHT - 95),
        (WIDTH - 65, HEIGHT // 2 - 35),
    ]
    for i, (px, py) in enumerate(positions):
        if game.bids[i] is not None:
            bid_str = "Nil" if game.bids[i] == 0 else str(game.bids[i])
            # Use raw drawing for small dynamic text
            _draw_info_text(game, px, py, f"Won: {game.tricks_won[i]}/{bid_str}")


def _draw_info_text(game, x, y, text):
    """Helper to draw small info text using a temporary arcade.Text."""
    # We reuse a pattern - create and cache on game object
    key = f"_spades_info_{x}_{y}"
    if not hasattr(game, key):
        setattr(game, key, arcade.Text(
            "", x, y, arcade.color.LIGHT_GRAY, 10,
            anchor_x="center", anchor_y="center",
        ))
    txt_obj = getattr(game, key)
    txt_obj.text = text
    txt_obj.draw()


# ------------------------------------------------------------------ trick result

def _draw_trick_result(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2 + 135, 350, 30), (0, 0, 0, 160)
    )
    game.txt_trick_result.draw()


# ------------------------------------------------------------------ round over

def _draw_round_over(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH - 60, 260), (20, 20, 40, 230)
    )
    arcade.draw_rect_outline(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH - 60, 260), arcade.color.WHITE, 2
    )
    game.txt_round_summary.draw()
    for t in game.txt_round_details:
        t.draw()
    game.txt_continue.draw()


# ------------------------------------------------------------------ game over

def _draw_game_over(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_BG
    )
    game.txt_game_over_msg.draw()
    game.txt_game_over_hint.draw()
