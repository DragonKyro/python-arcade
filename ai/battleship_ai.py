"""
Battleship AI - Pure logic, no arcade imports.
Implements hunt/target strategy for shooting and random ship placement.
"""

import random


class BattleshipAI:
    """AI opponent for Battleship. Handles ship placement and shot selection."""

    # Cell states
    EMPTY = 0
    SHIP = 1
    HIT = 2
    MISS = 3
    SUNK = 4

    def __init__(self, grid_size=10):
        self.grid_size = grid_size
        # The AI's own board (where its ships live)
        self.board = [[self.EMPTY] * grid_size for _ in range(grid_size)]
        # Tracking board for shots the AI fires at the player
        self.shot_board = [[self.EMPTY] * grid_size for _ in range(grid_size)]
        # Ship data: list of sets of (row, col) for each placed ship
        self.ships = []
        # Tracking for shot strategy
        self.hits = []  # unsunk hit cells still being targeted
        self.mode = "hunt"  # "hunt" or "target"
        self.target_queue = []  # adjacent cells to try in target mode
        self.all_shots = set()

    # ------------------------------------------------------------------ #
    #  Ship placement
    # ------------------------------------------------------------------ #

    def place_ships(self, ship_sizes):
        """Randomly place ships on the AI board. Returns the board."""
        self.board = [[self.EMPTY] * self.grid_size for _ in range(self.grid_size)]
        self.ships = []

        for size in ship_sizes:
            placed = False
            attempts = 0
            while not placed and attempts < 1000:
                attempts += 1
                horizontal = random.choice([True, False])
                if horizontal:
                    row = random.randint(0, self.grid_size - 1)
                    col = random.randint(0, self.grid_size - size)
                else:
                    row = random.randint(0, self.grid_size - size)
                    col = random.randint(0, self.grid_size - 1)

                cells = []
                valid = True
                for i in range(size):
                    r = row if horizontal else row + i
                    c = col + i if horizontal else col
                    if self.board[r][c] != self.EMPTY:
                        valid = False
                        break
                    cells.append((r, c))

                if valid:
                    ship_cells = set()
                    for r, c in cells:
                        self.board[r][c] = self.SHIP
                        ship_cells.add((r, c))
                    self.ships.append(ship_cells)
                    placed = True

        return self.board

    # ------------------------------------------------------------------ #
    #  Shot selection  (hunt + target)
    # ------------------------------------------------------------------ #

    def get_shot(self):
        """Return (row, col) for the AI's next shot."""
        # Target mode: try queued adjacent cells from previous hits
        if self.mode == "target" and self.target_queue:
            while self.target_queue:
                r, c = self.target_queue.pop(0)
                if (r, c) not in self.all_shots:
                    self.all_shots.add((r, c))
                    return (r, c)
            # Queue exhausted, fall back to hunt
            self.mode = "hunt"

        # Hunt mode: checkerboard pattern for efficiency
        candidates = []
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if (r + c) % 2 == 0 and (r, c) not in self.all_shots:
                    candidates.append((r, c))

        # If checkerboard exhausted, use remaining cells
        if not candidates:
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if (r, c) not in self.all_shots:
                        candidates.append((r, c))

        if not candidates:
            return None  # no moves left

        shot = random.choice(candidates)
        self.all_shots.add(shot)
        return shot

    def report_result(self, row, col, hit):
        """
        Called after the AI fires a shot so it can update its strategy.
        `hit` should be True if the shot was a hit, False for miss.
        """
        if hit:
            self.shot_board[row][col] = self.HIT
            self.hits.append((row, col))
            self.mode = "target"
            # Enqueue orthogonal neighbors
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size:
                    if (nr, nc) not in self.all_shots:
                        self.target_queue.append((nr, nc))
        else:
            self.shot_board[row][col] = self.MISS

    def report_sunk(self, ship_cells):
        """
        Called when a ship is fully sunk. Removes those cells from the
        active hit list so the AI stops targeting around them.
        """
        for cell in ship_cells:
            if cell in self.hits:
                self.hits.remove(cell)

        # Clean target queue of neighbors of sunk cells
        sunk_neighbors = set()
        for r, c in ship_cells:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                sunk_neighbors.add((r + dr, c + dc))
        self.target_queue = [
            pos for pos in self.target_queue
            if pos not in sunk_neighbors or pos in self.hits
        ]

        if not self.hits and not self.target_queue:
            self.mode = "hunt"

    # ------------------------------------------------------------------ #
    #  Helpers for external code to check ship status
    # ------------------------------------------------------------------ #

    def all_ships_sunk(self):
        """Return True if every cell of every ship has been hit."""
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.board[r][c] == self.SHIP:
                    return False
        return True

    def receive_shot(self, row, col):
        """
        Process an incoming shot at (row, col) on the AI's board.
        Returns (hit: bool, sunk_ship_cells: set or None).
        """
        if self.board[row][col] == self.SHIP:
            self.board[row][col] = self.HIT
            # Check if any ship is fully sunk
            for ship in self.ships:
                if (row, col) in ship:
                    if all(self.board[r][c] == self.HIT for r, c in ship):
                        return True, ship
                    break
            return True, None
        else:
            self.board[row][col] = self.MISS
            return False, None
