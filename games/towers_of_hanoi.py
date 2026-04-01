import arcade
from pages.rules import RulesView
from renderers import towers_of_hanoi_renderer
from renderers.towers_of_hanoi_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT, PLAYING, WON,
    CONFIG_Y, CONFIG_BTN_SIZE, peg_base_x,
    MAX_DISK_WIDTH, PEG_Y_BASE, PEG_HEIGHT,
)


class TowersOfHanoiView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.num_disks = 3
        self._create_texts()
        self._init_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        self.txt_back = arcade.Text(
            "Back", 55, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_moves = arcade.Text(
            "", 200, bar_y, arcade.color.YELLOW,
            font_size=16, anchor_x="center", anchor_y="center",
        )
        self.txt_min_moves = arcade.Text(
            "", 330, bar_y, arcade.color.LIGHT_GRAY,
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

        # Disk count selector texts
        self.txt_disks_label = arcade.Text(
            "Disks:", 200, CONFIG_Y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_disk_counts = []
        for i, n in enumerate(range(3, 8)):
            bx = 250 + i * (CONFIG_BTN_SIZE + 10)
            t = arcade.Text(
                str(n), bx, CONFIG_Y, arcade.color.WHITE,
                font_size=14, anchor_x="center", anchor_y="center",
                bold=True,
            )
            self.txt_disk_counts.append(t)

        self.txt_you_win = arcade.Text(
            "YOU WIN!", WIDTH / 2, HEIGHT / 2 + 20,
            arcade.color.YELLOW, font_size=44,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_details = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 - 25,
            arcade.color.WHITE, font_size=18,
            anchor_x="center", anchor_y="center",
        )

    def _init_game(self):
        """Initialize or reset game state."""
        # pegs[0] = leftmost, pegs[2] = rightmost
        # Each peg is a list of disk sizes, bottom to top
        # Size: num_disks (largest) down to 1 (smallest)
        self.pegs = [[], [], []]
        for size in range(self.num_disks, 0, -1):
            self.pegs[0].append(size)
        self.selected_peg = None
        self.move_count = 0
        self.game_state = PLAYING

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def _peg_from_click(self, x, y):
        """Return peg index (0-2) from a click, or None."""
        for i in range(3):
            px = peg_base_x(i)
            zone_w = MAX_DISK_WIDTH + 20
            zone_h = PEG_HEIGHT + 60
            zone_y = PEG_Y_BASE + PEG_HEIGHT / 2
            if (px - zone_w / 2 <= x <= px + zone_w / 2 and
                    zone_y - zone_h / 2 <= y <= zone_y + zone_h / 2):
                return i
        return None

    def _try_place(self, from_peg, to_peg):
        """Try to move top disk from from_peg to to_peg. Returns True if successful."""
        if not self.pegs[from_peg]:
            return False
        disk = self.pegs[from_peg][-1]
        if self.pegs[to_peg] and self.pegs[to_peg][-1] < disk:
            return False
        self.pegs[to_peg].append(self.pegs[from_peg].pop())
        self.move_count += 1
        self._check_win()
        return True

    def _check_win(self):
        """Win when all disks are on the rightmost peg."""
        if len(self.pegs[2]) == self.num_disks:
            self.game_state = WON

    def on_draw(self):
        self.clear()
        towers_of_hanoi_renderer.draw(self)

    def on_mouse_press(self, x, y, button, modifiers):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        # Back button
        if self._hit_test_button(x, y, 55, bar_y, 90, 35):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if self._hit_test_button(x, y, WIDTH - 65, bar_y, 110, 35):
            self._init_game()
            return

        # Help button
        if self._hit_test_button(x, y, WIDTH - 135, bar_y, 40, 35):
            rules_view = RulesView(
                "Towers of Hanoi", "towers_of_hanoi.txt", None,
                self.menu_view, existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        # Disk count selector buttons
        for i, n in enumerate(range(3, 8)):
            bx = 250 + i * (CONFIG_BTN_SIZE + 10)
            if self._hit_test_button(x, y, bx, CONFIG_Y, CONFIG_BTN_SIZE, CONFIG_BTN_SIZE):
                self.num_disks = n
                self._init_game()
                return

        if self.game_state != PLAYING:
            return

        # Peg click
        peg = self._peg_from_click(x, y)
        if peg is None:
            return

        if self.selected_peg is None:
            # Pick up from this peg if it has disks
            if self.pegs[peg]:
                self.selected_peg = peg
        else:
            if peg == self.selected_peg:
                # Deselect
                self.selected_peg = None
            else:
                # Try to place
                self._try_place(self.selected_peg, peg)
                self.selected_peg = None
