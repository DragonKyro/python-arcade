import arcade
import random
from pages.rules import RulesView

# Window constants
WIDTH = 800
HEIGHT = 600

# Game constants
NUM_SLOTS = 4
MAX_ATTEMPTS = 10
NUM_COLORS = 6

# The 6 code colors
CODE_COLORS = [
    arcade.color.RED,
    arcade.color.BLUE,
    arcade.color.GREEN,
    arcade.color.YELLOW,
    arcade.color.ORANGE,
    arcade.color.PURPLE,
]

# Layout constants
BOARD_LEFT = 200
BOARD_TOP = 540
ROW_HEIGHT = 40
SLOT_RADIUS = 14
SLOT_SPACING = 50
FEEDBACK_OFFSET_X = 240
FEEDBACK_PEG_RADIUS = 6
FEEDBACK_PEG_SPACING = 16

PALETTE_Y = 40
PALETTE_SPACING = 60
PALETTE_RADIUS = 20

EMPTY_COLOR = (80, 80, 80)
HIGHLIGHT_COLOR = arcade.color.WHITE


class MastermindView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.reset_game()

    def reset_game(self):
        """Initialize or reset all game state."""
        self.secret_code = [random.randint(0, NUM_COLORS - 1) for _ in range(NUM_SLOTS)]
        self.guesses = []  # list of lists of color indices
        self.feedback = []  # list of (black_pegs, white_pegs)
        self.current_guess = [None, None, None, None]
        self.current_row = 0
        self.selected_color = 0
        self.game_over = False
        self.won = False

    def on_show(self):
        arcade.set_background_color((40, 40, 60))

    def on_draw(self):
        self.clear()

        # Title
        arcade.draw_text(
            "Mastermind",
            WIDTH / 2, HEIGHT - 30,
            arcade.color.WHITE,
            font_size=28,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )

        # Back button
        self._draw_button(60, HEIGHT - 30, 90, 36, "Back", arcade.color.DARK_SLATE_BLUE)

        # New Game button
        self._draw_button(WIDTH - 70, HEIGHT - 30, 110, 36, "New Game", arcade.color.DARK_GREEN)

        # Help button
        self._draw_button(WIDTH - 140, HEIGHT - 30, 40, 36, "?", arcade.color.DARK_SLATE_BLUE)

        # Draw the guess board
        self._draw_board()

        # Draw color palette
        self._draw_palette()

        # Draw submit button
        if not self.game_over:
            all_filled = all(c is not None for c in self.current_guess)
            btn_color = arcade.color.DARK_BLUE if all_filled else (60, 60, 80)
            self._draw_button(WIDTH - 70, self._row_y(self.current_row), 100, 32, "Submit", btn_color)

        # Draw win/lose message
        if self.game_over:
            self._draw_game_over_message()

    def _draw_button(self, cx, cy, w, h, text, color):
        arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), color)
        arcade.draw_rect_outline(arcade.XYWH(cx, cy, w, h), arcade.color.WHITE)
        arcade.draw_text(
            text, cx, cy, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )

    def _row_y(self, row_index):
        """Return the y-coordinate for a given row (0=bottom row, 9=top row)."""
        base_y = 90
        return base_y + row_index * ROW_HEIGHT

    def _slot_x(self, slot_index):
        """Return the x-coordinate for a given slot in a row."""
        return BOARD_LEFT + slot_index * SLOT_SPACING

    def _draw_board(self):
        for row in range(MAX_ATTEMPTS):
            y = self._row_y(row)

            # Row number label
            arcade.draw_text(
                str(row + 1), BOARD_LEFT - 40, y,
                arcade.color.LIGHT_GRAY, font_size=12,
                anchor_x="center", anchor_y="center",
            )

            for slot in range(NUM_SLOTS):
                x = self._slot_x(slot)

                if row < len(self.guesses):
                    # Completed guess row
                    color = CODE_COLORS[self.guesses[row][slot]]
                    arcade.draw_circle_filled(x, y, SLOT_RADIUS, color)
                    arcade.draw_circle_outline(x, y, SLOT_RADIUS, arcade.color.WHITE, 2)
                elif row == self.current_row and not self.game_over:
                    # Current guess row
                    if self.current_guess[slot] is not None:
                        color = CODE_COLORS[self.current_guess[slot]]
                        arcade.draw_circle_filled(x, y, SLOT_RADIUS, color)
                        arcade.draw_circle_outline(x, y, SLOT_RADIUS, HIGHLIGHT_COLOR, 2)
                    else:
                        arcade.draw_circle_filled(x, y, SLOT_RADIUS, EMPTY_COLOR)
                        arcade.draw_circle_outline(x, y, SLOT_RADIUS, arcade.color.LIGHT_GRAY, 1)
                else:
                    # Empty future row
                    arcade.draw_circle_filled(x, y, SLOT_RADIUS, EMPTY_COLOR)
                    arcade.draw_circle_outline(x, y, SLOT_RADIUS, (100, 100, 100), 1)

            # Draw feedback pegs for completed rows
            if row < len(self.feedback):
                black_pegs, white_pegs = self.feedback[row]
                fb_x_start = self._slot_x(NUM_SLOTS - 1) + FEEDBACK_OFFSET_X - 140
                peg_index = 0
                for _ in range(black_pegs):
                    px = fb_x_start + (peg_index % 2) * FEEDBACK_PEG_SPACING
                    py = y + (peg_index // 2) * FEEDBACK_PEG_SPACING - FEEDBACK_PEG_SPACING / 2
                    arcade.draw_circle_filled(px, py, FEEDBACK_PEG_RADIUS, arcade.color.BLACK)
                    arcade.draw_circle_outline(px, py, FEEDBACK_PEG_RADIUS, arcade.color.WHITE, 1)
                    peg_index += 1
                for _ in range(white_pegs):
                    px = fb_x_start + (peg_index % 2) * FEEDBACK_PEG_SPACING
                    py = y + (peg_index // 2) * FEEDBACK_PEG_SPACING - FEEDBACK_PEG_SPACING / 2
                    arcade.draw_circle_filled(px, py, FEEDBACK_PEG_RADIUS, arcade.color.WHITE)
                    arcade.draw_circle_outline(px, py, FEEDBACK_PEG_RADIUS, arcade.color.GRAY, 1)
                    peg_index += 1

        # If game lost, reveal the secret code at the top
        if self.game_over and not self.won:
            secret_y = self._row_y(MAX_ATTEMPTS) + 10
            arcade.draw_text(
                "Secret:", BOARD_LEFT - 40, secret_y,
                arcade.color.LIGHT_CORAL, font_size=12,
                anchor_x="center", anchor_y="center",
            )
            for slot in range(NUM_SLOTS):
                x = self._slot_x(slot)
                color = CODE_COLORS[self.secret_code[slot]]
                arcade.draw_circle_filled(x, secret_y, SLOT_RADIUS, color)
                arcade.draw_circle_outline(x, secret_y, SLOT_RADIUS, arcade.color.LIGHT_CORAL, 2)

    def _draw_palette(self):
        palette_start_x = WIDTH / 2 - (NUM_COLORS - 1) * PALETTE_SPACING / 2
        for i, color in enumerate(CODE_COLORS):
            x = palette_start_x + i * PALETTE_SPACING
            arcade.draw_circle_filled(x, PALETTE_Y, PALETTE_RADIUS, color)
            if i == self.selected_color:
                arcade.draw_circle_outline(x, PALETTE_Y, PALETTE_RADIUS + 4, HIGHLIGHT_COLOR, 3)
            else:
                arcade.draw_circle_outline(x, PALETTE_Y, PALETTE_RADIUS, (160, 160, 160), 1)

        # Label
        arcade.draw_text(
            "Select a color:", WIDTH / 2, PALETTE_Y + 35,
            arcade.color.LIGHT_GRAY, font_size=12,
            anchor_x="center", anchor_y="center",
        )

    def _draw_game_over_message(self):
        # Semi-transparent overlay
        arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 400, 120), (0, 0, 0, 180))
        arcade.draw_rect_outline(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 400, 120), arcade.color.WHITE, 2)
        if self.won:
            msg = f"You Win! Guessed in {len(self.guesses)} attempt(s)!"
            color = arcade.color.LIGHT_GREEN
        else:
            msg = "Game Over! You ran out of attempts."
            color = arcade.color.LIGHT_CORAL
        arcade.draw_text(
            msg, WIDTH / 2, HEIGHT / 2 + 15,
            color, font_size=20,
            anchor_x="center", anchor_y="center", bold=True,
        )
        arcade.draw_text(
            "Click 'New Game' to play again.",
            WIDTH / 2, HEIGHT / 2 - 25,
            arcade.color.LIGHT_GRAY, font_size=14,
            anchor_x="center", anchor_y="center",
        )

    def _calculate_feedback(self, guess):
        """Return (black_pegs, white_pegs) for a guess against the secret code."""
        black = 0
        secret_remaining = []
        guess_remaining = []
        for i in range(NUM_SLOTS):
            if guess[i] == self.secret_code[i]:
                black += 1
            else:
                secret_remaining.append(self.secret_code[i])
                guess_remaining.append(guess[i])
        white = 0
        secret_counts = {}
        for c in secret_remaining:
            secret_counts[c] = secret_counts.get(c, 0) + 1
        for c in guess_remaining:
            if secret_counts.get(c, 0) > 0:
                white += 1
                secret_counts[c] -= 1
        return (black, white)

    def _hit_rect(self, mx, my, cx, cy, w, h):
        return (cx - w / 2 <= mx <= cx + w / 2) and (cy - h / 2 <= my <= cy + h / 2)

    def _hit_circle(self, mx, my, cx, cy, r):
        return (mx - cx) ** 2 + (my - cy) ** 2 <= r ** 2

    def on_mouse_press(self, x, y, button, modifiers):
        # Back button
        if self._hit_rect(x, y, 60, HEIGHT - 30, 90, 36):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if self._hit_rect(x, y, WIDTH - 70, HEIGHT - 30, 110, 36):
            self.reset_game()
            return

        # Help button
        if self._hit_rect(x, y, WIDTH - 140, HEIGHT - 30, 40, 36):
            rules_view = RulesView("Mastermind", "mastermind.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self.game_over:
            return

        # Color palette
        palette_start_x = WIDTH / 2 - (NUM_COLORS - 1) * PALETTE_SPACING / 2
        for i in range(NUM_COLORS):
            px = palette_start_x + i * PALETTE_SPACING
            if self._hit_circle(x, y, px, PALETTE_Y, PALETTE_RADIUS + 4):
                self.selected_color = i
                return

        # Current row slots
        row_y = self._row_y(self.current_row)
        for slot in range(NUM_SLOTS):
            sx = self._slot_x(slot)
            if self._hit_circle(x, y, sx, row_y, SLOT_RADIUS + 4):
                self.current_guess[slot] = self.selected_color
                return

        # Submit button
        all_filled = all(c is not None for c in self.current_guess)
        if all_filled and self._hit_rect(x, y, WIDTH - 70, row_y, 100, 32):
            self._submit_guess()

    def _submit_guess(self):
        guess = list(self.current_guess)
        self.guesses.append(guess)
        fb = self._calculate_feedback(guess)
        self.feedback.append(fb)

        if fb[0] == NUM_SLOTS:
            self.game_over = True
            self.won = True
            return

        self.current_row += 1
        self.current_guess = [None, None, None, None]

        if self.current_row >= MAX_ATTEMPTS:
            self.game_over = True
            self.won = False


# Allow running standalone for testing
if __name__ == "__main__":
    window = arcade.Window(WIDTH, HEIGHT, "Mastermind")
    arcade.set_background_color((40, 40, 60))

    class DummyMenu(arcade.View):
        def on_draw(self):
            self.clear()
            arcade.draw_text("Menu (placeholder)", WIDTH / 2, HEIGHT / 2,
                             arcade.color.WHITE, 20, anchor_x="center")

    menu = DummyMenu()
    game = MastermindView(menu)
    window.show_view(game)
    arcade.run()
