"""
Old Maid game view using Arcade 3.x APIs.
"""

import random

import arcade
from pages.components import Button
from pages.rules import RulesView
from ai.old_maid_ai import OldMaidAI
from utils.card import Card, create_deck, CARD_WIDTH, CARD_HEIGHT
from renderers.old_maid_renderer import (
    WIDTH, HEIGHT,
    BUTTON_W, BUTTON_H,
)

# Game phases
PHASE_SETUP = "setup"
PHASE_HUMAN_DRAW = "human_draw"
PHASE_AI_TURN = "ai_turn"
PHASE_GAME_OVER = "game_over"

# AI thinking delay
AI_DELAY = 0.8


class OldMaidView(arcade.View):
    """Arcade View for Old Maid."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.help_button = Button(
            WIDTH - 145, HEIGHT - 30, 40, 36, "?", color=arcade.color.DARK_SLATE_BLUE
        )

        # Setup state
        self.phase = PHASE_SETUP
        self.pending_num_ai = 0

        # Game state
        self.hands = []          # list of list[Card], index 0 = human
        self.player_names = []
        self.ai_agents = []      # list (None for human, OldMaidAI for AI)
        self.current_turn = 0    # index of player whose turn it is
        self.num_players = 0
        self.out_players = set() # indices of players who are out (safe)
        self.discard_pile = []   # pairs removed

        # AI timer
        self.ai_timer = 0.0

        # Human drawing state
        self.opponent_hand_index = -1  # whose hand the human draws from
        self.hover_card_index = -1     # card being hovered over

        # Message for feedback
        self.message = ""
        self.message_timer = 0.0

        # Setup buttons (1-3 AI opponents)
        self.setup_buttons = []
        for i in range(3):
            bx = WIDTH // 2 - 80 + i * 80
            by = HEIGHT // 2 + 20
            self.setup_buttons.append((bx, by, 60, 44))

        self._create_texts()

    # ------------------------------------------------------------------ texts

    def _create_texts(self):
        """Create reusable arcade.Text objects."""
        self.txt_btn_back = arcade.Text(
            "Back", 60, HEIGHT - 30, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_btn_new_game = arcade.Text(
            "New Game", WIDTH - 70, HEIGHT - 30, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_title = arcade.Text(
            "Old Maid", WIDTH // 2, HEIGHT - 30,
            arcade.color.WHITE, 22, anchor_x="center", anchor_y="center", bold=True,
        )

        # Setup
        self.txt_setup_prompt = arcade.Text(
            "Choose number of AI opponents (1-3):", WIDTH // 2, HEIGHT // 2 + 80,
            arcade.color.WHITE, 20, anchor_x="center", anchor_y="center",
        )
        self.txt_setup_btn_labels = []
        for i in range(3):
            bx = WIDTH // 2 - 80 + i * 80
            by = HEIGHT // 2 + 20
            self.txt_setup_btn_labels.append(
                arcade.Text(
                    str(i + 1), bx, by, arcade.color.WHITE, 18,
                    anchor_x="center", anchor_y="center", bold=True,
                )
            )
        self.txt_start_btn = arcade.Text(
            "Start Game", WIDTH // 2, HEIGHT // 2 - 60,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )

        # Turn / status
        self.txt_turn = arcade.Text(
            "", WIDTH // 2, HEIGHT - 70,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center",
        )
        self.txt_message = arcade.Text(
            "", WIDTH // 2, HEIGHT - 95,
            arcade.color.YELLOW, 14, anchor_x="center", anchor_y="center",
        )

        # Player labels (up to 4)
        self.txt_player_labels = []
        for _ in range(4):
            self.txt_player_labels.append(
                arcade.Text("", 0, 0, arcade.color.WHITE, 13,
                            anchor_x="center", anchor_y="center", bold=True)
            )

        # Game over
        self.txt_game_over_msg = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 30,
            arcade.color.WHITE, 48, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_hint = arcade.Text(
            "Click 'New Game' to play again",
            WIDTH // 2, HEIGHT // 2 - 30,
            arcade.color.WHITE, 18, anchor_x="center", anchor_y="center",
        )

    # ------------------------------------------------------------------ setup

    def _start_game(self):
        """Initialize the game with the selected number of AI opponents."""
        num_ai = self.pending_num_ai
        self.num_players = 1 + num_ai
        self.hands = [[] for _ in range(self.num_players)]
        self.player_names = ["You"] + [f"AI {i+1}" for i in range(num_ai)]
        self.ai_agents = [None] + [OldMaidAI() for _ in range(num_ai)]
        self.out_players = set()
        self.discard_pile = []
        self.message = ""
        self.message_timer = 0.0

        # Create deck, remove one Queen
        deck = create_deck(shuffled=True)
        # Remove the first Queen we find (e.g. Queen of clubs)
        for i, card in enumerate(deck):
            if card.rank == "q":
                deck.pop(i)
                break

        # Deal all cards
        for i, card in enumerate(deck):
            self.hands[i % self.num_players].append(card)

        # Remove all initial pairs from each hand
        for pidx in range(self.num_players):
            self._remove_pairs(pidx)

        # Check if anyone is already out
        self._check_out_players()

        # Human goes first
        self.current_turn = 0
        self._advance_to_active()
        self._begin_turn()

    def _remove_pairs(self, player_idx):
        """Remove all pairs (same rank) from a player's hand."""
        hand = self.hands[player_idx]
        # Group by rank
        rank_groups = {}
        for card in hand:
            rank_groups.setdefault(card.rank, []).append(card)

        new_hand = []
        for rank, cards in rank_groups.items():
            while len(cards) >= 2:
                c1 = cards.pop()
                c2 = cards.pop()
                self.discard_pile.extend([c1, c2])
            new_hand.extend(cards)

        self.hands[player_idx] = new_hand

    def _check_out_players(self):
        """Mark players with empty hands as out (safe)."""
        for i in range(self.num_players):
            if len(self.hands[i]) == 0 and i not in self.out_players:
                self.out_players.add(i)

    def _active_players(self):
        """Indices of players still holding cards."""
        return [i for i in range(self.num_players) if i not in self.out_players]

    def _prev_player(self, idx):
        """Return the previous active player (the one whose hand we draw from)."""
        n = self.num_players
        for offset in range(1, n + 1):
            candidate = (idx - offset) % n
            if candidate not in self.out_players:
                return candidate
        return idx

    def _next_player(self, idx):
        """Return the next active player."""
        n = self.num_players
        for offset in range(1, n + 1):
            candidate = (idx + offset) % n
            if candidate not in self.out_players:
                return candidate
        return idx

    def _advance_to_active(self):
        """If current_turn is out, advance to next active."""
        if self.current_turn in self.out_players:
            self.current_turn = self._next_player(self.current_turn)

    def _begin_turn(self):
        """Set up the current turn."""
        active = self._active_players()
        if len(active) <= 1:
            self._end_game()
            return

        if self.current_turn == 0:
            opp = self._prev_player(0)
            self.opponent_hand_index = opp
            # Shuffle opponent hand so human can't track the Queen
            if self.ai_agents[opp] is not None:
                self.ai_agents[opp].shuffle_hand(self.hands[opp])
            else:
                random.shuffle(self.hands[opp])
            self.phase = PHASE_HUMAN_DRAW
            self.txt_turn.text = f"Your turn! Pick a card from {self.player_names[opp]}'s hand."
            self.txt_turn.color = arcade.color.WHITE
        else:
            self.phase = PHASE_AI_TURN
            self.ai_timer = 0.0
            name = self.player_names[self.current_turn]
            self.txt_turn.text = f"{name} is drawing..."
            self.txt_turn.color = arcade.color.YELLOW

    def _do_draw(self, drawer, source, card_index):
        """Player *drawer* draws card at *card_index* from *source*'s hand."""
        card = self.hands[source].pop(card_index)
        self.hands[drawer].append(card)

        # Check for new pair
        pair_found = self._remove_pairs(drawer)
        self._check_out_players()

        return card

    def _end_game(self):
        """Determine loser (player left holding the Queen)."""
        self.phase = PHASE_GAME_OVER
        active = self._active_players()
        if len(active) == 1:
            loser = active[0]
            if loser == 0:
                self.txt_game_over_msg.text = "You Lose!"
                self.txt_game_over_msg.color = arcade.color.RED
            else:
                self.txt_game_over_msg.text = "You Win!"
                self.txt_game_over_msg.color = arcade.color.GREEN
        elif len(active) == 0:
            # Shouldn't happen normally
            self.txt_game_over_msg.text = "Draw!"
            self.txt_game_over_msg.color = arcade.color.YELLOW
        self.txt_turn.text = ""

    def _set_message(self, msg):
        self.message = msg
        self.message_timer = 2.0
        self.txt_message.text = msg

    # ------------------------------------------------------------------ helpers

    def _in_rect(self, x, y, cx, cy, w, h):
        return cx - w / 2 <= x <= cx + w / 2 and cy - h / 2 <= y <= cy + h / 2

    # ------------------------------------------------------------------ update

    def on_update(self, delta_time):
        # Message timer
        if self.message_timer > 0:
            self.message_timer -= delta_time
            if self.message_timer <= 0:
                self.message = ""
                self.txt_message.text = ""

        if self.phase == PHASE_AI_TURN:
            self.ai_timer += delta_time
            if self.ai_timer >= AI_DELAY:
                self._do_ai_turn()

    def _do_ai_turn(self):
        """Execute the AI's draw."""
        idx = self.current_turn
        source = self._prev_player(idx)
        ai = self.ai_agents[idx]

        if len(self.hands[source]) == 0:
            # Source ran out, skip
            self.current_turn = self._next_player(idx)
            self._advance_to_active()
            self._begin_turn()
            return

        card_idx = ai.choose_card_from(self.hands[source])
        card = self._do_draw(idx, source, card_idx)

        name = self.player_names[idx]
        src_name = self.player_names[source]
        self._set_message(f"{name} drew from {src_name}.")

        # Check if source is now out
        self._check_out_players()

        # Check game over
        active = self._active_players()
        if len(active) <= 1:
            self._end_game()
            return

        # Next turn
        self.current_turn = self._next_player(idx)
        self._advance_to_active()
        self._begin_turn()

    # ------------------------------------------------------------------ draw

    def on_draw(self):
        self.clear()
        from renderers import old_maid_renderer
        old_maid_renderer.draw(self)

    # ------------------------------------------------------------------ input

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Back button
        if self._in_rect(x, y, 60, HEIGHT - 30, BUTTON_W, BUTTON_H):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if self._in_rect(x, y, WIDTH - 70, HEIGHT - 30, BUTTON_W + 10, BUTTON_H):
            self.phase = PHASE_SETUP
            self.pending_num_ai = 0
            return

        # Help button
        if self.help_button.hit_test(x, y):
            rules_view = RulesView(
                "Old Maid", "old_maid.txt", None, self.menu_view,
                existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        if self.phase == PHASE_SETUP:
            self._handle_setup_click(x, y)
        elif self.phase == PHASE_HUMAN_DRAW:
            self._handle_human_draw_click(x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.phase == PHASE_HUMAN_DRAW:
            self._update_hover(x, y)
        else:
            self.hover_card_index = -1

    def _handle_setup_click(self, x, y):
        for i, (bx, by, bw, bh) in enumerate(self.setup_buttons):
            if self._in_rect(x, y, bx, by, bw, bh):
                self.pending_num_ai = i + 1
                return

        if self.pending_num_ai > 0:
            sx, sy = WIDTH // 2, HEIGHT // 2 - 60
            if self._in_rect(x, y, sx, sy, 140, 44):
                self._start_game()

    def _handle_human_draw_click(self, x, y):
        """Human clicks a card back in the opponent's fan to draw it."""
        opp = self.opponent_hand_index
        opp_hand = self.hands[opp]
        if len(opp_hand) == 0:
            return

        # Compute card-back positions (fan at top area)
        positions = self._get_opponent_fan_positions(opp)
        for i in range(len(opp_hand) - 1, -1, -1):
            cx, cy = positions[i]
            if self._in_rect(x, y, cx, cy, CARD_WIDTH, CARD_HEIGHT):
                card = self._do_draw(0, opp, i)
                self._set_message(f"You drew {card!r}.")
                self._check_out_players()

                active = self._active_players()
                if len(active) <= 1:
                    self._end_game()
                    return

                self.current_turn = self._next_player(0)
                self._advance_to_active()
                self._begin_turn()
                return

    def _update_hover(self, x, y):
        """Update which card the mouse hovers over in opponent fan."""
        opp = self.opponent_hand_index
        if opp < 0 or opp >= self.num_players:
            self.hover_card_index = -1
            return
        opp_hand = self.hands[opp]
        if len(opp_hand) == 0:
            self.hover_card_index = -1
            return

        positions = self._get_opponent_fan_positions(opp)
        # Check in reverse order (top card first)
        for i in range(len(opp_hand) - 1, -1, -1):
            cx, cy = positions[i]
            if self._in_rect(x, y, cx, cy, CARD_WIDTH, CARD_HEIGHT):
                self.hover_card_index = i
                return
        self.hover_card_index = -1

    def _get_opponent_fan_positions(self, opp_idx):
        """Get the (x, y) positions for each card back in the opponent's fan."""
        hand = self.hands[opp_idx]
        n = len(hand)
        if n == 0:
            return []

        fan_y = HEIGHT - 180
        max_width = 500
        if n == 1:
            spacing = 0
        else:
            spacing = min(30, max_width / n)
        total_w = spacing * (n - 1)
        start_x = WIDTH // 2 - total_w / 2

        positions = []
        for i in range(n):
            cx = start_x + i * spacing
            positions.append((cx, fan_y))
        return positions

    def get_human_hand_positions(self):
        """Get (x, y) positions for the human's hand cards at the bottom."""
        hand = self.hands[0] if self.hands else []
        n = len(hand)
        if n == 0:
            return []

        hand_y = 70
        max_width = 700
        if n == 1:
            spacing = 0
        else:
            spacing = min(40, max_width / n)
        total_w = spacing * (n - 1)
        start_x = WIDTH // 2 - total_w / 2

        positions = []
        for i in range(n):
            cx = start_x + i * spacing
            positions.append((cx, hand_y))
        return positions
