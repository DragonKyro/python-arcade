"""
Frogger game view for Python Arcade 3.x.
Classic Frogger gameplay: guide your frog across roads and rivers to reach home.
"""

import arcade
import random
import math

from pages.rules import RulesView

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
BOTTOM_BAR_HEIGHT = 40
CELL_SIZE = 40
COLS = WIDTH // CELL_SIZE  # 20 columns
ROWS = 13  # rows 0-12

# Play area origin (bottom-left of row 0)
GRID_ORIGIN_Y = BOTTOM_BAR_HEIGHT

# Colors
BG_COLOR = (30, 30, 46)
GRASS_COLOR = (34, 120, 34)
ROAD_COLOR = (60, 60, 60)
MEDIAN_COLOR = (34, 120, 34)
WATER_COLOR = (30, 80, 180)
HOME_ROW_COLOR = (20, 70, 20)
SIDEWALK_COLOR = (100, 100, 80)
LINE_COLOR = (205, 214, 244)
BUTTON_COLOR = (69, 71, 90)
BUTTON_HOVER_COLOR = (88, 91, 112)
BUTTON_TEXT_COLOR = (205, 214, 244)
OVERLAY_COLOR = (30, 30, 46, 200)
SCORE_COLOR = (249, 226, 175)
FROG_COLOR = (50, 200, 50)
FROG_EYE_COLOR = (255, 255, 255)
FROG_PUPIL_COLOR = (0, 0, 0)
LOG_COLOR = (139, 90, 43)
LOG_BARK_COLOR = (110, 70, 30)
TURTLE_COLOR = (34, 140, 34)
TURTLE_SHELL_COLOR = (20, 100, 20)
TURTLE_DIVE_COLOR = (30, 80, 180, 120)
CAR_COLORS = [
    (220, 50, 50),   # red
    (50, 50, 220),   # blue
    (220, 220, 50),  # yellow
    (220, 130, 50),  # orange
    (180, 50, 220),  # purple
]
TRUCK_COLOR = (180, 180, 180)
LILY_PAD_COLOR = (30, 160, 30)
LILY_PAD_FILLED_COLOR = (50, 200, 50)
TIMER_BG_COLOR = (60, 60, 60)
TIMER_FG_COLOR = (50, 200, 50)
TIMER_LOW_COLOR = (220, 50, 50)
LANE_MARKER_COLOR = (200, 200, 50)
WHITE_COLOR = (255, 255, 255)

# Timing
TIMER_DURATION = 30.0  # seconds per frog life

# Lane definitions: (row, type, direction, speed, objects)
# direction: 1 = right, -1 = left
# speed in pixels per second
LANE_CONFIGS = [
    # Road lanes (rows 1-5)
    {"row": 1, "kind": "road", "dir": -1, "speed": 60,  "obj": "car",    "count": 3, "length": 1, "gap_min": 3, "gap_max": 5},
    {"row": 2, "kind": "road", "dir":  1, "speed": 80,  "obj": "truck",  "count": 2, "length": 3, "gap_min": 4, "gap_max": 6},
    {"row": 3, "kind": "road", "dir": -1, "speed": 100, "obj": "car",    "count": 3, "length": 1, "gap_min": 3, "gap_max": 5},
    {"row": 4, "kind": "road", "dir":  1, "speed": 50,  "obj": "car",    "count": 4, "length": 1, "gap_min": 2, "gap_max": 4},
    {"row": 5, "kind": "road", "dir": -1, "speed": 120, "obj": "truck",  "count": 2, "length": 2, "gap_min": 5, "gap_max": 7},
    # River lanes (rows 7-11)
    {"row": 7,  "kind": "river", "dir":  1, "speed": 50,  "obj": "log",    "count": 3, "length": 3, "gap_min": 3, "gap_max": 5},
    {"row": 8,  "kind": "river", "dir": -1, "speed": 70,  "obj": "turtle", "count": 3, "length": 2, "gap_min": 3, "gap_max": 5, "diving": True},
    {"row": 9,  "kind": "river", "dir":  1, "speed": 40,  "obj": "log",    "count": 2, "length": 4, "gap_min": 3, "gap_max": 5},
    {"row": 10, "kind": "river", "dir": -1, "speed": 90,  "obj": "turtle", "count": 3, "length": 3, "gap_min": 3, "gap_max": 4, "diving": False},
    {"row": 11, "kind": "river", "dir":  1, "speed": 60,  "obj": "log",    "count": 2, "length": 2, "gap_min": 4, "gap_max": 6},
]

# Home slot positions (5 evenly spaced in row 12)
HOME_SLOT_COLS = [2, 6, 10, 14, 18]


class _Button:
    """Simple rectangular button helper."""

    def __init__(self, cx, cy, w, h, label):
        self.cx = cx
        self.cy = cy
        self.w = w
        self.h = h
        self.label = label

    def contains(self, x, y):
        return (abs(x - self.cx) <= self.w / 2) and (abs(y - self.cy) <= self.h / 2)

    def draw(self, hover=False):
        color = BUTTON_HOVER_COLOR if hover else BUTTON_COLOR
        arcade.draw_rect_filled(arcade.XYWH(self.cx, self.cy, self.w, self.h), color)
        arcade.draw_rect_outline(arcade.XYWH(self.cx, self.cy, self.w, self.h), LINE_COLOR, 2)
        arcade.draw_text(
            self.label,
            self.cx,
            self.cy,
            BUTTON_TEXT_COLOR,
            font_size=14,
            anchor_x="center",
            anchor_y="center",
        )


class _LaneObject:
    """A moving object in a lane (car, truck, log, or turtle group)."""

    def __init__(self, x, row, length, direction, speed, kind, diving=False):
        self.x = x  # pixel x position of left edge
        self.row = row
        self.length = length  # in cells
        self.direction = direction  # 1 or -1
        self.speed = speed  # pixels per second
        self.kind = kind  # "car", "truck", "log", "turtle"
        self.can_dive = diving
        self.diving = False
        self.dive_timer = random.uniform(4.0, 8.0) if diving else 0
        self.dive_blink_time = 0.0
        self.color_index = random.randint(0, len(CAR_COLORS) - 1)

    @property
    def width_px(self):
        return self.length * CELL_SIZE

    @property
    def center_x(self):
        return self.x + self.width_px / 2

    @property
    def center_y(self):
        return GRID_ORIGIN_Y + self.row * CELL_SIZE + CELL_SIZE / 2

    def update(self, dt):
        self.x += self.direction * self.speed * dt

        # Wrap around
        if self.direction > 0 and self.x > WIDTH + CELL_SIZE:
            self.x = -self.width_px - CELL_SIZE
        elif self.direction < 0 and self.x + self.width_px < -CELL_SIZE:
            self.x = WIDTH + CELL_SIZE

        # Diving logic for turtles
        if self.can_dive:
            self.dive_timer -= dt
            if self.dive_timer <= 0:
                if not self.diving:
                    self.diving = True
                    self.dive_timer = 2.0  # stay submerged for 2s
                    self.dive_blink_time = 0.0
                else:
                    self.diving = False
                    self.dive_timer = random.uniform(4.0, 8.0)
                    self.dive_blink_time = 0.0
            # Blink before diving (last 1.5 seconds before dive)
            if not self.diving and self.dive_timer < 1.5:
                self.dive_blink_time += dt

    def contains_col(self, col):
        """Check if a grid column overlaps this object."""
        px_left = col * CELL_SIZE
        px_right = px_left + CELL_SIZE
        obj_left = self.x
        obj_right = self.x + self.width_px
        return obj_right > px_left + 4 and obj_left < px_right - 4

    def is_safe(self):
        """Whether a frog can safely ride on this object."""
        if self.kind in ("log",):
            return True
        if self.kind == "turtle":
            return not self.diving
        return False

    def draw(self):
        cx = self.center_x
        cy = self.center_y
        w = self.width_px - 4
        h = CELL_SIZE - 4

        if self.kind == "car":
            color = CAR_COLORS[self.color_index]
            arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), color)
            # Windshield
            ws_offset = -8 * self.direction
            arcade.draw_rect_filled(
                arcade.XYWH(cx + ws_offset, cy, w * 0.3, h * 0.6),
                (180, 220, 255),
            )
            # Headlights
            hl_x = cx + (w / 2 - 3) * self.direction
            arcade.draw_circle_filled(hl_x, cy + 6, 3, (255, 255, 150))
            arcade.draw_circle_filled(hl_x, cy - 6, 3, (255, 255, 150))

        elif self.kind == "truck":
            arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), TRUCK_COLOR)
            # Cab
            cab_x = cx + (w / 2 - CELL_SIZE * 0.4) * self.direction
            arcade.draw_rect_filled(
                arcade.XYWH(cab_x, cy, CELL_SIZE * 0.7, h), (200, 60, 60)
            )
            # Cargo outline
            arcade.draw_rect_outline(arcade.XYWH(cx, cy, w, h), (80, 80, 80), 2)

        elif self.kind == "log":
            arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), LOG_COLOR)
            # Wood grain lines
            for i in range(self.length):
                lx = self.x + i * CELL_SIZE + CELL_SIZE / 2
                arcade.draw_line(lx - 5, cy - 5, lx + 5, cy + 5, LOG_BARK_COLOR, 2)
                arcade.draw_line(lx + 8, cy - 8, lx + 15, cy - 2, LOG_BARK_COLOR, 1)
            # Rounded ends
            arcade.draw_circle_filled(self.x + 2, cy, h / 2, LOG_COLOR)
            arcade.draw_circle_filled(self.x + self.width_px - 2, cy, h / 2, LOG_COLOR)

        elif self.kind == "turtle":
            if self.diving:
                # Underwater - faint outline
                arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), TURTLE_DIVE_COLOR)
            else:
                # Blink warning before dive
                if self.can_dive and not self.diving and self.dive_timer < 1.5:
                    blink = math.sin(self.dive_blink_time * 10) > 0
                    if blink:
                        base_color = (100, 180, 100)
                    else:
                        base_color = TURTLE_COLOR
                else:
                    base_color = TURTLE_COLOR

                # Draw each turtle in the group
                for i in range(self.length):
                    tx = self.x + i * CELL_SIZE + CELL_SIZE / 2
                    # Shell (oval)
                    arcade.draw_ellipse_filled(tx, cy, CELL_SIZE - 8, CELL_SIZE - 8, base_color)
                    arcade.draw_ellipse_filled(tx, cy, CELL_SIZE - 14, CELL_SIZE - 14, TURTLE_SHELL_COLOR)
                    # Head
                    head_x = tx + 10 * self.direction
                    arcade.draw_circle_filled(head_x, cy, 4, base_color)
                    # Legs
                    for dy in (-1, 1):
                        arcade.draw_circle_filled(tx - 6, cy + dy * 12, 3, base_color)
                        arcade.draw_circle_filled(tx + 6, cy + dy * 12, 3, base_color)


class FroggerView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.high_score = 0
        self.mouse_x = 0
        self.mouse_y = 0

        # Buttons
        self.btn_back = _Button(60, HEIGHT - 25, 90, 34, "Back")
        self.btn_new = _Button(WIDTH - 80, HEIGHT - 25, 110, 34, "New Game")
        self.btn_help = _Button(WIDTH - 150, HEIGHT - 25, 40, 40, "?")

        self._init_game()

    def _init_game(self):
        """Initialize or reset all game state."""
        self.frog_col = COLS // 2
        self.frog_row = 0
        self.max_row_reached = 0
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_over = False
        self.timer = TIMER_DURATION
        self.homes_filled = [False] * 5
        self.lane_objects = []
        self._build_lanes()

    def _build_lanes(self):
        """Create all lane objects based on config and current level."""
        self.lane_objects = []
        speed_mult = 1.0 + (self.level - 1) * 0.15

        for cfg in LANE_CONFIGS:
            row = cfg["row"]
            direction = cfg["dir"]
            speed = cfg["speed"] * speed_mult
            kind = cfg["obj"]
            count = cfg["count"]
            length = cfg["length"]
            gap_min = cfg["gap_min"]
            gap_max = cfg["gap_max"]
            diving = cfg.get("diving", False)

            # Spread objects evenly with some randomness
            total_span = count * length * CELL_SIZE
            remaining = WIDTH + 2 * CELL_SIZE  # extra space for wrapping
            spacing = remaining / count

            for i in range(count):
                gap_offset = random.randint(0, (gap_max - gap_min) * CELL_SIZE)
                x = i * spacing + gap_offset - CELL_SIZE
                obj = _LaneObject(x, row, length, direction, speed, kind, diving)
                self.lane_objects.append(obj)

    def _reset_frog(self):
        """Reset frog to start position after death or home reached."""
        self.frog_col = COLS // 2
        self.frog_row = 0
        self.max_row_reached = 0
        self.timer = TIMER_DURATION

    def _kill_frog(self):
        """Handle frog death."""
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
            if self.score > self.high_score:
                self.high_score = self.score
        else:
            self._reset_frog()

    def _check_home_slot(self):
        """Check if frog landed in a home slot."""
        if self.frog_row != 12:
            return

        # Check each home slot
        for i, slot_col in enumerate(HOME_SLOT_COLS):
            if abs(self.frog_col - slot_col) <= 0:
                if self.homes_filled[i]:
                    # Already filled - death
                    self._kill_frog()
                    return
                else:
                    self.homes_filled[i] = True
                    self.score += 50
                    # Check if all homes filled
                    if all(self.homes_filled):
                        self.score += 1000
                        self.level += 1
                        self.homes_filled = [False] * 5
                        self._build_lanes()
                    self._reset_frog()
                    return

        # Landed between slots - death
        self._kill_frog()

    def _get_objects_in_row(self, row):
        """Get all lane objects in a given row."""
        return [obj for obj in self.lane_objects if obj.row == row]

    def _frog_on_river_object(self):
        """Check if frog is on a safe river object. Returns the object or None."""
        if self.frog_row < 7 or self.frog_row > 11:
            return None
        objects = self._get_objects_in_row(self.frog_row)
        for obj in objects:
            if obj.contains_col(self.frog_col) and obj.is_safe():
                return obj
        return None

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_update(self, delta_time):
        if self.game_over:
            return

        # Update timer
        self.timer -= delta_time
        if self.timer <= 0:
            self._kill_frog()
            return

        # Update all lane objects
        for obj in self.lane_objects:
            obj.update(delta_time)

        # If frog is on a river object, move with it
        if 7 <= self.frog_row <= 11:
            river_obj = self._frog_on_river_object()
            if river_obj:
                # Move frog with the object
                pixel_move = river_obj.direction * river_obj.speed * delta_time
                # Convert pixel movement to fractional column and accumulate
                frog_px = self.frog_col * CELL_SIZE + pixel_move
                self.frog_col = frog_px / CELL_SIZE

                # Check if frog went off screen
                if self.frog_col < -0.5 or self.frog_col >= COLS + 0.5:
                    self._kill_frog()
                    return
            else:
                # In river but not on anything - death
                self._kill_frog()
                return

        # Check vehicle collision (road rows 1-5)
        if 1 <= self.frog_row <= 5:
            objects = self._get_objects_in_row(self.frog_row)
            frog_col_int = int(round(self.frog_col))
            for obj in objects:
                if obj.contains_col(frog_col_int):
                    self._kill_frog()
                    return

    def on_key_press(self, key, modifiers):
        if self.game_over:
            if key == arcade.key.SPACE:
                self._init_game()
            return

        frog_col_int = int(round(self.frog_col))
        new_col = frog_col_int
        new_row = self.frog_row

        if key == arcade.key.UP:
            new_row = self.frog_row + 1
        elif key == arcade.key.DOWN:
            new_row = max(0, self.frog_row - 1)
        elif key == arcade.key.LEFT:
            new_col = frog_col_int - 1
        elif key == arcade.key.RIGHT:
            new_col = frog_col_int + 1

        # Bounds check
        if new_col < 0 or new_col >= COLS:
            return
        if new_row > 12:
            return

        # Apply movement
        if new_row != self.frog_row or new_col != frog_col_int:
            self.frog_col = float(new_col)
            self.frog_row = new_row

            # Score for forward progress
            if new_row > self.max_row_reached:
                self.score += 10 * (new_row - self.max_row_reached)
                self.max_row_reached = new_row

            # Check home row
            if self.frog_row == 12:
                self._check_home_slot()

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if self.btn_back.contains(x, y):
            self.window.show_view(self.menu_view)
        elif self.btn_new.contains(x, y):
            self._init_game()
        elif self.btn_help.contains(x, y):
            rules_view = RulesView(
                "Frogger", "frogger.txt", None, self.menu_view,
                existing_game_view=self,
            )
            self.window.show_view(rules_view)

    def on_draw(self):
        self.clear()

        # Draw row backgrounds
        self._draw_row_backgrounds()

        # Draw lane markings on road
        self._draw_lane_markings()

        # Draw home slots
        self._draw_home_slots()

        # Draw lane objects
        for obj in self.lane_objects:
            obj.draw()

        # Draw frog
        if not self.game_over:
            self._draw_frog()

        # Draw filled homes
        self._draw_filled_homes()

        # Draw UI
        self._draw_top_bar()
        self._draw_bottom_bar()

        # Game over overlay
        if self.game_over:
            self._draw_game_over()

    def _draw_row_backgrounds(self):
        """Draw background color for each row."""
        for row in range(ROWS):
            y = GRID_ORIGIN_Y + row * CELL_SIZE + CELL_SIZE / 2

            if row == 0:
                color = SIDEWALK_COLOR
            elif 1 <= row <= 5:
                color = ROAD_COLOR
            elif row == 6:
                color = MEDIAN_COLOR
            elif 7 <= row <= 11:
                color = WATER_COLOR
            elif row == 12:
                color = HOME_ROW_COLOR
            else:
                color = BG_COLOR

            arcade.draw_rect_filled(
                arcade.XYWH(WIDTH / 2, y, WIDTH, CELL_SIZE), color
            )

    def _draw_lane_markings(self):
        """Draw dashed lane markings on roads."""
        for row in range(1, 5):  # between lanes
            y = GRID_ORIGIN_Y + (row + 1) * CELL_SIZE
            for x in range(0, WIDTH, 40):
                arcade.draw_line(x, y, x + 20, y, LANE_MARKER_COLOR, 1)

    def _draw_home_slots(self):
        """Draw the 5 home slot indicators."""
        y = GRID_ORIGIN_Y + 12 * CELL_SIZE + CELL_SIZE / 2
        for col in HOME_SLOT_COLS:
            x = col * CELL_SIZE + CELL_SIZE / 2
            # Dark alcove
            arcade.draw_rect_filled(
                arcade.XYWH(x, y, CELL_SIZE - 2, CELL_SIZE - 2),
                (10, 50, 10),
            )
            # Lily pad circle
            arcade.draw_circle_filled(x, y, CELL_SIZE / 2 - 4, LILY_PAD_COLOR)
            arcade.draw_circle_filled(x, y, CELL_SIZE / 2 - 8, (40, 130, 40))

    def _draw_filled_homes(self):
        """Draw small frogs in filled home slots."""
        y = GRID_ORIGIN_Y + 12 * CELL_SIZE + CELL_SIZE / 2
        for i, filled in enumerate(self.homes_filled):
            if filled:
                col = HOME_SLOT_COLS[i]
                x = col * CELL_SIZE + CELL_SIZE / 2
                # Mini frog
                arcade.draw_circle_filled(x, y, 10, FROG_COLOR)
                arcade.draw_circle_filled(x - 4, y + 5, 3, FROG_EYE_COLOR)
                arcade.draw_circle_filled(x + 4, y + 5, 3, FROG_EYE_COLOR)
                arcade.draw_circle_filled(x - 4, y + 5, 1.5, FROG_PUPIL_COLOR)
                arcade.draw_circle_filled(x + 4, y + 5, 1.5, FROG_PUPIL_COLOR)

    def _draw_frog(self):
        """Draw the frog at its current position."""
        x = self.frog_col * CELL_SIZE + CELL_SIZE / 2
        y = GRID_ORIGIN_Y + self.frog_row * CELL_SIZE + CELL_SIZE / 2

        # Body
        arcade.draw_rect_filled(
            arcade.XYWH(x, y, CELL_SIZE - 6, CELL_SIZE - 6),
            FROG_COLOR,
        )

        # Body rounded look
        arcade.draw_circle_filled(x, y + (CELL_SIZE / 2 - 5), 10, FROG_COLOR)
        arcade.draw_circle_filled(x, y - (CELL_SIZE / 2 - 5), 8, FROG_COLOR)

        # Eyes (on top portion)
        eye_y = y + 8
        for dx in (-7, 7):
            arcade.draw_circle_filled(x + dx, eye_y, 5, FROG_EYE_COLOR)
            arcade.draw_circle_filled(x + dx, eye_y, 2.5, FROG_PUPIL_COLOR)

        # Legs (small bumps)
        for dx in (-12, 12):
            arcade.draw_circle_filled(x + dx, y + 5, 4, FROG_COLOR)
            arcade.draw_circle_filled(x + dx, y - 8, 4, FROG_COLOR)

    def _draw_top_bar(self):
        """Draw the top bar with buttons and score."""
        # Background
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT - TOP_BAR_HEIGHT / 2, WIDTH, TOP_BAR_HEIGHT),
            BG_COLOR,
        )
        arcade.draw_line(0, HEIGHT - TOP_BAR_HEIGHT, WIDTH, HEIGHT - TOP_BAR_HEIGHT, LINE_COLOR, 1)

        # Buttons
        self.btn_back.draw(self.btn_back.contains(self.mouse_x, self.mouse_y))
        self.btn_help.draw(self.btn_help.contains(self.mouse_x, self.mouse_y))
        self.btn_new.draw(self.btn_new.contains(self.mouse_x, self.mouse_y))

        # Score in center
        arcade.draw_text(
            f"Score: {self.score}",
            WIDTH / 2,
            HEIGHT - 25,
            SCORE_COLOR,
            font_size=16,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )

    def _draw_bottom_bar(self):
        """Draw bottom bar with lives, level, timer, and high score."""
        # Background
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, BOTTOM_BAR_HEIGHT / 2, WIDTH, BOTTOM_BAR_HEIGHT),
            BG_COLOR,
        )
        arcade.draw_line(0, BOTTOM_BAR_HEIGHT, WIDTH, BOTTOM_BAR_HEIGHT, LINE_COLOR, 1)

        # Lives (small frog icons)
        arcade.draw_text("Lives:", 10, 20, LINE_COLOR, font_size=12, anchor_x="left", anchor_y="center")
        for i in range(self.lives):
            lx = 70 + i * 25
            arcade.draw_circle_filled(lx, 20, 8, FROG_COLOR)
            arcade.draw_circle_filled(lx - 2, 24, 2, FROG_EYE_COLOR)
            arcade.draw_circle_filled(lx + 2, 24, 2, FROG_EYE_COLOR)

        # Level
        arcade.draw_text(
            f"Level: {self.level}",
            200,
            20,
            LINE_COLOR,
            font_size=12,
            anchor_x="left",
            anchor_y="center",
        )

        # Timer bar
        timer_x = 320
        timer_w = 200
        timer_h = 14
        timer_y = 20
        # Background
        arcade.draw_rect_filled(
            arcade.XYWH(timer_x + timer_w / 2, timer_y, timer_w, timer_h),
            TIMER_BG_COLOR,
        )
        # Fill
        frac = max(0, self.timer / TIMER_DURATION)
        fill_w = timer_w * frac
        fill_color = TIMER_FG_COLOR if frac > 0.3 else TIMER_LOW_COLOR
        if fill_w > 0:
            arcade.draw_rect_filled(
                arcade.XYWH(timer_x + fill_w / 2, timer_y, fill_w, timer_h),
                fill_color,
            )
        arcade.draw_rect_outline(
            arcade.XYWH(timer_x + timer_w / 2, timer_y, timer_w, timer_h),
            LINE_COLOR, 1,
        )
        arcade.draw_text("TIME", timer_x - 35, 20, LINE_COLOR, font_size=10, anchor_x="left", anchor_y="center")

        # High score
        arcade.draw_text(
            f"Hi: {self.high_score}",
            WIDTH - 10,
            20,
            SCORE_COLOR,
            font_size=12,
            anchor_x="right",
            anchor_y="center",
        )

    def _draw_game_over(self):
        """Draw game over overlay."""
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
            OVERLAY_COLOR,
        )
        arcade.draw_text(
            "GAME OVER",
            WIDTH / 2,
            HEIGHT / 2 + 40,
            (220, 50, 50),
            font_size=36,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        arcade.draw_text(
            f"Final Score: {self.score}",
            WIDTH / 2,
            HEIGHT / 2 - 10,
            SCORE_COLOR,
            font_size=20,
            anchor_x="center",
            anchor_y="center",
        )
        arcade.draw_text(
            "Press SPACE or click New Game to restart",
            WIDTH / 2,
            HEIGHT / 2 - 50,
            LINE_COLOR,
            font_size=14,
            anchor_x="center",
            anchor_y="center",
        )
