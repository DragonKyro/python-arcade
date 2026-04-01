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
from games.nim import NimView
from games.snake import SnakeView
from games.checkers import CheckersView
from games.wordle import WordleView
from games.sudoku import SudokuView

# Each entry: (display name, view class, rules filename)
GAME_LIST = [
    ("Mastermind", MastermindView, "mastermind.txt"),
    ("Minesweeper", MinesweeperView, "minesweeper.txt"),
    ("2048", Twenty48View, "twenty48.txt"),
    ("Tic-Tac-Toe", TicTacToeView, "tictactoe.txt"),
    ("Rock Paper Scissors", RPSView, "rps.txt"),
    ("Connect Four", Connect4View, "connect4.txt"),
    ("Othello", OthelloView, "othello.txt"),
    ("Battleship", BattleshipView, "battleship.txt"),
    ("Dots and Boxes", DotsBoxesView, "dots_boxes.txt"),
    ("Mancala", MancalaView, "mancala.txt"),
    ("Backgammon", BackgammonView, "backgammon.txt"),
    ("Nim", NimView, "nim.txt"),
    ("Snake", SnakeView, "snake.txt"),
    ("Checkers", CheckersView, "checkers.txt"),
    ("Wordle", WordleView, "wordle.txt"),
    ("Sudoku", SudokuView, "sudoku.txt"),
]
