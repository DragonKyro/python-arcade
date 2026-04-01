import copy

EMPTY = 0
BLACK = 1
WHITE = 2

CORNERS = [(0, 0), (0, 7), (7, 0), (7, 7)]
EDGES = set()
for i in range(8):
    EDGES.add((0, i))
    EDGES.add((7, i))
    EDGES.add((i, 0))
    EDGES.add((i, 7))
EDGES -= set(CORNERS)

# Squares adjacent to each corner (penalized when the corner is empty)
CORNER_ADJACENT = {
    (0, 0): [(0, 1), (1, 0), (1, 1)],
    (0, 7): [(0, 6), (1, 7), (1, 6)],
    (7, 0): [(6, 0), (7, 1), (6, 1)],
    (7, 7): [(6, 7), (7, 6), (6, 6)],
}

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),           (0, 1),
              (1, -1),  (1, 0),  (1, 1)]


def _opponent(color):
    return WHITE if color == BLACK else BLACK


def get_valid_moves(board, color):
    """Return a list of (row, col) tuples for all valid moves for the given color."""
    moves = []
    opp = _opponent(color)
    for r in range(8):
        for c in range(8):
            if board[r][c] != EMPTY:
                continue
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                found_opp = False
                while 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == opp:
                    nr += dr
                    nc += dc
                    found_opp = True
                if found_opp and 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == color:
                    moves.append((r, c))
                    break
    return moves


def apply_move(board, row, col, color):
    """Place a piece and flip opponents. Returns a new board."""
    new_board = copy.deepcopy(board)
    new_board[row][col] = color
    opp = _opponent(color)
    for dr, dc in DIRECTIONS:
        nr, nc = row + dr, col + dc
        to_flip = []
        while 0 <= nr < 8 and 0 <= nc < 8 and new_board[nr][nc] == opp:
            to_flip.append((nr, nc))
            nr += dr
            nc += dc
        if to_flip and 0 <= nr < 8 and 0 <= nc < 8 and new_board[nr][nc] == color:
            for fr, fc in to_flip:
                new_board[fr][fc] = color
    return new_board


def check_game_over(board):
    """Return True if neither player has a valid move."""
    return len(get_valid_moves(board, BLACK)) == 0 and len(get_valid_moves(board, WHITE)) == 0


def _evaluate(board, ai_color):
    """Heuristic evaluation from the perspective of ai_color."""
    opp = _opponent(ai_color)
    score = 0

    for r in range(8):
        for c in range(8):
            if board[r][c] == EMPTY:
                continue
            sign = 1 if board[r][c] == ai_color else -1
            if (r, c) in CORNERS:
                score += sign * 10
            elif (r, c) in EDGES:
                score += sign * 2
            else:
                score += sign * 1

    # Penalty for occupying squares adjacent to empty corners
    for corner, adjacents in CORNER_ADJACENT.items():
        cr, cc = corner
        if board[cr][cc] == EMPTY:
            for ar, ac in adjacents:
                if board[ar][ac] == ai_color:
                    score -= 3
                elif board[ar][ac] == opp:
                    score += 3

    return score


def _minimax(board, depth, alpha, beta, maximizing, ai_color):
    """Minimax with alpha-beta pruning."""
    if depth == 0 or check_game_over(board):
        return _evaluate(board, ai_color), None

    current_color = ai_color if maximizing else _opponent(ai_color)
    moves = get_valid_moves(board, current_color)

    # Pass turn if no valid moves
    if not moves:
        val, _ = _minimax(board, depth - 1, alpha, beta, not maximizing, ai_color)
        return val, None

    best_move = moves[0]

    if maximizing:
        max_eval = float("-inf")
        for move in moves:
            new_board = apply_move(board, move[0], move[1], current_color)
            val, _ = _minimax(new_board, depth - 1, alpha, beta, False, ai_color)
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
            new_board = apply_move(board, move[0], move[1], current_color)
            val, _ = _minimax(new_board, depth - 1, alpha, beta, True, ai_color)
            if val < min_eval:
                min_eval = val
                best_move = move
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_eval, best_move


class OthelloAI:
    """Othello AI using minimax with alpha-beta pruning."""

    def __init__(self, depth=4):
        self.depth = depth

    def get_move(self, board, ai_color):
        """Return (row, col) for the best move, or None if no valid moves."""
        moves = get_valid_moves(board, ai_color)
        if not moves:
            return None
        _, best_move = _minimax(board, self.depth, float("-inf"), float("inf"), True, ai_color)
        return best_move
