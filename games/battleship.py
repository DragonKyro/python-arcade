"""
Battleship game view for Python Arcade 2.6.x.
Two-phase game: placement then battle against an AI opponent.
"""

import arcade

from ai.battleship_ai import BattleshipAI
from pages.rules import RulesView
from renderers.battleship_renderer import (
    WIDTH, HEIGHT,
    GRID_SIZE, CELL_SIZE, GRID_PIXEL,
    PLAYER_GRID_LEFT, AI_GRID_LEFT, GRID_TOP,
    SHIP_SIZES, SHIP_NAMES,
    BTN_W, BTN_H,
    AI_SHOT_DELAY,
)


class BattleshipView(arcade.View):
    """Main view for the Battleship game."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self._create_texts()
        self.new_game()

    # ------------------------------------------------------------------ #
    #  Game state reset
    # ------------------------------------------------------------------ #

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        # Button labels (static)
        self.txt_btn_back = arcade.Text("Back", 55, HEIGHT - 22, arcade.color.WHITE, 13, anchor_x="center", anchor_y="center")
        self.txt_btn_new_game = arcade.Text("New Game", WIDTH - 55, HEIGHT - 22, arcade.color.WHITE, 13, anchor_x="center", anchor_y="center")
        self.txt_btn_help = arcade.Text("?", WIDTH - 140, HEIGHT - 22, arcade.color.WHITE, 13, anchor_x="center", anchor_y="center")

        # Grid column/row labels (static) -- player grid
        self.txt_player_col_labels = []
        self.txt_player_row_labels = []
        for i in range(GRID_SIZE):
            lx = PLAYER_GRID_LEFT + i * CELL_SIZE + CELL_SIZE // 2
            ly_top = GRID_TOP + 10
            self.txt_player_col_labels.append(
                arcade.Text(str(i), lx, ly_top, arcade.color.WHITE, 10, anchor_x="center", anchor_y="center")
            )
            lx_side = PLAYER_GRID_LEFT - 12
            ly_side = GRID_TOP - i * CELL_SIZE - CELL_SIZE // 2
            self.txt_player_row_labels.append(
                arcade.Text(chr(65 + i), lx_side, ly_side, arcade.color.WHITE, 10, anchor_x="center", anchor_y="center")
            )

        # Grid column/row labels (static) -- AI grid
        self.txt_ai_col_labels = []
        self.txt_ai_row_labels = []
        for i in range(GRID_SIZE):
            lx = AI_GRID_LEFT + i * CELL_SIZE + CELL_SIZE // 2
            self.txt_ai_col_labels.append(
                arcade.Text(str(i), lx, GRID_TOP + 10, arcade.color.WHITE, 10, anchor_x="center", anchor_y="center")
            )
            ly_side = GRID_TOP - i * CELL_SIZE - CELL_SIZE // 2
            self.txt_ai_row_labels.append(
                arcade.Text(chr(65 + i), AI_GRID_LEFT - 12, ly_side, arcade.color.WHITE, 10, anchor_x="center", anchor_y="center")
            )

        # Ship list header and items (placement phase)
        sx = PLAYER_GRID_LEFT + GRID_PIXEL + 40
        sy = GRID_TOP - 10
        self.txt_ship_list_header = arcade.Text("Ships:", sx, sy, arcade.color.WHITE, 14, bold=True)
        self.txt_ship_list_items = []
        for i, name in enumerate(SHIP_NAMES):
            self.txt_ship_list_items.append(
                arcade.Text("", sx, sy - 25 - i * 22, (200, 200, 200), 12)
            )

        # Battle phase labels (static)
        px = PLAYER_GRID_LEFT + GRID_PIXEL // 2
        ax = AI_GRID_LEFT + GRID_PIXEL // 2
        label_y = GRID_TOP + 26
        self.txt_label_your_board = arcade.Text("Your Board", px, label_y, arcade.color.WHITE, 14, anchor_x="center", bold=True)
        self.txt_label_enemy_board = arcade.Text("Enemy Board", ax, label_y, arcade.color.WHITE, 14, anchor_x="center", bold=True)

        # Status message (dynamic)
        self.txt_message = arcade.Text("", WIDTH // 2, 30, arcade.color.YELLOW, 15, anchor_x="center", anchor_y="center")

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
        from renderers import battleship_renderer
        battleship_renderer.draw(self)

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

        # Help button
        hx, hy = WIDTH - 140, HEIGHT - 22
        if abs(x - hx) < 20 and abs(y - hy) < 15:
            rules_view = RulesView("Battleship", "battleship.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
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
