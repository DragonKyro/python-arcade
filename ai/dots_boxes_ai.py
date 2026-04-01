"""
Dots and Boxes AI - pure logic, no arcade dependency.
"""


class DotsBoxesAI:
    """Greedy AI for Dots and Boxes."""

    @staticmethod
    def count_sides(h_lines, v_lines, row, col):
        """Return the number of sides drawn for the box at (row, col)."""
        sides = 0
        # Top
        if h_lines[row][col]:
            sides += 1
        # Bottom
        if h_lines[row + 1][col]:
            sides += 1
        # Left
        if v_lines[row][col]:
            sides += 1
        # Right
        if v_lines[row][col + 1]:
            sides += 1
        return sides

    @staticmethod
    def _get_all_available_moves(h_lines, v_lines, grid_rows, grid_cols):
        """Return list of all available (undrawn) moves as (orientation, r, c)."""
        moves = []
        # Horizontal lines: (grid_rows+1) rows, grid_cols columns
        for r in range(grid_rows + 1):
            for c in range(grid_cols):
                if not h_lines[r][c]:
                    moves.append(('h', r, c))
        # Vertical lines: grid_rows rows, (grid_cols+1) columns
        for r in range(grid_rows):
            for c in range(grid_cols + 1):
                if not v_lines[r][c]:
                    moves.append(('v', r, c))
        return moves

    @staticmethod
    def _boxes_completed_by_move(h_lines, v_lines, grid_rows, grid_cols, orientation, r, c):
        """Return number of boxes that would be completed by playing this move."""
        # Temporarily place the line
        if orientation == 'h':
            h_lines[r][c] = True
        else:
            v_lines[r][c] = True

        completed = 0
        # A horizontal line at (r, c) borders the box above (r-1, c) and below (r, c)
        # A vertical line at (r, c) borders the box to the left (r, c-1) and right (r, c)
        if orientation == 'h':
            # Box above: row r-1, col c
            if r > 0:
                if DotsBoxesAI.count_sides(h_lines, v_lines, r - 1, c) == 4:
                    completed += 1
            # Box below: row r, col c
            if r < grid_rows:
                if DotsBoxesAI.count_sides(h_lines, v_lines, r, c) == 4:
                    completed += 1
        else:
            # Box to the left: row r, col c-1
            if c > 0:
                if DotsBoxesAI.count_sides(h_lines, v_lines, r, c - 1) == 4:
                    completed += 1
            # Box to the right: row r, col c
            if c < grid_cols:
                if DotsBoxesAI.count_sides(h_lines, v_lines, r, c) == 4:
                    completed += 1

        # Undo the temporary placement
        if orientation == 'h':
            h_lines[r][c] = False
        else:
            v_lines[r][c] = False

        return completed

    @staticmethod
    def _boxes_with_three_sides_created(h_lines, v_lines, grid_rows, grid_cols, orientation, r, c):
        """Return number of boxes that would reach exactly 3 sides after this move."""
        if orientation == 'h':
            h_lines[r][c] = True
        else:
            v_lines[r][c] = True

        count = 0
        if orientation == 'h':
            if r > 0:
                if DotsBoxesAI.count_sides(h_lines, v_lines, r - 1, c) == 3:
                    count += 1
            if r < grid_rows:
                if DotsBoxesAI.count_sides(h_lines, v_lines, r, c) == 3:
                    count += 1
        else:
            if c > 0:
                if DotsBoxesAI.count_sides(h_lines, v_lines, r, c - 1) == 3:
                    count += 1
            if c < grid_cols:
                if DotsBoxesAI.count_sides(h_lines, v_lines, r, c) == 3:
                    count += 1

        if orientation == 'h':
            h_lines[r][c] = False
        else:
            v_lines[r][c] = False

        return count

    def get_move(self, h_lines, v_lines, grid_rows, grid_cols):
        """
        Return (orientation, row, col) for the AI's chosen move.

        Strategy:
        1. Complete any box needing just 1 more line.
        2. Otherwise, play a line that does NOT create a 3-sided box for the opponent.
        3. If all moves give the opponent a box, pick the one giving the fewest.
        """
        moves = self._get_all_available_moves(h_lines, v_lines, grid_rows, grid_cols)
        if not moves:
            return None

        # Step 1: complete a box (any move that results in 4 sides)
        for move in moves:
            ori, r, c = move
            completed = self._boxes_completed_by_move(
                h_lines, v_lines, grid_rows, grid_cols, ori, r, c
            )
            if completed > 0:
                return move

        # Step 2: safe moves (don't create any 3-sided boxes)
        safe_moves = []
        dangerous_moves = []
        for move in moves:
            ori, r, c = move
            danger = self._boxes_with_three_sides_created(
                h_lines, v_lines, grid_rows, grid_cols, ori, r, c
            )
            if danger == 0:
                safe_moves.append(move)
            else:
                dangerous_moves.append((danger, move))

        if safe_moves:
            return safe_moves[0]

        # Step 3: all moves are dangerous; pick the least damaging
        dangerous_moves.sort(key=lambda x: x[0])
        return dangerous_moves[0][1]
