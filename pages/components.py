import arcade


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
