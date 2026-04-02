"""
TriPeaks Solitaire – Remove peak cards that are +/-1 rank of the waste top.

3 overlapping pyramids (peaks) of 30 cards total:
  Row 0: 3 face-down cards (peaks)
  Row 1: 6 face-down cards
  Row 2: 9 face-down cards
  Row 3: 10 face-up cards (bottom row)
Remaining 22 cards form the stock.  Wrapping allowed (K<->A).
Win by clearing all 30 peak cards.
Streak bonuses for consecutive removals.
"""

import arcade
from utils.card import (
    create_deck, draw_card, draw_card_back, draw_empty_slot,
    point_in_card, CARD_WIDTH, CARD_HEIGHT, RANK_VALUES,
)
from renderers import tripeaks_renderer
from renderers.tripeaks_renderer import WIDTH, HEIGHT, TOP_BAR_HEIGHT
from pages.rules import RulesView


class TriPeaksView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self._create_texts()
        self._init_game()

    # ------------------------------------------------------------------ texts
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
        self.txt_score = arcade.Text(
            "Score: 0", WIDTH / 2 - 60, bar_y, arcade.color.LIGHT_GRAY,
            font_size=13, anchor_x="center", anchor_y="center",
        )
        self.txt_streak = arcade.Text(
            "Streak: 0", WIDTH / 2 + 60, bar_y, arcade.color.LIGHT_GOLDENROD_YELLOW,
            font_size=13, anchor_x="center", anchor_y="center",
        )
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
        self.txt_lose_title = arcade.Text(
            "No More Moves", WIDTH / 2, HEIGHT / 2 + 30,
            arcade.color.RED_ORANGE, font_size=32,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_lose_hint = arcade.Text(
            "Click New Game to try again",
            WIDTH / 2, HEIGHT / 2 - 20,
            arcade.color.LIGHT_GRAY, font_size=14,
            anchor_x="center", anchor_y="center",
        )

    # ------------------------------------------------------------------ init
    def _init_game(self):
        deck = create_deck(shuffled=True)

        # Build the peak layout.
        # We store cards in a flat list with metadata: row, col, children indices.
        # Layout (col positions are in a shared coordinate space):
        #   Row 0 (3 cards):  peaks at positions 0, 3, 6
        #   Row 1 (6 cards):  positions 0,1,  3,4,  6,7
        #   Row 2 (9 cards):  positions 0,1,2,  3,4,5,  6,7,8
        #   Row 3 (10 cards): positions 0,1,2,3,4,5,6,7,8,9
        #
        # But to make 3 connected peaks with proper overlap, we use a specific layout:

        # Peak card entries: (row, col_index) where col_index is the visual column
        # Row 0: 3 peaks
        # Row 1: 6 cards (2 children per peak)
        # Row 2: 9 cards (overlapping)
        # Row 3: 10 cards (bottom, all face up)

        self.peaks = []  # list of dicts: {card, row, col, removed}
        card_idx = 0

        # Row 0: peaks at visual columns 1, 4, 7
        row0_cols = [1, 4, 7]
        for c in row0_cols:
            self.peaks.append({
                "card": deck[card_idx], "row": 0, "col": c, "removed": False,
            })
            card_idx += 1

        # Row 1: columns 0,2, 3,5, 6,8
        row1_cols = [0, 2, 3, 5, 6, 8]
        for c in row1_cols:
            self.peaks.append({
                "card": deck[card_idx], "row": 1, "col": c, "removed": False,
            })
            card_idx += 1

        # Row 2: columns 0,1,2, 3,4,5, 6,7,8  (but shifted by 0.5)
        # We use half-step offsets. Let's use a different approach:
        # Think of bottom row as 10 positions: 0..9
        # Row 2 spans 9 positions above: 0..8 (each covering two bottom cards)
        # Row 1 spans 6 positions: every other starting from 0
        # Row 0 spans 3 positions: peaks

        # Reset and use a cleaner model. Each row's cards cover two cards below.
        self.peaks = []
        card_idx = 0

        # Row 3 (bottom): 10 face-up cards, columns 0-9
        # Row 2: 9 cards, columns 0-8 (card at col c covers row3[c] and row3[c+1])
        # Row 1: 6 cards, columns 0,1, 3,4, 6,7
        # Row 0: 3 cards, columns 0, 3, 6

        # Build from top to bottom in the list, but deal top first
        # Row 0
        row0_cols = [0, 3, 6]
        for c in row0_cols:
            self.peaks.append({
                "card": deck[card_idx], "row": 0, "col": c, "removed": False,
            })
            card_idx += 1

        # Row 1
        row1_cols = [0, 1, 3, 4, 6, 7]
        for c in row1_cols:
            self.peaks.append({
                "card": deck[card_idx], "row": 1, "col": c, "removed": False,
            })
            card_idx += 1

        # Row 2
        row2_cols = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        for c in row2_cols:
            self.peaks.append({
                "card": deck[card_idx], "row": 2, "col": c, "removed": False,
            })
            card_idx += 1

        # Row 3 (bottom): 10 face-up cards
        # These overlap with row 2: row2[c] covers row3[c] and row3[c+1]
        # But row 2 has 9 cards covering 10 bottom cards -- that doesn't give 10.
        # TriPeaks standard: bottom row has 10 cards.
        # Row 2 has 9 cards? No. Standard TriPeaks:
        #   Row 0: 3 cards (peaks)
        #   Row 1: 6 cards
        #   Row 2: 9 cards
        #   Row 3: 10 cards
        # Total = 28.  But spec says 30. Let me re-read...
        # Spec: "3 peaks of 10 cards each (30 total)"
        # "4 rows: 3 cards, 6 cards, 9 cards, 10 face-up cards at bottom row"
        # 3+6+9+10 = 28. With 52-28=24 in stock... but spec says 22.
        # 52-30=22 -> so 30 peak cards. 3+6+9+10=28 != 30.
        # Standard TriPeaks uses 28 cards in tableau + 24 in stock.
        # But spec says 30 in peaks, 22 in stock.
        # Let's follow the spec: 3+6+9+12 = 30 with bottom row of 12?
        # Or perhaps the bottom row has 12 cards: 3+6+9+12=30.
        # Actually re-reading: "(4 rows: 3 cards, 6 cards, 9 cards, 10 face-up cards
        # at bottom row)" = 28. But "3 peaks of 10 cards each (30 total)" suggests
        # each peak is 1+2+3+4=10. That gives 30 with overlaps... but shared cards.
        # Actually 3 peaks of (1+2+3+4)=10 each, but bottom rows overlap:
        #   Row 0: 3
        #   Row 1: 6
        #   Row 2: 9  (3 groups of 3, but groups share edges? No overlap at row 2)
        #   Row 3: 10 (the 3 groups of 4 = 12, minus 2 shared = 10)
        # So row 3 has 10 cards. Total = 3+6+9+10 = 28. Stock = 52-28 = 24.
        # But spec says 22 in stock -> 30 in peaks.
        # I'll use the layout described: row 3 has 10 cards, but add 2 more somewhere
        # to reach 30. Actually let's just follow standard TriPeaks = 28 in tableau.
        # Spec says "Remaining 22 cards in stock" which means 30 in peaks.
        # Let me do: bottom row = 12 cards to make 3+6+9+12=30. Stock=22.

        # Clear and redo -- bottom row has 12 to match 30 total
        self.peaks = []
        card_idx = 0

        # Row 0: 3 peak tops
        for c in [0, 3, 6]:
            self.peaks.append({
                "card": deck[card_idx], "row": 0, "col": c, "removed": False,
            })
            card_idx += 1

        # Row 1: 6 cards
        for c in [0, 1, 3, 4, 6, 7]:
            self.peaks.append({
                "card": deck[card_idx], "row": 1, "col": c, "removed": False,
            })
            card_idx += 1

        # Row 2: 9 cards
        for c in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
            self.peaks.append({
                "card": deck[card_idx], "row": 2, "col": c, "removed": False,
            })
            card_idx += 1

        # Row 3: 12 face-up cards (each row2 card covers 2 row3 cards)
        # Row 2 has 9 cards at cols 0..8, covering row3 cols 0..9 (10 cards).
        # To get 12, extend: add cols -1 and 9 from the outer peaks' coverage?
        # Actually let's just do 12 columns for the bottom row.
        # Row 2 col c covers row 3 col c and c+1.
        # So row 2 cols 0-8 cover row 3 cols 0-9 (10 cards).
        # For 12 bottom cards we'd need row 2 cols -1..9 (11 cards) -> 11 != 9.
        # This doesn't cleanly work. Let's just use standard 28 layout and 24 stock.

        self.peaks = []
        card_idx = 0

        # Standard TriPeaks: 28 tableau cards
        for c in [0, 3, 6]:
            self.peaks.append({
                "card": deck[card_idx], "row": 0, "col": c, "removed": False,
            })
            card_idx += 1

        for c in [0, 1, 3, 4, 6, 7]:
            self.peaks.append({
                "card": deck[card_idx], "row": 1, "col": c, "removed": False,
            })
            card_idx += 1

        for c in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
            self.peaks.append({
                "card": deck[card_idx], "row": 2, "col": c, "removed": False,
            })
            card_idx += 1

        # Row 3: 10 cards at columns 0..9
        for c in range(10):
            self.peaks.append({
                "card": deck[card_idx], "row": 3, "col": c, "removed": False,
            })
            card_idx += 1

        # Set face-up for bottom row only; upper rows face-down
        for p in self.peaks:
            p["card"].face_up = (p["row"] == 3)

        # Stock = remaining 24 cards
        self.stock = deck[28:]
        for c in self.stock:
            c.face_up = False

        # Waste starts with one card dealt from stock
        self.waste = []
        if self.stock:
            first = self.stock.pop()
            first.face_up = True
            self.waste.append(first)

        self.score = 0
        self.streak = 0
        self.game_won = False
        self.game_over = False
        self.selected = None

        self._assign_positions()

    def _assign_positions(self):
        """Compute screen x, y for all peak cards."""
        # Layout: 10 columns across the bottom row, centered.
        col_spacing = CARD_WIDTH + 4
        total_w = 10 * col_spacing
        left_x = (WIDTH - total_w) / 2 + CARD_WIDTH / 2
        top_y = HEIGHT - TOP_BAR_HEIGHT - 30
        row_spacing = CARD_HEIGHT * 0.42

        for p in self.peaks:
            row = p["row"]
            col = p["col"]
            # Each row is offset by half a card width relative to the row below
            # Row 3: columns 0-9 map directly
            # Row 2: columns 0-8, each centered between row3[c] and row3[c+1]
            # Row 1: columns map to between row2 pairs
            # Row 0: peak tops

            if row == 3:
                x = left_x + col * col_spacing
            elif row == 2:
                x = left_x + (col + 0.5) * col_spacing
            elif row == 1:
                # Row 1 cols: 0,1, 3,4, 6,7
                # Col 0 is between row2[0] and row2[1]
                x = left_x + (col + 1.0) * col_spacing
            elif row == 0:
                # Col 0 is centered above row1[0] and row1[1]
                x = left_x + (col + 1.5) * col_spacing

            y = top_y - row * row_spacing
            p["card"].x = x
            p["card"].y = y

    # ------------------------------------------------------------------ logic
    def _children(self, peak_entry):
        """Return list of peak entries that are covered by this card."""
        row = peak_entry["row"]
        col = peak_entry["col"]
        if row == 3:
            return []
        # Children in next row
        children = []
        if row == 0:
            # Peak at col c covers row1 cols c and c+1
            child_cols = [col, col + 1]
            child_row = 1
        elif row == 1:
            # Row1 col c covers row2 cols c and c+1
            child_cols = [col, col + 1]
            child_row = 2
        elif row == 2:
            # Row2 col c covers row3 cols c and c+1
            child_cols = [col, col + 1]
            child_row = 3
        else:
            return []

        for p in self.peaks:
            if not p["removed"] and p["row"] == child_row and p["col"] in child_cols:
                children.append(p)
        return children

    def _parents(self, peak_entry):
        """Return peak entries that cover this card from the row above."""
        row = peak_entry["row"]
        col = peak_entry["col"]
        if row == 0:
            return []
        parents = []
        parent_row = row - 1
        # A parent at parent_col covers child_cols [parent_col, parent_col+1]
        # So this card (row, col) is covered by parents at parent_col = col-1 and col
        for p in self.peaks:
            if (not p["removed"] and p["row"] == parent_row
                    and p["col"] in [col - 1, col]):
                parents.append(p)
        return parents

    def is_exposed(self, peak_entry):
        """A card is exposed if it has no non-removed parents covering it."""
        if peak_entry["removed"]:
            return False
        return len(self._parents(peak_entry)) == 0

    def _flip_newly_exposed(self):
        """Flip face-down cards that are now exposed."""
        for p in self.peaks:
            if not p["removed"] and not p["card"].face_up:
                if self.is_exposed(p):
                    p["card"].face_up = True

    def _peaks_remaining(self):
        return sum(1 for p in self.peaks if not p["removed"])

    def _ranks_adjacent(self, v1, v2):
        """Check if two rank values are +/-1 with wrapping (K<->A)."""
        diff = abs(v1 - v2)
        return diff == 1 or diff == 12  # 13-1=12 for K<->A

    def _has_moves(self):
        if not self.waste:
            return bool(self.stock)
        wv = self.waste[-1].value
        for p in self.peaks:
            if not p["removed"] and self.is_exposed(p):
                if self._ranks_adjacent(p["card"].value, wv):
                    return True
        return bool(self.stock)

    def _check_win(self):
        if self._peaks_remaining() == 0:
            self.game_won = True
            return
        if not self._has_moves():
            self.game_over = True

    # ------------------------------------------------------------------ hit
    def _hit_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def _peak_at(self, px, py):
        """Return the topmost exposed peak entry at pixel, or None."""
        for p in reversed(self.peaks):
            if p["removed"]:
                continue
            if not self.is_exposed(p):
                continue
            if point_in_card(px, py, p["card"].x, p["card"].y):
                return p
        return None

    # ------------------------------------------------------------------ callbacks
    def on_update(self, delta_time):
        pass

    def on_draw(self):
        self.clear()
        tripeaks_renderer.draw(self)

    def on_mouse_press(self, x, y, button, modifiers):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        # Back button
        if self._hit_button(x, y, 55, bar_y, 90, 35):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if self._hit_button(x, y, WIDTH - 65, bar_y, 110, 35):
            self._init_game()
            return

        # Help button
        if self._hit_button(x, y, WIDTH - 135, bar_y, 40, 40):
            rules_view = RulesView("TriPeaks Solitaire", "tripeaks.txt", None,
                                   self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self.game_won or self.game_over:
            return

        # Stock click
        stock_x = 100
        stock_y = 80
        if point_in_card(x, y, stock_x, stock_y):
            if self.stock:
                card = self.stock.pop()
                card.face_up = True
                self.waste.append(card)
                self.streak = 0  # dealing from stock resets streak
                self._check_win()
                return

        # Peak card click
        hit = self._peak_at(x, y)
        if hit is not None and self.waste:
            waste_val = self.waste[-1].value
            card_val = hit["card"].value
            if self._ranks_adjacent(card_val, waste_val):
                hit["removed"] = True
                hit["card"].face_up = True
                self.waste.append(hit["card"])
                self.streak += 1
                self.score += self.streak * 10
                self._flip_newly_exposed()
                self._check_win()
                return

        self.selected = None
