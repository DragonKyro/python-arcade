"""
Go AI using Monte Carlo random playouts.
Pure Python, no arcade imports.
"""

import copy
import random

EMPTY = 0
BLACK = 1
WHITE = 2

BOARD_SIZE = 9


def _opponent(color):
    return WHITE if color == BLACK else BLACK


def _get_group(board, r, c):
    """Return the set of positions in the group containing (r, c) and its liberties."""
    color = board[r][c]
    if color == EMPTY:
        return set(), set()
    group = set()
    liberties = set()
    stack = [(r, c)]
    while stack:
        cr, cc = stack.pop()
        if (cr, cc) in group:
            continue
        group.add((cr, cc))
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if board[nr][nc] == EMPTY:
                    liberties.add((nr, nc))
                elif board[nr][nc] == color and (nr, nc) not in group:
                    stack.append((nr, nc))
    return group, liberties


def _remove_group(board, group):
    """Remove a group from the board, returning the number of stones removed."""
    for r, c in group:
        board[r][c] = EMPTY
    return len(group)


def _try_capture(board, r, c, color):
    """After placing `color` at (r,c), capture any opponent groups with no liberties.
    Returns the number of captured stones."""
    opp = _opponent(color)
    captured = 0
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == opp:
            group, liberties = _get_group(board, nr, nc)
            if len(liberties) == 0:
                captured += _remove_group(board, group)
    return captured


def apply_move(board, r, c, color, prev_board_hash=None):
    """Place a stone and handle captures.
    Returns (new_board, captured_count, new_board_hash) or None if the move is illegal.
    """
    if board[r][c] != EMPTY:
        return None

    new_board = copy.deepcopy(board)
    new_board[r][c] = color
    captured = _try_capture(new_board, r, c, color)

    # Check suicide: if the placed stone's group has no liberties and no captures happened
    if captured == 0:
        group, liberties = _get_group(new_board, r, c)
        if len(liberties) == 0:
            return None  # Suicide

    # Check ko
    new_hash = _board_hash(new_board)
    if prev_board_hash is not None and new_hash == prev_board_hash:
        return None  # Ko violation

    return new_board, captured, new_hash


def _board_hash(board):
    """Simple board hash for ko detection."""
    return tuple(tuple(row) for row in board)


def get_legal_moves(board, color, prev_board_hash=None):
    """Return list of legal (row, col) moves for the given color."""
    moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                continue
            result = apply_move(board, r, c, color, prev_board_hash)
            if result is not None:
                moves.append((r, c))
    return moves


def score_game(board, black_captured, white_captured):
    """Score using Chinese rules (area scoring).
    Returns (black_score, white_score). White gets 6.5 komi."""
    # Territory: flood-fill empty regions to determine ownership
    visited = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    black_territory = 0
    white_territory = 0

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == BLACK:
                black_territory += 1  # area scoring: own stones count
            elif board[r][c] == WHITE:
                white_territory += 1
            elif not visited[r][c]:
                # Flood-fill empty region
                region = []
                borders = set()
                stack = [(r, c)]
                while stack:
                    cr, cc = stack.pop()
                    if visited[cr][cc]:
                        continue
                    if board[cr][cc] != EMPTY:
                        borders.add(board[cr][cc])
                        continue
                    visited[cr][cc] = True
                    region.append((cr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and not visited[nr][nc]:
                            stack.append((nr, nc))
                # Assign territory if bordered by only one color
                if borders == {BLACK}:
                    black_territory += len(region)
                elif borders == {WHITE}:
                    white_territory += len(region)

    komi = 6.5
    return black_territory, white_territory + komi


def _random_playout(board, color, prev_board_hash):
    """Play a random game to completion, return winner (BLACK or WHITE)."""
    b = copy.deepcopy(board)
    current = color
    prev_hash = prev_board_hash
    consecutive_passes = 0
    max_moves = BOARD_SIZE * BOARD_SIZE * 3

    for _ in range(max_moves):
        moves = get_legal_moves(b, current, prev_hash)
        if not moves or random.random() < 0.1:  # sometimes pass randomly
            consecutive_passes += 1
            if consecutive_passes >= 2:
                break
            current = _opponent(current)
            continue

        consecutive_passes = 0
        move = random.choice(moves)
        r, c = move
        result = apply_move(b, r, c, current, prev_hash)
        if result is None:
            consecutive_passes += 1
            if consecutive_passes >= 2:
                break
            current = _opponent(current)
            continue

        b, _, prev_hash = result
        current = _opponent(current)

    bs, ws = score_game(b, 0, 0)
    return BLACK if bs > ws else WHITE


class GoAI:
    """Go AI using Monte Carlo random playouts."""

    DIFFICULTY_PLAYOUTS = {"easy": 50, "medium": 200, "hard": 500}

    def __init__(self, difficulty="hard"):
        self.difficulty = difficulty
        self.num_playouts = self.DIFFICULTY_PLAYOUTS.get(difficulty, 500)

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.num_playouts = self.DIFFICULTY_PLAYOUTS.get(difficulty, 500)

    def get_move(self, board, ai_color, prev_board_hash=None):
        """Return (row, col) for the best move, or 'pass' to pass."""
        moves = get_legal_moves(board, ai_color, prev_board_hash)
        if not moves:
            return "pass"

        # Quick check: if a move captures opponent stones, prioritize it
        best_move = None
        best_wins = -1

        for move in moves:
            r, c = move
            result = apply_move(board, r, c, ai_color, prev_board_hash)
            if result is None:
                continue
            new_board, captured, new_hash = result

            wins = 0
            for _ in range(self.num_playouts):
                winner = _random_playout(new_board, _opponent(ai_color), new_hash)
                if winner == ai_color:
                    wins += 1

            if wins > best_wins:
                best_wins = wins
                best_move = move

        if best_move is None:
            return "pass"
        return best_move
