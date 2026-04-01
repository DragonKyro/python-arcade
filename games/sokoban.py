import arcade
import copy
from pages.rules import RulesView
from renderers import sokoban_renderer
from renderers.sokoban_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT, PLAYING, WON,
    FLOOR, WALL, GOAL,
)


# Level format: # = wall, . = goal, @ = player, $ = box, * = box on goal, + = player on goal, space = floor
# Each level is a list of strings.
LEVEL_DATA = [
    # Level 1 - simple intro
    [
        "  ####  ",
        "###  ###",
        "#  $   #",
        "# .@$. #",
        "#  $   #",
        "###  ###",
        "  ####  ",
    ],
    # Level 2
    [
        "######  ",
        "#    ## ",
        "# ## .##",
        "#   $  #",
        "##$ .$ #",
        " #  ## #",
        " # @   #",
        " #######",
    ],
    # Level 3
    [
        "  ######",
        "  #    #",
        "### $# #",
        "# . $  #",
        "# .#$###",
        "# .  #  ",
        "#  @##  ",
        "#####   ",
    ],
    # Level 4
    [
        "########",
        "#      #",
        "# #### #",
        "# #..# #",
        "# $  $ #",
        "##$ $# #",
        " # @   #",
        " #######",
    ],
    # Level 5
    [
        " ####   ",
        "##  ### ",
        "#   $.##",
        "# #$.  #",
        "#  $.# #",
        "##$. @ #",
        " #   ###",
        " #####  ",
    ],
    # Level 6
    [
        "  ##### ",
        "###   # ",
        "#  $# ##",
        "# #  $ #",
        "# . .#@#",
        "##.$ $ #",
        " # #   #",
        " # ...##",
        " ##$$##",
        "  #  # ",
        "  #### ",
    ],
    # Level 7
    [
        " ###### ",
        "##    ##",
        "#  ##  #",
        "# $..$ #",
        "#  ..  #",
        "##$..$ #",
        " # ## ##",
        " # @  # ",
        " ###### ",
    ],
]


def _parse_level(strings):
    """Parse a level from string format into grid, player_pos, boxes, goals."""
    max_w = max(len(s) for s in strings)
    grid = []
    player_pos = None
    boxes = set()
    goals = set()

    for r, line in enumerate(strings):
        row = []
        for c in range(max_w):
            ch = line[c] if c < len(line) else ' '
            if ch == '#':
                row.append(WALL)
            elif ch == '.':
                row.append(GOAL)
                goals.add((r, c))
            elif ch == '@':
                row.append(FLOOR)
                player_pos = (r, c)
            elif ch == '$':
                row.append(FLOOR)
                boxes.add((r, c))
            elif ch == '*':
                row.append(GOAL)
                boxes.add((r, c))
                goals.add((r, c))
            elif ch == '+':
                row.append(GOAL)
                player_pos = (r, c)
                goals.add((r, c))
            else:
                row.append(FLOOR)
        grid.append(row)

    return {
        "grid": grid,
        "player_start": player_pos,
        "boxes_start": frozenset(boxes),
        "goals": frozenset(goals),
    }


class SokobanView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.levels = [_parse_level(ld) for ld in LEVEL_DATA]
        self.level_index = 0
        self._create_texts()
        self._init_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        self.txt_back = arcade.Text(
            "Back", 55, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_moves = arcade.Text(
            "", 200, bar_y, arcade.color.YELLOW,
            font_size=16, anchor_x="center", anchor_y="center",
        )
        self.txt_level = arcade.Text(
            "", 340, bar_y, arcade.color.LIGHT_GRAY,
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
        self.txt_undo_hint = arcade.Text(
            "Z = Undo", WIDTH - 220, bar_y, arcade.color.LIGHT_GRAY,
            font_size=11, anchor_x="center", anchor_y="center",
        )

        self.txt_you_win = arcade.Text(
            "LEVEL COMPLETE!", WIDTH / 2, HEIGHT / 2 + 20,
            arcade.color.YELLOW, font_size=40,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_details = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 - 25,
            arcade.color.WHITE, font_size=18,
            anchor_x="center", anchor_y="center",
        )
        self.txt_next_level = arcade.Text(
            "Next Level", WIDTH / 2, HEIGHT / 2 - 70,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )

    def current_level(self):
        return self.levels[self.level_index]

    def _init_game(self):
        """Initialize or reset state for the current level."""
        level = self.current_level()
        self.player_pos = level["player_start"]
        self.boxes = set(level["boxes_start"])
        self.move_count = 0
        self.game_state = PLAYING
        self.history = []  # list of (player_pos, boxes_copy) for undo

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def _move(self, dr, dc):
        """Try to move player by (dr, dc). Push box if possible."""
        if self.game_state != PLAYING:
            return

        pr, pc = self.player_pos
        nr, nc = pr + dr, pc + dc
        level = self.current_level()
        grid = level["grid"]
        h = len(grid)
        w = len(grid[0])

        # Bounds check
        if nr < 0 or nr >= h or nc < 0 or nc >= w:
            return
        # Wall check
        if grid[nr][nc] == WALL:
            return

        # Save state for undo before moving
        old_state = (self.player_pos, frozenset(self.boxes))

        if (nr, nc) in self.boxes:
            # Try to push box
            br, bc = nr + dr, nc + dc
            if br < 0 or br >= h or bc < 0 or bc >= w:
                return
            if grid[br][bc] == WALL:
                return
            if (br, bc) in self.boxes:
                return
            # Push the box
            self.boxes.remove((nr, nc))
            self.boxes.add((br, bc))

        self.history.append(old_state)
        self.player_pos = (nr, nc)
        self.move_count += 1
        self._check_win()

    def _undo(self):
        """Undo the last move."""
        if not self.history or self.game_state != PLAYING:
            return
        self.player_pos, boxes_frozen = self.history.pop()
        self.boxes = set(boxes_frozen)
        self.move_count = max(0, self.move_count - 1)

    def _check_win(self):
        """All boxes must be on goal squares."""
        goals = self.current_level()["goals"]
        if self.boxes == set(goals):
            self.game_state = WON

    def on_draw(self):
        self.clear()
        sokoban_renderer.draw(self)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self._move(-1, 0)
        elif key == arcade.key.DOWN:
            self._move(1, 0)
        elif key == arcade.key.LEFT:
            self._move(0, -1)
        elif key == arcade.key.RIGHT:
            self._move(0, 1)
        elif key == arcade.key.Z:
            self._undo()

    def on_mouse_press(self, x, y, button, modifiers):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        # Back button
        if self._hit_test_button(x, y, 55, bar_y, 90, 35):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if self._hit_test_button(x, y, WIDTH - 65, bar_y, 110, 35):
            self._init_game()
            return

        # Help button
        if self._hit_test_button(x, y, WIDTH - 135, bar_y, 40, 35):
            rules_view = RulesView(
                "Sokoban", "sokoban.txt", None,
                self.menu_view, existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        # Next level button (when won)
        if self.game_state == WON and self.level_index < len(self.levels) - 1:
            if self._hit_test_button(x, y, WIDTH / 2, HEIGHT / 2 - 70, 160, 40):
                self.level_index += 1
                self._init_game()
                return
