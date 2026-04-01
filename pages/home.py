import arcade
from pages.components import Button

WIDTH = 800
HEIGHT = 600


class HomeView(arcade.View):
    def __init__(self):
        super().__init__()

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
                    from pages.games import GamesView
                    self.window.show_view(GamesView())
                elif btn.text == "Settings":
                    print("Settings clicked")
                elif btn.text == "Credits":
                    print("Credits clicked")
                elif btn.text == "Exit":
                    arcade.close_window()
