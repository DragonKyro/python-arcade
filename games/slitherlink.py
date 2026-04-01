import arcade
import random
from pages.rules import RulesView
from renderers import slitherlink_renderer
from renderers.slitherlink_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT,
    GRID_ROWS, GRID_COLS, CELL_SIZE,
    GRID_ORIGIN_X, GRID_ORIGIN_Y,
    EDGE_TOLERANCE, PLAYING, WON,
)


# ---------- Puzzle generator ----------

def _generate_random_loop(rows, cols):
    """Generate a random closed loop on a rows x cols dot grid.

    Returns sets of horizontal and vertical edges forming a single closed loop.
    h_edges_set: set of (r, c) meaning horizontal edge between dot (r,c) and (r,c+1)
    v_edges_set: set of (r, c) meaning vertical edge between dot (r,c) and (r+1,c)
    """
    # Strategy: create a random closed loop using a random walk approach.
    # Start with a small loop and expand it by adding detours.

    # Start with a simple rectangular loop in the middle
    mr, mc = rows // 2 - 1, cols // 2 - 1
    h_set = set()
    v_set = set()

    # Small 2x2 rectangle
    for c in range(mc, mc + 2):
        h_set.add((mr, c))
        h_set.add((mr + 2, c))
    for r in range(mr, mr + 2):
        v_set.add((r, mc))
        v_set.add((r, mc + 2))

    # Expand the loop by random detours
    for _ in range(rows * cols * 3):
        _try_expand_loop(h_set, v_set, rows, cols)

    return h_set, v_set


def _try_expand_loop(h_set, v_set, rows, cols):
    """Try to expand the loop by adding a rectangular bump."""
    # Pick a random horizontal or vertical edge on the loop
    all_edges = list(h_set) + list(v_set)
    if not all_edges:
        return

    # Try a random horizontal edge bump
    if random.random() < 0.5 and h_set:
        edge = random.choice(list(h_set))
        r, c = edge
        # Try bumping up or down
        direction = random.choice([-1, 1])
        nr = r + direction
        if 0 <= nr <= rows and 0 <= nr - (1 if direction == 1 else 0) < rows:
            # Check if we can add a bump: remove edge (r,c), add three edges
            new_h = (nr, c)
            if direction == 1:
                new_v1 = (r, c)
                new_v2 = (r, c + 1)
            else:
                new_v1 = (nr, c)
                new_v2 = (nr, c + 1)

            # Validate bounds
            vr1 = new_v1[0]
            vr2 = new_v2[0]
            if not (0 <= vr1 < rows and 0 <= new_v1[1] <= cols):
                return
            if not (0 <= vr2 < rows and 0 <= new_v2[1] <= cols):
                return
            if not (0 <= new_h[0] <= rows and 0 <= new_h[1] < cols):
                return

            # Don't create crossings
            if new_h in h_set or new_v1 in v_set or new_v2 in v_set:
                return

            # Check that added vertical edges don't already exist
            h_set.discard(edge)
            h_set.add(new_h)
            if new_v1 in v_set:
                v_set.discard(new_v1)
            else:
                v_set.add(new_v1)
            if new_v2 in v_set:
                v_set.discard(new_v2)
            else:
                v_set.add(new_v2)
    else:
        if not v_set:
            return
        edge = random.choice(list(v_set))
        r, c = edge
        direction = random.choice([-1, 1])
        nc = c + direction
        if 0 <= nc <= cols and 0 <= nc - (1 if direction == 1 else 0) < cols:
            new_v = (r, nc)
            if direction == 1:
                new_h1 = (r, c)
                new_h2 = (r + 1, c)
            else:
                new_h1 = (r, nc)
                new_h2 = (r + 1, nc)

            hr1 = new_h1[0]
            hr2 = new_h2[0]
            if not (0 <= hr1 <= rows and 0 <= new_h1[1] < cols):
                return
            if not (0 <= hr2 <= rows and 0 <= new_h2[1] < cols):
                return
            if not (0 <= new_v[0] < rows and 0 <= new_v[1] <= cols):
                return

            if new_v in v_set or new_h1 in h_set or new_h2 in h_set:
                return

            v_set.discard(edge)
            v_set.add(new_v)
            if new_h1 in h_set:
                h_set.discard(new_h1)
            else:
                h_set.add(new_h1)
            if new_h2 in h_set:
                h_set.discard(new_h2)
            else:
                h_set.add(new_h2)


def _derive_clues(h_set, v_set, rows, cols):
    """Derive clue numbers from the loop. Returns a rows x cols grid of clue values (0-3)."""
    clues = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            count = 0
            if (r, c) in h_set:
                count += 1
            if (r + 1, c) in h_set:
                count += 1
            if (r, c) in v_set:
                count += 1
            if (r, c + 1) in v_set:
                count += 1
            clues[r][c] = count
    return clues


def _generate_puzzle(rows, cols, clue_removal_ratio=0.4):
    """Generate a Slitherlink puzzle.

    Returns clues grid where None means no clue shown.
    """
    # Simple approach: generate a valid loop and derive all clues
    # For reliability, use a simple rectangular loop with bumps
    h_set, v_set = _generate_random_loop(rows, cols)

    # Validate the loop is connected and closed
    if not _validate_loop(h_set, v_set, rows, cols):
        # Fallback: simple rectangular loop
        h_set = set()
        v_set = set()
        margin = 1
        for c in range(margin, cols - margin):
            h_set.add((margin, c))
            h_set.add((rows - margin, c))
        for r in range(margin, rows - margin):
            v_set.add((r, margin))
            v_set.add((r, cols - margin))

    clue_values = _derive_clues(h_set, v_set, rows, cols)

    # Remove some clues for difficulty
    clues = [[clue_values[r][c] for c in range(cols)] for r in range(rows)]
    cells = [(r, c) for r in range(rows) for c in range(cols)]
    random.shuffle(cells)
    remove_count = int(len(cells) * clue_removal_ratio)
    for i in range(remove_count):
        r, c = cells[i]
        clues[r][c] = None

    return clues, h_set, v_set


def _validate_loop(h_set, v_set, rows, cols):
    """Check that edges form a single closed loop (every vertex has degree 0 or 2)."""
    # Build adjacency: count degree of each dot
    degree = {}
    for (r, c) in h_set:
        degree[(r, c)] = degree.get((r, c), 0) + 1
        degree[(r, c + 1)] = degree.get((r, c + 1), 0) + 1
    for (r, c) in v_set:
        degree[(r, c)] = degree.get((r, c), 0) + 1
        degree[(r + 1, c)] = degree.get((r + 1, c), 0) + 1

    if not degree:
        return False

    # Every vertex in the loop must have degree 2
    for v, d in degree.items():
        if d != 2:
            return False

    # Check connectivity via BFS
    vertices = set(degree.keys())
    start = next(iter(vertices))
    visited = set()
    queue = [start]
    visited.add(start)

    # Build neighbor map
    neighbors = {v: [] for v in vertices}
    for (r, c) in h_set:
        a, b = (r, c), (r, c + 1)
        neighbors[a].append(b)
        neighbors[b].append(a)
    for (r, c) in v_set:
        a, b = (r, c), (r + 1, c)
        neighbors[a].append(b)
        neighbors[b].append(a)

    while queue:
        node = queue.pop(0)
        for nb in neighbors[node]:
            if nb not in visited:
                visited.add(nb)
                queue.append(nb)

    return visited == vertices


# ---------- View ----------

class SlitherlinkView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self._create_texts()
        self._init_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects for rendering."""
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
            font_size=16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_timer = arcade.Text(
            "", WIDTH / 2, bar_y, arcade.color.WHITE,
            font_size=16, anchor_x="center", anchor_y="center", bold=True,
        )

        # Clue texts (one per cell)
        self.txt_clues = {}
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                cx = GRID_ORIGIN_X + c * CELL_SIZE + CELL_SIZE / 2
                cy = GRID_ORIGIN_Y + (GRID_ROWS - 1 - r) * CELL_SIZE + CELL_SIZE / 2
                self.txt_clues[(r, c)] = arcade.Text(
                    "", cx, cy, arcade.color.WHITE,
                    font_size=16, anchor_x="center", anchor_y="center", bold=True,
                )

        # Win overlay texts
        self.txt_win_title = arcade.Text(
            "Puzzle Solved!", WIDTH / 2, HEIGHT / 2 + 20,
            arcade.color.GOLD, font_size=36,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_hint = arcade.Text(
            "Click New Game to play again",
            WIDTH / 2, HEIGHT / 2 - 30,
            arcade.color.LIGHT_GRAY, font_size=14,
            anchor_x="center", anchor_y="center",
        )

    def _init_game(self):
        """Initialize or reset game state."""
        clues, self._solution_h, self._solution_v = _generate_puzzle(GRID_ROWS, GRID_COLS)
        self.clues = clues

        # Edge states: 0=empty, 1=line, 2=X (no line)
        # h_edges[r][c]: horizontal edge between dots (r,c) and (r,c+1)
        self.h_edges = [[0] * GRID_COLS for _ in range(GRID_ROWS + 1)]
        # v_edges[r][c]: vertical edge between dots (r,c) and (r+1,c)
        self.v_edges = [[0] * (GRID_COLS + 1) for _ in range(GRID_ROWS)]

        self.game_state = PLAYING
        self.elapsed_time = 0.0

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def _find_nearest_edge(self, px, py):
        """Find the nearest edge to pixel position. Returns ('h', r, c) or ('v', r, c) or None."""
        best = None
        best_dist = EDGE_TOLERANCE + 1

        # Check horizontal edges
        for r in range(GRID_ROWS + 1):
            for c in range(GRID_COLS):
                mx = GRID_ORIGIN_X + c * CELL_SIZE + CELL_SIZE / 2
                my = GRID_ORIGIN_Y + (GRID_ROWS - r) * CELL_SIZE
                dist = ((px - mx) ** 2 + (py - my) ** 2) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best = ('h', r, c)

        # Check vertical edges
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS + 1):
                mx = GRID_ORIGIN_X + c * CELL_SIZE
                my = GRID_ORIGIN_Y + (GRID_ROWS - 1 - r) * CELL_SIZE + CELL_SIZE / 2
                dist = ((px - mx) ** 2 + (py - my) ** 2) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best = ('v', r, c)

        return best

    def _check_win(self):
        """Check if the puzzle is solved: all clues satisfied and edges form a single closed loop."""
        # Check all clues
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if self.clues[r][c] is None:
                    continue
                count = 0
                if self.h_edges[r][c] == 1:
                    count += 1
                if self.h_edges[r + 1][c] == 1:
                    count += 1
                if self.v_edges[r][c] == 1:
                    count += 1
                if self.v_edges[r][c + 1] == 1:
                    count += 1
                if count != self.clues[r][c]:
                    return

        # Collect all active edges and check they form a single closed loop
        h_set = set()
        v_set = set()
        for r in range(GRID_ROWS + 1):
            for c in range(GRID_COLS):
                if self.h_edges[r][c] == 1:
                    h_set.add((r, c))
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS + 1):
                if self.v_edges[r][c] == 1:
                    v_set.add((r, c))

        if not h_set and not v_set:
            return

        if _validate_loop(h_set, v_set, GRID_ROWS, GRID_COLS):
            self.game_state = WON

    # --- arcade callbacks ---

    def on_update(self, delta_time):
        if self.game_state == PLAYING:
            self.elapsed_time += delta_time

    def on_draw(self):
        self.clear()
        slitherlink_renderer.draw(self)

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
        if self._hit_test_button(x, y, WIDTH - 135, bar_y, 40, 40):
            rules_view = RulesView("Slitherlink", "slitherlink.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self.game_state != PLAYING:
            return

        # Find nearest edge
        edge = self._find_nearest_edge(x, y)
        if edge is None:
            return

        kind, r, c = edge
        if kind == 'h':
            if button == arcade.MOUSE_BUTTON_LEFT:
                # Cycle: 0 -> 1 -> 0
                self.h_edges[r][c] = 1 if self.h_edges[r][c] != 1 else 0
            elif button == arcade.MOUSE_BUTTON_RIGHT:
                # Cycle: 0 -> 2 -> 0
                self.h_edges[r][c] = 2 if self.h_edges[r][c] != 2 else 0
        else:
            if button == arcade.MOUSE_BUTTON_LEFT:
                self.v_edges[r][c] = 1 if self.v_edges[r][c] != 1 else 0
            elif button == arcade.MOUSE_BUTTON_RIGHT:
                self.v_edges[r][c] = 2 if self.v_edges[r][c] != 2 else 0

        self._check_win()
