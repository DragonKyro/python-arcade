import arcade
import random
from pages.rules import RulesView
from renderers import mastermind_renderer
from renderers.mastermind_renderer import (
    WIDTH, HEIGHT, NUM_SLOTS, MAX_ATTEMPTS, NUM_COLORS,
    BOARD_LEFT, ROW_HEIGHT, SLOT_RADIUS, SLOT_SPACING,
    PALETTE_Y, PALETTE_SPACING, PALETTE_RADIUS,
)


class MastermindView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self._create_texts()
        self.reset_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        self.txt_title = arcade.Text(
            "Mastermind", WIDTH / 2, HEIGHT - 30, arcade.color.WHITE,
            font_size=28, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_back = arcade.Text(
            "Back", 60, HEIGHT - 30, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_new_game = arcade.Text(
            "New Game", WIDTH - 70, HEIGHT - 30, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_help = arcade.Text(
            "?", WIDTH - 140, HEIGHT - 30, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_submit = arcade.Text(
            "Submit", WIDTH - 70, 0, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        # Row number labels (1..10)
        self.txt_row_numbers = []
        for row in range(MAX_ATTEMPTS):
            base_y = 90
            y = base_y + row * ROW_HEIGHT
            t = arcade.Text(
                str(row + 1), BOARD_LEFT - 40, y,
                arcade.color.LIGHT_GRAY, font_size=12,
                anchor_x="center", anchor_y="center",
            )
            self.txt_row_numbers.append(t)
        self.txt_secret_label = arcade.Text(
            "Secret:", BOARD_LEFT - 40, 0,
            arcade.color.LIGHT_CORAL, font_size=12,
            anchor_x="center", anchor_y="center",
        )
        self.txt_select_color = arcade.Text(
            "Select a color:", WIDTH / 2, PALETTE_Y + 35,
            arcade.color.LIGHT_GRAY, font_size=12,
            anchor_x="center", anchor_y="center",
        )
        self.txt_game_over_msg = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 + 15,
            arcade.color.LIGHT_GREEN, font_size=20,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_hint = arcade.Text(
            "Click 'New Game' to play again.",
            WIDTH / 2, HEIGHT / 2 - 25,
            arcade.color.LIGHT_GRAY, font_size=14,
            anchor_x="center", anchor_y="center",
        )

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
        mastermind_renderer.draw(self)

    def _row_y(self, row_index):
        """Return the y-coordinate for a given row (0=bottom row, 9=top row)."""
        base_y = 90
        return base_y + row_index * ROW_HEIGHT

    def _slot_x(self, slot_index):
        """Return the x-coordinate for a given slot in a row."""
        return BOARD_LEFT + slot_index * SLOT_SPACING

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
        def __init__(self):
            super().__init__()
            self.txt_menu = arcade.Text(
                "Menu (placeholder)", WIDTH / 2, HEIGHT / 2,
                arcade.color.WHITE, font_size=20, anchor_x="center",
            )

        def on_draw(self):
            self.clear()
            self.txt_menu.draw()

    menu = DummyMenu()
    game = MastermindView(menu)
    window.show_view(game)
    arcade.run()
