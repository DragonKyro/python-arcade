"""
Checkers AI using Minimax with Alpha-Beta Pruning.
Pure game logic - no arcade imports.

Board representation (8x8 list of lists):
  0 = empty
  1 = red (player)
  2 = black (AI)
  3 = red king
  4 = black king

Red starts at bottom (rows 5-7), Black starts at top (rows 0-2).
"""

import math

EMPTY = 0
RED = 1
BLACK = 2
RED_KING = 3
BLACK_KING = 4

DEPTH_LIMIT = 5


def initial_board():
    """Return the starting board for checkers."""
    board = [[EMPTY] * 8 for _ in range(8)]
    for row in range(3):
        for col in range(8):
            if (row + col) % 2 == 1:
                board[row][col] = BLACK
    for row in range(5, 8):
        for col in range(8):
            if (row + col) % 2 == 1:
                board[row][col] = RED
    return board


def _pieces_for_color(color):
    """Return the (normal, king) piece values for a color."""
    if color == RED:
        return (RED, RED_KING)
    return (BLACK, BLACK_KING)


def _opponent_color(color):
    """Return the opponent's color."""
    return BLACK if color == RED else RED


def _opponent_pieces(color):
    """Return (normal, king) pieces of the opponent."""
    return _pieces_for_color(_opponent_color(color))


def _is_own_piece(piece, color):
    """Check if a piece belongs to the given color."""
    if color == RED:
        return piece in (RED, RED_KING)
    return piece in (BLACK, BLACK_KING)


def _is_king(piece):
    return piece in (RED_KING, BLACK_KING)


def _forward_directions(color, piece):
    """Return the row directions a piece can move.
    Red moves up (decreasing row), Black moves down (increasing row).
    Kings can move both ways."""
    if _is_king(piece):
        return [-1, 1]
    if color == RED:
        return [-1]
    return [1]


def _promote_if_needed(piece, row):
    """Promote a piece to king if it reaches the opposite end."""
    if piece == RED and row == 0:
        return RED_KING
    if piece == BLACK and row == 7:
        return BLACK_KING
    return piece


def get_captures(board, row, col):
    """Return all capture sequences from (row, col) as a list of move paths.
    Each path is [(from_row, from_col), (land_row, land_col), ...] for multi-jumps."""
    piece = board[row][col]
    if piece == EMPTY:
        return []
    color = RED if piece in (RED, RED_KING) else BLACK
    opp_normal, opp_king = _opponent_pieces(color)

    results = []

    def _dfs(board_state, r, c, current_piece, path):
        found_capture = False
        directions = _forward_directions(color, current_piece)
        for dr in directions:
            for dc in [-1, 1]:
                mr, mc = r + dr, c + dc  # mid (captured piece)
                lr, lc = r + 2 * dr, c + 2 * dc  # landing
                if 0 <= lr < 8 and 0 <= lc < 8:
                    mid_piece = board_state[mr][mc]
                    if mid_piece in (opp_normal, opp_king) and board_state[lr][lc] == EMPTY:
                        found_capture = True
                        new_board = [row_[:] for row_ in board_state]
                        new_board[r][c] = EMPTY
                        new_board[mr][mc] = EMPTY
                        landed_piece = _promote_if_needed(current_piece, lr)
                        new_board[lr][lc] = landed_piece
                        _dfs(new_board, lr, lc, landed_piece, path + [(lr, lc)])
        if not found_capture and len(path) > 1:
            results.append(path)

    _dfs(board, row, col, piece, [(row, col)])
    return results


def _get_simple_moves(board, row, col):
    """Return non-capture moves from (row, col)."""
    piece = board[row][col]
    if piece == EMPTY:
        return []
    color = RED if piece in (RED, RED_KING) else BLACK
    moves = []
    directions = _forward_directions(color, piece)
    for dr in directions:
        for dc in [-1, 1]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == EMPTY:
                moves.append([(row, col), (nr, nc)])
    return moves


def get_all_moves(board, color):
    """Return all valid moves for a color. Mandatory captures enforced."""
    normal, king = _pieces_for_color(color)
    captures = []
    simple = []
    for r in range(8):
        for c in range(8):
            if board[r][c] in (normal, king):
                caps = get_captures(board, r, c)
                if caps:
                    captures.extend(caps)
                else:
                    smoves = _get_simple_moves(board, r, c)
                    simple.extend(smoves)
    # Mandatory capture rule
    if captures:
        return captures
    return simple


def apply_move(board, move):
    """Apply a move (list of positions) and return a new board."""
    new_board = [row[:] for row in board]
    start_r, start_c = move[0]
    piece = new_board[start_r][start_c]
    new_board[start_r][start_c] = EMPTY

    for i in range(1, len(move)):
        prev_r, prev_c = move[i - 1]
        next_r, next_c = move[i]
        # Check if this is a capture (distance 2)
        dr = next_r - prev_r
        dc = next_c - prev_c
        if abs(dr) == 2:
            # Remove captured piece
            mid_r = (prev_r + next_r) // 2
            mid_c = (prev_c + next_c) // 2
            new_board[mid_r][mid_c] = EMPTY

    # Place piece at final position
    final_r, final_c = move[-1]
    piece = _promote_if_needed(piece, final_r)
    new_board[final_r][final_c] = piece
    return new_board


def check_winner(board):
    """Return RED, BLACK, or 'draw' if game is over, else None."""
    red_pieces = 0
    black_pieces = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] in (RED, RED_KING):
                red_pieces += 1
            elif board[r][c] in (BLACK, BLACK_KING):
                black_pieces += 1
    if red_pieces == 0:
        return BLACK
    if black_pieces == 0:
        return RED
    red_moves = get_all_moves(board, RED)
    black_moves = get_all_moves(board, BLACK)
    if not red_moves and not black_moves:
        return "draw"
    if not red_moves:
        return BLACK
    if not black_moves:
        return RED
    return None


def count_pieces(board):
    """Return (red_count, black_count) including kings."""
    red = 0
    black = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] in (RED, RED_KING):
                red += 1
            elif board[r][c] in (BLACK, BLACK_KING):
                black += 1
    return red, black


# ------------------------------------------------------------------ AI

def _evaluate(board):
    """Evaluate board from BLACK (AI) perspective.
    Positive = good for black, negative = good for red."""
    score = 0.0
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == EMPTY:
                continue

            # Base piece value (kings worth 1.5x)
            if piece == BLACK:
                val = 1.0
            elif piece == BLACK_KING:
                val = 1.5
            elif piece == RED:
                val = -1.0
            elif piece == RED_KING:
                val = -1.5
            else:
                continue

            score += val

            # Advancement bonus (how far a piece has progressed)
            if piece == BLACK:
                # Black moves down, row 7 is promotion
                score += r * 0.05
            elif piece == RED:
                # Red moves up, row 0 is promotion
                score -= (7 - r) * 0.05

            # Center control bonus (columns 2-5, rows 2-5)
            if 2 <= r <= 5 and 2 <= c <= 5:
                if piece in (BLACK, BLACK_KING):
                    score += 0.1
                else:
                    score -= 0.1

    return score


def _minimax(board, depth, alpha, beta, maximizing):
    """Minimax with alpha-beta pruning. Maximizing = BLACK (AI)."""
    color = BLACK if maximizing else RED
    winner = check_winner(board)
    if winner == BLACK:
        return 100.0 + depth  # prefer faster wins
    if winner == RED:
        return -100.0 - depth
    if winner == "draw":
        return 0.0
    if depth == 0:
        return _evaluate(board)

    moves = get_all_moves(board, color)
    if not moves:
        return _evaluate(board)

    if maximizing:
        max_eval = -math.inf
        for move in moves:
            new_board = apply_move(board, move)
            val = _minimax(new_board, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for move in moves:
            new_board = apply_move(board, move)
            val = _minimax(new_board, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, val)
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_eval


class CheckersAI:
    """Checkers AI using minimax with alpha-beta pruning."""

    def __init__(self, depth=DEPTH_LIMIT):
        self.depth = depth

    def get_move(self, board, ai_color=BLACK):
        """Return the best move as a list of positions [(r,c), (r,c), ...].
        Returns None if no moves available."""
        moves = get_all_moves(board, ai_color)
        if not moves:
            return None

        best_move = None
        best_score = -math.inf

        for move in moves:
            new_board = apply_move(board, move)
            score = _minimax(new_board, self.depth - 1, -math.inf, math.inf, False)
            if score > best_score:
                best_score = score
                best_move = move

        return best_move
