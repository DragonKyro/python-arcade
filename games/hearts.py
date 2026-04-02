"""
Hearts card game view using Arcade 3.x APIs.

4 players (1 human + 3 AI). Standard 52-card deck, 13 cards each.
Pass 3 cards (left/right/across/none, rotating). 2 of clubs leads first trick.
Hearts = 1pt each, Queen of Spades = 13pts. Low score wins.
Shoot the moon: one player takes all 26 => 0 for them, 26 for everyone else.
Play to 100.
"""

import arcade
from pages.components import Button
from pages.rules import RulesView
from ai.hearts_ai import HeartsAI
from utils.card import Card, create_deck, CARD_WIDTH, CARD_HEIGHT, RANK_VALUES
from utils.tricks import (
    trick_winner, can_follow_suit, get_valid_plays, sort_hand,
    count_points_hearts,
)
from renderers.hearts_renderer import (
    WIDTH, HEIGHT, BUTTON_W, BUTTON_H,
)

# Game phases
PHASE_DEAL = "deal"
PHASE_PASS = "pass"
PHASE_PLAY = "play"
PHASE_TRICK_DONE = "trick_done"
PHASE_ROUND_OVER = "round_over"
PHASE_GAME_OVER = "game_over"

# Pass directions
PASS_LEFT = 0
PASS_RIGHT = 1
PASS_ACROSS = 2
PASS_NONE = 3
PASS_NAMES = ["Left", "Right", "Across", "No Pass"]

PLAYER_NAMES = ["You", "West (AI)", "North (AI)", "East (AI)"]


class HeartsView(arcade.View):
    """Arcade View for Hearts."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.help_button = Button(
            WIDTH - 145, HEIGHT - 30, 40, 36, "?", color=arcade.color.DARK_SLATE_BLUE
        )

        # Core state
        self.phase = PHASE_DEAL
        self.hands = [[], [], [], []]           # 4 hands of Card objects
        self.tricks_taken = [[], [], [], []]     # cards won per player this round
        self.round_points = [0, 0, 0, 0]        # points this round
        self.total_scores = [0, 0, 0, 0]        # cumulative scores
        self.current_trick = []                  # list of (player_idx, Card)
        self.trick_leader = 0
        self.current_player = 0
        self.hearts_broken = False
        self.first_trick = True

        # Passing
        self.pass_direction = PASS_LEFT
        self.selected_pass_cards = []            # indices in human hand

        # AI
        self.ai = [None, HeartsAI(1), HeartsAI(2), HeartsAI(3)]

        # Timing
        self.ai_timer = 0.0
        self.trick_done_timer = 0.0

        # Round history for score display
        self.round_history = []  # list of [p0, p1, p2, p3] per round

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
            "Hearts", WIDTH // 2, HEIGHT - 30,
            arcade.color.WHITE, 22, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_phase_info = arcade.Text(
            "", WIDTH // 2, HEIGHT - 65,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center",
        )
        self.txt_turn_info = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 140,
            arcade.color.YELLOW, 14, anchor_x="center", anchor_y="center",
        )
        # Player name labels (bottom, left, top, right)
        self.txt_player_names = []
        positions = [
            (WIDTH // 2, 155),      # bottom (human)
            (65, HEIGHT // 2),      # left
            (WIDTH // 2, HEIGHT - 95),  # top
            (WIDTH - 65, HEIGHT // 2),  # right
        ]
        for i, (px, py) in enumerate(positions):
            t = arcade.Text(
                PLAYER_NAMES[i], px, py, arcade.color.WHITE, 13,
                anchor_x="center", anchor_y="center", bold=True,
            )
            self.txt_player_names.append(t)

        # Score texts (right side panel)
        self.txt_score_header = arcade.Text(
            "Scores", WIDTH - 70, HEIGHT - 100,
            arcade.color.WHITE, 14, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_score_lines = []
        for i in range(4):
            t = arcade.Text(
                "", WIDTH - 70, HEIGHT - 120 - i * 18,
                arcade.color.LIGHT_GRAY, 11, anchor_x="center", anchor_y="center",
            )
            self.txt_score_lines.append(t)

        # Pass phase prompt
        self.txt_pass_prompt = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 20,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center",
        )
        self.txt_pass_btn = arcade.Text(
            "Pass Cards", WIDTH // 2, HEIGHT // 2 - 25,
            arcade.color.WHITE, 14, anchor_x="center", anchor_y="center", bold=True,
        )

        # Trick done / round over messages
        self.txt_trick_result = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_round_summary = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 30,
            arcade.color.WHITE, 18, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_round_details = []
        for i in range(4):
            t = arcade.Text(
                "", WIDTH // 2, HEIGHT // 2 - 5 - i * 22,
                arcade.color.LIGHT_GRAY, 14, anchor_x="center", anchor_y="center",
            )
            self.txt_round_details.append(t)
        self.txt_continue = arcade.Text(
            "Click to continue", WIDTH // 2, HEIGHT // 2 - 100,
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

    # ------------------------------------------------------------------ deal / pass

    def _start_round(self):
        """Deal cards and enter pass or play phase."""
        deck = create_deck(shuffled=True)
        for card in deck:
            card.face_up = True
        self.hands = [deck[i * 13:(i + 1) * 13] for i in range(4)]
        for h in self.hands:
            sort_hand(h)
        self.tricks_taken = [[], [], [], []]
        self.round_points = [0, 0, 0, 0]
        self.current_trick = []
        self.hearts_broken = False
        self.first_trick = True
        self.selected_pass_cards = []
        self.ai_timer = 0.0
        self.trick_done_timer = 0.0

        if self.pass_direction == PASS_NONE:
            self.phase = PHASE_PLAY
            self._find_two_of_clubs_leader()
            self._update_phase_text()
        else:
            self.phase = PHASE_PASS
            self._update_phase_text()

    def _pass_target(self, player, direction):
        """Return the target player index for a given pass direction."""
        if direction == PASS_LEFT:
            return (player + 1) % 4
        elif direction == PASS_RIGHT:
            return (player - 1) % 4
        elif direction == PASS_ACROSS:
            return (player + 2) % 4
        return player

    def _execute_pass(self):
        """Perform the card pass for all players."""
        pass_cards = [[] for _ in range(4)]

        # Human picks
        human_cards = [self.hands[0][i] for i in sorted(self.selected_pass_cards, reverse=True)]
        for i in sorted(self.selected_pass_cards, reverse=True):
            self.hands[0].pop(i)
        pass_cards[0] = human_cards

        # AI picks
        for p in range(1, 4):
            picks = self.ai[p].choose_pass_cards(self.hands[p], self.pass_direction)
            pass_cards[p] = picks
            for c in picks:
                self.hands[p].remove(c)

        # Distribute
        for p in range(4):
            target = self._pass_target(p, self.pass_direction)
            self.hands[target].extend(pass_cards[p])

        for h in self.hands:
            sort_hand(h)

        self.selected_pass_cards = []
        self.phase = PHASE_PLAY
        self._find_two_of_clubs_leader()
        self._update_phase_text()

    def _find_two_of_clubs_leader(self):
        """Find who has the 2 of clubs and make them lead."""
        for p in range(4):
            for card in self.hands[p]:
                if card.rank == "2" and card.suit == "c":
                    self.trick_leader = p
                    self.current_player = p
                    return

    # ------------------------------------------------------------------ play logic

    def _get_valid_plays_for(self, player):
        """Get valid plays respecting Hearts rules."""
        hand = self.hands[player]
        lead_suit = None
        if self.current_trick:
            lead_suit = self.current_trick[0][1].suit

        if lead_suit is None:
            # Leading
            if self.first_trick:
                # Must lead 2 of clubs
                return [c for c in hand if c.rank == "2" and c.suit == "c"]
            if not self.hearts_broken:
                non_hearts = [c for c in hand if c.suit != "h"]
                if non_hearts:
                    return non_hearts
            return list(hand)
        else:
            # Following
            valid = get_valid_plays(hand, lead_suit)
            if self.first_trick:
                # Can't play hearts or QS on first trick (unless no choice)
                filtered = [c for c in valid
                            if not (c.suit == "h" or (c.suit == "s" and c.rank == "q"))]
                if filtered:
                    return filtered
            return valid

    def _play_card(self, player, card):
        """Play a card from a player's hand into the current trick."""
        self.hands[player].remove(card)
        self.current_trick.append((player, card))

        if card.suit == "h":
            self.hearts_broken = True
        if card.suit == "s" and card.rank == "q":
            self.hearts_broken = True

        if len(self.current_trick) == 4:
            self._resolve_trick()
        else:
            self.current_player = (self.current_player + 1) % 4
            self.ai_timer = 0.0
            self._update_phase_text()

    def _resolve_trick(self):
        """Determine trick winner and collect cards."""
        lead_suit = self.current_trick[0][1].suit
        winner = trick_winner(self.current_trick, lead_suit, trump_suit=None)
        cards_won = [c for _, c in self.current_trick]
        self.tricks_taken[winner].extend(cards_won)
        pts = count_points_hearts(cards_won)
        self.round_points[winner] += pts

        self.txt_trick_result.text = f"{PLAYER_NAMES[winner]} wins the trick! (+{pts} pts)"
        self.phase = PHASE_TRICK_DONE
        self.trick_done_timer = 0.0
        self.trick_leader = winner
        self.first_trick = False

    def _finish_trick(self):
        """After trick display, start next trick or end round."""
        self.current_trick = []

        # Check if round is over (all cards played)
        if all(len(h) == 0 for h in self.hands):
            self._end_round()
        else:
            self.current_player = self.trick_leader
            self.phase = PHASE_PLAY
            self.ai_timer = 0.0
            self._update_phase_text()

    def _end_round(self):
        """Score the round, check shoot the moon, check game over."""
        # Shoot the moon
        moon_shooter = -1
        for p in range(4):
            if self.round_points[p] == 26:
                moon_shooter = p
                break

        if moon_shooter >= 0:
            for p in range(4):
                if p == moon_shooter:
                    self.round_points[p] = 0
                else:
                    self.round_points[p] = 26

        for p in range(4):
            self.total_scores[p] += self.round_points[p]

        self.round_history.append(list(self.round_points))

        # Update round summary
        if moon_shooter >= 0:
            self.txt_round_summary.text = f"{PLAYER_NAMES[moon_shooter]} shot the moon!"
            self.txt_round_summary.color = arcade.color.YELLOW
        else:
            self.txt_round_summary.text = "Round Over"
            self.txt_round_summary.color = arcade.color.WHITE

        for i in range(4):
            self.txt_round_details[i].text = (
                f"{PLAYER_NAMES[i]}: +{self.round_points[i]}  "
                f"(Total: {self.total_scores[i]})"
            )

        # Check game over
        if max(self.total_scores) >= 100:
            self.phase = PHASE_ROUND_OVER  # show summary first
        else:
            self.phase = PHASE_ROUND_OVER

        self._update_score_display()

    def _check_game_over(self):
        """Check if the game should end after round summary is shown."""
        if max(self.total_scores) >= 100:
            winner = min(range(4), key=lambda p: self.total_scores[p])
            if winner == 0:
                self.txt_game_over_msg.text = "You Win!"
                self.txt_game_over_msg.color = arcade.color.GREEN
            else:
                self.txt_game_over_msg.text = f"{PLAYER_NAMES[winner]} Wins!"
                self.txt_game_over_msg.color = arcade.color.RED
            self.phase = PHASE_GAME_OVER
            return True
        return False

    # ------------------------------------------------------------------ display helpers

    def _update_phase_text(self):
        if self.phase == PHASE_PASS:
            self.txt_phase_info.text = f"Pass 3 cards {PASS_NAMES[self.pass_direction]}"
            self.txt_turn_info.text = "Select 3 cards to pass, then click Pass Cards"
        elif self.phase == PHASE_PLAY:
            if self.current_player == 0:
                self.txt_phase_info.text = "Your turn - click a card to play"
                self.txt_turn_info.text = ""
            else:
                self.txt_phase_info.text = f"{PLAYER_NAMES[self.current_player]} is thinking..."
                self.txt_turn_info.text = ""
        else:
            self.txt_phase_info.text = ""
            self.txt_turn_info.text = ""

    def _update_score_display(self):
        for i in range(4):
            short = PLAYER_NAMES[i][:4] if i > 0 else "You"
            self.txt_score_lines[i].text = f"{short}: {self.total_scores[i]}"

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
        # Check from right to left (topmost card)
        for i in range(n - 1, -1, -1):
            cx = start_x + i * spacing
            if abs(mx - cx) <= CARD_WIDTH * 0.45 / 1 and abs(my - cy) <= CARD_HEIGHT * 0.45 / 1:
                return i
        return -1

    # ------------------------------------------------------------------ update

    def on_update(self, delta_time):
        if self.phase == PHASE_TRICK_DONE:
            self.trick_done_timer += delta_time
            if self.trick_done_timer >= 1.2:
                self._finish_trick()
            return

        if self.phase == PHASE_PLAY and self.current_player != 0:
            self.ai_timer += delta_time
            if self.ai_timer >= 0.6:
                player = self.current_player
                valid = self._get_valid_plays_for(player)
                card = self.ai[player].choose_play(
                    hand=self.hands[player],
                    valid_plays=valid,
                    current_trick=self.current_trick,
                    hearts_broken=self.hearts_broken,
                    first_trick=self.first_trick,
                    round_points=list(self.round_points),
                    tricks_taken=self.tricks_taken,
                )
                self._play_card(player, card)
                self.ai_timer = 0.0

    # ------------------------------------------------------------------ draw

    def on_draw(self):
        self.clear()
        from renderers import hearts_renderer
        hearts_renderer.draw(self)

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
                "Hearts", "hearts.txt", None, self.menu_view,
                existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        if self.phase == PHASE_PASS:
            self._handle_pass_click(x, y)
        elif self.phase == PHASE_PLAY and self.current_player == 0:
            self._handle_play_click(x, y)
        elif self.phase == PHASE_TRICK_DONE:
            self._finish_trick()
        elif self.phase == PHASE_ROUND_OVER:
            if self._check_game_over():
                return
            # Advance pass direction and start new round
            self.pass_direction = (self.pass_direction + 1) % 4
            self._start_round()

    def _handle_pass_click(self, x, y):
        # Check pass button
        btn_x, btn_y = WIDTH // 2, HEIGHT // 2 - 25
        if len(self.selected_pass_cards) == 3 and self._in_rect(x, y, btn_x, btn_y, 130, 36):
            self._execute_pass()
            return

        # Toggle card selection
        idx = self._card_at_pos(x, y)
        if idx >= 0:
            if idx in self.selected_pass_cards:
                self.selected_pass_cards.remove(idx)
            elif len(self.selected_pass_cards) < 3:
                self.selected_pass_cards.append(idx)

    def _handle_play_click(self, x, y):
        idx = self._card_at_pos(x, y)
        if idx < 0:
            return
        card = self.hands[0][idx]
        valid = self._get_valid_plays_for(0)
        if card in valid:
            self._play_card(0, card)

    def _new_game(self):
        self.total_scores = [0, 0, 0, 0]
        self.round_history = []
        self.pass_direction = PASS_LEFT
        self._start_round()
        self._update_score_display()
