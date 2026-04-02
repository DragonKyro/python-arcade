"""
Blackjack -- classic casino card game with AI opponents.

Dealer + human player + 0-3 AI players. Standard blackjack rules:
hit, stand, double down, split. Dealer hits on 16, stands on 17+.
Blackjack (A + 10-value) pays 3:2.
"""

import arcade
from pages.rules import RulesView
from ai.blackjack_ai import BlackjackAI, choose_bet
from renderers import blackjack_renderer
from renderers.blackjack_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT,
    ACTION_BTN_W, ACTION_BTN_H, ACTION_BTN_Y, ACTION_BTN_SPACING,
    BET_BTN_W, BET_BTN_H, BET_BTN_Y, BET_BTN_SPACING,
    SETUP_BTN_W, SETUP_BTN_H,
)
from utils.card import create_deck, CARD_WIDTH, CARD_HEIGHT
from utils.betting import BettingPlayer, BET_AMOUNTS, format_chips

# Phases
PHASE_SETUP = "setup"
PHASE_BETTING = "betting"
PHASE_DEALING = "dealing"
PHASE_PLAYER_TURN = "player_turn"
PHASE_DEALER_TURN = "dealer_turn"
PHASE_RESULT = "result"
PHASE_GAME_OVER = "game_over"


def hand_value(cards):
    """Calculate best blackjack hand value. Aces count as 1 or 11."""
    total = 0
    aces = 0
    for card in cards:
        if card.rank == "a":
            aces += 1
            total += 11
        elif card.rank in ("j", "q", "k"):
            total += 10
        else:
            total += int(card.rank)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total


def is_blackjack(cards):
    """Check if a 2-card hand is a natural blackjack."""
    if len(cards) != 2:
        return False
    return hand_value(cards) == 21


def card_bj_value(card):
    """Get blackjack value of a single card (A=11)."""
    if card.rank == "a":
        return 11
    if card.rank in ("j", "q", "k"):
        return 10
    return int(card.rank)


class BlackjackView(arcade.View):
    """Arcade View for Blackjack."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.phase = PHASE_SETUP
        self.pending_num_ai = 0

        # Deck
        self.deck = []
        self.deck_index = 0

        # Dealer
        self.dealer_hand = []

        # Players: list of dicts with BettingPlayer, hands, AI
        self.players = []
        self.current_player_idx = 0
        self.current_hand_idx = 0

        # AI timer
        self.ai_timer = 0.0
        self.ai_acting = False

        # Dealer reveal timer
        self.dealer_timer = 0.0

        # Bet selection
        self.selected_bet_index = 2  # default to middle bet

        # Setup buttons (0-3 AI)
        self.setup_buttons = []
        for i in range(4):
            bx = WIDTH // 2 - 120 + i * 80
            by = HEIGHT // 2 + 20
            self.setup_buttons.append((bx, by, SETUP_BTN_W, SETUP_BTN_H))

        self._create_texts()

    # ------------------------------------------------------------------
    # Text objects
    # ------------------------------------------------------------------

    def _create_texts(self):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        self.txt_back = arcade.Text(
            "Back", 55, bar_y, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_new_game = arcade.Text(
            "New Game", WIDTH - 65, bar_y, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_help = arcade.Text(
            "?", WIDTH - 135, bar_y, arcade.color.WHITE, 16,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_title = arcade.Text(
            "Blackjack", WIDTH // 2, bar_y, arcade.color.WHITE, 20,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Setup phase
        self.txt_setup_prompt = arcade.Text(
            "Choose number of AI players (0-3):",
            WIDTH // 2, HEIGHT // 2 + 80,
            arcade.color.WHITE, 20, anchor_x="center", anchor_y="center",
        )
        self.txt_setup_labels = []
        for i in range(4):
            bx = WIDTH // 2 - 120 + i * 80
            by = HEIGHT // 2 + 20
            self.txt_setup_labels.append(arcade.Text(
                str(i), bx, by, arcade.color.WHITE, 18,
                anchor_x="center", anchor_y="center", bold=True,
            ))
        self.txt_start_btn = arcade.Text(
            "Start", WIDTH // 2, HEIGHT // 2 - 60,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )

        # Betting phase
        self.txt_bet_prompt = arcade.Text(
            "Place your bet:", WIDTH // 2, HEIGHT // 2 + 40,
            arcade.color.WHITE, 20, anchor_x="center", anchor_y="center",
        )
        self.txt_chips_display = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 80,
            arcade.color.GOLD, 16, anchor_x="center", anchor_y="center",
        )
        self.txt_bet_labels = []
        for i, amt in enumerate(BET_AMOUNTS):
            bx = WIDTH // 2 + (i - 2) * BET_BTN_SPACING
            self.txt_bet_labels.append(arcade.Text(
                format_chips(amt), bx, BET_BTN_Y,
                arcade.color.WHITE, 12, anchor_x="center", anchor_y="center",
            ))
        self.txt_deal_btn = arcade.Text(
            "Deal", WIDTH // 2, BET_BTN_Y - 60,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )

        # Dealer label and value
        self.txt_dealer_label = arcade.Text(
            "Dealer", WIDTH // 2, HEIGHT - TOP_BAR_HEIGHT - 40,
            arcade.color.WHITE, 14, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_dealer_value = arcade.Text(
            "", WIDTH // 2, HEIGHT - TOP_BAR_HEIGHT - 140,
            arcade.color.WHITE, 14, anchor_x="center", anchor_y="center",
        )

        # Player info (up to 4 players: human + 3 AI)
        self.txt_player_names = []
        self.txt_player_chips = []
        self.txt_player_values = []
        self.txt_player_results = []
        for i in range(4):
            self.txt_player_names.append(arcade.Text(
                "", 0, 0, arcade.color.WHITE, 12,
                anchor_x="center", anchor_y="center", bold=True,
            ))
            self.txt_player_chips.append(arcade.Text(
                "", 0, 0, arcade.color.GOLD, 11,
                anchor_x="center", anchor_y="center",
            ))
            self.txt_player_values.append(arcade.Text(
                "", 0, 0, arcade.color.LIGHT_GRAY, 12,
                anchor_x="center", anchor_y="center",
            ))
            self.txt_player_results.append(arcade.Text(
                "", 0, 0, arcade.color.WHITE, 14,
                anchor_x="center", anchor_y="center", bold=True,
            ))

        # Action buttons
        btn_labels = ["Hit", "Stand", "Double", "Split"]
        self.txt_action_btns = []
        num_btns = len(btn_labels)
        total_w = (num_btns - 1) * ACTION_BTN_SPACING
        start_x = WIDTH // 2 - total_w // 2
        for i, label in enumerate(btn_labels):
            bx = start_x + i * ACTION_BTN_SPACING
            self.txt_action_btns.append(arcade.Text(
                label, bx, ACTION_BTN_Y, arcade.color.WHITE, 13,
                anchor_x="center", anchor_y="center", bold=True,
            ))

        # Game over
        self.txt_game_over = arcade.Text(
            "Game Over", WIDTH // 2, HEIGHT // 2 + 30,
            arcade.color.WHITE, 36, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_hint = arcade.Text(
            "Click 'New Game' to play again",
            WIDTH // 2, HEIGHT // 2 - 20,
            arcade.color.LIGHT_GRAY, 14, anchor_x="center", anchor_y="center",
        )

    # ------------------------------------------------------------------
    # Game setup and dealing
    # ------------------------------------------------------------------

    def _start_game(self):
        num_ai = self.pending_num_ai
        self.players = []

        # Human player (index 0)
        self.players.append({
            "betting": BettingPlayer("You", chips=1000, is_human=True),
            "hands": [{"cards": [], "bet": 0, "stood": False, "doubled": False}],
            "ai": None,
        })

        styles = ["tight", "balanced", "aggressive"]
        for i in range(num_ai):
            name = f"AI {i + 1}"
            self.players.append({
                "betting": BettingPlayer(name, chips=1000, is_human=False),
                "hands": [{"cards": [], "bet": 0, "stood": False, "doubled": False}],
                "ai": BlackjackAI(),
            })

        self._update_player_texts()
        self.phase = PHASE_BETTING

    def _update_player_texts(self):
        num_players = len(self.players)
        total_width = (num_players - 1) * 180
        start_x = WIDTH // 2 - total_width // 2

        for pi in range(4):
            if pi < num_players:
                player = self.players[pi]
                bp = player["betting"]
                px = start_x + pi * 180
                py = 220

                self.txt_player_names[pi].text = bp.name
                self.txt_player_names[pi].x = px
                self.txt_player_names[pi].y = py + 65

                self.txt_player_chips[pi].text = format_chips(bp.chips)
                self.txt_player_chips[pi].x = px
                self.txt_player_chips[pi].y = py + 50

                # Hand value
                hand = player["hands"][0]
                if hand["cards"]:
                    val = hand_value(hand["cards"])
                    self.txt_player_values[pi].text = str(val)
                else:
                    self.txt_player_values[pi].text = ""
                self.txt_player_values[pi].x = px
                self.txt_player_values[pi].y = py - 60

                self.txt_player_results[pi].x = px
                self.txt_player_results[pi].y = py - 78
            else:
                self.txt_player_names[pi].text = ""
                self.txt_player_chips[pi].text = ""
                self.txt_player_values[pi].text = ""
                self.txt_player_results[pi].text = ""

    def _new_deck_if_needed(self):
        """Shuffle a new deck if we're running low."""
        if self.deck_index > len(self.deck) - 20:
            self.deck = create_deck(shuffled=True)
            self.deck_index = 0

    def _deal_card(self, face_up=True):
        """Deal one card from the deck."""
        self._new_deck_if_needed()
        card = self.deck[self.deck_index]
        card.face_up = face_up
        self.deck_index += 1
        return card

    def _start_hand(self):
        """Deal initial cards to all players and dealer."""
        self._new_deck_if_needed()

        # Reset hands
        self.dealer_hand = []
        for player in self.players:
            player["hands"] = [{"cards": [], "bet": 0, "stood": False, "doubled": False}]

        # Place bets
        human = self.players[0]
        bet_amt = BET_AMOUNTS[self.selected_bet_index]
        actual = human["betting"].place_bet(bet_amt)
        human["hands"][0]["bet"] = actual

        for player in self.players[1:]:
            ai_bet = choose_bet(player["betting"].chips)
            actual = player["betting"].place_bet(ai_bet)
            player["hands"][0]["bet"] = actual

        # Deal 2 cards to each player, then dealer
        for _ in range(2):
            for player in self.players:
                player["hands"][0]["cards"].append(self._deal_card(face_up=True))
            self.dealer_hand.append(self._deal_card(face_up=True))

        # Dealer's first card is face down
        self.dealer_hand[0].face_up = False

        self.current_player_idx = 0
        self.current_hand_idx = 0
        self.ai_timer = 0.0
        self.ai_acting = False
        self.phase = PHASE_PLAYER_TURN

        # Clear results
        for txt in self.txt_player_results:
            txt.text = ""

        self._update_player_texts()
        self._update_dealer_text()
        self._skip_finished_players()

    def _update_dealer_text(self):
        if not self.dealer_hand:
            self.txt_dealer_value.text = ""
            return
        if self.phase == PHASE_PLAYER_TURN:
            # Only show up-card value
            visible = [c for c in self.dealer_hand if c.face_up]
            if visible:
                self.txt_dealer_value.text = str(hand_value(visible))
            else:
                self.txt_dealer_value.text = "?"
        else:
            self.txt_dealer_value.text = str(hand_value(self.dealer_hand))

    # ------------------------------------------------------------------
    # Available actions
    # ------------------------------------------------------------------

    def get_available_actions(self):
        """Return set of available actions for current player/hand."""
        if self.phase != PHASE_PLAYER_TURN:
            return set()
        player = self.players[self.current_player_idx]
        hand = player["hands"][self.current_hand_idx]
        cards = hand["cards"]
        bp = player["betting"]

        actions = {"hit", "stand"}

        # Double down: 2 cards, enough chips
        if len(cards) == 2 and bp.chips >= hand["bet"]:
            actions.add("double")

        # Split: 2 cards of same value, enough chips
        if (len(cards) == 2 and
                card_bj_value(cards[0]) == card_bj_value(cards[1]) and
                bp.chips >= hand["bet"] and
                len(player["hands"]) < 4):  # max 4 split hands
            actions.add("split")

        return actions

    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------

    def _do_hit(self):
        player = self.players[self.current_player_idx]
        hand = player["hands"][self.current_hand_idx]
        hand["cards"].append(self._deal_card(face_up=True))

        val = hand_value(hand["cards"])
        if val >= 21:
            hand["stood"] = True
            self._advance_to_next()
        self._update_player_texts()

    def _do_stand(self):
        player = self.players[self.current_player_idx]
        hand = player["hands"][self.current_hand_idx]
        hand["stood"] = True
        self._advance_to_next()

    def _do_double(self):
        player = self.players[self.current_player_idx]
        hand = player["hands"][self.current_hand_idx]
        bp = player["betting"]

        # Double the bet
        extra = bp.place_bet(hand["bet"])
        hand["bet"] += extra
        hand["doubled"] = True

        # Get exactly one more card
        hand["cards"].append(self._deal_card(face_up=True))
        hand["stood"] = True
        self._update_player_texts()
        self._advance_to_next()

    def _do_split(self):
        player = self.players[self.current_player_idx]
        hand = player["hands"][self.current_hand_idx]
        bp = player["betting"]
        cards = hand["cards"]

        # Create new hand with second card
        new_hand = {
            "cards": [cards.pop()],
            "bet": bp.place_bet(hand["bet"]),
            "stood": False,
            "doubled": False,
        }

        # Deal one new card to each hand
        hand["cards"].append(self._deal_card(face_up=True))
        new_hand["cards"].append(self._deal_card(face_up=True))

        player["hands"].insert(self.current_hand_idx + 1, new_hand)
        self._update_player_texts()

    def _advance_to_next(self):
        """Advance to next hand or next player."""
        player = self.players[self.current_player_idx]

        # Check next hand for current player
        if self.current_hand_idx + 1 < len(player["hands"]):
            self.current_hand_idx += 1
            self.ai_timer = 0.0
            self.ai_acting = False
            return

        # Move to next player
        self.current_player_idx += 1
        self.current_hand_idx = 0
        self.ai_timer = 0.0
        self.ai_acting = False

        if self.current_player_idx >= len(self.players):
            # All players done -- dealer's turn
            self._start_dealer_turn()
            return

        self._skip_finished_players()

    def _skip_finished_players(self):
        """Skip players who already busted or have blackjack."""
        while self.current_player_idx < len(self.players):
            player = self.players[self.current_player_idx]
            all_done = True
            for hi, hand in enumerate(player["hands"]):
                if not hand["stood"]:
                    val = hand_value(hand["cards"])
                    if val >= 21:
                        hand["stood"] = True
                    else:
                        self.current_hand_idx = hi
                        all_done = False
                        break
            if not all_done:
                break
            self.current_player_idx += 1
            self.current_hand_idx = 0

        if self.current_player_idx >= len(self.players):
            self._start_dealer_turn()

    # ------------------------------------------------------------------
    # Dealer turn
    # ------------------------------------------------------------------

    def _start_dealer_turn(self):
        self.phase = PHASE_DEALER_TURN
        # Reveal hole card
        self.dealer_hand[0].face_up = True
        self.dealer_timer = 0.0
        self._update_dealer_text()

    def _dealer_play(self):
        """Dealer hits until 17+."""
        while hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self._deal_card(face_up=True))
        self._update_dealer_text()
        self._resolve_hands()

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def _resolve_hands(self):
        dealer_val = hand_value(self.dealer_hand)
        dealer_bj = is_blackjack(self.dealer_hand)
        dealer_bust = dealer_val > 21

        for pi, player in enumerate(self.players):
            bp = player["betting"]
            total_result = 0

            for hand in player["hands"]:
                cards = hand["cards"]
                val = hand_value(cards)
                bet = hand["bet"]
                player_bj = is_blackjack(cards)
                bust = val > 21

                if bust:
                    # Player busted -- already lost (bet was placed)
                    result_text = "Bust"
                    result_color = (255, 80, 80)
                elif player_bj and not dealer_bj:
                    # Blackjack pays 3:2
                    payout = int(bet * 2.5)
                    bp.chips += payout
                    bp.current_bet = 0
                    result_text = "Blackjack!"
                    result_color = arcade.color.GOLD
                elif player_bj and dealer_bj:
                    # Both blackjack -- push
                    bp.chips += bet
                    bp.current_bet = 0
                    result_text = "Push"
                    result_color = arcade.color.LIGHT_GRAY
                elif dealer_bust or val > dealer_val:
                    # Player wins
                    bp.chips += bet * 2
                    bp.current_bet = 0
                    result_text = "Win!"
                    result_color = arcade.color.GREEN
                elif val == dealer_val:
                    # Push
                    bp.chips += bet
                    bp.current_bet = 0
                    result_text = "Push"
                    result_color = arcade.color.LIGHT_GRAY
                else:
                    # Dealer wins
                    result_text = "Lose"
                    result_color = (255, 80, 80)

                bp.current_bet = 0

            # Set result text for first hand (simplified display)
            if pi < len(self.txt_player_results):
                self.txt_player_results[pi].text = result_text
                self.txt_player_results[pi].color = result_color

        self._update_player_texts()
        self.phase = PHASE_RESULT

        # Check if human is broke
        if self.players[0]["betting"].is_broke:
            self.phase = PHASE_GAME_OVER

    # ------------------------------------------------------------------
    # Arcade callbacks
    # ------------------------------------------------------------------

    def on_update(self, delta_time):
        if self.phase == PHASE_PLAYER_TURN:
            # AI turn
            if self.current_player_idx > 0 and self.current_player_idx < len(self.players):
                player = self.players[self.current_player_idx]
                if player["ai"] is not None:
                    self.ai_timer += delta_time
                    if self.ai_timer >= 0.5 and not self.ai_acting:
                        self.ai_acting = True
                        hand = player["hands"][self.current_hand_idx]
                        cards = hand["cards"]
                        val = hand_value(cards)
                        dealer_up = self.dealer_hand[1] if len(self.dealer_hand) > 1 else self.dealer_hand[0]
                        dealer_val = card_bj_value(dealer_up)

                        actions = self.get_available_actions()
                        can_split = "split" in actions
                        can_double = "double" in actions

                        decision = player["ai"].decide(
                            val, len(cards), dealer_val, can_split, can_double
                        )

                        if decision == "double" and "double" in actions:
                            self._do_double()
                        elif decision == "split" and "split" in actions:
                            self._do_split()
                        elif decision == "hit":
                            self._do_hit()
                        else:
                            self._do_stand()

                        self.ai_timer = 0.0
                        self.ai_acting = False

        elif self.phase == PHASE_DEALER_TURN:
            self.dealer_timer += delta_time
            if self.dealer_timer >= 0.5:
                self._dealer_play()

        # Update chips display for betting phase
        if self.phase == PHASE_BETTING and self.players:
            bp = self.players[0]["betting"]
            self.txt_chips_display.text = f"Your chips: {format_chips(bp.chips)}"

    def on_draw(self):
        self.clear()
        blackjack_renderer.draw(self)

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
                "Blackjack", "blackjack.txt", None, self.menu_view,
                existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        if self.phase == PHASE_SETUP:
            self._handle_setup_click(x, y)
        elif self.phase == PHASE_BETTING:
            self._handle_betting_click(x, y)
        elif self.phase == PHASE_PLAYER_TURN:
            self._handle_action_click(x, y)
        elif self.phase == PHASE_RESULT:
            # Click to start next hand
            self.phase = PHASE_BETTING

    def _handle_setup_click(self, x, y):
        for i in range(4):
            bx, by, bw, bh = self.setup_buttons[i]
            if self._in_rect(x, y, bx, by, bw, bh):
                self.pending_num_ai = i
                return
        # Start button
        if self._in_rect(x, y, WIDTH // 2, HEIGHT // 2 - 60, 140, 44):
            self._start_game()

    def _handle_betting_click(self, x, y):
        # Bet amount buttons
        for i in range(len(BET_AMOUNTS)):
            bx = WIDTH // 2 + (i - 2) * BET_BTN_SPACING
            if self._in_rect(x, y, bx, BET_BTN_Y, BET_BTN_W, BET_BTN_H):
                bp = self.players[0]["betting"]
                if bp.chips >= BET_AMOUNTS[i]:
                    self.selected_bet_index = i
                return

        # Deal button
        if self._in_rect(x, y, WIDTH // 2, BET_BTN_Y - 60, 120, 40):
            self._start_hand()

    def _handle_action_click(self, x, y):
        if self.current_player_idx != 0:
            return  # Not human's turn

        actions = self.get_available_actions()
        btn_names = ["hit", "stand", "double", "split"]
        num_btns = len(btn_names)
        total_w = (num_btns - 1) * ACTION_BTN_SPACING
        start_x = WIDTH // 2 - total_w // 2

        for i, action in enumerate(btn_names):
            bx = start_x + i * ACTION_BTN_SPACING
            if self._in_rect(x, y, bx, ACTION_BTN_Y, ACTION_BTN_W, ACTION_BTN_H):
                if action in actions:
                    if action == "hit":
                        self._do_hit()
                    elif action == "stand":
                        self._do_stand()
                    elif action == "double":
                        self._do_double()
                    elif action == "split":
                        self._do_split()
                return

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _in_rect(self, x, y, cx, cy, w, h):
        return cx - w / 2 <= x <= cx + w / 2 and cy - h / 2 <= y <= cy + h / 2
