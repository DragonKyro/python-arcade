"""
Renderer for the Hearts game view.
All drawing calls for Hearts are centralized here.
NO ``from games.*`` imports -- constants are defined locally.
"""

import arcade
from utils.card import draw_card, draw_card_back, CARD_WIDTH, CARD_HEIGHT

# Window constants (must match the game view)
WIDTH = 800
HEIGHT = 600

# Layout
BUTTON_W = 100
BUTTON_H = 36

# Phases (duplicated to avoid importing from games.hearts)
PHASE_DEAL = "deal"
PHASE_PASS = "pass"
PHASE_PLAY = "play"
PHASE_TRICK_DONE = "trick_done"
PHASE_ROUND_OVER = "round_over"
PHASE_GAME_OVER = "game_over"

# Trick card positions (center of table, offset per player seat)
# Player 0=bottom, 1=left, 2=top, 3=right
TRICK_POSITIONS = [
    (WIDTH // 2, HEIGHT // 2 - 55),
    (WIDTH // 2 - 80, HEIGHT // 2),
    (WIDTH // 2, HEIGHT // 2 + 55),
    (WIDTH // 2 + 80, HEIGHT // 2),
]

# AI card-back display positions
AI_HAND_ANCHORS = [
    None,                           # player 0 is human
    (30, HEIGHT // 2 + 60),         # left - vertical stack
    (WIDTH // 2 - 160, HEIGHT - 55),  # top - horizontal
    (WIDTH - 30, HEIGHT // 2 + 60),   # right - vertical stack
]

TABLE_COLOR = (30, 100, 50)
TABLE_BORDER = (20, 70, 35)
OVERLAY_BG = (0, 0, 0, 180)

CARD_SCALE = 0.85


def draw(game):
    """Render the entire Hearts game state."""
    _draw_table(game)
    _draw_buttons(game)
    _draw_scores(game)

    if game.phase == PHASE_PASS:
        _draw_hands(game)
        _draw_pass_ui(game)
    elif game.phase in (PHASE_PLAY, PHASE_TRICK_DONE):
        _draw_hands(game)
        _draw_trick(game)
        if game.phase == PHASE_TRICK_DONE:
            _draw_trick_result(game)
    elif game.phase == PHASE_ROUND_OVER:
        _draw_round_over(game)
    elif game.phase == PHASE_GAME_OVER:
        _draw_game_over(game)

    game.txt_phase_info.draw()


# ------------------------------------------------------------------ table

def _draw_table(game):
    """Draw green table area."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, 380, 280), TABLE_COLOR
    )
    arcade.draw_rect_outline(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, 380, 280), TABLE_BORDER, 2
    )


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

    game.help_button.draw()
    game.txt_title.draw()


# ------------------------------------------------------------------ scores

def _draw_scores(game):
    game.txt_score_header.draw()
    for t in game.txt_score_lines:
        t.draw()
    # Player name labels
    for t in game.txt_player_names:
        t.draw()


# ------------------------------------------------------------------ hands

def _draw_hands(game):
    """Draw all 4 hands."""
    _draw_human_hand(game)
    for p in range(1, 4):
        _draw_ai_hand(game, p)


def _draw_human_hand(game):
    """Draw human hand at bottom, sorted, face up."""
    hand = game.hands[0]
    n = len(hand)
    if n == 0:
        return
    spacing = min(55, (WIDTH - 200) / max(n, 1))
    start_x = WIDTH / 2 - (n - 1) * spacing / 2
    cy = 70

    for i, card in enumerate(hand):
        cx = start_x + i * spacing
        # Highlight selected pass cards
        selected = i in game.selected_pass_cards
        if selected:
            arcade.draw_rect_filled(
                arcade.XYWH(cx, cy + CARD_HEIGHT * CARD_SCALE / 2 + 5,
                             CARD_WIDTH * CARD_SCALE + 4, 4),
                arcade.color.YELLOW
            )
            draw_card(card, cx, cy + 12, CARD_SCALE)
        else:
            # Highlight valid plays during play phase
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
    """Draw an AI hand as face-down cards."""
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
        # Top: horizontal row
        spacing = min(28, 300 / max(n, 1))
        start_x = ax
        for i in range(n):
            draw_card_back(start_x + i * spacing, ay, scale)
    elif player == 1:
        # Left: vertical column
        spacing = min(20, 200 / max(n, 1))
        for i in range(n):
            draw_card_back(ax, ay - i * spacing, scale)
    else:
        # Right: vertical column
        spacing = min(20, 200 / max(n, 1))
        for i in range(n):
            draw_card_back(ax, ay - i * spacing, scale)


# ------------------------------------------------------------------ trick

def _draw_trick(game):
    """Draw cards played in the current trick."""
    for player_idx, card in game.current_trick:
        tx, ty = TRICK_POSITIONS[player_idx]
        card.face_up = True
        draw_card(card, tx, ty, CARD_SCALE)


# ------------------------------------------------------------------ pass UI

def _draw_pass_ui(game):
    game.txt_turn_info.draw()
    if len(game.selected_pass_cards) == 3:
        btn_x, btn_y = WIDTH // 2, HEIGHT // 2 - 25
        arcade.draw_rect_filled(arcade.XYWH(btn_x, btn_y, 130, 36), arcade.color.DARK_BLUE)
        arcade.draw_rect_outline(arcade.XYWH(btn_x, btn_y, 130, 36), arcade.color.WHITE, 2)
        game.txt_pass_btn.draw()


# ------------------------------------------------------------------ trick result

def _draw_trick_result(game):
    """Brief overlay showing who won the trick."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2 + 135, 350, 30), (0, 0, 0, 160)
    )
    game.txt_trick_result.y = HEIGHT // 2 + 135
    game.txt_trick_result.draw()


# ------------------------------------------------------------------ round over

def _draw_round_over(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH - 60, 240), (20, 20, 40, 230)
    )
    arcade.draw_rect_outline(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH - 60, 240), arcade.color.WHITE, 2
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
