import arcade
from pages.rules import RulesView
from renderers import bloxorz_renderer
from renderers.bloxorz_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT,
    PLAYING, WON, FALLEN,
    EMPTY, NORMAL, FRAGILE, GOAL,
    STANDING, LYING_X, LYING_Z,
)

# Levels: (board_2d, start_pos, goal_pos)
# 0=empty, 1=normal, 2=fragile, 3=goal
LEVELS = [
    # Level 1: simple bridge
    {
        "board": [
            [1, 1, 1, 0, 0, 0],
            [1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1],
            [0, 0, 0, 1, 1, 3],
        ],
        "start": (0, 0),
    },
    # Level 2: L-shape
    {
        "board": [
            [1, 1, 1, 1, 0, 0, 0],
            [1, 1, 1, 1, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 1, 1, 1, 0],
            [0, 0, 0, 1, 1, 3, 0],
        ],
        "start": (0, 0),
    },
    # Level 3: with fragile tiles
    {
        "board": [
            [1, 1, 1, 0, 0, 0, 0],
            [1, 1, 1, 2, 1, 0, 0],
            [0, 0, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 1, 1, 1],
            [0, 0, 0, 0, 0, 1, 3],
        ],
        "start": (0, 0),
    },
    # Level 4: wider with fragile center
    {
        "board": [
            [1, 1, 1, 1, 1, 0, 0, 0],
            [0, 1, 1, 1, 1, 0, 0, 0],
            [0, 0, 1, 2, 1, 1, 1, 0],
            [0, 0, 0, 1, 2, 1, 1, 0],
            [0, 0, 0, 0, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 0, 1, 3],
        ],
        "start": (0, 0),
    },
    # Level 5: complex path
    {
        "board": [
            [0, 0, 1, 1, 1, 0, 0],
            [1, 1, 1, 1, 1, 0, 0],
            [1, 1, 1, 0, 1, 1, 1],
            [1, 1, 0, 0, 2, 1, 1],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 3, 0, 0],
        ],
        "start": (0, 2),
    },
    # Level 6: tricky fragile
    {
        "board": [
            [1, 1, 0, 0, 0, 0, 0, 0],
            [1, 1, 1, 1, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 0, 0, 0],
            [0, 0, 2, 1, 1, 1, 0, 0],
            [0, 0, 0, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 2, 1, 1, 1],
            [0, 0, 0, 0, 0, 0, 1, 3],
        ],
        "start": (0, 0),
    },
]


def _find_goal(board):
    for r, row in enumerate(board):
        for c, val in enumerate(row):
            if val == GOAL:
                return (r, c)
    return None


class BloxorzView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.level_index = 0
        self._create_texts()
        self._init_game()

    def _create_texts(self):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
        self.txt_back = arcade.Text(
            "Back", 55, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_info = arcade.Text(
            "", WIDTH / 2, bar_y, arcade.color.YELLOW,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_new_game = arcade.Text(
            "New Game", WIDTH - 65, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_help = arcade.Text(
            "?", WIDTH - 135, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_you_win = arcade.Text(
            "LEVEL COMPLETE!", WIDTH / 2, HEIGHT / 2 + 20,
            arcade.color.YELLOW, font_size=40,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_details = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 - 25,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )
        self.txt_fallen = arcade.Text(
            "FELL OFF!", WIDTH / 2, HEIGHT / 2 + 20,
            arcade.color.RED, font_size=40,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_fallen_hint = arcade.Text(
            "Press any key to retry", WIDTH / 2, HEIGHT / 2 - 25,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )

    def _init_game(self):
        level = LEVELS[self.level_index % len(LEVELS)]
        self.board = [row[:] for row in level["board"]]
        self.block_pos = level["start"]
        self.block_state = STANDING
        self.goal_pos = _find_goal(self.board)
        self.move_count = 0
        self.game_state = PLAYING
        self.txt_info.text = f"Level {self.level_index + 1}/{len(LEVELS)}  Moves: 0"

    def _get_occupied_cells(self, pos, state):
        """Return list of (row, col) cells the block occupies."""
        r, c = pos
        if state == STANDING:
            return [(r, c)]
        elif state == LYING_X:
            return [(r, c), (r, c + 1)]
        elif state == LYING_Z:
            return [(r, c), (r + 1, c)]
        return []

    def _is_valid_position(self, pos, state):
        """Check if block position is on the board."""
        cells = self._get_occupied_cells(pos, state)
        rows = len(self.board)
        for r, c in cells:
            if r < 0 or r >= rows:
                return False
            cols = len(self.board[r])
            if c < 0 or c >= cols:
                return False
            if self.board[r][c] == EMPTY:
                return False
        return True

    def _check_fragile(self, pos, state):
        """Check if standing on a fragile tile (not allowed when standing)."""
        if state != STANDING:
            return True
        r, c = pos
        return self.board[r][c] != FRAGILE

    def _move_block(self, direction):
        """Move the block in a direction. Returns True if move was valid."""
        if self.game_state != PLAYING:
            return False

        r, c = self.block_pos
        st = self.block_state
        new_pos = None
        new_state = None

        if direction == "up":  # decrease row
            if st == STANDING:
                new_pos = (r - 2, c)
                new_state = LYING_Z
            elif st == LYING_X:
                new_pos = (r - 1, c)
                new_state = LYING_X
            elif st == LYING_Z:
                new_pos = (r - 1, c)
                new_state = STANDING
        elif direction == "down":  # increase row
            if st == STANDING:
                new_pos = (r + 1, c)
                new_state = LYING_Z
            elif st == LYING_X:
                new_pos = (r + 1, c)
                new_state = LYING_X
            elif st == LYING_Z:
                new_pos = (r + 2, c)
                new_state = STANDING
        elif direction == "left":  # decrease col
            if st == STANDING:
                new_pos = (r, c - 2)
                new_state = LYING_X
            elif st == LYING_X:
                new_pos = (r, c - 1)
                new_state = STANDING
            elif st == LYING_Z:
                new_pos = (r, c - 1)
                new_state = LYING_Z
        elif direction == "right":  # increase col
            if st == STANDING:
                new_pos = (r, c + 1)
                new_state = LYING_X
            elif st == LYING_X:
                new_pos = (r, c + 2)
                new_state = STANDING
            elif st == LYING_Z:
                new_pos = (r, c + 1)
                new_state = LYING_Z

        if new_pos is None:
            return False

        if not self._is_valid_position(new_pos, new_state):
            self.game_state = FALLEN
            return True

        if not self._check_fragile(new_pos, new_state):
            self.game_state = FALLEN
            return True

        self.block_pos = new_pos
        self.block_state = new_state
        self.move_count += 1
        self.txt_info.text = f"Level {self.level_index + 1}/{len(LEVELS)}  Moves: {self.move_count}"

        # Check win: standing on goal
        if self.block_state == STANDING and self.block_pos == self.goal_pos:
            self.game_state = WON
            self.txt_win_details.text = f"Solved in {self.move_count} moves!"

        return True

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def on_draw(self):
        self.clear()
        bloxorz_renderer.draw(self)

    def on_key_press(self, key, modifiers):
        if self.game_state == FALLEN:
            self._init_game()
            return

        if self.game_state == WON:
            return

        if key == arcade.key.UP:
            self._move_block("up")
        elif key == arcade.key.DOWN:
            self._move_block("down")
        elif key == arcade.key.LEFT:
            self._move_block("left")
        elif key == arcade.key.RIGHT:
            self._move_block("right")
        elif key == arcade.key.R:
            self._init_game()

    def on_mouse_press(self, x, y, button, modifiers):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        if self._hit_test_button(x, y, 55, bar_y, 90, 35):
            self.window.show_view(self.menu_view)
            return
        if self._hit_test_button(x, y, WIDTH - 65, bar_y, 110, 35):
            if self.game_state == WON:
                self.level_index = (self.level_index + 1) % len(LEVELS)
            self._init_game()
            return
        if self._hit_test_button(x, y, WIDTH - 135, bar_y, 40, 35):
            rules_view = RulesView(
                "Bloxorz", "bloxorz.txt", None,
                self.menu_view, existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return
