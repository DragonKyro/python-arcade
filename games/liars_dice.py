"""
Liar's Dice game view using Arcade 3.x APIs.
"""

import random

import arcade
from pages.components import Button
from pages.rules import RulesView
from ai.liars_dice_ai import LiarsDiceAI
from renderers.liars_dice_renderer import (
    WIDTH, HEIGHT,
    BUTTON_W, BUTTON_H,
    BID_BUTTON_W, BID_BUTTON_H,
    LIAR_BUTTON_W, LIAR_BUTTON_H,
    SELECTOR_BTN_SIZE,
    AI_POSITIONS,
)

# Game phases
PHASE_SETUP = "setup"
PHASE_PLAYING = "playing"
PHASE_RESOLUTION = "resolution"
PHASE_ROUND_OVER = "round_over"
PHASE_GAME_OVER = "game_over"

# Difficulty per AI index (cycles through)
AI_DIFFICULTIES = ["easy", "medium", "hard", "medium"]

# Starting dice per player
STARTING_DICE = 5


class LiarsDiceView(arcade.View):
    """Arcade View for Liar's Dice."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.help_button = Button(
            WIDTH - 145, HEIGHT - 30, 40, 36, "?", color=arcade.color.DARK_SLATE_BLUE
        )

        # Setup state
        self.phase = PHASE_SETUP
        self.pending_num_ai = 0

        # Game state (initialized in _start_game)
        self.players = []         # list of dicts: {"name", "dice", "ai"}
        self.current_player_index = 0
        self.current_bid = None   # (quantity, face) or None
        self.bid_history = []     # list of (player_name, quantity, face)
        self.round_starter = 0

        # Human bid selectors
        self.selected_qty = 1
        self.selected_face = 2

        # AI thinking timer
        self.ai_timer = 0.0
        self.ai_acting = False

        # Resolution state
        self.resolution_caller = -1
        self.resolution_bidder = -1
        self.resolution_actual = 0
        self.resolution_bid_qty = 0
        self.resolution_bid_face = 0
        self.resolution_liar_correct = False
        self.resolution_timer = 0.0

        # Round-over state
        self.round_over_msg = ""
        self.round_over_timer = 0.0

        # Setup buttons (positions for 1-4 AI opponents)
        self.setup_buttons = []
        for i in range(4):
            bx = WIDTH // 2 - 120 + i * 80
            by = HEIGHT // 2 + 20
            self.setup_buttons.append((bx, by, 60, 44))

        self._create_texts()

    # ------------------------------------------------------------------ texts

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        # Top bar buttons
        self.txt_btn_back = arcade.Text(
            "Back", 60, HEIGHT - 30, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_btn_new_game = arcade.Text(
            "New Game", WIDTH - 70, HEIGHT - 30, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_title = arcade.Text(
            "Liar's Dice", WIDTH // 2, HEIGHT - 30,
            arcade.color.WHITE, 22, anchor_x="center", anchor_y="center", bold=True,
        )

        # Setup phase
        self.txt_setup_prompt = arcade.Text(
            "Choose number of AI opponents:", WIDTH // 2, HEIGHT // 2 + 80,
            arcade.color.WHITE, 20, anchor_x="center", anchor_y="center",
        )
        self.txt_setup_btn_labels = []
        for i in range(4):
            bx = WIDTH // 2 - 120 + i * 80
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

        # Turn indicator
        self.txt_turn = arcade.Text(
            "", WIDTH // 2, HEIGHT - 70,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center",
        )

        # Player names and dice counts (index 0 = human, 1-4 = AI)
        self.txt_player_names = []
        self.txt_player_dice_counts = []
        for i in range(5):
            self.txt_player_names.append(
                arcade.Text(
                    "", 0, 0, arcade.color.WHITE, 14,
                    anchor_x="center", anchor_y="center", bold=True,
                )
            )
            self.txt_player_dice_counts.append(
                arcade.Text(
                    "", 0, 0, arcade.color.LIGHT_GRAY, 12,
                    anchor_x="center", anchor_y="center",
                )
            )

        # Current bid display
        self.txt_current_bid = arcade.Text(
            "No bid yet", WIDTH // 2, HEIGHT // 2 + 40,
            arcade.color.WHITE, 18, anchor_x="center", anchor_y="center", bold=True,
        )

        # Bid history
        self.txt_history_title = arcade.Text(
            "Bid History", WIDTH - 90, HEIGHT // 2 + 10,
            arcade.color.LIGHT_GRAY, 13, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_history_lines = []
        for i in range(6):
            self.txt_history_lines.append(
                arcade.Text(
                    "", WIDTH - 90, HEIGHT // 2 - 10 - i * 18,
                    arcade.color.LIGHT_GRAY, 11, anchor_x="center", anchor_y="center",
                )
            )

        # Bid controls
        base_y = 170
        self.txt_qty_label = arcade.Text(
            "Qty:", WIDTH // 2 - 155, base_y,
            arcade.color.WHITE, 14, anchor_x="center", anchor_y="center",
        )
        self.txt_qty_minus = arcade.Text(
            "-", WIDTH // 2 - 120, base_y,
            arcade.color.WHITE, 18, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_qty_value = arcade.Text(
            "1", WIDTH // 2 - 75, base_y,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_qty_plus = arcade.Text(
            "+", WIDTH // 2 - 30, base_y,
            arcade.color.WHITE, 18, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_face_label = arcade.Text(
            "Face:", WIDTH // 2 + 20, base_y,
            arcade.color.WHITE, 14, anchor_x="center", anchor_y="center",
        )
        self.txt_face_minus = arcade.Text(
            "-", WIDTH // 2 + 50, base_y,
            arcade.color.WHITE, 18, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_face_value = arcade.Text(
            "2", WIDTH // 2 + 95, base_y,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_face_plus = arcade.Text(
            "+", WIDTH // 2 + 140, base_y,
            arcade.color.WHITE, 18, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_bid_btn = arcade.Text(
            "Bid", WIDTH // 2 - 60, base_y - 45,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_liar_btn = arcade.Text(
            "Liar!", WIDTH // 2 + 60, base_y - 45,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )

        # Resolution texts
        self.txt_resolution_title = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 60,
            arcade.color.YELLOW, 20, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_resolution_detail = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 20,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center",
        )
        self.txt_resolution_result = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 - 20,
            arcade.color.WHITE, 18, anchor_x="center", anchor_y="center", bold=True,
        )

        # Round over texts
        self.txt_round_over = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 20,
            arcade.color.WHITE, 18, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_round_continue = arcade.Text(
            "Click to continue", WIDTH // 2, HEIGHT // 2 - 20,
            arcade.color.LIGHT_GRAY, 14, anchor_x="center", anchor_y="center",
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

    # ------------------------------------------------------------------ game setup

    def _start_game(self):
        """Initialize game with the selected number of AI opponents."""
        num_ai = self.pending_num_ai
        self.players = []

        # Human player (index 0)
        self.players.append({
            "name": "You",
            "dice": [],
            "ai": None,
        })
        self.txt_player_names[0].text = "You"

        # AI players
        for i in range(num_ai):
            diff = AI_DIFFICULTIES[i % len(AI_DIFFICULTIES)]
            name = f"AI {i + 1} ({diff.title()})"
            self.players.append({
                "name": name,
                "dice": [],
                "ai": LiarsDiceAI(difficulty=diff),
            })
            self.txt_player_names[i + 1].text = name

        self._start_new_round()

    def _start_new_round(self):
        """Deal dice to all active players and begin a new round."""
        for player in self.players:
            num_dice = len(player["dice"])
            if num_dice == 0 and self.phase == PHASE_SETUP:
                num_dice = STARTING_DICE
            if num_dice > 0:
                player["dice"] = [random.randint(1, 6) for _ in range(num_dice)]

        # On first round, give everyone starting dice
        if self.phase == PHASE_SETUP:
            for player in self.players:
                player["dice"] = [random.randint(1, 6) for _ in range(STARTING_DICE)]

        self.current_bid = None
        self.bid_history = []
        self.phase = PHASE_PLAYING
        self.ai_timer = 0.0
        self.ai_acting = False

        # Find a valid starter
        self._advance_to_valid_player(self.round_starter)
        self.selected_qty = 1
        self.selected_face = 2
        self._update_turn_text()
        self._update_bid_display()
        self._update_history_display()

    # ------------------------------------------------------------------ helpers

    def _active_players(self):
        """Return list of indices of players with dice remaining."""
        return [i for i, p in enumerate(self.players) if len(p["dice"]) > 0]

    def _total_dice(self):
        """Total dice in play."""
        return sum(len(p["dice"]) for p in self.players)

    def _next_active_player(self, idx):
        """Return the index of the next active player after idx."""
        n = len(self.players)
        for offset in range(1, n + 1):
            candidate = (idx + offset) % n
            if len(self.players[candidate]["dice"]) > 0:
                return candidate
        return idx

    def _advance_to_valid_player(self, start_idx):
        """Set current_player_index to start_idx if active, otherwise next active."""
        if len(self.players[start_idx]["dice"]) > 0:
            self.current_player_index = start_idx
        else:
            self.current_player_index = self._next_active_player(start_idx)

    def _update_turn_text(self):
        if self.phase != PHASE_PLAYING:
            self.txt_turn.text = ""
            return
        name = self.players[self.current_player_index]["name"]
        if self.current_player_index == 0:
            self.txt_turn.text = "Your turn - place a bid or call Liar!"
            self.txt_turn.color = arcade.color.WHITE
        else:
            self.txt_turn.text = f"{name} is thinking..."
            self.txt_turn.color = arcade.color.YELLOW

    def _update_bid_display(self):
        if self.current_bid is None:
            self.txt_current_bid.text = "No bid yet"
            self.txt_current_bid.color = arcade.color.WHITE
        else:
            q, f = self.current_bid
            self.txt_current_bid.text = f"Current Bid: {q} x {f}'s"
            self.txt_current_bid.color = arcade.color.YELLOW

    def _update_history_display(self):
        # Show last 6 bids
        recent = self.bid_history[-6:]
        for i, txt in enumerate(self.txt_history_lines):
            if i < len(recent):
                name, q, f = recent[i]
                txt.text = f"{name}: {q}x{f}'s"
            else:
                txt.text = ""

    def _is_valid_bid(self, qty, face):
        """Check if (qty, face) is a valid raise over current_bid."""
        if self.current_bid is None:
            return qty >= 1 and 1 <= face <= 6
        cur_qty, cur_face = self.current_bid
        # Valid: higher quantity (any face), or same quantity with higher face
        if qty > cur_qty:
            return True
        if qty == cur_qty and face > cur_face:
            return True
        return False

    def can_human_bid(self):
        """Check if the currently selected qty/face is a valid bid."""
        return self._is_valid_bid(self.selected_qty, self.selected_face)

    def _place_bid(self, player_idx, qty, face):
        """Place a bid for the given player."""
        self.current_bid = (qty, face)
        name = self.players[player_idx]["name"]
        self.bid_history.append((name, qty, face))
        self._update_bid_display()
        self._update_history_display()

        # Advance to next player
        self.current_player_index = self._next_active_player(player_idx)
        self.ai_timer = 0.0
        self.ai_acting = False
        self._update_turn_text()

    def _call_liar(self, caller_idx):
        """Handle a player calling liar."""
        if self.current_bid is None:
            return

        bid_qty, bid_face = self.current_bid

        # Find who made the last bid (the player before the caller in active order)
        # It is the previous active player
        bidder_idx = self._prev_active_player(caller_idx)

        # Count all dice matching the bid face (1s are wild)
        actual_count = 0
        for p in self.players:
            for d in p["dice"]:
                if d == bid_face or (d == 1 and bid_face != 1):
                    actual_count += 1

        self.resolution_caller = caller_idx
        self.resolution_bidder = bidder_idx
        self.resolution_actual = actual_count
        self.resolution_bid_qty = bid_qty
        self.resolution_bid_face = bid_face
        self.resolution_liar_correct = actual_count < bid_qty
        self.resolution_timer = 0.0
        self.phase = PHASE_RESOLUTION

        # Update resolution texts
        caller_name = self.players[caller_idx]["name"]
        bidder_name = self.players[bidder_idx]["name"]
        self.txt_resolution_title.text = f"{caller_name} calls LIAR on {bidder_name}!"
        self.txt_resolution_detail.text = (
            f"Bid: {bid_qty} x {bid_face}'s  |  Actual: {actual_count} x {bid_face}'s"
        )

        if self.resolution_liar_correct:
            # Bidder loses a die
            loser = bidder_idx
            self.txt_resolution_result.text = f"Liar call correct! {bidder_name} loses a die."
            self.txt_resolution_result.color = arcade.color.GREEN
        else:
            # Caller loses a die
            loser = caller_idx
            self.txt_resolution_result.text = f"Bid was valid! {caller_name} loses a die."
            self.txt_resolution_result.color = arcade.color.RED

        # Remove a die from the loser
        if len(self.players[loser]["dice"]) > 0:
            self.players[loser]["dice"].pop()

        self.txt_turn.text = ""

    def _prev_active_player(self, idx):
        """Return the index of the previous active player before idx."""
        n = len(self.players)
        for offset in range(1, n + 1):
            candidate = (idx - offset) % n
            if len(self.players[candidate]["dice"]) > 0:
                return candidate
        return idx

    def _finish_resolution(self):
        """After resolution display, check for game over or start new round."""
        active = self._active_players()
        if len(active) <= 1:
            self.phase = PHASE_GAME_OVER
            if len(active) == 1:
                winner_name = self.players[active[0]]["name"]
                if active[0] == 0:
                    self.txt_game_over_msg.text = "You Win!"
                    self.txt_game_over_msg.color = arcade.color.GREEN
                else:
                    self.txt_game_over_msg.text = f"{winner_name} Wins!"
                    self.txt_game_over_msg.color = arcade.color.RED
            else:
                self.txt_game_over_msg.text = "Draw!"
                self.txt_game_over_msg.color = arcade.color.YELLOW
            return

        # Determine who starts the next round (loser of the call)
        if self.resolution_liar_correct:
            loser = self.resolution_bidder
        else:
            loser = self.resolution_caller

        # If the loser is eliminated, the next active player starts
        if len(self.players[loser]["dice"]) > 0:
            self.round_starter = loser
        else:
            self.round_starter = self._next_active_player(loser)

        # Show round-over briefly
        loser_name = self.players[loser]["name"]
        remaining = len(self.players[loser]["dice"])
        if remaining > 0:
            self.round_over_msg = f"{loser_name} now has {remaining} dice. New round!"
        else:
            self.round_over_msg = f"{loser_name} is eliminated!"
        self.txt_round_over.text = self.round_over_msg
        self.phase = PHASE_ROUND_OVER
        self.round_over_timer = 0.0

    # ------------------------------------------------------------------ in_rect

    def _in_rect(self, x, y, cx, cy, w, h):
        return cx - w / 2 <= x <= cx + w / 2 and cy - h / 2 <= y <= cy + h / 2

    # ------------------------------------------------------------------ update

    def on_update(self, delta_time):
        if self.phase == PHASE_RESOLUTION:
            self.resolution_timer += delta_time
            if self.resolution_timer >= 3.0:
                self._finish_resolution()
            return

        if self.phase == PHASE_ROUND_OVER:
            self.round_over_timer += delta_time
            return

        if self.phase != PHASE_PLAYING:
            return

        # AI turn
        if self.current_player_index != 0:
            self.ai_timer += delta_time
            if self.ai_timer >= 1.0 and not self.ai_acting:
                self.ai_acting = True
                player = self.players[self.current_player_index]
                ai = player["ai"]
                if ai is None:
                    return

                action = ai.decide(
                    own_dice=player["dice"],
                    num_total_dice=self._total_dice(),
                    current_bid=self.current_bid,
                    num_players_remaining=len(self._active_players()),
                )

                if action[0] == "liar" and self.current_bid is not None:
                    self._call_liar(self.current_player_index)
                elif action[0] == "bid":
                    _, qty, face = action
                    # Ensure the AI's bid is actually valid
                    if not self._is_valid_bid(qty, face):
                        # Fallback: make minimum valid raise
                        qty, face = self._min_valid_bid()
                    self._place_bid(self.current_player_index, qty, face)
                else:
                    # Fallback for edge cases
                    if self.current_bid is not None:
                        self._call_liar(self.current_player_index)
                    else:
                        self._place_bid(self.current_player_index, 1, 2)

        # Update selector display
        self.txt_qty_value.text = str(self.selected_qty)
        self.txt_face_value.text = str(self.selected_face)

    def _min_valid_bid(self):
        """Return the minimum valid bid above the current bid."""
        if self.current_bid is None:
            return (1, 2)
        cur_qty, cur_face = self.current_bid
        if cur_face < 6:
            return (cur_qty, cur_face + 1)
        return (cur_qty + 1, 1)

    # ------------------------------------------------------------------ draw

    def on_draw(self):
        self.clear()
        from renderers import liars_dice_renderer
        liars_dice_renderer.draw(self)

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
                "Liar's Dice", "liars_dice.txt", None, self.menu_view,
                existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        # Phase-specific input
        if self.phase == PHASE_SETUP:
            self._handle_setup_click(x, y)
        elif self.phase == PHASE_PLAYING:
            self._handle_playing_click(x, y)
        elif self.phase == PHASE_RESOLUTION:
            # Click to skip resolution wait
            self._finish_resolution()
        elif self.phase == PHASE_ROUND_OVER:
            self._start_new_round()

    def _handle_setup_click(self, x, y):
        # Check AI count buttons
        for i, (bx, by, bw, bh) in enumerate(self.setup_buttons):
            if self._in_rect(x, y, bx, by, bw, bh):
                self.pending_num_ai = i + 1
                return

        # Start button
        if self.pending_num_ai > 0:
            sx, sy = WIDTH // 2, HEIGHT // 2 - 60
            if self._in_rect(x, y, sx, sy, 140, 44):
                self._start_game()
                return

    def _handle_playing_click(self, x, y):
        if self.current_player_index != 0:
            return  # Not the human's turn

        base_y = 170

        # Quantity minus
        qm_x, qm_y = WIDTH // 2 - 120, base_y
        if self._in_rect(x, y, qm_x, qm_y, SELECTOR_BTN_SIZE, SELECTOR_BTN_SIZE):
            self.selected_qty = max(1, self.selected_qty - 1)
            return

        # Quantity plus
        qp_x, qp_y = WIDTH // 2 - 30, base_y
        if self._in_rect(x, y, qp_x, qp_y, SELECTOR_BTN_SIZE, SELECTOR_BTN_SIZE):
            self.selected_qty = min(self._total_dice(), self.selected_qty + 1)
            return

        # Face minus
        fm_x, fm_y = WIDTH // 2 + 50, base_y
        if self._in_rect(x, y, fm_x, fm_y, SELECTOR_BTN_SIZE, SELECTOR_BTN_SIZE):
            self.selected_face = max(1, self.selected_face - 1)
            return

        # Face plus
        fp_x, fp_y = WIDTH // 2 + 140, base_y
        if self._in_rect(x, y, fp_x, fp_y, SELECTOR_BTN_SIZE, SELECTOR_BTN_SIZE):
            self.selected_face = min(6, self.selected_face + 1)
            return

        # Bid button
        bid_x, bid_y = WIDTH // 2 - 60, base_y - 45
        if self._in_rect(x, y, bid_x, bid_y, BID_BUTTON_W, BID_BUTTON_H):
            if self.can_human_bid():
                self._place_bid(0, self.selected_qty, self.selected_face)
            return

        # Liar button
        if self.current_bid is not None:
            liar_x, liar_y = WIDTH // 2 + 60, base_y - 45
            if self._in_rect(x, y, liar_x, liar_y, LIAR_BUTTON_W, LIAR_BUTTON_H):
                self._call_liar(0)
                return
