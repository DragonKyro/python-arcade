"""
Pyramid Solitaire – Remove pairs of exposed cards that sum to 13.

28 cards arranged in a 7-row pyramid (all face up).
Remaining 24 cards form the stock.  Kings (value 13) are removed alone.
Win by clearing the entire pyramid.
"""

import arcade
from utils.card import (
    create_deck, draw_card, draw_card_back, draw_empty_slot,
    point_in_card, CARD_WIDTH, CARD_HEIGHT, RANK_VALUES,
)
from renderers import pyramid_renderer
from renderers.pyramid_renderer import WIDTH, HEIGHT, TOP_BAR_HEIGHT
from pages.rules import RulesView


class PyramidView(arcade.View):
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
            "Score: 0", WIDTH / 2, bar_y, arcade.color.LIGHT_GRAY,
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

        # Build pyramid: 7 rows, row i has i+1 cards, total 28
        self.pyramid = []  # list of lists; pyramid[row][col]
        idx = 0
        for row in range(7):
            row_cards = []
            for col in range(row + 1):
                card = deck[idx]
                card.face_up = True
                row_cards.append(card)
                idx += 1
            self.pyramid.append(row_cards)

        # Remaining 24 cards are the stock
        self.stock = deck[28:]
        for c in self.stock:
            c.face_up = False
        self.waste = []

        self.selected = None  # (row, col) or "waste"
        self.score = 0
        self.game_won = False
        self.game_over = False
        self._assign_positions()

    def _assign_positions(self):
        """Compute x, y for every pyramid card (used by renderer)."""
        start_y = HEIGHT - TOP_BAR_HEIGHT - 30
        for row in range(7):
            num = row + 1
            total_w = num * CARD_WIDTH + (num - 1) * 5
            start_x = (WIDTH - total_w) / 2 + CARD_WIDTH / 2
            for col in range(num):
                card = self.pyramid[row][col]
                if card is not None:
                    card.x = start_x + col * (CARD_WIDTH + 5)
                    card.y = start_y - row * (CARD_HEIGHT * 0.45)

    # ------------------------------------------------------------------ logic
    def is_exposed(self, row, col):
        """A pyramid card is exposed if no cards cover it from the row below."""
        card = self.pyramid[row][col]
        if card is None:
            return False
        if row == 6:
            return True
        below = self.pyramid[row + 1]
        left_child = below[col] if col < len(below) else None
        right_child = below[col + 1] if col + 1 < len(below) else None
        return left_child is None and right_child is None

    def _pyramid_remaining(self):
        count = 0
        for row in self.pyramid:
            for card in row:
                if card is not None:
                    count += 1
        return count

    def _try_remove_pair(self, r1, c1, r2, c2):
        """Try to remove two pyramid cards if they sum to 13."""
        card1 = self.pyramid[r1][c1]
        card2 = self.pyramid[r2][c2]
        if card1 is None or card2 is None:
            return False
        if card1.value + card2.value == 13:
            self.pyramid[r1][c1] = None
            self.pyramid[r2][c2] = None
            self.score += card1.value + card2.value
            return True
        return False

    def _try_remove_with_waste(self, row, col):
        """Try to match a pyramid card with the waste top."""
        card = self.pyramid[row][col]
        if card is None or not self.waste:
            return False
        waste_card = self.waste[-1]
        if card.value + waste_card.value == 13:
            self.pyramid[row][col] = None
            self.waste.pop()
            self.score += card.value + waste_card.value
            return True
        return False

    def _check_win(self):
        if self._pyramid_remaining() == 0:
            self.game_won = True
            return
        # Check if any moves remain
        if not self._has_moves():
            self.game_over = True

    def _has_moves(self):
        """Return True if at least one valid move exists."""
        # Collect all exposed card values
        exposed = []
        for row in range(7):
            for col in range(len(self.pyramid[row])):
                if self.is_exposed(row, col):
                    exposed.append((row, col, self.pyramid[row][col].value))

        # King alone
        for r, c, v in exposed:
            if v == 13:
                return True

        # Pair among exposed
        for i in range(len(exposed)):
            for j in range(i + 1, len(exposed)):
                if exposed[i][2] + exposed[j][2] == 13:
                    return True

        # Pair with waste top
        if self.waste:
            wv = self.waste[-1].value
            for r, c, v in exposed:
                if v + wv == 13:
                    return True

        # Stock cards remain
        if self.stock:
            return True

        return False

    # ------------------------------------------------------------------ hit
    def _hit_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def _pyramid_card_at(self, px, py):
        """Return (row, col) of the topmost exposed card at pixel, or None."""
        # Check from bottom row up so topmost visual card wins
        for row in range(6, -1, -1):
            for col in range(len(self.pyramid[row])):
                card = self.pyramid[row][col]
                if card is not None and self.is_exposed(row, col):
                    if point_in_card(px, py, card.x, card.y):
                        return (row, col)
        return None

    # ------------------------------------------------------------------ callbacks
    def on_update(self, delta_time):
        pass

    def on_draw(self):
        self.clear()
        pyramid_renderer.draw(self)

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
            rules_view = RulesView("Pyramid Solitaire", "pyramid.txt", None,
                                   self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self.game_won or self.game_over:
            return

        # Stock click
        stock_x = 100
        stock_y = 80
        if self.stock and point_in_card(x, y, stock_x, stock_y):
            card = self.stock.pop()
            card.face_up = True
            self.waste.append(card)
            self.selected = None
            self._check_win()
            return

        # Waste click
        waste_x = 200
        waste_y = 80
        if self.waste and point_in_card(x, y, waste_x, waste_y):
            waste_card = self.waste[-1]
            if waste_card.value == 13:
                self.waste.pop()
                self.score += 13
                self.selected = None
                self._check_win()
                return
            if self.selected is None:
                self.selected = "waste"
            elif self.selected == "waste":
                self.selected = None
            else:
                # Selected is a pyramid card, try pair with waste
                sr, sc = self.selected
                if self._try_remove_with_waste(sr, sc):
                    self.selected = None
                    self._check_win()
                else:
                    self.selected = "waste"
            return

        # Pyramid click
        hit = self._pyramid_card_at(x, y)
        if hit is not None:
            row, col = hit
            card = self.pyramid[row][col]

            # King: remove alone
            if card.value == 13:
                self.pyramid[row][col] = None
                self.score += 13
                self.selected = None
                self._check_win()
                return

            if self.selected is None:
                self.selected = (row, col)
            elif self.selected == "waste":
                # Try match with waste
                if self._try_remove_with_waste(row, col):
                    self.selected = None
                    self._check_win()
                else:
                    self.selected = (row, col)
            elif self.selected == (row, col):
                self.selected = None
            else:
                sr, sc = self.selected
                if self._try_remove_pair(sr, sc, row, col):
                    self.selected = None
                    self._check_win()
                else:
                    self.selected = (row, col)
            return

        # Clicked empty space
        self.selected = None
