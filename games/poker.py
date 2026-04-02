"""
Texas Hold'em Poker -- multiplayer poker with AI opponents.

1-5 AI opponents. Small blind=10, big blind=20.
Standard Texas Hold'em: 2 hole cards, community cards (flop/turn/river),
4 betting rounds, best 5-card hand from 7 wins the pot.
"""

import random
import arcade
from pages.rules import RulesView
from ai.poker_ai import PokerAI, evaluate_hand, RANK_ORDER
from renderers import poker_renderer
from renderers.poker_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT,
    ACTION_BTN_W, ACTION_BTN_H, ACTION_BTN_Y, ACTION_BTN_SPACING,
    SETUP_BTN_W, SETUP_BTN_H,
    SEAT_POSITIONS,
)
from utils.card import create_deck
from utils.betting import format_chips

# Phases
PHASE_SETUP = "setup"
PHASE_PREFLOP = "preflop"
PHASE_FLOP = "flop"
PHASE_TURN = "turn"
PHASE_RIVER = "river"
PHASE_SHOWDOWN = "showdown"
PHASE_GAME_OVER = "game_over"

BETTING_PHASES = (PHASE_PREFLOP, PHASE_FLOP, PHASE_TURN, PHASE_RIVER)

# Blinds
SMALL_BLIND = 10
BIG_BLIND = 20

# Hand rank names for display
HAND_NAMES = {
    0: "High Card", 1: "One Pair", 2: "Two Pair", 3: "Three of a Kind",
    4: "Straight", 5: "Flush", 6: "Full House", 7: "Four of a Kind",
    8: "Straight Flush", 9: "Royal Flush",
}

AI_STYLES = ["tight", "balanced", "aggressive", "balanced", "tight"]


class PokerView(arcade.View):
    """Arcade View for Texas Hold'em Poker."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.phase = PHASE_SETUP
        self.pending_num_ai = 0

        # Deck
        self.deck = []
        self.deck_index = 0

        # Community cards
        self.community_cards = []

        # Players: list of dicts
        self.players = []
        self.dealer_button = 0
        self.current_player_idx = 0

        # Pot and betting
        self.pot = 0
        self.current_bet = 0  # current bet level this round
        self.min_raise = BIG_BLIND
        self.last_raiser = -1

        # Round tracking
        self.bets_this_round = {}  # player_idx -> amount bet this round

        # AI timer
        self.ai_timer = 0.0
        self.ai_acting = False

        # Showdown timer
        self.showdown_timer = 0.0

        # Raise amount selector
        self.raise_amount = BIG_BLIND

        # Setup buttons (1-5 AI)
        self.setup_buttons = []
        for i in range(5):
            bx = WIDTH // 2 - 160 + i * 80
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
            "Texas Hold'em", WIDTH // 2, bar_y, arcade.color.WHITE, 18,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Setup
        self.txt_setup_prompt = arcade.Text(
            "Choose number of AI opponents (1-5):",
            WIDTH // 2, HEIGHT // 2 + 80,
            arcade.color.WHITE, 20, anchor_x="center", anchor_y="center",
        )
        self.txt_setup_labels = []
        for i in range(5):
            bx = WIDTH // 2 - 160 + i * 80
            by = HEIGHT // 2 + 20
            self.txt_setup_labels.append(arcade.Text(
                str(i + 1), bx, by, arcade.color.WHITE, 18,
                anchor_x="center", anchor_y="center", bold=True,
            ))
        self.txt_start_btn = arcade.Text(
            "Start", WIDTH // 2, HEIGHT // 2 - 60,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )

        # Pot display
        self.txt_pot = arcade.Text(
            "Pot: $0", WIDTH // 2, HEIGHT // 2 + 70,
            arcade.color.GOLD, 18, anchor_x="center", anchor_y="center", bold=True,
        )

        # Player info (up to 6)
        self.txt_player_names = []
        self.txt_player_chips = []
        self.txt_player_bets = []
        self.txt_player_actions = []
        self.txt_dealer_btn_markers = []
        for i in range(6):
            sx, sy = SEAT_POSITIONS[i] if i < len(SEAT_POSITIONS) else (0, 0)
            self.txt_player_names.append(arcade.Text(
                "", sx, sy - 20, arcade.color.WHITE, 11,
                anchor_x="center", anchor_y="center", bold=True,
            ))
            self.txt_player_chips.append(arcade.Text(
                "", sx, sy - 34, arcade.color.GOLD, 10,
                anchor_x="center", anchor_y="center",
            ))
            self.txt_player_bets.append(arcade.Text(
                "", sx, sy - 48, arcade.color.LIGHT_GRAY, 10,
                anchor_x="center", anchor_y="center",
            ))
            self.txt_player_actions.append(arcade.Text(
                "", sx, sy + 50, arcade.color.YELLOW, 11,
                anchor_x="center", anchor_y="center", bold=True,
            ))
            self.txt_dealer_btn_markers.append(arcade.Text(
                "D", sx + 30, sy + 35, arcade.color.GOLD, 12,
                anchor_x="center", anchor_y="center", bold=True,
            ))

        # Action buttons
        btn_labels = ["Fold", "Check", "Call", "Raise"]
        self.txt_action_btns = []
        num_btns = len(btn_labels)
        total_w = (num_btns - 1) * ACTION_BTN_SPACING
        start_x = WIDTH // 2 - total_w // 2
        for i, label in enumerate(btn_labels):
            bx = start_x + i * ACTION_BTN_SPACING
            self.txt_action_btns.append(arcade.Text(
                label, bx, ACTION_BTN_Y, arcade.color.WHITE, 12,
                anchor_x="center", anchor_y="center", bold=True,
            ))

        # Raise amount
        rmx = WIDTH // 2 + 200
        self.txt_raise_amount = arcade.Text(
            "$20", rmx, ACTION_BTN_Y + 20, arcade.color.WHITE, 12,
            anchor_x="center", anchor_y="center",
        )
        self.txt_raise_minus = arcade.Text(
            "-", rmx - 30, ACTION_BTN_Y, arcade.color.WHITE, 16,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_raise_plus = arcade.Text(
            "+", rmx + 30, ACTION_BTN_Y, arcade.color.WHITE, 16,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Showdown / winner
        self.txt_winner_msg = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 - 40,
            arcade.color.GREEN, 18, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_hand_desc = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 - 60,
            arcade.color.LIGHT_GRAY, 14, anchor_x="center", anchor_y="center",
        )

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
    # Game setup
    # ------------------------------------------------------------------

    def _start_game(self):
        num_ai = self.pending_num_ai
        self.players = []

        # Human (index 0)
        self.players.append({
            "name": "You",
            "chips": 1000,
            "hole_cards": [],
            "folded": False,
            "all_in": False,
            "ai": None,
        })

        for i in range(num_ai):
            style = AI_STYLES[i % len(AI_STYLES)]
            self.players.append({
                "name": f"AI {i + 1}",
                "chips": 1000,
                "hole_cards": [],
                "folded": False,
                "all_in": False,
                "ai": PokerAI(style=style),
            })

        self.dealer_button = 0
        self._start_new_hand()

    def _start_new_hand(self):
        """Reset for a new hand: shuffle, post blinds, deal hole cards."""
        # Reset deck
        self.deck = create_deck(shuffled=True)
        self.deck_index = 0
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise = BIG_BLIND
        self.last_raiser = -1
        self.bets_this_round = {}
        self.showdown_timer = 0.0

        # Reset player state
        for p in self.players:
            p["hole_cards"] = []
            p["folded"] = False
            p["all_in"] = False

        # Remove broke players (except human)
        self.players = [p for i, p in enumerate(self.players)
                        if p["chips"] > 0 or i == 0]

        if len(self.players) < 2:
            self.phase = PHASE_GAME_OVER
            if self.players[0]["chips"] > 0:
                self.txt_game_over.text = "You Win!"
                self.txt_game_over.color = arcade.color.GREEN
            else:
                self.txt_game_over.text = "You're Broke!"
                self.txt_game_over.color = arcade.color.RED
            return

        # Advance dealer button
        self.dealer_button = (self.dealer_button) % len(self.players)

        # Post blinds
        num = len(self.players)
        sb_idx = (self.dealer_button + 1) % num
        bb_idx = (self.dealer_button + 2) % num
        if num == 2:
            sb_idx = self.dealer_button
            bb_idx = (self.dealer_button + 1) % num

        self._force_bet(sb_idx, SMALL_BLIND)
        self._force_bet(bb_idx, BIG_BLIND)
        self.current_bet = BIG_BLIND

        # Deal 2 hole cards to each player
        for p in self.players:
            for _ in range(2):
                card = self._deal_card()
                card.face_up = True
                p["hole_cards"].append(card)

        # First to act pre-flop is after big blind
        self.current_player_idx = (bb_idx + 1) % num
        self.last_raiser = bb_idx
        self.phase = PHASE_PREFLOP
        self.ai_timer = 0.0
        self.ai_acting = False
        self.raise_amount = BIG_BLIND

        # Clear action texts
        for txt in self.txt_player_actions:
            txt.text = ""
        self.txt_winner_msg.text = ""
        self.txt_hand_desc.text = ""

        self._update_display()

    def _force_bet(self, player_idx, amount):
        """Force a player to bet (blinds). Handles all-in."""
        p = self.players[player_idx]
        actual = min(amount, p["chips"])
        p["chips"] -= actual
        self.pot += actual
        self.bets_this_round[player_idx] = self.bets_this_round.get(player_idx, 0) + actual
        if p["chips"] <= 0:
            p["all_in"] = True

    def _deal_card(self):
        card = self.deck[self.deck_index]
        self.deck_index += 1
        return card

    # ------------------------------------------------------------------
    # Display updates
    # ------------------------------------------------------------------

    def _update_display(self):
        self.txt_pot.text = f"Pot: {format_chips(self.pot)}"

        for pi in range(6):
            if pi < len(self.players):
                p = self.players[pi]
                self.txt_player_names[pi].text = p["name"]
                self.txt_player_chips[pi].text = format_chips(p["chips"])
                bet = self.bets_this_round.get(pi, 0)
                self.txt_player_bets[pi].text = f"Bet: {format_chips(bet)}" if bet > 0 else ""
            else:
                self.txt_player_names[pi].text = ""
                self.txt_player_chips[pi].text = ""
                self.txt_player_bets[pi].text = ""
                self.txt_player_actions[pi].text = ""

        self.txt_raise_amount.text = format_chips(self.raise_amount)

    # ------------------------------------------------------------------
    # Available actions
    # ------------------------------------------------------------------

    def get_available_actions(self):
        """Return set of available actions for current player."""
        if self.phase not in BETTING_PHASES:
            return set()

        p = self.players[self.current_player_idx]
        if p["folded"] or p["all_in"]:
            return set()

        actions = {"fold"}
        to_call = self.current_bet - self.bets_this_round.get(self.current_player_idx, 0)

        if to_call <= 0:
            actions.add("check")
        else:
            if p["chips"] >= to_call:
                actions.add("call")

        # Raise
        if p["chips"] > to_call:
            actions.add("raise")

        return actions

    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------

    def _do_fold(self, player_idx):
        self.players[player_idx]["folded"] = True
        self.txt_player_actions[player_idx].text = "Fold"
        self.txt_player_actions[player_idx].color = (180, 80, 80)
        self._advance_action()

    def _do_check(self, player_idx):
        self.txt_player_actions[player_idx].text = "Check"
        self.txt_player_actions[player_idx].color = arcade.color.LIGHT_GRAY
        self._advance_action()

    def _do_call(self, player_idx):
        p = self.players[player_idx]
        to_call = self.current_bet - self.bets_this_round.get(player_idx, 0)
        actual = min(to_call, p["chips"])
        p["chips"] -= actual
        self.pot += actual
        self.bets_this_round[player_idx] = self.bets_this_round.get(player_idx, 0) + actual
        if p["chips"] <= 0:
            p["all_in"] = True
            self.txt_player_actions[player_idx].text = "All-In"
            self.txt_player_actions[player_idx].color = arcade.color.RED
        else:
            self.txt_player_actions[player_idx].text = "Call"
            self.txt_player_actions[player_idx].color = arcade.color.WHITE
        self._update_display()
        self._advance_action()

    def _do_raise(self, player_idx, raise_amount):
        p = self.players[player_idx]
        to_call = self.current_bet - self.bets_this_round.get(player_idx, 0)
        total_needed = to_call + raise_amount
        actual = min(total_needed, p["chips"])
        p["chips"] -= actual
        self.pot += actual
        self.bets_this_round[player_idx] = self.bets_this_round.get(player_idx, 0) + actual
        self.current_bet = self.bets_this_round[player_idx]
        self.min_raise = max(self.min_raise, raise_amount)
        self.last_raiser = player_idx

        if p["chips"] <= 0:
            p["all_in"] = True
            self.txt_player_actions[player_idx].text = "All-In"
            self.txt_player_actions[player_idx].color = arcade.color.RED
        else:
            self.txt_player_actions[player_idx].text = f"Raise {format_chips(raise_amount)}"
            self.txt_player_actions[player_idx].color = arcade.color.YELLOW

        self._update_display()
        self._advance_action()

    def _advance_action(self):
        """Move to next player or next phase."""
        # Check if only one player left
        active = [i for i, p in enumerate(self.players) if not p["folded"]]
        if len(active) <= 1:
            self._award_pot(active[0] if active else 0)
            return

        # Find next player who can act
        num = len(self.players)
        start = self.current_player_idx
        for offset in range(1, num + 1):
            idx = (start + offset) % num
            p = self.players[idx]
            if p["folded"] or p["all_in"]:
                continue
            # If we've gone around to the last raiser and everyone has matched
            if idx == self.last_raiser:
                self._end_betting_round()
                return
            to_call = self.current_bet - self.bets_this_round.get(idx, 0)
            # This player can act
            self.current_player_idx = idx
            self.ai_timer = 0.0
            self.ai_acting = False
            self._update_display()
            return

        # Everyone has acted or is all-in
        self._end_betting_round()

    def _end_betting_round(self):
        """Move to next phase (flop/turn/river/showdown)."""
        phase_order = [PHASE_PREFLOP, PHASE_FLOP, PHASE_TURN, PHASE_RIVER, PHASE_SHOWDOWN]
        current_idx = phase_order.index(self.phase)
        next_phase = phase_order[current_idx + 1]

        # Deal community cards
        if next_phase == PHASE_FLOP:
            for _ in range(3):
                card = self._deal_card()
                card.face_up = True
                self.community_cards.append(card)
        elif next_phase in (PHASE_TURN, PHASE_RIVER):
            card = self._deal_card()
            card.face_up = True
            self.community_cards.append(card)

        if next_phase == PHASE_SHOWDOWN:
            self._do_showdown()
            return

        # Reset for new betting round
        self.phase = next_phase
        self.current_bet = 0
        self.bets_this_round = {}
        self.min_raise = BIG_BLIND
        self.raise_amount = BIG_BLIND

        # Clear action texts
        for txt in self.txt_player_actions:
            txt.text = ""

        # First to act post-flop: first active player after dealer
        num = len(self.players)
        for offset in range(1, num + 1):
            idx = (self.dealer_button + offset) % num
            p = self.players[idx]
            if not p["folded"] and not p["all_in"]:
                self.current_player_idx = idx
                self.last_raiser = idx
                break

        self.ai_timer = 0.0
        self.ai_acting = False
        self._update_display()

    # ------------------------------------------------------------------
    # Showdown
    # ------------------------------------------------------------------

    def _do_showdown(self):
        """Evaluate hands and determine winner."""
        self.phase = PHASE_SHOWDOWN
        self.showdown_timer = 0.0

        # Reveal all cards
        for p in self.players:
            for c in p["hole_cards"]:
                c.face_up = True

        # Evaluate each active player's hand
        active = [i for i, p in enumerate(self.players) if not p["folded"]]
        best_eval = None
        winner_idx = active[0]

        for idx in active:
            p = self.players[idx]
            all_cards = p["hole_cards"] + self.community_cards
            evaluation = evaluate_hand(all_cards)
            if best_eval is None or evaluation > best_eval:
                best_eval = evaluation
                winner_idx = idx

        self._award_pot(winner_idx, best_eval)

    def _award_pot(self, winner_idx, hand_eval=None):
        """Give the pot to the winner."""
        winner = self.players[winner_idx]
        winner["chips"] += self.pot

        winner_name = winner["name"]
        if hand_eval:
            tier = hand_eval[0]
            hand_name = HAND_NAMES.get(tier, "Unknown")
            self.txt_winner_msg.text = f"{winner_name} wins {format_chips(self.pot)}!"
            self.txt_hand_desc.text = f"with {hand_name}"
        else:
            self.txt_winner_msg.text = f"{winner_name} wins {format_chips(self.pot)}! (others folded)"
            self.txt_hand_desc.text = ""

        self.pot = 0
        self.phase = PHASE_SHOWDOWN
        self.showdown_timer = 0.0
        self._update_display()

    # ------------------------------------------------------------------
    # Arcade callbacks
    # ------------------------------------------------------------------

    def on_update(self, delta_time):
        if self.phase in BETTING_PHASES:
            p = self.players[self.current_player_idx]
            if p["ai"] is not None and not p["folded"] and not p["all_in"]:
                self.ai_timer += delta_time
                if self.ai_timer >= 0.5 and not self.ai_acting:
                    self.ai_acting = True
                    self._ai_act(self.current_player_idx)

        elif self.phase == PHASE_SHOWDOWN:
            self.showdown_timer += delta_time
            if self.showdown_timer >= 3.0:
                # Auto-advance to next hand
                self.dealer_button = (self.dealer_button + 1) % len(self.players)
                # Check if human is broke
                if self.players[0]["chips"] <= 0:
                    self.phase = PHASE_GAME_OVER
                    self.txt_game_over.text = "You're Broke!"
                    self.txt_game_over.color = arcade.color.RED
                else:
                    # Check if all AI are broke
                    alive_ai = [p for p in self.players[1:] if p["chips"] > 0]
                    if not alive_ai:
                        self.phase = PHASE_GAME_OVER
                        self.txt_game_over.text = "You Win!"
                        self.txt_game_over.color = arcade.color.GREEN
                    else:
                        self._start_new_hand()

    def _ai_act(self, player_idx):
        """Execute AI decision for the given player."""
        p = self.players[player_idx]
        ai = p["ai"]

        decision = ai.decide(
            hole_cards=p["hole_cards"],
            community_cards=self.community_cards,
            pot=self.pot,
            current_bet=self.current_bet,
            my_bet_this_round=self.bets_this_round.get(player_idx, 0),
            my_chips=p["chips"],
            min_raise=self.min_raise,
            phase=self.phase,
        )

        action = decision[0]
        if action == "fold":
            self._do_fold(player_idx)
        elif action == "check":
            to_call = self.current_bet - self.bets_this_round.get(player_idx, 0)
            if to_call > 0:
                self._do_call(player_idx)
            else:
                self._do_check(player_idx)
        elif action == "call":
            self._do_call(player_idx)
        elif action == "raise":
            amount = decision[1] if len(decision) > 1 else self.min_raise
            amount = max(self.min_raise, amount)
            self._do_raise(player_idx, amount)
        else:
            # Fallback
            to_call = self.current_bet - self.bets_this_round.get(player_idx, 0)
            if to_call <= 0:
                self._do_check(player_idx)
            else:
                self._do_call(player_idx)

    def on_draw(self):
        self.clear()
        poker_renderer.draw(self)

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        # Top bar
        if self._in_rect(x, y, 55, bar_y, 90, 35):
            self.window.show_view(self.menu_view)
            return
        if self._in_rect(x, y, WIDTH - 65, bar_y, 110, 35):
            self.phase = PHASE_SETUP
            self.pending_num_ai = 0
            return
        if self._in_rect(x, y, WIDTH - 135, bar_y, 40, 40):
            rules_view = RulesView(
                "Texas Hold'em", "poker.txt", None, self.menu_view,
                existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        if self.phase == PHASE_SETUP:
            self._handle_setup_click(x, y)
        elif self.phase in BETTING_PHASES:
            self._handle_action_click(x, y)
        elif self.phase == PHASE_SHOWDOWN:
            # Click to skip wait
            self.dealer_button = (self.dealer_button + 1) % len(self.players)
            if self.players[0]["chips"] <= 0:
                self.phase = PHASE_GAME_OVER
                self.txt_game_over.text = "You're Broke!"
                self.txt_game_over.color = arcade.color.RED
            else:
                alive_ai = [p for p in self.players[1:] if p["chips"] > 0]
                if not alive_ai:
                    self.phase = PHASE_GAME_OVER
                    self.txt_game_over.text = "You Win!"
                    self.txt_game_over.color = arcade.color.GREEN
                else:
                    self._start_new_hand()

    def _handle_setup_click(self, x, y):
        for i in range(5):
            bx, by, bw, bh = self.setup_buttons[i]
            if self._in_rect(x, y, bx, by, bw, bh):
                self.pending_num_ai = i + 1
                return
        if self.pending_num_ai > 0:
            if self._in_rect(x, y, WIDTH // 2, HEIGHT // 2 - 60, 140, 44):
                self._start_game()

    def _handle_action_click(self, x, y):
        if self.current_player_idx != 0:
            return
        if self.players[0]["folded"]:
            return

        actions = self.get_available_actions()
        btn_defs = ["fold", "check", "call", "raise"]
        num_btns = len(btn_defs)
        total_w = (num_btns - 1) * ACTION_BTN_SPACING
        start_x = WIDTH // 2 - total_w // 2

        for i, action in enumerate(btn_defs):
            bx = start_x + i * ACTION_BTN_SPACING
            if self._in_rect(x, y, bx, ACTION_BTN_Y, ACTION_BTN_W, ACTION_BTN_H):
                if action in actions:
                    if action == "fold":
                        self._do_fold(0)
                    elif action == "check":
                        self._do_check(0)
                    elif action == "call":
                        self._do_call(0)
                    elif action == "raise":
                        self._do_raise(0, self.raise_amount)
                return

        # Raise +/- buttons
        if "raise" in actions:
            rmx = WIDTH // 2 + 200
            if self._in_rect(x, y, rmx - 30, ACTION_BTN_Y, 28, 28):
                self.raise_amount = max(self.min_raise, self.raise_amount - BIG_BLIND)
                self.txt_raise_amount.text = format_chips(self.raise_amount)
                return
            if self._in_rect(x, y, rmx + 30, ACTION_BTN_Y, 28, 28):
                max_raise = self.players[0]["chips"]
                self.raise_amount = min(max_raise, self.raise_amount + BIG_BLIND)
                self.txt_raise_amount.text = format_chips(self.raise_amount)
                return

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _in_rect(self, x, y, cx, cy, w, h):
        return cx - w / 2 <= x <= cx + w / 2 and cy - h / 2 <= y <= cy + h / 2
