from pages.home import HomeView
# NOTE: GamesView is imported lazily where it's used (pages.home.on_mouse_press, tests, etc.).
# Eager-importing it here would pull in games/__init__.py, which triggers a circular import
# because game modules import from pages.rules.
