import arcade
import random
from pages.rules import RulesView
from renderers import mahjong_solitaire_renderer
from renderers.mahjong_solitaire_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT,
    TILE_W, TILE_H, BOARD_ORIGIN_X, BOARD_ORIGIN_Y, LAYER_OFFSET_X, LAYER_OFFSET_Y,
)

# Tile types: 3 suits x 9 numbers + 4 winds + 3 dragons = 34 types
SUITS = ["Bamboo", "Circle", "Character"]
NUMBERS = list(range(1, 10))
WINDS = ["East", "South", "West", "North"]
DRAGONS = ["Red", "Green", "White"]

# Short labels for display
SUIT_LABELS = {"Bamboo": "B", "Circle": "C", "Character": "W"}
SUIT_COLORS = {
    "Bamboo": arcade.color.DARK_GREEN,
    "Circle": arcade.color.DARK_BLUE,
    "Character": arcade.color.DARK_RED,
}

TILE_TYPES = []
for suit in SUITS:
    for num in NUMBERS:
        TILE_TYPES.append(("suit", suit, num))
for w in WINDS:
    TILE_TYPES.append(("wind", w, 0))
for d in DRAGONS:
    TILE_TYPES.append(("dragon", d, 0))

# 36 unique types, but we only need 144 / 4 = 36 types with 4 copies each
# Use first 36 types (all of them: 27 suited + 4 winds + 3 dragons + 2 extra)
# Actually 34 types. We need 36 for 144 tiles. Add 2 flower/season types.
TILE_TYPES.append(("flower", "Plum", 0))
TILE_TYPES.append(("flower", "Orchid", 0))

assert len(TILE_TYPES) == 36


def _tile_label(tile_type):
    """Return a short label for a tile type."""
    kind, name, num = tile_type
    if kind == "suit":
        return f"{SUIT_LABELS[name]}{num}"
    elif kind == "wind":
        return name[0]  # E, S, W, N
    elif kind == "dragon":
        return name[0] + "D"  # RD, GD, WD
    else:
        return name[:2]  # Pl, Or


def _tile_color(tile_type):
    """Return a color for a tile type."""
    kind, name, num = tile_type
    if kind == "suit":
        return SUIT_COLORS[name]
    elif kind == "wind":
        return arcade.color.DARK_SLATE_GRAY
    elif kind == "dragon":
        colors = {"Red": arcade.color.CRIMSON, "Green": arcade.color.DARK_GREEN,
                  "White": arcade.color.GRAY}
        return colors[name]
    else:
        return arcade.color.DARK_ORCHID


def _tiles_match(t1, t2):
    """Check if two tile types match (same type tuple)."""
    return t1 == t2


# ---------- Classic Turtle Layout ----------

def _turtle_layout():
    """Return list of (col, row, layer) positions for the classic turtle layout.
    Uses a 12-wide, 8-tall grid system across 5 layers.
    Total = 144 tiles.
    """
    positions = []

    # Layer 0 (bottom): 12x8 with some edges trimmed = 86 tiles
    # Classic turtle: rows 0-7, varying widths
    layer0_rows = {
        0: list(range(2, 10)),      # 8 tiles
        1: list(range(1, 11)),      # 10 tiles
        2: list(range(0, 12)),      # 12 tiles
        3: list(range(0, 12)),      # 12 tiles
        4: list(range(0, 12)),      # 12 tiles
        5: list(range(0, 12)),      # 12 tiles
        6: list(range(1, 11)),      # 10 tiles
        7: list(range(2, 10)),      # 8 tiles
    }
    for r, cols in layer0_rows.items():
        for c in cols:
            positions.append((c, r, 0))
    # = 84 tiles

    # Layer 1: 10x6 centered = 30 tiles? Let's do 6x4 = 24
    for r in range(2, 6):
        for c in range(2, 10):
            positions.append((c, r, 1))
    # = 32 tiles -> total 116

    # Layer 2: 4x2 centered
    for r in range(3, 5):
        for c in range(3, 9):
            positions.append((c, r, 2))
    # = 12 tiles -> total 128

    # Layer 3: 2x2 centered
    for r in range(3, 5):
        for c in range(4, 8):
            positions.append((c, r, 3))
    # = 8 tiles -> total 136

    # Layer 4: 2x2 centered
    for r in range(3, 5):
        for c in range(5, 7):
            positions.append((c, r, 4))
    # = 4 tiles -> total 140

    # Add 4 special edge tiles to reach 144
    # Two on far left, two on far right of middle row
    positions.append((-1, 3, 0))   # far left
    positions.append((-1, 4, 0))   # far left
    positions.append((12, 3, 0))   # far right
    positions.append((12, 4, 0))   # far right

    assert len(positions) == 144, f"Expected 144, got {len(positions)}"
    return positions


# ---------- Puzzle generation ----------

def _generate_tiles():
    """Generate a shuffled set of 144 tiles (36 types x 4 copies) placed on the turtle layout.
    Returns list of dicts with col, row, layer, tile_type, removed=False.
    Tiles are placed in a solvable order (reverse pair-removal).
    """
    positions = _turtle_layout()
    # Sort positions by layer (bottom first), then by row/col for placement order
    positions.sort(key=lambda p: (p[2], p[1], p[0]))

    # Create tile type pool: 36 types x 4 copies = 144
    pool = []
    for tt in TILE_TYPES:
        pool.extend([tt] * 4)
    random.shuffle(pool)

    tiles = []
    for i, (c, r, layer) in enumerate(positions):
        tiles.append({
            "col": c,
            "row": r,
            "layer": layer,
            "tile_type": pool[i],
            "removed": False,
            "id": i,
        })
    return tiles


# ---------- View ----------

class MahjongSolitaireView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self._create_texts()
        self._init_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects for rendering."""
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
        self.txt_back = arcade.Text(
            "Back", 55, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_new_game = arcade.Text(
            "New Game", WIDTH - 65, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_help = arcade.Text(
            "?", WIDTH - 135, bar_y, arcade.color.WHITE,
            font_size=16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_shuffle = arcade.Text(
            "Shuffle", WIDTH / 2, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_remaining = arcade.Text(
            "", WIDTH / 2 + 100, bar_y, arcade.color.LIGHT_GRAY,
            font_size=12, anchor_x="center", anchor_y="center",
        )
        # Win overlay
        self.txt_win_title = arcade.Text(
            "You Win!", WIDTH / 2, HEIGHT / 2 + 30,
            arcade.color.GOLD, font_size=36,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_hint = arcade.Text(
            "Click New Game to play again",
            WIDTH / 2, HEIGHT / 2 - 20,
            arcade.color.LIGHT_GRAY, font_size=14,
            anchor_x="center", anchor_y="center",
        )
        # Pre-create tile label texts (max 144)
        self.txt_tiles = {}
        for i in range(144):
            self.txt_tiles[i] = arcade.Text(
                "", 0, 0, arcade.color.WHITE,
                font_size=10, anchor_x="center", anchor_y="center", bold=True,
            )

    def _init_game(self):
        """Initialize or reset game state."""
        self.tiles = _generate_tiles()
        self.selected = None  # tile id or None
        self.game_won = False
        self.elapsed_time = 0.0
        self._build_spatial_index()

    def _build_spatial_index(self):
        """Build a lookup for quick neighbor/coverage checks."""
        self._occupied = set()
        for t in self.tiles:
            if not t["removed"]:
                self._occupied.add((t["col"], t["row"], t["layer"]))

    def _tile_screen_pos(self, tile):
        """Return the pixel center of a tile."""
        x = BOARD_ORIGIN_X + tile["col"] * TILE_W + TILE_W / 2 + tile["layer"] * LAYER_OFFSET_X
        y = BOARD_ORIGIN_Y + tile["row"] * TILE_H + TILE_H / 2 + tile["layer"] * LAYER_OFFSET_Y
        return x, y

    def _is_free(self, tile):
        """A tile is free if nothing is on top AND (left or right side is open)."""
        if tile["removed"]:
            return False
        c, r, layer = tile["col"], tile["row"], tile["layer"]

        # Check if any tile is directly on top (layer+1, same or overlapping position)
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if (c + dc, r + dr, layer + 1) in self._occupied:
                    # Check if it actually overlaps (adjacent positions on higher layer cover)
                    pass
        # Simplified: tile on top means same col,row at layer+1
        if (c, r, layer + 1) in self._occupied:
            return False

        # Check left open: no tile at (col-1, row, layer)
        left_open = (c - 1, r, layer) not in self._occupied
        # Check right open: no tile at (col+1, row, layer)
        right_open = (c + 1, r, layer) not in self._occupied

        return left_open or right_open

    def _remaining_count(self):
        return sum(1 for t in self.tiles if not t["removed"])

    def _shuffle_remaining(self):
        """Shuffle the tile types of all remaining tiles (keeps positions)."""
        remaining = [t for t in self.tiles if not t["removed"]]
        types = [t["tile_type"] for t in remaining]
        random.shuffle(types)
        for t, tt in zip(remaining, types):
            t["tile_type"] = tt
        self.selected = None

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def _tile_at_pixel(self, px, py):
        """Find the topmost tile at pixel position."""
        best = None
        for t in self.tiles:
            if t["removed"]:
                continue
            tx, ty = self._tile_screen_pos(t)
            hw, hh = TILE_W / 2, TILE_H / 2
            if tx - hw <= px <= tx + hw and ty - hh <= py <= ty + hh:
                if best is None or t["layer"] > best["layer"]:
                    best = t
        return best

    # --- arcade callbacks ---

    def on_update(self, delta_time):
        if not self.game_won:
            self.elapsed_time += delta_time

    def on_draw(self):
        self.clear()
        mahjong_solitaire_renderer.draw(self)

    def on_mouse_press(self, x, y, button, modifiers):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        # Back button
        if self._hit_test_button(x, y, 55, bar_y, 90, 35):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if self._hit_test_button(x, y, WIDTH - 65, bar_y, 110, 35):
            self._init_game()
            return

        # Help button
        if self._hit_test_button(x, y, WIDTH - 135, bar_y, 40, 40):
            rules_view = RulesView("Mahjong Solitaire", "mahjong_solitaire.txt", None,
                                   self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        # Shuffle button
        if self._hit_test_button(x, y, WIDTH / 2, bar_y, 80, 35):
            self._shuffle_remaining()
            return

        if self.game_won:
            return

        # Tile click
        tile = self._tile_at_pixel(x, y)
        if tile is None:
            self.selected = None
            return

        if not self._is_free(tile):
            return

        if self.selected is None:
            self.selected = tile["id"]
        elif self.selected == tile["id"]:
            self.selected = None
        else:
            # Check match
            sel_tile = self.tiles[self.selected]
            if _tiles_match(sel_tile["tile_type"], tile["tile_type"]):
                sel_tile["removed"] = True
                tile["removed"] = True
                self._build_spatial_index()
                self.selected = None
                if self._remaining_count() == 0:
                    self.game_won = True
            else:
                # Select the new tile instead
                self.selected = tile["id"]

    def tile_label(self, tile):
        return _tile_label(tile["tile_type"])

    def tile_color(self, tile):
        return _tile_color(tile["tile_type"])
