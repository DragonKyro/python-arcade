import os
import arcade
from pages.components import Button

WIDTH = 800
HEIGHT = 600
TEXT_TOP = HEIGHT - 90
TEXT_BOTTOM = 80
LINE_HEIGHT = 22


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
            self.play_button = Button(
                WIDTH / 2, 40, 200, 50, "Resume", color=arcade.color.DARK_GREEN
            )
        else:
            self.play_button = Button(
                WIDTH / 2, 40, 200, 50, "Play", color=arcade.color.DARK_GREEN
            )

        # Scroll state
        self.scroll_y = 0

        # Pre-created Text objects
        self.txt_title = arcade.Text(
            self.game_name, WIDTH / 2, HEIGHT - 45,
            arcade.color.WHITE, font_size=30, anchor_x="center",
        )

        # Create one Text object per line (avoids flicker from reuse)
        self.lines = self.rules_text.split("\n")
        self.line_texts = []
        for line in self.lines:
            is_header = line.isupper() and line.strip()
            txt = arcade.Text(
                line, 60, 0,
                arcade.color.YELLOW if is_header else arcade.color.WHITE,
                font_size=16 if is_header else 13,
                bold=is_header,
            )
            self.line_texts.append(txt)

        self.total_text_height = len(self.lines) * LINE_HEIGHT

    def on_show(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

    def on_draw(self):
        self.clear()

        # Draw rules lines
        start_y = TEXT_TOP + self.scroll_y
        for i, txt in enumerate(self.line_texts):
            y = start_y - i * LINE_HEIGHT
            if y > TEXT_TOP + 10:
                continue
            if y < TEXT_BOTTOM - 10:
                break
            txt.y = y
            txt.draw()

        # Top bar background (covers scrolled text)
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT - 35, WIDTH, 70),
            arcade.color.DARK_SLATE_GRAY,
        )
        self.txt_title.draw()
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
