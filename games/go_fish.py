"""
Go Fish -- multiplayer card game with 1-3 AI opponents.

Ask opponents for a rank you hold.  If they have it, they give all matching
cards.  Otherwise, "Go Fish!" and draw from the stock.  Collect books of 4.
"""

import random

import arcade
from pages.rules import RulesView
from ai.go_fish_ai import GoFishAI
from renderers.go_fish_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT,
    HAND_Y, HAND_OVERLAP,
    STOCK_X, STOCK_Y,
    AI_POSITIONS,
    BUTTON_W, BUTTON_H,
    SCALE,
)
from utils.card import (
    create_deck, point_in_card,
    CARD_WIDTH, CARD_HEIGHT, RANKS,
)

CARD_W = CARD_WIDTH * SCALE
CARD_H = CARD_HEIGHT * SCALE

# Phases
PHASE_SETUP = "setup"
PHASE_SELECT_OPPONENT = "select_opponent"
PHASE_SELECT_RANK = "select_rank"
PHASE_RESULT = "result"
PHASE_AI_TURN = "ai_turn"
PHASE_GAME_OVER = "game_over"


class GoFishView(arcade.View):
    """Arcade View for Go Fish."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view

        # Setup
        self.phase = PHASE_SETUP
        self.pending_num_ai = 0

        # Game state
        self.players = []           # {"name", "hand", "books", "ai"}
        self.stock = []
        self.current_player = 0
        self.selected_opponent = -1
        self.selected_card_index = -1
        self.result_timer = 0.0
        self.ai_timer = 0.0
        self.go_again = False       # whether current player gets another turn

        # Setup buttons
        self.setup_buttons = []
        for i in range(3):
            bx = WIDTH // 2 - 80 + i * 80
            by = HEIGHT // 2 + 20
            self.setup_buttons.append((bx, by, 60, 44))

        self._create_texts()

    # ------------------------------------------------------------------ texts

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
            font_size=16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_title = arcade.Text(
            "Go Fish", WIDTH // 2, bar_y, arcade.color.WHITE,
            font_size=20, anchor_x="center", anchor_y="center", bold=True,
        )

        # Setup
        self.txt_setup_prompt = arcade.Text(
            "Choose number of AI opponents:", WIDTH // 2, HEIGHT // 2 + 80,
            arcade.color.WHITE, 20, anchor_x="center", anchor_y="center",
        )
        self.txt_setup_labels = []
        for i in range(3):
            bx = WIDTH // 2 - 80 + i * 80
            by = HEIGHT // 2 + 20
            self.txt_setup_labels.append(
                arcade.Text(
                    str(i + 1), bx, by, arcade.color.WHITE, 18,
                    anchor_x="center", anchor_y="center", bold=True,
                )
            )
        self.txt_start_btn = arcade.Text(
            "Start Game", WIDTH // 2, HEIGHT // 2 - 60,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", bold=True,
        )

        # In-game
        self.txt_stock_count = arcade.Text(
            "", STOCK_X, STOCK_Y - CARD_H / 2 - 12,
            arcade.color.LIGHT_GRAY, 11, anchor_x="center", anchor_y="center",
        )
        self.txt_status = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 50,
            arcade.color.WHITE, 14, anchor_x="center", anchor_y="center",
        )

        # Books
        self.txt_books_label = arcade.Text(
            "Books", 60, HEIGHT // 2 + 80,
            arcade.color.WHITE, 14, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_book_counts = []
        for i in range(4):
            self.txt_book_counts.append(
                arcade.Text(
                    "", 60, HEIGHT // 2 + 60 - i * 18,
                    arcade.color.LIGHT_GRAY, 11, anchor_x="center", anchor_y="center",
                )
            )

        # AI names / counts
        self.txt_ai_names = []
        self.txt_ai_counts = []
        for i in range(3):
            self.txt_ai_names.append(
                arcade.Text(
                    "", 0, 0, arcade.color.WHITE, 13,
                    anchor_x="center", anchor_y="center", bold=True,
                )
            )
            self.txt_ai_counts.append(
                arcade.Text(
                    "", 0, 0, arcade.color.LIGHT_GRAY, 11,
                    anchor_x="center", anchor_y="center",
                )
            )

        # Game over
        self.txt_game_over_msg = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 40,
            arcade.color.WHITE, 36, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_score = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 - 10,
            arcade.color.LIGHT_GRAY, 18, anchor_x="center", anchor_y="center",
        )
        self.txt_game_over_hint = arcade.Text(
            "Click 'New Game' to play again",
            WIDTH // 2, HEIGHT // 2 - 50,
            arcade.color.LIGHT_GRAY, 14, anchor_x="center", anchor_y="center",
        )

    # ------------------------------------------------------------------ game init

    def _start_game(self):
        num_ai = self.pending_num_ai
        total = 1 + num_ai
        cards_each = 7 if total < 4 else 5

        deck = create_deck(shuffled=True)

        self.players = []
        self.players.append({"name": "You", "hand": [], "books": [], "ai": None})
        for i in range(num_ai):
            ai = GoFishAI()
            self.players.append({
                "name": f"AI {i + 1}",
                "hand": [],
                "books": [],
                "ai": ai,
            })
            self.txt_ai_names[i].text = f"AI {i + 1}"

        # Deal
        idx = 0
        for p in self.players:
            for _ in range(cards_each):
                p["hand"].append(deck[idx])
                idx += 1

        self.stock = deck[idx:]
        for c in self.stock:
            c.face_up = False

        self.current_player = 0
        self.selected_opponent = -1
        self.selected_card_index = -1
        self.go_again = False
        self.phase = PHASE_SELECT_OPPONENT

        # Check for immediate books
        for i in range(len(self.players)):
            self._check_books(i)

        self._update_status("Your turn -- click an opponent to ask.")
        self._update_displays()

    def _update_displays(self):
        self.txt_stock_count.text = f"Ocean: {len(self.stock)}"

    def _update_status(self, msg):
        self.txt_status.text = msg

    # ------------------------------------------------------------------ logic

    def _check_books(self, player_idx):
        """Check if player has 4 of any rank and remove them as a book."""
        player = self.players[player_idx]
        hand = player["hand"]
        rank_counts = {}
        for c in hand:
            rank_counts[c.rank] = rank_counts.get(c.rank, 0) + 1

        for rank, count in list(rank_counts.items()):
            if count >= 4:
                player["books"].append(rank)
                player["hand"] = [c for c in player["hand"] if c.rank != rank]
                # Notify AIs
                for p in self.players:
                    if p["ai"]:
                        p["ai"].observe_book(player_idx, rank)

    def _all_books_done(self):
        """Check if all 13 books are collected."""
        total = sum(len(p["books"]) for p in self.players)
        return total >= 13

    def _is_game_over(self):
        if self._all_books_done():
            return True
        # Stock empty and someone has no cards
        if not self.stock:
            for p in self.players:
                if not p["hand"]:
                    return True
        return False

    def _end_game(self):
        self.phase = PHASE_GAME_OVER
        # Find winner (most books)
        best = -1
        winner_idx = -1
        for i, p in enumerate(self.players):
            if len(p["books"]) > best:
                best = len(p["books"])
                winner_idx = i

        scores = ", ".join(
            f"{p['name']}: {len(p['books'])}" for p in self.players
        )
        if winner_idx == 0:
            self.txt_game_over_msg.text = "You Win!"
            self.txt_game_over_msg.color = arcade.color.GOLD
        else:
            self.txt_game_over_msg.text = f"{self.players[winner_idx]['name']} Wins!"
            self.txt_game_over_msg.color = arcade.color.RED
        self.txt_game_over_score.text = scores

    def _ask_for_rank(self, asker_idx, target_idx, rank):
        """
        Player *asker_idx* asks *target_idx* for all cards of *rank*.
        Returns (cards_given: list, go_fish: bool).
        """
        target = self.players[target_idx]
        given = [c for c in target["hand"] if c.rank == rank]
        target["hand"] = [c for c in target["hand"] if c.rank != rank]

        # Notify AIs of the ask
        for p in self.players:
            if p["ai"]:
                p["ai"].observe_ask(asker_idx, rank)

        if given:
            self.players[asker_idx]["hand"].extend(given)
            self._check_books(asker_idx)
            return given, False
        else:
            return [], True

    def _go_fish(self, player_idx, asked_rank=None):
        """Draw from stock. Returns drawn card or None."""
        if not self.stock:
            return None
        card = self.stock.pop()
        card.face_up = False
        self.players[player_idx]["hand"].append(card)
        self._check_books(player_idx)
        # If drawn card matches asked rank, go again
        if asked_rank and card.rank == asked_rank:
            return card  # signal to go again
        return card

    def _active_opponents(self, player_idx):
        """Indices of other players who still have cards."""
        return [
            i for i in range(len(self.players))
            if i != player_idx and self.players[i]["hand"]
        ]

    def _next_turn(self):
        if self._is_game_over():
            self._end_game()
            return

        if self.go_again:
            self.go_again = False
            # Same player goes again
        else:
            self.current_player = (self.current_player + 1) % len(self.players)

        # If current player has no cards, try to draw or skip
        player = self.players[self.current_player]
        if not player["hand"]:
            if self.stock:
                card = self.stock.pop()
                card.face_up = False
                player["hand"].append(card)
            else:
                # Skip to next player that has cards
                for _ in range(len(self.players)):
                    self.current_player = (self.current_player + 1) % len(self.players)
                    if self.players[self.current_player]["hand"]:
                        break
                else:
                    self._end_game()
                    return

        self.ai_timer = 0.0
        self.selected_opponent = -1
        self.selected_card_index = -1

        if self.current_player == 0:
            self.phase = PHASE_SELECT_OPPONENT
            self._update_status("Your turn -- click an opponent to ask.")
        else:
            self.phase = PHASE_AI_TURN
            name = self.players[self.current_player]["name"]
            self._update_status(f"{name} is thinking...")
        self._update_displays()

    # ------------------------------------------------------------------ hit test

    def _in_rect(self, x, y, cx, cy, w, h):
        return cx - w / 2 <= x <= cx + w / 2 and cy - h / 2 <= y <= cy + h / 2

    def _hand_card_at(self, px, py):
        hand = self.players[0]["hand"]
        if not hand:
            return -1
        total_w = CARD_W + (len(hand) - 1) * HAND_OVERLAP
        start_x = WIDTH / 2 - total_w / 2 + CARD_W / 2
        for i in range(len(hand) - 1, -1, -1):
            cx = start_x + i * HAND_OVERLAP
            if point_in_card(px, py, cx, HAND_Y, SCALE):
                return i
        return -1

    def _ai_area_at(self, px, py):
        """Return player index (1-based) if clicking on an AI area, else -1."""
        for ai_idx in range(len(self.players) - 1):
            if ai_idx >= len(AI_POSITIONS):
                break
            ppx, ppy = AI_POSITIONS[ai_idx]
            if self._in_rect(px, py, ppx, ppy, 160, 90):
                return ai_idx + 1
        return -1

    # ------------------------------------------------------------------ callbacks

    def on_draw(self):
        self.clear()
        from renderers import go_fish_renderer
        go_fish_renderer.draw(self)

    def on_update(self, delta_time):
        if self.phase == PHASE_RESULT:
            self.result_timer += delta_time
            if self.result_timer >= 1.5:
                self._next_turn()
            return

        if self.phase == PHASE_AI_TURN:
            self.ai_timer += delta_time
            if self.ai_timer >= 0.8:
                self._do_ai_turn()

    def _do_ai_turn(self):
        p = self.players[self.current_player]
        ai = p["ai"]
        if ai is None or not p["hand"]:
            self._next_turn()
            return

        active_opps = self._active_opponents(self.current_player)
        if not active_opps:
            self._next_turn()
            return

        target_idx, rank = ai.choose_target_and_rank(
            self.current_player, p["hand"], len(self.players), active_opps,
        )

        # Ensure target is valid
        if target_idx not in active_opps:
            target_idx = active_opps[0]
        # Ensure we actually hold this rank
        held_ranks = set(c.rank for c in p["hand"])
        if rank not in held_ranks:
            rank = list(held_ranks)[0]

        target_name = self.players[target_idx]["name"]
        given, go_fish = self._ask_for_rank(self.current_player, target_idx, rank)

        rank_display = rank.upper() if rank in ("a", "j", "q", "k") else rank

        if given:
            count = len(given)
            self._update_status(
                f"{p['name']} asks {target_name} for {rank_display}s "
                f"and gets {count}!"
            )
            self.go_again = True
        else:
            drawn = self._go_fish(self.current_player, asked_rank=rank)
            if drawn and drawn.rank == rank:
                self._update_status(
                    f"{p['name']} asks {target_name} for {rank_display}s -- "
                    f"Go Fish! Drew the right card!"
                )
                self.go_again = True
            else:
                self._update_status(
                    f"{p['name']} asks {target_name} for {rank_display}s -- "
                    f"Go Fish!"
                )
                self.go_again = False

        self._update_displays()
        self.phase = PHASE_RESULT
        self.result_timer = 0.0

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        # Top bar
        if self._in_rect(x, y, 55, bar_y, 90, 35):
            self.window.show_view(self.menu_view)
            return
        if self._in_rect(x, y, WIDTH - 65, bar_y, 110, 35):
            self.phase = PHASE_SETUP
            self.pending_num_ai = 0
            return
        if self._in_rect(x, y, WIDTH - 135, bar_y, 40, 40):
            rules_view = RulesView(
                "Go Fish", "go_fish.txt", None,
                self.menu_view, existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        if self.phase == PHASE_SETUP:
            self._handle_setup_click(x, y)
        elif self.phase == PHASE_SELECT_OPPONENT:
            self._handle_select_opponent(x, y)
        elif self.phase == PHASE_SELECT_RANK:
            self._handle_select_rank(x, y)

    def _handle_setup_click(self, x, y):
        for i, (bx, by, bw, bh) in enumerate(self.setup_buttons):
            if self._in_rect(x, y, bx, by, bw, bh):
                self.pending_num_ai = i + 1
                return
        if self.pending_num_ai > 0:
            sx, sy = WIDTH // 2, HEIGHT // 2 - 60
            if self._in_rect(x, y, sx, sy, 140, 44):
                self._start_game()

    def _handle_select_opponent(self, x, y):
        target = self._ai_area_at(x, y)
        if target > 0 and self.players[target]["hand"]:
            self.selected_opponent = target
            self.phase = PHASE_SELECT_RANK
            name = self.players[target]["name"]
            self._update_status(f"Asking {name} -- now click a card to choose its rank.")

    def _handle_select_rank(self, x, y):
        # Allow changing opponent
        target = self._ai_area_at(x, y)
        if target > 0 and self.players[target]["hand"]:
            self.selected_opponent = target
            name = self.players[target]["name"]
            self._update_status(f"Asking {name} -- now click a card to choose its rank.")
            return

        idx = self._hand_card_at(x, y)
        if idx < 0:
            return

        card = self.players[0]["hand"][idx]
        self.selected_card_index = idx
        rank = card.rank
        rank_display = rank.upper() if rank in ("a", "j", "q", "k") else rank
        target_name = self.players[self.selected_opponent]["name"]

        given, go_fish = self._ask_for_rank(0, self.selected_opponent, rank)

        if given:
            count = len(given)
            self._update_status(
                f"You ask {target_name} for {rank_display}s and get {count}!"
            )
            self.go_again = True
        else:
            drawn = self._go_fish(0, asked_rank=rank)
            if drawn and drawn.rank == rank:
                self._update_status(
                    f"Go Fish! You drew a {rank_display} -- go again!"
                )
                self.go_again = True
            else:
                self._update_status(f"Go Fish! No {rank_display}s there.")
                self.go_again = False

        self._update_displays()
        self.phase = PHASE_RESULT
        self.result_timer = 0.0
        self.selected_card_index = -1
