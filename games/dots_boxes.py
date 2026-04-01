"""
Dots and Boxes game view for Python Arcade 2.6.x.
"""

import arcade

from ai.dots_boxes_ai import DotsBoxesAI
from pages.components import Button
from pages.rules import RulesView
from renderers import dots_boxes_renderer
from renderers.dots_boxes_renderer import (
    WIDTH, HEIGHT,
    GRID_ROWS, GRID_COLS,
    DOT_SPACING,
    HIT_TOLERANCE,
    BTN_W, BTN_H, BTN_BACK_X, BTN_BACK_Y, BTN_NEW_X, BTN_NEW_Y,
    _dot_pos,
)


class DotsBoxesView(arcade.View):
    """Dots and Boxes: player vs AI."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.ai = DotsBoxesAI()
        self.help_button = Button(WIDTH - 135, HEIGHT - 25, 40, 32, "?", color=arcade.color.DARK_SLATE_BLUE)
        dots_boxes_renderer.create_text_objects(self)
        self._init_game()

    # ------------------------------------------------------------------ #
    # State helpers
    # ------------------------------------------------------------------ #
    def _init_game(self):
        # Horizontal lines: (GRID_ROWS+1) x GRID_COLS
        self.h_lines = [[False] * GRID_COLS for _ in range(GRID_ROWS + 1)]
        # Vertical lines: GRID_ROWS x (GRID_COLS+1)
        self.v_lines = [[False] * (GRID_COLS + 1) for _ in range(GRID_ROWS)]

        # Who drew each line: same shape, value None / 'player' / 'ai'
        self.h_owners = [[None] * GRID_COLS for _ in range(GRID_ROWS + 1)]
        self.v_owners = [[None] * (GRID_COLS + 1) for _ in range(GRID_ROWS)]

        # Box owners: GRID_ROWS x GRID_COLS, None / 'player' / 'ai'
        self.box_owner = [[None] * GRID_COLS for _ in range(GRID_ROWS)]

        self.player_score = 0
        self.ai_score = 0
        self.current_turn = 'player'  # 'player' or 'ai'
        self.game_over = False

        # AI delay accumulator
        self.ai_timer = 0.0
        self.ai_delay = 0.3

    def _all_lines_drawn(self):
        for row in self.h_lines:
            if False in row:
                return False
        for row in self.v_lines:
            if False in row:
                return False
        return True

    def _place_line(self, orientation, r, c, who):
        """Place a line and check for completed boxes. Return number of boxes completed."""
        if orientation == 'h':
            self.h_lines[r][c] = True
            self.h_owners[r][c] = who
        else:
            self.v_lines[r][c] = True
            self.v_owners[r][c] = who

        completed = 0
        boxes_to_check = []
        if orientation == 'h':
            if r > 0:
                boxes_to_check.append((r - 1, c))
            if r < GRID_ROWS:
                boxes_to_check.append((r, c))
        else:
            if c > 0:
                boxes_to_check.append((r, c - 1))
            if c < GRID_COLS:
                boxes_to_check.append((r, c))

        for br, bc in boxes_to_check:
            if self.box_owner[br][bc] is None:
                if self.ai.count_sides(self.h_lines, self.v_lines, br, bc) == 4:
                    self.box_owner[br][bc] = who
                    if who == 'player':
                        self.player_score += 1
                    else:
                        self.ai_score += 1
                    completed += 1

        if self._all_lines_drawn():
            self.game_over = True

        return completed

    # ------------------------------------------------------------------ #
    # Input
    # ------------------------------------------------------------------ #
    def _closest_line(self, mx, my):
        """Return (orientation, r, c, dist) of the closest undrawn line to (mx, my)."""
        best = None
        best_dist = float('inf')

        # Check horizontal lines
        for r in range(GRID_ROWS + 1):
            for c in range(GRID_COLS):
                if self.h_lines[r][c]:
                    continue
                x1, y1 = _dot_pos(r, c)
                x2, y2 = _dot_pos(r, c + 1)
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                d = ((mx - cx) ** 2 + (my - cy) ** 2) ** 0.5
                if d < best_dist:
                    best_dist = d
                    best = ('h', r, c, d)

        # Check vertical lines
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS + 1):
                if self.v_lines[r][c]:
                    continue
                x1, y1 = _dot_pos(r, c)
                x2, y2 = _dot_pos(r + 1, c)
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                d = ((mx - cx) ** 2 + (my - cy) ** 2) ** 0.5
                if d < best_dist:
                    best_dist = d
                    best = ('v', r, c, d)

        return best

    def on_mouse_press(self, x, y, button, modifiers):
        # Back button
        if (BTN_BACK_X - BTN_W / 2 <= x <= BTN_BACK_X + BTN_W / 2
                and BTN_BACK_Y - BTN_H / 2 <= y <= BTN_BACK_Y + BTN_H / 2):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if (BTN_NEW_X - BTN_W / 2 <= x <= BTN_NEW_X + BTN_W / 2
                and BTN_NEW_Y - BTN_H / 2 <= y <= BTN_NEW_Y + BTN_H / 2):
            self._init_game()
            return

        # Help button
        if self.help_button.hit_test(x, y):
            rules_view = RulesView("Dots and Boxes", "dots_boxes.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self.game_over or self.current_turn != 'player':
            return

        result = self._closest_line(x, y)
        if result is None:
            return
        orientation, r, c, dist = result
        if dist > HIT_TOLERANCE + DOT_SPACING / 2:
            return

        completed = self._place_line(orientation, r, c, 'player')
        if not self.game_over and completed == 0:
            self.current_turn = 'ai'
            self.ai_timer = 0.0

    # ------------------------------------------------------------------ #
    # Update (AI turn)
    # ------------------------------------------------------------------ #
    def on_update(self, delta_time):
        if self.game_over or self.current_turn != 'ai':
            return

        self.ai_timer += delta_time
        if self.ai_timer < self.ai_delay:
            return

        move = self.ai.get_move(self.h_lines, self.v_lines, GRID_ROWS, GRID_COLS)
        if move is None:
            self.game_over = True
            return

        orientation, r, c = move
        completed = self._place_line(orientation, r, c, 'ai')

        if not self.game_over:
            if completed > 0:
                # AI gets another turn; reset timer
                self.ai_timer = 0.0
            else:
                self.current_turn = 'player'

    # ------------------------------------------------------------------ #
    # Drawing
    # ------------------------------------------------------------------ #
    def on_draw(self):
        self.clear()
        dots_boxes_renderer.draw(self)
