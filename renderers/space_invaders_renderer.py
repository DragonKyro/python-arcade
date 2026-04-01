"""
Renderer for the Space Invaders game.
All drawing code extracted from games/space_invaders.py.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
BOTTOM_BAR_HEIGHT = 40

# Player
PLAYER_WIDTH = 44
PLAYER_HEIGHT = 20
PLAYER_TURRET_W = 6
PLAYER_TURRET_H = 10
PLAYER_Y = BOTTOM_BAR_HEIGHT + 30

# Shield
SHIELD_BLOCK_SIZE = 6

# Colors
BG_COLOR = (0, 0, 0)
LINE_COLOR = (205, 214, 244)
OVERLAY_COLOR = (0, 0, 0, 200)
SCORE_COLOR = (255, 255, 255)
PLAYER_COLOR = (100, 255, 100)
PLAYER_TURRET_COLOR = (150, 255, 150)
SHIELD_COLOR = (80, 200, 80)


def draw(game):
    """Render the entire Space Invaders game state."""
    # --- Draw play area ---

    # Shields
    for block in game.shields:
        if block[2]:
            arcade.draw_rect_filled(
                arcade.XYWH(block[0], block[1], SHIELD_BLOCK_SIZE, SHIELD_BLOCK_SIZE),
                SHIELD_COLOR,
            )

    # Aliens
    alive_aliens = game._alive_aliens()
    for a in alive_aliens:
        a.draw(game.alien_anim_frame)

    # Alien bullets
    for b in game.alien_bullets:
        b.draw()

    # Player bullets
    for b in game.player_bullets:
        b.draw()

    # Player ship (draw with blinking if invincible)
    draw_player = True
    if game.player_invincible > 0:
        if int(game.player_invincible * 10) % 2 == 0:
            draw_player = False

    if draw_player and not game.game_over:
        _draw_player_ship(game)

    # UFO
    game.ufo.draw()

    # UFO score display
    if game.ufo_score_display:
        ux, uy = game.ufo_score_display
        game.txt_ufo_score.text = f"{game.ufo.points}"
        game.txt_ufo_score.x = ux
        game.txt_ufo_score.y = uy
        game.txt_ufo_score.draw()

    # --- Top bar ---
    _draw_top_bar(game)

    # --- Bottom bar ---
    _draw_bottom_bar(game)

    # --- Overlays ---
    if game.game_over:
        _draw_game_over(game)


def _draw_player_ship(game):
    """Draw the player's ship."""
    px, py = game.player_x, PLAYER_Y
    # Main body
    arcade.draw_rect_filled(
        arcade.XYWH(px, py, PLAYER_WIDTH, PLAYER_HEIGHT), PLAYER_COLOR
    )
    # Turret
    arcade.draw_rect_filled(
        arcade.XYWH(px, py + PLAYER_HEIGHT / 2 + PLAYER_TURRET_H / 2,
                     PLAYER_TURRET_W, PLAYER_TURRET_H),
        PLAYER_TURRET_COLOR,
    )
    # Angled sides for a more ship-like look
    arcade.draw_triangle_filled(
        px - PLAYER_WIDTH / 2, py - PLAYER_HEIGHT / 2,
        px - PLAYER_WIDTH / 2 - 4, py - PLAYER_HEIGHT / 2,
        px - PLAYER_WIDTH / 2, py + PLAYER_HEIGHT / 2,
        PLAYER_COLOR,
    )
    arcade.draw_triangle_filled(
        px + PLAYER_WIDTH / 2, py - PLAYER_HEIGHT / 2,
        px + PLAYER_WIDTH / 2 + 4, py - PLAYER_HEIGHT / 2,
        px + PLAYER_WIDTH / 2, py + PLAYER_HEIGHT / 2,
        PLAYER_COLOR,
    )


def _draw_top_bar(game):
    """Draw the top bar with score, wave, and buttons."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT - TOP_BAR_HEIGHT // 2, WIDTH, TOP_BAR_HEIGHT),
        BG_COLOR,
    )
    arcade.draw_line(0, HEIGHT - TOP_BAR_HEIGHT, WIDTH, HEIGHT - TOP_BAR_HEIGHT, LINE_COLOR, 1)

    # Score
    game.txt_score.text = f"SCORE: {game.score}"
    game.txt_score.draw()
    game.txt_high_score.text = f"HI: {game.high_score}"
    game.txt_high_score.draw()

    # Wave number
    game.txt_wave.text = f"WAVE {game.wave}"
    game.txt_wave.draw()

    # Buttons
    hover_back = game.btn_back.contains(game.mouse_x, game.mouse_y)
    hover_help = game.btn_help.contains(game.mouse_x, game.mouse_y)
    game.btn_back.draw(hover=hover_back)
    game.btn_help.draw(hover=hover_help)


def _draw_bottom_bar(game):
    """Draw the bottom bar with lives."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, BOTTOM_BAR_HEIGHT // 2, WIDTH, BOTTOM_BAR_HEIGHT),
        BG_COLOR,
    )
    arcade.draw_line(0, BOTTOM_BAR_HEIGHT, WIDTH, BOTTOM_BAR_HEIGHT, LINE_COLOR, 1)

    # Lives as ship icons
    game.txt_lives_label.draw()
    for i in range(game.lives):
        lx = 80 + i * 35
        ly = BOTTOM_BAR_HEIGHT // 2
        arcade.draw_rect_filled(arcade.XYWH(lx, ly, 20, 10), PLAYER_COLOR)
        arcade.draw_rect_filled(arcade.XYWH(lx, ly + 7, 3, 5), PLAYER_TURRET_COLOR)


def _draw_game_over(game):
    """Draw the game over overlay."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_COLOR
    )
    game.txt_game_over.draw()
    game.txt_final_score.text = f"Final Score: {game.score}  |  Wave: {game.wave}"
    game.txt_final_score.draw()
    game.txt_restart_hint.draw()
