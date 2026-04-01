"""
Checkers game view using Arcade 3.x APIs.
"""

import arcade
from pages.components import Button
from pages.rules import RulesView
from renderers import checkers_renderer
from renderers.checkers_renderer import (
    WIDTH, HEIGHT,
    BOARD_SIZE, CELL_SIZE, BOARD_PIXEL, BOARD_LEFT, BOARD_BOTTOM,
    BUTTON_W, BUTTON_H,
)
from ai.checkers_ai import (
    CheckersAI,
    initial_board,
    get_all_moves,
    get_captures,
    apply_move,
    check_winner,
    RED,
    BLACK,
    RED_KING,
)

# Game states
STATE_PLAYER_TURN = "player_turn"
STATE_PLAYER_MULTI_JUMP = "player_multi_jump"
STATE_AI_THINKING = "ai_thinking"
STATE_GAME_OVER = "game_over"


class CheckersView(arcade.View):
    """Arcade View for the Checkers game."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.ai = CheckersAI(depth=5)
        self.help_button = Button(
            WIDTH - 145, HEIGHT - 30, 40, 36, "?",
            color=arcade.color.DARK_SLATE_BLUE,
        )
        self.board = None
        self.state = None
        self.winner = None
        self.selected = None          # (row, col) of selected piece
        self.valid_destinations = []  # list of moves starting from selected piece
        self.ai_delay = 0.0
        self.multi_jump_pos = None    # (row, col) during multi-jump
        self._create_texts()
        self.new_game()

    def new_game(self):
        """Reset the board and start a fresh game."""
        self.board = initial_board()
        self.state = STATE_PLAYER_TURN
        self.winner = None
        self.selected = None
        self.valid_destinations = []
        self.ai_delay = 0.0
        self.multi_jump_pos = None

    def _create_texts(self):
        """Create reusable arcade.Text objects for rendering."""
        from renderers.checkers_renderer import (
            BOARD_BOTTOM, BOARD_PIXEL, PLAYER_COLOR,
        )
        board_top = BOARD_BOTTOM + BOARD_PIXEL
        self.txt_back = arcade.Text(
            "Back", 60, HEIGHT - 30, arcade.color.WHITE,
            14, anchor_x="center", anchor_y="center",
        )
        self.txt_new_game = arcade.Text(
            "New Game", WIDTH - 70, HEIGHT - 30, arcade.color.WHITE,
            14, anchor_x="center", anchor_y="center",
        )
        self.txt_title = arcade.Text(
            "Checkers", WIDTH // 2, HEIGHT - 30, arcade.color.WHITE,
            22, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_turn = arcade.Text(
            "", WIDTH // 2, board_top + 18, arcade.color.WHITE,
            16, anchor_x="center", anchor_y="center", bold=True,
        )
        # Reusable king marker text
        self.txt_king = arcade.Text(
            "K", 0, 0, (212, 175, 55),
            16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_red_count = arcade.Text(
            "", 38, HEIGHT // 2 + 20, arcade.color.WHITE,
            14, anchor_x="left", anchor_y="center",
        )
        self.txt_black_count = arcade.Text(
            "", 38, HEIGHT // 2 - 10, arcade.color.WHITE,
            14, anchor_x="left", anchor_y="center",
        )
        self.txt_game_over = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 30, arcade.color.WHITE,
            48, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_hint = arcade.Text(
            "Click 'New Game' to play again",
            WIDTH // 2, HEIGHT // 2 - 30, arcade.color.WHITE,
            18, anchor_x="center", anchor_y="center",
        )

    # ------------------------------------------------------------------ helpers

    def _cell_center(self, row, col):
        """Return (screen_x, screen_y) for the center of a board cell.
        Row 0 is at the top of the board visually."""
        cx = BOARD_LEFT + col * CELL_SIZE + CELL_SIZE // 2
        cy = BOARD_BOTTOM + (BOARD_SIZE - 1 - row) * CELL_SIZE + CELL_SIZE // 2
        return cx, cy

    def _cell_from_screen(self, x, y):
        """Convert screen coordinates to (row, col) or None."""
        rel_x = x - BOARD_LEFT
        rel_y = y - BOARD_BOTTOM
        if rel_x < 0 or rel_x >= BOARD_PIXEL or rel_y < 0 or rel_y >= BOARD_PIXEL:
            return None
        col = int(rel_x // CELL_SIZE)
        row = BOARD_SIZE - 1 - int(rel_y // CELL_SIZE)
        if 0 <= row < 8 and 0 <= col < 8:
            return (row, col)
        return None

    def _in_button(self, x, y, bx, by, bw=BUTTON_W, bh=BUTTON_H):
        """Check if (x, y) is inside a button centered at (bx, by)."""
        return (
            bx - bw // 2 <= x <= bx + bw // 2
            and by - bh // 2 <= y <= by + bh // 2
        )

    def _compute_valid_destinations(self):
        """Compute valid destination moves for the currently selected piece."""
        self.valid_destinations = []
        if self.selected is None:
            return
        sr, sc = self.selected
        all_moves = get_all_moves(self.board, RED)
        for move in all_moves:
            if move[0] == (sr, sc):
                self.valid_destinations.append(move)

    def _compute_multi_jump_destinations(self):
        """Compute capture continuations during a multi-jump."""
        self.valid_destinations = []
        if self.multi_jump_pos is None:
            return
        r, c = self.multi_jump_pos
        captures = get_captures(self.board, r, c)
        for cap in captures:
            self.valid_destinations.append(cap)

    # ------------------------------------------------------------------ update

    def on_update(self, delta_time):
        if self.state == STATE_AI_THINKING:
            self.ai_delay += delta_time
            if self.ai_delay >= 0.5:
                move = self.ai.get_move(self.board, BLACK)
                if move is not None:
                    self.board = apply_move(self.board, move)
                result = check_winner(self.board)
                if result is not None:
                    self.winner = result
                    self.state = STATE_GAME_OVER
                else:
                    self.state = STATE_PLAYER_TURN

    # ------------------------------------------------------------------ draw

    def on_draw(self):
        self.clear()
        checkers_renderer.draw(self)

    # ------------------------------------------------------------------ input

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Back button
        if self._in_button(x, y, 60, HEIGHT - 30):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if self._in_button(x, y, WIDTH - 70, HEIGHT - 30, BUTTON_W + 10, BUTTON_H):
            self.new_game()
            return

        # Help button
        if self.help_button.hit_test(x, y):
            rules_view = RulesView(
                "Checkers", "checkers.txt", None,
                self.menu_view, existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        # Handle multi-jump state
        if self.state == STATE_PLAYER_MULTI_JUMP:
            cell = self._cell_from_screen(x, y)
            if cell is None:
                return
            self._handle_multi_jump_click(cell)
            return

        # Player move
        if self.state != STATE_PLAYER_TURN:
            return

        cell = self._cell_from_screen(x, y)
        if cell is None:
            return

        row, col = cell
        piece = self.board[row][col]

        # If clicking on a valid destination, make the move
        if self.selected is not None:
            for move in self.valid_destinations:
                if len(move) >= 2 and move[1] == (row, col):
                    self._execute_player_move(move)
                    return
            # Deselect if clicking elsewhere
            self.selected = None
            self.valid_destinations = []

        # Select own piece
        if piece in (RED, RED_KING):
            # Check if this piece has any valid moves
            all_moves = get_all_moves(self.board, RED)
            piece_moves = [m for m in all_moves if m[0] == (row, col)]
            if piece_moves:
                self.selected = (row, col)
                self.valid_destinations = piece_moves

    def _execute_player_move(self, move):
        """Execute a player's chosen move, handling multi-jump."""
        # Check if this is a capture move (move has more than 2 positions)
        is_capture = len(move) > 2 or (
            len(move) == 2
            and abs(move[1][0] - move[0][0]) == 2
        )

        if is_capture and len(move) > 2:
            # Apply only the first jump of the sequence
            partial_move = [move[0], move[1]]
            self.board = apply_move(self.board, partial_move)
            land_r, land_c = move[1]

            # Check if the piece can continue capturing from the landing spot
            further_captures = get_captures(self.board, land_r, land_c)
            if further_captures:
                self.multi_jump_pos = (land_r, land_c)
                self.selected = None
                self.state = STATE_PLAYER_MULTI_JUMP
                self._compute_multi_jump_destinations()
                return

        # Not a multi-jump or no further captures: apply full move
        if not (is_capture and len(move) > 2):
            self.board = apply_move(self.board, move)

        self._finish_player_turn()

    def _handle_multi_jump_click(self, cell):
        """Handle a click during multi-jump."""
        row, col = cell
        for move in self.valid_destinations:
            if len(move) >= 2 and move[1] == (row, col):
                # Apply this jump
                partial_move = [move[0], move[1]]
                self.board = apply_move(self.board, partial_move)
                land_r, land_c = move[1]

                # Check for more captures
                further_captures = get_captures(self.board, land_r, land_c)
                if further_captures:
                    self.multi_jump_pos = (land_r, land_c)
                    self._compute_multi_jump_destinations()
                    return

                # No more captures
                self._finish_player_turn()
                return

    def _finish_player_turn(self):
        """End the player's turn and set up for AI."""
        self.selected = None
        self.valid_destinations = []
        self.multi_jump_pos = None

        result = check_winner(self.board)
        if result is not None:
            self.winner = result
            self.state = STATE_GAME_OVER
        else:
            self.state = STATE_AI_THINKING
            self.ai_delay = 0.0
