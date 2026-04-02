"""
Renderer for the War card game view.
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

# Game phases (duplicated to avoid importing from games.war)
PHASE_READY = "ready"
PHASE_REVEAL = "reveal"
PHASE_WAR_REVEAL = "war_reveal"
PHASE_GAME_OVER = "game_over"

# Layout
BUTTON_W = 100
BUTTON_H = 36

OVERLAY_BG = (0, 0, 0, 170)

# Deck positions
HUMAN_DECK_X = 200
HUMAN_DECK_Y = 250
AI_DECK_X = 600
AI_DECK_Y = 350

# Center battle area
CENTER_HUMAN_X = 340
CENTER_HUMAN_Y = 300
CENTER_AI_X = 460
CENTER_AI_Y = 300

# War card offsets
WAR_FACEDOWN_OFFSET = 18
WAR_FACEUP_OFFSET_X = 0
WAR_FACEUP_OFFSET_Y = -110


def draw(game):
    """Render the entire War game state."""
    _draw_buttons(game)

    if game.phase == PHASE_GAME_OVER:
        _draw_table(game)
        _draw_game_over_overlay(game)
    else:
        _draw_table(game)


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


# ------------------------------------------------------------------ table

def _draw_table(game):
    """Draw decks, revealed cards, war stack, and counts."""
    _draw_decks(game)
    _draw_revealed(game)
    _draw_war_stack(game)
    _draw_counts(game)
    _draw_status(game)


def _draw_decks(game):
    """Draw the two face-down deck piles."""
    # Human deck (bottom-left area)
    if game._total_human() > 0:
        draw_card_back(HUMAN_DECK_X, HUMAN_DECK_Y)
        # Stack effect
        if len(game.human_deck) + len(game.human_won_pile) > 1:
            arcade.draw_rect_outline(
                arcade.XYWH(HUMAN_DECK_X + 2, HUMAN_DECK_Y - 2, CARD_WIDTH, CARD_HEIGHT),
                (80, 80, 80), 1,
            )
    else:
        draw_empty_slot(HUMAN_DECK_X, HUMAN_DECK_Y)

    # AI deck (top-right area)
    if game._total_ai() > 0:
        draw_card_back(AI_DECK_X, AI_DECK_Y)
        if len(game.ai_deck) + len(game.ai_won_pile) > 1:
            arcade.draw_rect_outline(
                arcade.XYWH(AI_DECK_X + 2, AI_DECK_Y - 2, CARD_WIDTH, CARD_HEIGHT),
                (80, 80, 80), 1,
            )
    else:
        draw_empty_slot(AI_DECK_X, AI_DECK_Y)


def _draw_revealed(game):
    """Draw the currently revealed cards in the center."""
    if game.phase in (PHASE_REVEAL, PHASE_WAR_REVEAL, PHASE_GAME_OVER):
        if game.human_card is not None:
            game.human_card.face_up = True
            draw_card(game.human_card, CENTER_HUMAN_X, CENTER_HUMAN_Y)
        if game.ai_card is not None:
            game.ai_card.face_up = True
            draw_card(game.ai_card, CENTER_AI_X, CENTER_AI_Y)


def _draw_war_stack(game):
    """Draw face-down war cards and the war face-up cards dramatically."""
    if not game.in_war and game.phase != PHASE_WAR_REVEAL:
        return

    # Draw face-down war cards as a fanned stack
    for i, _card in enumerate(game.war_stack_human):
        ox = CENTER_HUMAN_X - 80 - i * WAR_FACEDOWN_OFFSET
        oy = CENTER_HUMAN_Y
        draw_card_back(ox, oy, scale=0.8)

    for i, _card in enumerate(game.war_stack_ai):
        ox = CENTER_AI_X + 80 + i * WAR_FACEDOWN_OFFSET
        oy = CENTER_AI_Y
        draw_card_back(ox, oy, scale=0.8)

    # War banner
    if game.phase == PHASE_WAR_REVEAL or game.in_war:
        game.txt_war_banner.draw()


def _draw_counts(game):
    """Draw card counts."""
    game.txt_human_count.draw()
    game.txt_ai_count.draw()


def _draw_status(game):
    """Draw status text and messages."""
    if game.phase == PHASE_READY:
        game.txt_status.draw()
    game.txt_message.draw()


# ------------------------------------------------------------------ game over

def _draw_game_over_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_BG
    )
    game.txt_game_over_msg.draw()
    game.txt_game_over_hint.draw()
