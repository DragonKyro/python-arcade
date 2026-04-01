"""
Gomoku (Five in a Row) AI using minimax with alpha-beta pruning.
Pure Python, no arcade imports.
"""

import copy

EMPTY = 0
BLACK = 1
WHITE = 2

BOARD_SIZE = 15

DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]


def _opponent(color):
    return WHITE if color == BLACK else BLACK


def get_legal_moves(board):
    """Return list of (row, col) for all empty intersections adjacent to existing stones."""
    moves = set()
    has_stones = False
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                has_stones = True
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                            moves.add((nr, nc))
    if not has_stones:
        return [(BOARD_SIZE // 2, BOARD_SIZE // 2)]
    return list(moves)


def check_winner(board):
    """Return BLACK or WHITE if someone has 5 in a row, else None."""
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == EMPTY:
                continue
            color = board[r][c]
            for dr, dc in DIRECTIONS:
                count = 1
                nr, nc = r + dr, c + dc
                while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == color:
                    count += 1
                    nr += dr
                    nc += dc
                if count >= 5:
                    return color
    return None


def is_board_full(board):
    """Return True if no empty cells remain."""
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == EMPTY:
                return False
    return True


def _count_pattern(board, color, length, open_ends_required):
    """Count sequences of `length` stones of `color` with at least `open_ends_required` open ends."""
    opp = _opponent(color)
    count = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            for dr, dc in DIRECTIONS:
                # Check if starting position is valid (not preceded by same color)
                pr, pc = r - dr, c - dc
                if 0 <= pr < BOARD_SIZE and 0 <= pc < BOARD_SIZE and board[pr][pc] == color:
                    continue
                # Count consecutive stones
                seq = 0
                nr, nc = r, c
                while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == color:
                    seq += 1
                    nr += dr
                    nc += dc
                if seq != length:
                    continue
                # Check open ends
                open_ends = 0
                # Before
                if 0 <= pr < BOARD_SIZE and 0 <= pc < BOARD_SIZE and board[pr][pc] == EMPTY:
                    open_ends += 1
                # After
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                    open_ends += 1
                if open_ends >= open_ends_required:
                    count += 1
    return count


def _evaluate(board, ai_color):
    """Heuristic evaluation from the perspective of ai_color."""
    opp = _opponent(ai_color)

    winner = check_winner(board)
    if winner == ai_color:
        return 1000000
    if winner == opp:
        return -1000000

    score = 0

    # AI patterns
    score += _count_pattern(board, ai_color, 4, 2) * 10000   # open four
    score += _count_pattern(board, ai_color, 4, 1) * 5000    # half-open four
    score += _count_pattern(board, ai_color, 3, 2) * 1000    # open three
    score += _count_pattern(board, ai_color, 3, 1) * 100     # half-open three
    score += _count_pattern(board, ai_color, 2, 2) * 50      # open two
    score += _count_pattern(board, ai_color, 2, 1) * 10      # half-open two

    # Opponent patterns (threats to block)
    score -= _count_pattern(board, opp, 4, 2) * 10000
    score -= _count_pattern(board, opp, 4, 1) * 5000
    score -= _count_pattern(board, opp, 3, 2) * 1000
    score -= _count_pattern(board, opp, 3, 1) * 100
    score -= _count_pattern(board, opp, 2, 2) * 50
    score -= _count_pattern(board, opp, 2, 1) * 10

    # Slight center preference
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == ai_color:
                dist = abs(r - 7) + abs(c - 7)
                score += max(0, 7 - dist)
            elif board[r][c] == opp:
                dist = abs(r - 7) + abs(c - 7)
                score -= max(0, 7 - dist)

    return score


def _order_moves(board, moves, ai_color):
    """Order moves by a quick heuristic for better pruning."""
    opp = _opponent(ai_color)

    def score_move(move):
        r, c = move
        s = 0
        # Center preference
        s += max(0, 7 - abs(r - 7) - abs(c - 7))
        # Adjacent to existing stones
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if board[nr][nc] != EMPTY:
                        s += 3
        return s

    return sorted(moves, key=score_move, reverse=True)


def _minimax(board, depth, alpha, beta, maximizing, ai_color):
    """Minimax with alpha-beta pruning."""
    winner = check_winner(board)
    if winner is not None:
        if winner == ai_color:
            return 1000000 + depth, None
        else:
            return -1000000 - depth, None

    if depth == 0 or is_board_full(board):
        return _evaluate(board, ai_color), None

    current_color = ai_color if maximizing else _opponent(ai_color)
    moves = get_legal_moves(board)
    if not moves:
        return _evaluate(board, ai_color), None

    moves = _order_moves(board, moves, ai_color)
    # Limit branching to top candidates for performance
    if len(moves) > 20:
        moves = moves[:20]

    best_move = moves[0]

    if maximizing:
        max_eval = float("-inf")
        for move in moves:
            r, c = move
            board[r][c] = current_color
            val, _ = _minimax(board, depth - 1, alpha, beta, False, ai_color)
            board[r][c] = EMPTY
            if val > max_eval:
                max_eval = val
                best_move = move
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float("inf")
        for move in moves:
            r, c = move
            board[r][c] = current_color
            val, _ = _minimax(board, depth - 1, alpha, beta, True, ai_color)
            board[r][c] = EMPTY
            if val < min_eval:
                min_eval = val
                best_move = move
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_eval, best_move


class GomokuAI:
    """Gomoku AI using minimax with alpha-beta pruning."""

    DIFFICULTY_DEPTHS = {"easy": 1, "medium": 2, "hard": 3}

    def __init__(self, difficulty="hard"):
        self.difficulty = difficulty
        self.depth = self.DIFFICULTY_DEPTHS.get(difficulty, 3)

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.depth = self.DIFFICULTY_DEPTHS.get(difficulty, 3)

    def get_move(self, board, ai_color):
        """Return (row, col) for the best move, or None if no legal moves."""
        moves = get_legal_moves(board)
        if not moves:
            return None

        # Quick check: if only one move (first move), take center
        if len(moves) == 1:
            return moves[0]

        # Check for immediate wins or blocks
        opp = _opponent(ai_color)
        for move in moves:
            r, c = move
            board[r][c] = ai_color
            if check_winner(board) == ai_color:
                board[r][c] = EMPTY
                return move
            board[r][c] = EMPTY

        for move in moves:
            r, c = move
            board[r][c] = opp
            if check_winner(board) == opp:
                board[r][c] = EMPTY
                return move
            board[r][c] = EMPTY

        _, best_move = _minimax(board, self.depth, float("-inf"), float("inf"), True, ai_color)
        return best_move
