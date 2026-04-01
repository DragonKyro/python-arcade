"""
Tetris game view for Python Arcade 3.x.
Classic Tetris gameplay with standard 7 tetrominoes, scoring, levels, and ghost piece.
"""

import arcade
import random
from pages.rules import RulesView

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
CELL_SIZE = 25
BOARD_COLS = 10
BOARD_ROWS = 20

# Board positioning — left-of-center to leave room for side panel
BOARD_PIXEL_W = BOARD_COLS * CELL_SIZE   # 250
BOARD_PIXEL_H = BOARD_ROWS * CELL_SIZE   # 500
BOARD_ORIGIN_X = (WIDTH // 2 - BOARD_PIXEL_W) // 2 + 40
BOARD_ORIGIN_Y = (HEIGHT - TOP_BAR_HEIGHT - BOARD_PIXEL_H) // 2

# Side panel
PANEL_X = BOARD_ORIGIN_X + BOARD_PIXEL_W + 40

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

# Ghost piece alpha
GHOST_ALPHA = 60

# Timing
BASE_TICK = 0.8
MIN_TICK = 0.1
LOCK_DELAY = 0.3

# Scoring for 1, 2, 3, 4 lines
LINE_SCORES = [100, 300, 500, 800]

# -------------------------------------------------------------------
# Tetromino definitions: each piece has 4 rotation states.
# Each state is a list of (row, col) offsets from the piece origin.
# -------------------------------------------------------------------
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

# Wall kick offsets to try when rotation collides (standard SRS-lite)
WALL_KICKS = [(0, 0), (-1, 0), (1, 0), (0, 1), (-1, 1), (1, 1), (-2, 0), (2, 0)]


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
        arcade.draw_text(
            self.label,
            self.cx,
            self.cy,
            BUTTON_TEXT_COLOR,
            font_size=14,
            anchor_x="center",
            anchor_y="center",
        )


def _cell_to_screen(col, row):
    """Convert board (col, row) to screen center (x, y). Row 0 is bottom."""
    x = BOARD_ORIGIN_X + col * CELL_SIZE + CELL_SIZE // 2
    y = BOARD_ORIGIN_Y + row * CELL_SIZE + CELL_SIZE // 2
    return x, y


class TetrisView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.mouse_x = 0
        self.mouse_y = 0

        # Buttons
        self.btn_back = _Button(60, HEIGHT - 25, 90, 34, "Back")
        self.btn_new = _Button(WIDTH - 80, HEIGHT - 25, 110, 34, "New Game")
        self.btn_help = _Button(WIDTH - 150, HEIGHT - 25, 40, 40, "?")

        self._init_game()

    # ------------------------------------------------------------------
    # Game state
    # ------------------------------------------------------------------
    def _init_game(self):
        """Initialize / reset all game state."""
        # Board: 2D list [row][col], None means empty, otherwise color tuple
        self.board = [[None] * BOARD_COLS for _ in range(BOARD_ROWS)]
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.fall_timer = 0.0
        self.lock_timer = -1.0  # negative means not locking
        self.soft_drop = False

        # Piece bag (7-bag randomizer)
        self.bag = []
        self._fill_bag()
        self.next_piece_type = self._pop_bag()
        self._spawn_piece()

    def _fill_bag(self):
        """Refill the piece bag with a shuffled set of all 7 tetrominoes."""
        pieces = list(TETROMINOES.keys())
        random.shuffle(pieces)
        self.bag.extend(pieces)

    def _pop_bag(self):
        if not self.bag:
            self._fill_bag()
        return self.bag.pop()

    def _spawn_piece(self):
        """Spawn the next piece at the top of the board."""
        self.current_type = self.next_piece_type
        self.next_piece_type = self._pop_bag()
        self.rotation = 0
        # Spawn position: centered, top of board
        self.piece_col = BOARD_COLS // 2 - 2
        self.piece_row = BOARD_ROWS - 1  # will be adjusted
        # Find the lowest occupied row in the piece shape so we can place it at the top
        shape = TETROMINOES[self.current_type][self.rotation]
        max_r = max(r for r, c in shape)
        self.piece_row = BOARD_ROWS - 1 - max_r + 1  # top visible row

        self.fall_timer = 0.0
        self.lock_timer = -1.0
        self.soft_drop = False

        # Check if spawn position is valid — if not, game over
        if not self._valid_position(self.current_type, self.rotation, self.piece_col, self.piece_row):
            self.game_over = True

    # ------------------------------------------------------------------
    # Collision helpers
    # ------------------------------------------------------------------
    def _get_cells(self, piece_type, rotation, col, row):
        """Return list of (board_col, board_row) for a piece at given position."""
        shape = TETROMINOES[piece_type][rotation]
        cells = []
        for dr, dc in shape:
            cells.append((col + dc, row - dr))
        return cells

    def _valid_position(self, piece_type, rotation, col, row):
        """Check if piece at given position is valid (in bounds and no overlap)."""
        for bc, br in self._get_cells(piece_type, rotation, col, row):
            if bc < 0 or bc >= BOARD_COLS:
                return False
            if br < 0 or br >= BOARD_ROWS:
                return False
            if self.board[br][bc] is not None:
                return False
        return True

    def _ghost_row(self):
        """Find the lowest row where the current piece can be placed."""
        row = self.piece_row
        while self._valid_position(self.current_type, self.rotation, self.piece_col, row - 1):
            row -= 1
        return row

    # ------------------------------------------------------------------
    # Piece actions
    # ------------------------------------------------------------------
    def _move(self, dc):
        """Move current piece left/right by dc columns."""
        new_col = self.piece_col + dc
        if self._valid_position(self.current_type, self.rotation, new_col, self.piece_row):
            self.piece_col = new_col
            # If we moved and piece can now fall, reset lock timer
            if self._valid_position(self.current_type, self.rotation, self.piece_col, self.piece_row - 1):
                self.lock_timer = -1.0

    def _rotate(self):
        """Rotate piece clockwise with wall kicks."""
        new_rot = (self.rotation + 1) % 4
        for dx, dy in WALL_KICKS:
            new_col = self.piece_col + dx
            new_row = self.piece_row + dy
            if self._valid_position(self.current_type, new_rot, new_col, new_row):
                self.rotation = new_rot
                self.piece_col = new_col
                self.piece_row = new_row
                # Reset lock timer if rotation succeeds
                if self._valid_position(self.current_type, self.rotation, self.piece_col, self.piece_row - 1):
                    self.lock_timer = -1.0
                return

    def _hard_drop(self):
        """Instantly drop piece to ghost position and lock."""
        drop_row = self._ghost_row()
        # Score bonus for hard drop distance
        self.score += (self.piece_row - drop_row) * 2
        self.piece_row = drop_row
        self._lock_piece()

    def _lock_piece(self):
        """Lock current piece onto the board and spawn the next one."""
        color = PIECE_COLORS[self.current_type]
        for bc, br in self._get_cells(self.current_type, self.rotation, self.piece_col, self.piece_row):
            if 0 <= br < BOARD_ROWS and 0 <= bc < BOARD_COLS:
                self.board[br][bc] = color

        self._clear_lines()
        self._spawn_piece()

    def _clear_lines(self):
        """Check and clear full rows, update score/level."""
        full_rows = []
        for r in range(BOARD_ROWS):
            if all(self.board[r][c] is not None for c in range(BOARD_COLS)):
                full_rows.append(r)

        if not full_rows:
            return

        # Remove full rows (from top to bottom to keep indices stable)
        for r in sorted(full_rows, reverse=True):
            del self.board[r]

        # Add empty rows at the top
        for _ in full_rows:
            self.board.append([None] * BOARD_COLS)

        count = len(full_rows)
        self.lines_cleared += count
        self.score += LINE_SCORES[min(count, 4) - 1] * self.level
        self.level = self.lines_cleared // 10 + 1

    def _tick_interval(self):
        """Return the current gravity tick interval based on level."""
        interval = BASE_TICK - (self.level - 1) * 0.07
        return max(interval, MIN_TICK)

    # ------------------------------------------------------------------
    # Arcade View callbacks
    # ------------------------------------------------------------------
    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_update(self, delta_time):
        if self.game_over:
            return

        interval = self._tick_interval()
        if self.soft_drop:
            interval = max(interval * 0.1, MIN_TICK * 0.5)

        self.fall_timer += delta_time

        if self.fall_timer >= interval:
            self.fall_timer = 0.0
            # Try to move piece down
            if self._valid_position(self.current_type, self.rotation, self.piece_col, self.piece_row - 1):
                self.piece_row -= 1
                self.lock_timer = -1.0
                if self.soft_drop:
                    self.score += 1  # soft drop bonus
            else:
                # Piece can't move down — start or continue lock timer
                if self.lock_timer < 0:
                    self.lock_timer = 0.0
                self.lock_timer += interval
                if self.lock_timer >= LOCK_DELAY:
                    self._lock_piece()

    def on_key_press(self, key, modifiers):
        if self.game_over:
            # Allow new game on Enter
            if key == arcade.key.RETURN:
                self._init_game()
            return

        if key == arcade.key.LEFT:
            self._move(-1)
        elif key == arcade.key.RIGHT:
            self._move(1)
        elif key == arcade.key.UP:
            self._rotate()
        elif key == arcade.key.DOWN:
            self.soft_drop = True
        elif key == arcade.key.SPACE:
            self._hard_drop()

    def on_key_release(self, key, modifiers):
        if key == arcade.key.DOWN:
            self.soft_drop = False

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if self.btn_back.contains(x, y):
            self.window.show_view(self.menu_view)
        elif self.btn_new.contains(x, y):
            self._init_game()
        elif self.btn_help.contains(x, y):
            rules_view = RulesView("Tetris", "tetris.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def on_draw(self):
        self.clear()

        self._draw_board_bg()
        self._draw_grid_lines()
        self._draw_locked_cells()
        if not self.game_over:
            self._draw_ghost()
            self._draw_current_piece()
        self._draw_board_outline()
        self._draw_side_panel()
        self._draw_top_bar()

        if self.game_over:
            self._draw_game_over()

    def _draw_board_bg(self):
        """Draw the dark board background."""
        cx = BOARD_ORIGIN_X + BOARD_PIXEL_W / 2
        cy = BOARD_ORIGIN_Y + BOARD_PIXEL_H / 2
        arcade.draw_rect_filled(
            arcade.XYWH(cx, cy, BOARD_PIXEL_W, BOARD_PIXEL_H),
            BOARD_BG_COLOR,
        )

    def _draw_grid_lines(self):
        """Draw faint grid lines on the board."""
        for c in range(BOARD_COLS + 1):
            x = BOARD_ORIGIN_X + c * CELL_SIZE
            arcade.draw_line(
                x, BOARD_ORIGIN_Y,
                x, BOARD_ORIGIN_Y + BOARD_PIXEL_H,
                GRID_LINE_COLOR, 1,
            )
        for r in range(BOARD_ROWS + 1):
            y = BOARD_ORIGIN_Y + r * CELL_SIZE
            arcade.draw_line(
                BOARD_ORIGIN_X, y,
                BOARD_ORIGIN_X + BOARD_PIXEL_W, y,
                GRID_LINE_COLOR, 1,
            )

    def _draw_board_outline(self):
        """Draw the board border."""
        cx = BOARD_ORIGIN_X + BOARD_PIXEL_W / 2
        cy = BOARD_ORIGIN_Y + BOARD_PIXEL_H / 2
        arcade.draw_rect_outline(
            arcade.XYWH(cx, cy, BOARD_PIXEL_W, BOARD_PIXEL_H),
            LINE_COLOR, 2,
        )

    def _draw_cell(self, col, row, color, outline_color=None):
        """Draw a single cell on the board."""
        x, y = _cell_to_screen(col, row)
        arcade.draw_rect_filled(
            arcade.XYWH(x, y, CELL_SIZE - 2, CELL_SIZE - 2),
            color,
        )
        if outline_color:
            arcade.draw_rect_outline(
                arcade.XYWH(x, y, CELL_SIZE - 2, CELL_SIZE - 2),
                outline_color, 1,
            )

    def _draw_locked_cells(self):
        """Draw all locked cells on the board."""
        for r in range(BOARD_ROWS):
            for c in range(BOARD_COLS):
                color = self.board[r][c]
                if color is not None:
                    # Subtle lighter outline
                    outline = tuple(min(v + 40, 255) for v in color)
                    self._draw_cell(c, r, color, outline)

    def _draw_current_piece(self):
        """Draw the currently falling piece."""
        color = PIECE_COLORS[self.current_type]
        outline = tuple(min(v + 40, 255) for v in color)
        for bc, br in self._get_cells(self.current_type, self.rotation, self.piece_col, self.piece_row):
            if 0 <= br < BOARD_ROWS:
                self._draw_cell(bc, br, color, outline)

    def _draw_ghost(self):
        """Draw translucent ghost piece showing landing position."""
        ghost_r = self._ghost_row()
        if ghost_r == self.piece_row:
            return  # ghost is at current position, skip
        base_color = PIECE_COLORS[self.current_type]
        ghost_color = (base_color[0], base_color[1], base_color[2], GHOST_ALPHA)
        for bc, br in self._get_cells(self.current_type, self.rotation, self.piece_col, ghost_r):
            if 0 <= br < BOARD_ROWS:
                x, y = _cell_to_screen(bc, br)
                arcade.draw_rect_filled(
                    arcade.XYWH(x, y, CELL_SIZE - 2, CELL_SIZE - 2),
                    ghost_color,
                )
                arcade.draw_rect_outline(
                    arcade.XYWH(x, y, CELL_SIZE - 2, CELL_SIZE - 2),
                    ghost_color, 1,
                )

    def _draw_side_panel(self):
        """Draw next piece preview, score, level, and lines on the right."""
        x = PANEL_X
        top_y = BOARD_ORIGIN_Y + BOARD_PIXEL_H

        # Title
        arcade.draw_text(
            "TETRIS",
            x, top_y + 10,
            SCORE_COLOR,
            font_size=22,
            bold=True,
            anchor_x="left",
            anchor_y="bottom",
        )

        # Next piece label
        y = top_y - 20
        arcade.draw_text("NEXT", x, y, STATUS_TEXT_COLOR, font_size=14, anchor_x="left", anchor_y="top")

        # Draw next piece preview
        preview_y = y - 25
        shape = TETROMINOES[self.next_piece_type][0]
        color = PIECE_COLORS[self.next_piece_type]
        outline = tuple(min(v + 40, 255) for v in color)
        preview_size = 20
        for dr, dc in shape:
            px = x + dc * preview_size + preview_size // 2
            py = preview_y - dr * preview_size - preview_size // 2
            arcade.draw_rect_filled(
                arcade.XYWH(px, py, preview_size - 2, preview_size - 2),
                color,
            )
            arcade.draw_rect_outline(
                arcade.XYWH(px, py, preview_size - 2, preview_size - 2),
                outline, 1,
            )

        # Stats
        stats_y = preview_y - 110
        arcade.draw_text("SCORE", x, stats_y, STATUS_TEXT_COLOR, font_size=13, anchor_x="left", anchor_y="top")
        arcade.draw_text(
            str(self.score), x, stats_y - 20, SCORE_COLOR,
            font_size=18, bold=True, anchor_x="left", anchor_y="top",
        )

        stats_y -= 60
        arcade.draw_text("LEVEL", x, stats_y, STATUS_TEXT_COLOR, font_size=13, anchor_x="left", anchor_y="top")
        arcade.draw_text(
            str(self.level), x, stats_y - 20, SCORE_COLOR,
            font_size=18, bold=True, anchor_x="left", anchor_y="top",
        )

        stats_y -= 60
        arcade.draw_text("LINES", x, stats_y, STATUS_TEXT_COLOR, font_size=13, anchor_x="left", anchor_y="top")
        arcade.draw_text(
            str(self.lines_cleared), x, stats_y - 20, SCORE_COLOR,
            font_size=18, bold=True, anchor_x="left", anchor_y="top",
        )

        # Controls hint
        stats_y -= 80
        controls = [
            "CONTROLS",
            "← →  Move",
            "↑    Rotate",
            "↓    Soft Drop",
            "Space Hard Drop",
        ]
        for i, line in enumerate(controls):
            fs = 11 if i > 0 else 12
            c = STATUS_TEXT_COLOR if i > 0 else SCORE_COLOR
            arcade.draw_text(
                line, x, stats_y - i * 18, c,
                font_size=fs, anchor_x="left", anchor_y="top",
            )

    def _draw_top_bar(self):
        """Draw buttons on the top bar."""
        # Dim bar background
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT - TOP_BAR_HEIGHT / 2, WIDTH, TOP_BAR_HEIGHT),
            (30, 30, 46, 220),
        )

        self.btn_back.draw(self.btn_back.contains(self.mouse_x, self.mouse_y))
        self.btn_new.draw(self.btn_new.contains(self.mouse_x, self.mouse_y))
        self.btn_help.draw(self.btn_help.contains(self.mouse_x, self.mouse_y))

    def _draw_game_over(self):
        """Draw game over overlay."""
        # Semi-transparent overlay
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
            OVERLAY_COLOR,
        )

        arcade.draw_text(
            "GAME OVER",
            WIDTH / 2, HEIGHT / 2 + 30,
            (243, 139, 168),
            font_size=36,
            bold=True,
            anchor_x="center",
            anchor_y="center",
        )
        arcade.draw_text(
            f"Score: {self.score}",
            WIDTH / 2, HEIGHT / 2 - 15,
            SCORE_COLOR,
            font_size=20,
            anchor_x="center",
            anchor_y="center",
        )
        arcade.draw_text(
            "Press ENTER or click New Game to play again",
            WIDTH / 2, HEIGHT / 2 - 50,
            STATUS_TEXT_COLOR,
            font_size=13,
            anchor_x="center",
            anchor_y="center",
        )
