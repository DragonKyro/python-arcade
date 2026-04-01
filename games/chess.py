"""
Chess game view using Arcade 3.x APIs.
"""

import arcade
from renderers import chess_renderer
from renderers.chess_renderer import (
    WIDTH, HEIGHT,
    BOARD_LEFT, BOARD_BOTTOM, BOARD_PIXEL, CELL_SIZE,
    BUTTON_W, BUTTON_H,
    STATE_DIFFICULTY, STATE_PLAYER_TURN, STATE_AI_THINKING,
    STATE_PROMOTION, STATE_GAME_OVER,
    board_to_screen, screen_to_board,
)
from ai.chess_ai import (
    ChessAI,
    initial_board,
    initial_castling_rights,
    get_all_legal_moves,
    get_legal_moves_for_piece,
    apply_move,
    is_in_check,
    is_checkmate,
    is_stalemate,
    find_king,
    piece_color,
    is_own,
    DEPTH_EASY, DEPTH_MEDIUM, DEPTH_HARD,
)


class ChessView(arcade.View):
    """Arcade View for the Chess game."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.ai = ChessAI(depth=DEPTH_MEDIUM)

        # Game state
        self.board = None
        self.castling_rights = None
        self.en_passant_target = None
        self.state = STATE_DIFFICULTY
        self.selected = None
        self.valid_moves = []  # list of (row, col, promo) tuples
        self.last_move = None  # ((fr, fc), (tr, tc))
        self.in_check = False
        self.check_square = None  # (row, col) of king in check
        self.winner = None  # 'white', 'black', or 'draw'
        self.ai_delay = 0.0
        self.game_over_reason = ""

        # Captured pieces tracking
        self.captured_by_white = []  # black pieces captured by white
        self.captured_by_black = []  # white pieces captured by black

        # Promotion state
        self.promo_from = None
        self.promo_to = None

        # Difficulty buttons
        self.diff_buttons = {
            'easy': (WIDTH // 2, HEIGHT // 2 + 40),
            'medium': (WIDTH // 2, HEIGHT // 2 - 30),
            'hard': (WIDTH // 2, HEIGHT // 2 - 100),
        }

        self._create_texts()

    def _create_texts(self):
        """Create reusable arcade.Text objects."""
        self.txt_back = arcade.Text(
            "Back", 60, HEIGHT - 30, arcade.color.WHITE,
            14, anchor_x="center", anchor_y="center",
        )
        self.txt_new_game = arcade.Text(
            "New Game", WIDTH - 70, HEIGHT - 30, arcade.color.WHITE,
            14, anchor_x="center", anchor_y="center",
        )
        self.txt_title = arcade.Text(
            "Chess", WIDTH // 2, HEIGHT - 30, arcade.color.WHITE,
            22, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_turn_player = arcade.Text(
            "Your turn (White)", WIDTH // 2, BOARD_BOTTOM + BOARD_PIXEL + 20,
            arcade.color.WHITE, 14, anchor_x="center", anchor_y="center",
        )
        self.txt_turn_ai = arcade.Text(
            "AI thinking...", WIDTH // 2, BOARD_BOTTOM + BOARD_PIXEL + 20,
            arcade.color.LIGHT_GRAY, 14, anchor_x="center", anchor_y="center",
        )

        # Difficulty screen
        self.txt_diff_title = arcade.Text(
            "Chess", WIDTH // 2, HEIGHT // 2 + 150,
            arcade.color.WHITE, 36, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_diff_subtitle = arcade.Text(
            "Select Difficulty", WIDTH // 2, HEIGHT // 2 + 100,
            arcade.color.LIGHT_GRAY, 18, anchor_x="center", anchor_y="center",
        )
        self.txt_diff_buttons = {
            'easy': arcade.Text(
                "Easy", WIDTH // 2, HEIGHT // 2 + 40,
                arcade.color.WHITE, 18, anchor_x="center", anchor_y="center", bold=True,
            ),
            'medium': arcade.Text(
                "Medium", WIDTH // 2, HEIGHT // 2 - 30,
                arcade.color.WHITE, 18, anchor_x="center", anchor_y="center", bold=True,
            ),
            'hard': arcade.Text(
                "Hard", WIDTH // 2, HEIGHT // 2 - 100,
                arcade.color.WHITE, 18, anchor_x="center", anchor_y="center", bold=True,
            ),
        }

        # Captured pieces labels
        sidebar_x = BOARD_LEFT - 50
        sidebar_x2 = BOARD_LEFT + BOARD_PIXEL + 50
        self.txt_captured_white_label = arcade.Text(
            "Won", sidebar_x, BOARD_BOTTOM + BOARD_PIXEL - 30,
            arcade.color.WHITE, 11, anchor_x="center", anchor_y="center",
        )
        self.txt_captured_black_label = arcade.Text(
            "Lost", sidebar_x2, BOARD_BOTTOM + BOARD_PIXEL - 30,
            arcade.color.WHITE, 11, anchor_x="center", anchor_y="center",
        )

        # Promotion picker
        self.txt_promo_title = arcade.Text(
            "Promote pawn to:", WIDTH // 2, HEIGHT // 2 + 25,
            arcade.color.WHITE, 14, anchor_x="center", anchor_y="center",
        )

        # Game over
        self.txt_game_over = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 30,
            arcade.color.WHITE, 32, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_sub = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 - 10,
            arcade.color.LIGHT_GRAY, 16, anchor_x="center", anchor_y="center",
        )
        self.txt_play_again = arcade.Text(
            "Play Again", WIDTH // 2, HEIGHT // 2 - 60,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )

        # File and rank labels
        self.file_labels = []
        self.rank_labels = []
        files = 'abcdefgh'
        for i in range(8):
            x = BOARD_LEFT + i * CELL_SIZE + CELL_SIZE // 2
            y = BOARD_BOTTOM - 12
            self.file_labels.append(arcade.Text(
                files[i], x, y, arcade.color.LIGHT_GRAY, 10,
                anchor_x="center", anchor_y="center",
            ))
            sx = BOARD_LEFT - 12
            sy = BOARD_BOTTOM + (7 - i) * CELL_SIZE + CELL_SIZE // 2
            self.rank_labels.append(arcade.Text(
                str(8 - i), sx, sy, arcade.color.LIGHT_GRAY, 10,
                anchor_x="center", anchor_y="center",
            ))

    def new_game(self, depth=DEPTH_MEDIUM):
        """Reset and start a fresh game."""
        self.ai = ChessAI(depth=depth)
        self.board = initial_board()
        self.castling_rights = initial_castling_rights()
        self.en_passant_target = None
        self.state = STATE_PLAYER_TURN
        self.selected = None
        self.valid_moves = []
        self.last_move = None
        self.in_check = False
        self.check_square = None
        self.winner = None
        self.ai_delay = 0.0
        self.game_over_reason = ""
        self.captured_by_white = []
        self.captured_by_black = []
        self.promo_from = None
        self.promo_to = None

    def on_show_view(self):
        """Called when this view becomes active."""
        self.window.background_color = (30, 30, 30)

    def on_draw(self):
        """Render the game."""
        self.clear()
        chess_renderer.draw(self)

    def on_update(self, delta_time):
        """Update game logic."""
        if self.state == STATE_AI_THINKING:
            self.ai_delay -= delta_time
            if self.ai_delay <= 0:
                self._do_ai_move()

    def on_mouse_press(self, x, y, button, modifiers):
        """Handle mouse clicks."""
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Difficulty selection
        if self.state == STATE_DIFFICULTY:
            self._handle_difficulty_click(x, y)
            return

        # Game over: play again button
        if self.state == STATE_GAME_OVER:
            bx, by = WIDTH // 2, HEIGHT // 2 - 60
            if abs(x - bx) < 80 and abs(y - by) < 22:
                self.state = STATE_DIFFICULTY
            return

        # Promotion picker
        if self.state == STATE_PROMOTION:
            self._handle_promotion_click(x, y)
            return

        # Back button
        bx, by = 60, HEIGHT - 30
        if abs(x - bx) < BUTTON_W // 2 and abs(y - by) < BUTTON_H // 2:
            self.window.show_view(self.menu_view)
            return

        # New Game button
        nx, ny = WIDTH - 70, HEIGHT - 30
        if abs(x - nx) < (BUTTON_W + 10) // 2 and abs(y - ny) < BUTTON_H // 2:
            self.state = STATE_DIFFICULTY
            return

        # Board clicks during player turn
        if self.state != STATE_PLAYER_TURN:
            return

        result = screen_to_board(x, y)
        if result is None:
            self.selected = None
            self.valid_moves = []
            return

        row, col = result
        piece = self.board[row][col]

        # If we have a selected piece and click a valid destination
        if self.selected is not None:
            matching = [(r, c, p) for r, c, p in self.valid_moves if r == row and c == col]
            if matching:
                # Check if this is a promotion move
                promo_moves = [m for m in matching if m[2] is not None]
                if promo_moves:
                    # Show promotion picker
                    self.promo_from = self.selected
                    self.promo_to = (row, col)
                    self.state = STATE_PROMOTION
                    self.selected = None
                    self.valid_moves = []
                    return

                # Normal move
                self._execute_player_move(self.selected, (row, col), None)
                return
            # Clicking on own piece: reselect
            if is_own(piece, 'white'):
                self._select_piece(row, col)
                return
            # Click elsewhere: deselect
            self.selected = None
            self.valid_moves = []
            return

        # No piece selected: select own piece
        if is_own(piece, 'white'):
            self._select_piece(row, col)

    def _handle_difficulty_click(self, x, y):
        """Handle clicks on the difficulty selection screen."""
        for key, (bx, by) in self.diff_buttons.items():
            if abs(x - bx) < 90 and abs(y - by) < 25:
                depth = {'easy': DEPTH_EASY, 'medium': DEPTH_MEDIUM, 'hard': DEPTH_HARD}[key]
                self.new_game(depth)
                return

    def _handle_promotion_click(self, x, y):
        """Handle clicks on the promotion picker."""
        bx, by = WIDTH // 2, HEIGHT // 2
        promo_pieces = ['Q', 'R', 'B', 'N']
        start_x = bx - 90
        for i, p in enumerate(promo_pieces):
            px = start_x + i * 60
            py = by - 5
            if abs(x - px) < 25 and abs(y - py) < 25:
                self._execute_player_move(self.promo_from, self.promo_to, p)
                self.promo_from = None
                self.promo_to = None
                return

    def _select_piece(self, row, col):
        """Select a piece and compute valid moves."""
        self.selected = (row, col)
        self.valid_moves = get_legal_moves_for_piece(
            self.board, row, col, self.castling_rights, self.en_passant_target
        )

    def _execute_player_move(self, from_sq, to_sq, promotion):
        """Execute a player move on the board."""
        fr, fc = from_sq
        tr, tc = to_sq
        promo_piece = promotion if promotion is None else promotion
        move = (fr, fc, tr, tc, promo_piece)

        new_board, new_castling, new_ep, captured = apply_move(
            self.board, move, self.castling_rights, self.en_passant_target
        )

        self.board = new_board
        self.castling_rights = new_castling
        self.en_passant_target = new_ep
        self.last_move = (from_sq, to_sq)
        self.selected = None
        self.valid_moves = []

        if captured is not None:
            self.captured_by_white.append(captured)

        # Check game end conditions
        self.in_check = is_in_check(self.board, 'black')
        self.check_square = find_king(self.board, 'black') if self.in_check else None
        if is_checkmate(self.board, 'black', self.castling_rights, self.en_passant_target):
            self._end_game('white', "Checkmate!")
            return
        if is_stalemate(self.board, 'black', self.castling_rights, self.en_passant_target):
            self._end_game('draw', "Stalemate!")
            return
        if self._is_insufficient_material():
            self._end_game('draw', "Insufficient material")
            return

        # AI's turn
        self.state = STATE_AI_THINKING
        self.ai_delay = 0.5

    def _do_ai_move(self):
        """Execute the AI's move."""
        result = self.ai.get_move(
            self.board, 'black', self.castling_rights, self.en_passant_target
        )
        if result is None:
            # No legal moves (should be caught by checkmate/stalemate check)
            if is_in_check(self.board, 'black'):
                self._end_game('white', "Checkmate!")
            else:
                self._end_game('draw', "Stalemate!")
            return

        from_sq, to_sq, promo = result
        fr, fc = from_sq
        tr, tc = to_sq
        move = (fr, fc, tr, tc, promo)

        new_board, new_castling, new_ep, captured = apply_move(
            self.board, move, self.castling_rights, self.en_passant_target
        )

        self.board = new_board
        self.castling_rights = new_castling
        self.en_passant_target = new_ep
        self.last_move = (from_sq, to_sq)

        if captured is not None:
            self.captured_by_black.append(captured)

        # Check game end conditions
        self.in_check = is_in_check(self.board, 'white')
        self.check_square = find_king(self.board, 'white') if self.in_check else None
        if is_checkmate(self.board, 'white', self.castling_rights, self.en_passant_target):
            self._end_game('black', "Checkmate!")
            return
        if is_stalemate(self.board, 'white', self.castling_rights, self.en_passant_target):
            self._end_game('draw', "Stalemate!")
            return
        if self._is_insufficient_material():
            self._end_game('draw', "Insufficient material")
            return

        self.state = STATE_PLAYER_TURN

    def _end_game(self, winner, reason):
        """End the game with result."""
        self.winner = winner
        self.game_over_reason = reason
        self.state = STATE_GAME_OVER
        self.selected = None
        self.valid_moves = []

        if winner == 'white':
            self.txt_game_over.text = "You Win!"
            self.txt_game_over.color = arcade.color.GOLD
        elif winner == 'black':
            self.txt_game_over.text = "AI Wins!"
            self.txt_game_over.color = arcade.color.RED
        else:
            self.txt_game_over.text = "Draw!"
            self.txt_game_over.color = arcade.color.LIGHT_GRAY

        self.txt_game_over_sub.text = reason

    def _is_insufficient_material(self):
        """Check for insufficient material draw."""
        white_pieces = []
        black_pieces = []
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p is None:
                    continue
                if p.isupper():
                    white_pieces.append(p)
                else:
                    black_pieces.append(p)

        # Remove kings
        w = [p for p in white_pieces if p != 'K']
        b = [p for p in black_pieces if p != 'k']

        # K vs K
        if not w and not b:
            return True
        # K+B vs K or K+N vs K
        if (not w and len(b) == 1 and b[0] in ('b', 'n')):
            return True
        if (not b and len(w) == 1 and w[0] in ('B', 'N')):
            return True

        return False
