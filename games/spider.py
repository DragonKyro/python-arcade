"""
Spider Solitaire game logic.
"""

import random
import arcade
from renderers import spider_renderer
from utils.card import Card, RANKS, RANK_VALUES, point_in_card, CARD_WIDTH, CARD_HEIGHT

WIDTH = 800
HEIGHT = 600

# Difficulty modes
DIFFICULTY_1_SUIT = 1
DIFFICULTY_2_SUITS = 2
DIFFICULTY_4_SUITS = 4

# Layout constants (shared with renderer)
NUM_COLUMNS = 10
CARD_SCALE = 0.85
COL_SPACING = 74
COL_START_X = 42
TOP_Y = HEIGHT - 80
CARD_Y_OVERLAP_FACE_DOWN = 18
CARD_Y_OVERLAP_FACE_UP = 24
STOCK_X = WIDTH - 50
STOCK_Y = 40
COMPLETED_X = 50
COMPLETED_Y = 40

# Button layout
BACK_BTN_X = 60
BACK_BTN_Y = HEIGHT - 30
BACK_BTN_W = 80
BACK_BTN_H = 30
NEW_GAME_BTN_X = WIDTH - 70
NEW_GAME_BTN_Y = HEIGHT - 30
NEW_GAME_BTN_W = 100
NEW_GAME_BTN_H = 30


class SpiderView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.difficulty = None  # set during difficulty selection
        self.choosing_difficulty = True
        self.tableau = []  # list of 10 lists of Card
        self.stock = []  # remaining cards to deal
        self.completed_runs = 0
        self.score = 500
        self.moves = 0
        self.dragging_cards = []
        self.drag_source_col = -1
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.game_won = False
        self._create_texts()

    def _create_texts(self):
        """Create reusable arcade.Text objects."""
        self.txt_title = arcade.Text(
            "Spider Solitaire", WIDTH / 2, HEIGHT - 30,
            arcade.color.WHITE, font_size=22,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_back = arcade.Text(
            "Back", BACK_BTN_X, BACK_BTN_Y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_new_game = arcade.Text(
            "New Game", NEW_GAME_BTN_X, NEW_GAME_BTN_Y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_score = arcade.Text(
            "Score: 500", WIDTH / 2, 20,
            arcade.color.WHITE, font_size=14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_stock_count = arcade.Text(
            "Stock: 50", STOCK_X, STOCK_Y + 60,
            arcade.color.WHITE, font_size=11,
            anchor_x="center", anchor_y="center",
        )
        self.txt_completed = arcade.Text(
            "Runs: 0/8", COMPLETED_X, COMPLETED_Y + 60,
            arcade.color.WHITE, font_size=11,
            anchor_x="center", anchor_y="center",
        )
        self.txt_win = arcade.Text(
            "You Win!", WIDTH / 2, HEIGHT / 2,
            arcade.color.GOLD, font_size=48,
            anchor_x="center", anchor_y="center", bold=True,
        )
        # Difficulty selection texts
        self.txt_choose = arcade.Text(
            "Choose Difficulty", WIDTH / 2, HEIGHT / 2 + 100,
            arcade.color.WHITE, font_size=28,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_1suit = arcade.Text(
            "1 Suit (Easy)", WIDTH / 2, HEIGHT / 2 + 20,
            arcade.color.WHITE, font_size=18,
            anchor_x="center", anchor_y="center",
        )
        self.txt_2suits = arcade.Text(
            "2 Suits (Medium)", WIDTH / 2, HEIGHT / 2 - 30,
            arcade.color.WHITE, font_size=18,
            anchor_x="center", anchor_y="center",
        )
        self.txt_4suits = arcade.Text(
            "4 Suits (Hard)", WIDTH / 2, HEIGHT / 2 - 80,
            arcade.color.WHITE, font_size=18,
            anchor_x="center", anchor_y="center",
        )
        self.txt_moves = arcade.Text(
            "Moves: 0", WIDTH / 2 - 120, 20,
            arcade.color.WHITE, font_size=14,
            anchor_x="center", anchor_y="center",
        )

    def _build_deck(self, difficulty):
        """Build a 104-card deck based on difficulty."""
        if difficulty == DIFFICULTY_1_SUIT:
            suits = ["s"]
        elif difficulty == DIFFICULTY_2_SUITS:
            suits = ["s", "h"]
        else:
            suits = ["s", "h", "d", "c"]

        cards = []
        # Need 104 cards total = 8 full suit runs of 13
        decks_per_suit = 8 // len(suits)
        for _ in range(decks_per_suit):
            for suit in suits:
                for rank in RANKS:
                    cards.append(Card(rank, suit))
        random.shuffle(cards)
        return cards

    def start_game(self, difficulty):
        """Initialize a new game with the given difficulty."""
        self.difficulty = difficulty
        self.choosing_difficulty = False
        self.game_won = False
        self.completed_runs = 0
        self.score = 500
        self.moves = 0
        self.dragging_cards = []
        self.drag_source_col = -1

        deck = self._build_deck(difficulty)

        # Deal tableau: first 4 columns get 6 cards, last 6 get 5 cards
        self.tableau = [[] for _ in range(NUM_COLUMNS)]
        idx = 0
        for col in range(NUM_COLUMNS):
            num_cards = 6 if col < 4 else 5
            for _ in range(num_cards):
                self.tableau[col].append(deck[idx])
                idx += 1
            # Top card face up
            self.tableau[col][-1].face_up = True

        # Remaining cards go to stock
        self.stock = deck[idx:]

        self._update_card_positions()
        self._update_dynamic_texts()

    def _update_card_positions(self):
        """Recalculate x, y for all cards in the tableau."""
        for col_idx in range(NUM_COLUMNS):
            col = self.tableau[col_idx]
            x = COL_START_X + col_idx * COL_SPACING
            for card_idx, card in enumerate(col):
                if card in self.dragging_cards:
                    continue
                overlap = CARD_Y_OVERLAP_FACE_UP if card.face_up else CARD_Y_OVERLAP_FACE_DOWN
                y = TOP_Y - card_idx * overlap
                card.x = x
                card.y = y

    def _update_dynamic_texts(self):
        """Update score, stock count, and completed run texts."""
        self.txt_score.text = f"Score: {self.score}"
        self.txt_stock_count.text = f"Stock: {len(self.stock)}"
        self.txt_completed.text = f"Runs: {self.completed_runs}/8"
        self.txt_moves.text = f"Moves: {self.moves}"

    def _check_and_remove_complete_runs(self, col_idx):
        """Check if a column has a complete K-to-A same-suit run on top. Remove it if so."""
        col = self.tableau[col_idx]
        if len(col) < 13:
            return False

        # Check last 13 cards for a complete descending same-suit run
        run_cards = col[-13:]
        if not all(c.face_up for c in run_cards):
            return False

        suit = run_cards[0].suit
        for i, card in enumerate(run_cards):
            if card.suit != suit:
                return False
            expected_value = 13 - i  # K=13, Q=12, ..., A=1
            if card.value != expected_value:
                return False

        # Remove the completed run
        del col[-13:]
        self.completed_runs += 1
        self.score += 100

        # Flip the new top card if face down
        if col and not col[-1].face_up:
            col[-1].face_up = True

        if self.completed_runs == 8:
            self.game_won = True

        return True

    def _get_movable_run_length(self, col_idx, start_from_bottom_of_run):
        """Return the number of cards in the same-suit descending run from the bottom of the column.
        start_from_bottom_of_run is the index in the column to start checking from."""
        col = self.tableau[col_idx]
        if start_from_bottom_of_run >= len(col):
            return 0
        if not col[start_from_bottom_of_run].face_up:
            return 0

        count = 1
        for i in range(start_from_bottom_of_run + 1, len(col)):
            prev = col[i - 1]
            curr = col[i]
            if not curr.face_up:
                break
            if curr.suit != prev.suit or curr.value != prev.value - 1:
                break
            count += 1
        return count

    def _can_pick_up(self, col_idx, card_idx):
        """Check if the card at card_idx and everything below it form a same-suit descending run."""
        col = self.tableau[col_idx]
        if card_idx >= len(col) or not col[card_idx].face_up:
            return False
        for i in range(card_idx + 1, len(col)):
            prev = col[i - 1]
            curr = col[i]
            if curr.suit != prev.suit or curr.value != prev.value - 1:
                return False
        return True

    def _can_place(self, card, col_idx):
        """Check if a card can be placed on top of a column."""
        col = self.tableau[col_idx]
        if not col:
            return True  # any card can go on empty column
        top = col[-1]
        return top.value == card.value + 1  # descending regardless of suit

    def deal_from_stock(self):
        """Deal 10 cards from stock, one to each column."""
        if not self.stock:
            return False
        # All columns must be non-empty
        for col in self.tableau:
            if not col:
                return False
        if len(self.stock) < 10:
            return False

        for col_idx in range(NUM_COLUMNS):
            card = self.stock.pop()
            card.face_up = True
            self.tableau[col_idx].append(card)

        self.score -= 1
        self.moves += 1

        # Check for completed runs in all columns after dealing
        for col_idx in range(NUM_COLUMNS):
            self._check_and_remove_complete_runs(col_idx)

        self._update_card_positions()
        self._update_dynamic_texts()
        return True

    def on_draw(self):
        self.clear()
        spider_renderer.draw(self)

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Difficulty selection
        if self.choosing_difficulty:
            if abs(x - WIDTH / 2) < 120:
                if abs(y - (HEIGHT / 2 + 20)) < 18:
                    self.start_game(DIFFICULTY_1_SUIT)
                elif abs(y - (HEIGHT / 2 - 30)) < 18:
                    self.start_game(DIFFICULTY_2_SUITS)
                elif abs(y - (HEIGHT / 2 - 80)) < 18:
                    self.start_game(DIFFICULTY_4_SUITS)
            return

        if self.game_won:
            return

        # Back button
        if (abs(x - BACK_BTN_X) < BACK_BTN_W / 2 and
                abs(y - BACK_BTN_Y) < BACK_BTN_H / 2):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if (abs(x - NEW_GAME_BTN_X) < NEW_GAME_BTN_W / 2 and
                abs(y - NEW_GAME_BTN_Y) < NEW_GAME_BTN_H / 2):
            self.choosing_difficulty = True
            return

        # Stock click
        if (abs(x - STOCK_X) < CARD_WIDTH * CARD_SCALE / 2 and
                abs(y - STOCK_Y) < CARD_HEIGHT * CARD_SCALE / 2):
            self.deal_from_stock()
            return

        # Try to pick up cards from tableau
        # Search columns from left to right, cards from bottom (visually top) to top
        for col_idx in range(NUM_COLUMNS):
            col = self.tableau[col_idx]
            if not col:
                continue
            # Check cards from bottom of column (last in list = top visually) upward
            for card_idx in range(len(col) - 1, -1, -1):
                card = col[card_idx]
                if not card.face_up:
                    continue
                if point_in_card(x, y, card.x, card.y, CARD_SCALE):
                    if self._can_pick_up(col_idx, card_idx):
                        self.dragging_cards = col[card_idx:]
                        self.drag_source_col = col_idx
                        self.drag_offset_x = x - card.x
                        self.drag_offset_y = y - card.y
                        return
            # If clicked in the column area but above visible cards, skip
            # (handled by checking each card individually)

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.dragging_cards:
            return
        base_x = x - self.drag_offset_x
        base_y = y - self.drag_offset_y
        for i, card in enumerate(self.dragging_cards):
            card.x = base_x
            card.y = base_y - i * CARD_Y_OVERLAP_FACE_UP

    def on_mouse_release(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT or not self.dragging_cards:
            return

        top_card = self.dragging_cards[0]
        placed = False

        # Find target column
        for col_idx in range(NUM_COLUMNS):
            col_x = COL_START_X + col_idx * COL_SPACING
            if abs(x - col_x) < COL_SPACING / 2:
                if col_idx != self.drag_source_col and self._can_place(top_card, col_idx):
                    # Move cards
                    src = self.tableau[self.drag_source_col]
                    card_idx = src.index(self.dragging_cards[0])
                    moving = src[card_idx:]
                    del src[card_idx:]
                    self.tableau[col_idx].extend(moving)

                    # Flip new top of source column
                    if src and not src[-1].face_up:
                        src[-1].face_up = True

                    self.score -= 1
                    self.moves += 1
                    placed = True

                    # Check for completed runs
                    self._check_and_remove_complete_runs(col_idx)
                    break

        self.dragging_cards = []
        self.drag_source_col = -1
        self._update_card_positions()
        self._update_dynamic_texts()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(self.menu_view)
