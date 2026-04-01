"""
Ludo game view using Arcade 3.x APIs.
State, input, and logic only -- rendering is in renderers/ludo_renderer.py.
"""

import random

import arcade
from pages.rules import RulesView
from ai.ludo_ai import LudoAI
from renderers.ludo_renderer import (
    WIDTH, HEIGHT,
    BUTTON_W, BUTTON_H,
    ROLL_BTN_X, ROLL_BTN_Y, ROLL_BTN_W, ROLL_BTN_H,
    CELL_SIZE, BOARD_LEFT, BOARD_BOTTOM,
    PLAYER_COLORS, PLAYER_COLOR_NAMES,
    TRACK_COORDS, FINISH_LANES, HOME_BASES, SAFE_SQUARES,
    PLAYER_ENTRY, PIECE_RADIUS,
    SIDEBAR_X,
    grid_to_pixel,
)

# Game phases
PHASE_SETUP = "setup"
PHASE_ROLL = "roll"        # waiting for dice roll
PHASE_PICK = "pick"        # waiting for piece selection
PHASE_ANIMATING = "animating"
PHASE_GAME_OVER = "game_over"

# Timing
AI_DELAY = 0.5

# Track / finish constants
TRACK_LENGTH = 52
FINISH_LANE_LENGTH = 6
STEPS_TO_FINISH = 51  # steps from entry around the track to the finish lane entrance


class LudoView(arcade.View):
    """Arcade View for Ludo."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view

        # Setup state
        self.phase = PHASE_SETUP
        self.pending_num_players = 0

        # Game state
        self.num_players = 0
        self.pieces = []           # pieces[player_id] = list of 4 piece dicts
        self.current_player = 0
        self.dice_result = 0
        self.consecutive_sixes = 0
        self.valid_moves = []      # list of piece indices that can move
        self.ai_players = []       # list of LudoAI or None
        self.ai_timer = 0.0
        self.animation_timer = 0.0
        self.winner = -1

        self._create_texts()

    def _create_texts(self):
        """Create reusable arcade.Text objects."""
        self.txt_title = arcade.Text(
            "Ludo", WIDTH / 2, HEIGHT - 30,
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
            "Choose number of players (1 human + AI):", WIDTH // 2, HEIGHT // 2 + 80,
            arcade.color.WHITE, 18, anchor_x="center", anchor_y="center",
        )
        self.txt_setup_btn_labels = []
        for i in range(3):
            bx = WIDTH // 2 - 80 + i * 80
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
        for i in range(4):
            self.txt_color_labels.append(
                arcade.Text(
                    "", 0, 0, arcade.color.LIGHT_GRAY, 11,
                    anchor_x="center", anchor_y="center",
                )
            )

        # Playing phase
        self.txt_turn = arcade.Text(
            "", SIDEBAR_X + 50, 530, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_dice_label = arcade.Text(
            "Dice:", SIDEBAR_X + 10, 440, arcade.color.LIGHT_GRAY, 13,
            anchor_x="center", anchor_y="center",
        )
        self.txt_roll_btn = arcade.Text(
            "Roll Dice", ROLL_BTN_X, ROLL_BTN_Y, arcade.color.WHITE, 16,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_pick_instr = arcade.Text(
            "Click a piece to move", SIDEBAR_X + 50, 350,
            arcade.color.YELLOW, 13, anchor_x="center", anchor_y="center",
        )

        # Player info (up to 4)
        self.txt_player_infos = []
        self.txt_player_finished = []
        for i in range(4):
            self.txt_player_infos.append(
                arcade.Text(
                    "", 0, 0, arcade.color.WHITE, 13,
                    anchor_x="left", anchor_y="center",
                )
            )
            self.txt_player_finished.append(
                arcade.Text(
                    "", 0, 0, arcade.color.LIGHT_GRAY, 11,
                    anchor_x="left", anchor_y="center",
                )
            )

        self.txt_sixes_warning = arcade.Text(
            "", SIDEBAR_X + 50, 480, arcade.color.ORANGE, 12,
            anchor_x="center", anchor_y="center",
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

    # ------------------------------------------------------------------ game setup

    def _make_piece(self):
        """Create a new piece dict in home state."""
        return {
            "state": "home",       # home, track, finish_lane, finished
            "track_pos": -1,       # global track index (0-51)
            "finish_pos": -1,      # position in finish lane (0-5)
            "steps_from_entry": 0, # steps taken since entering track
        }

    def _start_game(self):
        """Initialize game with selected player count."""
        self.num_players = self.pending_num_players
        self.pieces = []
        for _ in range(self.num_players):
            self.pieces.append([self._make_piece() for _ in range(4)])

        self.current_player = 0
        self.dice_result = 0
        self.consecutive_sixes = 0
        self.valid_moves = []
        self.winner = -1
        self.ai_timer = 0.0

        # AI players (index 0 = human = None)
        self.ai_players = [None]
        for i in range(1, self.num_players):
            self.ai_players.append(LudoAI())

        self.phase = PHASE_ROLL
        self._update_turn_text()

    def _update_turn_text(self):
        if self.phase == PHASE_GAME_OVER:
            self.txt_turn.text = ""
            return
        if self.current_player == 0:
            if self.phase == PHASE_ROLL:
                self.txt_turn.text = "Your turn - Roll!"
            elif self.phase == PHASE_PICK:
                self.txt_turn.text = "Pick a piece"
            else:
                self.txt_turn.text = "Your turn"
            self.txt_turn.color = arcade.color.WHITE
        else:
            name = f"AI {self.current_player}"
            self.txt_turn.text = f"{name}'s turn..."
            self.txt_turn.color = arcade.color.YELLOW

    # ------------------------------------------------------------------ game logic

    def _roll_dice(self):
        """Roll the dice for the current player."""
        result = random.randint(1, 6)
        self.dice_result = result

        if result == 6:
            self.consecutive_sixes += 1
            if self.consecutive_sixes >= 3:
                # Three 6s in a row: lose turn
                self.consecutive_sixes = 0
                self.phase = PHASE_ANIMATING
                self.animation_timer = 0.6
                return
        else:
            self.consecutive_sixes = 0

        # Find valid moves
        self.valid_moves = self._get_valid_piece_indices(self.current_player, result)

        if not self.valid_moves:
            # No valid moves, advance turn
            self.phase = PHASE_ANIMATING
            self.animation_timer = 0.4
            return

        if len(self.valid_moves) == 1 and self.current_player != 0:
            # AI with one option: auto-select
            self._move_piece(self.current_player, self.valid_moves[0], result)
            return

        self.phase = PHASE_PICK
        self._update_turn_text()

    def _get_valid_piece_indices(self, player_id, dice):
        """Return indices of pieces that can legally move."""
        valid = []
        entry = PLAYER_ENTRY[player_id]

        for i, p in enumerate(self.pieces[player_id]):
            if p["state"] == "finished":
                continue
            if p["state"] == "home":
                if dice == 6:
                    valid.append(i)
            elif p["state"] == "track":
                steps_after = p["steps_from_entry"] + dice
                if steps_after <= STEPS_TO_FINISH + FINISH_LANE_LENGTH:
                    valid.append(i)
            elif p["state"] == "finish_lane":
                new_fp = p["finish_pos"] + dice
                if new_fp <= FINISH_LANE_LENGTH:
                    valid.append(i)
        return valid

    def _move_piece(self, player_id, piece_idx, dice):
        """Move a piece by the dice value."""
        piece = self.pieces[player_id][piece_idx]
        entry = PLAYER_ENTRY[player_id]

        if piece["state"] == "home":
            # Enter the track
            piece["state"] = "track"
            piece["track_pos"] = entry
            piece["steps_from_entry"] = 0
            # Check for capture at entry
            self._check_capture(player_id, entry)

        elif piece["state"] == "track":
            steps_after = piece["steps_from_entry"] + dice
            if steps_after > STEPS_TO_FINISH:
                # Enter finish lane
                finish_pos = steps_after - STEPS_TO_FINISH
                if finish_pos == FINISH_LANE_LENGTH:
                    piece["state"] = "finished"
                    piece["track_pos"] = -1
                    piece["finish_pos"] = -1
                else:
                    piece["state"] = "finish_lane"
                    piece["finish_pos"] = finish_pos - 1  # 0-indexed
                    piece["track_pos"] = -1
            else:
                new_global = (entry + steps_after) % TRACK_LENGTH
                piece["track_pos"] = new_global
                piece["steps_from_entry"] = steps_after
                self._check_capture(player_id, new_global)

        elif piece["state"] == "finish_lane":
            new_fp = piece["finish_pos"] + dice
            if new_fp + 1 == FINISH_LANE_LENGTH:
                piece["state"] = "finished"
                piece["finish_pos"] = -1
            else:
                piece["finish_pos"] = new_fp

        # Check for win
        if all(p["state"] == "finished" for p in self.pieces[player_id]):
            self.winner = player_id
            self.phase = PHASE_GAME_OVER
            if self.winner == 0:
                self.txt_game_over_msg.text = "You Win!"
                self.txt_game_over_msg.color = arcade.color.LIGHT_GREEN
            else:
                self.txt_game_over_msg.text = f"AI {self.winner} Wins!"
                self.txt_game_over_msg.color = arcade.color.LIGHT_CORAL
            return

        # Bonus turn for rolling 6
        if self.dice_result == 6:
            self.phase = PHASE_ANIMATING
            self.animation_timer = 0.3
            self._bonus_turn = True
        else:
            self.phase = PHASE_ANIMATING
            self.animation_timer = 0.3
            self._bonus_turn = False

    def _check_capture(self, player_id, track_pos):
        """Send opponent pieces home if landed on a non-safe square."""
        if track_pos in SAFE_SQUARES:
            return
        for opp_id in range(self.num_players):
            if opp_id == player_id:
                continue
            for p in self.pieces[opp_id]:
                if p["state"] == "track" and p["track_pos"] == track_pos:
                    p["state"] = "home"
                    p["track_pos"] = -1
                    p["steps_from_entry"] = 0

    def _advance_turn(self):
        """Move to the next player's turn."""
        if hasattr(self, '_bonus_turn') and self._bonus_turn:
            self._bonus_turn = False
            self.phase = PHASE_ROLL
            self.ai_timer = 0.0
            self._update_turn_text()
            return

        self.current_player = (self.current_player + 1) % self.num_players
        self.consecutive_sixes = 0
        self.phase = PHASE_ROLL
        self.ai_timer = 0.0
        self._update_turn_text()

    def _build_board_state(self, player_id):
        """Build the board_state dict for the AI."""
        entry = PLAYER_ENTRY[player_id]
        opponent_positions = []
        for opp_id in range(self.num_players):
            if opp_id == player_id:
                continue
            for p in self.pieces[opp_id]:
                if p["state"] == "track":
                    opponent_positions.append(p["track_pos"])

        return {
            "opponent_positions": opponent_positions,
            "safe_squares": SAFE_SQUARES,
            "finish_lane_length": FINISH_LANE_LENGTH,
            "track_length": TRACK_LENGTH,
            "player_entry": entry,
            "steps_to_finish_entry": STEPS_TO_FINISH,
        }

    # ------------------------------------------------------------------ lifecycle

    def on_show(self):
        arcade.set_background_color((40, 50, 70))

    def on_draw(self):
        self.clear()
        from renderers import ludo_renderer
        ludo_renderer.draw(self)

    def on_update(self, delta_time):
        if self.phase in (PHASE_SETUP, PHASE_GAME_OVER):
            return

        # Handle animation delay
        if self.phase == PHASE_ANIMATING:
            self.animation_timer -= delta_time
            if self.animation_timer <= 0:
                self._advance_turn()
            return

        # AI turns
        if self.current_player != 0:
            self.ai_timer += delta_time
            if self.ai_timer >= AI_DELAY:
                if self.phase == PHASE_ROLL:
                    self._roll_dice()
                    # If phase changed to PICK, AI needs to choose
                    if self.phase == PHASE_PICK:
                        self._do_ai_pick()
                elif self.phase == PHASE_PICK:
                    self._do_ai_pick()

    def _do_ai_pick(self):
        """Let AI choose a piece to move."""
        ai = self.ai_players[self.current_player]
        if ai is None:
            return

        board_state = self._build_board_state(self.current_player)
        pieces_data = self.pieces[self.current_player]

        choice = ai.choose_piece(pieces_data, self.dice_result, board_state)

        if choice >= 0 and choice in self.valid_moves:
            self._move_piece(self.current_player, choice, self.dice_result)
        elif self.valid_moves:
            # Fallback
            self._move_piece(self.current_player, self.valid_moves[0], self.dice_result)
        else:
            # No valid moves
            self.phase = PHASE_ANIMATING
            self.animation_timer = 0.3

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
                "Ludo", "ludo.txt", None,
                self.menu_view, existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        if self.phase == PHASE_SETUP:
            self._handle_setup_click(x, y)
        elif self.phase == PHASE_ROLL and self.current_player == 0:
            self._handle_roll_click(x, y)
        elif self.phase == PHASE_PICK and self.current_player == 0:
            self._handle_pick_click(x, y)

    def _handle_setup_click(self, x, y):
        # Player count buttons (2-4)
        for i in range(3):
            bx = WIDTH // 2 - 80 + i * 80
            by = HEIGHT // 2 + 20
            if self._in_rect(x, y, bx, by, 60, 44):
                self.pending_num_players = i + 2
                return

        # Start button
        if self.pending_num_players > 0:
            sx, sy = WIDTH // 2, HEIGHT // 2 - 120
            if self._in_rect(x, y, sx, sy, 140, 44):
                self._start_game()

    def _handle_roll_click(self, x, y):
        if self._in_rect(x, y, ROLL_BTN_X, ROLL_BTN_Y, ROLL_BTN_W, ROLL_BTN_H):
            self._roll_dice()
            if self.phase == PHASE_PICK:
                self._update_turn_text()

    def _handle_pick_click(self, x, y):
        """Handle clicking on a piece to move it."""
        player_id = 0
        for piece_idx in self.valid_moves:
            piece = self.pieces[player_id][piece_idx]
            px, py = self._get_piece_pixel(player_id, piece_idx)
            if px is None:
                continue
            dist = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
            if dist <= PIECE_RADIUS + 4:
                self._move_piece(player_id, piece_idx, self.dice_result)
                return

    def _get_piece_pixel(self, player_id, piece_idx):
        """Get pixel position of a piece for click detection."""
        piece = self.pieces[player_id][piece_idx]
        if piece["state"] == "home":
            center_col, center_row = HOME_BASES[player_id]
            cx, cy = grid_to_pixel(center_col, center_row)
            offsets = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
            dx, dy = offsets[piece_idx]
            return cx + dx * CELL_SIZE * 1.2, cy + dy * CELL_SIZE * 1.2
        elif piece["state"] == "track":
            col, row = TRACK_COORDS[piece["track_pos"] % len(TRACK_COORDS)]
            return grid_to_pixel(col, row)
        elif piece["state"] == "finish_lane":
            fp = piece["finish_pos"]
            if 0 <= fp < len(FINISH_LANES[player_id]):
                col, row = FINISH_LANES[player_id][fp]
                return grid_to_pixel(col, row)
        return None, None

    def _in_rect(self, x, y, cx, cy, w, h):
        return cx - w / 2 <= x <= cx + w / 2 and cy - h / 2 <= y <= cy + h / 2


# Allow running standalone for testing
if __name__ == "__main__":
    window = arcade.Window(WIDTH, HEIGHT, "Ludo")

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
    game = LudoView(menu)
    window.show_view(game)
    arcade.run()
