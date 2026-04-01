import arcade
from ai.mancala_ai import MancalaAI, sow
from pages.rules import RulesView
from renderers.mancala_renderer import (
    WIDTH, HEIGHT,
    PIT_RADIUS, PIT_SPACING, PITS_START_X,
    PLAYER_ROW_Y,
    PLAYER_SIDE, AI_SIDE,
    LEFT_STORE_X, RIGHT_STORE_X,
    STORE_H, STORE_Y,
    BOARD_CY,
)

# Timing
AI_DELAY = 0.5
EXTRA_TURN_DISPLAY_TIME = 1.5


class MancalaView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.ai = MancalaAI()
        self._create_texts()
        self.reset_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        # Title (static)
        self.txt_title = arcade.Text(
            "Mancala", WIDTH / 2, HEIGHT - 30,
            arcade.color.WHITE, font_size=28,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Button labels (static) -- drawn inside _draw_button, so we create them
        self.txt_btn_back = arcade.Text(
            "Back", 60, HEIGHT - 30, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_btn_new_game = arcade.Text(
            "New Game", WIDTH - 70, HEIGHT - 30, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_btn_help = arcade.Text(
            "?", WIDTH - 140, HEIGHT - 30, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )

        # Stone count labels under each pit (dynamic per pit)
        self.txt_pit_counts = []
        for i in range(6):
            px = PITS_START_X + i * PIT_SPACING
            # Player pit count
            self.txt_pit_counts.append(
                arcade.Text("", px, PLAYER_ROW_Y - PIT_RADIUS - 12,
                            arcade.color.WHITE, font_size=12,
                            anchor_x="center", anchor_y="center", bold=True)
            )
        self.txt_ai_pit_counts = []
        for i in range(6):
            px = PITS_START_X + i * PIT_SPACING
            ai_display_index = 5 - i
            self.txt_ai_pit_counts.append(
                arcade.Text("", px, BOARD_CY + 55 - PIT_RADIUS - 12,
                            arcade.color.WHITE, font_size=12,
                            anchor_x="center", anchor_y="center", bold=True)
            )

        # Store count labels (dynamic)
        self.txt_ai_store_count = arcade.Text(
            "", LEFT_STORE_X, STORE_Y,
            arcade.color.WHITE, font_size=24,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_ai_store_label = arcade.Text(
            "AI", LEFT_STORE_X, STORE_Y + STORE_H / 2 + 12,
            arcade.color.LIGHT_GRAY, font_size=11,
            anchor_x="center", anchor_y="center",
        )
        self.txt_player_store_count = arcade.Text(
            "", RIGHT_STORE_X, STORE_Y,
            arcade.color.WHITE, font_size=24,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_player_store_label = arcade.Text(
            "You", RIGHT_STORE_X, STORE_Y - STORE_H / 2 - 12,
            arcade.color.LIGHT_GRAY, font_size=11,
            anchor_x="center", anchor_y="center",
        )

        # Turn indicator (dynamic)
        self.txt_turn = arcade.Text(
            "", WIDTH / 2, 40,
            arcade.color.WHITE, font_size=14,
            anchor_x="center", anchor_y="center",
        )

        # Pit index labels for player (static)
        self.txt_pit_index_labels = []
        for i in range(6):
            px = PITS_START_X + i * PIT_SPACING
            self.txt_pit_index_labels.append(
                arcade.Text(str(i + 1), px, PLAYER_ROW_Y - PIT_RADIUS - 26,
                            arcade.color.LIGHT_GRAY, font_size=10,
                            anchor_x="center", anchor_y="center")
            )

        # Extra turn text (dynamic)
        self.txt_extra_turn = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2,
            arcade.color.YELLOW, font_size=22,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Game over texts (dynamic)
        self.txt_game_over_msg = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 + 25,
            arcade.color.WHITE, font_size=26,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_score = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 - 10,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )
        self.txt_game_over_hint = arcade.Text(
            "Click 'New Game' to play again.",
            WIDTH / 2, HEIGHT / 2 - 40,
            arcade.color.LIGHT_GRAY, font_size=13,
            anchor_x="center", anchor_y="center",
        )

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
        def __init__(self):
            super().__init__()
            self.txt_placeholder = arcade.Text(
                "Menu (placeholder)", WIDTH / 2, HEIGHT / 2,
                arcade.color.WHITE, 20, anchor_x="center")

        def on_draw(self):
            self.clear()
            self.txt_placeholder.draw()

    menu = DummyMenu()
    game = MancalaView(menu)
    window.show_view(game)
    arcade.run()
