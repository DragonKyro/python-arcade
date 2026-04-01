import os
import arcade
from pages.components import Button

WIDTH = 800
HEIGHT = 600


class RulesView(arcade.View):
    """Displays game rules. Can launch a new game or return to an existing one."""

    def __init__(self, game_name, rules_file, game_view_class, menu_view,
                 existing_game_view=None):
        super().__init__()
        self.game_name = game_name
        self.game_view_class = game_view_class
        self.menu_view = menu_view
        self.existing_game_view = existing_game_view

        # Load rules text
        rules_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "rules", rules_file
        )
        try:
            with open(rules_path, "r") as f:
                self.rules_text = f.read()
        except FileNotFoundError:
            self.rules_text = "No rules available."

        # Buttons
        self.back_button = Button(
            80, HEIGHT - 40, 120, 50, "Back", color=arcade.color.DARK_SLATE_BLUE
        )

        if self.existing_game_view:
            # Opened from in-game "?" — show Resume button
            self.play_button = Button(
                WIDTH / 2, 40, 200, 50, "Resume", color=arcade.color.DARK_GREEN
            )
        else:
            # Opened from game selection — show Play button
            self.play_button = Button(
                WIDTH / 2, 40, 200, 50, "Play", color=arcade.color.DARK_GREEN
            )

        # Scroll state
        self.scroll_y = 0
        self._compute_text_height()

    def _compute_text_height(self):
        lines = self.rules_text.split("\n")
        self.text_line_height = 22
        self.total_text_height = len(lines) * self.text_line_height

    def on_show(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

    def on_draw(self):
        self.clear()

        # Rules text area (between top bar and bottom button)
        text_top = HEIGHT - 90
        text_bottom = 80
        text_area_height = text_top - text_bottom

        # Draw rules text
        lines = self.rules_text.split("\n")
        x = 60
        start_y = text_top + self.scroll_y

        for i, line in enumerate(lines):
            y = start_y - i * self.text_line_height
            if y > text_top + 10:
                continue
            if y < text_bottom - 10:
                break

            if line.isupper() and line.strip():
                # Section headers
                arcade.draw_text(
                    line, x, y, arcade.color.YELLOW,
                    font_size=16, bold=True,
                )
            else:
                arcade.draw_text(
                    line, x, y, arcade.color.WHITE,
                    font_size=13,
                )

        # Top bar background
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT - 35, WIDTH, 70),
            arcade.color.DARK_SLATE_GRAY,
        )
        arcade.draw_text(
            self.game_name,
            WIDTH / 2, HEIGHT - 45,
            arcade.color.WHITE,
            font_size=30,
            anchor_x="center",
        )
        self.back_button.draw()

        # Bottom bar background
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, 40, WIDTH, 70),
            arcade.color.DARK_SLATE_GRAY,
        )
        self.play_button.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if self.back_button.hit_test(x, y):
            self.window.show_view(self.menu_view)
            return

        if self.play_button.hit_test(x, y):
            if self.existing_game_view:
                self.window.show_view(self.existing_game_view)
            else:
                game_view = self.game_view_class(menu_view=self.menu_view)
                self.window.show_view(game_view)
            return

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.scroll_y -= scroll_y * 25
        max_scroll = max(0, self.total_text_height - (HEIGHT - 170))
        if self.scroll_y < 0:
            self.scroll_y = 0
        if self.scroll_y > max_scroll:
            self.scroll_y = max_scroll
