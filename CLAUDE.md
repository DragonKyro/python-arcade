# Python Arcade Game Collection

## Project Overview
A collection of 55 games built with the `arcade` library (3.x). Includes single-player puzzles, AI-opponent board games, retro arcade classics, multiplayer party games, and VS modes.

## Architecture
- `game_launcher.py` — minimal entry point, creates window and shows HomeView
- `pages/` — UI views (HomeView, GamesView, RulesView) and shared components (Button)
- `games/` — game state, input handling, and logic only (no drawing code)
- `renderers/` — all drawing/rendering code, one module per game (`{game}_renderer.py`)
- `ai/` — pure Python AI logic (no arcade imports), one module per game
- `rules/` — plain text rules files (one per game), displayed in RulesView
- `assets/` — generated PNG icons and sprites (`icons/`, `ui/`)
- `tests/` — pytest test suite (AI unit tests, game logic tests, integration tests)
- `games/__init__.py` — `GAME_LIST` registry (name, ViewClass, rules_file, icon_file)
- `generate_assets.py` — regenerate all PNG assets (requires Pillow)

## Key Separation of Concerns
- **`games/*.py`** — state, input, logic. Zero `arcade.draw_*` calls (except `self.clear()`).
- **`renderers/*_renderer.py`** — all rendering. Each has a `draw(game)` function that receives the game view instance and accesses state via `game.attribute`.
- **`ai/*.py`** — pure Python, no arcade imports. Independently testable.
- **Text rendering** — uses `arcade.Text` objects (created in game `__init__` or `_create_texts()`), never `arcade.draw_text()`.

## Conventions
- All rendering uses arcade 3.x APIs (`arcade.draw_rect_filled(arcade.XYWH(...), color)`, etc.)
- Window size: 800x600 (WIDTH/HEIGHT constants)
- Every game view has "Back" (top-left), "New Game" (top-right), and "?" help buttons
- Game selection shows rules/instructions first; "?" button re-opens rules mid-game
- AI moves use `on_update` with a short delay (0.3-0.5s), never blocking
- Games with VS modes (Tetris, Puzzle Bubble) show a mode selection screen (Solo / VS AI)
- Multiplayer AI games (Liar's Dice, Tron) allow choosing number of AI opponents
- Constants live in renderers; games import from renderers if needed (avoids circular imports)

## Testing
Tests are in `tests/` using pytest:
- `tests/ai/` — unit tests for all 15 AI modules (move validity, rule helpers, edge cases)
- `tests/games/` — logic tests for non-AI games (2048, Wordle, Mastermind, 15 Puzzle, Peg Solitaire)
- `tests/integration/` — full game flow simulations (TicTacToe, Connect4, Othello, Checkers, Mancala)

## Adding a New Game
1. Create `games/your_game.py` with `YourGameView(arcade.View)` taking `menu_view` param
2. Create `renderers/your_game_renderer.py` with `draw(game)` function for all rendering
3. If AI-based, create `ai/your_game_ai.py` with pure logic class
4. Create `rules/your_game.txt` with game instructions
5. Add icon: create function in `generate_assets.py` or add 120x120 PNG to `assets/icons/`
6. Register in `games/__init__.py` GAME_LIST as `(name, ViewClass, "rules.txt", "icon.png")`
7. Add a "?" help button that opens `RulesView(name, rules_file, None, self.menu_view, existing_game_view=self)`
8. Add tests in `tests/ai/` and/or `tests/games/`

## Commands
- Run: `python game_launcher.py`
- Install deps: `pip install -r requirements.txt`
- Run tests: `python -m pytest tests/ -v`
- Regenerate assets: `python generate_assets.py`

## Dependencies
- `arcade>=3.0`
- `pytest>=7.0` (dev)
