"""
Battleship game view for Python Arcade 2.6.x.
Two-phase game: placement then battle against an AI opponent.
"""

import arcade
import random

from ai.battleship_ai import BattleshipAI

# Window constants
WIDTH = 800
HEIGHT = 600

# Grid / cell constants
GRID_SIZE = 10
CELL_SIZE = 28
GRID_PIXEL = GRID_SIZE * CELL_SIZE  # 280

# Layout positions
PLAYER_GRID_LEFT = 30
AI_GRID_LEFT = WIDTH - GRID_PIXEL - 30
GRID_TOP = HEIGHT - 80

# Ship sizes for a standard game
SHIP_SIZES = [5, 4, 3, 3, 2]
SHIP_NAMES = ["Carrier (5)", "Battleship (4)", "Cruiser (3)", "Submarine (3)", "Destroyer (2)"]

# Colors
COLOR_WATER = (173, 216, 230)
COLOR_SHIP = (128, 128, 128)
COLOR_HIT = (220, 50, 50)
COLOR_MISS_DOT = (255, 255, 255)
COLOR_GRID_LINE = (60, 60, 80)
COLOR_PREVIEW_VALID = (100, 200, 100, 120)
COLOR_PREVIEW_INVALID = (200, 100, 100, 120)
COLOR_SUNK = (180, 40, 40)

# Button geometry
BTN_W = 90
BTN_H = 30

AI_SHOT_DELAY = 0.5  # seconds


class BattleshipView(arcade.View):
    """Main view for the Battleship game."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.new_game()

    # ------------------------------------------------------------------ #
    #  Game state reset
    # ------------------------------------------------------------------ #

    def new_game(self):
        """Initialize / reset all game state."""
        # Phase: "placement" or "battle" or "gameover"
        self.phase = "placement"
        self.turn = "player"  # "player" or "ai"
        self.winner = None

        # Player board: 0=empty, 1=ship, 2=hit, 3=miss
        self.player_board = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.player_ships = []  # list of sets of (r,c)
        self.player_ships_sunk = [False] * len(SHIP_SIZES)

        # Placement state
        self.placement_index = 0  # which ship we're placing next
        self.placement_horizontal = True
        self.hover_cell = None  # (row, col) under cursor on player grid

        # AI
        self.ai = BattleshipAI(GRID_SIZE)
        self.ai.place_ships(SHIP_SIZES)

        # Tracking board for player's shots at AI
        self.player_shot_board = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.ai_ships_sunk_cells = set()  # revealed sunk ship cells

        # AI turn timer
        self.ai_timer = 0.0

        # Status message
        self.message = "Place your Carrier (5 cells). R to rotate."

    # ------------------------------------------------------------------ #
    #  Coordinate helpers
    # ------------------------------------------------------------------ #

    def _grid_to_screen(self, grid_left, row, col):
        """Return center (x, y) for a cell."""
        x = grid_left + col * CELL_SIZE + CELL_SIZE // 2
        y = GRID_TOP - row * CELL_SIZE - CELL_SIZE // 2
        return x, y

    def _screen_to_grid(self, grid_left, sx, sy):
        """Return (row, col) or None if outside grid."""
        col = int((sx - grid_left) / CELL_SIZE)
        row = int((GRID_TOP - sy) / CELL_SIZE)
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            return row, col
        return None

    # ------------------------------------------------------------------ #
    #  Placement helpers
    # ------------------------------------------------------------------ #

    def _placement_cells(self, row, col):
        """Return list of (r, c) for current ship at (row, col), or None if invalid."""
        size = SHIP_SIZES[self.placement_index]
        cells = []
        for i in range(size):
            r = row if self.placement_horizontal else row + i
            c = col + i if self.placement_horizontal else col
            if r < 0 or r >= GRID_SIZE or c < 0 or c >= GRID_SIZE:
                return None
            cells.append((r, c))
        return cells

    def _placement_valid(self, cells):
        if cells is None:
            return False
        for r, c in cells:
            if self.player_board[r][c] != 0:
                return False
        return True

    # ------------------------------------------------------------------ #
    #  Drawing
    # ------------------------------------------------------------------ #

    def on_draw(self):
        self.clear()
        self._draw_background()
        self._draw_buttons()

        if self.phase == "placement":
            self._draw_grid(PLAYER_GRID_LEFT, self.player_board, show_ships=True)
            self._draw_placement_preview()
            self._draw_ship_list()
        else:
            self._draw_grid(PLAYER_GRID_LEFT, self.player_board, show_ships=True)
            self._draw_ai_grid()
            self._draw_labels()

        self._draw_message()

    def _draw_background(self):
        arcade.draw_rect_filled(arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), (30, 30, 50))

    def _draw_buttons(self):
        # Back button
        bx, by = 55, HEIGHT - 22
        arcade.draw_rect_filled(arcade.XYWH(bx, by, BTN_W, BTN_H), (80, 80, 100))
        arcade.draw_rect_outline(arcade.XYWH(bx, by, BTN_W, BTN_H), arcade.color.WHITE)
        arcade.draw_text("Back", bx, by, arcade.color.WHITE, 13, anchor_x="center", anchor_y="center")

        # New Game button
        nx, ny = WIDTH - 55, HEIGHT - 22
        arcade.draw_rect_filled(arcade.XYWH(nx, ny, BTN_W, BTN_H), (80, 80, 100))
        arcade.draw_rect_outline(arcade.XYWH(nx, ny, BTN_W, BTN_H), arcade.color.WHITE)
        arcade.draw_text("New Game", nx, ny, arcade.color.WHITE, 13, anchor_x="center", anchor_y="center")

    def _draw_grid(self, left, board, show_ships=False):
        """Draw a 10x10 grid from a 2D board array."""
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x, y = self._grid_to_screen(left, row, col)
                val = board[row][col]

                # Background
                if val == 1 and show_ships:
                    color = COLOR_SHIP
                elif val == 2:
                    color = COLOR_HIT
                elif val == 3:
                    color = COLOR_WATER
                else:
                    color = COLOR_WATER

                arcade.draw_rect_filled(arcade.XYWH(x, y, CELL_SIZE - 1, CELL_SIZE - 1), color)
                arcade.draw_rect_outline(arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE), COLOR_GRID_LINE)

                # Miss dot
                if val == 3:
                    arcade.draw_circle_filled(x, y, 5, COLOR_MISS_DOT)

                # Hit X
                if val == 2:
                    hs = CELL_SIZE // 2 - 4
                    arcade.draw_line(x - hs, y - hs, x + hs, y + hs, (255, 255, 255), 2)
                    arcade.draw_line(x - hs, y + hs, x + hs, y - hs, (255, 255, 255), 2)

        # Column / row labels
        for i in range(GRID_SIZE):
            lx = left + i * CELL_SIZE + CELL_SIZE // 2
            ly_top = GRID_TOP + 10
            arcade.draw_text(str(i), lx, ly_top, arcade.color.WHITE, 10, anchor_x="center", anchor_y="center")
            lx_side = left - 12
            ly_side = GRID_TOP - i * CELL_SIZE - CELL_SIZE // 2
            arcade.draw_text(chr(65 + i), lx_side, ly_side, arcade.color.WHITE, 10, anchor_x="center", anchor_y="center")

    def _draw_ai_grid(self):
        """Draw the AI grid showing only the player's shots (and sunk ships)."""
        left = AI_GRID_LEFT
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x, y = self._grid_to_screen(left, row, col)
                val = self.player_shot_board[row][col]

                if (row, col) in self.ai_ships_sunk_cells:
                    color = COLOR_SUNK
                elif val == 2:
                    color = COLOR_HIT
                elif val == 3:
                    color = COLOR_WATER
                else:
                    # In game-over, reveal AI ships
                    if self.phase == "gameover" and self.ai.board[row][col] in (1,):
                        color = COLOR_SHIP
                    else:
                        color = COLOR_WATER

                arcade.draw_rect_filled(arcade.XYWH(x, y, CELL_SIZE - 1, CELL_SIZE - 1), color)
                arcade.draw_rect_outline(arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE), COLOR_GRID_LINE)

                if val == 3:
                    arcade.draw_circle_filled(x, y, 5, COLOR_MISS_DOT)
                if val == 2:
                    hs = CELL_SIZE // 2 - 4
                    arcade.draw_line(x - hs, y - hs, x + hs, y + hs, (255, 255, 255), 2)
                    arcade.draw_line(x - hs, y + hs, x + hs, y - hs, (255, 255, 255), 2)

        # Labels
        for i in range(GRID_SIZE):
            lx = left + i * CELL_SIZE + CELL_SIZE // 2
            arcade.draw_text(str(i), lx, GRID_TOP + 10, arcade.color.WHITE, 10, anchor_x="center", anchor_y="center")
            ly_side = GRID_TOP - i * CELL_SIZE - CELL_SIZE // 2
            arcade.draw_text(chr(65 + i), left - 12, ly_side, arcade.color.WHITE, 10, anchor_x="center", anchor_y="center")

    def _draw_placement_preview(self):
        """Show translucent preview of ship being placed."""
        if self.hover_cell is None:
            return
        if self.placement_index >= len(SHIP_SIZES):
            return
        row, col = self.hover_cell
        cells = self._placement_cells(row, col)
        valid = self._placement_valid(cells)
        color = COLOR_PREVIEW_VALID if valid else COLOR_PREVIEW_INVALID

        if cells is None:
            # Show partial preview even when out of bounds
            size = SHIP_SIZES[self.placement_index]
            cells = []
            for i in range(size):
                r = row if self.placement_horizontal else row + i
                c = col + i if self.placement_horizontal else col
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                    cells.append((r, c))
            color = COLOR_PREVIEW_INVALID

        for r, c in cells:
            x, y = self._grid_to_screen(PLAYER_GRID_LEFT, r, c)
            arcade.draw_rect_filled(arcade.XYWH(x, y, CELL_SIZE - 1, CELL_SIZE - 1), color)

    def _draw_ship_list(self):
        """Draw the list of ships during placement phase."""
        sx = PLAYER_GRID_LEFT + GRID_PIXEL + 40
        sy = GRID_TOP - 10
        arcade.draw_text("Ships:", sx, sy, arcade.color.WHITE, 14, bold=True)
        for i, name in enumerate(SHIP_NAMES):
            color = (100, 200, 100) if i < self.placement_index else (200, 200, 200)
            prefix = "[x] " if i < self.placement_index else "[ ] "
            if i == self.placement_index:
                prefix = ">>> "
                color = (255, 255, 100)
            arcade.draw_text(prefix + name, sx, sy - 25 - i * 22, color, 12)

    def _draw_labels(self):
        """Draw grid titles during battle phase."""
        px = PLAYER_GRID_LEFT + GRID_PIXEL // 2
        ax = AI_GRID_LEFT + GRID_PIXEL // 2
        label_y = GRID_TOP + 26
        arcade.draw_text("Your Board", px, label_y, arcade.color.WHITE, 14, anchor_x="center", bold=True)
        arcade.draw_text("Enemy Board", ax, label_y, arcade.color.WHITE, 14, anchor_x="center", bold=True)

    def _draw_message(self):
        """Draw status message at the bottom."""
        arcade.draw_text(self.message, WIDTH // 2, 30, arcade.color.YELLOW, 15, anchor_x="center", anchor_y="center")

    # ------------------------------------------------------------------ #
    #  Input handling
    # ------------------------------------------------------------------ #

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R and self.phase == "placement":
            self.placement_horizontal = not self.placement_horizontal
            orient = "horizontal" if self.placement_horizontal else "vertical"
            self.message = f"Orientation: {orient}. Click to place."

    def on_mouse_motion(self, x, y, dx, dy):
        if self.phase == "placement":
            cell = self._screen_to_grid(PLAYER_GRID_LEFT, x, y)
            self.hover_cell = cell
        else:
            self.hover_cell = None

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Back button
        bx, by = 55, HEIGHT - 22
        if abs(x - bx) < BTN_W // 2 and abs(y - by) < BTN_H // 2:
            self.window.show_view(self.menu_view)
            return

        # New Game button
        nx, ny = WIDTH - 55, HEIGHT - 22
        if abs(x - nx) < BTN_W // 2 and abs(y - ny) < BTN_H // 2:
            self.new_game()
            return

        if self.phase == "placement":
            self._handle_placement_click(x, y)
        elif self.phase == "battle" and self.turn == "player":
            self._handle_battle_click(x, y)

    # ------------------------------------------------------------------ #
    #  Placement logic
    # ------------------------------------------------------------------ #

    def _handle_placement_click(self, x, y):
        if self.placement_index >= len(SHIP_SIZES):
            return
        cell = self._screen_to_grid(PLAYER_GRID_LEFT, x, y)
        if cell is None:
            return
        row, col = cell
        cells = self._placement_cells(row, col)
        if not self._placement_valid(cells):
            self.message = "Invalid placement! Try again."
            return

        ship_cells = set()
        for r, c in cells:
            self.player_board[r][c] = 1
            ship_cells.add((r, c))
        self.player_ships.append(ship_cells)
        self.placement_index += 1

        if self.placement_index < len(SHIP_SIZES):
            name = SHIP_NAMES[self.placement_index]
            self.message = f"Place your {name}. R to rotate."
        else:
            self.phase = "battle"
            self.message = "Battle! Click on the enemy grid to fire."

    # ------------------------------------------------------------------ #
    #  Battle logic
    # ------------------------------------------------------------------ #

    def _handle_battle_click(self, x, y):
        cell = self._screen_to_grid(AI_GRID_LEFT, x, y)
        if cell is None:
            return
        row, col = cell
        if self.player_shot_board[row][col] != 0:
            self.message = "Already fired there!"
            return

        hit, sunk_ship = self.ai.receive_shot(row, col)
        self.player_shot_board[row][col] = 2 if hit else 3

        if sunk_ship:
            for r, c in sunk_ship:
                self.ai_ships_sunk_cells.add((r, c))
            self.message = "You sank a ship!"
        elif hit:
            self.message = "Hit!"
        else:
            self.message = "Miss!"

        # Check win
        if self.ai.all_ships_sunk():
            self.phase = "gameover"
            self.winner = "player"
            self.message = "YOU WIN! All enemy ships sunk!"
            return

        # Switch to AI turn
        self.turn = "ai"
        self.ai_timer = 0.0

    def _ai_take_shot(self):
        """Execute the AI's shot on the player's board."""
        shot = self.ai.get_shot()
        if shot is None:
            return
        row, col = shot

        hit = self.player_board[row][col] == 1
        if hit:
            self.player_board[row][col] = 2
        else:
            if self.player_board[row][col] == 0:
                self.player_board[row][col] = 3

        self.ai.report_result(row, col, hit)

        if hit:
            # Check if a player ship was sunk
            for i, ship in enumerate(self.player_ships):
                if (row, col) in ship:
                    if all(self.player_board[r][c] == 2 for r, c in ship):
                        self.ai.report_sunk(ship)
                        self.player_ships_sunk[i] = True
                        self.message = "AI sank your ship!"
                    else:
                        self.message = "AI hit your ship!"
                    break
        else:
            self.message = "AI missed. Your turn!"

        # Check AI win
        if all(self.player_ships_sunk):
            self.phase = "gameover"
            self.winner = "ai"
            self.message = "GAME OVER. The AI sank all your ships!"
            return

        self.turn = "player"

    # ------------------------------------------------------------------ #
    #  Update
    # ------------------------------------------------------------------ #

    def on_update(self, delta_time):
        if self.phase == "battle" and self.turn == "ai":
            self.ai_timer += delta_time
            if self.ai_timer >= AI_SHOT_DELAY:
                self._ai_take_shot()
