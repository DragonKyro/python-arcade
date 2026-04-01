"""
Tron Light Cycles game view for Python Arcade 3.x.
"""

import arcade
from ai.tron_ai import TronAI
from renderers import tron_renderer

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WIDTH = 800
HEIGHT = 600
GRID_W = 80
GRID_H = 60
CELL_SIZE = 10
TICK_RATE = 1 / 10  # 10 ticks per second

PLAYER_NAMES = {1: "Player", 2: "AI 1", 3: "AI 2", 4: "AI 3"}
PLAYER_CSS = {
    1: (0, 220, 255),
    2: (255, 40, 40),
    3: (0, 220, 60),
    4: (255, 220, 0),
}

START_POSITIONS = {
    2: [(5, GRID_H // 2), (GRID_W - 6, GRID_H // 2)],
    3: [(5, GRID_H // 2), (GRID_W - 6, GRID_H // 4), (GRID_W - 6, 3 * GRID_H // 4)],
    4: [(5, 5), (GRID_W - 6, 5), (5, GRID_H - 6), (GRID_W - 6, GRID_H - 6)],
}

START_DIRS = {
    2: ['right', 'left'],
    3: ['right', 'left', 'left'],
    4: ['right', 'left', 'right', 'left'],
}

DIFFICULTIES = ['easy', 'medium', 'hard']


class TronView(arcade.View):
    """Tron Light Cycles game view."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view

        # Grid geometry
        self.grid_w = GRID_W
        self.grid_h = GRID_H
        self.cell_size = CELL_SIZE
        self.grid_offset_x = (WIDTH - GRID_W * CELL_SIZE) // 2
        self.grid_offset_y = (HEIGHT - GRID_H * CELL_SIZE) // 2

        # State
        self.grid = []
        self.players = []
        self.ais = {}
        self.phase = 'setup'  # 'setup' | 'playing' | 'gameover'
        self.tick_timer = 0.0
        self.num_opponents = 1
        self.difficulty = 'medium'
        self.pending_direction = None  # buffered player input

        # UI text objects (no draw_text!)
        self.setup_texts = []
        self.gameover_texts = []
        self.button_texts = []
        self.status_text = None
        self.help_visible = False
        self.help_texts = []

        self._build_button_texts()
        self._build_setup_texts()

    # ------------------------------------------------------------------
    # UI text builders
    # ------------------------------------------------------------------

    def _build_button_texts(self):
        self.button_texts = [
            arcade.Text("Back", 10, HEIGHT - 30, arcade.color.WHITE, 14, bold=True),
            arcade.Text("New Game", WIDTH // 2 - 40, HEIGHT - 30, arcade.color.WHITE, 14, bold=True),
            arcade.Text("?", WIDTH - 30, HEIGHT - 30, arcade.color.WHITE, 16, bold=True),
        ]

    def _build_setup_texts(self):
        self.setup_texts = [
            arcade.Text("TRON - Light Cycles", WIDTH // 2, HEIGHT // 2 + 120,
                        arcade.color.CYAN, 28, anchor_x="center", bold=True),
            arcade.Text(f"Opponents: {self.num_opponents}  (LEFT/RIGHT to change)",
                        WIDTH // 2, HEIGHT // 2 + 60, arcade.color.WHITE, 16, anchor_x="center"),
            arcade.Text(f"Difficulty: {self.difficulty}  (UP/DOWN to change)",
                        WIDTH // 2, HEIGHT // 2 + 20, arcade.color.WHITE, 16, anchor_x="center"),
            arcade.Text("Press ENTER to start", WIDTH // 2, HEIGHT // 2 - 40,
                        arcade.color.YELLOW, 18, anchor_x="center", bold=True),
            arcade.Text("Arrow keys to steer during the game", WIDTH // 2, HEIGHT // 2 - 80,
                        (160, 160, 160), 13, anchor_x="center"),
        ]

    def _build_gameover_texts(self, winner_name, winner_color):
        self.gameover_texts = [
            arcade.Text("GAME OVER", WIDTH // 2, HEIGHT // 2 + 60,
                        arcade.color.WHITE, 30, anchor_x="center", bold=True),
            arcade.Text(f"{winner_name} wins!" if winner_name else "Draw!",
                        WIDTH // 2, HEIGHT // 2, winner_color if winner_name else arcade.color.WHITE,
                        22, anchor_x="center", bold=True),
            arcade.Text("Press ENTER or click New Game to play again",
                        WIDTH // 2, HEIGHT // 2 - 50, (160, 160, 160), 14, anchor_x="center"),
        ]

    def _build_status_text(self):
        alive = [p for p in self.players if p['alive']]
        parts = []
        for p in self.players:
            tag = PLAYER_NAMES.get(p['id'], f"P{p['id']}")
            status = tag if p['alive'] else f"[{tag}]"
            parts.append(status)
        self.status_text = arcade.Text(
            "  ".join(parts), WIDTH // 2, HEIGHT - 30,
            arcade.color.WHITE, 13, anchor_x="center"
        )

    def _build_help_texts(self):
        lines = [
            "HOW TO PLAY",
            "",
            "You are the CYAN light cycle.",
            "Use ARROW KEYS to steer.",
            "You cannot reverse direction.",
            "",
            "Every player leaves a trail.",
            "Hitting a wall, trail, or head = death.",
            "Last one alive wins!",
            "",
            "Click ? again to close.",
        ]
        self.help_texts = []
        for i, line in enumerate(lines):
            self.help_texts.append(arcade.Text(
                line, WIDTH // 2, HEIGHT // 2 + 120 - i * 24,
                arcade.color.WHITE if i == 0 else (190, 190, 190),
                16 if i == 0 else 13, anchor_x="center",
                bold=(i == 0),
            ))

    # ------------------------------------------------------------------
    # Game logic
    # ------------------------------------------------------------------

    def _start_game(self):
        total = self.num_opponents + 1
        self.grid = [[0] * GRID_W for _ in range(GRID_H)]
        positions = START_POSITIONS[total]
        directions = START_DIRS[total]

        self.players = []
        self.ais = {}
        for i in range(total):
            pid = i + 1
            pos = positions[i]
            d = directions[i]
            self.players.append({
                'id': pid,
                'pos': pos,
                'direction': d,
                'alive': True,
                'is_human': (i == 0),
            })
            # Place starting cell
            self.grid[pos[1]][pos[0]] = pid
            if not (i == 0):
                self.ais[pid] = TronAI(difficulty=self.difficulty)

        self.pending_direction = None
        self.tick_timer = 0.0
        self.phase = 'playing'
        self.help_visible = False
        self._build_status_text()

    def _tick(self):
        """Advance all players one cell."""
        # 1. Gather intended new positions
        new_positions = {}
        for p in self.players:
            if not p['alive']:
                continue
            pid = p['id']
            if p['is_human']:
                if self.pending_direction and self.pending_direction != _opposite(p['direction']):
                    p['direction'] = self.pending_direction
                self.pending_direction = None
            else:
                ai = self.ais[pid]
                other_heads = [
                    op['pos'] for op in self.players
                    if op['alive'] and op['id'] != pid
                ]
                new_dir = ai.get_direction(
                    p['pos'], p['direction'], self.grid,
                    GRID_W, GRID_H, other_heads
                )
                if new_dir and new_dir != _opposite(p['direction']):
                    p['direction'] = new_dir

            dx, dy = _dir_delta(p['direction'])
            nx, ny = p['pos'][0] + dx, p['pos'][1] + dy
            new_positions[pid] = (nx, ny)

        # 2. Detect collisions
        dead_this_tick = set()
        for pid, (nx, ny) in new_positions.items():
            # Wall collision
            if nx < 0 or nx >= GRID_W or ny < 0 or ny >= GRID_H:
                dead_this_tick.add(pid)
                continue
            # Trail collision
            if self.grid[ny][nx] != 0:
                dead_this_tick.add(pid)
                continue

        # Head-to-head collision
        pos_to_pids = {}
        for pid, pos in new_positions.items():
            if pid in dead_this_tick:
                continue
            pos_to_pids.setdefault(pos, []).append(pid)
        for pos, pids in pos_to_pids.items():
            if len(pids) > 1:
                dead_this_tick.update(pids)

        # 3. Apply moves
        for p in self.players:
            pid = p['id']
            if not p['alive']:
                continue
            if pid in dead_this_tick:
                p['alive'] = False
                continue
            if pid in new_positions:
                p['pos'] = new_positions[pid]
                x, y = p['pos']
                self.grid[y][x] = pid

        # 4. Check game over
        alive = [p for p in self.players if p['alive']]
        self._build_status_text()

        if len(alive) <= 1:
            self.phase = 'gameover'
            if alive:
                w = alive[0]
                self._build_gameover_texts(
                    PLAYER_NAMES.get(w['id'], f"P{w['id']}"),
                    PLAYER_CSS.get(w['id'], (255, 255, 255))
                )
            else:
                self._build_gameover_texts(None, None)

    # ------------------------------------------------------------------
    # Arcade callbacks
    # ------------------------------------------------------------------

    def on_show_view(self):
        self.window.background_color = arcade.color.BLACK

    def on_draw(self):
        self.clear()
        tron_renderer.draw(self)
        if self.help_visible:
            # Dim overlay
            arcade.draw_lbwh_rectangle_filled(
                WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2, (0, 0, 0, 200)
            )
            for t in self.help_texts:
                t.draw()

    def on_update(self, delta_time):
        if self.phase != 'playing':
            return
        self.tick_timer += delta_time
        if self.tick_timer >= TICK_RATE:
            self.tick_timer -= TICK_RATE
            self._tick()

    def on_key_press(self, key, modifiers):
        if self.phase == 'setup':
            if key == arcade.key.LEFT:
                self.num_opponents = max(1, self.num_opponents - 1)
                self._build_setup_texts()
            elif key == arcade.key.RIGHT:
                self.num_opponents = min(3, self.num_opponents + 1)
                self._build_setup_texts()
            elif key == arcade.key.UP:
                idx = DIFFICULTIES.index(self.difficulty)
                self.difficulty = DIFFICULTIES[(idx + 1) % len(DIFFICULTIES)]
                self._build_setup_texts()
            elif key == arcade.key.DOWN:
                idx = DIFFICULTIES.index(self.difficulty)
                self.difficulty = DIFFICULTIES[(idx - 1) % len(DIFFICULTIES)]
                self._build_setup_texts()
            elif key == arcade.key.RETURN:
                self._start_game()
            elif key == arcade.key.ESCAPE:
                self._go_back()
        elif self.phase == 'playing':
            direction_map = {
                arcade.key.UP: 'up',
                arcade.key.DOWN: 'down',
                arcade.key.LEFT: 'left',
                arcade.key.RIGHT: 'right',
            }
            if key in direction_map:
                self.pending_direction = direction_map[key]
            elif key == arcade.key.ESCAPE:
                self.phase = 'setup'
                self._build_setup_texts()
        elif self.phase == 'gameover':
            if key == arcade.key.RETURN:
                self.phase = 'setup'
                self._build_setup_texts()
            elif key == arcade.key.ESCAPE:
                self._go_back()

    def on_mouse_press(self, x, y, button, modifiers):
        # "Back" button (top-left)
        if x < 70 and y > HEIGHT - 45:
            self._go_back()
            return
        # "New Game" button (top-center)
        if WIDTH // 2 - 50 < x < WIDTH // 2 + 60 and y > HEIGHT - 45:
            self.phase = 'setup'
            self._build_setup_texts()
            return
        # "?" button (top-right)
        if x > WIDTH - 45 and y > HEIGHT - 45:
            if not self.help_texts:
                self._build_help_texts()
            self.help_visible = not self.help_visible
            return

    def _go_back(self):
        if self.menu_view:
            self.window.show_view(self.menu_view)


# ---------------------------------------------------------------------------
# Helpers (module-level)
# ---------------------------------------------------------------------------

_DIR_DELTA = {'up': (0, 1), 'down': (0, -1), 'left': (-1, 0), 'right': (1, 0)}
_OPPOSITE = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}


def _dir_delta(d):
    return _DIR_DELTA[d]


def _opposite(d):
    return _OPPOSITE[d]
