"""
Asset generator — creates PNG icons and sprites for the arcade launcher.
Run once:  python generate_assets.py
Requires Pillow (installed with arcade).
"""

import math
import os
from PIL import Image, ImageDraw, ImageFont

ICON_SIZE = 120
BG = (44, 62, 80)        # dark blue-gray
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
RED = (231, 76, 60)
GREEN = (46, 204, 113)
BLUE = (52, 152, 219)
YELLOW = (241, 196, 15)
ORANGE = (243, 156, 18)
PURPLE = (155, 89, 182)
DARK_GREEN = (39, 174, 96)
BROWN = (139, 90, 43)
LIGHT = (236, 240, 241)
GOLD = (212, 175, 55)

ICONS_DIR = os.path.join("assets", "icons")
UI_DIR = os.path.join("assets", "ui")


def _font(size):
    """Return a truetype font, falling back to default."""
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
        except OSError:
            return ImageFont.load_default()


def _new(bg=BG):
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), bg)
    return img, ImageDraw.Draw(img)


def _save(img, name, folder=ICONS_DIR):
    img.save(os.path.join(folder, name))
    print(f"  {folder}/{name}")


# ── Game Icons ───────────────────────────────────────────────────────

def icon_mastermind():
    img, d = _new()
    colors = [RED, BLUE, GREEN, YELLOW]
    y = 60
    for i, c in enumerate(colors):
        x = 18 + i * 28
        d.ellipse([x, y - 10, x + 20, y + 10], fill=c, outline=WHITE)
    # feedback pegs
    d.ellipse([30, 82, 38, 90], fill=BLACK)
    d.ellipse([44, 82, 52, 90], fill=WHITE)
    d.text((60, 20), "?", fill=WHITE, font=_font(28))
    _save(img, "mastermind.png")


def icon_minesweeper():
    img, d = _new()
    # mine body
    cx, cy, r = 60, 60, 22
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLACK)
    # spikes
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1 = cx + int(r * math.cos(rad))
        y1 = cy + int(r * math.sin(rad))
        x2 = cx + int((r + 10) * math.cos(rad))
        y2 = cy + int((r + 10) * math.sin(rad))
        d.line([(x1, y1), (x2, y2)], fill=BLACK, width=3)
    # glint
    d.ellipse([cx - 8, cy - 10, cx - 2, cy - 4], fill=WHITE)
    _save(img, "minesweeper.png")


def icon_2048():
    img, d = _new((187, 173, 160))
    # tile
    d.rounded_rectangle([20, 25, 100, 95], radius=8, fill=(237, 197, 63))
    d.text((28, 38), "2048", fill=WHITE, font=_font(24))
    _save(img, "twenty48.png")


def icon_tictactoe():
    img, d = _new()
    # grid lines
    for x in [45, 75]:
        d.line([(x, 20), (x, 100)], fill=WHITE, width=2)
    for y in [45, 75]:
        d.line([(20, y), (100, y)], fill=WHITE, width=2)
    # X
    d.line([(24, 24), (40, 40)], fill=RED, width=3)
    d.line([(40, 24), (24, 40)], fill=RED, width=3)
    # O
    d.ellipse([50, 50, 70, 70], outline=BLUE, width=3)
    _save(img, "tictactoe.png")


def icon_rps():
    img, d = _new()
    # rock (circle)
    d.ellipse([10, 40, 45, 75], fill=GRAY, outline=WHITE)
    # paper (rectangle)
    d.rectangle([48, 35, 78, 80], fill=LIGHT, outline=WHITE)
    # scissors (V shape)
    d.line([(85, 35), (95, 65)], fill=RED, width=3)
    d.line([(105, 35), (95, 65)], fill=RED, width=3)
    d.text((20, 10), "RPS", fill=WHITE, font=_font(18))
    _save(img, "rps.png")


def icon_connect4():
    img, d = _new((0, 0, 170))
    # grid of holes
    for row in range(3):
        for col in range(4):
            x = 18 + col * 25
            y = 25 + row * 25
            c = RED if (row == 2 and col < 2) or (row == 1 and col == 0) else YELLOW if (row == 2 and col == 2) else WHITE
            d.ellipse([x, y, x + 18, y + 18], fill=c)
    _save(img, "connect4.png")


def icon_othello():
    img, d = _new(DARK_GREEN)
    # grid
    for i in range(5):
        x = 20 + i * 20
        d.line([(x, 20), (x, 100)], fill=(0, 100, 0), width=1)
        d.line([(20, x), (100, x)], fill=(0, 100, 0), width=1)
    # pieces
    d.ellipse([30, 30, 50, 50], fill=BLACK, outline=GRAY)
    d.ellipse([50, 50, 70, 70], fill=WHITE, outline=GRAY)
    d.ellipse([50, 30, 70, 50], fill=WHITE, outline=GRAY)
    d.ellipse([30, 50, 50, 70], fill=BLACK, outline=GRAY)
    _save(img, "othello.png")


def icon_battleship():
    img, d = _new((52, 73, 94))
    # water waves
    for y in [80, 90]:
        points = [(10, y)]
        for x in range(10, 110, 10):
            points.append((x + 5, y - 4))
            points.append((x + 10, y))
        d.line(points, fill=(100, 150, 200), width=2)
    # ship hull
    d.polygon([(20, 65), (100, 65), (110, 75), (15, 75)], fill=GRAY)
    # tower
    d.rectangle([50, 40, 70, 65], fill=GRAY, outline=WHITE)
    # hits
    d.ellipse([30, 55, 40, 65], fill=RED)
    _save(img, "battleship.png")


def icon_dots_boxes():
    img, d = _new()
    # dots
    for row in range(4):
        for col in range(4):
            x = 22 + col * 26
            y = 22 + row * 26
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=WHITE)
    # some lines
    d.line([(22, 22), (48, 22)], fill=BLUE, width=2)
    d.line([(48, 22), (74, 22)], fill=BLUE, width=2)
    d.line([(22, 22), (22, 48)], fill=BLUE, width=2)
    d.line([(48, 22), (48, 48)], fill=RED, width=2)
    d.line([(22, 48), (48, 48)], fill=RED, width=2)
    # filled box
    d.rectangle([24, 24, 46, 46], fill=(52, 152, 219, 60))
    _save(img, "dots_boxes.png")


def icon_mancala():
    img, d = _new(BROWN)
    # board outline
    d.rounded_rectangle([10, 30, 110, 90], radius=20, outline=GOLD, width=2)
    # stores
    d.rounded_rectangle([12, 35, 30, 85], radius=8, fill=(100, 60, 30))
    d.rounded_rectangle([90, 35, 108, 85], radius=8, fill=(100, 60, 30))
    # pits
    for i in range(4):
        x = 38 + i * 16
        d.ellipse([x, 40, x + 12, 52], fill=(100, 60, 30))
        d.ellipse([x, 68, x + 12, 80], fill=(100, 60, 30))
    _save(img, "mancala.png")


def icon_backgammon():
    img, d = _new((139, 90, 43))
    # triangles
    for i in range(6):
        x = 10 + i * 17
        c = DARK_GREEN if i % 2 == 0 else RED
        d.polygon([(x, 95), (x + 15, 95), (x + 7, 40)], fill=c)
    # checkers
    d.ellipse([14, 78, 30, 92], fill=WHITE, outline=GRAY)
    d.ellipse([48, 78, 64, 92], fill=(60, 40, 20), outline=GRAY)
    _save(img, "backgammon.png")


def icon_nim():
    img, d = _new()
    # rows of stones
    rows = [1, 3, 5, 7]
    for r, count in enumerate(rows):
        y = 20 + r * 24
        total_w = count * 16
        sx = 60 - total_w // 2
        for i in range(count):
            x = sx + i * 16
            d.ellipse([x, y, x + 12, y + 12], fill=GOLD, outline=WHITE)
    _save(img, "nim.png")


def icon_snake():
    img, d = _new()
    # snake body
    segments = [(30, 80), (30, 65), (45, 65), (45, 50), (60, 50), (60, 35),
                (75, 35), (75, 50), (90, 50)]
    for i in range(len(segments) - 1):
        d.line([segments[i], segments[i + 1]], fill=GREEN, width=10)
    # head
    hx, hy = segments[-1]
    d.ellipse([hx - 6, hy - 6, hx + 6, hy + 6], fill=DARK_GREEN)
    # eye
    d.ellipse([hx, hy - 3, hx + 3, hy], fill=WHITE)
    # apple
    d.ellipse([35, 30, 50, 45], fill=RED)
    d.line([(42, 30), (45, 22)], fill=BROWN, width=2)
    _save(img, "snake.png")


def icon_checkers():
    img, d = _new()
    # board squares
    for row in range(4):
        for col in range(4):
            x = 18 + col * 22
            y = 18 + row * 22
            c = (180, 120, 60) if (row + col) % 2 == 0 else (80, 50, 20)
            d.rectangle([x, y, x + 22, y + 22], fill=c)
    # red piece
    d.ellipse([22, 64, 44, 82], fill=RED, outline=WHITE, width=2)
    # black piece
    d.ellipse([64, 24, 86, 42], fill=(30, 30, 30), outline=GRAY, width=2)
    _save(img, "checkers.png")


def icon_wordle():
    img, d = _new()
    # letter tiles
    letters = "WORDLE"
    colors_list = [GREEN, YELLOW, GRAY, GREEN, YELLOW, GREEN]
    for i, (ch, c) in enumerate(zip(letters, colors_list)):
        if i < 3:
            x = 15 + i * 32
            y = 35
        else:
            x = 15 + (i - 3) * 32
            y = 68
        d.rectangle([x, y, x + 28, y + 28], fill=c)
        d.text((x + 6, y + 2), ch, fill=WHITE, font=_font(18))
    _save(img, "wordle.png")


def icon_sudoku():
    img, d = _new(LIGHT)
    # grid
    off = 15
    cell = 10
    for i in range(10):
        w = 2 if i % 3 == 0 else 1
        pos = off + i * cell
        d.line([(pos, off), (pos, off + 90)], fill=BLACK, width=w)
        d.line([(off, pos), (off + 90, pos)], fill=BLACK, width=w)
    # some numbers
    nums = [(0, 0, "5"), (1, 2, "3"), (2, 1, "9"), (4, 4, "7"), (6, 7, "1"), (8, 8, "4")]
    small = _font(9)
    for r, c, n in nums:
        x = off + c * cell + 2
        y = off + r * cell
        d.text((x, y), n, fill=BLACK, font=small)
    _save(img, "sudoku.png")


def icon_pong():
    img, d = _new(BLACK)
    # paddles
    d.rectangle([15, 30, 22, 80], fill=WHITE)
    d.rectangle([98, 40, 105, 90], fill=WHITE)
    # ball
    d.rectangle([55, 55, 63, 63], fill=WHITE)
    # center line
    for y in range(20, 100, 12):
        d.rectangle([58, y, 60, y + 6], fill=GRAY)
    # score
    d.text((30, 10), "3", fill=WHITE, font=_font(16))
    d.text((78, 10), "2", fill=WHITE, font=_font(16))
    _save(img, "pong.png")


def icon_tetris():
    img, d = _new(BLACK)
    # some placed blocks
    colors_t = [RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE]
    blocks = [(0, 4), (1, 4), (2, 4), (2, 3), (0, 3), (1, 3), (0, 2), (3, 4), (3, 3), (3, 2)]
    for i, (col, row) in enumerate(blocks):
        x = 25 + col * 16
        y = 20 + row * 16
        d.rectangle([x, y, x + 14, y + 14], fill=colors_t[i % len(colors_t)], outline=(40, 40, 40))
    # falling piece (T)
    for dx, dy in [(0, 0), (1, 0), (2, 0), (1, -1)]:
        x = 33 + dx * 16
        y = 12 + dy * 16
        d.rectangle([x, y, x + 14, y + 14], fill=PURPLE, outline=(40, 40, 40))
    _save(img, "tetris.png")


def icon_space_invaders():
    img, d = _new(BLACK)
    # aliens (simple pixel art)
    for row in range(3):
        for col in range(5):
            x = 15 + col * 20
            y = 15 + row * 20
            c = GREEN if row == 0 else (100, 200, 255) if row == 1 else YELLOW
            d.rectangle([x, y, x + 14, y + 10], fill=c)
            # eyes
            d.point((x + 3, y + 3), fill=BLACK)
            d.point((x + 10, y + 3), fill=BLACK)
    # player ship
    d.polygon([(55, 95), (65, 85), (75, 95)], fill=GREEN)
    # laser
    d.line([(65, 82), (65, 70)], fill=WHITE, width=2)
    _save(img, "space_invaders.png")


def icon_frogger():
    img, d = _new()
    # road
    d.rectangle([0, 55, 120, 95], fill=(60, 60, 60))
    # lane lines
    for y in [65, 75, 85]:
        for x in range(5, 120, 20):
            d.rectangle([x, y, x + 10, y + 2], fill=YELLOW)
    # car
    d.rectangle([70, 58, 100, 68], fill=RED)
    d.rectangle([20, 78, 55, 88], fill=BLUE)
    # water
    d.rectangle([0, 15, 120, 55], fill=(30, 100, 200))
    # log
    d.rectangle([25, 28, 70, 40], fill=BROWN)
    # frog
    d.ellipse([52, 42, 68, 54], fill=GREEN, outline=DARK_GREEN, width=2)
    # eyes
    d.ellipse([55, 43, 59, 47], fill=WHITE)
    d.ellipse([61, 43, 65, 47], fill=WHITE)
    # grass
    d.rectangle([0, 0, 120, 15], fill=DARK_GREEN)
    d.rectangle([0, 95, 120, 120], fill=DARK_GREEN)
    _save(img, "frogger.png")


def icon_flappy_bird():
    img, d = _new((135, 206, 235))
    # pipes
    d.rectangle([40, 0, 55, 35], fill=GREEN, outline=DARK_GREEN)
    d.rectangle([37, 32, 58, 40], fill=GREEN, outline=DARK_GREEN)
    d.rectangle([40, 80, 55, 120], fill=GREEN, outline=DARK_GREEN)
    d.rectangle([37, 75, 58, 83], fill=GREEN, outline=DARK_GREEN)
    # second pipe pair
    d.rectangle([85, 0, 100, 50], fill=GREEN, outline=DARK_GREEN)
    d.rectangle([82, 47, 103, 55], fill=GREEN, outline=DARK_GREEN)
    d.rectangle([85, 90, 100, 120], fill=GREEN, outline=DARK_GREEN)
    d.rectangle([82, 85, 103, 93], fill=GREEN, outline=DARK_GREEN)
    # bird
    d.ellipse([18, 50, 38, 66], fill=YELLOW, outline=ORANGE)
    # eye
    d.ellipse([30, 52, 36, 58], fill=WHITE)
    d.ellipse([32, 54, 35, 57], fill=BLACK)
    # beak
    d.polygon([(37, 57), (44, 60), (37, 63)], fill=ORANGE)
    # ground
    d.rectangle([0, 108, 120, 120], fill=BROWN)
    _save(img, "flappy_bird.png")


# ── UI Assets ────────────────────────────────────────────────────────

def ui_help():
    """40x40 '?' icon."""
    img = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 38, 38], fill=(52, 73, 94), outline=WHITE, width=2)
    d.text((11, 4), "?", fill=WHITE, font=_font(24))
    _save(img, "help.png", UI_DIR)


def ui_back():
    """40x40 back arrow icon."""
    img = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 38, 38], fill=(52, 73, 94), outline=WHITE, width=2)
    # arrow
    d.polygon([(12, 20), (24, 10), (24, 30)], fill=WHITE)
    d.rectangle([22, 16, 30, 24], fill=WHITE)
    _save(img, "back.png", UI_DIR)


def ui_new_game():
    """40x40 refresh icon."""
    img = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 38, 38], fill=(52, 73, 94), outline=WHITE, width=2)
    # circular arrow (simplified)
    d.arc([10, 10, 30, 30], start=30, end=330, fill=WHITE, width=2)
    d.polygon([(26, 8), (30, 16), (22, 14)], fill=WHITE)
    _save(img, "new_game.png", UI_DIR)


# ── Main ─────────────────────────────────────────────────────────────

def main():
    os.makedirs(ICONS_DIR, exist_ok=True)
    os.makedirs(UI_DIR, exist_ok=True)

    print("Generating game icons...")
    icon_mastermind()
    icon_minesweeper()
    icon_2048()
    icon_tictactoe()
    icon_rps()
    icon_connect4()
    icon_othello()
    icon_battleship()
    icon_dots_boxes()
    icon_mancala()
    icon_backgammon()
    icon_nim()
    icon_snake()
    icon_checkers()
    icon_wordle()
    icon_sudoku()
    icon_pong()
    icon_tetris()
    icon_space_invaders()
    icon_frogger()
    icon_flappy_bird()

    print("Generating UI assets...")
    ui_help()
    ui_back()
    ui_new_game()

    print("Done!")


if __name__ == "__main__":
    main()
