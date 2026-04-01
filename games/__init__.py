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
from games.lights_out import LightsOutView
from games.rush_hour import RushHourView
from games.ricochet_robots import RicochetRobotsView
from games.towers_of_hanoi import TowersOfHanoiView
from games.sokoban import SokobanView
from games.nonograms import NonogramsView
from games.slitherlink import SlitherlinkView
from games.hashi import HashiView
from games.hitori import HitoriView
from games.nurikabe import NurikabeView
from games.kakuro import KakuroView
from games.kenken import KenKenView
from games.flow_free import FlowFreeView
from games.bloxorz import BloxorzView
from games.laser_maze import LaserMazeView
from games.mahjong_solitaire import MahjongSolitaireView
from games.skyscrapers import SkyscrapersView
from games.picross import PicrossView
from games.gomoku import GomokuView
from games.go import GoView
from games.chess import ChessView
from games.snakes_and_ladders import SnakesAndLaddersView
from games.ludo import LudoView
from games.yahtzee import YahtzeeView

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
    ("Lights Out", LightsOutView, "lights_out.txt", "lights_out.png"),
    ("Rush Hour", RushHourView, "rush_hour.txt", "rush_hour.png"),
    ("Ricochet Robots", RicochetRobotsView, "ricochet_robots.txt", "ricochet_robots.png"),
    ("Towers of Hanoi", TowersOfHanoiView, "towers_of_hanoi.txt", "towers_of_hanoi.png"),
    ("Sokoban", SokobanView, "sokoban.txt", "sokoban.png"),
    ("Nonograms", NonogramsView, "nonograms.txt", "nonograms.png"),
    ("Slitherlink", SlitherlinkView, "slitherlink.txt", "slitherlink.png"),
    ("Hashi", HashiView, "hashi.txt", "hashi.png"),
    ("Hitori", HitoriView, "hitori.txt", "hitori.png"),
    ("Nurikabe", NurikabeView, "nurikabe.txt", "nurikabe.png"),
    ("Kakuro", KakuroView, "kakuro.txt", "kakuro.png"),
    ("KenKen", KenKenView, "kenken.txt", "kenken.png"),
    ("Flow Free", FlowFreeView, "flow_free.txt", "flow_free.png"),
    ("Bloxorz", BloxorzView, "bloxorz.txt", "bloxorz.png"),
    ("Laser Maze", LaserMazeView, "laser_maze.txt", "laser_maze.png"),
    ("Mahjong Solitaire", MahjongSolitaireView, "mahjong_solitaire.txt", "mahjong_solitaire.png"),
    ("Skyscrapers", SkyscrapersView, "skyscrapers.txt", "skyscrapers.png"),
    ("Picross", PicrossView, "picross.txt", "picross.png"),
    ("Gomoku", GomokuView, "gomoku.txt", "gomoku.png"),
    ("Go", GoView, "go.txt", "go.png"),
    ("Chess", ChessView, "chess.txt", "chess.png"),
    ("Snakes & Ladders", SnakesAndLaddersView, "snakes_and_ladders.txt", "snakes_and_ladders.png"),
    ("Ludo", LudoView, "ludo.txt", "ludo.png"),
    ("Yahtzee", YahtzeeView, "yahtzee.txt", "yahtzee.png"),
]
