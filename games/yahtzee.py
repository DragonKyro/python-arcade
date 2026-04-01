"""
Yahtzee game view using Arcade 3.x APIs.
"""

import random

import arcade
from pages.components import Button
from pages.rules import RulesView
from ai.yahtzee_ai import YahtzeeAI, calculate_score, CATEGORIES, UPPER_CATEGORIES
from renderers.yahtzee_renderer import (
    WIDTH, HEIGHT,
    BUTTON_W, BUTTON_H,
    ROLL_BTN_W, ROLL_BTN_H,
    SCORE_BTN_W, SCORE_BTN_H,
    SETUP_BTN_W, SETUP_BTN_H,
    DICE_AREA_Y, DICE_START_X,
    DIE_SIZE, DIE_GAP,
    CARD_LEFT, CARD_TOP, CARD_ROW_H, CARD_LABEL_W, CARD_COL_W, CARD_HEADER_H,
    CATEGORY_NAMES,
)

# Phases
PHASE_SETUP = "setup"
PHASE_ROLLING = "rolling"
PHASE_SCORING = "scoring"
PHASE_AI_TURN = "ai_turn"
PHASE_GAME_OVER = "game_over"

TOTAL_ROUNDS = 13
AI_DELAY = 0.8


class YahtzeeView(arcade.View):
    """Arcade View for Yahtzee."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.help_button = Button(
            WIDTH - 145, HEIGHT - 30, 40, 36, "?", color=arcade.color.DARK_SLATE_BLUE
        )

        # Setup state
        self.phase = PHASE_SETUP
        self.pending_num_players = 0

        # Game state
        self.players = []
        self.current_player_index = 0
        self.current_round = 1
        self.dice = [1, 1, 1, 1, 1]
        self.kept_indices = set()
        self.roll_number = 0  # 0=not rolled yet, 1-3
        self.selected_category = None

        # AI state
        self.ai_timer = 0.0
        self.ai_step = 0  # 0=roll, 1=keep/reroll, 2=keep/reroll2, 3=score

        self._create_texts()

    # ------------------------------------------------------------------ texts

    def _create_texts(self):
        """Create reusable arcade.Text objects."""
        # Top bar
        self.txt_btn_back = arcade.Text(
            "Back", 60, HEIGHT - 30, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_btn_new_game = arcade.Text(
            "New Game", WIDTH - 70, HEIGHT - 30, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_title = arcade.Text(
            "Yahtzee", WIDTH // 2, HEIGHT - 30,
            arcade.color.WHITE, 22, anchor_x="center", anchor_y="center", bold=True,
        )

        # Setup phase
        self.txt_setup_prompt = arcade.Text(
            "Choose number of players (1 human + AI):", WIDTH // 2, HEIGHT // 2 + 80,
            arcade.color.WHITE, 18, anchor_x="center", anchor_y="center",
        )
        self.txt_setup_btn_labels = []
        for i in range(4):
            bx = WIDTH // 2 - 120 + i * 80
            by = HEIGHT // 2 + 20
            label = f"{i + 1}P" if i == 0 else f"1+{i}AI"
            self.txt_setup_btn_labels.append(
                arcade.Text(
                    label, bx, by, arcade.color.WHITE, 14,
                    anchor_x="center", anchor_y="center", bold=True,
                )
            )
        self.txt_start_btn = arcade.Text(
            "Start Game", WIDTH // 2, HEIGHT // 2 - 60,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )

        # Info bar
        self.txt_round_info = arcade.Text(
            "", WIDTH // 2, HEIGHT - 70,
            arcade.color.WHITE, 14, anchor_x="center", anchor_y="center",
        )
        self.txt_current_player = arcade.Text(
            "", WIDTH // 2, HEIGHT - 90,
            arcade.color.YELLOW, 16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_rolls_left = arcade.Text(
            "", 660, DICE_AREA_Y + 50,
            arcade.color.LIGHT_GRAY, 12, anchor_x="center", anchor_y="center",
        )

        # Dice "kept" labels
        self.txt_kept_labels = []
        for i in range(5):
            self.txt_kept_labels.append(
                arcade.Text(
                    "KEEP", 0, 0, arcade.color.LIGHT_BLUE, 10,
                    anchor_x="center", anchor_y="center",
                )
            )

        # Roll / Score buttons
        self.txt_roll_btn = arcade.Text(
            "Roll", 0, 0, arcade.color.WHITE, 16,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_score_btn = arcade.Text(
            "Score", 0, 0, arcade.color.WHITE, 16,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Scorecard texts
        self.txt_card_header = arcade.Text(
            "Category", 0, 0, arcade.color.WHITE, 12,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_player_headers = []
        for i in range(4):
            self.txt_player_headers.append(
                arcade.Text(
                    "", 0, 0, arcade.color.WHITE, 11,
                    anchor_x="center", anchor_y="center", bold=True,
                )
            )

        self.txt_cat_labels = []
        for _ in CATEGORIES:
            self.txt_cat_labels.append(
                arcade.Text(
                    "", 0, 0, arcade.color.LIGHT_GRAY, 11,
                    anchor_x="left", anchor_y="center",
                )
            )

        # Score texts: 13 categories x 4 players max
        self.txt_scores = []
        for _ in CATEGORIES:
            row = []
            for _ in range(4):
                row.append(
                    arcade.Text(
                        "", 0, 0, arcade.color.WHITE, 11,
                        anchor_x="center", anchor_y="center",
                    )
                )
            self.txt_scores.append(row)

        # Summary rows (upper bonus, upper total, lower total, grand total)
        self.txt_summary_labels = []
        for _ in range(4):
            self.txt_summary_labels.append(
                arcade.Text(
                    "", 0, 0, arcade.color.WHITE, 11,
                    anchor_x="left", anchor_y="center", bold=True,
                )
            )
        self.txt_summary_scores = []
        for _ in range(4):
            row = []
            for _ in range(4):
                row.append(
                    arcade.Text(
                        "", 0, 0, arcade.color.WHITE, 11,
                        anchor_x="center", anchor_y="center",
                    )
                )
            self.txt_summary_scores.append(row)

        # Game over
        self.txt_game_over_title = arcade.Text(
            "Game Over!", WIDTH // 2, HEIGHT // 2 + 100,
            arcade.color.WHITE, 36, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_winner = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 50,
            arcade.color.GREEN, 24, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_scores = []
        for i in range(4):
            self.txt_game_over_scores.append(
                arcade.Text(
                    "", WIDTH // 2, HEIGHT // 2 - i * 30,
                    arcade.color.WHITE, 18, anchor_x="center", anchor_y="center",
                )
            )
        self.txt_game_over_hint = arcade.Text(
            "Click 'New Game' to play again",
            WIDTH // 2, HEIGHT // 2 - 140,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center",
        )

    # ------------------------------------------------------------------ game setup

    def _start_game(self):
        """Initialize the game with selected number of players."""
        num_total = self.pending_num_players
        self.players = []

        # Human player (always index 0)
        self.players.append({
            "name": "You",
            "scores": {},
            "scores_used": set(),
            "ai": None,
        })
        self.txt_player_headers[0].text = "You"

        # AI players
        for i in range(num_total - 1):
            name = f"AI {i + 1}"
            ai = YahtzeeAI()
            self.players.append({
                "name": name,
                "scores": {},
                "scores_used": set(),
                "ai": ai,
            })
            self.txt_player_headers[i + 1].text = name

        self.current_round = 1
        self.current_player_index = 0
        self._start_turn()

    def _start_turn(self):
        """Start a new turn for the current player."""
        self.dice = [0, 0, 0, 0, 0]
        self.kept_indices = set()
        self.roll_number = 0
        self.selected_category = None
        self.ai_timer = 0.0
        self.ai_step = 0

        player = self.players[self.current_player_index]
        if player["ai"] is not None:
            self.phase = PHASE_AI_TURN
        else:
            self.phase = PHASE_ROLLING

        self._update_info_texts()

    def _update_info_texts(self):
        """Update the info bar texts."""
        self.txt_round_info.text = f"Round {self.current_round} of {TOTAL_ROUNDS}"
        name = self.players[self.current_player_index]["name"]
        if self.current_player_index == 0:
            self.txt_current_player.text = "Your turn"
            self.txt_current_player.color = arcade.color.WHITE
        else:
            self.txt_current_player.text = f"{name}'s turn"
            self.txt_current_player.color = arcade.color.YELLOW

        rolls_left = 3 - self.roll_number
        if rolls_left > 0:
            self.txt_rolls_left.text = f"Rolls left: {rolls_left}"
        else:
            self.txt_rolls_left.text = "Must score"

    # ------------------------------------------------------------------ game logic

    def _roll_dice(self):
        """Roll all non-kept dice."""
        if self.roll_number >= 3:
            return
        for i in range(5):
            if i not in self.kept_indices:
                self.dice[i] = random.randint(1, 6)
        self.roll_number += 1
        self.selected_category = None
        self._update_info_texts()

        if self.roll_number >= 1 and self.phase == PHASE_ROLLING:
            self.phase = PHASE_ROLLING

    def _score_category(self, category):
        """Score the current dice in the given category for the current player."""
        player = self.players[self.current_player_index]
        if category in player["scores_used"]:
            return False

        score = calculate_score(self.dice, category)
        player["scores"][category] = score
        player["scores_used"].add(category)
        return True

    def _advance_turn(self):
        """Move to the next player or next round."""
        next_idx = self.current_player_index + 1
        if next_idx >= len(self.players):
            next_idx = 0
            self.current_round += 1
            if self.current_round > TOTAL_ROUNDS:
                self._end_game()
                return

        self.current_player_index = next_idx
        self._start_turn()

    def _end_game(self):
        """Determine winner and set game over."""
        self.phase = PHASE_GAME_OVER

        best_score = -1
        winner_name = ""
        for i, player in enumerate(self.players):
            total = self._get_grand_total(player)
            self.txt_game_over_scores[i].text = f"{player['name']}: {total} points"
            if total > best_score:
                best_score = total
                winner_name = player["name"]

        if winner_name == "You":
            self.txt_game_over_winner.text = "You Win!"
            self.txt_game_over_winner.color = arcade.color.GREEN
        else:
            self.txt_game_over_winner.text = f"{winner_name} Wins!"
            self.txt_game_over_winner.color = arcade.color.RED

    def _get_grand_total(self, player):
        """Calculate grand total including upper bonus."""
        upper_total = sum(player["scores"].get(c, 0) for c in UPPER_CATEGORIES)
        lower_cats = [c for c in CATEGORIES if c not in UPPER_CATEGORIES]
        lower_total = sum(player["scores"].get(c, 0) for c in lower_cats)
        bonus = 35 if upper_total >= 63 else 0
        return upper_total + lower_total + bonus

    # ------------------------------------------------------------------ AI

    def on_update(self, delta_time):
        if self.phase != PHASE_AI_TURN:
            return

        self.ai_timer += delta_time
        if self.ai_timer < AI_DELAY:
            return

        self.ai_timer = 0.0
        player = self.players[self.current_player_index]
        ai = player["ai"]
        if ai is None:
            return

        if self.ai_step == 0:
            # First roll
            self.kept_indices = set()
            self._roll_dice()
            self.ai_step = 1
        elif self.ai_step == 1:
            # Choose dice to keep, then reroll
            if self.roll_number < 3:
                keep = ai.choose_dice_to_keep(self.dice, player["scores_used"], self.roll_number)
                self.kept_indices = set(keep)
                self._roll_dice()
                self.ai_step = 2
            else:
                self.ai_step = 3
        elif self.ai_step == 2:
            # Second reroll or go to scoring
            if self.roll_number < 3:
                keep = ai.choose_dice_to_keep(self.dice, player["scores_used"], self.roll_number)
                self.kept_indices = set(keep)
                self._roll_dice()
            self.ai_step = 3
        elif self.ai_step == 3:
            # Pick a category and score
            category = ai.choose_category(self.dice, player["scores_used"])
            self._score_category(category)
            self._advance_turn()

    # ------------------------------------------------------------------ draw

    def on_draw(self):
        self.clear()
        from renderers import yahtzee_renderer
        yahtzee_renderer.draw(self)

    # ------------------------------------------------------------------ input

    def _in_rect(self, x, y, cx, cy, w, h):
        return cx - w / 2 <= x <= cx + w / 2 and cy - h / 2 <= y <= cy + h / 2

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
            self.pending_num_players = 0
            return

        # Help button
        if self.help_button.hit_test(x, y):
            rules_view = RulesView(
                "Yahtzee", "yahtzee.txt", None, self.menu_view,
                existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        if self.phase == PHASE_SETUP:
            self._handle_setup_click(x, y)
        elif self.phase in (PHASE_ROLLING, PHASE_SCORING):
            self._handle_playing_click(x, y)

    def _handle_setup_click(self, x, y):
        """Handle clicks during setup phase."""
        for i in range(4):
            bx = WIDTH // 2 - 120 + i * 80
            by = HEIGHT // 2 + 20
            if self._in_rect(x, y, bx, by, SETUP_BTN_W, SETUP_BTN_H):
                self.pending_num_players = i + 1
                return

        # Start button
        if self.pending_num_players > 0:
            sx, sy = WIDTH // 2, HEIGHT // 2 - 60
            if self._in_rect(x, y, sx, sy, 140, 44):
                self._start_game()
                return

    def _handle_playing_click(self, x, y):
        """Handle clicks during the playing phases."""
        if self.current_player_index != 0:
            return

        # Click on dice to toggle keep
        if self.roll_number >= 1 and self.roll_number < 3:
            for i in range(5):
                dx = DICE_START_X + i * (DIE_SIZE + DIE_GAP)
                dy = DICE_AREA_Y
                if self._in_rect(x, y, dx, dy, DIE_SIZE, DIE_SIZE):
                    if i in self.kept_indices:
                        self.kept_indices.discard(i)
                    else:
                        self.kept_indices.add(i)
                    return

        # Roll button
        roll_x, roll_y = 660, DICE_AREA_Y + 20
        if self._in_rect(x, y, roll_x, roll_y, ROLL_BTN_W, ROLL_BTN_H):
            if self.roll_number < 3:
                self._roll_dice()
            return

        # Score button
        if self.roll_number >= 1:
            score_x, score_y = 660, DICE_AREA_Y - 30
            if self._in_rect(x, y, score_x, score_y, SCORE_BTN_W, SCORE_BTN_H):
                if self.selected_category is not None:
                    if self._score_category(self.selected_category):
                        self._advance_turn()
                return

        # Click on scorecard category row
        if self.roll_number >= 1:
            self._handle_category_click(x, y)

    def _handle_category_click(self, x, y):
        """Check if a category row in the scorecard was clicked."""
        player = self.players[self.current_player_index]
        num_players = len(self.players)
        card_width = CARD_LABEL_W + num_players * CARD_COL_W

        for cat_idx, cat in enumerate(CATEGORIES):
            if cat in player["scores_used"]:
                continue
            ry = CARD_TOP - CARD_HEADER_H - cat_idx * CARD_ROW_H
            row_x = CARD_LEFT + card_width // 2
            if self._in_rect(x, y, row_x, ry, card_width, CARD_ROW_H):
                self.selected_category = cat
                self.phase = PHASE_SCORING
                return
