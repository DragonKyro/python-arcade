import arcade
from pages.rules import RulesView
from renderers import laser_maze_renderer
from renderers.laser_maze_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT, CELL_SIZE,
    PLAYING, WON,
    EMPTY_CELL, WALL, MIRROR_NE, MIRROR_NW, LASER_SRC, TARGET, SPLITTER,
    DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT,
    grid_metrics, cell_center,
)

# Puzzles: (grid, laser_pos, laser_dir, movable_mirrors)
# grid values: 0=empty, 1=wall, 2=mirror_NE(/), 3=mirror_NW(\), 4=laser, 5=target, 6=splitter
# movable_mirrors: set of (r, c) that the player can rotate
PUZZLES = [
    # Puzzle 1: simple reflection (7x7)
    {
        "rows": 5, "cols": 7,
        "grid": [
            [0, 0, 0, 0, 0, 0, 0],
            [4, 0, 0, 2, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 5, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ],
        "laser_pos": (1, 0), "laser_dir": DIR_RIGHT,
        "movable": {(1, 3)},
    },
    # Puzzle 2: two mirrors
    {
        "rows": 6, "cols": 7,
        "grid": [
            [0, 0, 0, 0, 0, 0, 0],
            [4, 0, 0, 0, 2, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 3, 0, 0, 0, 5],
            [0, 0, 0, 0, 0, 0, 0],
        ],
        "laser_pos": (1, 0), "laser_dir": DIR_RIGHT,
        "movable": {(1, 4), (4, 2)},
    },
    # Puzzle 3: walls and mirrors
    {
        "rows": 6, "cols": 7,
        "grid": [
            [0, 0, 0, 0, 0, 0, 0],
            [4, 0, 1, 0, 3, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 2, 0, 0, 1, 0, 5],
            [0, 0, 0, 0, 0, 0, 0],
        ],
        "laser_pos": (1, 0), "laser_dir": DIR_RIGHT,
        "movable": {(1, 4), (4, 1)},
    },
    # Puzzle 4: multiple targets
    {
        "rows": 7, "cols": 7,
        "grid": [
            [0, 0, 0, 0, 0, 0, 0],
            [4, 0, 0, 2, 0, 0, 5],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 3, 0, 2, 0, 0],
            [5, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ],
        "laser_pos": (1, 0), "laser_dir": DIR_RIGHT,
        "movable": {(1, 3), (4, 2), (4, 4)},
    },
    # Puzzle 5: complex with walls
    {
        "rows": 7, "cols": 8,
        "grid": [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 4, 0, 0, 2, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 3, 0, 5],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 5, 0, 0, 2, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ],
        "laser_pos": (1, 1), "laser_dir": DIR_RIGHT,
        "movable": {(1, 4), (3, 5), (5, 4)},
    },
    # Puzzle 6: with splitter
    {
        "rows": 7, "cols": 7,
        "grid": [
            [0, 0, 0, 0, 0, 0, 0],
            [4, 0, 0, 6, 0, 0, 5],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 5, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ],
        "laser_pos": (1, 0), "laser_dir": DIR_RIGHT,
        "movable": set(),
    },
]


class LaserMazeView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.puzzle_index = 0
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
            "PUZZLE COMPLETE!", WIDTH / 2, HEIGHT / 2 + 20,
            arcade.color.YELLOW, font_size=40,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_details = arcade.Text(
            "Click 'New Game' for next puzzle", WIDTH / 2, HEIGHT / 2 - 25,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )

    def _init_game(self):
        puzzle = PUZZLES[self.puzzle_index % len(PUZZLES)]
        self.grid_rows = puzzle["rows"]
        self.grid_cols = puzzle["cols"]
        self.grid = [row[:] for row in puzzle["grid"]]
        self.laser_pos = puzzle["laser_pos"]
        self.laser_dir = puzzle["laser_dir"]
        self.movable = set(puzzle["movable"])
        self.game_state = PLAYING

        # Find all target positions
        self.target_positions = set()
        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                if self.grid[r][c] == TARGET:
                    self.target_positions.add((r, c))

        self.hit_targets = set()
        self.beam_segments = []
        self._trace_laser()
        self.txt_info.text = f"Puzzle {self.puzzle_index + 1}/{len(PUZZLES)}  Targets: {len(self.hit_targets)}/{len(self.target_positions)}"

    def _trace_laser(self):
        """Trace the laser beam from source, reflecting off mirrors."""
        self.beam_segments = []
        self.hit_targets = set()

        # BFS-like trace supporting splitters
        # Each beam: (row, col, direction)
        beams = [(self.laser_pos[0], self.laser_pos[1], self.laser_dir)]
        visited = set()
        max_steps = 200

        step = 0
        while beams and step < max_steps:
            step += 1
            new_beams = []
            for br, bc, bdir in beams:
                # Move one step in direction
                dr, dc = 0, 0
                if bdir == DIR_UP:
                    dr = -1
                elif bdir == DIR_DOWN:
                    dr = 1
                elif bdir == DIR_LEFT:
                    dc = -1
                elif bdir == DIR_RIGHT:
                    dc = 1

                nr, nc = br + dr, bc + dc
                if nr < 0 or nr >= self.grid_rows or nc < 0 or nc >= self.grid_cols:
                    continue

                state_key = (nr, nc, bdir)
                if state_key in visited:
                    continue
                visited.add(state_key)

                cell = self.grid[nr][nc]

                if cell == WALL:
                    continue  # blocked

                self.beam_segments.append(((br, bc), (nr, nc)))

                if cell == TARGET:
                    self.hit_targets.add((nr, nc))
                    # Beam continues through target
                    new_beams.append((nr, nc, bdir))
                elif cell == MIRROR_NE:  # /
                    new_dir = {
                        DIR_RIGHT: DIR_UP,
                        DIR_UP: DIR_RIGHT,
                        DIR_LEFT: DIR_DOWN,
                        DIR_DOWN: DIR_LEFT,
                    }[bdir]
                    new_beams.append((nr, nc, new_dir))
                elif cell == MIRROR_NW:  # backslash
                    new_dir = {
                        DIR_RIGHT: DIR_DOWN,
                        DIR_DOWN: DIR_RIGHT,
                        DIR_LEFT: DIR_UP,
                        DIR_UP: DIR_LEFT,
                    }[bdir]
                    new_beams.append((nr, nc, new_dir))
                elif cell == SPLITTER:
                    # Split into / and \ reflections
                    dir_ne = {
                        DIR_RIGHT: DIR_UP, DIR_UP: DIR_RIGHT,
                        DIR_LEFT: DIR_DOWN, DIR_DOWN: DIR_LEFT,
                    }[bdir]
                    dir_nw = {
                        DIR_RIGHT: DIR_DOWN, DIR_DOWN: DIR_RIGHT,
                        DIR_LEFT: DIR_UP, DIR_UP: DIR_LEFT,
                    }[bdir]
                    new_beams.append((nr, nc, dir_ne))
                    new_beams.append((nr, nc, dir_nw))
                else:
                    # Empty or laser source — beam continues
                    new_beams.append((nr, nc, bdir))

            beams = new_beams

        self._check_win()

    def _rotate_mirror(self, r, c):
        """Rotate a mirror 90 degrees: NE->NW->NE..."""
        cell = self.grid[r][c]
        if cell == MIRROR_NE:
            self.grid[r][c] = MIRROR_NW
        elif cell == MIRROR_NW:
            self.grid[r][c] = MIRROR_NE

    def _check_win(self):
        if self.hit_targets == self.target_positions and len(self.target_positions) > 0:
            self.game_state = WON

    def _pixel_to_grid(self, x, y):
        gw, gh, ox, oy = grid_metrics(self.grid_rows, self.grid_cols)
        col = int((x - ox) / CELL_SIZE)
        row_visual = int((y - oy) / CELL_SIZE)
        row = (self.grid_rows - 1) - row_visual
        if 0 <= row < self.grid_rows and 0 <= col < self.grid_cols:
            return row, col
        return None

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def on_draw(self):
        self.clear()
        laser_maze_renderer.draw(self)

    def on_mouse_press(self, x, y, button, modifiers):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        if self._hit_test_button(x, y, 55, bar_y, 90, 35):
            self.window.show_view(self.menu_view)
            return
        if self._hit_test_button(x, y, WIDTH - 65, bar_y, 110, 35):
            if self.game_state == WON:
                self.puzzle_index = (self.puzzle_index + 1) % len(PUZZLES)
            self._init_game()
            return
        if self._hit_test_button(x, y, WIDTH - 135, bar_y, 40, 35):
            rules_view = RulesView(
                "Laser Maze", "laser_maze.txt", None,
                self.menu_view, existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        if self.game_state != PLAYING:
            return

        result = self._pixel_to_grid(x, y)
        if result is None:
            return
        r, c = result

        # Click on a movable mirror to rotate it
        if (r, c) in self.movable:
            cell = self.grid[r][c]
            if cell in (MIRROR_NE, MIRROR_NW):
                self._rotate_mirror(r, c)
                self.game_state = PLAYING  # reset in case checking
                self.hit_targets = set()
                self._trace_laser()
                self.txt_info.text = f"Puzzle {self.puzzle_index + 1}/{len(PUZZLES)}  Targets: {len(self.hit_targets)}/{len(self.target_positions)}"
