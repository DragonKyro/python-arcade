"""Tests for Wordle game logic.

We test _evaluate_guess and _update_key_colors without instantiating the full
WordleView (which needs an OpenGL context).  We build a minimal stand-in that
carries only the attributes the methods need, then bind the real methods.
"""

import types

from renderers.wordle_renderer import GREEN, YELLOW, DARK_GRAY, WORD_LENGTH


def _make_game(answer):
    """Return a lightweight object with Wordle state + bound logic methods."""

    class _Stub:
        pass

    g = _Stub()
    g.answer = answer.upper()
    g.key_colors = {}

    from games.wordle import WordleView
    for name in ("_evaluate_guess", "_update_key_colors"):
        method = getattr(WordleView, name)
        setattr(g, name, types.MethodType(method, g))

    return g


# ===================================================================
# Exact matches (all green)
# ===================================================================

def test_all_exact():
    g = _make_game("CRANE")
    colors = g._evaluate_guess("CRANE")
    assert colors == [GREEN, GREEN, GREEN, GREEN, GREEN]


# ===================================================================
# No matches (all gray)
# ===================================================================

def test_no_match():
    g = _make_game("CRANE")
    colors = g._evaluate_guess("BOUGHT".replace("T", "")[:5])
    # Use a word with no overlapping letters
    colors = g._evaluate_guess("GLYPH")
    assert colors == [DARK_GRAY, DARK_GRAY, DARK_GRAY, DARK_GRAY, DARK_GRAY]


# ===================================================================
# Partial matches (yellow)
# ===================================================================

def test_all_yellow():
    """Every letter is in the word but in the wrong position."""
    g = _make_game("CRANE")
    # C=0, R=1, A=2, N=3, E=4
    # Rearranged: R(pos0), A(pos1), N(pos2), E(pos3), C(pos4)
    colors = g._evaluate_guess("RANEC")
    assert colors == [YELLOW, YELLOW, YELLOW, YELLOW, YELLOW]


def test_mixed_green_yellow_gray():
    g = _make_game("CRANE")
    # Guess: CREST -> C green, R green, E yellow, S gray, T gray
    colors = g._evaluate_guess("CREST")
    assert colors[0] == GREEN   # C
    assert colors[1] == GREEN   # R
    assert colors[2] == YELLOW  # E (in word but not pos 2)
    assert colors[3] == DARK_GRAY  # S
    assert colors[4] == DARK_GRAY  # T


# ===================================================================
# Duplicate letter handling
# ===================================================================

def test_duplicate_guess_one_in_answer():
    """Guess has two L's, answer has one L.  Only one should be marked."""
    g = _make_game("PLANE")
    # Guess: LLAMA -> first L at pos 0 (not in pos 0 of PLANE -> P),
    #   but L is at pos 1 of PLANE
    colors = g._evaluate_guess("LLAMA")
    l_colors = [colors[0], colors[1]]
    # Exactly one L should be green or yellow, the other gray
    assert l_colors.count(DARK_GRAY) == 1
    # pos 0: L — answer pos 0 is P, so not green. L is in answer -> yellow
    assert colors[0] == YELLOW
    # pos 1: L — answer pos 1 is L, so green
    assert colors[1] == GREEN


def test_duplicate_in_answer_and_guess():
    """Both answer and guess have double letters."""
    g = _make_game("LLAMA")  # Not a real Wordle word, but logic is generic
    # Pretend it's the answer
    colors = g._evaluate_guess("LLAMA")
    assert colors == [GREEN, GREEN, GREEN, GREEN, GREEN]


def test_duplicate_guess_two_in_answer():
    """Answer has two E's, guess has two E's in different positions."""
    g = _make_game("GEESE")
    # G=0 E=1 E=2 S=3 E=4
    # Guess: EGGED  -> E(0) G(1) G(2) E(3) D(4)
    colors = g._evaluate_guess("EGGED")
    # E at 0: answer[0]=G, not exact. E is in answer -> yellow
    assert colors[0] == YELLOW
    # G at 1: answer[1]=E, not exact. G is at pos 0 -> yellow
    assert colors[1] == YELLOW
    # G at 2: answer[2]=E, not exact. G already accounted for (only 1 G in answer)
    assert colors[2] == DARK_GRAY
    # E at 3: answer[3]=S, not exact. E is still in answer
    assert colors[3] == YELLOW
    # D at 4: not in answer
    assert colors[4] == DARK_GRAY


def test_green_takes_priority_over_yellow():
    """If one copy of a letter is exact and answer has only one, the other copy is gray."""
    g = _make_game("AROSE")
    # A at pos 0 is exact green.  Guess: ALARM -> A at 0 (green), L, A at 2, R, M
    # Only one A in AROSE, so second A should be gray.
    colors = g._evaluate_guess("ALARM")
    assert colors[0] == GREEN      # A exact
    assert colors[2] == DARK_GRAY  # second A, no more A's available


# ===================================================================
# Keyboard color tracking
# ===================================================================

def test_key_colors_green_overrides_yellow():
    g = _make_game("CRANE")
    # First guess gives C as yellow
    g._update_key_colors("XYZCA", [DARK_GRAY, DARK_GRAY, DARK_GRAY, YELLOW, DARK_GRAY])
    assert g.key_colors["C"] == YELLOW
    # Second guess gives C as green — should override
    g._update_key_colors("CRANE", [GREEN, GREEN, GREEN, GREEN, GREEN])
    assert g.key_colors["C"] == GREEN


def test_key_colors_green_not_downgraded():
    g = _make_game("CRANE")
    g._update_key_colors("CRANE", [GREEN, GREEN, GREEN, GREEN, GREEN])
    # Later guess marks C as gray — green should stick
    g._update_key_colors("CXXXX", [DARK_GRAY, DARK_GRAY, DARK_GRAY, DARK_GRAY, DARK_GRAY])
    assert g.key_colors["C"] == GREEN


# ===================================================================
# Valid word checking (uses the word list)
# ===================================================================

def test_valid_word_in_list():
    from games.wordle import VALID_GUESSES
    assert "crane" in VALID_GUESSES
    assert "about" in VALID_GUESSES


def test_invalid_word_not_in_list():
    from games.wordle import VALID_GUESSES
    assert "zzzzz" not in VALID_GUESSES
    assert "xyzab" not in VALID_GUESSES
