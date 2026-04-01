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
from games.pong import PongView
from games.tetris import TetrisView
from games.space_invaders import SpaceInvadersView
from games.frogger import FroggerView
from games.flappy_bird import FlappyBirdView
from games.asteroids import AsteroidsView
from games.liars_dice import LiarsDiceView
from games.tron import TronView
from games.fifteen_puzzle import FifteenPuzzleView
from games.peg_solitaire import PegSolitaireView
from games.breakout import BreakoutView
from games.puzzle_bubble import PuzzleBubbleView
from games.tetris_vs import TetrisVSView
from games.puzzle_bubble_vs import PuzzleBubbleVSView

# Each entry: (display name, view class, rules filename, icon filename)
GAME_LIST = [
    ("Mastermind", MastermindView, "mastermind.txt", "mastermind.png"),
    ("Minesweeper", MinesweeperView, "minesweeper.txt", "minesweeper.png"),
    ("2048", Twenty48View, "twenty48.txt", "twenty48.png"),
    ("Tic-Tac-Toe", TicTacToeView, "tictactoe.txt", "tictactoe.png"),
    ("Rock Paper Scissors", RPSView, "rps.txt", "rps.png"),
    ("Connect Four", Connect4View, "connect4.txt", "connect4.png"),
    ("Othello", OthelloView, "othello.txt", "othello.png"),
    ("Battleship", BattleshipView, "battleship.txt", "battleship.png"),
    ("Dots and Boxes", DotsBoxesView, "dots_boxes.txt", "dots_boxes.png"),
    ("Mancala", MancalaView, "mancala.txt", "mancala.png"),
    ("Backgammon", BackgammonView, "backgammon.txt", "backgammon.png"),
    ("Nim", NimView, "nim.txt", "nim.png"),
    ("Snake", SnakeView, "snake.txt", "snake.png"),
    ("Checkers", CheckersView, "checkers.txt", "checkers.png"),
    ("Wordle", WordleView, "wordle.txt", "wordle.png"),
    ("Sudoku", SudokuView, "sudoku.txt", "sudoku.png"),
    ("Pong", PongView, "pong.txt", "pong.png"),
    ("Tetris", TetrisView, "tetris.txt", "tetris.png"),
    ("Space Invaders", SpaceInvadersView, "space_invaders.txt", "space_invaders.png"),
    ("Frogger", FroggerView, "frogger.txt", "frogger.png"),
    ("Flappy Bird", FlappyBirdView, "flappy_bird.txt", "flappy_bird.png"),
    ("Asteroids", AsteroidsView, "asteroids.txt", "asteroids.png"),
    ("Liar's Dice", LiarsDiceView, "liars_dice.txt", "liars_dice.png"),
    ("Tron", TronView, "tron.txt", "tron.png"),
    ("15 Puzzle", FifteenPuzzleView, "fifteen_puzzle.txt", "fifteen_puzzle.png"),
    ("Peg Solitaire", PegSolitaireView, "peg_solitaire.txt", "peg_solitaire.png"),
    ("Breakout", BreakoutView, "breakout.txt", "breakout.png"),
    ("Puzzle Bubble", PuzzleBubbleView, "puzzle_bubble.txt", "puzzle_bubble.png"),
    ("Tetris VS", TetrisVSView, "tetris_vs.txt", "tetris_vs.png"),
    ("Puzzle Bubble VS", PuzzleBubbleVSView, "puzzle_bubble_vs.txt", "puzzle_bubble_vs.png"),
]
