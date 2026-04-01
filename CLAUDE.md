# Python Arcade Game Collection

## Project Overview
A collection of single-player and AI-opponent games built with the `arcade` library (2.6.x).

## Architecture
- `main.py` — minimal entry point, creates window and shows HomeView
- `pages/` — UI views (HomeView, GamesView) and shared components (Button)
- `games/` — each game is an `arcade.View` subclass accepting `menu_view` in its constructor
- `ai/` — pure Python AI logic (no arcade imports), one module per game
- `games/__init__.py` — `GAME_LIST` registry; add new games here

## Conventions
- All games use arcade 2.6.x APIs (`arcade.start_render()`, `arcade.draw_*`)
- Window size: 800x600 (WIDTH/HEIGHT constants)
- Every game view has "Back" (top-left) and "New Game" (top-right) buttons
- AI moves use `on_update` with a short delay (0.3-0.5s), never blocking
- AI modules are pure logic with no UI dependencies, making them independently testable

## Adding a New Game
1. Create `games/your_game.py` with `YourGameView(arcade.View)` taking `menu_view` param
2. If AI-based, create `ai/your_game_ai.py` with pure logic class
3. Import and register in `games/__init__.py` GAME_LIST
4. The game selection page auto-populates from GAME_LIST

## Commands
- Run: `python main.py`
- Install deps: `pip install -r requirements.txt`

## Dependencies
- `arcade>=2.6,<3.0` (pinned to 2.x due to breaking API changes in 3.x)
