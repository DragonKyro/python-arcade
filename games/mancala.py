import arcade
import copy
from ai.mancala_ai import MancalaAI, sow
from pages.rules import RulesView

# Window constants
WIDTH = 800
HEIGHT = 600

# Board layout constants
BOARD_CX = WIDTH / 2
BOARD_CY = HEIGHT / 2
BOARD_W = 700
BOARD_H = 260
BOARD_CORNER = 60

STORE_W = 70
STORE_H = 180
PIT_RADIUS = 36
PIT_SPACING = 85
PITS_START_X = BOARD_CX - 2.5 * PIT_SPACING

PLAYER_ROW_Y = BOARD_CY - 55
AI_ROW_Y = BOARD_CY + 55
STORE_Y = BOARD_CY

LEFT_STORE_X = BOARD_CX - BOARD_W / 2 + STORE_W / 2 + 15
RIGHT_STORE_X = BOARD_CX + BOARD_W / 2 - STORE_W / 2 - 15

STONE_RADIUS = 5
STONE_COLOR = (180, 140, 100)

BOARD_COLOR = (101, 67, 33)
BOARD_OUTLINE_COLOR = (60, 40, 20)
PIT_COLOR = (70, 45, 20)
PIT_HIGHLIGHT_COLOR = (140, 200, 140)
STORE_COLOR = (80, 50, 25)

PLAYER_SIDE = 0
AI_SIDE = 1

# Timing
AI_DELAY = 0.5
EXTRA_TURN_DISPLAY_TIME = 1.5


class MancalaView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.ai = MancalaAI()
        self.reset_game()

    def reset_game(self):
        """Initialize or reset all game state."""
        self.pits = [[4] * 6, [4] * 6]  # [player_pits, ai_pits]
        self.stores = [0, 0]  # [player_store, ai_store]
        self.player_turn = True
        self.game_over = False
        self.winner = None  # "Player", "AI", or "Tie"
        self.ai_timer = 0.0
        self.ai_thinking = False
        self.extra_turn_text = ""
        self.extra_turn_timer = 0.0
        self.hovered_pit = -1

    def on_show(self):
        arcade.set_background_color((40, 60, 40))

    # ------------------------------------------------------------------ draw
    def on_draw(self):
        self.clear()

        # Title
        arcade.draw_text(
            "Mancala",
            WIDTH / 2, HEIGHT - 30,
            arcade.color.WHITE, font_size=28,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Back button
        self._draw_button(60, HEIGHT - 30, 90, 36, "Back", arcade.color.DARK_SLATE_BLUE)
        # New Game button
        self._draw_button(WIDTH - 70, HEIGHT - 30, 110, 36, "New Game", arcade.color.DARK_GREEN)
        # Help button
        self._draw_button(WIDTH - 140, HEIGHT - 30, 40, 36, "?", arcade.color.DARK_SLATE_BLUE)

        self._draw_board()
        self._draw_pits()
        self._draw_stores()
        self._draw_labels()

        if self.extra_turn_timer > 0:
            arcade.draw_text(
                self.extra_turn_text,
                WIDTH / 2, HEIGHT / 2,
                arcade.color.YELLOW, font_size=22,
                anchor_x="center", anchor_y="center", bold=True,
            )

        if self.game_over:
            self._draw_game_over()

    def _draw_button(self, cx, cy, w, h, text, color):
        arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), color)
        arcade.draw_rect_outline(arcade.XYWH(cx, cy, w, h), arcade.color.WHITE)
        arcade.draw_text(
            text, cx, cy, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )

    def _draw_board(self):
        """Draw the rounded board background."""
        arcade.draw_rect_filled(arcade.XYWH(BOARD_CX, BOARD_CY, BOARD_W, BOARD_H), BOARD_COLOR)
        arcade.draw_rect_outline(arcade.XYWH(BOARD_CX, BOARD_CY, BOARD_W, BOARD_H), BOARD_OUTLINE_COLOR, 3)
        # Rounded ends (circles at left/right)
        arcade.draw_circle_filled(BOARD_CX - BOARD_W / 2, BOARD_CY, BOARD_H / 2, BOARD_COLOR)
        arcade.draw_circle_filled(BOARD_CX + BOARD_W / 2, BOARD_CY, BOARD_H / 2, BOARD_COLOR)
        arcade.draw_circle_outline(BOARD_CX - BOARD_W / 2, BOARD_CY, BOARD_H / 2, BOARD_OUTLINE_COLOR, 3)
        arcade.draw_circle_outline(BOARD_CX + BOARD_W / 2, BOARD_CY, BOARD_H / 2, BOARD_OUTLINE_COLOR, 3)

    def _pit_x(self, index):
        """X position for pit index 0-5 (left to right)."""
        return PITS_START_X + index * PIT_SPACING

    def _draw_pits(self):
        """Draw all 12 pits with stones."""
        for i in range(6):
            px = self._pit_x(i)

            # --- Player pit (bottom row) ---
            is_valid = (
                self.player_turn
                and not self.game_over
                and self.pits[PLAYER_SIDE][i] > 0
            )
            is_hovered = is_valid and self.hovered_pit == i
            pit_col = PIT_HIGHLIGHT_COLOR if is_hovered else (PIT_COLOR if not is_valid else (90, 65, 35))
            outline_col = arcade.color.LIGHT_GREEN if is_valid else BOARD_OUTLINE_COLOR

            arcade.draw_circle_filled(px, PLAYER_ROW_Y, PIT_RADIUS, pit_col)
            arcade.draw_circle_outline(px, PLAYER_ROW_Y, PIT_RADIUS, outline_col, 2)
            self._draw_stones_in_pit(px, PLAYER_ROW_Y, self.pits[PLAYER_SIDE][i])

            # --- AI pit (top row, mirrored: AI pit 0 is above player pit 5) ---
            ai_display_index = 5 - i
            ai_px = self._pit_x(i)
            arcade.draw_circle_filled(ai_px, AI_ROW_Y, PIT_RADIUS, PIT_COLOR)
            arcade.draw_circle_outline(ai_px, AI_ROW_Y, PIT_RADIUS, BOARD_OUTLINE_COLOR, 2)
            self._draw_stones_in_pit(ai_px, AI_ROW_Y, self.pits[AI_SIDE][ai_display_index])

    def _draw_stones_in_pit(self, cx, cy, count):
        """Draw stone count and small circles if count <= 10."""
        if count <= 0:
            return

        # Draw small stone circles for counts up to 10
        if count <= 10:
            positions = self._stone_positions(cx, cy, count)
            for sx, sy in positions:
                arcade.draw_circle_filled(sx, sy, STONE_RADIUS, STONE_COLOR)
                arcade.draw_circle_outline(sx, sy, STONE_RADIUS, (120, 90, 60), 1)

        # Always draw count text
        arcade.draw_text(
            str(count), cx, cy - PIT_RADIUS - 12,
            arcade.color.WHITE, font_size=12,
            anchor_x="center", anchor_y="center", bold=True,
        )

    def _stone_positions(self, cx, cy, count):
        """Return a list of (x, y) positions to draw stones in a pit."""
        import math
        positions = []
        if count == 1:
            positions.append((cx, cy))
        elif count <= 4:
            offsets = [(-8, -8), (8, -8), (-8, 8), (8, 8)]
            for k in range(count):
                positions.append((cx + offsets[k][0], cy + offsets[k][1]))
        elif count <= 10:
            # Arrange in a circle
            radius = min(18, PIT_RADIUS - STONE_RADIUS - 4)
            for k in range(count):
                angle = 2 * math.pi * k / count - math.pi / 2
                sx = cx + radius * math.cos(angle)
                sy = cy + radius * math.sin(angle)
                positions.append((sx, sy))
        return positions

    def _draw_stores(self):
        """Draw the two stores on left and right ends."""
        # AI store (left end for display — AI's store is on the left
        # when player sits at bottom)
        # Actually in Mancala: player's store is to their right,
        # AI's store is to AI's right (player's left).
        # Player store = right, AI store = left.

        # AI store (left)
        arcade.draw_rect_filled(arcade.XYWH(LEFT_STORE_X, STORE_Y, STORE_W, STORE_H), STORE_COLOR)
        arcade.draw_rect_outline(arcade.XYWH(LEFT_STORE_X, STORE_Y, STORE_W, STORE_H), BOARD_OUTLINE_COLOR, 2)
        arcade.draw_text(
            str(self.stores[AI_SIDE]),
            LEFT_STORE_X, STORE_Y,
            arcade.color.WHITE, font_size=24,
            anchor_x="center", anchor_y="center", bold=True,
        )
        arcade.draw_text(
            "AI", LEFT_STORE_X, STORE_Y + STORE_H / 2 + 12,
            arcade.color.LIGHT_GRAY, font_size=11,
            anchor_x="center", anchor_y="center",
        )

        # Player store (right)
        arcade.draw_rect_filled(arcade.XYWH(RIGHT_STORE_X, STORE_Y, STORE_W, STORE_H), STORE_COLOR)
        arcade.draw_rect_outline(arcade.XYWH(RIGHT_STORE_X, STORE_Y, STORE_W, STORE_H), BOARD_OUTLINE_COLOR, 2)
        arcade.draw_text(
            str(self.stores[PLAYER_SIDE]),
            RIGHT_STORE_X, STORE_Y,
            arcade.color.WHITE, font_size=24,
            anchor_x="center", anchor_y="center", bold=True,
        )
        arcade.draw_text(
            "You", RIGHT_STORE_X, STORE_Y - STORE_H / 2 - 12,
            arcade.color.LIGHT_GRAY, font_size=11,
            anchor_x="center", anchor_y="center",
        )

    def _draw_labels(self):
        """Draw row labels and turn indicator."""
        # Turn indicator
        if not self.game_over:
            if self.player_turn:
                turn_text = "Your turn — click a highlighted pit"
            else:
                turn_text = "AI is thinking..."
            arcade.draw_text(
                turn_text, WIDTH / 2, 40,
                arcade.color.WHITE, font_size=14,
                anchor_x="center", anchor_y="center",
            )

        # Pit index labels for player
        for i in range(6):
            px = self._pit_x(i)
            arcade.draw_text(
                str(i + 1), px, PLAYER_ROW_Y - PIT_RADIUS - 26,
                arcade.color.LIGHT_GRAY, font_size=10,
                anchor_x="center", anchor_y="center",
            )

    def _draw_game_over(self):
        """Draw game over overlay."""
        arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 420, 140), (0, 0, 0, 200))
        arcade.draw_rect_outline(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 420, 140), arcade.color.WHITE, 2)

        if self.winner == "Tie":
            msg = "It's a tie!"
            color = arcade.color.LIGHT_STEEL_BLUE
        elif self.winner == "Player":
            msg = "You win!"
            color = arcade.color.LIGHT_GREEN
        else:
            msg = "AI wins!"
            color = arcade.color.LIGHT_CORAL

        score_msg = f"You: {self.stores[PLAYER_SIDE]}  —  AI: {self.stores[AI_SIDE]}"

        arcade.draw_text(
            msg, WIDTH / 2, HEIGHT / 2 + 25,
            color, font_size=26,
            anchor_x="center", anchor_y="center", bold=True,
        )
        arcade.draw_text(
            score_msg, WIDTH / 2, HEIGHT / 2 - 10,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )
        arcade.draw_text(
            "Click 'New Game' to play again.",
            WIDTH / 2, HEIGHT / 2 - 40,
            arcade.color.LIGHT_GRAY, font_size=13,
            anchor_x="center", anchor_y="center",
        )

    # --------------------------------------------------------------- update
    def on_update(self, delta_time):
        # Extra turn message timer
        if self.extra_turn_timer > 0:
            self.extra_turn_timer -= delta_time
            if self.extra_turn_timer <= 0:
                self.extra_turn_text = ""

        if self.game_over:
            return

        # AI turn with delay
        if not self.player_turn:
            self.ai_timer += delta_time
            if self.ai_timer >= AI_DELAY:
                self._do_ai_move()

    def _do_ai_move(self):
        """Execute the AI's move."""
        move = self.ai.get_move(self.pits, self.stores, AI_SIDE)
        if move is None:
            # No valid move — game should end
            self._check_game_over()
            return

        new_pits, new_stores, extra_turn, _ = sow(
            self.pits, self.stores, AI_SIDE, move
        )
        self.pits = new_pits
        self.stores = new_stores

        if self._check_game_over():
            return

        if extra_turn:
            self.extra_turn_text = "AI gets an extra turn!"
            self.extra_turn_timer = EXTRA_TURN_DISPLAY_TIME
            self.ai_timer = 0.0  # reset delay for next AI move
        else:
            self.player_turn = True
            self.ai_timer = 0.0

    # --------------------------------------------------------------- input
    def on_mouse_motion(self, x, y, dx, dy):
        self.hovered_pit = -1
        if not self.player_turn or self.game_over:
            return
        for i in range(6):
            px = self._pit_x(i)
            if (x - px) ** 2 + (y - PLAYER_ROW_Y) ** 2 <= PIT_RADIUS ** 2:
                if self.pits[PLAYER_SIDE][i] > 0:
                    self.hovered_pit = i
                break

    def on_mouse_press(self, x, y, button, modifiers):
        # Back button
        if self._hit_rect(x, y, 60, HEIGHT - 30, 90, 36):
            self.window.show_view(self.menu_view)
            return

        # Help button
        if self._hit_rect(x, y, WIDTH - 140, HEIGHT - 30, 40, 36):
            rules_view = RulesView("Mancala", "mancala.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        # New Game button
        if self._hit_rect(x, y, WIDTH - 70, HEIGHT - 30, 110, 36):
            self.reset_game()
            return

        if self.game_over or not self.player_turn:
            return

        # Check if a player pit was clicked
        for i in range(6):
            px = self._pit_x(i)
            if (x - px) ** 2 + (y - PLAYER_ROW_Y) ** 2 <= PIT_RADIUS ** 2:
                if self.pits[PLAYER_SIDE][i] > 0:
                    self._do_player_move(i)
                return

    def _do_player_move(self, pit_index):
        """Execute the player's move."""
        new_pits, new_stores, extra_turn, _ = sow(
            self.pits, self.stores, PLAYER_SIDE, pit_index
        )
        self.pits = new_pits
        self.stores = new_stores

        if self._check_game_over():
            return

        if extra_turn:
            self.extra_turn_text = "Extra turn!"
            self.extra_turn_timer = EXTRA_TURN_DISPLAY_TIME
            # player_turn stays True
        else:
            self.player_turn = False
            self.ai_timer = 0.0

    def _check_game_over(self):
        """Check if the game is over. If so, finalize scores."""
        player_empty = all(s == 0 for s in self.pits[PLAYER_SIDE])
        ai_empty = all(s == 0 for s in self.pits[AI_SIDE])

        if not player_empty and not ai_empty:
            return False

        # Remaining stones go to the opponent's store
        # (Standard Kalah: remaining stones go to the side that still has them)
        for side in range(2):
            self.stores[side] += sum(self.pits[side])
            self.pits[side] = [0] * 6

        self.game_over = True
        if self.stores[PLAYER_SIDE] > self.stores[AI_SIDE]:
            self.winner = "Player"
        elif self.stores[AI_SIDE] > self.stores[PLAYER_SIDE]:
            self.winner = "AI"
        else:
            self.winner = "Tie"
        return True

    def _hit_rect(self, mx, my, cx, cy, w, h):
        return (cx - w / 2 <= mx <= cx + w / 2) and (cy - h / 2 <= my <= cy + h / 2)


# Allow running standalone for testing
if __name__ == "__main__":
    window = arcade.Window(WIDTH, HEIGHT, "Mancala")
    arcade.set_background_color((40, 60, 40))

    class DummyMenu(arcade.View):
        def on_draw(self):
            self.clear()
            arcade.draw_text("Menu (placeholder)", WIDTH / 2, HEIGHT / 2,
                             arcade.color.WHITE, 20, anchor_x="center")

    menu = DummyMenu()
    game = MancalaView(menu)
    window.show_view(game)
    arcade.run()
