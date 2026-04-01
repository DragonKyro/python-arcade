# Python Arcade

A collection of classic games built with the [Python Arcade](https://api.arcade.academy/) library. Includes single-player puzzles, AI-opponent board games, and retro arcade classics, all playable from a single launcher.

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
| Tetris | Arcade | - |
| Space Invaders | Arcade | - |
| Frogger | Arcade | - |
| Flappy Bird | Arcade | - |

## Getting Started

### Requirements
- Python 3.13+
- arcade 3.x

### Install and Run

```bash
pip install -r requirements.txt
python main.py
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
generate_assets.py   Regenerate all assets (requires Pillow)
```

## Adding a New Game

1. Create `games/your_game.py` with a `YourGameView(arcade.View)` class (state + input only, no drawing)
2. Create `renderers/your_game_renderer.py` with a `draw(game)` function for all rendering
3. If AI-based, create `ai/your_game_ai.py` with pure game logic
4. Create `rules/your_game.txt` with game instructions
5. Add an icon: create a function in `generate_assets.py` and run it, or add a 120x120 PNG to `assets/icons/`
6. Register it in `games/__init__.py` by adding to `GAME_LIST` as `(name, ViewClass, "rules.txt", "icon.png")`

The game selection screen auto-populates from the registry. Selecting a game shows its rules first, with a Play button to launch. Each game also has a "?" button to re-read rules mid-game.
