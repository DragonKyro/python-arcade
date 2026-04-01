import arcade
from pages.rules import RulesView
from renderers import flow_free_renderer
from renderers.flow_free_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT, PLAYING, WON,
    grid_metrics, cell_center,
)


# Puzzles: (grid_size, endpoints_dict)
# endpoints_dict: {color_id: [(r1,c1),(r2,c2)]}
PUZZLES = [
    # Puzzle 1: 5x5
    (5, {
        1: [(0, 0), (3, 3)],
        2: [(0, 3), (4, 1)],
        3: [(1, 0), (3, 4)],
        4: [(2, 0), (4, 4)],
        5: [(1, 4), (4, 0)],
    }),
    # Puzzle 2: 5x5
    (5, {
        1: [(0, 1), (2, 3)],
        2: [(0, 4), (3, 2)],
        3: [(1, 0), (4, 3)],
        4: [(1, 2), (4, 0)],
        5: [(2, 1), (3, 4)],
    }),
    # Puzzle 3: 6x6
    (6, {
        1: [(0, 0), (5, 5)],
        2: [(0, 3), (3, 0)],
        3: [(1, 1), (4, 4)],
        4: [(1, 5), (5, 2)],
        5: [(2, 2), (5, 0)],
        6: [(0, 5), (3, 3)],
    }),
    # Puzzle 4: 6x6
    (6, {
        1: [(0, 0), (4, 3)],
        2: [(0, 2), (2, 5)],
        3: [(1, 0), (5, 4)],
        4: [(1, 3), (4, 0)],
        5: [(3, 1), (5, 5)],
        6: [(2, 2), (5, 0)],
    }),
    # Puzzle 5: 7x7
    (7, {
        1: [(0, 0), (6, 6)],
        2: [(0, 3), (3, 0)],
        3: [(1, 1), (5, 5)],
        4: [(1, 6), (6, 2)],
        5: [(2, 2), (6, 0)],
        6: [(0, 6), (4, 4)],
        7: [(3, 3), (6, 4)],
    }),
    # Puzzle 6: 7x7
    (7, {
        1: [(0, 1), (3, 5)],
        2: [(0, 4), (4, 0)],
        3: [(1, 2), (6, 5)],
        4: [(1, 6), (5, 3)],
        5: [(2, 0), (6, 6)],
        6: [(3, 1), (6, 0)],
        7: [(2, 3), (5, 6)],
    }),
]


class FlowFreeView(arcade.View):
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
        self.grid_size = puzzle[0]
        self.endpoints = {}
        for cid, pts in puzzle[1].items():
            self.endpoints[cid] = list(pts)

        # cell_colors tracks which color occupies each cell (0 = empty)
        self.cell_colors = [[0] * self.grid_size for _ in range(self.grid_size)]
        # paths: {color_id: [(r,c), ...]}
        self.paths = {cid: [] for cid in self.endpoints}
        # Mark endpoint cells
        for cid, pts in self.endpoints.items():
            for r, c in pts:
                self.cell_colors[r][c] = cid

        self.drawing_color = 0
        self.current_path = []
        self.game_state = PLAYING
        self.txt_info.text = f"Puzzle {self.puzzle_index + 1}/{len(PUZZLES)}  ({self.grid_size}x{self.grid_size})"

    def _pixel_to_grid(self, x, y):
        gs = self.grid_size
        cell_size, gw, gh, ox, oy = grid_metrics(gs)
        col = int((x - ox) / cell_size)
        row_visual = int((y - oy) / cell_size)
        row = (gs - 1) - row_visual
        if 0 <= row < gs and 0 <= col < gs:
            return row, col
        return None

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def _is_endpoint(self, r, c):
        for cid, pts in self.endpoints.items():
            for pr, pc in pts:
                if pr == r and pc == c:
                    return cid
        return 0

    def _clear_path(self, color_id):
        """Remove a path and free its cells."""
        if color_id in self.paths:
            for r, c in self.paths[color_id]:
                if self._is_endpoint(r, c) == color_id:
                    continue  # keep endpoint color
                if self.cell_colors[r][c] == color_id:
                    self.cell_colors[r][c] = 0
            self.paths[color_id] = []

    def _is_adjacent(self, r1, c1, r2, c2):
        return abs(r1 - r2) + abs(c1 - c2) == 1

    def _check_win(self):
        # All pairs connected?
        for cid, pts in self.endpoints.items():
            path = self.paths.get(cid, [])
            if len(path) < 2:
                return
            if list(path[0]) != list(pts[0]) and list(path[0]) != list(pts[1]):
                return
            if list(path[-1]) != list(pts[0]) and list(path[-1]) != list(pts[1]):
                return
        # All cells filled?
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.cell_colors[r][c] == 0:
                    return
        self.game_state = WON

    def on_draw(self):
        self.clear()
        flow_free_renderer.draw(self)

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
                "Flow Free", "flow_free.txt", None,
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

        # Click on an endpoint to start drawing
        ep_color = self._is_endpoint(r, c)
        if ep_color > 0:
            self._clear_path(ep_color)
            self.drawing_color = ep_color
            self.current_path = [(r, c)]
            self.paths[ep_color] = [(r, c)]
            self.cell_colors[r][c] = ep_color
            return

        # Click on an existing path cell to clear that path
        if self.cell_colors[r][c] > 0:
            self._clear_path(self.cell_colors[r][c])
            return

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.game_state != PLAYING or self.drawing_color == 0:
            return
        result = self._pixel_to_grid(x, y)
        if result is None:
            return
        r, c = result
        if (r, c) in self.current_path:
            # If dragging back, trim path
            idx = self.current_path.index((r, c))
            removed = self.current_path[idx + 1:]
            self.current_path = self.current_path[:idx + 1]
            self.paths[self.drawing_color] = list(self.current_path)
            for rr, cc in removed:
                if self._is_endpoint(rr, cc) != self.drawing_color:
                    if self.cell_colors[rr][cc] == self.drawing_color:
                        self.cell_colors[rr][cc] = 0
            return

        last_r, last_c = self.current_path[-1]
        if not self._is_adjacent(last_r, last_c, r, c):
            return

        # Can't overlap another color's path (unless it's an endpoint of our color)
        if self.cell_colors[r][c] != 0 and self.cell_colors[r][c] != self.drawing_color:
            return

        # If this cell is the other endpoint of our color, complete the path
        ep_color = self._is_endpoint(r, c)
        if ep_color == self.drawing_color and (r, c) != self.current_path[0]:
            self.current_path.append((r, c))
            self.paths[self.drawing_color] = list(self.current_path)
            self.cell_colors[r][c] = self.drawing_color
            self.drawing_color = 0
            self.current_path = []
            self._check_win()
            return

        # Normal cell — extend path
        if self.cell_colors[r][c] == 0:
            self.current_path.append((r, c))
            self.paths[self.drawing_color] = list(self.current_path)
            self.cell_colors[r][c] = self.drawing_color

    def on_mouse_release(self, x, y, button, modifiers):
        if self.drawing_color > 0:
            # If path doesn't end on the matching endpoint, keep it but stop drawing
            path = self.current_path
            if len(path) >= 2:
                last = path[-1]
                ep = self._is_endpoint(last[0], last[1])
                if ep == self.drawing_color and last != path[0]:
                    # Path is complete
                    pass
                # else: keep partial path, user can restart from endpoint
            self.drawing_color = 0
            self.current_path = []
