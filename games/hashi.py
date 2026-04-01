import arcade
import random
from pages.rules import RulesView
from renderers import hashi_renderer
from renderers.hashi_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT,
    GRID_SIZE, CELL_SIZE, GRID_ORIGIN_X, GRID_ORIGIN_Y,
    ISLAND_RADIUS, PLAYING, WON,
)


# ---------- Puzzle generator ----------

def _generate_puzzle(grid_size):
    """Generate a Hashi puzzle on a grid_size x grid_size grid.

    Strategy: place islands, connect them with bridges, derive numbers.
    """
    max_attempts = 50
    for _ in range(max_attempts):
        result = _try_generate(grid_size)
        if result is not None:
            return result

    # Fallback: simple puzzle
    return _generate_simple_puzzle(grid_size)


def _try_generate(grid_size):
    """Attempt to generate a valid puzzle."""
    # Place islands randomly with minimum spacing
    islands = {}
    positions = []

    # Generate candidate positions with spacing
    num_islands = random.randint(10, 16)
    candidates = [(r, c) for r in range(grid_size) for c in range(grid_size)]
    random.shuffle(candidates)

    for r, c in candidates:
        if len(positions) >= num_islands:
            break
        # Check minimum distance to existing islands
        too_close = False
        for pr, pc in positions:
            if abs(r - pr) + abs(c - pc) < 2:
                too_close = True
                break
        if not too_close:
            positions.append((r, c))

    if len(positions) < 6:
        return None

    # Build bridges: for each island, try to connect to nearest aligned islands
    bridges = {}  # {((r1,c1),(r2,c2)): count}

    # Find all possible bridge connections (horizontal/vertical line of sight)
    possible = []
    pos_set = set(positions)
    for i, (r1, c1) in enumerate(positions):
        for j, (r2, c2) in enumerate(positions):
            if j <= i:
                continue
            if r1 == r2:  # Same row - horizontal bridge
                # Check no island between them
                min_c, max_c = min(c1, c2), max(c1, c2)
                if max_c - min_c < 2:
                    continue
                blocked = False
                for cc in range(min_c + 1, max_c):
                    if (r1, cc) in pos_set:
                        blocked = True
                        break
                if not blocked:
                    possible.append(((r1, c1), (r2, c2)))
            elif c1 == c2:  # Same column - vertical bridge
                min_r, max_r = min(r1, r2), max(r1, r2)
                if max_r - min_r < 2:
                    continue
                blocked = False
                for rr in range(min_r + 1, max_r):
                    if (rr, c1) in pos_set:
                        blocked = True
                        break
                if not blocked:
                    possible.append(((r1, c1), (r2, c2)))

    if not possible:
        return None

    # Randomly assign bridges (1 or 2) to connections
    random.shuffle(possible)

    # Use a spanning tree approach to ensure connectivity
    parent = {p: p for p in positions}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            return True
        return False

    # First pass: create spanning tree
    for (a, b) in possible:
        if find(a) != find(b):
            count = random.choice([1, 2])
            key = (a, b) if a < b else (b, a)
            bridges[key] = count
            union(a, b)

    # Check if all connected
    roots = set(find(p) for p in positions)
    if len(roots) > 1:
        return None

    # Second pass: optionally add more bridges
    for (a, b) in possible:
        key = (a, b) if a < b else (b, a)
        if key in bridges:
            continue
        if random.random() < 0.3:
            # Check for crossing with existing bridges
            if not _bridges_cross(key, bridges, pos_set):
                bridges[key] = random.choice([1, 2])

    # Derive island numbers from bridge counts
    for pos in positions:
        total = 0
        for (a, b), count in bridges.items():
            if pos == a or pos == b:
                total += count
        if total == 0:
            return None  # Isolated island
        islands[pos] = total

    return islands, bridges


def _bridges_cross(new_bridge, existing_bridges, island_positions):
    """Check if a new bridge would cross any existing bridge."""
    (r1, c1), (r2, c2) = new_bridge

    for (a, b), count in existing_bridges.items():
        if count == 0:
            continue
        (ra, ca), (rb, cb) = a, b

        # Horizontal vs Vertical crossing
        if r1 == r2 and ca == cb:  # New is horizontal, existing is vertical
            min_c, max_c = min(c1, c2), max(c1, c2)
            min_r, max_r = min(ra, rb), max(ra, rb)
            if min_c < ca < max_c and min_r < r1 < max_r:
                return True
        elif c1 == c2 and ra == rb:  # New is vertical, existing is horizontal
            min_r, max_r = min(r1, r2), max(r1, r2)
            min_c, max_c = min(ca, cb), max(ca, cb)
            if min_r < ra < max_r and min_c < c1 < max_c:
                return True

    return False


def _generate_simple_puzzle(grid_size):
    """Generate a simple fallback puzzle."""
    islands = {
        (0, 0): 2, (0, 4): 3, (0, 8): 1,
        (2, 0): 2, (2, 4): 4, (2, 8): 2,
        (4, 2): 2, (4, 6): 2,
        (6, 0): 2, (6, 4): 3, (6, 8): 1,
        (8, 0): 1, (8, 4): 1,
    }
    bridges = {
        ((0, 0), (0, 4)): 1, ((0, 4), (0, 8)): 1,
        ((0, 0), (2, 0)): 1, ((0, 4), (2, 4)): 2,
        ((0, 8), (2, 8)): 0, ((2, 0), (2, 4)): 1,
        ((2, 4), (2, 8)): 1, ((2, 8), (6, 8)): 1,
        ((2, 0), (6, 0)): 1, ((4, 2), (4, 6)): 1,
        ((2, 4), (6, 4)): 1, ((4, 2), (6, 0)): 0,
        ((4, 6), (6, 8)): 0, ((6, 0), (8, 0)): 1,
        ((6, 4), (8, 4)): 1, ((6, 0), (6, 4)): 1,
    }
    # Recalculate island values from bridges
    for pos in list(islands.keys()):
        total = 0
        for (a, b), count in bridges.items():
            if pos == a or pos == b:
                total += count
        islands[pos] = max(total, 1)

    return islands, bridges


# ---------- View ----------

class HashiView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self._create_texts()
        self._init_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects."""
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

        # Island number texts
        self.txt_islands = {}
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cx = GRID_ORIGIN_X + c * CELL_SIZE + CELL_SIZE / 2
                cy = GRID_ORIGIN_Y + (GRID_SIZE - 1 - r) * CELL_SIZE + CELL_SIZE / 2
                self.txt_islands[(r, c)] = arcade.Text(
                    "", cx, cy, arcade.color.WHITE,
                    font_size=16, anchor_x="center", anchor_y="center", bold=True,
                )

        # Win overlay
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
        islands_data, self._solution_bridges = _generate_puzzle(GRID_SIZE)
        self.islands = islands_data  # {(r,c): number}

        # Player bridges: {((r1,c1),(r2,c2)): 0|1|2}
        self.bridges = {}
        # Initialize all possible bridge connections with 0
        positions = list(self.islands.keys())
        pos_set = set(positions)
        for i, (r1, c1) in enumerate(positions):
            for j, (r2, c2) in enumerate(positions):
                if j <= i:
                    continue
                connected = False
                if r1 == r2:
                    min_c, max_c = min(c1, c2), max(c1, c2)
                    blocked = any((r1, cc) in pos_set for cc in range(min_c + 1, max_c))
                    if not blocked and max_c - min_c >= 2:
                        connected = True
                elif c1 == c2:
                    min_r, max_r = min(r1, r2), max(r1, r2)
                    blocked = any((rr, c1) in pos_set for rr in range(min_r + 1, max_r))
                    if not blocked and max_r - min_r >= 2:
                        connected = True
                if connected:
                    key = ((r1, c1), (r2, c2)) if (r1, c1) < (r2, c2) else ((r2, c2), (r1, c1))
                    self.bridges[key] = 0

        self.selected_island = None
        self.game_state = PLAYING
        self.elapsed_time = 0.0

    def get_island_bridge_count(self, r, c):
        """Get total bridge count for an island at (r, c)."""
        total = 0
        pos = (r, c)
        for (a, b), count in self.bridges.items():
            if pos == a or pos == b:
                total += count
        return total

    def _find_island_at(self, px, py):
        """Find island at pixel position, or None."""
        for (r, c) in self.islands:
            cx = GRID_ORIGIN_X + c * CELL_SIZE + CELL_SIZE / 2
            cy = GRID_ORIGIN_Y + (GRID_SIZE - 1 - r) * CELL_SIZE + CELL_SIZE / 2
            dist = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
            if dist <= ISLAND_RADIUS + 5:
                return (r, c)
        return None

    def _find_bridge_key(self, island1, island2):
        """Find the bridge key for two islands, or None if not connectable."""
        key = (island1, island2) if island1 < island2 else (island2, island1)
        if key in self.bridges:
            return key
        return None

    def _would_cross(self, key):
        """Check if adding a bridge at key would cross existing bridges."""
        (r1, c1), (r2, c2) = key
        for other_key, count in self.bridges.items():
            if count == 0 or other_key == key:
                continue
            (ra, ca), (rb, cb) = other_key
            # Horizontal vs vertical crossing
            if r1 == r2 and ca == cb:
                min_c, max_c = min(c1, c2), max(c1, c2)
                min_r, max_r = min(ra, rb), max(ra, rb)
                if min_c < ca < max_c and min_r < r1 < max_r:
                    return True
            elif c1 == c2 and ra == rb:
                min_r, max_r = min(r1, r2), max(r1, r2)
                min_c, max_c = min(ca, cb), max(ca, cb)
                if min_r < ra < max_r and min_c < c1 < max_c:
                    return True
        return False

    def _check_win(self):
        """Check if puzzle is solved: all island numbers satisfied, all connected."""
        # Check all island numbers
        for (r, c), value in self.islands.items():
            if self.get_island_bridge_count(r, c) != value:
                return

        # Check connectivity
        positions = list(self.islands.keys())
        if not positions:
            return

        visited = set()
        queue = [positions[0]]
        visited.add(positions[0])

        while queue:
            node = queue.pop(0)
            for (a, b), count in self.bridges.items():
                if count == 0:
                    continue
                neighbor = None
                if a == node:
                    neighbor = b
                elif b == node:
                    neighbor = a
                if neighbor and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        if visited == set(positions):
            self.game_state = WON

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    # --- arcade callbacks ---

    def on_update(self, delta_time):
        if self.game_state == PLAYING:
            self.elapsed_time += delta_time

    def on_draw(self):
        self.clear()
        hashi_renderer.draw(self)

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
            rules_view = RulesView("Hashi", "hashi.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self.game_state != PLAYING:
            return

        # Island click
        island = self._find_island_at(x, y)
        if island is None:
            self.selected_island = None
            return

        if self.selected_island is None:
            self.selected_island = island
        elif self.selected_island == island:
            self.selected_island = None
        else:
            # Try to toggle bridge between selected and clicked island
            key = self._find_bridge_key(self.selected_island, island)
            if key is not None:
                current = self.bridges[key]
                if current == 0:
                    if not self._would_cross(key):
                        self.bridges[key] = 1
                elif current == 1:
                    self.bridges[key] = 2
                else:
                    self.bridges[key] = 0
                self._check_win()
            self.selected_island = None
