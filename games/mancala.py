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
        from renderers import mancala_renderer
        mancala_renderer.draw(self)

    def _pit_x(self, index):
        """X position for pit index 0-5 (left to right)."""
        return PITS_START_X + index * PIT_SPACING

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
