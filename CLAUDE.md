# Python Arcade Game Collection

## Project Overview
A collection of single-player, AI-opponent, and retro arcade games built with the `arcade` library (3.x).

## Architecture
- `main.py` — minimal entry point, creates window and shows HomeView
- `pages/` — UI views (HomeView, GamesView, RulesView) and shared components (Button)
- `games/` — game state, input handling, and logic only (no drawing code)
- `renderers/` — all drawing/rendering code, one module per game (`{game}_renderer.py`)
- `ai/` — pure Python AI logic (no arcade imports), one module per game
- `rules/` — plain text rules files (one per game), displayed in RulesView
- `assets/` — generated PNG icons and sprites (`icons/`, `ui/`)
- `games/__init__.py` — `GAME_LIST` registry (name, ViewClass, rules_file, icon_file)
- `generate_assets.py` — regenerate all PNG assets (requires Pillow)

## Key Separation of Concerns
- **`games/*.py`** — state, input, logic. Zero `arcade.draw_*` calls (except `self.clear()`).
- **`renderers/*_renderer.py`** — all `arcade.draw_*` calls. Each has a `draw(game)` function that receives the game view instance and accesses state via `game.attribute`.
- **`ai/*.py`** — pure Python, no arcade imports. Independently testable.

## Conventions
- All rendering uses arcade 3.x APIs (`arcade.draw_rect_filled(arcade.XYWH(...), color)`, etc.)
- Window size: 800x600 (WIDTH/HEIGHT constants)
- Every game view has "Back" (top-left), "New Game" (top-right), and "?" help buttons
- Game selection shows rules/instructions first; "?" button re-opens rules mid-game
- AI moves use `on_update` with a short delay (0.3-0.5s), never blocking
- Game icon view uses 120x120 PNG icons from `assets/icons/`

## Adding a New Game
1. Create `games/your_game.py` with `YourGameView(arcade.View)` taking `menu_view` param
2. Create `renderers/your_game_renderer.py` with `draw(game)` function for all rendering
3. If AI-based, create `ai/your_game_ai.py` with pure logic class
4. Create `rules/your_game.txt` with game instructions
5. Add icon: create function in `generate_assets.py` or add 120x120 PNG to `assets/icons/`
6. Register in `games/__init__.py` GAME_LIST as `(name, ViewClass, "rules.txt", "icon.png")`
7. Add a "?" help button that opens `RulesView(name, rules_file, None, self.menu_view, existing_game_view=self)`

## Commands
- Run: `python main.py`
- Install deps: `pip install -r requirements.txt`
- Regenerate assets: `python generate_assets.py`

## Dependencies
- `arcade>=3.0`
