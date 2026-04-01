"""
Backgammon game view using arcade 2.6.x APIs.

Player = White checkers, moves points 24->1 (board indices 23->0)
AI = Brown checkers, moves points 1->24 (board indices 0->23)
"""

import arcade
import random

from pages.rules import RulesView
from ai.backgammon_ai import (
    BackgammonAI, initial_board, get_all_legal_moves, apply_moves,
    _single_die_moves, _apply_single_move, _all_in_home,
    PLAYER, AI,
)
from renderers.backgammon_renderer import (
    WIDTH, HEIGHT,
    BOARD_LEFT, BOARD_RIGHT, BOARD_TOP, BOARD_BOTTOM,
    BAR_LEFT, BAR_RIGHT,
    POINT_WIDTH, HALF_HEIGHT,
    CHECKER_RADIUS, CHECKER_STACK_OFFSET,
    BG_COLOR,
    PLAYER_COLOR, AI_COLOR,
)

# Game states
STATE_PLAYER_ROLL = "player_roll"
STATE_PLAYER_MOVE = "player_move"
STATE_AI_TURN = "ai_turn"
STATE_GAME_OVER = "game_over"


class BackgammonView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.ai = BackgammonAI()
        self._create_texts()
        self.reset_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        bar_cx = (BAR_LEFT + BAR_RIGHT) / 2
        off_x = BOARD_RIGHT + 20

        # Title (static)
        self.txt_title = arcade.Text(
            "Backgammon", WIDTH / 2, HEIGHT - 20,
            arcade.color.WHITE, font_size=22,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Button labels (static)
        self.txt_btn_back = arcade.Text(
            "Back", 55, HEIGHT - 20, arcade.color.WHITE,
            font_size=13, anchor_x="center", anchor_y="center",
        )
        self.txt_btn_new_game = arcade.Text(
            "New Game", WIDTH - 65, HEIGHT - 20, arcade.color.WHITE,
            font_size=13, anchor_x="center", anchor_y="center",
        )
        self.txt_btn_help = arcade.Text(
            "?", WIDTH - 135, HEIGHT - 20, arcade.color.WHITE,
            font_size=13, anchor_x="center", anchor_y="center",
        )
        self.txt_btn_roll_dice = arcade.Text(
            "Roll Dice", WIDTH / 2, HEIGHT - 50, arcade.color.WHITE,
            font_size=13, anchor_x="center", anchor_y="center",
        )

        # Player/AI side labels (static)
        self.txt_label_player = arcade.Text(
            "You (White)", BOARD_LEFT, BOARD_BOTTOM - 35,
            PLAYER_COLOR, font_size=12, anchor_x="left", anchor_y="center",
        )
        self.txt_label_ai = arcade.Text(
            "AI (Brown)", BOARD_LEFT, BOARD_TOP + 25,
            AI_COLOR, font_size=12, anchor_x="left", anchor_y="center",
        )

        # Bar label (static)
        mid_y = (BOARD_BOTTOM + BOARD_TOP) / 2
        self.txt_bar_label = arcade.Text(
            "BAR", bar_cx, mid_y, (200, 200, 200),
            font_size=10, anchor_x="center", anchor_y="center", bold=True,
        )

        # Bar counts (dynamic)
        self.txt_bar_player = arcade.Text(
            "", bar_cx, BOARD_BOTTOM + 10, PLAYER_COLOR,
            font_size=10, anchor_x="center", anchor_y="center",
        )
        self.txt_bar_ai = arcade.Text(
            "", bar_cx, BOARD_TOP - 10, AI_COLOR,
            font_size=10, anchor_x="center", anchor_y="center",
        )

        # Off area labels (static)
        self.txt_off_player_label = arcade.Text(
            "OFF", off_x, BOARD_BOTTOM + HALF_HEIGHT // 2, (200, 200, 200),
            font_size=9, anchor_x="center", anchor_y="center",
        )
        self.txt_off_ai_label = arcade.Text(
            "OFF", off_x, BOARD_TOP - HALF_HEIGHT // 2, (200, 200, 200),
            font_size=9, anchor_x="center", anchor_y="center",
        )

        # Off counts (dynamic)
        self.txt_off_player_count = arcade.Text(
            "", off_x, BOARD_BOTTOM + HALF_HEIGHT // 2 - 20, PLAYER_COLOR,
            font_size=16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_off_ai_count = arcade.Text(
            "", off_x, BOARD_TOP - HALF_HEIGHT // 2 + 20, AI_COLOR,
            font_size=16, anchor_x="center", anchor_y="center", bold=True,
        )

        # Point number labels (static)
        self.txt_point_labels = []
        for i in range(24):
            x, base_y, tip_y, is_top = self._point_tip_xy_static(i)
            if is_top:
                ly = BOARD_TOP + 10
            else:
                ly = BOARD_BOTTOM - 14
            self.txt_point_labels.append(
                arcade.Text(str(i + 1), x, ly, (180, 180, 180),
                            font_size=9, anchor_x="center", anchor_y="center")
            )

        # Checker count labels for stacks > 5 (dynamic, reusable pool)
        # We'll create 24 of them (one per point max)
        self.txt_checker_counts = []
        for _ in range(24):
            self.txt_checker_counts.append(
                arcade.Text("", 0, 0, arcade.color.BLACK,
                            font_size=11, anchor_x="center", anchor_y="center", bold=True)
            )

        # Dice value labels (dynamic, up to 4 dice)
        self.txt_dice = []
        for _ in range(4):
            self.txt_dice.append(
                arcade.Text("", 0, 0, arcade.color.BLACK,
                            font_size=18, anchor_x="center", anchor_y="center", bold=True)
            )

        # Status message (dynamic)
        self.txt_message = arcade.Text(
            "", WIDTH / 2, 25,
            arcade.color.WHITE, font_size=13,
            anchor_x="center", anchor_y="center",
        )

        # Game over texts (dynamic)
        self.txt_game_over_msg = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 + 15,
            arcade.color.WHITE, font_size=26,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_hint = arcade.Text(
            "Click 'New Game' to play again.",
            WIDTH / 2, HEIGHT / 2 - 25,
            arcade.color.LIGHT_GRAY, font_size=14,
            anchor_x="center", anchor_y="center",
        )

    def _point_tip_xy_static(self, point_index):
        """Static version of _point_tip_xy for use before reset_game."""
        # Duplicate logic from _point_tip_xy for Text creation in __init__
        if point_index < 6:
            col = 5 - point_index
            x = BAR_RIGHT + col * POINT_WIDTH + POINT_WIDTH // 2
            y = BOARD_BOTTOM
            tip_y = BOARD_BOTTOM + HALF_HEIGHT
            return x, y, tip_y, False
        elif point_index < 12:
            col = 11 - point_index
            x = BOARD_LEFT + col * POINT_WIDTH + POINT_WIDTH // 2
            y = BOARD_BOTTOM
            tip_y = BOARD_BOTTOM + HALF_HEIGHT
            return x, y, tip_y, False
        elif point_index < 18:
            col = point_index - 12
            x = BOARD_LEFT + col * POINT_WIDTH + POINT_WIDTH // 2
            y = BOARD_TOP
            tip_y = BOARD_TOP - HALF_HEIGHT
            return x, y, tip_y, True
        else:
            col = point_index - 18
            x = BAR_RIGHT + col * POINT_WIDTH + POINT_WIDTH // 2
            y = BOARD_TOP
            tip_y = BOARD_TOP - HALF_HEIGHT
            return x, y, tip_y, True

    def reset_game(self):
        self.board, self.bar, self.off = initial_board()
        self.dice = []
        self.used_dice = []
        self.state = STATE_PLAYER_ROLL
        self.selected_point = None  # Index of selected checker or 'bar'
        self.valid_destinations = []  # List of valid destination indices or 'off'
        self.message = "Roll the dice to start your turn."
        self.ai_timer = 0.0
        self.ai_moves_pending = []
        self.winner = None

    def on_show(self):
        arcade.set_background_color(BG_COLOR)

    def on_update(self, delta_time):
        if self.state == STATE_AI_TURN:
            self.ai_timer += delta_time
            if self.ai_timer >= 0.5:
                self._do_ai_turn()

    def _do_ai_turn(self):
        """Execute AI turn."""
        # Roll dice for AI
        self.dice = [random.randint(1, 6), random.randint(1, 6)]
        if self.dice[0] == self.dice[1]:
            self.dice = self.dice * 2

        self.message = f"AI rolled {self.dice[0]}"
        if len(self.dice) >= 2:
            self.message = f"AI rolled {self.dice[0]} and {self.dice[1]}"
            if len(self.dice) == 4:
                self.message += " (doubles!)"

        # Get AI moves
        moves = self.ai.get_moves(self.board, self.bar, self.off, self.dice, AI)
        if moves:
            self.board, self.bar, self.off = apply_moves(
                self.board, self.bar, self.off, moves, AI
            )
            move_desc = ", ".join(
                f"{self._fmt_point(m[0])}->{self._fmt_point(m[1])}" for m in moves
            )
            self.message = f"AI rolled {self.dice[0]},{self.dice[1 % len(self.dice)]} and moved: {move_desc}"
        else:
            self.message = f"AI rolled {self.dice[0]},{self.dice[1 % len(self.dice)]} but has no legal moves."

        self.dice = []
        self.ai_timer = 0.0

        # Check win
        if self.off[1] >= 15:
            self.state = STATE_GAME_OVER
            self.winner = "AI"
            self.message = "AI wins! All checkers borne off."
        else:
            self.state = STATE_PLAYER_ROLL
            self.message += " Your turn - roll the dice."

    def _fmt_point(self, p):
        if p == 'bar':
            return "Bar"
        if p == 'off':
            return "Off"
        return str(p + 1)

    def _roll_dice(self):
        self.dice = [random.randint(1, 6), random.randint(1, 6)]
        if self.dice[0] == self.dice[1]:
            self.dice = self.dice * 2
        self.used_dice = []
        self.selected_point = None
        self.valid_destinations = []

        # Check if player has any legal moves
        all_moves = get_all_legal_moves(self.board, self.bar, self.off, self.dice, PLAYER)
        if not all_moves or all_moves == [[]]:
            self.message = f"You rolled {self.dice[0]} and {self.dice[1 % len(self.dice)]} but have no legal moves."
            self.dice = []
            self.state = STATE_AI_TURN
            self.ai_timer = 0.0
        else:
            self.state = STATE_PLAYER_MOVE
            dstr = f"{self.dice[0]} and {self.dice[1 % len(self.dice)]}"
            if len(self.dice) == 4:
                dstr += " (doubles!)"
            self.message = f"You rolled {dstr}. Select a checker to move."

    def _remaining_dice(self):
        """Return list of dice values not yet used."""
        remaining = list(self.dice)
        for d in self.used_dice:
            if d in remaining:
                remaining.remove(d)
        return remaining

    def _get_valid_destinations_for(self, source):
        """Get valid destination points for a selected source, considering remaining dice."""
        remaining = self._remaining_dice()
        if not remaining:
            return []

        destinations = []
        tried_dice = set()
        for die in remaining:
            if die in tried_dice:
                continue
            tried_dice.add(die)
            moves = _single_die_moves(self.board, self.bar, self.off, die, PLAYER)
            for frm, to in moves:
                if frm == source and to not in destinations:
                    destinations.append(to)
        return destinations

    def _execute_player_move(self, frm, to):
        """Execute a player move and determine which die was used."""
        remaining = self._remaining_dice()

        # Figure out which die value was used
        if frm == 'bar':
            if to == 'off':
                die_used = None
            else:
                die_used = 24 - to  # Player enters from bar: die -> index 24-die
        elif to == 'off':
            # Bearing off: die_used = frm + 1 if exact, else might be larger
            # Try each remaining die
            die_used = None
            for d in remaining:
                target = frm - d
                if target == -1:
                    die_used = d
                    break
                elif target < -1:
                    # Overshoot - check if this is the farthest
                    if _all_in_home(self.board, self.bar, PLAYER):
                        # Check farthest
                        farthest = -1
                        for i in range(23, -1, -1):
                            if self.board[i] > 0:
                                farthest = i
                                break
                        if frm == farthest:
                            die_used = d
                            break
            if die_used is None:
                die_used = frm + 1
        else:
            die_used = frm - to

        self.board, self.bar, self.off = _apply_single_move(
            self.board, self.bar, self.off, (frm, to), PLAYER
        )
        self.used_dice.append(die_used)
        self.selected_point = None
        self.valid_destinations = []

        # Check if player wins
        if self.off[0] >= 15:
            self.state = STATE_GAME_OVER
            self.winner = "Player"
            self.message = "You win! All checkers borne off!"
            return

        # Check if more dice to use
        remaining = self._remaining_dice()
        if not remaining:
            self.message = "All dice used. AI's turn."
            self.dice = []
            self.state = STATE_AI_TURN
            self.ai_timer = 0.0
        else:
            # Check if any legal moves remain
            all_moves = get_all_legal_moves(
                self.board, self.bar, self.off, remaining, PLAYER
            )
            if not all_moves or all_moves == [[]]:
                self.message = "No more legal moves. AI's turn."
                self.dice = []
                self.state = STATE_AI_TURN
                self.ai_timer = 0.0
            else:
                self.message = f"Dice remaining: {remaining}. Select a checker."

    # ---- Coordinate helpers ----

    def _point_tip_xy(self, point_index):
        """Return (x, y) of the tip of a triangular point."""
        # Points 0-5: bottom right quadrant (player home)
        # Points 6-11: bottom left quadrant
        # Points 12-17: top left quadrant
        # Points 18-23: top right quadrant
        if point_index < 6:
            # Bottom right, index 0 is rightmost
            col = 5 - point_index
            x = BAR_RIGHT + col * POINT_WIDTH + POINT_WIDTH // 2
            y = BOARD_BOTTOM
            tip_y = BOARD_BOTTOM + HALF_HEIGHT
            return x, y, tip_y, False  # bottom points, triangle goes up
        elif point_index < 12:
            # Bottom left, index 6 is closest to bar
            col = 11 - point_index
            x = BOARD_LEFT + col * POINT_WIDTH + POINT_WIDTH // 2
            y = BOARD_BOTTOM
            tip_y = BOARD_BOTTOM + HALF_HEIGHT
            return x, y, tip_y, False
        elif point_index < 18:
            # Top left, index 12 is closest to bar
            col = point_index - 12
            x = BOARD_LEFT + col * POINT_WIDTH + POINT_WIDTH // 2
            y = BOARD_TOP
            tip_y = BOARD_TOP - HALF_HEIGHT
            return x, y, tip_y, True  # top points, triangle goes down
        else:
            # Top right, index 18 is closest to bar
            col = point_index - 18
            x = BAR_RIGHT + col * POINT_WIDTH + POINT_WIDTH // 2
            y = BOARD_TOP
            tip_y = BOARD_TOP - HALF_HEIGHT
            return x, y, tip_y, True

    def _checker_xy(self, point_index, stack_pos):
        """Return (x, y) for a checker at a point, stacked at position stack_pos (0=base)."""
        x, base_y, tip_y, is_top = self._point_tip_xy(point_index)
        if is_top:
            y = base_y - CHECKER_RADIUS - stack_pos * CHECKER_STACK_OFFSET
        else:
            y = base_y + CHECKER_RADIUS + stack_pos * CHECKER_STACK_OFFSET
        return x, y

    def _point_from_xy(self, mx, my):
        """Determine which point index (0-23) was clicked, or 'bar', 'off', or None."""
        # Check bar area
        if BAR_LEFT <= mx <= BAR_RIGHT:
            if BOARD_BOTTOM <= my <= BOARD_BOTTOM + HALF_HEIGHT:
                return 'bar'  # Player bar is bottom
            if BOARD_TOP - HALF_HEIGHT <= my <= BOARD_TOP:
                return 'bar'  # Could be relevant
            return None

        # Check bottom points (0-11)
        if BOARD_BOTTOM <= my <= BOARD_BOTTOM + HALF_HEIGHT:
            # Right side (0-5)
            if BAR_RIGHT <= mx <= BOARD_RIGHT:
                col = int((mx - BAR_RIGHT) / POINT_WIDTH)
                col = max(0, min(5, col))
                return 5 - col
            # Left side (6-11)
            if BOARD_LEFT <= mx <= BAR_LEFT:
                col = int((mx - BOARD_LEFT) / POINT_WIDTH)
                col = max(0, min(5, col))
                return 11 - col

        # Check top points (12-23)
        if BOARD_TOP - HALF_HEIGHT <= my <= BOARD_TOP:
            # Left side (12-17)
            if BOARD_LEFT <= mx <= BAR_LEFT:
                col = int((mx - BOARD_LEFT) / POINT_WIDTH)
                col = max(0, min(5, col))
                return 12 + col
            # Right side (18-23)
            if BAR_RIGHT <= mx <= BOARD_RIGHT:
                col = int((mx - BAR_RIGHT) / POINT_WIDTH)
                col = max(0, min(5, col))
                return 18 + col

        # Check bearing off areas (right edge)
        if mx > BOARD_RIGHT - 30:
            return 'off'

        return None

    # ---- Drawing ----

    def on_draw(self):
        self.clear()
        from renderers import backgammon_renderer
        backgammon_renderer.draw(self)

    # ---- Input ----

    def _hit_rect(self, mx, my, cx, cy, w, h):
        return (cx - w / 2 <= mx <= cx + w / 2) and (cy - h / 2 <= my <= cy + h / 2)

    def on_mouse_press(self, x, y, button, modifiers):
        # Back button
        if self._hit_rect(x, y, 55, HEIGHT - 20, 90, 30):
            self.window.show_view(self.menu_view)
            return

        # Help button
        if self._hit_rect(x, y, WIDTH - 135, HEIGHT - 20, 40, 30):
            rules_view = RulesView("Backgammon", "backgammon.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        # New Game button
        if self._hit_rect(x, y, WIDTH - 65, HEIGHT - 20, 110, 30):
            self.reset_game()
            return

        if self.state == STATE_GAME_OVER:
            return

        # Roll Dice button
        if self.state == STATE_PLAYER_ROLL:
            if self._hit_rect(x, y, WIDTH / 2, HEIGHT - 50, 120, 32):
                self._roll_dice()
            return

        if self.state == STATE_PLAYER_MOVE:
            self._handle_player_click(x, y)

    def _handle_player_click(self, x, y):
        """Handle click during player move phase."""
        clicked = self._point_from_xy(x, y)

        # If clicking a valid destination while a checker is selected
        if self.selected_point is not None and clicked in self.valid_destinations:
            self._execute_player_move(self.selected_point, clicked)
            return

        # Check if clicking on the bearing off area
        if clicked == 'off' and self.selected_point is not None:
            if 'off' in self.valid_destinations:
                self._execute_player_move(self.selected_point, 'off')
                return

        # Select a checker
        if clicked == 'bar':
            if self.bar[0] > 0:
                self.selected_point = 'bar'
                self.valid_destinations = self._get_valid_destinations_for('bar')
                if self.valid_destinations:
                    self.message = "Select a destination (highlighted in green)."
                else:
                    self.selected_point = None
                    self.message = "No valid moves from bar with remaining dice."
            return

        if clicked is not None and clicked != 'off':
            # Must enter from bar first
            if self.bar[0] > 0:
                self.message = "You must enter from the bar first! Click the bar."
                self.selected_point = None
                self.valid_destinations = []
                return

            if isinstance(clicked, int) and 0 <= clicked < 24 and self.board[clicked] > 0:
                self.selected_point = clicked
                self.valid_destinations = self._get_valid_destinations_for(clicked)
                if self.valid_destinations:
                    self.message = f"Point {clicked + 1} selected. Click a destination."
                else:
                    self.selected_point = None
                    self.valid_destinations = []
                    self.message = "No valid moves from that point. Try another."
            else:
                self.selected_point = None
                self.valid_destinations = []


# Allow running standalone for testing
if __name__ == "__main__":
    window = arcade.Window(WIDTH, HEIGHT, "Backgammon")

    class DummyMenu(arcade.View):
        def __init__(self):
            super().__init__()
            self.txt_placeholder = arcade.Text(
                "Menu (placeholder)", WIDTH / 2, HEIGHT / 2,
                arcade.color.WHITE, 20, anchor_x="center")

        def on_draw(self):
            self.clear()
            self.txt_placeholder.draw()

    menu = DummyMenu()
    game = BackgammonView(menu)
    window.show_view(game)
    arcade.run()
