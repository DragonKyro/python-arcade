import os
import arcade
from pages.components import Button
from games import GAME_LIST

WIDTH = 800
HEIGHT = 600
TOP_BAR_HEIGHT = 100
CONTENT_TOP = HEIGHT - TOP_BAR_HEIGHT
CONTENT_BOTTOM = 10
SCROLLBAR_WIDTH = 8
SCROLLBAR_X = WIDTH - 12
SCROLLBAR_COLOR = (255, 255, 255, 120)
ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons")


class GamesView(arcade.View):
    def __init__(self):
        super().__init__()
        self.view_mode = "list"
        self.scroll_y = 0

        self.back_button = Button(
            80, HEIGHT - 40, 120, 50, "Back", color=arcade.color.DARK_SLATE_BLUE
        )
        self.toggle_button = Button(
            WIDTH - 120, HEIGHT - 40, 200, 50,
            "View: List", color=arcade.color.DARK_SLATE_BLUE,
        )

        # Pre-load icon textures
        self.icon_textures = {}
        for name, _, _, icon_file in GAME_LIST:
            path = os.path.join(ICONS_DIR, icon_file)
            if os.path.exists(path):
                self.icon_textures[name] = arcade.load_texture(path)

        self.game_buttons = []
        self.game_entries = []
        self._build_game_list()

        self.txt_header = arcade.Text(
            "Select a Game", WIDTH / 2, HEIGHT - 70,
            arcade.color.WHITE, font_size=36, anchor_x="center",
        )
        self.txt_icon_label = arcade.Text(
            "", 0, 0, arcade.color.WHITE,
            font_size=11, anchor_x="center", anchor_y="center",
        )

    def _build_game_list(self):
        self.game_buttons.clear()
        self.game_entries.clear()
        self.scroll_y = 0

        # Position items starting just below the top bar
        if self.view_mode == "list":
            btn_w = 400
            btn_h = 42
            spacing = 10
            start_y = CONTENT_TOP - spacing - btn_h / 2
            for i, (name, view_cls, rules_file, _icon) in enumerate(GAME_LIST):
                cy = start_y - i * (btn_h + spacing)
                btn = Button(
                    WIDTH / 2, cy, btn_w, btn_h, name,
                    color=arcade.color.DARK_SLATE_BLUE,
                )
                self.game_buttons.append(btn)
                self.game_entries.append((view_cls, rules_file, name))
        else:
            icon_size = 120
            label_height = 22
            cell_height = icon_size + label_height
            spacing = 16
            cols = 4
            total_w = cols * icon_size + (cols - 1) * spacing
            start_x = WIDTH / 2 - total_w / 2 + icon_size / 2
            start_y = CONTENT_TOP - spacing - cell_height / 2
            for i, (name, view_cls, rules_file, _icon) in enumerate(GAME_LIST):
                col = i % cols
                row = i // cols
                cx = start_x + col * (icon_size + spacing)
                cy = start_y - row * (cell_height + spacing)
                btn = Button(
                    cx, cy, icon_size, cell_height, name,
                    color=arcade.color.DARK_SLATE_BLUE,
                )
                self.game_buttons.append(btn)
                self.game_entries.append((view_cls, rules_file, name))

    def _max_scroll(self):
        if not self.game_buttons:
            return 0
        lowest = min(b.center_y - b.height / 2 for b in self.game_buttons)
        if lowest < CONTENT_BOTTOM:
            return abs(lowest - CONTENT_BOTTOM)
        return 0

    def _content_height(self):
        if not self.game_buttons:
            return 0
        highest = max(b.center_y + b.height / 2 for b in self.game_buttons)
        lowest = min(b.center_y - b.height / 2 for b in self.game_buttons)
        return highest - lowest

    def on_show(self):
        arcade.set_background_color(arcade.color.AMAZON)

    def on_draw(self):
        self.clear()

        # Draw scrollable game buttons
        for idx, btn in enumerate(self.game_buttons):
            draw_y = btn.center_y + self.scroll_y
            if draw_y + btn.height / 2 < CONTENT_BOTTOM or draw_y - btn.height / 2 > CONTENT_TOP:
                continue

            name = self.game_entries[idx][2]

            if self.view_mode == "icons" and name in self.icon_textures:
                arcade.draw_rect_filled(
                    arcade.XYWH(btn.center_x, draw_y, btn.width, btn.height),
                    arcade.color.DARK_SLATE_BLUE,
                )
                arcade.draw_rect_outline(
                    arcade.XYWH(btn.center_x, draw_y, btn.width, btn.height),
                    arcade.color.WHITE,
                )
                tex = self.icon_textures[name]
                icon_y = draw_y + 11
                arcade.draw_texture_rect(
                    tex,
                    arcade.XYWH(btn.center_x, icon_y, btn.width - 8, btn.width - 8),
                )
                label_y = draw_y - btn.height / 2 + 12
                self.txt_icon_label.text = name
                self.txt_icon_label.x = btn.center_x
                self.txt_icon_label.y = label_y
                self.txt_icon_label.draw()
            else:
                orig_y = btn.center_y
                btn.center_y = draw_y
                btn.draw()
                btn.center_y = orig_y

        # Scrollbar
        max_s = self._max_scroll()
        if max_s > 0:
            visible_height = CONTENT_TOP - CONTENT_BOTTOM
            total = self._content_height()
            bar_height = max(30, visible_height * (visible_height / (total + visible_height)))
            track_height = visible_height - bar_height
            bar_y = CONTENT_TOP - bar_height / 2 - (self.scroll_y / max_s) * track_height
            arcade.draw_rect_filled(
                arcade.XYWH(SCROLLBAR_X, bar_y, SCROLLBAR_WIDTH, bar_height),
                SCROLLBAR_COLOR,
            )

        # Top bar (covers scrolled content)
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT - TOP_BAR_HEIGHT / 2, WIDTH, TOP_BAR_HEIGHT),
            arcade.color.AMAZON,
        )
        self.txt_header.draw()
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

        if y > CONTENT_TOP:
            return

        for i, btn in enumerate(self.game_buttons):
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
        self.scroll_y -= scroll_y * 30
        max_s = self._max_scroll()
        if self.scroll_y < 0:
            self.scroll_y = 0
        if self.scroll_y > max_s:
            self.scroll_y = max_s
