"""
Checkers game view using Arcade 3.x APIs.
"""

import arcade
from pages.components import Button
from pages.rules import RulesView
from ai.checkers_ai import (
    CheckersAI,
    initial_board,
    get_all_moves,
    get_captures,
    apply_move,
    check_winner,
    count_pieces,
    EMPTY,
    RED,
    BLACK,
    RED_KING,
    BLACK_KING,
)

WIDTH = 800
HEIGHT = 600

# Board drawing constants
BOARD_SIZE = 8
CELL_SIZE = 60
BOARD_PIXEL = BOARD_SIZE * CELL_SIZE  # 480
BOARD_LEFT = (WIDTH - BOARD_PIXEL) // 2
BOARD_BOTTOM = 30
PIECE_RADIUS = CELL_SIZE * 0.38

# Colors
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
PLAYER_COLOR = (200, 30, 30)        # Red pieces
AI_PIECE_COLOR = (30, 30, 30)       # Black pieces
SELECT_HIGHLIGHT = (255, 255, 0, 100)
VALID_DEST_COLOR = (0, 200, 0, 130)
KING_MARKER_COLOR = (255, 215, 0)   # Gold for king text
OVERLAY_BG = (0, 0, 0, 170)

# Button dimensions
BUTTON_W = 100
BUTTON_H = 36

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
        self._draw_buttons()
        self._draw_board()
        self._draw_pieces()
        self._draw_highlights()
        self._draw_piece_counts()
        if self.state == STATE_GAME_OVER:
            self._draw_overlay()

    def _draw_buttons(self):
        # Back button (top-left)
        bx, by = 60, HEIGHT - 30
        arcade.draw_rect_filled(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.DARK_GRAY)
        arcade.draw_rect_outline(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.WHITE, 2)
        arcade.draw_text("Back", bx, by, arcade.color.WHITE, 14, anchor_x="center", anchor_y="center")

        # New Game button (top-right)
        nx, ny = WIDTH - 70, HEIGHT - 30
        arcade.draw_rect_filled(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.DARK_GREEN)
        arcade.draw_rect_outline(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.WHITE, 2)
        arcade.draw_text("New Game", nx, ny, arcade.color.WHITE, 14, anchor_x="center", anchor_y="center")

        # Help button
        self.help_button.draw()

        # Title
        arcade.draw_text(
            "Checkers",
            WIDTH // 2, HEIGHT - 30,
            arcade.color.WHITE, 22, anchor_x="center", anchor_y="center",
            bold=True,
        )

        # Turn indicator
        board_top = BOARD_BOTTOM + BOARD_PIXEL
        if self.state == STATE_PLAYER_TURN:
            msg = "Your turn (Red)"
            color = PLAYER_COLOR
        elif self.state == STATE_PLAYER_MULTI_JUMP:
            msg = "Continue jumping!"
            color = PLAYER_COLOR
        elif self.state == STATE_AI_THINKING:
            msg = "AI is thinking..."
            color = arcade.color.WHITE
        else:
            msg = ""
            color = arcade.color.WHITE

        if msg:
            arcade.draw_text(
                msg, WIDTH // 2, board_top + 18,
                color, 16, anchor_x="center", anchor_y="center", bold=True,
            )

    def _draw_board(self):
        """Draw the checkerboard squares."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                cx, cy = self._cell_center(row, col)
                if (row + col) % 2 == 0:
                    color = LIGHT_SQUARE
                else:
                    color = DARK_SQUARE
                arcade.draw_rect_filled(
                    arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE), color
                )

        # Board border
        bcx = BOARD_LEFT + BOARD_PIXEL // 2
        bcy = BOARD_BOTTOM + BOARD_PIXEL // 2
        arcade.draw_rect_outline(
            arcade.XYWH(bcx, bcy, BOARD_PIXEL, BOARD_PIXEL),
            arcade.color.WHITE, 2,
        )

    def _draw_pieces(self):
        """Draw all pieces on the board."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece == EMPTY:
                    continue
                cx, cy = self._cell_center(row, col)
                if piece in (RED, RED_KING):
                    arcade.draw_circle_filled(cx, cy, PIECE_RADIUS, PLAYER_COLOR)
                    arcade.draw_circle_outline(cx, cy, PIECE_RADIUS, (120, 10, 10), 2)
                else:
                    arcade.draw_circle_filled(cx, cy, PIECE_RADIUS, AI_PIECE_COLOR)
                    arcade.draw_circle_outline(cx, cy, PIECE_RADIUS, (80, 80, 80), 2)

                # King marker
                if piece in (RED_KING, BLACK_KING):
                    text_color = KING_MARKER_COLOR
                    arcade.draw_text(
                        "K", cx, cy,
                        text_color, 16,
                        anchor_x="center", anchor_y="center",
                        bold=True,
                    )

    def _draw_highlights(self):
        """Draw selection highlight and valid destination markers."""
        # Highlight selected piece
        sel = self.selected if self.state == STATE_PLAYER_TURN else self.multi_jump_pos
        if sel is not None:
            cx, cy = self._cell_center(sel[0], sel[1])
            arcade.draw_rect_filled(
                arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE), SELECT_HIGHLIGHT
            )

        # Highlight valid destinations
        dest_cells = set()
        for move in self.valid_destinations:
            if len(move) >= 2:
                # Show the next step destination
                dest_cells.add(move[1])
        for (dr, dc) in dest_cells:
            cx, cy = self._cell_center(dr, dc)
            arcade.draw_circle_filled(cx, cy, 10, VALID_DEST_COLOR)

    def _draw_piece_counts(self):
        """Draw piece count display."""
        red_count, black_count = count_pieces(self.board)
        # Left side - player (red) count
        arcade.draw_circle_filled(25, HEIGHT // 2 + 20, 10, PLAYER_COLOR)
        arcade.draw_text(
            f" {red_count}", 38, HEIGHT // 2 + 20,
            arcade.color.WHITE, 14, anchor_x="left", anchor_y="center",
        )
        # Left side - AI (black) count
        arcade.draw_circle_filled(25, HEIGHT // 2 - 10, 10, AI_PIECE_COLOR)
        arcade.draw_circle_outline(25, HEIGHT // 2 - 10, 10, (80, 80, 80), 1)
        arcade.draw_text(
            f" {black_count}", 38, HEIGHT // 2 - 10,
            arcade.color.WHITE, 14, anchor_x="left", anchor_y="center",
        )

    def _draw_overlay(self):
        """Draw a semi-transparent overlay with the result message."""
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_BG
        )

        if self.winner == RED:
            msg = "You Win!"
            color = PLAYER_COLOR
        elif self.winner == BLACK:
            msg = "AI Wins!"
            color = arcade.color.WHITE
        else:
            msg = "It's a Draw!"
            color = arcade.color.WHITE

        arcade.draw_text(
            msg, WIDTH // 2, HEIGHT // 2 + 30,
            color, 48, anchor_x="center", anchor_y="center", bold=True,
        )
        arcade.draw_text(
            "Click 'New Game' to play again",
            WIDTH // 2, HEIGHT // 2 - 30,
            arcade.color.WHITE, 18, anchor_x="center", anchor_y="center",
        )

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
