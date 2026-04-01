import arcade
from games import GAME_LIST

# Window constants
WIDTH = 800
HEIGHT = 600
TITLE = "Python Arcade"


class Button:
    def __init__(
        self, center_x, center_y, width, height, text, color=arcade.color.DARK_BLUE
    ):
        self.center_x = center_x
        self.center_y = center_y
        self.width = width
        self.height = height
        self.text = text
        self.color = color

    def draw(self):
        arcade.draw_rectangle_filled(
            self.center_x, self.center_y, self.width, self.height, self.color
        )
        arcade.draw_rectangle_outline(
            self.center_x, self.center_y, self.width, self.height, arcade.color.WHITE
        )
        arcade.draw_text(
            self.text,
            self.center_x,
            self.center_y,
            arcade.color.WHITE,
            font_size=20,
            anchor_x="center",
            anchor_y="center",
        )

    def hit_test(self, x, y):
        return (
            x >= self.center_x - self.width / 2
            and x <= self.center_x + self.width / 2
            and y >= self.center_y - self.height / 2
            and y <= self.center_y + self.height / 2
        )


class HomeView(arcade.View):
    def __init__(self):
        super().__init__()

        # Layout buttons vertically centered
        btn_w = 300
        btn_h = 60
        spacing = 20
        total_height = 4 * btn_h + 3 * spacing
        start_y = HEIGHT / 2 + total_height / 2 - btn_h / 2

        labels = ["Play", "Settings", "Credits", "Exit"]
        self.buttons = []
        for i, label in enumerate(labels):
            cx = WIDTH / 2
            cy = start_y - i * (btn_h + spacing)
            self.buttons.append(Button(cx, cy, btn_w, btn_h, label))

    def on_show(self):
        arcade.set_background_color(arcade.color.AMAZON)

    def on_draw(self):
        arcade.start_render()
        arcade.draw_text(
            "Python Arcade",
            WIDTH / 2,
            HEIGHT - 80,
            arcade.color.WHITE,
            font_size=48,
            anchor_x="center",
        )
        for btn in self.buttons:
            btn.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        for btn in self.buttons:
            if btn.hit_test(x, y):
                if btn.text == "Play":
                    games_view = GamesView()
                    self.window.show_view(games_view)
                elif btn.text == "Settings":
                    print("Settings clicked")
                elif btn.text == "Credits":
                    print("Credits clicked")
                elif btn.text == "Exit":
                    arcade.close_window()


class GamesView(arcade.View):
    def __init__(self):
        super().__init__()
        self.view_mode = "list"

        # Top bar buttons
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

        # Build game buttons from the registry
        self.game_buttons = []
        self.game_classes = []
        self._build_game_list()

    def _build_game_list(self):
        """Build clickable buttons for each registered game."""
        self.game_buttons.clear()
        self.game_classes.clear()

        if self.view_mode == "list":
            btn_w = 400
            btn_h = 55
            spacing = 15
            total_height = len(GAME_LIST) * btn_h + (len(GAME_LIST) - 1) * spacing
            start_y = (HEIGHT - 100) / 2 + total_height / 2 - btn_h / 2
            for i, (name, view_cls) in enumerate(GAME_LIST):
                cy = start_y - i * (btn_h + spacing)
                btn = Button(
                    WIDTH / 2, cy, btn_w, btn_h, name,
                    color=arcade.color.DARK_SLATE_BLUE,
                )
                self.game_buttons.append(btn)
                self.game_classes.append(view_cls)
        else:
            # Icon / grid mode
            icon_size = 140
            spacing = 30
            cols = 3
            rows = (len(GAME_LIST) + cols - 1) // cols
            total_w = cols * icon_size + (cols - 1) * spacing
            total_h = rows * icon_size + (rows - 1) * spacing
            start_x = WIDTH / 2 - total_w / 2 + icon_size / 2
            start_y = (HEIGHT - 100) / 2 + total_h / 2 - icon_size / 2
            for i, (name, view_cls) in enumerate(GAME_LIST):
                col = i % cols
                row = i // cols
                cx = start_x + col * (icon_size + spacing)
                cy = start_y - row * (icon_size + spacing)
                btn = Button(
                    cx, cy, icon_size, icon_size, name,
                    color=arcade.color.DARK_SLATE_BLUE,
                )
                self.game_buttons.append(btn)
                self.game_classes.append(view_cls)

    def on_show(self):
        arcade.set_background_color(arcade.color.AMAZON)

    def on_draw(self):
        arcade.start_render()
        # Header
        arcade.draw_text(
            "Select a Game",
            WIDTH / 2,
            HEIGHT - 80,
            arcade.color.WHITE,
            font_size=40,
            anchor_x="center",
        )
        self.back_button.draw()
        self.toggle_button.draw()

        # Game entries
        for btn in self.game_buttons:
            btn.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if self.back_button.hit_test(x, y):
            home_view = HomeView()
            self.window.show_view(home_view)
            return

        if self.toggle_button.hit_test(x, y):
            self.view_mode = "icons" if self.view_mode == "list" else "list"
            self.toggle_button.text = f"View: {self.view_mode.title()}"
            self._build_game_list()
            return

        # Check game buttons
        for i, btn in enumerate(self.game_buttons):
            if btn.hit_test(x, y):
                game_view = self.game_classes[i](menu_view=self)
                self.window.show_view(game_view)
                return


def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    home_view = HomeView()
    window.show_view(home_view)
    arcade.run()


if __name__ == "__main__":
    main()
