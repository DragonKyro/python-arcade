import arcade
from pages.rules import RulesView
from renderers import rush_hour_renderer
from renderers.rush_hour_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT, CELL_SIZE,
    GRID_ORIGIN_X, GRID_ORIGIN_Y, GRID_SIZE,
    PLAYING, WON,
)


# Each car: (id, row, col, length, orientation, color)
# orientation: 'H' = horizontal, 'V' = vertical
# row/col are the top-left cell of the car (row 0 = bottom, col 0 = left)
# Red car (id=0) must be horizontal on row 2

PUZZLES = [
    # Puzzle 1 - Easy
    [
        (0, 2, 0, 2, 'H', (220, 50, 50)),   # Red car
        (1, 0, 0, 3, 'V', (50, 180, 50)),
        (2, 0, 1, 2, 'H', (50, 50, 200)),
        (3, 3, 2, 3, 'V', (200, 150, 50)),
        (4, 4, 4, 2, 'H', (180, 50, 180)),
    ],
    # Puzzle 2
    [
        (0, 2, 1, 2, 'H', (220, 50, 50)),
        (1, 0, 0, 2, 'V', (50, 180, 50)),
        (2, 3, 0, 3, 'V', (50, 50, 200)),
        (3, 0, 3, 3, 'V', (200, 150, 50)),
        (4, 5, 1, 2, 'H', (180, 50, 180)),
        (5, 0, 4, 2, 'H', (50, 200, 200)),
    ],
    # Puzzle 3
    [
        (0, 2, 0, 2, 'H', (220, 50, 50)),
        (1, 0, 0, 2, 'V', (50, 180, 50)),
        (2, 3, 0, 2, 'V', (50, 50, 200)),
        (3, 0, 2, 3, 'V', (200, 150, 50)),
        (4, 5, 0, 2, 'H', (180, 50, 180)),
        (5, 3, 3, 2, 'H', (50, 200, 200)),
        (6, 4, 4, 2, 'V', (200, 100, 50)),
    ],
    # Puzzle 4
    [
        (0, 2, 0, 2, 'H', (220, 50, 50)),
        (1, 0, 0, 3, 'V', (50, 180, 50)),
        (2, 3, 0, 3, 'V', (50, 50, 200)),
        (3, 0, 1, 2, 'H', (200, 150, 50)),
        (4, 0, 3, 2, 'V', (180, 50, 180)),
        (5, 4, 2, 2, 'H', (50, 200, 200)),
        (6, 3, 4, 3, 'V', (200, 100, 50)),
        (7, 1, 4, 2, 'H', (100, 200, 100)),
    ],
    # Puzzle 5 - Hard
    [
        (0, 2, 1, 2, 'H', (220, 50, 50)),
        (1, 0, 0, 2, 'V', (50, 180, 50)),
        (2, 3, 0, 3, 'V', (50, 50, 200)),
        (3, 0, 2, 3, 'V', (200, 150, 50)),
        (4, 5, 0, 3, 'H', (180, 50, 180)),
        (5, 0, 4, 2, 'V', (50, 200, 200)),
        (6, 4, 3, 2, 'H', (200, 100, 50)),
        (7, 3, 4, 2, 'V', (100, 200, 100)),
        (8, 1, 5, 2, 'V', (200, 200, 50)),
    ],
]


class RushHourView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.current_level = 0
        self._create_texts()
        self._init_game()

    def _create_texts(self):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        self.txt_back = arcade.Text(
            "Back", 55, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_new_game = arcade.Text(
            "New Game", WIDTH - 65, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_help = arcade.Text(
            "?", WIDTH - 135, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_moves = arcade.Text(
            "", 250, bar_y, arcade.color.YELLOW,
            font_size=16, anchor_x="center", anchor_y="center",
        )
        self.txt_level = arcade.Text(
            "", 400, bar_y, arcade.color.YELLOW,
            font_size=16, anchor_x="center", anchor_y="center",
        )
        self.txt_you_win = arcade.Text(
            "LEVEL COMPLETE!", WIDTH / 2, HEIGHT / 2 + 10,
            arcade.color.YELLOW, font_size=36,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_info = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 - 30,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )

    def _init_game(self):
        """Load the current puzzle level."""
        puzzle_data = PUZZLES[self.current_level]
        self.cars = []
        for car_id, row, col, length, orient, color in puzzle_data:
            self.cars.append({
                'id': car_id,
                'row': row,
                'col': col,
                'length': length,
                'orient': orient,
                'color': color,
            })
        self.game_state = PLAYING
        self.moves = 0
        self.dragging_car = None
        self.drag_start_pixel = None
        self.drag_start_pos = None

    def _get_occupied_cells(self, exclude_id=None):
        """Return set of (row, col) occupied by all cars except exclude_id."""
        occupied = set()
        for car in self.cars:
            if car['id'] == exclude_id:
                continue
            for i in range(car['length']):
                if car['orient'] == 'H':
                    occupied.add((car['row'], car['col'] + i))
                else:
                    occupied.add((car['row'] + i, car['col']))
        return occupied

    def _car_at_pixel(self, x, y):
        """Find which car is at pixel (x, y), or None."""
        col = (x - GRID_ORIGIN_X) / CELL_SIZE
        row = (y - GRID_ORIGIN_Y) / CELL_SIZE
        for car in self.cars:
            if car['orient'] == 'H':
                if (car['row'] <= row < car['row'] + 1 and
                        car['col'] <= col < car['col'] + car['length']):
                    return car
            else:
                if (car['row'] <= row < car['row'] + car['length'] and
                        car['col'] <= col < car['col'] + 1):
                    return car
        return None

    def _check_win(self):
        """Red car (id=0) reaches right edge: col + length >= GRID_SIZE."""
        red_car = self.cars[0]
        if red_car['col'] + red_car['length'] >= GRID_SIZE:
            self.game_state = WON

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def on_draw(self):
        self.clear()
        rush_hour_renderer.draw(self)

    def on_mouse_press(self, x, y, button, modifiers):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        if self._hit_test_button(x, y, 55, bar_y, 90, 35):
            self.window.show_view(self.menu_view)
            return

        if self._hit_test_button(x, y, WIDTH - 65, bar_y, 110, 35):
            if self.game_state == WON:
                self.current_level = (self.current_level + 1) % len(PUZZLES)
            self._init_game()
            return

        if self._hit_test_button(x, y, WIDTH - 135, bar_y, 40, 35):
            rules_view = RulesView("Rush Hour", "rush_hour.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self.game_state != PLAYING:
            return

        car = self._car_at_pixel(x, y)
        if car:
            self.dragging_car = car
            self.drag_start_pixel = (x, y)
            self.drag_start_pos = (car['row'], car['col'])

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.dragging_car is None or self.game_state != PLAYING:
            return

        car = self.dragging_car
        start_x, start_y = self.drag_start_pixel
        start_row, start_col = self.drag_start_pos
        occupied = self._get_occupied_cells(exclude_id=car['id'])

        if car['orient'] == 'H':
            delta_cells = round((x - start_x) / CELL_SIZE)
            new_col = start_col + delta_cells
            # Clamp to grid bounds
            new_col = max(0, min(GRID_SIZE - car['length'], new_col))
            # Check collisions by trying each position between current and target
            step = 1 if new_col >= car['col'] else -1
            final_col = car['col']
            for c in range(car['col'] + step, new_col + step, step):
                blocked = False
                for i in range(car['length']):
                    if (car['row'], c + i) in occupied:
                        blocked = True
                        break
                if blocked:
                    break
                final_col = c
            car['col'] = final_col
        else:
            delta_cells = round((y - start_y) / CELL_SIZE)
            new_row = start_row + delta_cells
            new_row = max(0, min(GRID_SIZE - car['length'], new_row))
            step = 1 if new_row >= car['row'] else -1
            final_row = car['row']
            for r in range(car['row'] + step, new_row + step, step):
                blocked = False
                for i in range(car['length']):
                    if (r + i, car['col']) in occupied:
                        blocked = True
                        break
                if blocked:
                    break
                final_row = r
            car['row'] = final_row

    def on_mouse_release(self, x, y, button, modifiers):
        if self.dragging_car is not None and self.drag_start_pos is not None:
            car = self.dragging_car
            if (car['row'], car['col']) != self.drag_start_pos:
                self.moves += 1
                self._check_win()
        self.dragging_car = None
        self.drag_start_pixel = None
        self.drag_start_pos = None
