"""
Klondike Solitaire — classic card game.

7 tableau piles, 4 foundation piles, stock and waste.
Supports draw-1 and draw-3 modes, drag-and-drop, double-click auto-move.
"""

import time
import arcade
from pages.rules import RulesView
from renderers import klondike_renderer
from renderers.klondike_renderer import WIDTH, HEIGHT, TOP_BAR_HEIGHT
from utils.card import (
    Card, create_deck, point_in_card,
    CARD_WIDTH, CARD_HEIGHT, RANK_VALUES, SUITS,
)

# Layout constants (matching renderer)
SCALE = 1.0
CARD_W = CARD_WIDTH * SCALE
CARD_H = CARD_HEIGHT * SCALE
TABLEAU_TOP_Y = HEIGHT - TOP_BAR_HEIGHT - 130
TABLEAU_X_START = 60
TABLEAU_X_GAP = 105
FOUNDATION_X_START = TABLEAU_X_START + 3 * TABLEAU_X_GAP
FOUNDATION_Y = HEIGHT - TOP_BAR_HEIGHT - 30
STOCK_X = TABLEAU_X_START
STOCK_Y = FOUNDATION_Y
WASTE_X = STOCK_X + TABLEAU_X_GAP
WASTE_Y = FOUNDATION_Y
FACE_DOWN_OFFSET = 20
FACE_UP_OFFSET = 30

# Double-click threshold (seconds)
DOUBLE_CLICK_TIME = 0.35


class KlondikeView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.draw_count = 1  # 1 or 3
        self._create_texts()
        self._init_game()

    # ------------------------------------------------------------------
    # Text objects (no arcade.draw_text allowed)
    # ------------------------------------------------------------------

    def _create_texts(self):
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
        self.txt_moves = arcade.Text(
            "Moves: 0", 200, bar_y, arcade.color.LIGHT_GRAY,
            font_size=12, anchor_x="center", anchor_y="center",
        )
        self.txt_timer = arcade.Text(
            "0:00", 310, bar_y, arcade.color.LIGHT_GRAY,
            font_size=12, anchor_x="center", anchor_y="center",
        )
        self.txt_draw_mode = arcade.Text(
            "Draw 1", 420, bar_y, arcade.color.WHITE,
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

    # ------------------------------------------------------------------
    # Game state
    # ------------------------------------------------------------------

    def _init_game(self):
        deck = create_deck(shuffled=True)
        # 7 tableau piles
        self.tableau = [[] for _ in range(7)]
        idx = 0
        for i in range(7):
            for j in range(i + 1):
                self.tableau[i].append(deck[idx])
                idx += 1
            self.tableau[i][-1].face_up = True  # top card face up

        # Stock = remaining cards
        self.stock = deck[idx:]
        for c in self.stock:
            c.face_up = False
        self.waste = []

        # 4 foundations (one per suit, indexed 0-3 matching SUITS order)
        self.foundations = [[] for _ in range(4)]

        # Drag state
        self.dragging = []          # list of Card being dragged
        self.drag_source = None     # ("tableau", pile_idx) | ("waste",) | ("foundation", idx)
        self.drag_offset_x = 0.0
        self.drag_offset_y = 0.0

        # Counters
        self.move_count = 0
        self.elapsed_time = 0.0
        self.game_won = False

        # Double-click detection
        self._last_click_time = 0.0
        self._last_click_pos = (0, 0)

        self._update_card_positions()

    # ------------------------------------------------------------------
    # Position helpers
    # ------------------------------------------------------------------

    def _update_card_positions(self):
        """Assign x/y to every card for rendering and hit-testing."""
        # Stock
        for c in self.stock:
            c.x = STOCK_X
            c.y = STOCK_Y

        # Waste — show up to 3 fanned
        visible = min(len(self.waste), 3)
        for i, c in enumerate(self.waste):
            if i < len(self.waste) - visible:
                c.x = WASTE_X
                c.y = WASTE_Y
            else:
                fan_idx = i - (len(self.waste) - visible)
                c.x = WASTE_X + fan_idx * 18
                c.y = WASTE_Y

        # Foundations
        for fi in range(4):
            fx = FOUNDATION_X_START + fi * TABLEAU_X_GAP
            for c in self.foundations[fi]:
                c.x = fx
                c.y = FOUNDATION_Y

        # Tableau
        for ti in range(7):
            tx = TABLEAU_X_START + ti * TABLEAU_X_GAP
            y = TABLEAU_TOP_Y
            for ci, c in enumerate(self.tableau[ti]):
                c.x = tx
                c.y = y
                if c.face_up:
                    y -= FACE_UP_OFFSET
                else:
                    y -= FACE_DOWN_OFFSET

    def _foundation_x(self, fi):
        return FOUNDATION_X_START + fi * TABLEAU_X_GAP

    # ------------------------------------------------------------------
    # Card finding / hit testing
    # ------------------------------------------------------------------

    def _card_at(self, px, py):
        """Return (source_tuple, card_index_in_pile) for topmost card at px,py.
        source_tuple: ('stock',) | ('waste',) | ('foundation', i) | ('tableau', i)
        card_index_in_pile: index of the card clicked within its pile.
        Returns (None, None) if nothing hit.
        """
        # Check waste top (visible fan)
        if self.waste:
            visible = min(len(self.waste), 3)
            for i in range(len(self.waste) - 1, max(len(self.waste) - visible - 1, -1), -1):
                c = self.waste[i]
                if point_in_card(px, py, c.x, c.y, SCALE):
                    if i == len(self.waste) - 1:
                        return ("waste",), i
                    return None, None  # can't pick non-top waste

        # Check stock
        if self.stock and point_in_card(px, py, STOCK_X, STOCK_Y, SCALE):
            return ("stock",), 0

        # Empty stock slot (click to recycle)
        if not self.stock and point_in_card(px, py, STOCK_X, STOCK_Y, SCALE):
            return ("stock_empty",), 0

        # Foundations (top card only)
        for fi in range(4):
            fx = self._foundation_x(fi)
            if self.foundations[fi]:
                c = self.foundations[fi][-1]
                if point_in_card(px, py, c.x, c.y, SCALE):
                    return ("foundation", fi), len(self.foundations[fi]) - 1
            else:
                if point_in_card(px, py, fx, FOUNDATION_Y, SCALE):
                    return ("foundation_empty", fi), 0

        # Tableau — iterate top-to-bottom (last card first) for correct overlap
        for ti in range(7):
            pile = self.tableau[ti]
            for ci in range(len(pile) - 1, -1, -1):
                c = pile[ci]
                if point_in_card(px, py, c.x, c.y, SCALE):
                    if c.face_up:
                        return ("tableau", ti), ci
                    return None, None  # face-down card
            # Empty tableau slot
            if not pile:
                slot_x = TABLEAU_X_START + ti * TABLEAU_X_GAP
                if point_in_card(px, py, slot_x, TABLEAU_TOP_Y, SCALE):
                    return ("tableau_empty", ti), 0

        return None, None

    # ------------------------------------------------------------------
    # Move validation
    # ------------------------------------------------------------------

    def _can_place_on_tableau(self, card, pile_idx):
        pile = self.tableau[pile_idx]
        if not pile:
            return card.rank == "k"  # only Kings on empty
        top = pile[-1]
        return (top.face_up and
                card.color != top.color and
                card.value == top.value - 1)

    def _can_place_on_foundation(self, card, found_idx):
        pile = self.foundations[found_idx]
        if not pile:
            return card.rank == "a" and SUITS[found_idx] == card.suit
        top = pile[-1]
        return top.suit == card.suit and card.value == top.value + 1

    def _find_foundation_for(self, card):
        """Return foundation index if this card can go on a foundation, else -1."""
        for fi in range(4):
            if self._can_place_on_foundation(card, fi):
                return fi
        return -1

    # ------------------------------------------------------------------
    # Auto-flip and win detection
    # ------------------------------------------------------------------

    def _auto_flip_tableau(self):
        for pile in self.tableau:
            if pile and not pile[-1].face_up:
                pile[-1].flip()

    def _check_win(self):
        if all(len(f) == 13 for f in self.foundations):
            self.game_won = True

    # ------------------------------------------------------------------
    # Stock dealing
    # ------------------------------------------------------------------

    def _deal_from_stock(self):
        if not self.stock:
            # Recycle waste back to stock
            if self.waste:
                self.stock = list(reversed(self.waste))
                for c in self.stock:
                    c.face_up = False
                self.waste = []
                self.move_count += 1
            return

        count = min(self.draw_count, len(self.stock))
        for _ in range(count):
            card = self.stock.pop()
            card.face_up = True
            self.waste.append(card)
        self.move_count += 1

    # ------------------------------------------------------------------
    # Auto-move: move obvious cards to foundations
    # ------------------------------------------------------------------

    def _auto_move_to_foundation(self, card, source):
        """Try to move a single card to its foundation. Returns True if moved."""
        fi = self._find_foundation_for(card)
        if fi < 0:
            return False

        # Remove from source
        if source[0] == "waste":
            self.waste.pop()
        elif source[0] == "tableau":
            self.tableau[source[1]].pop()
            self._auto_flip_tableau()
        elif source[0] == "foundation":
            self.foundations[source[1]].pop()

        self.foundations[fi].append(card)
        self.move_count += 1
        self._update_card_positions()
        self._check_win()
        return True

    # ------------------------------------------------------------------
    # Arcade callbacks
    # ------------------------------------------------------------------

    def on_update(self, delta_time):
        if not self.game_won:
            self.elapsed_time += delta_time
            minutes = int(self.elapsed_time) // 60
            seconds = int(self.elapsed_time) % 60
            self.txt_timer.text = f"{minutes}:{seconds:02d}"
            self.txt_moves.text = f"Moves: {self.move_count}"

    def on_draw(self):
        self.clear()
        klondike_renderer.draw(self)

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        # --- Top-bar buttons ---
        if self._hit_btn(x, y, 55, bar_y, 90, 35):
            self.window.show_view(self.menu_view)
            return
        if self._hit_btn(x, y, WIDTH - 65, bar_y, 110, 35):
            self._init_game()
            return
        if self._hit_btn(x, y, WIDTH - 135, bar_y, 40, 40):
            rules_view = RulesView("Klondike Solitaire", "klondike.txt", None,
                                   self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return
        # Draw mode toggle
        if self._hit_btn(x, y, 420, bar_y, 70, 35):
            self.draw_count = 3 if self.draw_count == 1 else 1
            self.txt_draw_mode.text = f"Draw {self.draw_count}"
            return

        if self.game_won:
            return

        # --- Double-click detection ---
        now = time.time()
        is_double = (now - self._last_click_time < DOUBLE_CLICK_TIME and
                     abs(x - self._last_click_pos[0]) < 10 and
                     abs(y - self._last_click_pos[1]) < 10)
        self._last_click_time = now
        self._last_click_pos = (x, y)

        source, ci = self._card_at(x, y)
        if source is None:
            return

        # Stock click
        if source[0] == "stock" or source[0] == "stock_empty":
            self._deal_from_stock()
            self._update_card_positions()
            return

        # Double-click: auto-move to foundation
        if is_double and source[0] in ("waste", "tableau", "foundation"):
            card = self._get_card_from_source(source, ci)
            if card is not None:
                # Only auto-move single cards (top of pile for tableau)
                if source[0] == "tableau" and ci == len(self.tableau[source[1]]) - 1:
                    self._auto_move_to_foundation(card, source)
                    return
                elif source[0] == "waste":
                    self._auto_move_to_foundation(card, source)
                    return

        # Begin drag
        if source[0] == "waste":
            card = self.waste[-1]
            self.dragging = [card]
            self.drag_source = ("waste",)
            self.drag_offset_x = card.x - x
            self.drag_offset_y = card.y - y

        elif source[0] == "tableau":
            ti = source[1]
            # Grab from ci to end of pile (stack drag)
            self.dragging = self.tableau[ti][ci:]
            self.drag_source = ("tableau", ti)
            top_card = self.dragging[0]
            self.drag_offset_x = top_card.x - x
            self.drag_offset_y = top_card.y - y

        elif source[0] == "foundation":
            fi = source[1]
            card = self.foundations[fi][-1]
            self.dragging = [card]
            self.drag_source = ("foundation", fi)
            self.drag_offset_x = card.x - x
            self.drag_offset_y = card.y - y

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.dragging:
            return
        base_x = x + self.drag_offset_x
        base_y = y + self.drag_offset_y
        for i, card in enumerate(self.dragging):
            card.x = base_x
            card.y = base_y - i * FACE_UP_OFFSET

    def on_mouse_release(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT or not self.dragging:
            return

        dropped = False
        card = self.dragging[0]

        # Try dropping on foundation (single card only)
        if len(self.dragging) == 1:
            for fi in range(4):
                fx = self._foundation_x(fi)
                fy = FOUNDATION_Y
                if self._overlaps(card.x, card.y, fx, fy):
                    if self._can_place_on_foundation(card, fi):
                        self._remove_from_source()
                        self.foundations[fi].append(card)
                        self.move_count += 1
                        dropped = True
                        break

        # Try dropping on tableau
        if not dropped:
            for ti in range(7):
                tx = TABLEAU_X_START + ti * TABLEAU_X_GAP
                if self.tableau[ti]:
                    top = self.tableau[ti][-1]
                    ty = top.y
                else:
                    ty = TABLEAU_TOP_Y
                if self._overlaps(card.x, card.y, tx, ty):
                    if self._can_place_on_tableau(card, ti):
                        self._remove_from_source()
                        self.tableau[ti].extend(self.dragging)
                        self.move_count += 1
                        dropped = True
                        break

        self.dragging = []
        self.drag_source = None
        self._auto_flip_tableau()
        self._update_card_positions()
        self._check_win()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _hit_btn(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def _overlaps(self, ax, ay, bx, by):
        """Check if two card-sized rects overlap enough to count as a drop target."""
        return abs(ax - bx) < CARD_W * 0.6 and abs(ay - by) < CARD_H * 0.8

    def _get_card_from_source(self, source, ci):
        if source[0] == "waste" and self.waste:
            return self.waste[-1]
        if source[0] == "tableau":
            pile = self.tableau[source[1]]
            if 0 <= ci < len(pile):
                return pile[ci]
        if source[0] == "foundation":
            pile = self.foundations[source[1]]
            if pile:
                return pile[-1]
        return None

    def _remove_from_source(self):
        """Remove the dragged cards from their source pile."""
        src = self.drag_source
        if src[0] == "waste":
            self.waste.pop()
        elif src[0] == "tableau":
            ti = src[1]
            count = len(self.dragging)
            self.tableau[ti] = self.tableau[ti][:-count]
        elif src[0] == "foundation":
            self.foundations[src[1]].pop()
