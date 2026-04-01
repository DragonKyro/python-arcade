"""
Tetris VS game view for Python Arcade 3.x.
Split-screen competitive Tetris against an AI opponent.
"""

import arcade
import random
from ai.tetris_ai import TetrisAI
from pages.rules import RulesView
from renderers import tetris_vs_renderer

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
CELL_SIZE = 20
BOARD_COLS = 10
BOARD_ROWS = 20

BOARD_PIXEL_W = BOARD_COLS * CELL_SIZE  # 200
BOARD_PIXEL_H = BOARD_ROWS * CELL_SIZE  # 400

# Board positions (two boards side by side)
MARGIN = 20
LEFT_BOARD_X = MARGIN + 20
RIGHT_BOARD_X = WIDTH - MARGIN - 20 - BOARD_PIXEL_W
BOARD_Y = (HEIGHT - TOP_BAR_HEIGHT - BOARD_PIXEL_H) // 2

# Side panel areas (between boards and edges)
LEFT_PANEL_X = LEFT_BOARD_X + BOARD_PIXEL_W + 10
RIGHT_PANEL_X = RIGHT_BOARD_X - 80

# Colors (Catppuccin-ish palette)
BG_COLOR = (30, 30, 46)
GRID_LINE_COLOR = (45, 45, 65)
LINE_COLOR = (205, 214, 244)
BUTTON_COLOR = (69, 71, 90)
BUTTON_HOVER_COLOR = (88, 91, 112)
BUTTON_TEXT_COLOR = (205, 214, 244)
OVERLAY_COLOR = (30, 30, 46, 200)
STATUS_TEXT_COLOR = (205, 214, 244)
SCORE_COLOR = (249, 226, 175)
BOARD_BG_COLOR = (24, 24, 37)

# Piece colors
PIECE_COLORS = {
    "I": (6, 214, 250),
    "O": (249, 226, 175),
    "T": (203, 166, 247),
    "S": (166, 227, 161),
    "Z": (243, 139, 168),
    "J": (137, 180, 250),
    "L": (250, 179, 135),
}

GHOST_ALPHA = 60

# Timing
BASE_TICK = 0.8
MIN_TICK = 0.1
LOCK_DELAY = 0.3

# Scoring for 1, 2, 3, 4 lines
LINE_SCORES = [100, 300, 500, 800]

# Garbage line mapping: lines cleared -> garbage sent
GARBAGE_MAP = {2: 1, 3: 2, 4: 4}

# Tetromino definitions
TETROMINOES = {
    "I": [
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 1), (1, 1), (2, 1), (3, 1)],
    ],
    "O": [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
    ],
    "T": [
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 1)],
        [(0, 1), (1, 0), (1, 1), (2, 1)],
    ],
    "S": [
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
    ],
    "Z": [
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
    ],
    "J": [
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (0, 2), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 0), (2, 1)],
    ],
    "L": [
        [(0, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (1, 2), (2, 0)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
    ],
}

WALL_KICKS = [(0, 0), (-1, 0), (1, 0), (0, 1), (-1, 1), (1, 1), (-2, 0), (2, 0)]

# Difficulty button colors
DIFF_COLORS = {
    'easy': (166, 227, 161),
    'medium': (249, 226, 175),
    'hard': (243, 139, 168),
}


class _Button:
    """Simple rectangular button helper."""

    def __init__(self, cx, cy, w, h, label):
        self.cx = cx
        self.cy = cy
        self.w = w
        self.h = h
        self.label = label

    def contains(self, x, y):
        return (abs(x - self.cx) <= self.w / 2) and (abs(y - self.cy) <= self.h / 2)

    def draw(self, hover=False):
        color = BUTTON_HOVER_COLOR if hover else BUTTON_COLOR
        arcade.draw_rect_filled(arcade.XYWH(self.cx, self.cy, self.w, self.h), color)
        arcade.draw_rect_outline(arcade.XYWH(self.cx, self.cy, self.w, self.h), LINE_COLOR, 2)
        if not hasattr(self, '_txt_label'):
            self._txt_label = arcade.Text(
                self.label, self.cx, self.cy, BUTTON_TEXT_COLOR,
                font_size=14, anchor_x="center", anchor_y="center",
            )
        self._txt_label.text = self.label
        self._txt_label.x = self.cx
        self._txt_label.y = self.cy
        self._txt_label.draw()


class _BoardState:
    """State for one Tetris board (player or AI)."""

    def __init__(self):
        self.board = [[None] * BOARD_COLS for _ in range(BOARD_ROWS)]
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.fall_timer = 0.0
        self.lock_timer = -1.0
        self.soft_drop = False

        # Piece bag
        self.bag = []
        self._fill_bag()
        self.next_piece_type = self._pop_bag()
        self._spawn_piece()

        # Pending garbage lines to receive
        self.pending_garbage = 0

    def _fill_bag(self):
        pieces = list(TETROMINOES.keys())
        random.shuffle(pieces)
        self.bag.extend(pieces)

    def _pop_bag(self):
        if not self.bag:
            self._fill_bag()
        return self.bag.pop()

    def _spawn_piece(self):
        # Apply pending garbage before spawning
        self._apply_garbage()

        self.current_type = self.next_piece_type
        self.next_piece_type = self._pop_bag()
        self.rotation = 0
        self.piece_col = BOARD_COLS // 2 - 2
        shape = TETROMINOES[self.current_type][self.rotation]
        max_r = max(r for r, c in shape)
        self.piece_row = BOARD_ROWS - 1 - max_r + 1
        self.fall_timer = 0.0
        self.lock_timer = -1.0
        self.soft_drop = False

        if not self._valid_position(self.current_type, self.rotation, self.piece_col, self.piece_row):
            self.game_over = True

    def _apply_garbage(self):
        """Add pending garbage lines to the bottom of the board."""
        if self.pending_garbage <= 0:
            return
        count = self.pending_garbage
        self.pending_garbage = 0
        gap_col = random.randint(0, BOARD_COLS - 1)
        garbage_color = (100, 100, 100)
        for _ in range(count):
            # Remove top row
            self.board.pop()
            # Insert garbage row at bottom
            row = [garbage_color] * BOARD_COLS
            row[gap_col] = None
            self.board.insert(0, row)

    def _get_cells(self, piece_type, rotation, col, row):
        shape = TETROMINOES[piece_type][rotation]
        cells = []
        for dr, dc in shape:
            cells.append((col + dc, row - dr))
        return cells

    def _valid_position(self, piece_type, rotation, col, row):
        for bc, br in self._get_cells(piece_type, rotation, col, row):
            if bc < 0 or bc >= BOARD_COLS:
                return False
            if br < 0 or br >= BOARD_ROWS:
                return False
            if self.board[br][bc] is not None:
                return False
        return True

    def _ghost_row(self):
        row = self.piece_row
        while self._valid_position(self.current_type, self.rotation, self.piece_col, row - 1):
            row -= 1
        return row

    def _move(self, dc):
        new_col = self.piece_col + dc
        if self._valid_position(self.current_type, self.rotation, new_col, self.piece_row):
            self.piece_col = new_col
            if self._valid_position(self.current_type, self.rotation, self.piece_col, self.piece_row - 1):
                self.lock_timer = -1.0

    def _rotate(self):
        new_rot = (self.rotation + 1) % 4
        for dx, dy in WALL_KICKS:
            new_col = self.piece_col + dx
            new_row = self.piece_row + dy
            if self._valid_position(self.current_type, new_rot, new_col, new_row):
                self.rotation = new_rot
                self.piece_col = new_col
                self.piece_row = new_row
                if self._valid_position(self.current_type, self.rotation, self.piece_col, self.piece_row - 1):
                    self.lock_timer = -1.0
                return

    def _hard_drop(self):
        drop_row = self._ghost_row()
        self.score += (self.piece_row - drop_row) * 2
        self.piece_row = drop_row
        return self._lock_piece()

    def _lock_piece(self):
        """Lock current piece and return number of lines cleared."""
        color = PIECE_COLORS[self.current_type]
        for bc, br in self._get_cells(self.current_type, self.rotation, self.piece_col, self.piece_row):
            if 0 <= br < BOARD_ROWS and 0 <= bc < BOARD_COLS:
                self.board[br][bc] = color
        lines = self._clear_lines()
        self._spawn_piece()
        return lines

    def _clear_lines(self):
        full_rows = []
        for r in range(BOARD_ROWS):
            if all(self.board[r][c] is not None for c in range(BOARD_COLS)):
                full_rows.append(r)
        if not full_rows:
            return 0
        for r in sorted(full_rows, reverse=True):
            del self.board[r]
        for _ in full_rows:
            self.board.append([None] * BOARD_COLS)
        count = len(full_rows)
        self.lines_cleared += count
        self.score += LINE_SCORES[min(count, 4) - 1] * self.level
        self.level = self.lines_cleared // 10 + 1
        return count

    def _tick_interval(self):
        interval = BASE_TICK - (self.level - 1) * 0.07
        return max(interval, MIN_TICK)


class TetrisVSView(arcade.View):
    """Split-screen competitive Tetris against an AI opponent."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.mouse_x = 0
        self.mouse_y = 0

        # Buttons
        self.btn_back = _Button(60, HEIGHT - 25, 90, 34, "Back")
        self.btn_help = _Button(WIDTH - 40, HEIGHT - 25, 40, 40, "?")

        # Difficulty selection state
        self.selecting_difficulty = True
        self.difficulty = 'medium'

        # Difficulty buttons (centered on screen)
        btn_y = HEIGHT // 2
        self.btn_easy = _Button(WIDTH // 2, btn_y + 60, 180, 44, "Easy")
        self.btn_medium = _Button(WIDTH // 2, btn_y, 180, 44, "Medium")
        self.btn_hard = _Button(WIDTH // 2, btn_y - 60, 180, 44, "Hard")

        # Pre-create text objects for the renderer
        self._create_texts()

        # Game state will be initialized after difficulty selection
        self.player = None
        self.ai_board = None
        self.ai = None
        self.ai_timer = 0.0
        self.ai_target = None  # (col, rotation) target placement
        self.ai_executing = False
        self.ai_exec_timer = 0.0
        self.game_active = False
        self.winner = None  # 'player' or 'ai'

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        # Difficulty selection texts
        self.txt_select_title = arcade.Text(
            "TETRIS VS", WIDTH // 2, HEIGHT // 2 + 140, SCORE_COLOR,
            font_size=28, bold=True, anchor_x="center", anchor_y="center",
        )
        self.txt_select_subtitle = arcade.Text(
            "Select AI Difficulty", WIDTH // 2, HEIGHT // 2 + 100, STATUS_TEXT_COLOR,
            font_size=16, anchor_x="center", anchor_y="center",
        )

        # VS text in center
        self.txt_vs = arcade.Text(
            "VS", WIDTH // 2, BOARD_Y + BOARD_PIXEL_H // 2, (243, 139, 168),
            font_size=24, bold=True, anchor_x="center", anchor_y="center",
        )

        # Player label and score
        left_center = LEFT_BOARD_X + BOARD_PIXEL_W // 2
        right_center = RIGHT_BOARD_X + BOARD_PIXEL_W // 2

        self.txt_player_label = arcade.Text(
            "PLAYER", left_center, BOARD_Y + BOARD_PIXEL_H + 8, SCORE_COLOR,
            font_size=14, bold=True, anchor_x="center", anchor_y="bottom",
        )
        self.txt_player_score = arcade.Text(
            "0", left_center, BOARD_Y - 8, STATUS_TEXT_COLOR,
            font_size=13, anchor_x="center", anchor_y="top",
        )
        self.txt_player_lines = arcade.Text(
            "Lines: 0", left_center, BOARD_Y - 26, STATUS_TEXT_COLOR,
            font_size=11, anchor_x="center", anchor_y="top",
        )

        # AI label and score
        self.txt_ai_label = arcade.Text(
            "AI", right_center, BOARD_Y + BOARD_PIXEL_H + 8, SCORE_COLOR,
            font_size=14, bold=True, anchor_x="center", anchor_y="bottom",
        )
        self.txt_ai_score = arcade.Text(
            "0", right_center, BOARD_Y - 8, STATUS_TEXT_COLOR,
            font_size=13, anchor_x="center", anchor_y="top",
        )
        self.txt_ai_lines = arcade.Text(
            "Lines: 0", right_center, BOARD_Y - 26, STATUS_TEXT_COLOR,
            font_size=11, anchor_x="center", anchor_y="top",
        )

        # Next piece labels
        self.txt_player_next = arcade.Text(
            "NEXT", LEFT_BOARD_X + BOARD_PIXEL_W + 8, BOARD_Y + BOARD_PIXEL_H - 5,
            STATUS_TEXT_COLOR, font_size=10, anchor_x="left", anchor_y="top",
        )
        self.txt_ai_next = arcade.Text(
            "NEXT", RIGHT_BOARD_X - 78, BOARD_Y + BOARD_PIXEL_H - 5,
            STATUS_TEXT_COLOR, font_size=10, anchor_x="left", anchor_y="top",
        )

        # Garbage warning texts
        self.txt_player_garbage = arcade.Text(
            "", LEFT_BOARD_X - 2, BOARD_Y + 5, (243, 139, 168),
            font_size=10, anchor_x="right", anchor_y="bottom",
        )
        self.txt_ai_garbage = arcade.Text(
            "", RIGHT_BOARD_X + BOARD_PIXEL_W + 2, BOARD_Y + 5, (243, 139, 168),
            font_size=10, anchor_x="left", anchor_y="bottom",
        )

        # Difficulty indicator
        self.txt_difficulty = arcade.Text(
            "", WIDTH // 2, BOARD_Y - 8, STATUS_TEXT_COLOR,
            font_size=10, anchor_x="center", anchor_y="top",
        )

        # Win/lose overlay texts
        self.txt_result = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 20, (166, 227, 161),
            font_size=36, bold=True, anchor_x="center", anchor_y="center",
        )
        self.txt_result_hint = arcade.Text(
            "Press ENTER to play again", WIDTH // 2, HEIGHT // 2 - 30, STATUS_TEXT_COLOR,
            font_size=14, anchor_x="center", anchor_y="center",
        )

    def _init_game(self, difficulty):
        """Initialize game state for both players."""
        self.difficulty = difficulty
        self.selecting_difficulty = False
        self.game_active = True
        self.winner = None

        self.player = _BoardState()
        self.ai_board = _BoardState()
        self.ai = TetrisAI(difficulty)
        self.ai_timer = 0.0
        self.ai_target = None
        self.ai_executing = False
        self.ai_exec_timer = 0.0

        # Update difficulty text
        self.txt_difficulty.text = f"AI: {difficulty.upper()}"
        self.txt_ai_label.text = f"AI ({difficulty.capitalize()})"

    def _send_garbage(self, sender, lines_cleared):
        """Send garbage lines from sender to opponent."""
        if lines_cleared < 2:
            return
        garbage = GARBAGE_MAP.get(lines_cleared, 0)
        if garbage > 0:
            if sender == 'player':
                self.ai_board.pending_garbage += garbage
            else:
                self.player.pending_garbage += garbage

    def _check_game_over(self):
        """Check if either side has topped out."""
        if self.player.game_over and not self.ai_board.game_over:
            self.winner = 'ai'
            self.game_active = False
        elif self.ai_board.game_over and not self.player.game_over:
            self.winner = 'player'
            self.game_active = False
        elif self.player.game_over and self.ai_board.game_over:
            # Both died at the same time - player with higher score wins
            self.winner = 'player' if self.player.score >= self.ai_board.score else 'ai'
            self.game_active = False

    def _update_player(self, delta_time):
        """Update player board gravity and locking."""
        p = self.player
        if p.game_over:
            return

        interval = p._tick_interval()
        if p.soft_drop:
            interval = max(interval * 0.1, MIN_TICK * 0.5)

        p.fall_timer += delta_time

        if p.fall_timer >= interval:
            p.fall_timer = 0.0
            if p._valid_position(p.current_type, p.rotation, p.piece_col, p.piece_row - 1):
                p.piece_row -= 1
                p.lock_timer = -1.0
                if p.soft_drop:
                    p.score += 1
            else:
                if p.lock_timer < 0:
                    p.lock_timer = 0.0
                p.lock_timer += interval
                if p.lock_timer >= LOCK_DELAY:
                    lines = p._lock_piece()
                    self._send_garbage('player', lines)

    def _update_ai(self, delta_time):
        """Update AI board - decide placement and execute moves."""
        ab = self.ai_board
        if ab.game_over:
            return

        self.ai_timer += delta_time

        # AI decides on a target placement
        if self.ai_target is None:
            result = self.ai.get_placement(
                ab.board, ab.current_type, ab.next_piece_type
            )
            if result is not None:
                self.ai_target = result
                self.ai_executing = True
                self.ai_exec_timer = 0.0
            else:
                # No valid placement, just drop
                self.ai_target = (ab.piece_col, ab.rotation)
                self.ai_executing = True
                self.ai_exec_timer = 0.0

        # Execute AI moves at tick rate intervals
        if self.ai_executing:
            self.ai_exec_timer += delta_time
            move_interval = self.ai.tick_rate * 0.15  # sub-steps for moving into position

            if self.ai_exec_timer >= move_interval:
                self.ai_exec_timer = 0.0
                target_col, target_rot = self.ai_target

                # First handle rotation
                if ab.rotation != target_rot:
                    ab._rotate()
                # Then handle horizontal movement
                elif ab.piece_col < target_col:
                    ab._move(1)
                elif ab.piece_col > target_col:
                    ab._move(-1)
                else:
                    # In position - hard drop
                    lines = ab._hard_drop()
                    self._send_garbage('ai', lines)
                    self.ai_target = None
                    self.ai_executing = False
                    return

        # Gravity for AI (slower to give visual effect, but AI hard drops when ready)
        ab.fall_timer += delta_time
        ai_interval = self.ai.tick_rate
        if ab.fall_timer >= ai_interval:
            ab.fall_timer = 0.0
            if ab._valid_position(ab.current_type, ab.rotation, ab.piece_col, ab.piece_row - 1):
                ab.piece_row -= 1
                ab.lock_timer = -1.0
            else:
                if ab.lock_timer < 0:
                    ab.lock_timer = 0.0
                ab.lock_timer += ai_interval
                if ab.lock_timer >= LOCK_DELAY * 2:
                    # Safety: lock piece if AI hasn't hard-dropped in time
                    lines = ab._lock_piece()
                    self._send_garbage('ai', lines)
                    self.ai_target = None
                    self.ai_executing = False

    # ------------------------------------------------------------------
    # Arcade View callbacks
    # ------------------------------------------------------------------
    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_update(self, delta_time):
        if self.selecting_difficulty or not self.game_active:
            return

        self._update_player(delta_time)
        self._update_ai(delta_time)
        self._check_game_over()

    def on_key_press(self, key, modifiers):
        if not self.game_active and not self.selecting_difficulty:
            if key == arcade.key.RETURN:
                self.selecting_difficulty = True
            return

        if self.selecting_difficulty:
            return

        p = self.player
        if p.game_over:
            return

        if key == arcade.key.LEFT:
            p._move(-1)
        elif key == arcade.key.RIGHT:
            p._move(1)
        elif key == arcade.key.UP:
            p._rotate()
        elif key == arcade.key.DOWN:
            p.soft_drop = True
        elif key == arcade.key.SPACE:
            lines = p._hard_drop()
            self._send_garbage('player', lines)

    def on_key_release(self, key, modifiers):
        if self.player and key == arcade.key.DOWN:
            self.player.soft_drop = False

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if self.btn_back.contains(x, y):
            self.window.show_view(self.menu_view)
            return
        if self.btn_help.contains(x, y):
            rules_view = RulesView("Tetris VS", "tetris_vs.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self.selecting_difficulty:
            if self.btn_easy.contains(x, y):
                self._init_game('easy')
            elif self.btn_medium.contains(x, y):
                self._init_game('medium')
            elif self.btn_hard.contains(x, y):
                self._init_game('hard')

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def on_draw(self):
        self.clear()
        tetris_vs_renderer.draw(self)
