import arcade
import random
from pages.rules import RulesView
from renderers import ricochet_robots_renderer
from renderers.ricochet_robots_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT, CELL_SIZE,
    GRID_ORIGIN_X, GRID_ORIGIN_Y, GRID_SIZE,
    PLAYING, WON,
    COLOR_RED, COLOR_BLUE, COLOR_GREEN, COLOR_YELLOW,
)


ROBOT_COLORS = [COLOR_RED, COLOR_BLUE, COLOR_GREEN, COLOR_YELLOW]
ROBOT_NAMES = ["Red", "Blue", "Green", "Yellow"]
DIRECTIONS = {'UP': (1, 0), 'DOWN': (-1, 0), 'LEFT': (0, -1), 'RIGHT': (0, 1)}


class RicochetRobotsView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self._create_texts()
        self._init_game()

    def _create_texts(self):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        self.txt_back = arcade.Text(
            "Back", 55, bar_y, arcade.color.WHITE,
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
        self.txt_reset = arcade.Text(
            "Reset", WIDTH - 200, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_moves = arcade.Text(
            "", 250, bar_y, arcade.color.YELLOW,
            font_size=16, anchor_x="center", anchor_y="center",
        )
        self.txt_target_info = arcade.Text(
            "", 420, bar_y, arcade.color.YELLOW,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_selected = arcade.Text(
            "", WIDTH / 2, 20, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_you_win = arcade.Text(
            "TARGET REACHED!", WIDTH / 2, HEIGHT / 2 + 10,
            arcade.color.YELLOW, font_size=36,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_info = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 - 30,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )

    def _init_game(self):
        """Generate a random puzzle."""
        self.game_state = PLAYING
        self.moves = 0
        self.selected_robot = None

        # Walls: set of ((row, col), side) where side is 'N','S','E','W'
        # A wall on the north side of (r,c) means there's a wall between (r,c) and (r+1,c)
        self.walls = set()

        # Add border walls
        for i in range(GRID_SIZE):
            self.walls.add(((0, i), 'S'))
            self.walls.add(((GRID_SIZE - 1, i), 'N'))
            self.walls.add(((i, 0), 'W'))
            self.walls.add(((i, GRID_SIZE - 1), 'E'))

        # Add random internal walls (L-shaped wall segments)
        num_wall_pairs = random.randint(12, 18)
        for _ in range(num_wall_pairs):
            r = random.randint(1, GRID_SIZE - 2)
            c = random.randint(1, GRID_SIZE - 2)
            # Random L-shape orientation
            orient = random.choice(['NE', 'NW', 'SE', 'SW'])
            if orient == 'NE':
                self.walls.add(((r, c), 'N'))
                self.walls.add(((r + 1, c), 'S'))
                self.walls.add(((r, c), 'E'))
                self.walls.add(((r, c + 1), 'W'))
            elif orient == 'NW':
                self.walls.add(((r, c), 'N'))
                self.walls.add(((r + 1, c), 'S'))
                self.walls.add(((r, c), 'W'))
                self.walls.add(((r, c - 1), 'E'))
            elif orient == 'SE':
                self.walls.add(((r, c), 'S'))
                self.walls.add(((r - 1, c), 'N'))
                self.walls.add(((r, c), 'E'))
                self.walls.add(((r, c + 1), 'W'))
            elif orient == 'SW':
                self.walls.add(((r, c), 'S'))
                self.walls.add(((r - 1, c), 'N'))
                self.walls.add(((r, c), 'W'))
                self.walls.add(((r, c - 1), 'E'))

        # Place 4 robots at random non-overlapping positions
        positions = set()
        self.robots = []
        for i in range(4):
            while True:
                r = random.randint(0, GRID_SIZE - 1)
                c = random.randint(0, GRID_SIZE - 1)
                # Avoid center 2x2
                if (r in (7, 8) and c in (7, 8)):
                    continue
                if (r, c) not in positions:
                    positions.add((r, c))
                    self.robots.append({'row': r, 'col': c, 'color': ROBOT_COLORS[i], 'name': ROBOT_NAMES[i]})
                    break

        # Target: random cell for a random robot
        self.target_robot = random.randint(0, 3)
        while True:
            tr = random.randint(0, GRID_SIZE - 1)
            tc = random.randint(0, GRID_SIZE - 1)
            if (tr, tc) not in positions and not (tr in (7, 8) and tc in (7, 8)):
                self.target = (tr, tc)
                break

        # Save initial positions for reset
        self.initial_robots = [{'row': r['row'], 'col': r['col'], 'color': r['color'], 'name': r['name']} for r in self.robots]

    def _reset_puzzle(self):
        """Reset robots to initial positions."""
        self.robots = [{'row': r['row'], 'col': r['col'], 'color': r['color'], 'name': r['name']} for r in self.initial_robots]
        self.moves = 0
        self.game_state = PLAYING
        self.selected_robot = None

    def _get_robot_positions(self):
        """Return set of (row, col) for all robots."""
        return {(r['row'], r['col']) for r in self.robots}

    def _has_wall(self, row, col, direction):
        """Check if there's a wall on the given side of cell (row, col)."""
        return ((row, col), direction) in self.walls

    def _slide_robot(self, robot_idx, direction):
        """Slide a robot in the given direction until it hits a wall or robot."""
        robot = self.robots[robot_idx]
        dr, dc = DIRECTIONS[direction]
        robot_positions = self._get_robot_positions()
        robot_positions.discard((robot['row'], robot['col']))

        r, c = robot['row'], robot['col']
        moved = False

        while True:
            # Check wall on current cell's exit side
            if direction == 'UP' and self._has_wall(r, c, 'N'):
                break
            if direction == 'DOWN' and self._has_wall(r, c, 'S'):
                break
            if direction == 'LEFT' and self._has_wall(r, c, 'W'):
                break
            if direction == 'RIGHT' and self._has_wall(r, c, 'E'):
                break

            nr, nc = r + dr, c + dc

            # Check bounds
            if nr < 0 or nr >= GRID_SIZE or nc < 0 or nc >= GRID_SIZE:
                break

            # Check if another robot is there
            if (nr, nc) in robot_positions:
                break

            r, c = nr, nc
            moved = True

        if moved:
            robot['row'] = r
            robot['col'] = c
            self.moves += 1
            self._check_win()

    def _check_win(self):
        """Check if target robot is on target cell."""
        robot = self.robots[self.target_robot]
        if (robot['row'], robot['col']) == self.target:
            self.game_state = WON

    def _pixel_to_grid(self, x, y):
        col = int((x - GRID_ORIGIN_X) // CELL_SIZE)
        row = int((y - GRID_ORIGIN_Y) // CELL_SIZE)
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            return row, col
        return None

    def _robot_at(self, row, col):
        for i, robot in enumerate(self.robots):
            if robot['row'] == row and robot['col'] == col:
                return i
        return None

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def on_draw(self):
        self.clear()
        ricochet_robots_renderer.draw(self)

    def on_mouse_press(self, x, y, button, modifiers):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        if self._hit_test_button(x, y, 55, bar_y, 90, 35):
            self.window.show_view(self.menu_view)
            return

        if self._hit_test_button(x, y, WIDTH - 65, bar_y, 110, 35):
            self._init_game()
            return

        if self._hit_test_button(x, y, WIDTH - 135, bar_y, 40, 35):
            rules_view = RulesView("Ricochet Robots", "ricochet_robots.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self._hit_test_button(x, y, WIDTH - 200, bar_y, 70, 35):
            self._reset_puzzle()
            return

        if self.game_state != PLAYING:
            return

        result = self._pixel_to_grid(x, y)
        if result is None:
            return
        row, col = result

        robot_idx = self._robot_at(row, col)
        if robot_idx is not None:
            self.selected_robot = robot_idx
        elif self.selected_robot is not None:
            # Click on empty cell: determine direction from selected robot
            robot = self.robots[self.selected_robot]
            dr = row - robot['row']
            dc = col - robot['col']
            if abs(dr) > abs(dc):
                direction = 'UP' if dr > 0 else 'DOWN'
            elif abs(dc) > abs(dr):
                direction = 'RIGHT' if dc > 0 else 'LEFT'
            else:
                return
            self._slide_robot(self.selected_robot, direction)

    def on_key_press(self, key, modifiers):
        if self.game_state != PLAYING or self.selected_robot is None:
            return

        if key == arcade.key.UP:
            self._slide_robot(self.selected_robot, 'UP')
        elif key == arcade.key.DOWN:
            self._slide_robot(self.selected_robot, 'DOWN')
        elif key == arcade.key.LEFT:
            self._slide_robot(self.selected_robot, 'LEFT')
        elif key == arcade.key.RIGHT:
            self._slide_robot(self.selected_robot, 'RIGHT')
