"""
Crazy Eights -- multiplayer card game with 1-3 AI opponents.

Match suit or rank of discard pile top.  8 is wild (choose new suit).
First to empty hand wins.  Score = sum of opponents' remaining card values
(8 = 50, face = 10, others = face value).
"""

import arcade
from pages.rules import RulesView
from ai.crazy_eights_ai import CrazyEightsAI
from renderers.crazy_eights_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT,
    HAND_Y, HAND_OVERLAP,
    DISCARD_X, DISCARD_Y, STOCK_X, STOCK_Y,
    AI_POSITIONS,
    SUIT_CHOOSER_GAP, SUIT_CHOOSER_SIZE, SUIT_LABELS,
    BUTTON_W, BUTTON_H,
    SCALE,
)
from utils.card import (
    create_deck, point_in_card,
    CARD_WIDTH, CARD_HEIGHT, SUIT_NAMES,
)

CARD_W = CARD_WIDTH * SCALE
CARD_H = CARD_HEIGHT * SCALE

# Phases
PHASE_SETUP = "setup"
PHASE_PLAYING = "playing"
PHASE_DRAW = "draw"
PHASE_CHOOSE_SUIT = "choose_suit"
PHASE_AI_TURN = "ai_turn"
PHASE_GAME_OVER = "game_over"


def _card_score(card):
    """Score value of a card left in hand."""
    if card.rank == "8":
        return 50
    if card.rank in ("j", "q", "k"):
        return 10
    if card.rank == "a":
        return 1
    return int(card.rank)


class CrazyEightsView(arcade.View):
    """Arcade View for Crazy Eights."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view

        # Setup state
        self.phase = PHASE_SETUP
        self.pending_num_ai = 0

        # Game state
        self.players = []           # list of dicts: {"name", "hand", "ai"}
        self.stock = []
        self.discard_pile = []
        self.active_suit = ""       # suit currently required to match
        self.current_player = 0
        self.winner = -1
        self.score = 0

        # AI timing
        self.ai_timer = 0.0

        # Status message timer
        self.status_timer = 0.0

        # Setup buttons
        self.setup_buttons = []
        for i in range(3):
            bx = WIDTH // 2 - 80 + i * 80
            by = HEIGHT // 2 + 20
            self.setup_buttons.append((bx, by, 60, 44))

        self._create_texts()

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
        self.txt_title = arcade.Text(
            "Crazy Eights", WIDTH // 2, bar_y, arcade.color.WHITE,
            font_size=20, anchor_x="center", anchor_y="center", bold=True,
        )

        # Setup
        self.txt_setup_prompt = arcade.Text(
            "Choose number of AI opponents:", WIDTH // 2, HEIGHT // 2 + 80,
            arcade.color.WHITE, 20, anchor_x="center", anchor_y="center",
        )
        self.txt_setup_labels = []
        for i in range(3):
            bx = WIDTH // 2 - 80 + i * 80
            by = HEIGHT // 2 + 20
            self.txt_setup_labels.append(
                arcade.Text(
                    str(i + 1), bx, by, arcade.color.WHITE, 18,
                    anchor_x="center", anchor_y="center", bold=True,
                )
            )
        self.txt_start_btn = arcade.Text(
            "Start Game", WIDTH // 2, HEIGHT // 2 - 60,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )

        # In-game
        self.txt_stock_count = arcade.Text(
            "", STOCK_X, STOCK_Y - CARD_H / 2 - 12,
            arcade.color.LIGHT_GRAY, 11, anchor_x="center", anchor_y="center",
        )
        self.txt_active_suit = arcade.Text(
            "", DISCARD_X, DISCARD_Y - CARD_H / 2 - 14,
            arcade.color.YELLOW, 13, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_status = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 55,
            arcade.color.WHITE, 14, anchor_x="center", anchor_y="center",
        )

        # AI names / counts (up to 3)
        self.txt_ai_names = []
        self.txt_ai_counts = []
        for i in range(3):
            self.txt_ai_names.append(
                arcade.Text(
                    "", 0, 0, arcade.color.WHITE, 13,
                    anchor_x="center", anchor_y="center", bold=True,
                )
            )
            self.txt_ai_counts.append(
                arcade.Text(
                    "", 0, 0, arcade.color.LIGHT_GRAY, 11,
                    anchor_x="center", anchor_y="center",
                )
            )

        # Suit chooser
        self.txt_choose_suit_label = arcade.Text(
            "Choose a suit:", WIDTH // 2, HEIGHT // 2 + 25,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )
        suit_symbols = {"c": "C", "d": "D", "h": "H", "s": "S"}
        self.txt_suit_buttons = []
        for i, s in enumerate(SUIT_LABELS):
            self.txt_suit_buttons.append(
                arcade.Text(
                    SUIT_NAMES[s].title(), 0, 0,
                    arcade.color.WHITE, 12,
                    anchor_x="center", anchor_y="center", bold=True,
                )
            )

        # Game over
        self.txt_game_over_msg = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 40,
            arcade.color.WHITE, 36, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_score = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 - 10,
            arcade.color.LIGHT_GRAY, 18, anchor_x="center", anchor_y="center",
        )
        self.txt_game_over_hint = arcade.Text(
            "Click 'New Game' to play again",
            WIDTH // 2, HEIGHT // 2 - 50,
            arcade.color.LIGHT_GRAY, 14, anchor_x="center", anchor_y="center",
        )

    # ------------------------------------------------------------------ game init

    def _start_game(self):
        num_ai = self.pending_num_ai
        total = 1 + num_ai
        cards_each = 7 if total < 4 else 5

        deck = create_deck(shuffled=True)

        self.players = []
        # Human
        self.players.append({"name": "You", "hand": [], "ai": None})
        for i in range(num_ai):
            self.players.append({
                "name": f"AI {i + 1}",
                "hand": [],
                "ai": CrazyEightsAI(),
            })
            self.txt_ai_names[i].text = f"AI {i + 1}"

        # Deal
        idx = 0
        for p in self.players:
            for _ in range(cards_each):
                card = deck[idx]
                card.face_up = False
                p["hand"].append(card)
                idx += 1

        # Remaining cards become stock
        self.stock = deck[idx:]
        for c in self.stock:
            c.face_up = False

        # Flip one card to start discard pile (skip 8s)
        while self.stock:
            card = self.stock.pop(0)
            if card.rank != "8":
                card.face_up = True
                self.discard_pile = [card]
                self.active_suit = card.suit
                break
            else:
                # Put the 8 back at the bottom
                self.stock.append(card)

        self.current_player = 0
        self.winner = -1
        self.score = 0
        self.ai_timer = 0.0
        self.phase = PHASE_PLAYING
        self._update_status("Your turn -- play a card or click the stock to draw.")
        self._update_displays()

    def _update_displays(self):
        self.txt_stock_count.text = f"{len(self.stock)} left"
        if self.discard_pile:
            self.txt_active_suit.text = f"Suit: {SUIT_NAMES[self.active_suit].title()}"
        else:
            self.txt_active_suit.text = ""

    def _update_status(self, msg):
        self.txt_status.text = msg
        self.status_timer = 0.0

    # ------------------------------------------------------------------ logic

    def _can_play(self, card):
        """Check if a card can be played on the discard pile."""
        if card.rank == "8":
            return True
        if not self.discard_pile:
            return True
        return card.suit == self.active_suit or card.rank == self.discard_pile[-1].rank

    def _play_card(self, player_idx, card_idx):
        """Play a card from the player's hand onto the discard pile."""
        player = self.players[player_idx]
        card = player["hand"].pop(card_idx)
        card.face_up = True
        self.discard_pile.append(card)

        if card.rank == "8":
            # Wildcard -- choose suit
            if player["ai"] is not None:
                suit = player["ai"].choose_suit(player["hand"])
                self.active_suit = suit
                self._update_status(
                    f"{player['name']} plays {card} and chooses "
                    f"{SUIT_NAMES[self.active_suit].title()}!"
                )
                self._check_win(player_idx)
                if self.phase != PHASE_GAME_OVER:
                    self._next_turn()
            else:
                self.active_suit = card.suit  # temporary
                self.phase = PHASE_CHOOSE_SUIT
                self._update_status("Choose a suit for the wild 8!")
                return
        else:
            self.active_suit = card.suit
            self._update_status(f"{player['name']} plays {card}.")
            self._check_win(player_idx)
            if self.phase != PHASE_GAME_OVER:
                self._next_turn()

        self._update_displays()

    def _draw_from_stock(self, player_idx):
        """Draw a card from the stock pile."""
        if not self.stock:
            self._recycle_discard()
        if not self.stock:
            # No cards left anywhere -- skip turn
            self._next_turn()
            return None

        card = self.stock.pop()
        card.face_up = False
        self.players[player_idx]["hand"].append(card)
        self._update_displays()
        return card

    def _recycle_discard(self):
        """Recycle the discard pile (except top) back into the stock."""
        if len(self.discard_pile) <= 1:
            return
        top = self.discard_pile[-1]
        recycled = self.discard_pile[:-1]
        import random
        random.shuffle(recycled)
        for c in recycled:
            c.face_up = False
        self.stock = recycled
        self.discard_pile = [top]

    def _check_win(self, player_idx):
        if not self.players[player_idx]["hand"]:
            self.winner = player_idx
            self.score = sum(
                _card_score(c)
                for i, p in enumerate(self.players)
                if i != player_idx
                for c in p["hand"]
            )
            self.phase = PHASE_GAME_OVER
            name = self.players[player_idx]["name"]
            if player_idx == 0:
                self.txt_game_over_msg.text = "You Win!"
                self.txt_game_over_msg.color = arcade.color.GOLD
            else:
                self.txt_game_over_msg.text = f"{name} Wins!"
                self.txt_game_over_msg.color = arcade.color.RED
            self.txt_game_over_score.text = f"Score: {self.score}"

    def _next_turn(self):
        self.current_player = (self.current_player + 1) % len(self.players)
        self.ai_timer = 0.0
        if self.current_player == 0:
            self.phase = PHASE_PLAYING
            self._update_status("Your turn -- play a card or click the stock to draw.")
        else:
            self.phase = PHASE_AI_TURN
            name = self.players[self.current_player]["name"]
            self._update_status(f"{name} is thinking...")

    # ------------------------------------------------------------------ hit test

    def _in_rect(self, x, y, cx, cy, w, h):
        return cx - w / 2 <= x <= cx + w / 2 and cy - h / 2 <= y <= cy + h / 2

    def _hand_card_at(self, px, py):
        """Return index of card in human hand under (px, py), or -1."""
        hand = self.players[0]["hand"]
        if not hand:
            return -1
        total_w = CARD_W + (len(hand) - 1) * HAND_OVERLAP
        start_x = WIDTH / 2 - total_w / 2 + CARD_W / 2

        # Check from right to left (topmost card first)
        for i in range(len(hand) - 1, -1, -1):
            cx = start_x + i * HAND_OVERLAP
            if point_in_card(px, py, cx, HAND_Y, SCALE):
                return i
        return -1

    # ------------------------------------------------------------------ callbacks

    def on_draw(self):
        self.clear()
        from renderers import crazy_eights_renderer
        crazy_eights_renderer.draw(self)

    def on_update(self, delta_time):
        if self.phase == PHASE_AI_TURN:
            self.ai_timer += delta_time
            if self.ai_timer >= 0.5:
                self._do_ai_turn()

    def _do_ai_turn(self):
        """Execute the current AI player's turn."""
        p = self.players[self.current_player]
        ai = p["ai"]
        if ai is None:
            self._next_turn()
            return

        top = self.discard_pile[-1] if self.discard_pile else None
        top_rank = top.rank if top else ""
        top_suit = top.suit if top else ""

        idx = ai.choose_play(p["hand"], top_rank, top_suit, self.active_suit)

        if idx is not None:
            self._play_card(self.current_player, idx)
        else:
            # Draw
            drawn = self._draw_from_stock(self.current_player)
            if drawn and ai.should_play_drawn(drawn, top_rank, self.active_suit):
                # Play the drawn card (it's the last card in hand)
                card_idx = len(p["hand"]) - 1
                self._play_card(self.current_player, card_idx)
            else:
                name = p["name"]
                self._update_status(f"{name} draws a card.")
                self._next_turn()
                self._update_displays()

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        # Top bar buttons
        if self._in_rect(x, y, 55, bar_y, 90, 35):
            self.window.show_view(self.menu_view)
            return
        if self._in_rect(x, y, WIDTH - 65, bar_y, 110, 35):
            self.phase = PHASE_SETUP
            self.pending_num_ai = 0
            return
        if self._in_rect(x, y, WIDTH - 135, bar_y, 40, 40):
            rules_view = RulesView(
                "Crazy Eights", "crazy_eights.txt", None,
                self.menu_view, existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        if self.phase == PHASE_SETUP:
            self._handle_setup_click(x, y)
        elif self.phase == PHASE_PLAYING:
            self._handle_playing_click(x, y)
        elif self.phase == PHASE_CHOOSE_SUIT:
            self._handle_suit_click(x, y)

    def _handle_setup_click(self, x, y):
        for i, (bx, by, bw, bh) in enumerate(self.setup_buttons):
            if self._in_rect(x, y, bx, by, bw, bh):
                self.pending_num_ai = i + 1
                return
        if self.pending_num_ai > 0:
            sx, sy = WIDTH // 2, HEIGHT // 2 - 60
            if self._in_rect(x, y, sx, sy, 140, 44):
                self._start_game()

    def _handle_playing_click(self, x, y):
        if self.current_player != 0:
            return

        # Click on stock to draw
        if point_in_card(x, y, STOCK_X, STOCK_Y, SCALE):
            drawn = self._draw_from_stock(0)
            if drawn is None:
                self._update_status("No cards left to draw! Turn skipped.")
                self._next_turn()
                return
            # Check if drawn card is playable
            top = self.discard_pile[-1] if self.discard_pile else None
            if self._can_play(drawn):
                self._update_status(f"You drew {drawn} -- it's playable! Click it to play or pass.")
                # Auto-set face up for display
                drawn.face_up = True
            else:
                self._update_status(f"You drew {drawn} -- can't play it. Turn passes.")
                drawn.face_up = True
                self._next_turn()
            self._update_displays()
            return

        # Click on a card in hand
        idx = self._hand_card_at(x, y)
        if idx >= 0:
            card = self.players[0]["hand"][idx]
            if self._can_play(card):
                self._play_card(0, idx)
            else:
                self._update_status("That card doesn't match! Play a matching suit/rank or an 8.")

    def _handle_suit_click(self, x, y):
        start_x = WIDTH // 2 - int(1.5 * SUIT_CHOOSER_GAP)
        for i, suit in enumerate(SUIT_LABELS):
            bx = start_x + i * SUIT_CHOOSER_GAP
            by = HEIGHT // 2 - 15
            if self._in_rect(x, y, bx, by, SUIT_CHOOSER_SIZE, SUIT_CHOOSER_SIZE):
                self.active_suit = suit
                self._update_status(
                    f"You chose {SUIT_NAMES[suit].title()}!"
                )
                self._check_win(0)
                if self.phase != PHASE_GAME_OVER:
                    self._next_turn()
                self._update_displays()
                return
