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


def icon_asteroids():
    img, d = _new(BLACK)
    # ship
    d.polygon([(60, 80), (50, 60), (60, 65), (70, 60)], fill=WHITE)
    # asteroids
    d.polygon([(20, 30), (35, 20), (45, 30), (40, 45), (25, 45)], outline=GRAY, width=2)
    d.polygon([(75, 40), (90, 35), (95, 50), (85, 55), (70, 50)], outline=GRAY, width=2)
    d.polygon([(30, 80), (40, 75), (45, 85), (35, 95)], outline=GRAY, width=2)
    # bullet
    d.ellipse([58, 48, 62, 52], fill=WHITE)
    _save(img, "asteroids.png")


def icon_liars_dice():
    img, d = _new()
    # dice
    for i, (dx, dy) in enumerate([(25, 35), (55, 30), (85, 40), (40, 70), (70, 65)]):
        d.rectangle([dx, dy, dx + 20, dy + 20], fill=WHITE, outline=BLACK)
        # pips
        d.ellipse([dx + 8, dy + 8, dx + 12, dy + 12], fill=BLACK)
    # question mark for hidden dice
    d.text((45, 10), "?!", fill=YELLOW, font=_font(20))
    _save(img, "liars_dice.png")


def icon_tron():
    img, d = _new(BLACK)
    # trails
    path1 = [(20, 100), (20, 50), (60, 50), (60, 30)]
    path2 = [(100, 20), (100, 70), (50, 70), (50, 90)]
    for i in range(len(path1) - 1):
        d.line([path1[i], path1[i + 1]], fill=(0, 255, 255), width=4)
    for i in range(len(path2) - 1):
        d.line([path2[i], path2[i + 1]], fill=RED, width=4)
    # heads
    d.ellipse([56, 26, 64, 34], fill=(0, 255, 255))
    d.ellipse([46, 86, 54, 94], fill=RED)
    _save(img, "tron.png")


def icon_fifteen_puzzle():
    img, d = _new()
    cell = 24
    gap = 3
    off = 12
    nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0]
    colors = [BLUE, BLUE, BLUE, BLUE, GREEN, GREEN, GREEN, GREEN,
              ORANGE, ORANGE, ORANGE, ORANGE, RED, RED, RED, GRAY]
    small = _font(11)
    for i, n in enumerate(nums):
        r, c = divmod(i, 4)
        x = off + c * (cell + gap)
        y = off + r * (cell + gap)
        if n == 0:
            d.rectangle([x, y, x + cell, y + cell], fill=(40, 40, 40))
        else:
            d.rectangle([x, y, x + cell, y + cell], fill=colors[i], outline=WHITE)
            d.text((x + 5, y + 5), str(n), fill=WHITE, font=small)
    _save(img, "fifteen_puzzle.png")


def icon_peg_solitaire():
    img, d = _new()
    # Draw cross-shaped board with pegs
    valid = set()
    for r in range(7):
        for c in range(7):
            if (r < 2 or r > 4) and (c < 2 or c > 4):
                continue
            valid.add((r, c))
    for r, c in valid:
        x = 15 + c * 14
        y = 12 + r * 14
        if (r, c) == (3, 3):
            d.ellipse([x, y, x + 10, y + 10], outline=GRAY, width=1)
        else:
            d.ellipse([x, y, x + 10, y + 10], fill=BLUE, outline=WHITE)
    _save(img, "peg_solitaire.png")


def icon_breakout():
    img, d = _new(BLACK)
    # bricks
    colors_b = [RED, RED, ORANGE, ORANGE, GREEN, GREEN, YELLOW, YELLOW]
    for row in range(8):
        for col in range(6):
            x = 10 + col * 17
            y = 10 + row * 8
            d.rectangle([x, y, x + 15, y + 6], fill=colors_b[row])
    # paddle
    d.rectangle([40, 100, 80, 106], fill=WHITE)
    # ball
    d.ellipse([58, 90, 64, 96], fill=WHITE)
    _save(img, "breakout.png")


def icon_puzzle_bubble():
    img, d = _new((20, 20, 40))
    # bubbles in hex grid
    colors_pb = [RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE]
    r = 10
    for row in range(4):
        offset = 7 if row % 2 == 1 else 0
        for col in range(5):
            x = 15 + offset + col * 22
            y = 15 + row * 19
            c = colors_pb[(row + col) % len(colors_pb)]
            d.ellipse([x, y, x + r * 2, y + r * 2], fill=c, outline=WHITE)
    # shooter
    d.polygon([(55, 105), (60, 90), (65, 105)], fill=GRAY, outline=WHITE)
    # aim line
    d.line([(60, 90), (45, 60)], fill=WHITE, width=1)
    _save(img, "puzzle_bubble.png")


def icon_tetris_vs():
    img, d = _new(BLACK)
    # Two small boards side by side
    colors_t = [RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE]
    # Left board
    for i in range(6):
        x = 8 + (i % 3) * 12
        y = 60 + (i // 3) * 12
        d.rectangle([x, y, x + 10, y + 10], fill=colors_t[i], outline=(40, 40, 40))
    # Right board
    for i in range(6):
        x = 68 + (i % 3) * 12
        y = 55 + (i // 3) * 12
        d.rectangle([x, y, x + 10, y + 10], fill=colors_t[(i + 3) % 6], outline=(40, 40, 40))
    # VS text
    d.text((42, 35), "VS", fill=RED, font=_font(22))
    # Board borders
    d.rectangle([5, 20, 50, 100], outline=WHITE, width=1)
    d.rectangle([65, 20, 110, 100], outline=WHITE, width=1)
    _save(img, "tetris_vs.png")


def icon_puzzle_bubble_vs():
    img, d = _new((20, 20, 40))
    # Two boards with bubbles
    for bx in [10, 70]:
        for row in range(3):
            offset = 5 if row % 2 == 1 else 0
            for col in range(3):
                x = bx + offset + col * 14
                y = 15 + row * 12
                c = [RED, BLUE, GREEN, YELLOW][((row + col) * 3 + bx) % 4]
                d.ellipse([x, y, x + 10, y + 10], fill=c, outline=WHITE)
    # VS text
    d.text((42, 40), "VS", fill=RED, font=_font(20))
    # Shooters
    d.polygon([(25, 100), (30, 85), (35, 100)], fill=GRAY)
    d.polygon([(85, 100), (90, 85), (95, 100)], fill=GRAY)
    _save(img, "puzzle_bubble_vs.png")


def icon_lights_out():
    img, d = _new(BLACK)
    for r in range(5):
        for c in range(5):
            x, y = 8 + c * 22, 8 + r * 22
            on = (r + c) % 2 == 0
            d.rectangle([x, y, x + 18, y + 18], fill=YELLOW if on else (40, 40, 40), outline=GRAY)
    _save(img, "lights_out.png")

def icon_rush_hour():
    img, d = _new((180, 180, 180))
    for i in range(7):
        d.line([(10, 10 + i * 17), (110, 10 + i * 17)], fill=(120, 120, 120), width=1)
        d.line([(10 + i * 17, 10), (10 + i * 17, 110)], fill=(120, 120, 120), width=1)
    d.rectangle([27, 44, 61, 58], fill=RED)
    d.rectangle([27, 10, 41, 41], fill=BLUE)
    d.rectangle([78, 61, 110, 75], fill=GREEN)
    d.rectangle([110, 48, 115, 58], fill=YELLOW, outline=YELLOW)
    _save(img, "rush_hour.png")

def icon_ricochet_robots():
    img, d = _new((220, 220, 200))
    for i in range(5):
        d.line([(15, 15 + i * 22), (105, 15 + i * 22)], fill=GRAY)
        d.line([(15 + i * 22, 15), (15 + i * 22, 105)], fill=GRAY)
    d.ellipse([20, 20, 32, 32], fill=RED)
    d.ellipse([64, 42, 76, 54], fill=BLUE)
    d.ellipse([42, 86, 54, 98], fill=GREEN)
    d.rectangle([82, 82, 98, 98], outline=RED, width=2)
    _save(img, "ricochet_robots.png")

def icon_towers_of_hanoi():
    img, d = _new()
    base_y = 95
    d.rectangle([10, base_y, 110, base_y + 5], fill=BROWN)
    for px in [30, 60, 90]:
        d.rectangle([px - 2, 30, px + 2, base_y], fill=BROWN)
    widths = [40, 30, 20]
    colors = [RED, GREEN, BLUE]
    for i, (w, c) in enumerate(zip(widths, colors)):
        x = 30 - w // 2
        y = base_y - (i + 1) * 12
        d.rectangle([x, y, x + w, y + 10], fill=c, outline=WHITE)
    _save(img, "towers_of_hanoi.png")

def icon_sokoban():
    img, d = _new((60, 60, 60))
    d.rectangle([20, 20, 100, 100], fill=(80, 80, 80))
    d.rectangle([30, 50, 46, 66], fill=ORANGE, outline=BROWN)
    d.rectangle([60, 30, 76, 46], fill=ORANGE, outline=BROWN)
    d.ellipse([52, 70, 68, 86], outline=RED, width=2)
    d.ellipse([72, 50, 88, 66], outline=RED, width=2)
    d.rectangle([42, 82, 52, 98], fill=BLUE)
    _save(img, "sokoban.png")

def icon_nonograms():
    img, d = _new(WHITE)
    for i in range(6):
        d.line([(30, 30 + i * 15), (105, 30 + i * 15)], fill=GRAY)
        d.line([(30 + i * 15, 30), (30 + i * 15, 105)], fill=GRAY)
    fills = [(0,0),(0,1),(1,0),(2,2),(3,3),(4,4),(1,1),(2,1),(3,2)]
    for r, c in fills:
        d.rectangle([31 + c * 15, 31 + r * 15, 44 + c * 15, 44 + r * 15], fill=BLACK)
    d.text((5, 32), "2", fill=BLACK, font=_font(9))
    d.text((5, 47), "1", fill=BLACK, font=_font(9))
    _save(img, "nonograms.png")

def icon_slitherlink():
    img, d = _new(LIGHT)
    sp = 22
    for r in range(5):
        for c in range(5):
            d.ellipse([12 + c * sp - 2, 12 + r * sp - 2, 12 + c * sp + 2, 12 + r * sp + 2], fill=BLACK)
    d.line([(12, 12), (12 + sp, 12)], fill=BLUE, width=2)
    d.line([(12, 12), (12, 12 + sp)], fill=BLUE, width=2)
    d.line([(12 + sp, 12), (12 + sp, 12 + sp)], fill=BLUE, width=2)
    d.text((18, 16), "3", fill=BLACK, font=_font(12))
    d.text((40, 16), "2", fill=BLACK, font=_font(12))
    _save(img, "slitherlink.png")

def icon_hashi():
    img, d = _new(LIGHT)
    islands = [(25, 25, 3), (75, 25, 2), (25, 75, 4), (75, 75, 1), (50, 50, 2)]
    for x, y, n in islands:
        d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=WHITE, outline=BLACK, width=2)
        d.text((x - 4, y - 6), str(n), fill=BLACK, font=_font(12))
    d.line([(37, 25), (63, 25)], fill=BLACK, width=2)
    d.line([(25, 37), (25, 63)], fill=BLACK, width=2)
    _save(img, "hashi.png")

def icon_hitori():
    img, d = _new(WHITE)
    nums = [[1,2,3],[2,3,1],[3,1,2]]
    for r in range(3):
        for c in range(3):
            x, y = 20 + c * 28, 20 + r * 28
            shaded = (r == 0 and c == 2) or (r == 2 and c == 0)
            d.rectangle([x, y, x + 26, y + 26], fill=BLACK if shaded else WHITE, outline=GRAY)
            if not shaded:
                d.text((x + 7, y + 5), str(nums[r][c]), fill=BLACK, font=_font(14))
    _save(img, "hitori.png")

def icon_nurikabe():
    img, d = _new(LIGHT)
    grid = [[1,0,0,0],[0,0,0,0],[0,0,0,2],[0,0,0,0]]
    for r in range(4):
        for c in range(4):
            x, y = 15 + c * 24, 15 + r * 24
            sea = (r in [1,3] and c in [1,2]) or (r == 2 and c in [0,1])
            d.rectangle([x, y, x + 22, y + 22], fill=BLACK if sea else WHITE, outline=GRAY)
            if grid[r][c] > 0:
                d.text((x + 6, y + 3), str(grid[r][c]), fill=BLACK, font=_font(14))
    _save(img, "nurikabe.png")

def icon_kakuro():
    img, d = _new(WHITE)
    for r in range(4):
        for c in range(4):
            x, y = 15 + c * 24, 15 + r * 24
            if (r == 0 or c == 0) and not (r == 0 and c == 0):
                d.rectangle([x, y, x + 22, y + 22], fill=(50, 50, 50))
                d.line([(x, y), (x + 22, y + 22)], fill=WHITE)
                d.text((x + 12, y + 2), "7", fill=WHITE, font=_font(8))
            elif r == 0 and c == 0:
                d.rectangle([x, y, x + 22, y + 22], fill=BLACK)
            else:
                d.rectangle([x, y, x + 22, y + 22], fill=WHITE, outline=GRAY)
    _save(img, "kakuro.png")

def icon_kenken():
    img, d = _new(WHITE)
    for i in range(5):
        d.line([(15, 15 + i * 22), (103, 15 + i * 22)], fill=BLACK, width=1)
        d.line([(15 + i * 22, 15), (15 + i * 22, 103)], fill=BLACK, width=1)
    d.rectangle([15, 15, 59, 37], outline=BLACK, width=2)
    d.text((17, 16), "6+", fill=BLACK, font=_font(9))
    d.rectangle([59, 15, 103, 37], outline=BLACK, width=2)
    d.text((61, 16), "3-", fill=BLACK, font=_font(9))
    _save(img, "kenken.png")

def icon_flow_free():
    img, d = _new((40, 40, 40))
    for i in range(6):
        d.line([(15, 15 + i * 18), (105, 15 + i * 18)], fill=(60, 60, 60))
        d.line([(15 + i * 18, 15), (15 + i * 18, 105)], fill=(60, 60, 60))
    pairs = [(RED, (24, 24), (78, 78)), (BLUE, (60, 24), (24, 78)), (GREEN, (78, 24), (60, 78))]
    for c, p1, p2 in pairs:
        d.ellipse([p1[0] - 6, p1[1] - 6, p1[0] + 6, p1[1] + 6], fill=c)
        d.ellipse([p2[0] - 6, p2[1] - 6, p2[0] + 6, p2[1] + 6], fill=c)
    _save(img, "flow_free.png")

def icon_bloxorz():
    img, d = _new((100, 130, 160))
    for r in range(4):
        for c in range(5):
            x, y = 10 + c * 22, 30 + r * 18
            d.rectangle([x, y, x + 20, y + 16], fill=(180, 190, 200), outline=(120, 130, 140))
    d.rectangle([32, 48, 54, 64], fill=ORANGE, outline=BROWN, width=2)
    d.rectangle([76, 66, 98, 82], fill=(20, 20, 20), outline=BLACK)
    _save(img, "bloxorz.png")

def icon_laser_maze():
    img, d = _new((30, 30, 50))
    d.rectangle([15, 55, 25, 65], fill=RED)
    d.line([(25, 60), (50, 60)], fill=RED, width=2)
    d.line([(50, 60), (50, 30)], fill=RED, width=2)
    d.line([(50, 30), (90, 30)], fill=RED, width=2)
    d.polygon([(45, 55), (55, 65), (55, 55)], fill=GRAY, outline=WHITE)
    d.polygon([(45, 25), (55, 35), (45, 35)], fill=GRAY, outline=WHITE)
    d.ellipse([85, 25, 95, 35], fill=GREEN)
    _save(img, "laser_maze.png")

def icon_mahjong_solitaire():
    img, d = _new(DARK_GREEN)
    for layer in range(3):
        off = layer * 4
        for r in range(3):
            for c in range(4):
                x = 15 + c * 22 - off
                y = 20 + r * 26 - off
                d.rectangle([x, y, x + 20, y + 24], fill=(240, 230, 200), outline=(100, 80, 60))
                d.text((x + 4, y + 5), str((r * 4 + c) % 9 + 1), fill=BLACK, font=_font(10))
    _save(img, "mahjong_solitaire.png")

def icon_skyscrapers():
    img, d = _new(LIGHT)
    for i in range(5):
        d.line([(25, 25 + i * 18), (97, 25 + i * 18)], fill=BLACK)
        d.line([(25 + i * 18, 25), (25 + i * 18, 97)], fill=BLACK)
    d.text((35, 8), "2", fill=RED, font=_font(10))
    d.text((53, 8), "1", fill=RED, font=_font(10))
    d.text((8, 30), "3", fill=RED, font=_font(10))
    d.text((30, 30), "1", fill=BLACK, font=_font(12))
    d.text((48, 30), "4", fill=BLACK, font=_font(12))
    _save(img, "skyscrapers.png")

def icon_picross():
    img, d = _new(WHITE)
    for i in range(6):
        d.line([(30, 30 + i * 15), (105, 30 + i * 15)], fill=GRAY)
        d.line([(30 + i * 15, 30), (30 + i * 15, 105)], fill=GRAY)
    fills = [(0,2),(1,1),(1,2),(1,3),(2,0),(2,1),(2,2),(2,3),(2,4),(3,2),(4,1),(4,3)]
    for r, c in fills:
        d.rectangle([31 + c * 15, 31 + r * 15, 44 + c * 15, 44 + r * 15], fill=PURPLE)
    d.text((10, 62), "5", fill=BLACK, font=_font(9))
    _save(img, "picross.png")


def icon_gomoku():
    img, d = _new((210, 180, 140))
    for i in range(7):
        d.line([(15, 15 + i * 15), (105, 15 + i * 15)], fill=BLACK, width=1)
        d.line([(15 + i * 15, 15), (15 + i * 15, 105)], fill=BLACK, width=1)
    d.ellipse([25, 25, 39, 39], fill=BLACK)
    d.ellipse([40, 40, 54, 54], fill=WHITE, outline=BLACK)
    d.ellipse([55, 25, 69, 39], fill=BLACK)
    d.ellipse([40, 55, 54, 69], fill=BLACK)
    d.ellipse([25, 40, 39, 54], fill=WHITE, outline=BLACK)
    d.ellipse([70, 40, 84, 54], fill=BLACK)
    _save(img, "gomoku.png")

def icon_go():
    img, d = _new((210, 180, 140))
    for i in range(9):
        d.line([(12, 12 + i * 11), (100, 12 + i * 11)], fill=BLACK, width=1)
        d.line([(12 + i * 11, 12), (12 + i * 11, 100)], fill=BLACK, width=1)
    stones = [(23, 23, BLACK), (34, 34, WHITE, BLACK), (45, 23, BLACK),
              (56, 34, BLACK), (34, 56, WHITE, BLACK), (67, 45, WHITE, BLACK)]
    for s in stones:
        x, y = s[0], s[1]
        fill = s[2]
        outline = s[3] if len(s) > 3 else None
        d.ellipse([x-5, y-5, x+5, y+5], fill=fill, outline=outline)
    _save(img, "go.png")

def icon_chess():
    img, d = _new()
    for r in range(4):
        for c in range(4):
            x, y = 18 + c * 22, 18 + r * 22
            color = WHITE if (r + c) % 2 == 0 else (80, 50, 20)
            d.rectangle([x, y, x + 22, y + 22], fill=color)
    d.text((24, 24), "\u265A", fill=BLACK, font=_font(18))
    d.text((68, 24), "\u265B", fill=BLACK, font=_font(18))
    d.text((24, 68), "\u2654", fill=WHITE, font=_font(18))
    d.text((46, 68), "\u2655", fill=WHITE, font=_font(18))
    _save(img, "chess.png")

def icon_snakes_and_ladders():
    img, d = _new(LIGHT)
    for r in range(5):
        for c in range(5):
            x, y = 10 + c * 20, 10 + r * 20
            d.rectangle([x, y, x + 18, y + 18], fill=WHITE, outline=GRAY)
    # snake
    d.line([(60, 25), (40, 55), (60, 75)], fill=RED, width=3)
    # ladder
    d.line([(25, 80), (25, 30)], fill=BROWN, width=2)
    d.line([(35, 80), (35, 30)], fill=BROWN, width=2)
    for y in [35, 45, 55, 65, 75]:
        d.line([(25, y), (35, y)], fill=BROWN, width=1)
    _save(img, "snakes_and_ladders.png")

def icon_ludo():
    img, d = _new(WHITE)
    d.rectangle([10, 10, 50, 50], fill=RED)
    d.rectangle([70, 10, 110, 50], fill=BLUE)
    d.rectangle([10, 70, 50, 110], fill=GREEN)
    d.rectangle([70, 70, 110, 110], fill=YELLOW)
    d.rectangle([50, 45, 70, 75], fill=WHITE, outline=GRAY)
    for x, y, c in [(25, 25, WHITE), (85, 25, WHITE), (25, 85, WHITE), (85, 85, WHITE)]:
        d.ellipse([x-6, y-6, x+6, y+6], fill=c, outline=BLACK)
    _save(img, "ludo.png")

def icon_yahtzee():
    img, d = _new()
    positions = [(15, 35), (45, 30), (75, 40), (30, 70), (65, 65)]
    pips = [5, 3, 6, 2, 5]
    for (dx, dy), n in zip(positions, pips):
        d.rectangle([dx, dy, dx + 24, dy + 24], fill=WHITE, outline=BLACK, width=2)
        r = 3
        cx, cy = dx + 12, dy + 12
        if n >= 2:
            d.ellipse([dx + 3, dy + 3, dx + 3 + 2*r, dy + 3 + 2*r], fill=BLACK)
            d.ellipse([dx + 24 - 3 - 2*r, dy + 24 - 3 - 2*r, dx + 21, dy + 21], fill=BLACK)
        if n >= 4:
            d.ellipse([dx + 24 - 3 - 2*r, dy + 3, dx + 21, dy + 3 + 2*r], fill=BLACK)
            d.ellipse([dx + 3, dy + 24 - 3 - 2*r, dx + 3 + 2*r, dy + 21], fill=BLACK)
        if n % 2 == 1:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLACK)
        if n == 6:
            d.ellipse([dx + 3, cy - r, dx + 3 + 2*r, cy + r], fill=BLACK)
            d.ellipse([dx + 24 - 3 - 2*r, cy - r, dx + 21, cy + r], fill=BLACK)
    _save(img, "yahtzee.png")


def icon_doodle_jump():
    img, d = _new((245, 245, 220))
    # grid lines (graph paper)
    for i in range(0, 120, 15):
        d.line([(0, i), (120, i)], fill=(220, 220, 200), width=1)
        d.line([(i, 0), (i, 120)], fill=(220, 220, 200), width=1)
    # platforms
    d.rectangle([20, 85, 55, 92], fill=GREEN)
    d.rectangle([60, 55, 95, 62], fill=GREEN)
    d.rectangle([30, 30, 65, 37], fill=BLUE)
    d.rectangle([70, 100, 100, 107], fill=BROWN)
    # doodler
    d.ellipse([35, 40, 50, 55], fill=YELLOW, outline=BLACK)
    d.rectangle([38, 55, 47, 70], fill=GREEN)
    # jump arc
    d.line([(42, 70), (42, 85)], fill=GRAY, width=1)
    _save(img, "doodle_jump.png")

def icon_galaga():
    img, d = _new(BLACK)
    # stars
    for sx, sy in [(10,10),(30,20),(80,15),(50,40),(100,30),(20,90),(90,80)]:
        d.point((sx, sy), fill=WHITE)
    # enemies row 1 (bosses - green)
    for i in range(3):
        x = 30 + i * 25
        d.rectangle([x, 15, x + 18, 28], fill=GREEN, outline=(0, 180, 0))
        d.ellipse([x + 3, 18, x + 8, 23], fill=WHITE)
        d.ellipse([x + 10, 18, x + 15, 23], fill=WHITE)
    # enemies row 2 (butterflies - red)
    for i in range(4):
        x = 22 + i * 22
        d.polygon([(x + 8, 35), (x, 48), (x + 16, 48)], fill=RED)
    # enemies row 3 (bees - blue)
    for i in range(5):
        x = 15 + i * 20
        d.ellipse([x, 55, x + 14, 67], fill=BLUE, outline=(100, 100, 255))
    # player ship
    d.polygon([(55, 100), (60, 85), (65, 100)], fill=(0, 255, 255))
    # bullet
    d.line([(60, 82), (60, 72)], fill=WHITE, width=2)
    _save(img, "galaga.png")

def icon_pacman():
    img, d = _new(BLACK)
    # maze walls (simplified)
    d.rectangle([10, 10, 110, 12], fill=BLUE)
    d.rectangle([10, 108, 110, 110], fill=BLUE)
    d.rectangle([10, 10, 12, 110], fill=BLUE)
    d.rectangle([108, 10, 110, 110], fill=BLUE)
    d.rectangle([30, 30, 50, 45], fill=BLUE)
    d.rectangle([70, 30, 90, 45], fill=BLUE)
    d.rectangle([30, 70, 50, 85], fill=BLUE)
    d.rectangle([70, 70, 90, 85], fill=BLUE)
    # dots
    for x in range(20, 110, 12):
        for y in [55, 60]:
            d.ellipse([x-1, y-1, x+1, y+1], fill=WHITE)
    # power pellet
    d.ellipse([16, 16, 24, 24], fill=WHITE)
    # pac-man (open mouth facing right)
    d.pieslice([35, 50, 55, 70], start=30, end=330, fill=YELLOW)
    # ghosts
    ghost_colors = [RED, (255, 184, 255), (0, 255, 255), ORANGE]
    for i, gc in enumerate(ghost_colors):
        gx = 65 + i * 12
        gy = 90
        d.rectangle([gx, gy, gx + 10, gy + 12], fill=gc)
        d.pieslice([gx, gy - 2, gx + 10, gy + 8], start=180, end=360, fill=gc)
        d.ellipse([gx + 2, gy + 1, gx + 4, gy + 3], fill=WHITE)
        d.ellipse([gx + 6, gy + 1, gx + 8, gy + 3], fill=WHITE)
    _save(img, "pacman.png")


def icon_klondike():
    img, d = _new(DARK_GREEN)
    # 3 tableau columns with cascading cards
    for col in range(3):
        x = 15 + col * 35
        for row in range(col + 1):
            y = 15 + row * 15
            d.rectangle([x, y, x + 25, y + 35], fill=(40, 40, 40) if row < col else WHITE, outline=GRAY)
    # foundation
    d.rectangle([85, 10, 110, 45], outline=GOLD, width=2)
    d.text((90, 18), "A♠", fill=GOLD, font=_font(12))
    _save(img, "klondike.png")

def icon_spider():
    img, d = _new(DARK_GREEN)
    # many columns (10 narrow)
    for col in range(5):
        x = 8 + col * 22
        for row in range(3):
            y = 20 + row * 12
            d.rectangle([x, y, x + 18, y + 28], fill=(40, 40, 40) if row < 2 else WHITE, outline=GRAY)
    # spider web hint
    d.text((35, 75), "K→A", fill=WHITE, font=_font(14))
    _save(img, "spider.png")

def icon_freecell():
    img, d = _new(DARK_GREEN)
    # free cells (top left)
    for i in range(4):
        x = 8 + i * 18
        d.rectangle([x, 8, x + 15, y := 30], fill=(30, 60, 30), outline=WHITE)
    # foundations (top right)
    for i in range(4):
        x = 52 + i * 18
        d.rectangle([x, 8, x + 15, 30], outline=GOLD, width=2)
    # tableau columns
    for col in range(4):
        x = 15 + col * 25
        for row in range(3):
            y = 40 + row * 14
            d.rectangle([x, y, x + 20, y + 28], fill=WHITE, outline=GRAY)
    _save(img, "freecell.png")

def icon_pyramid_card():
    img, d = _new(DARK_GREEN)
    # pyramid shape of cards
    rows = [1, 2, 3, 4]
    for r, count in enumerate(rows):
        for c in range(count):
            x = 60 - count * 14 + c * 28
            y = 10 + r * 20
            d.rectangle([x, y, x + 22, y + 18], fill=WHITE, outline=GRAY)
    d.text((40, 90), "= 13", fill=YELLOW, font=_font(14))
    _save(img, "pyramid.png")

def icon_tripeaks():
    img, d = _new(DARK_GREEN)
    # 3 peaks
    peaks = [20, 55, 90]
    for px in peaks:
        d.rectangle([px, 15, px + 20, 35], fill=(40, 40, 40), outline=GRAY)
        d.rectangle([px - 10, 35, px + 10, 55], fill=(40, 40, 40), outline=GRAY)
        d.rectangle([px + 10, 35, px + 30, 55], fill=WHITE, outline=GRAY)
    # waste pile
    d.rectangle([50, 80, 75, 105], fill=WHITE, outline=GRAY)
    d.text((55, 85), "±1", fill=BLACK, font=_font(12))
    _save(img, "tripeaks.png")


def icon_blackjack():
    img, d = _new(DARK_GREEN)
    # two cards overlapping
    d.rectangle([25, 30, 55, 80], fill=WHITE, outline=GRAY)
    d.text((30, 35), "A", fill=BLACK, font=_font(16))
    d.text((30, 58), "♠", fill=BLACK, font=_font(14))
    d.rectangle([45, 25, 75, 75], fill=WHITE, outline=GRAY)
    d.text((50, 30), "K", fill=RED, font=_font(16))
    d.text((50, 53), "♥", fill=RED, font=_font(14))
    d.text((30, 88), "21", fill=GOLD, font=_font(18))
    _save(img, "blackjack.png")

def icon_poker():
    img, d = _new(DARK_GREEN)
    # 5 community cards
    for i in range(5):
        x = 8 + i * 21
        d.rectangle([x, 45, x + 18, y := 75], fill=WHITE, outline=GRAY)
    # 2 hole cards
    d.rectangle([30, 80, 50, 105], fill=WHITE, outline=GRAY)
    d.rectangle([55, 80, 75, 105], fill=WHITE, outline=GRAY)
    # chips
    d.ellipse([75, 15, 105, 35], fill=RED, outline=WHITE, width=2)
    d.ellipse([65, 10, 95, 30], fill=BLUE, outline=WHITE, width=2)
    d.text((25, 15), "POKER", fill=GOLD, font=_font(14))
    _save(img, "poker.png")

def icon_crazy_eights():
    img, d = _new(BLUE)
    d.rectangle([35, 25, 65, 75], fill=WHITE, outline=BLACK)
    d.text((42, 30), "8", fill=RED, font=_font(28))
    d.text((42, 60), "♦", fill=RED, font=_font(14))
    # wild indicator
    d.text((20, 85), "WILD!", fill=YELLOW, font=_font(14))
    _save(img, "crazy_eights.png")

def icon_go_fish():
    img, d = _new((100, 180, 220))
    # fish
    d.ellipse([30, 40, 80, 75], fill=ORANGE, outline=YELLOW)
    d.polygon([(75, 55), (95, 40), (95, 70)], fill=ORANGE)
    d.ellipse([40, 48, 48, 56], fill=WHITE)
    d.ellipse([42, 50, 46, 54], fill=BLACK)
    # cards
    d.rectangle([15, 80, 35, 105], fill=WHITE, outline=GRAY)
    d.rectangle([40, 80, 60, 105], fill=WHITE, outline=GRAY)
    d.text((20, 15), "Go Fish", fill=WHITE, font=_font(14))
    _save(img, "go_fish.png")

def icon_old_maid():
    img, d = _new(PURPLE)
    # queen card
    d.rectangle([35, 20, 65, 70], fill=WHITE, outline=GRAY)
    d.text((42, 25), "Q", fill=RED, font=_font(22))
    d.text((42, 50), "♥", fill=RED, font=_font(14))
    # X over it
    d.line([(35, 20), (65, 70)], fill=RED, width=3)
    d.line([(65, 20), (35, 70)], fill=RED, width=3)
    d.text((15, 80), "Old Maid", fill=WHITE, font=_font(12))
    _save(img, "old_maid.png")

def icon_war():
    img, d = _new((50, 50, 50))
    # two cards clashing
    d.rectangle([15, 30, 50, 80], fill=WHITE, outline=GRAY)
    d.text((22, 40), "K", fill=BLACK, font=_font(20))
    d.rectangle([60, 25, 95, 75], fill=WHITE, outline=GRAY)
    d.text((67, 35), "A", fill=RED, font=_font(20))
    # vs
    d.text((42, 48), "⚔", fill=GOLD, font=_font(16))
    d.text((30, 90), "WAR!", fill=RED, font=_font(16))
    _save(img, "war.png")

def icon_hearts():
    img, d = _new(DARK_GREEN)
    # large heart
    d.text((25, 20), "♥", fill=RED, font=_font(50))
    # queen of spades small
    d.rectangle([70, 60, 95, 95], fill=WHITE, outline=GRAY)
    d.text((74, 65), "Q♠", fill=BLACK, font=_font(12))
    d.text((15, 90), "-13", fill=RED, font=_font(12))
    _save(img, "hearts.png")

def icon_spades():
    img, d = _new(DARK_GREEN)
    # large spade
    d.text((25, 20), "♠", fill=WHITE, font=_font(50))
    # trump indicator
    d.text((15, 85), "TRUMP", fill=GOLD, font=_font(14))
    # bid number
    d.ellipse([75, 75, 105, 105], fill=BLUE, outline=WHITE)
    d.text((83, 80), "4", fill=WHITE, font=_font(16))
    _save(img, "spades.png")


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
    icon_asteroids()
    icon_liars_dice()
    icon_tron()
    icon_fifteen_puzzle()
    icon_peg_solitaire()
    icon_breakout()
    icon_puzzle_bubble()
    icon_tetris_vs()
    icon_puzzle_bubble_vs()
    icon_lights_out()
    icon_rush_hour()
    icon_ricochet_robots()
    icon_towers_of_hanoi()
    icon_sokoban()
    icon_nonograms()
    icon_slitherlink()
    icon_hashi()
    icon_hitori()
    icon_nurikabe()
    icon_kakuro()
    icon_kenken()
    icon_flow_free()
    icon_bloxorz()
    icon_laser_maze()
    icon_mahjong_solitaire()
    icon_skyscrapers()
    icon_picross()
    icon_gomoku()
    icon_go()
    icon_chess()
    icon_snakes_and_ladders()
    icon_ludo()
    icon_yahtzee()
    icon_doodle_jump()
    icon_galaga()
    icon_pacman()
    icon_klondike()
    icon_spider()
    icon_freecell()
    icon_pyramid_card()
    icon_tripeaks()
    icon_blackjack()
    icon_poker()
    icon_crazy_eights()
    icon_go_fish()
    icon_old_maid()
    icon_war()
    icon_hearts()
    icon_spades()

    print("Generating UI assets...")
    ui_help()
    ui_back()
    ui_new_game()

    print("Done!")


if __name__ == "__main__":
    main()
