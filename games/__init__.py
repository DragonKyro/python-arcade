from games.mastermind import MastermindView
from games.minesweeper import MinesweeperView
from games.twenty48 import Twenty48View
from games.tictactoe import TicTacToeView
from games.rps import RPSView
from games.connect4 import Connect4View
from games.othello import OthelloView
from games.battleship import BattleshipView
from games.dots_boxes import DotsBoxesView
from games.mancala import MancalaView
from games.backgammon import BackgammonView

# Each entry: (display name, view class)
GAME_LIST = [
    ("Mastermind", MastermindView),
    ("Minesweeper", MinesweeperView),
    ("2048", Twenty48View),
    ("Tic-Tac-Toe", TicTacToeView),
    ("Rock Paper Scissors", RPSView),
    ("Connect Four", Connect4View),
    ("Othello", OthelloView),
    ("Battleship", BattleshipView),
    ("Dots and Boxes", DotsBoxesView),
    ("Mancala", MancalaView),
    ("Backgammon", BackgammonView),
]
