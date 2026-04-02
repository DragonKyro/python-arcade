"""
Spades card game view using Arcade 3.x APIs.

4 players in 2 teams: human (P0) + AI partner (P2) vs AI opponents (P1, P3).
Deal all 52 cards (13 each). Bidding phase, then trick play.
Spades are trump. Can't lead spades until broken.
Scoring: meet bid = bid*10 + bags; fail = -bid*10; 10 bags = -100.
Nil bid: +100 if met, -100 if not. Play to 500.
"""

import arcade
from pages.components import Button
from pages.rules import RulesView
from ai.spades_ai import SpadesAI
from utils.card import Card, create_deck, CARD_WIDTH, CARD_HEIGHT, RANK_VALUES
from utils.tricks import (
    trick_winner, can_follow_suit, get_valid_plays, sort_hand,
    hand_score_spades,
)
from renderers.spades_renderer import (
    WIDTH, HEIGHT, BUTTON_W, BUTTON_H,
)

# Game phases
PHASE_BID = "bid"
PHASE_PLAY = "play"
PHASE_TRICK_DONE = "trick_done"
PHASE_ROUND_OVER = "round_over"
PHASE_GAME_OVER = "game_over"

PLAYER_NAMES = ["You", "West (Opp)", "Partner (AI)", "East (Opp)"]
TEAM_NAMES = ["Your Team", "Opponents"]


class SpadesView(arcade.View):
    """Arcade View for Spades."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.help_button = Button(
            WIDTH - 145, HEIGHT - 30, 40, 36, "?", color=arcade.color.DARK_SLATE_BLUE
        )

        # Core state
        self.phase = PHASE_BID
        self.hands = [[], [], [], []]
        self.tricks_won = [0, 0, 0, 0]         # tricks won this round per player
        self.bids = [None, None, None, None]    # bid per player (None = not yet bid)
        self.current_trick = []
        self.trick_leader = 0
        self.current_player = 0
        self.spades_broken = False
        self.dealer = 0

        # Team scores: team 0 = P0+P2, team 1 = P1+P3
        self.team_scores = [0, 0]
        self.team_bags = [0, 0]

        # Bidding UI
        self.human_bid_value = 1
        self.bid_order = []         # order in which players bid (left of dealer first)

        # AI
        self.ai = [None, SpadesAI(1), SpadesAI(2), SpadesAI(3)]

        # Timing
        self.ai_timer = 0.0
        self.trick_done_timer = 0.0

        # Round history
        self.round_number = 0

        self._create_texts()
        self._start_round()

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
            "Spades", WIDTH // 2, HEIGHT - 30,
            arcade.color.WHITE, 22, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_phase_info = arcade.Text(
            "", WIDTH // 2, HEIGHT - 65,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center",
        )

        # Player name labels
        self.txt_player_names = []
        positions = [
            (WIDTH // 2, 155),
            (65, HEIGHT // 2),
            (WIDTH // 2, HEIGHT - 95),
            (WIDTH - 65, HEIGHT // 2),
        ]
        for i, (px, py) in enumerate(positions):
            t = arcade.Text(
                PLAYER_NAMES[i], px, py, arcade.color.WHITE, 13,
                anchor_x="center", anchor_y="center", bold=True,
            )
            self.txt_player_names.append(t)

        # Bid display per player
        self.txt_bid_labels = []
        bid_positions = [
            (WIDTH // 2, 138),
            (65, HEIGHT // 2 - 18),
            (WIDTH // 2, HEIGHT - 112),
            (WIDTH - 65, HEIGHT // 2 - 18),
        ]
        for px, py in bid_positions:
            t = arcade.Text(
                "", px, py, arcade.color.LIGHT_GRAY, 11,
                anchor_x="center", anchor_y="center",
            )
            self.txt_bid_labels.append(t)

        # Score panel
        self.txt_score_header = arcade.Text(
            "Scores", WIDTH - 70, HEIGHT - 100,
            arcade.color.WHITE, 14, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_team_scores = []
        for i in range(2):
            t = arcade.Text(
                "", WIDTH - 70, HEIGHT - 120 - i * 20,
                arcade.color.LIGHT_GRAY, 11, anchor_x="center", anchor_y="center",
            )
            self.txt_team_scores.append(t)
        self.txt_bags_info = []
        for i in range(2):
            t = arcade.Text(
                "", WIDTH - 70, HEIGHT - 160 - i * 18,
                arcade.color.LIGHT_GRAY, 10, anchor_x="center", anchor_y="center",
            )
            self.txt_bags_info.append(t)

        # Bid phase UI
        self.txt_bid_prompt = arcade.Text(
            "Your bid:", WIDTH // 2 - 80, HEIGHT // 2 - 60,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center",
        )
        self.txt_bid_value = arcade.Text(
            "1", WIDTH // 2, HEIGHT // 2 - 60,
            arcade.color.WHITE, 20, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_bid_minus = arcade.Text(
            "-", WIDTH // 2 - 40, HEIGHT // 2 - 60,
            arcade.color.WHITE, 20, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_bid_plus = arcade.Text(
            "+", WIDTH // 2 + 40, HEIGHT // 2 - 60,
            arcade.color.WHITE, 20, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_bid_submit = arcade.Text(
            "Submit Bid", WIDTH // 2, HEIGHT // 2 - 100,
            arcade.color.WHITE, 14, anchor_x="center", anchor_y="center", bold=True,
        )

        # Trick result
        self.txt_trick_result = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 135,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )

        # Round over
        self.txt_round_summary = arcade.Text(
            "Round Over", WIDTH // 2, HEIGHT // 2 + 60,
            arcade.color.WHITE, 20, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_round_details = []
        for i in range(4):
            t = arcade.Text(
                "", WIDTH // 2, HEIGHT // 2 + 20 - i * 22,
                arcade.color.LIGHT_GRAY, 14, anchor_x="center", anchor_y="center",
            )
            self.txt_round_details.append(t)
        self.txt_continue = arcade.Text(
            "Click to continue", WIDTH // 2, HEIGHT // 2 - 80,
            arcade.color.LIGHT_GRAY, 13, anchor_x="center", anchor_y="center",
        )

        # Game over
        self.txt_game_over_msg = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 30,
            arcade.color.WHITE, 40, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_hint = arcade.Text(
            "Click 'New Game' to play again", WIDTH // 2, HEIGHT // 2 - 30,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center",
        )

    # ------------------------------------------------------------------ deal / bid

    def _start_round(self):
        """Deal and start bidding."""
        deck = create_deck(shuffled=True)
        for card in deck:
            card.face_up = True
        self.hands = [deck[i * 13:(i + 1) * 13] for i in range(4)]
        for h in self.hands:
            sort_hand(h, trump_suit="s")
        self.tricks_won = [0, 0, 0, 0]
        self.bids = [None, None, None, None]
        self.current_trick = []
        self.spades_broken = False
        self.ai_timer = 0.0
        self.trick_done_timer = 0.0
        self.round_number += 1

        # Bidding order: left of dealer
        self.bid_order = [(self.dealer + 1 + i) % 4 for i in range(4)]
        self.current_player = self.bid_order[0]
        self.human_bid_value = 1
        self.phase = PHASE_BID
        self._update_phase_text()
        self._update_bid_labels()

    def _submit_bid(self, player, bid_value):
        """Record a player's bid."""
        self.bids[player] = bid_value
        self._update_bid_labels()

        # Check if all bids are in
        if all(b is not None for b in self.bids):
            # Start play: left of dealer leads
            self.trick_leader = (self.dealer + 1) % 4
            self.current_player = self.trick_leader
            self.phase = PHASE_PLAY
            self._update_phase_text()
        else:
            # Advance to next bidder
            bid_idx = self.bid_order.index(player)
            self.current_player = self.bid_order[bid_idx + 1]
            self.ai_timer = 0.0
            self._update_phase_text()

    # ------------------------------------------------------------------ play logic

    def _get_valid_plays_for(self, player):
        """Get valid plays respecting Spades rules."""
        hand = self.hands[player]
        lead_suit = None
        if self.current_trick:
            lead_suit = self.current_trick[0][1].suit

        if lead_suit is None:
            # Leading
            if not self.spades_broken:
                non_spades = [c for c in hand if c.suit != "s"]
                if non_spades:
                    return non_spades
            return list(hand)
        else:
            return get_valid_plays(hand, lead_suit)

    def _play_card(self, player, card):
        """Play a card from player's hand into the current trick."""
        self.hands[player].remove(card)
        self.current_trick.append((player, card))

        # Check if spades broken
        if card.suit == "s" and len(self.current_trick) > 1:
            # Spade played not as lead
            self.spades_broken = True
        elif card.suit == "s" and len(self.current_trick) == 1:
            # Leading spades (only possible if broken or only spades left)
            self.spades_broken = True

        if len(self.current_trick) == 4:
            self._resolve_trick()
        else:
            self.current_player = (self.current_player + 1) % 4
            self.ai_timer = 0.0
            self._update_phase_text()

    def _resolve_trick(self):
        """Determine trick winner."""
        lead_suit = self.current_trick[0][1].suit
        winner = trick_winner(self.current_trick, lead_suit, trump_suit="s")
        self.tricks_won[winner] += 1

        self.txt_trick_result.text = (
            f"{PLAYER_NAMES[winner]} wins the trick! "
            f"(Tricks: {self.tricks_won[winner]})"
        )
        self.phase = PHASE_TRICK_DONE
        self.trick_done_timer = 0.0
        self.trick_leader = winner

    def _finish_trick(self):
        """After trick display, start next trick or end round."""
        self.current_trick = []
        if all(len(h) == 0 for h in self.hands):
            self._end_round()
        else:
            self.current_player = self.trick_leader
            self.phase = PHASE_PLAY
            self.ai_timer = 0.0
            self._update_phase_text()

    def _end_round(self):
        """Score the round by teams."""
        # Team 0: players 0 + 2, Team 1: players 1 + 3
        team_tricks = [
            self.tricks_won[0] + self.tricks_won[2],
            self.tricks_won[1] + self.tricks_won[3],
        ]
        team_bids = [
            self.bids[0] + self.bids[2],
            self.bids[1] + self.bids[3],
        ]

        round_scores = [0, 0]
        round_bags = [0, 0]

        for t in range(2):
            players = [0, 2] if t == 0 else [1, 3]
            # Handle nil bids individually
            nil_bonus = 0
            non_nil_bid = 0
            non_nil_tricks = 0
            has_nil = False

            for p in players:
                if self.bids[p] == 0:
                    has_nil = True
                    if self.tricks_won[p] == 0:
                        nil_bonus += 100
                    else:
                        nil_bonus -= 100
                else:
                    non_nil_bid += self.bids[p]
                    non_nil_tricks += self.tricks_won[p]

            if has_nil and non_nil_bid > 0:
                score, bags = hand_score_spades(non_nil_tricks, non_nil_bid)
                round_scores[t] = score + nil_bonus
                round_bags[t] = bags
            elif has_nil and non_nil_bid == 0:
                # Both players bid nil
                round_scores[t] = nil_bonus
                round_bags[t] = 0
            else:
                score, bags = hand_score_spades(team_tricks[t], team_bids[t])
                round_scores[t] = score
                round_bags[t] = bags

        # Apply bag penalties
        for t in range(2):
            self.team_bags[t] += round_bags[t]
            if self.team_bags[t] >= 10:
                round_scores[t] -= 100
                self.team_bags[t] -= 10

        for t in range(2):
            self.team_scores[t] += round_scores[t]

        # Update display
        self.txt_round_summary.text = f"Round {self.round_number} Over"
        detail_lines = [
            f"Your Team: bid {team_bids[0]}, won {team_tricks[0]} -> {'+' if round_scores[0] >= 0 else ''}{round_scores[0]}",
            f"Opponents: bid {team_bids[1]}, won {team_tricks[1]} -> {'+' if round_scores[1] >= 0 else ''}{round_scores[1]}",
            f"Totals: Your Team {self.team_scores[0]} | Opponents {self.team_scores[1]}",
            f"Bags: Your Team {self.team_bags[0]} | Opponents {self.team_bags[1]}",
        ]
        for i, line in enumerate(detail_lines):
            self.txt_round_details[i].text = line

        self.phase = PHASE_ROUND_OVER
        self._update_score_display()

        # Advance dealer
        self.dealer = (self.dealer + 1) % 4

    def _check_game_over(self):
        """Check if game should end."""
        if self.team_scores[0] >= 500 or self.team_scores[1] >= 500:
            if self.team_scores[0] > self.team_scores[1]:
                self.txt_game_over_msg.text = "Your Team Wins!"
                self.txt_game_over_msg.color = arcade.color.GREEN
            elif self.team_scores[1] > self.team_scores[0]:
                self.txt_game_over_msg.text = "Opponents Win!"
                self.txt_game_over_msg.color = arcade.color.RED
            else:
                self.txt_game_over_msg.text = "Tie Game!"
                self.txt_game_over_msg.color = arcade.color.YELLOW
            self.phase = PHASE_GAME_OVER
            return True
        # Also check if either team is deeply negative and other is at 500
        return False

    # ------------------------------------------------------------------ display helpers

    def _update_phase_text(self):
        if self.phase == PHASE_BID:
            if self.current_player == 0:
                self.txt_phase_info.text = "Your turn to bid"
            else:
                self.txt_phase_info.text = f"{PLAYER_NAMES[self.current_player]} is bidding..."
        elif self.phase == PHASE_PLAY:
            if self.current_player == 0:
                self.txt_phase_info.text = "Your turn - click a card to play"
            else:
                self.txt_phase_info.text = f"{PLAYER_NAMES[self.current_player]} is thinking..."
        else:
            self.txt_phase_info.text = ""

    def _update_bid_labels(self):
        for i in range(4):
            if self.bids[i] is not None:
                bid_str = "Nil" if self.bids[i] == 0 else str(self.bids[i])
                self.txt_bid_labels[i].text = f"Bid: {bid_str}"
            else:
                self.txt_bid_labels[i].text = ""

    def _update_score_display(self):
        for i in range(2):
            self.txt_team_scores[i].text = f"{TEAM_NAMES[i]}: {self.team_scores[i]}"
            self.txt_bags_info[i].text = f"Bags: {self.team_bags[i]}"

    # ------------------------------------------------------------------ helpers

    def _in_rect(self, x, y, cx, cy, w, h):
        return cx - w / 2 <= x <= cx + w / 2 and cy - h / 2 <= y <= cy + h / 2

    def _card_at_pos(self, mx, my):
        """Return index of human hand card at mouse position, or -1."""
        hand = self.hands[0]
        n = len(hand)
        if n == 0:
            return -1
        spacing = min(55, (WIDTH - 200) / max(n, 1))
        start_x = WIDTH / 2 - (n - 1) * spacing / 2
        cy = 70
        for i in range(n - 1, -1, -1):
            cx = start_x + i * spacing
            if abs(mx - cx) <= CARD_WIDTH * 0.45 and abs(my - cy) <= CARD_HEIGHT * 0.45:
                return i
        return -1

    # ------------------------------------------------------------------ update

    def on_update(self, delta_time):
        if self.phase == PHASE_TRICK_DONE:
            self.trick_done_timer += delta_time
            if self.trick_done_timer >= 1.2:
                self._finish_trick()
            return

        if self.phase == PHASE_BID and self.current_player != 0:
            self.ai_timer += delta_time
            if self.ai_timer >= 0.6:
                player = self.current_player
                bid = self.ai[player].choose_bid(self.hands[player], self.bids)
                self._submit_bid(player, bid)
                self.ai_timer = 0.0

        if self.phase == PHASE_PLAY and self.current_player != 0:
            self.ai_timer += delta_time
            if self.ai_timer >= 0.6:
                player = self.current_player
                valid = self._get_valid_plays_for(player)
                card = self.ai[player].choose_play(
                    hand=self.hands[player],
                    valid_plays=valid,
                    current_trick=self.current_trick,
                    spades_broken=self.spades_broken,
                    bids=self.bids,
                    tricks_won=list(self.tricks_won),
                )
                self._play_card(player, card)
                self.ai_timer = 0.0

    # ------------------------------------------------------------------ draw

    def on_draw(self):
        self.clear()
        from renderers import spades_renderer
        spades_renderer.draw(self)

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
            self._new_game()
            return

        # Help
        if self.help_button.hit_test(x, y):
            rules_view = RulesView(
                "Spades", "spades.txt", None, self.menu_view,
                existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        if self.phase == PHASE_BID and self.current_player == 0:
            self._handle_bid_click(x, y)
        elif self.phase == PHASE_PLAY and self.current_player == 0:
            self._handle_play_click(x, y)
        elif self.phase == PHASE_TRICK_DONE:
            self._finish_trick()
        elif self.phase == PHASE_ROUND_OVER:
            if self._check_game_over():
                return
            self._start_round()

    def _handle_bid_click(self, x, y):
        by_val = HEIGHT // 2 - 60
        # Minus button
        if self._in_rect(x, y, WIDTH // 2 - 40, by_val, 32, 32):
            self.human_bid_value = max(0, self.human_bid_value - 1)
            self.txt_bid_value.text = "Nil" if self.human_bid_value == 0 else str(self.human_bid_value)
            return
        # Plus button
        if self._in_rect(x, y, WIDTH // 2 + 40, by_val, 32, 32):
            self.human_bid_value = min(13, self.human_bid_value + 1)
            self.txt_bid_value.text = "Nil" if self.human_bid_value == 0 else str(self.human_bid_value)
            return
        # Submit
        if self._in_rect(x, y, WIDTH // 2, HEIGHT // 2 - 100, 120, 36):
            self._submit_bid(0, self.human_bid_value)

    def _handle_play_click(self, x, y):
        idx = self._card_at_pos(x, y)
        if idx < 0:
            return
        card = self.hands[0][idx]
        valid = self._get_valid_plays_for(0)
        if card in valid:
            self._play_card(0, card)

    def _new_game(self):
        self.team_scores = [0, 0]
        self.team_bags = [0, 0]
        self.dealer = 0
        self.round_number = 0
        self._start_round()
        self._update_score_display()
