import arcade
import random
import time
from pages.rules import RulesView
from renderers import wordle_renderer
from renderers.wordle_renderer import (
    WIDTH, HEIGHT,
    MAX_GUESSES, WORD_LENGTH,
    GREEN, YELLOW, DARK_GRAY,
    CELL_SIZE, CELL_GAP, GRID_TOP,
    KB_ROWS, KB_KEY_W, KB_KEY_H, KB_KEY_GAP, KB_Y_START,
    KEY_TEXT,
)

# Colors used only in game logic
BG_COLOR = (18, 18, 19)

# Word list (200+ common 5-letter words)
WORDS = [
    "about", "above", "abuse", "actor", "acute", "admit", "adopt", "adult",
    "after", "again", "agent", "agree", "ahead", "alarm", "album", "alert",
    "alien", "align", "alike", "alive", "alley", "allow", "alone", "along",
    "alter", "among", "angel", "anger", "angle", "angry", "ankle", "apart",
    "apple", "apply", "arena", "argue", "arise", "armor", "array", "aside",
    "asset", "avoid", "awake", "award", "aware", "badly", "baker", "basic",
    "basis", "beach", "begun", "being", "below", "bench", "bible", "birth",
    "black", "blade", "blame", "bland", "blank", "blast", "blaze", "bleed",
    "blend", "blind", "block", "blood", "blown", "board", "bonus", "booth",
    "bound", "brain", "brand", "brave", "bread", "break", "breed", "brick",
    "bride", "brief", "bring", "broad", "broke", "brook", "brown", "brush",
    "buddy", "build", "built", "bunch", "burst", "buyer", "cabin", "cable",
    "camel", "candy", "cargo", "carry", "catch", "cause", "cedar", "chain",
    "chair", "chalk", "chaos", "charm", "chase", "cheap", "check", "cheek",
    "cheer", "chess", "chest", "chief", "child", "china", "chunk", "cited",
    "civic", "civil", "claim", "class", "clean", "clear", "climb", "cling",
    "clock", "clone", "close", "cloth", "cloud", "coach", "coast", "color",
    "comet", "comic", "coral", "could", "count", "court", "cover", "crack",
    "craft", "crane", "crash", "crazy", "cream", "crime", "crisp", "cross",
    "crowd", "crown", "crush", "curve", "cycle", "daily", "dance", "death",
    "debug", "decay", "delay", "depot", "depth", "derby", "devil", "diary",
    "dirty", "doubt", "dough", "draft", "drain", "drama", "drank", "drawn",
    "dream", "dress", "dried", "drift", "drink", "drive", "drove", "dying",
    "eager", "eagle", "early", "earth", "eight", "elect", "elite", "email",
    "empty", "enemy", "enjoy", "enter", "entry", "equal", "error", "essay",
    "event", "every", "exact", "exile", "exist", "extra", "faint", "faith",
    "false", "fancy", "fatal", "fault", "feast", "fence", "fewer", "fiber",
    "field", "fifth", "fifty", "fight", "final", "first", "flame", "flash",
    "fleet", "flesh", "float", "flood", "floor", "flour", "fluid", "flush",
    "focus", "force", "forge", "forth", "forum", "found", "frame", "frank",
    "fraud", "fresh", "front", "frost", "fruit", "fully", "funny", "ghost",
    "giant", "given", "glass", "globe", "glory", "going", "grace", "grade",
    "grain", "grand", "grant", "graph", "grasp", "grass", "grave", "great",
    "green", "greet", "grief", "grill", "grind", "gross", "group", "grove",
    "grown", "guard", "guess", "guest", "guide", "guild", "guilt", "happy",
    "harsh", "haven", "heart", "heavy", "hence", "herbs", "hobby", "honey",
    "honor", "horse", "hotel", "house", "human", "humor", "ideal", "image",
    "imply", "index", "inner", "input", "irony", "issue", "ivory", "jewel",
    "joint", "jones", "judge", "juice", "knock", "known", "label", "labor",
    "large", "laser", "later", "laugh", "layer", "learn", "lease", "leave",
    "legal", "lemon", "level", "light", "limit", "linen", "liver", "local",
    "lodge", "logic", "loose", "lover", "lower", "loyal", "lucky", "lunch",
    "magic", "major", "maker", "manor", "maple", "march", "match", "mayor",
    "media", "mercy", "merit", "metal", "meter", "might", "minor", "minus",
    "model", "money", "month", "moral", "motor", "mount", "mouse", "mouth",
    "movie", "music", "naked", "nasty", "naval", "nerve", "never", "night",
    "noble", "noise", "north", "noted", "novel", "nurse", "nylon", "occur",
    "ocean", "offer", "often", "olive", "onset", "opera", "orbit", "order",
    "organ", "other", "ought", "outer", "owned", "owner", "oxide", "ozone",
    "paint", "panel", "panic", "party", "paste", "patch", "pause", "peace",
    "pearl", "penny", "phase", "phone", "photo", "piano", "piece", "pilot",
    "pitch", "pixel", "pizza", "place", "plain", "plane", "plant", "plate",
    "plaza", "plead", "plumb", "plump", "point", "polar", "pound", "power",
    "press", "price", "pride", "prime", "prince","print", "prior", "prize",
    "probe", "proof", "prose", "proud", "prove", "proxy", "pulse", "punch",
    "pupil", "queen", "query", "quest", "queue", "quick", "quiet", "quite",
    "quota", "quote", "radar", "radio", "raise", "rally", "ranch", "range",
    "rapid", "ratio", "reach", "ready", "realm", "rebel", "refer", "reign",
    "relax", "renew", "reply", "rider", "ridge", "rifle", "right", "rigid",
    "rival", "river", "robin", "robot", "rocky", "rouge", "rough", "round",
    "route", "royal", "rugby", "ruler", "rural", "sadly", "saint", "salad",
    "sauce", "scale", "scene", "scope", "score", "sense", "serve", "setup",
    "seven", "shade", "shake", "shall", "shame", "shape", "share", "shark",
    "sharp", "sheep", "sheer", "sheet", "shelf", "shell", "shift", "shine",
    "shirt", "shock", "shoot", "shore", "short", "shout", "sight", "skill",
    "skull", "slave", "sleep", "slice", "slide", "slope", "smart", "smell",
    "smile", "smoke", "snake", "solar", "solid", "solve", "sorry", "sound",
    "south", "space", "spare", "speak", "speed", "spend", "spent", "spill",
    "spine", "spite", "split", "spoke", "spoon", "sport", "spray", "squad",
    "stack", "staff", "stage", "stain", "stake", "stall", "stamp", "stand",
    "stark", "start", "state", "stays", "steam", "steel", "steep", "steer",
    "stern", "stick", "stiff", "still", "stock", "stone", "stood", "store",
    "storm", "story", "stove", "strap", "straw", "strip", "stuck", "study",
    "stuff", "style", "sugar", "suite", "super", "surge", "swamp", "swear",
    "sweep", "sweet", "swept", "swift", "swing", "sword", "swore", "sworn",
    "table", "taken", "taste", "teach", "teeth", "thank", "theme", "there",
    "thick", "thing", "think", "third", "those", "three", "threw", "throw",
    "thumb", "tiger", "tight", "timer", "tired", "title", "today", "token",
    "topic", "total", "touch", "tough", "towel", "tower", "toxic", "trace",
    "track", "trade", "trail", "train", "trait", "trash", "treat", "trend",
    "trial", "tribe", "trick", "tried", "troop", "truck", "truly", "trump",
    "trunk", "trust", "truth", "tumor", "tutor", "twice", "twist", "ultra",
    "uncle", "under", "union", "unite", "unity", "until", "upper", "upset",
    "urban", "usage", "usual", "valid", "value", "vapor", "vault", "venue",
    "verse", "video", "vigor", "virus", "visit", "vital", "vivid", "vocal",
    "voice", "voter", "wages", "waste", "watch", "water", "weave", "weigh",
    "weird", "whale", "wheat", "wheel", "where", "which", "while", "white",
    "whole", "whose", "width", "witch", "woman", "women", "world", "worry",
    "worse", "worst", "worth", "would", "wound", "write", "wrong", "wrote",
    "yacht", "yield", "young", "youth",
]

VALID_GUESSES = set(WORDS)


class WordleView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self._create_texts()
        self.reset_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects for rendering."""
        self.txt_title = arcade.Text(
            "Wordle", WIDTH / 2, HEIGHT - 30, arcade.color.WHITE,
            font_size=28, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_btn_back = arcade.Text(
            "Back", 60, HEIGHT - 30, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_btn_new_game = arcade.Text(
            "New Game", WIDTH - 70, HEIGHT - 30, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_btn_help = arcade.Text(
            "?", WIDTH - 145, HEIGHT - 30, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_message = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 + 40, (0, 0, 0),
            font_size=16, anchor_x="center", anchor_y="center", bold=True,
        )
        # Grid cell letter texts (6 rows x 5 cols)
        self.txt_grid = {}
        for row in range(MAX_GUESSES):
            for col in range(WORD_LENGTH):
                x = WIDTH / 2 + (col - WORD_LENGTH / 2 + 0.5) * (CELL_SIZE + CELL_GAP)
                y = GRID_TOP - row * (CELL_SIZE + CELL_GAP)
                self.txt_grid[(row, col)] = arcade.Text(
                    "", x, y, arcade.color.WHITE,
                    font_size=28, anchor_x="center", anchor_y="center", bold=True,
                )
        # Keyboard key texts (reusable single object)
        self.txt_key = arcade.Text(
            "", 0, 0, KEY_TEXT,
            font_size=14, anchor_x="center", anchor_y="center", bold=True,
        )

    def reset_game(self):
        """Initialize or reset all game state."""
        self.answer = random.choice(WORDS).upper()
        self.guesses = []           # list of submitted 5-letter strings
        self.guess_colors = []      # list of lists of color tuples per guess
        self.current_input = ""
        self.game_over = False
        self.won = False
        self.message = ""
        self.message_time = 0
        self.key_colors = {}        # letter -> best color so far

    def on_show(self):
        arcade.set_background_color(BG_COLOR)

    # ── Drawing ──────────────────────────────────────────────────────

    def on_draw(self):
        self.clear()
        wordle_renderer.draw(self)

    # ── Game Logic ───────────────────────────────────────────────────

    def _evaluate_guess(self, guess):
        """Return list of 5 colors for the guess, handling duplicate letters correctly."""
        colors = [DARK_GRAY] * WORD_LENGTH
        answer_chars = list(self.answer)
        guess_chars = list(guess)

        # First pass: mark greens
        for i in range(WORD_LENGTH):
            if guess_chars[i] == answer_chars[i]:
                colors[i] = GREEN
                answer_chars[i] = None
                guess_chars[i] = None

        # Second pass: mark yellows
        for i in range(WORD_LENGTH):
            if guess_chars[i] is not None and guess_chars[i] in answer_chars:
                colors[i] = YELLOW
                answer_chars[answer_chars.index(guess_chars[i])] = None

        return colors

    def _update_key_colors(self, guess, colors):
        """Update on-screen keyboard colors. Green > Yellow > Gray."""
        priority = {GREEN: 3, YELLOW: 2, DARK_GRAY: 1}
        for letter, color in zip(guess, colors):
            existing = self.key_colors.get(letter)
            if existing is None or priority[color] > priority.get(existing, 0):
                self.key_colors[letter] = color

    def _submit_guess(self):
        if len(self.current_input) != WORD_LENGTH:
            return

        word = self.current_input.lower()
        if word not in VALID_GUESSES:
            self.message = "Not in word list"
            self.message_time = time.time()
            return

        guess = self.current_input.upper()
        colors = self._evaluate_guess(guess)
        self.guesses.append(guess)
        self.guess_colors.append(colors)
        self._update_key_colors(guess, colors)
        self.current_input = ""

        if guess == self.answer:
            self.game_over = True
            self.won = True
            n = len(self.guesses)
            self.message = f"You got it! ({n}/6)"
            self.message_time = time.time()
        elif len(self.guesses) >= MAX_GUESSES:
            self.game_over = True
            self.won = False
            self.message = f"The word was: {self.answer}"
            self.message_time = time.time()

    def _type_letter(self, letter):
        if self.game_over:
            return
        if len(self.current_input) < WORD_LENGTH:
            self.current_input += letter.upper()

    def _backspace(self):
        if self.game_over:
            return
        self.current_input = self.current_input[:-1]

    # ── Input Handling ───────────────────────────────────────────────

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(self.menu_view)
            return

        if key == arcade.key.RETURN or key == arcade.key.NUM_ENTER:
            self._submit_guess()
            return

        if key == arcade.key.BACKSPACE:
            self._backspace()
            return

        # A-Z keys
        if arcade.key.A <= key <= arcade.key.Z:
            letter = chr(key).upper()
            self._type_letter(letter)

    def on_mouse_press(self, x, y, button, modifiers):
        # Back button
        if 15 <= x <= 105 and HEIGHT - 48 <= y <= HEIGHT - 12:
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if WIDTH - 125 <= x <= WIDTH - 15 and HEIGHT - 48 <= y <= HEIGHT - 12:
            self.reset_game()
            return

        # Help button
        if WIDTH - 165 <= x <= WIDTH - 125 and HEIGHT - 50 <= y <= HEIGHT - 10:
            rules_view = RulesView(
                "Wordle", "wordle.txt", None, self.menu_view,
                existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        # On-screen keyboard clicks
        self._handle_keyboard_click(x, y)

    def _handle_keyboard_click(self, mx, my):
        """Check if a virtual keyboard key was clicked."""
        for r, row_letters in enumerate(KB_ROWS):
            row_width = len(row_letters) * (KB_KEY_W + KB_KEY_GAP) - KB_KEY_GAP
            if r == 2:
                row_width += 2 * (KB_KEY_W * 1.5 + KB_KEY_GAP)
            start_x = WIDTH / 2 - row_width / 2 + KB_KEY_W / 2
            y = KB_Y_START - r * (KB_KEY_H + KB_KEY_GAP)

            if r == 2:
                # Check ENTER key
                enter_w = KB_KEY_W * 1.5
                ex = start_x
                if (ex - enter_w / 2 <= mx <= ex + enter_w / 2 and
                        y - KB_KEY_H / 2 <= my <= y + KB_KEY_H / 2):
                    self._submit_guess()
                    return
                start_x += enter_w + KB_KEY_GAP

            for i, letter in enumerate(row_letters):
                kx = start_x + i * (KB_KEY_W + KB_KEY_GAP)
                if (kx - KB_KEY_W / 2 <= mx <= kx + KB_KEY_W / 2 and
                        y - KB_KEY_H / 2 <= my <= y + KB_KEY_H / 2):
                    self._type_letter(letter)
                    return

            if r == 2:
                # Check BACK/DEL key
                back_w = KB_KEY_W * 1.5
                bx = start_x + len(row_letters) * (KB_KEY_W + KB_KEY_GAP)
                if (bx - back_w / 2 <= mx <= bx + back_w / 2 and
                        y - KB_KEY_H / 2 <= my <= y + KB_KEY_H / 2):
                    self._backspace()
                    return
