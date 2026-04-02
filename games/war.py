"""
War card game view using Arcade 3.x APIs.
"""

import arcade
from pages.components import Button
from pages.rules import RulesView
from ai.war_ai import WarAI
from utils.card import create_deck, CARD_WIDTH, CARD_HEIGHT
from renderers.war_renderer import (
    WIDTH, HEIGHT,
    BUTTON_W, BUTTON_H,
)

# Game phases
PHASE_READY = "ready"           # waiting for human to click/flip
PHASE_REVEAL = "reveal"         # cards revealed, showing result
PHASE_WAR_REVEAL = "war_reveal" # war cards revealed
PHASE_GAME_OVER = "game_over"

# Timing
REVEAL_DELAY = 1.5
AI_FLIP_DELAY = 0.5


class WarView(arcade.View):
    """Arcade View for War."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.help_button = Button(
            WIDTH - 145, HEIGHT - 30, 40, 36, "?", color=arcade.color.DARK_SLATE_BLUE
        )

        # Game state
        self.phase = PHASE_READY
        self.human_deck = []        # face-down pile
        self.ai_deck = []           # face-down pile
        self.human_won_pile = []    # cards won (bottom of deck eventually)
        self.ai_won_pile = []

        # Current battle
        self.human_card = None      # revealed card
        self.ai_card = None
        self.war_stack_human = []   # face-down war cards
        self.war_stack_ai = []
        self.war_face_human = None  # face-up war card
        self.war_face_ai = None
        self.pot = []               # all cards at stake in current battle
        self.in_war = False
        self.war_depth = 0          # for nested wars

        # AI
        self.ai = WarAI()

        # Timers
        self.reveal_timer = 0.0
        self.ai_timer = 0.0
        self.auto_advance = False

        # Message
        self.message = ""
        self.message_timer = 0.0

        self._deal()
        self._create_texts()

    # ------------------------------------------------------------------ texts

    def _create_texts(self):
        self.txt_btn_back = arcade.Text(
            "Back", 60, HEIGHT - 30, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_btn_new_game = arcade.Text(
            "New Game", WIDTH - 70, HEIGHT - 30, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_title = arcade.Text(
            "War", WIDTH // 2, HEIGHT - 30,
            arcade.color.WHITE, 22, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_status = arcade.Text(
            "Click your deck to flip!", WIDTH // 2, HEIGHT // 2,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center",
        )
        self.txt_human_count = arcade.Text(
            "", 200, 160, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_ai_count = arcade.Text(
            "", 600, HEIGHT - 160, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_message = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 - 30,
            arcade.color.YELLOW, 16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_war_banner = arcade.Text(
            "W A R !", WIDTH // 2, HEIGHT // 2 + 40,
            arcade.color.RED, 36, anchor_x="center", anchor_y="center", bold=True,
        )
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

    def _deal(self):
        deck = create_deck(shuffled=True)
        self.human_deck = deck[:26]
        self.ai_deck = deck[26:]
        self.human_won_pile = []
        self.ai_won_pile = []
        self.human_card = None
        self.ai_card = None
        self.war_stack_human = []
        self.war_stack_ai = []
        self.war_face_human = None
        self.war_face_ai = None
        self.pot = []
        self.in_war = False
        self.war_depth = 0
        self.phase = PHASE_READY
        self.auto_advance = False
        self.message = ""

    def _total_human(self):
        return len(self.human_deck) + len(self.human_won_pile)

    def _total_ai(self):
        return len(self.ai_deck) + len(self.ai_won_pile)

    def _draw_from_deck(self, is_human):
        """Draw a card from the player's deck, recycling won pile if needed."""
        import random
        if is_human:
            if not self.human_deck:
                random.shuffle(self.human_won_pile)
                self.human_deck = self.human_won_pile
                self.human_won_pile = []
            if self.human_deck:
                return self.human_deck.pop(0)
            return None
        else:
            if not self.ai_deck:
                random.shuffle(self.ai_won_pile)
                self.ai_deck = self.ai_won_pile
                self.ai_won_pile = []
            if self.ai_deck:
                return self.ai_deck.pop(0)
            return None

    @staticmethod
    def _rank_value(card):
        """Get numeric value for comparison. Ace is high (14)."""
        vals = {
            "a": 14, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
            "8": 8, "9": 9, "10": 10, "j": 11, "q": 12, "k": 13,
        }
        return vals[card.rank]

    # ------------------------------------------------------------------ gameplay

    def _flip_cards(self):
        """Both players reveal top card."""
        self.human_card = self._draw_from_deck(True)
        self.ai_card = self._draw_from_deck(False)

        if self.human_card is None or self.ai_card is None:
            self._check_game_over()
            return

        self.human_card.face_up = True
        self.ai_card.face_up = True
        self.pot.extend([self.human_card, self.ai_card])

        self.war_stack_human = []
        self.war_stack_ai = []
        self.war_face_human = None
        self.war_face_ai = None
        self.in_war = False

        self._resolve_battle()

    def _resolve_battle(self):
        """Compare revealed cards and determine outcome."""
        h_val = self._rank_value(self.human_card)
        a_val = self._rank_value(self.ai_card)

        if h_val > a_val:
            self.phase = PHASE_REVEAL
            self.reveal_timer = 0.0
            self.auto_advance = True
            self._set_message("You win this round!")
            self._winner_takes("human")
        elif a_val > h_val:
            self.phase = PHASE_REVEAL
            self.reveal_timer = 0.0
            self.auto_advance = True
            self._set_message("AI wins this round!")
            self._winner_takes("ai")
        else:
            # WAR!
            self._set_message("Tie! WAR!")
            self._start_war()

    def _winner_takes(self, winner):
        """Move all pot cards to the winner's won pile."""
        import random
        random.shuffle(self.pot)
        if winner == "human":
            self.human_won_pile.extend(self.pot)
        else:
            self.ai_won_pile.extend(self.pot)
        self.pot = []

    def _start_war(self):
        """Execute a war: each plays 3 face-down + 1 face-up."""
        self.in_war = True
        self.war_depth += 1
        self.war_stack_human = []
        self.war_stack_ai = []
        self.war_face_human = None
        self.war_face_ai = None

        # Each player puts 3 cards face-down
        for _ in range(3):
            hc = self._draw_from_deck(True)
            ac = self._draw_from_deck(False)
            if hc is None or ac is None:
                # Player can't complete the war -- they lose
                if hc:
                    self.pot.append(hc)
                if ac:
                    self.pot.append(ac)
                self._check_game_over()
                return
            self.war_stack_human.append(hc)
            self.war_stack_ai.append(ac)
            self.pot.extend([hc, ac])

        # Each plays 1 face-up
        hc = self._draw_from_deck(True)
        ac = self._draw_from_deck(False)
        if hc is None or ac is None:
            if hc:
                self.pot.append(hc)
            if ac:
                self.pot.append(ac)
            self._check_game_over()
            return

        hc.face_up = True
        ac.face_up = True
        self.war_face_human = hc
        self.war_face_ai = ac
        self.pot.extend([hc, ac])

        # Update the displayed "top cards" for comparison
        self.human_card = hc
        self.ai_card = ac

        self.phase = PHASE_WAR_REVEAL
        self.reveal_timer = 0.0
        self.auto_advance = True

        # Resolve
        h_val = self._rank_value(hc)
        a_val = self._rank_value(ac)
        if h_val > a_val:
            self._set_message("You win the war!")
            self._winner_takes("human")
        elif a_val > h_val:
            self._set_message("AI wins the war!")
            self._winner_takes("ai")
        else:
            self._set_message("Another tie! WAR again!")
            # Nested war -- will resolve on next auto-advance
            self._start_war()

    def _check_game_over(self):
        h = self._total_human()
        a = self._total_ai()
        if h == 0 or a >= 52:
            self.phase = PHASE_GAME_OVER
            self.txt_game_over_msg.text = "You Lose!"
            self.txt_game_over_msg.color = arcade.color.RED
            self.txt_status.text = ""
        elif a == 0 or h >= 52:
            self.phase = PHASE_GAME_OVER
            self.txt_game_over_msg.text = "You Win!"
            self.txt_game_over_msg.color = arcade.color.GREEN
            self.txt_status.text = ""

    def _set_message(self, msg):
        self.message = msg
        self.message_timer = 2.0
        self.txt_message.text = msg

    def _reset_round(self):
        """Reset for the next flip."""
        self.human_card = None
        self.ai_card = None
        self.war_stack_human = []
        self.war_stack_ai = []
        self.war_face_human = None
        self.war_face_ai = None
        self.in_war = False
        self.war_depth = 0
        self.auto_advance = False

        self._check_game_over()
        if self.phase != PHASE_GAME_OVER:
            self.phase = PHASE_READY
            self.txt_status.text = "Click your deck to flip!"

    # ------------------------------------------------------------------ helpers

    def _in_rect(self, x, y, cx, cy, w, h):
        return cx - w / 2 <= x <= cx + w / 2 and cy - h / 2 <= y <= cy + h / 2

    # ------------------------------------------------------------------ update

    def on_update(self, delta_time):
        # Message timer
        if self.message_timer > 0:
            self.message_timer -= delta_time
            if self.message_timer <= 0:
                self.txt_message.text = ""

        # Auto-advance after reveal
        if self.auto_advance and self.phase in (PHASE_REVEAL, PHASE_WAR_REVEAL):
            self.reveal_timer += delta_time
            if self.reveal_timer >= REVEAL_DELAY:
                self._reset_round()

        # Update counts
        self.txt_human_count.text = f"Your cards: {self._total_human()}"
        self.txt_ai_count.text = f"AI cards: {self._total_ai()}"

    # ------------------------------------------------------------------ draw

    def on_draw(self):
        self.clear()
        from renderers import war_renderer
        war_renderer.draw(self)

    # ------------------------------------------------------------------ input

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Back
        if self._in_rect(x, y, 60, HEIGHT - 30, BUTTON_W, BUTTON_H):
            self.window.show_view(self.menu_view)
            return

        # New Game
        if self._in_rect(x, y, WIDTH - 70, HEIGHT - 30, BUTTON_W + 10, BUTTON_H):
            self._deal()
            self._create_texts()
            return

        # Help
        if self.help_button.hit_test(x, y):
            rules_view = RulesView(
                "War", "war.txt", None, self.menu_view,
                existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        if self.phase == PHASE_READY:
            # Click human deck to flip
            deck_x, deck_y = 200, 250
            if self._in_rect(x, y, deck_x, deck_y, CARD_WIDTH, CARD_HEIGHT):
                self._flip_cards()
        elif self.phase in (PHASE_REVEAL, PHASE_WAR_REVEAL):
            # Click to skip the auto-advance wait
            self._reset_round()
