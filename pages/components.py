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
        self.label = arcade.Text(
            text, center_x, center_y, arcade.color.WHITE,
            font_size=20, anchor_x="center", anchor_y="center",
        )

    def draw(self):
        arcade.draw_rect_filled(arcade.XYWH(self.center_x, self.center_y, self.width, self.height), self.color)
        arcade.draw_rect_outline(arcade.XYWH(self.center_x, self.center_y, self.width, self.height), arcade.color.WHITE)
        self.label.x = self.center_x
        self.label.y = self.center_y
        self.label.text = self.text
        self.label.draw()

    def hit_test(self, x, y):
        return (
            x >= self.center_x - self.width / 2
            and x <= self.center_x + self.width / 2
            and y >= self.center_y - self.height / 2
            and y <= self.center_y + self.height / 2
        )
