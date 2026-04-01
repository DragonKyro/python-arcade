"""
Snakes & Ladders game view using Arcade 3.x APIs.
State, input, and logic only -- rendering is in renderers/snakes_and_ladders_renderer.py.
"""

import random

import arcade
from pages.rules import RulesView
from ai.snakes_and_ladders_ai import SnakesAndLaddersAI
from renderers.snakes_and_ladders_renderer import (
    WIDTH, HEIGHT,
    BUTTON_W, BUTTON_H,
    ROLL_BTN_X, ROLL_BTN_Y, ROLL_BTN_W, ROLL_BTN_H,
    CELL_SIZE, BOARD_LEFT, BOARD_BOTTOM, BOARD_SIZE,
    PLAYER_COLORS, PLAYER_COLOR_NAMES,
    LADDERS, SNAKES,
)

# Game phases
PHASE_SETUP = "setup"
PHASE_PLAYING = "playing"
PHASE_GAME_OVER = "game_over"

# Timing
AI_DELAY = 0.5


class SnakesAndLaddersView(arcade.View):
    """Arcade View for Snakes & Ladders."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view

        # Setup state
        self.phase = PHASE_SETUP
        self.pending_num_players = 0

        # Game state
        self.num_players = 0
        self.positions = []        # position per player (0 = not started, 1-100 = on board)
        self.current_player = 0
        self.dice_result = 0
        self.ai_players = []       # list of SnakesAndLaddersAI (index 0 = None for human)
        self.ai_timer = 0.0
        self.waiting_for_animation = False
        self.animation_timer = 0.0
        self.winner = -1

        self._create_texts()

    def _create_texts(self):
        """Create reusable arcade.Text objects."""
        self.txt_title = arcade.Text(
            "Snakes & Ladders", WIDTH / 2, HEIGHT - 30,
            arcade.color.WHITE, 22, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_btn_back = arcade.Text(
            "Back", 60, HEIGHT - 30, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_btn_new_game = arcade.Text(
            "New Game", WIDTH - 70, HEIGHT - 30, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_btn_help = arcade.Text(
            "?", WIDTH - 145, HEIGHT - 30, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )

        # Setup
        self.txt_setup_prompt = arcade.Text(
            "Choose total players (1 human + AI):", WIDTH // 2, HEIGHT // 2 + 80,
            arcade.color.WHITE, 20, anchor_x="center", anchor_y="center",
        )
        self.txt_setup_btn_labels = []
        for i in range(5):
            bx = WIDTH // 2 - 160 + i * 80
            by = HEIGHT // 2 + 20
            self.txt_setup_btn_labels.append(
                arcade.Text(
                    str(i + 2), bx, by, arcade.color.WHITE, 18,
                    anchor_x="center", anchor_y="center", bold=True,
                )
            )
        self.txt_start_btn = arcade.Text(
            "Start Game", WIDTH // 2, HEIGHT // 2 - 120,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_color_preview = arcade.Text(
            "Players:", WIDTH // 2, HEIGHT // 2 - 20,
            arcade.color.LIGHT_GRAY, 14, anchor_x="center", anchor_y="center",
        )
        self.txt_color_labels = []
        for i in range(6):
            self.txt_color_labels.append(
                arcade.Text(
                    "", 0, 0, arcade.color.LIGHT_GRAY, 11,
                    anchor_x="center", anchor_y="center",
                )
            )

        # Playing phase
        self.txt_turn = arcade.Text(
            "", 660, 530, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_dice_label = arcade.Text(
            "Dice:", 630, 470, arcade.color.LIGHT_GRAY, 13,
            anchor_x="center", anchor_y="center",
        )
        self.txt_roll_btn = arcade.Text(
            "Roll Dice", ROLL_BTN_X, ROLL_BTN_Y, arcade.color.WHITE, 16,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Player info (up to 6)
        self.txt_player_infos = []
        for i in range(6):
            self.txt_player_infos.append(
                arcade.Text(
                    "", 0, 0, arcade.color.WHITE, 13,
                    anchor_x="left", anchor_y="center",
                )
            )

        # Square numbers (100)
        self.txt_square_numbers = []
        for sq in range(1, 101):
            self.txt_square_numbers.append(
                arcade.Text(
                    str(sq), 0, 0, (120, 110, 90), 8,
                    anchor_x="center", anchor_y="center",
                )
            )

        # Game over
        self.txt_game_over_msg = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 + 20,
            arcade.color.WHITE, 28, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_hint = arcade.Text(
            "Click 'New Game' to play again.",
            WIDTH / 2, HEIGHT / 2 - 25,
            arcade.color.LIGHT_GRAY, 14, anchor_x="center", anchor_y="center",
        )

    def _start_game(self):
        """Initialize game state with selected player count."""
        self.num_players = self.pending_num_players
        self.positions = [0] * self.num_players
        self.current_player = 0
        self.dice_result = 0
        self.winner = -1
        self.ai_timer = 0.0
        self.waiting_for_animation = False

        # Create AI players (index 0 = human = None)
        self.ai_players = [None]
        for i in range(1, self.num_players):
            self.ai_players.append(SnakesAndLaddersAI())

        self.phase = PHASE_PLAYING
        self._update_turn_text()

    def _update_turn_text(self):
        if self.phase != PHASE_PLAYING:
            self.txt_turn.text = ""
            return
        if self.current_player == 0:
            self.txt_turn.text = "Your turn!"
            self.txt_turn.color = arcade.color.WHITE
        else:
            name = f"AI {self.current_player}"
            self.txt_turn.text = f"{name}'s turn..."
            self.txt_turn.color = arcade.color.YELLOW

    def _roll_dice(self):
        """Roll the dice and process the move for the current player."""
        if self.current_player == 0:
            result = random.randint(1, 6)
        else:
            result = self.ai_players[self.current_player].roll_dice()

        self.dice_result = result
        self._apply_move(result)

    def _apply_move(self, dice_value):
        """Apply dice roll to current player."""
        pos = self.positions[self.current_player]

        if pos == 0:
            # Player enters the board
            new_pos = dice_value
        else:
            new_pos = pos + dice_value

        # Need exact roll to reach 100
        if new_pos > 100:
            # Can't move, turn passes
            self.waiting_for_animation = True
            self.animation_timer = 0.5
            return

        self.positions[self.current_player] = new_pos

        # Check for win
        if new_pos == 100:
            self.winner = self.current_player
            self.phase = PHASE_GAME_OVER
            if self.winner == 0:
                self.txt_game_over_msg.text = "You Win!"
                self.txt_game_over_msg.color = arcade.color.LIGHT_GREEN
            else:
                self.txt_game_over_msg.text = f"AI {self.winner} Wins!"
                self.txt_game_over_msg.color = arcade.color.LIGHT_CORAL
            return

        # Check ladders and snakes
        if new_pos in LADDERS:
            self.positions[self.current_player] = LADDERS[new_pos]
        elif new_pos in SNAKES:
            self.positions[self.current_player] = SNAKES[new_pos]

        # Brief animation delay before next turn
        self.waiting_for_animation = True
        self.animation_timer = 0.4

    def _advance_turn(self):
        """Move to the next player's turn."""
        self.current_player = (self.current_player + 1) % self.num_players
        self.ai_timer = 0.0
        self._update_turn_text()

    # ------------------------------------------------------------------ lifecycle

    def on_show(self):
        arcade.set_background_color((50, 80, 50))

    def on_draw(self):
        self.clear()
        from renderers import snakes_and_ladders_renderer
        snakes_and_ladders_renderer.draw(self)

    def on_update(self, delta_time):
        if self.phase == PHASE_SETUP or self.phase == PHASE_GAME_OVER:
            return

        # Handle animation delay
        if self.waiting_for_animation:
            self.animation_timer -= delta_time
            if self.animation_timer <= 0:
                self.waiting_for_animation = False
                self._advance_turn()
            return

        # AI auto-roll
        if self.current_player != 0:
            self.ai_timer += delta_time
            if self.ai_timer >= AI_DELAY:
                self._roll_dice()

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
            self.pending_num_players = 0
            return

        # Help button
        if self._in_rect(x, y, WIDTH - 145, HEIGHT - 30, 40, BUTTON_H):
            rules_view = RulesView(
                "Snakes & Ladders", "snakes_and_ladders.txt", None,
                self.menu_view, existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        if self.phase == PHASE_SETUP:
            self._handle_setup_click(x, y)
        elif self.phase == PHASE_PLAYING:
            self._handle_playing_click(x, y)

    def _handle_setup_click(self, x, y):
        # Player count buttons (2-6)
        for i in range(5):
            bx = WIDTH // 2 - 160 + i * 80
            by = HEIGHT // 2 + 20
            if self._in_rect(x, y, bx, by, 60, 44):
                self.pending_num_players = i + 2
                return

        # Start button
        if self.pending_num_players > 0:
            sx, sy = WIDTH // 2, HEIGHT // 2 - 120
            if self._in_rect(x, y, sx, sy, 140, 44):
                self._start_game()

    def _handle_playing_click(self, x, y):
        # Roll button (human turn only)
        if self.current_player == 0 and not self.waiting_for_animation:
            if self._in_rect(x, y, ROLL_BTN_X, ROLL_BTN_Y, ROLL_BTN_W, ROLL_BTN_H):
                self._roll_dice()

    def _in_rect(self, x, y, cx, cy, w, h):
        return cx - w / 2 <= x <= cx + w / 2 and cy - h / 2 <= y <= cy + h / 2


# Allow running standalone for testing
if __name__ == "__main__":
    window = arcade.Window(WIDTH, HEIGHT, "Snakes & Ladders")

    class DummyMenu(arcade.View):
        def __init__(self):
            super().__init__()
            self.txt = arcade.Text(
                "Menu", WIDTH / 2, HEIGHT / 2,
                arcade.color.WHITE, 20, anchor_x="center")

        def on_draw(self):
            self.clear()
            self.txt.draw()

    menu = DummyMenu()
    game = SnakesAndLaddersView(menu)
    window.show_view(game)
    arcade.run()
