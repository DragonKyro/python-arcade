"""FreeCell Solitaire — game logic."""

import copy
import arcade
from pages.rules import RulesView
from renderers import freecell_renderer
from renderers.freecell_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT, PLAYING, WON,
    UNDO_BTN_X, UNDO_BTN_Y, UNDO_BTN_W, UNDO_BTN_H,
    get_clicked_location,
)
from utils.card import create_deck, SUITS

# Foundation suit order (one foundation per suit)
FOUNDATION_SUITS = SUITS  # ["c", "d", "h", "s"]


class FreeCellView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self._create_texts()
        self._init_game()

    # ------------------------------------------------------------------
    # Text objects (no arcade.draw_text)
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
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_undo = arcade.Text(
            "Undo", UNDO_BTN_X, UNDO_BTN_Y, arcade.color.WHITE,
            font_size=13, anchor_x="center", anchor_y="center",
        )
        self.txt_you_win = arcade.Text(
            "YOU WIN!", WIDTH / 2, HEIGHT / 2 + 20,
            arcade.color.YELLOW, font_size=44,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_hint = arcade.Text(
            "All foundations complete!", WIDTH / 2, HEIGHT / 2 - 25,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )

    # ------------------------------------------------------------------
    # Game initialisation
    # ------------------------------------------------------------------
    def _init_game(self):
        deck = create_deck(shuffled=True)
        for card in deck:
            card.face_up = True

        # 8 tableau columns: first 4 get 7 cards, last 4 get 6 cards
        self.tableau = [[] for _ in range(8)]
        idx = 0
        for col in range(8):
            count = 7 if col < 4 else 6
            for _ in range(count):
                self.tableau[col].append(deck[idx])
                idx += 1

        self.free_cells = [None, None, None, None]
        # Each foundation is a list of cards (bottom=Ace … top=King)
        self.foundations = [[] for _ in range(4)]
        self.selected = None  # None or ("free_cell", i) or ("tableau", col, row)
        self.undo_stack = []  # list of snapshots
        self.game_state = PLAYING

    # ------------------------------------------------------------------
    # Snapshot / undo
    # ------------------------------------------------------------------
    def _snapshot(self):
        """Save a deep copy of the game state for undo."""
        return {
            "tableau": [list(col) for col in self.tableau],
            "free_cells": list(self.free_cells),
            "foundations": [list(f) for f in self.foundations],
        }

    def _restore(self, snap):
        self.tableau = snap["tableau"]
        self.free_cells = snap["free_cells"]
        self.foundations = snap["foundations"]
        self.selected = None

    def _undo(self):
        if self.undo_stack:
            if self.game_state == WON:
                self.game_state = PLAYING
            self._restore(self.undo_stack.pop())

    # ------------------------------------------------------------------
    # Move helpers
    # ------------------------------------------------------------------
    def _num_free_cells(self):
        return sum(1 for c in self.free_cells if c is None)

    def _num_empty_columns(self):
        return sum(1 for col in self.tableau if not col)

    def _max_movable(self, dest_is_empty_col=False):
        """Max stack size that can be moved at once."""
        free = self._num_free_cells()
        empty = self._num_empty_columns()
        # If moving to an empty column, that column can't be used as a helper
        if dest_is_empty_col:
            empty = max(0, empty - 1)
        return (free + 1) * (2 ** empty)

    def _is_valid_tableau_stack(self, cards):
        """Check if a list of cards forms a valid descending alternating-color run."""
        for i in range(len(cards) - 1):
            top, bot = cards[i], cards[i + 1]
            if bot.value != top.value - 1:
                return False
            if bot.color == top.color:
                return False
        return True

    def _can_place_on_tableau(self, card, column):
        """Can card be placed on top of this tableau column?"""
        if not column:
            return True  # any card can go on empty column
        top = column[-1]
        return card.value == top.value - 1 and card.color != top.color

    def _foundation_index_for(self, card):
        """Return foundation index where this card could go, or -1."""
        for i, suit in enumerate(FOUNDATION_SUITS):
            if card.suit != suit:
                continue
            pile = self.foundations[i]
            if card.value == 1 and not pile:
                return i
            if pile and card.value == pile[-1].value + 1:
                return i
        return -1

    def _should_auto_foundation(self, card):
        """Return True if card can safely auto-move to foundation.

        A card can auto-move when all cards of opposite color with lower rank
        are already on their foundations.
        """
        fi = self._foundation_index_for(card)
        if fi == -1:
            return False
        # Aces and twos are always safe
        if card.value <= 2:
            return True
        # Check that all opposite-color cards with value < card.value
        # are already on foundations
        needed_value = card.value - 1
        for i, suit in enumerate(FOUNDATION_SUITS):
            from utils.card import SUIT_COLORS
            if SUIT_COLORS[suit] == card.color:
                continue  # same color — skip
            pile = self.foundations[i]
            top_val = pile[-1].value if pile else 0
            if top_val < needed_value:
                return False
        return True

    def _try_auto_foundation(self):
        """Repeatedly auto-move safe cards to foundations."""
        moved = True
        while moved:
            moved = False
            # Check free cells
            for i, card in enumerate(self.free_cells):
                if card is not None and self._should_auto_foundation(card):
                    fi = self._foundation_index_for(card)
                    self.foundations[fi].append(card)
                    self.free_cells[i] = None
                    moved = True
            # Check tableau tops
            for col in self.tableau:
                if col:
                    card = col[-1]
                    if self._should_auto_foundation(card):
                        fi = self._foundation_index_for(card)
                        self.foundations[fi].append(card)
                        col.pop()
                        moved = True

    def _check_win(self):
        if all(len(f) == 13 for f in self.foundations):
            self.game_state = WON

    # ------------------------------------------------------------------
    # Perform moves
    # ------------------------------------------------------------------
    def _move_to_foundation(self, card, source_type, source_idx, source_row=None):
        """Attempt to move card to its foundation. Returns True if successful."""
        fi = self._foundation_index_for(card)
        if fi == -1:
            return False
        snap = self._snapshot()
        if source_type == "free_cell":
            self.free_cells[source_idx] = None
        elif source_type == "tableau":
            self.tableau[source_idx].pop()
        self.foundations[fi].append(card)
        self.undo_stack.append(snap)
        self.selected = None
        self._try_auto_foundation()
        self._check_win()
        return True

    def _move_to_free_cell(self, card, source_type, source_idx):
        """Move a single card to the first empty free cell. Returns True if successful."""
        slot = -1
        for i in range(4):
            if self.free_cells[i] is None:
                slot = i
                break
        if slot == -1:
            return False
        snap = self._snapshot()
        if source_type == "free_cell":
            self.free_cells[source_idx] = None
        elif source_type == "tableau":
            self.tableau[source_idx].pop()
        self.free_cells[slot] = card
        self.undo_stack.append(snap)
        self.selected = None
        self._try_auto_foundation()
        self._check_win()
        return True

    def _move_stack_to_tableau(self, cards, src_col, dest_col):
        """Move a stack of cards from one tableau column to another."""
        dest_empty = not self.tableau[dest_col]
        if not self._can_place_on_tableau(cards[0], self.tableau[dest_col]):
            return False
        if len(cards) > self._max_movable(dest_is_empty_col=dest_empty):
            return False
        snap = self._snapshot()
        # Remove cards from source
        del self.tableau[src_col][-len(cards):]
        self.tableau[dest_col].extend(cards)
        self.undo_stack.append(snap)
        self.selected = None
        self._try_auto_foundation()
        self._check_win()
        return True

    def _move_free_to_tableau(self, card, fc_idx, dest_col):
        """Move a card from a free cell to a tableau column."""
        if not self._can_place_on_tableau(card, self.tableau[dest_col]):
            return False
        snap = self._snapshot()
        self.free_cells[fc_idx] = None
        self.tableau[dest_col].append(card)
        self.undo_stack.append(snap)
        self.selected = None
        self._try_auto_foundation()
        self._check_win()
        return True

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------
    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    # ------------------------------------------------------------------
    # Arcade callbacks
    # ------------------------------------------------------------------
    def on_draw(self):
        self.clear()
        freecell_renderer.draw(self)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.Z:
            self._undo()

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
        if self._hit_test_button(x, y, WIDTH - 135, bar_y, 40, 35):
            rules_view = RulesView(
                "FreeCell", "freecell.txt", None,
                self.menu_view, existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        # Undo button
        if self._hit_test_button(x, y, UNDO_BTN_X, UNDO_BTN_Y, UNDO_BTN_W, UNDO_BTN_H):
            self._undo()
            return

        if self.game_state != PLAYING:
            return

        clicked = get_clicked_location(self, x, y)

        # --- Nothing selected yet: select something ---
        if self.selected is None:
            if clicked is None:
                return
            kind = clicked[0]
            if kind == "free_cell":
                idx = clicked[1]
                if self.free_cells[idx] is not None:
                    self.selected = ("free_cell", idx)
            elif kind == "tableau":
                col, row = clicked[1], clicked[2]
                if row == -1:
                    return  # clicked empty column with nothing selected
                column = self.tableau[col]
                # Select the clicked card and any valid stack below it
                sub = column[row:]
                if self._is_valid_tableau_stack(sub):
                    self.selected = ("tableau", col, row)
            # Clicking a foundation does nothing for selection
            return

        # --- Already have a selection: try to place ---
        sel = self.selected

        # Determine source card(s)
        if sel[0] == "free_cell":
            src_card = self.free_cells[sel[1]]
            src_cards = [src_card]
        else:  # tableau
            src_col, src_row = sel[1], sel[2]
            src_cards = self.tableau[src_col][src_row:]
            src_card = src_cards[0]

        # Click on nothing — deselect
        if clicked is None:
            self.selected = None
            return

        dest_kind = clicked[0]

        # --- Destination: foundation ---
        if dest_kind == "foundation":
            if len(src_cards) == 1:
                self._move_to_foundation(
                    src_card, sel[0],
                    sel[1] if sel[0] == "free_cell" else sel[1],
                )
            else:
                self.selected = None
            return

        # --- Destination: free cell ---
        if dest_kind == "free_cell":
            dest_idx = clicked[1]
            if self.free_cells[dest_idx] is None and len(src_cards) == 1:
                # Move to that specific free cell
                snap = self._snapshot()
                if sel[0] == "free_cell":
                    self.free_cells[sel[1]] = None
                else:
                    self.tableau[sel[1]].pop()
                self.free_cells[dest_idx] = src_card
                self.undo_stack.append(snap)
                self.selected = None
                self._try_auto_foundation()
                self._check_win()
            elif self.free_cells[dest_idx] is not None:
                # Re-select the card in that free cell
                self.selected = ("free_cell", dest_idx)
            else:
                self.selected = None
            return

        # --- Destination: tableau ---
        if dest_kind == "tableau":
            dest_col = clicked[1]
            # Moving from free cell
            if sel[0] == "free_cell":
                if not self._move_free_to_tableau(src_card, sel[1], dest_col):
                    # If clicking on a card in destination, re-select it
                    dest_row = clicked[2]
                    if dest_row >= 0 and self.tableau[dest_col]:
                        sub = self.tableau[dest_col][dest_row:]
                        if self._is_valid_tableau_stack(sub):
                            self.selected = ("tableau", dest_col, dest_row)
                            return
                    self.selected = None
                return
            # Moving from tableau
            src_col_idx = sel[1]
            if dest_col == src_col_idx:
                # Clicked same column — deselect
                self.selected = None
                return
            if not self._move_stack_to_tableau(src_cards, src_col_idx, dest_col):
                # If single card, try free cell as fallback? No — just re-select
                dest_row = clicked[2]
                if dest_row >= 0 and self.tableau[dest_col]:
                    sub = self.tableau[dest_col][dest_row:]
                    if self._is_valid_tableau_stack(sub):
                        self.selected = ("tableau", dest_col, dest_row)
                        return
                self.selected = None
            return

    def on_mouse_release(self, x, y, button, modifiers):
        pass
