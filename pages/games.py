import arcade
from pages.components import Button
from games import GAME_LIST

WIDTH = 800
HEIGHT = 600
TOP_BAR_HEIGHT = 100


class GamesView(arcade.View):
    def __init__(self):
        super().__init__()
        self.view_mode = "list"
        self.scroll_y = 0  # scroll offset (positive = scrolled down)

        self.back_button = Button(
            80, HEIGHT - 40, 120, 50, "Back", color=arcade.color.DARK_SLATE_BLUE
        )
        self.toggle_button = Button(
            WIDTH - 120,
            HEIGHT - 40,
            200,
            50,
            "View: List",
            color=arcade.color.DARK_SLATE_BLUE,
        )

        self.game_buttons = []
        self.game_entries = []  # (view_class, rules_file, display_name)
        self._build_game_list()

    def _build_game_list(self):
        self.game_buttons.clear()
        self.game_entries.clear()
        self.scroll_y = 0

        if self.view_mode == "list":
            btn_w = 400
            btn_h = 42
            spacing = 10
            total_height = len(GAME_LIST) * btn_h + (len(GAME_LIST) - 1) * spacing
            available = HEIGHT - TOP_BAR_HEIGHT
            start_y = available / 2 + total_height / 2 - btn_h / 2
            for i, (name, view_cls, rules_file) in enumerate(GAME_LIST):
                cy = start_y - i * (btn_h + spacing)
                btn = Button(
                    WIDTH / 2, cy, btn_w, btn_h, name,
                    color=arcade.color.DARK_SLATE_BLUE,
                )
                self.game_buttons.append(btn)
                self.game_entries.append((view_cls, rules_file, name))
        else:
            icon_size = 120
            spacing = 20
            cols = 4
            rows = (len(GAME_LIST) + cols - 1) // cols
            total_w = cols * icon_size + (cols - 1) * spacing
            total_h = rows * icon_size + (rows - 1) * spacing
            available = HEIGHT - TOP_BAR_HEIGHT
            start_x = WIDTH / 2 - total_w / 2 + icon_size / 2
            start_y = available / 2 + total_h / 2 - icon_size / 2
            for i, (name, view_cls, rules_file) in enumerate(GAME_LIST):
                col = i % cols
                row = i // cols
                cx = start_x + col * (icon_size + spacing)
                cy = start_y - row * (icon_size + spacing)
                btn = Button(
                    cx, cy, icon_size, icon_size, name,
                    color=arcade.color.DARK_SLATE_BLUE,
                )
                self.game_buttons.append(btn)
                self.game_entries.append((view_cls, rules_file, name))

    def _max_scroll(self):
        if not self.game_buttons:
            return 0
        lowest = min(b.center_y - b.height / 2 for b in self.game_buttons)
        if lowest < 10:
            return abs(lowest) + 10
        return 0

    def on_show(self):
        arcade.set_background_color(arcade.color.AMAZON)

    def on_draw(self):
        self.clear()

        # Draw scrollable game buttons
        for btn in self.game_buttons:
            # Offset by scroll, skip if above top bar or below screen
            draw_y = btn.center_y + self.scroll_y
            if draw_y + btn.height / 2 < 0 or draw_y - btn.height / 2 > HEIGHT - TOP_BAR_HEIGHT:
                continue
            # Temporarily shift for drawing
            orig_y = btn.center_y
            btn.center_y = draw_y
            btn.draw()
            btn.center_y = orig_y

        # Draw top bar background over scrolled content
        arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT - TOP_BAR_HEIGHT / 2, WIDTH, TOP_BAR_HEIGHT), arcade.color.AMAZON, )
        arcade.draw_text(
            "Select a Game",
            WIDTH / 2,
            HEIGHT - 70,
            arcade.color.WHITE,
            font_size=36,
            anchor_x="center",
        )
        self.back_button.draw()
        self.toggle_button.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if self.back_button.hit_test(x, y):
            from pages.home import HomeView
            self.window.show_view(HomeView())
            return

        if self.toggle_button.hit_test(x, y):
            self.view_mode = "icons" if self.view_mode == "list" else "list"
            self.toggle_button.text = f"View: {self.view_mode.title()}"
            self._build_game_list()
            return

        # Don't register clicks in the top bar area
        if y > HEIGHT - TOP_BAR_HEIGHT:
            return

        for i, btn in enumerate(self.game_buttons):
            # Adjust hit test for scroll offset
            shifted_y = btn.center_y + self.scroll_y
            if (
                x >= btn.center_x - btn.width / 2
                and x <= btn.center_x + btn.width / 2
                and y >= shifted_y - btn.height / 2
                and y <= shifted_y + btn.height / 2
            ):
                from pages.rules import RulesView
                view_cls, rules_file, name = self.game_entries[i]
                rules_view = RulesView(name, rules_file, view_cls, menu_view=self)
                self.window.show_view(rules_view)
                return

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.scroll_y += scroll_y * 30
        max_s = self._max_scroll()
        if self.scroll_y < 0:
            self.scroll_y = 0
        if self.scroll_y > max_s:
            self.scroll_y = max_s
