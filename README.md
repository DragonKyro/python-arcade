# Python Arcade

A collection of 55 classic games built with the [Python Arcade](https://api.arcade.academy/) library. Includes single-player puzzles, AI-opponent board games, retro arcade classics, multiplayer party games, and VS modes — all playable from a single launcher.

## Games

| Game | Type | AI |
|------|------|----|
| Mastermind | Code-breaking puzzle | - |
| Minesweeper | Mine grid | - |
| 2048 | Tile sliding | - |
| Tic-Tac-Toe | Board game | Minimax |
| Rock Paper Scissors | Hand game | Frequency analysis |
| Connect Four | Board game | Minimax + alpha-beta |
| Othello | Board game | Minimax + alpha-beta |
| Battleship | Strategy | Hunt/target |
| Dots and Boxes | Territory | Greedy |
| Mancala | Seed sowing | Minimax + alpha-beta |
| Backgammon | Board game | Heuristic evaluation |
| Nim | Strategy | Optimal (XOR) |
| Snake | Arcade | - |
| Checkers | Board game | Minimax + alpha-beta |
| Wordle | Word puzzle | - |
| Sudoku | Number puzzle | - |
| Pong | Arcade | Difficulty-scaled |
| Tetris | Arcade (+ VS AI) | Placement evaluation |
| Space Invaders | Arcade | - |
| Frogger | Arcade | - |
| Flappy Bird | Arcade | - |
| Asteroids | Arcade | - |
| Liar's Dice | Dice (1-4 AI) | Probability-based |
| Tron | Arcade (1-3 AI) | Flood-fill |
| 15 Puzzle | Sliding puzzle | - |
| Peg Solitaire | Peg jumping | - |
| Breakout | Arcade | - |
| Puzzle Bubble | Arcade (+ VS AI) | Target evaluation |
| Lights Out | Logic puzzle | - |
| Rush Hour | Sliding puzzle | - |
| Ricochet Robots | Sliding puzzle | - |
| Towers of Hanoi | Logic puzzle | - |
| Sokoban | Push puzzle | - |
| Nonograms | Grid puzzle | - |
| Slitherlink | Loop puzzle | - |
| Hashi | Bridge puzzle | - |
| Hitori | Shading puzzle | - |
| Nurikabe | Island puzzle | - |
| Kakuro | Number puzzle | - |
| KenKen | Cage puzzle | - |
| Flow Free | Path puzzle | - |
| Bloxorz | Block rolling | - |
| Laser Maze | Reflection puzzle | - |
| Mahjong Solitaire | Tile matching | - |
| Skyscrapers | Visibility puzzle | - |
| Picross | Grid puzzle | - |
| Gomoku | Board game | Minimax + alpha-beta |
| Go (9x9) | Board game | Monte Carlo playouts |
| Chess | Board game | Minimax + piece-square tables |
| Snakes & Ladders | Party (2-6) | Auto-roll |
| Ludo | Party (2-4) | Heuristic |
| Yahtzee | Dice (1-4) | Expected value |
| Doodle Jump | Arcade | - |
| Galaga | Arcade | Per-enemy type AI |
| Pac-Man | Arcade | 4 unique ghost AIs |

## Getting Started

### Requirements
- Python 3.13+
- arcade 3.x

### Install and Run

```bash
pip install -r requirements.txt
python main.py
```

### Run Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Project Structure

```
main.py              Entry point
pages/               UI screens (home menu, game selection, rules)
  components.py      Shared UI components (Button)
  rules.py           Rules/instructions view
games/               Game state, input, and logic (no drawing code)
renderers/           All rendering code (one *_renderer.py per game)
ai/                  AI logic (pure Python, no UI dependencies)
rules/               Game rules text files
assets/              Generated PNG icons and sprites
  icons/             Game selection icons (120x120)
  ui/                Shared UI icons
tests/               Test suite (pytest)
  ai/                AI module unit tests
  games/             Game logic tests
  integration/       Full game flow simulations
generate_assets.py   Regenerate all assets (requires Pillow)
```

## Adding a New Game

1. Create `games/your_game.py` with a `YourGameView(arcade.View)` class (state + input only, no drawing)
2. Create `renderers/your_game_renderer.py` with a `draw(game)` function for all rendering
3. If AI-based, create `ai/your_game_ai.py` with pure game logic
4. Create `rules/your_game.txt` with game instructions
5. Add an icon: create a function in `generate_assets.py` and run it, or add a 120x120 PNG to `assets/icons/`
6. Register it in `games/__init__.py` by adding to `GAME_LIST` as `(name, ViewClass, "rules.txt", "icon.png")`
7. Add tests in `tests/ai/` and/or `tests/games/`

The game selection screen auto-populates from the registry. Selecting a game shows its rules first, with a Play button to launch. Each game also has a "?" button to re-read rules mid-game.
