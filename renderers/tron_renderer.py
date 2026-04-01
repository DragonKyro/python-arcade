"""
Tron Light Cycles renderer.
No arcade.draw_text(), no ``from games.*`` imports.
"""

import arcade


# Neon colour palette -------------------------------------------------------
# Each entry: (trail_colour, head_colour)
PLAYER_COLORS = {
    1: ((0, 220, 255),    (100, 255, 255)),   # cyan
    2: ((255, 40, 40),    (255, 130, 130)),    # red
    3: ((0, 220, 60),     (100, 255, 140)),    # green
    4: ((255, 220, 0),    (255, 255, 130)),    # yellow
}

GRID_BORDER_COLOR = (60, 60, 60)
BG_COLOR = (0, 0, 0)


def draw(game):
    """Render the full Tron game state.

    *game* is expected to be a ``TronView`` instance exposing the attributes
    used below (grid, players, phase, text objects, etc.).
    """
    _draw_background(game)
    _draw_grid_border(game)
    if game.grid:
        _draw_trails(game)
        _draw_heads(game)
    _draw_ui(game)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _draw_background(game):
    """Fill with black."""
    arcade.draw_lbwh_rectangle_filled(0, 0, game.window.width, game.window.height, BG_COLOR)


def _draw_grid_border(game):
    ox, oy = game.grid_offset_x, game.grid_offset_y
    w = game.grid_w * game.cell_size
    h = game.grid_h * game.cell_size
    arcade.draw_rect_outline(arcade.XYWH(ox + w / 2, oy + h / 2, w, h), GRID_BORDER_COLOR, 2)


def _draw_trails(game):
    """Draw every trail cell as a small filled rectangle."""
    if not game.grid:
        return
    cs = game.cell_size
    ox, oy = game.grid_offset_x, game.grid_offset_y

    for y in range(len(game.grid)):
        for x in range(len(game.grid[y])):
            pid = game.grid[y][x]
            if pid != 0:
                color = PLAYER_COLORS.get(pid, ((180, 180, 180), (255, 255, 255)))[0]
                sx = ox + x * cs
                sy = oy + y * cs
                arcade.draw_lbwh_rectangle_filled(sx, sy, cs, cs, color)


def _draw_heads(game):
    """Draw living players' heads slightly larger/brighter."""
    cs = game.cell_size
    ox, oy = game.grid_offset_x, game.grid_offset_y
    pad = max(1, cs // 5)

    for p in game.players:
        if not p['alive']:
            continue
        hx, hy = p['pos']
        color = PLAYER_COLORS.get(p['id'], ((180, 180, 180), (255, 255, 255)))[1]
        sx = ox + hx * cs - pad
        sy = oy + hy * cs - pad
        arcade.draw_lbwh_rectangle_filled(sx, sy, cs + pad * 2, cs + pad * 2, color)


def _draw_ui(game):
    """Draw pre-built arcade.Text objects stored on the game view."""
    # Phase-specific text objects
    if game.phase == 'setup':
        for txt in game.setup_texts:
            txt.draw()
    elif game.phase == 'playing':
        if hasattr(game, 'status_text') and game.status_text:
            game.status_text.draw()
    elif game.phase == 'gameover':
        for txt in game.gameover_texts:
            txt.draw()

    # Persistent buttons
    for btn in game.button_texts:
        btn.draw()
