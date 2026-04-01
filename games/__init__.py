from games.mastermind import MastermindView
from games.minesweeper import MinesweeperView
from games.twenty48 import Twenty48View

# Each entry: (display name, view class)
GAME_LIST = [
    ("Mastermind", MastermindView),
    ("Minesweeper", MinesweeperView),
    ("2048", Twenty48View),
]
