import arcade
from pages import HomeView

WIDTH = 800
HEIGHT = 600
TITLE = "Python Arcade"


def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    window.show_view(HomeView())
    arcade.run()


if __name__ == "__main__":
    main()
