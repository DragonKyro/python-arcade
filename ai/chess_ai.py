"""
Chess AI using Minimax with Alpha-Beta Pruning.
Pure game logic - no arcade imports.

Board representation: 8x8 list of lists (row 0 = rank 8, row 7 = rank 1).
  Pieces as strings: 'P','N','B','R','Q','K' (white upper)
                     'p','n','b','r','q','k' (black lower)
                     None = empty square

White starts at bottom (rows 6-7), Black starts at top (rows 0-1).
"""

import copy
import math

# Piece values
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0,
    'p': -100, 'n': -320, 'b': -330, 'r': -500, 'q': -900, 'k': 0,
}

# Difficulty depths
DEPTH_EASY = 2
DEPTH_MEDIUM = 3
DEPTH_HARD = 4

# Piece-square tables (from white's perspective, row 0=rank8 top, row 7=rank1 bottom)
# For black, we mirror vertically and negate.

PAWN_TABLE = [
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [ 50, 50, 50, 50, 50, 50, 50, 50],
    [ 10, 10, 20, 30, 30, 20, 10, 10],
    [  5,  5, 10, 25, 25, 10,  5,  5],
    [  0,  0,  0, 20, 20,  0,  0,  0],
    [  5, -5,-10,  0,  0,-10, -5,  5],
    [  5, 10, 10,-20,-20, 10, 10,  5],
    [  0,  0,  0,  0,  0,  0,  0,  0],
]

KNIGHT_TABLE = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50],
]

BISHOP_TABLE = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20],
]

ROOK_TABLE = [
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [  5, 10, 10, 10, 10, 10, 10,  5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [  0,  0,  0,  5,  5,  0,  0,  0],
]

QUEEN_TABLE = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [ -5,  0,  5,  5,  5,  5,  0, -5],
    [  0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20],
]

KING_TABLE_MID = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [ 20, 20,  0,  0,  0,  0, 20, 20],
    [ 20, 30, 10,  0,  0, 10, 30, 20],
]

PST = {
    'P': PAWN_TABLE, 'N': KNIGHT_TABLE, 'B': BISHOP_TABLE,
    'R': ROOK_TABLE, 'Q': QUEEN_TABLE, 'K': KING_TABLE_MID,
}


def initial_board():
    """Return the standard starting chess position."""
    board = [[None] * 8 for _ in range(8)]
    # Black pieces (top)
    board[0] = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']
    board[1] = ['p'] * 8
    # White pieces (bottom)
    board[6] = ['P'] * 8
    board[7] = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
    return board


def initial_castling_rights():
    """Return initial castling rights dict."""
    return {'K': True, 'Q': True, 'k': True, 'q': True}


def is_white(piece):
    """Check if a piece is white (uppercase)."""
    return piece is not None and piece.isupper()


def is_black(piece):
    """Check if a piece is black (lowercase)."""
    return piece is not None and piece.islower()


def piece_color(piece):
    """Return 'white' or 'black' for a piece, or None."""
    if piece is None:
        return None
    return 'white' if piece.isupper() else 'black'


def is_own(piece, color):
    """Check if piece belongs to given color."""
    if piece is None:
        return False
    return (color == 'white' and piece.isupper()) or (color == 'black' and piece.islower())


def is_enemy(piece, color):
    """Check if piece belongs to the opponent."""
    if piece is None:
        return False
    return not is_own(piece, color)


def opponent(color):
    """Return the opponent color."""
    return 'black' if color == 'white' else 'white'


def in_bounds(r, c):
    """Check if (r, c) is within the board."""
    return 0 <= r < 8 and 0 <= c < 8


def find_king(board, color):
    """Find the king position for the given color."""
    king = 'K' if color == 'white' else 'k'
    for r in range(8):
        for c in range(8):
            if board[r][c] == king:
                return (r, c)
    return None


def is_square_attacked(board, r, c, by_color):
    """Check if square (r, c) is attacked by any piece of by_color."""
    # Pawn attacks
    if by_color == 'white':
        for dc in [-1, 1]:
            pr, pc = r + 1, c + dc
            if in_bounds(pr, pc) and board[pr][pc] == 'P':
                return True
    else:
        for dc in [-1, 1]:
            pr, pc = r - 1, c + dc
            if in_bounds(pr, pc) and board[pr][pc] == 'p':
                return True

    # Knight attacks
    knight = 'N' if by_color == 'white' else 'n'
    for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                   (1, -2), (1, 2), (2, -1), (2, 1)]:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc) and board[nr][nc] == knight:
            return True

    # King attacks
    king = 'K' if by_color == 'white' else 'k'
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and board[nr][nc] == king:
                return True

    # Sliding pieces: bishop/queen (diagonals)
    bishop = 'B' if by_color == 'white' else 'b'
    queen = 'Q' if by_color == 'white' else 'q'
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc):
            p = board[nr][nc]
            if p is not None:
                if p == bishop or p == queen:
                    return True
                break
            nr += dr
            nc += dc

    # Sliding pieces: rook/queen (straight lines)
    rook = 'R' if by_color == 'white' else 'r'
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc):
            p = board[nr][nc]
            if p is not None:
                if p == rook or p == queen:
                    return True
                break
            nr += dr
            nc += dc

    return False


def is_in_check(board, color):
    """Check if the given color's king is in check."""
    king_pos = find_king(board, color)
    if king_pos is None:
        return True  # King captured (shouldn't happen in normal play)
    return is_square_attacked(board, king_pos[0], king_pos[1], opponent(color))


def _generate_pseudo_legal_moves(board, color, castling_rights=None, en_passant_target=None):
    """Generate all pseudo-legal moves (may leave king in check)."""
    moves = []  # Each move: (from_r, from_c, to_r, to_c, promotion_piece_or_None)

    pawn_dir = -1 if color == 'white' else 1
    start_row = 6 if color == 'white' else 1
    promo_row = 0 if color == 'white' else 7

    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if not is_own(piece, color):
                continue

            pt = piece.upper()

            if pt == 'P':
                # Forward one
                nr = r + pawn_dir
                if in_bounds(nr, c) and board[nr][c] is None:
                    if nr == promo_row:
                        for promo in ['Q', 'R', 'B', 'N']:
                            p = promo if color == 'white' else promo.lower()
                            moves.append((r, c, nr, c, p))
                    else:
                        moves.append((r, c, nr, c, None))
                    # Forward two from start
                    if r == start_row:
                        nr2 = r + 2 * pawn_dir
                        if board[nr2][c] is None:
                            moves.append((r, c, nr2, c, None))

                # Captures
                for dc in [-1, 1]:
                    nc = c + dc
                    nr = r + pawn_dir
                    if not in_bounds(nr, nc):
                        continue
                    target = board[nr][nc]
                    if target is not None and is_enemy(target, color):
                        if nr == promo_row:
                            for promo in ['Q', 'R', 'B', 'N']:
                                p = promo if color == 'white' else promo.lower()
                                moves.append((r, c, nr, nc, p))
                        else:
                            moves.append((r, c, nr, nc, None))

                # En passant
                if en_passant_target is not None:
                    ep_r, ep_c = en_passant_target
                    if r + pawn_dir == ep_r and abs(c - ep_c) == 1:
                        moves.append((r, c, ep_r, ep_c, None))

            elif pt == 'N':
                for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                               (1, -2), (1, 2), (2, -1), (2, 1)]:
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and not is_own(board[nr][nc], color):
                        moves.append((r, c, nr, nc, None))

            elif pt == 'B':
                for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    nr, nc = r + dr, c + dc
                    while in_bounds(nr, nc):
                        if is_own(board[nr][nc], color):
                            break
                        moves.append((r, c, nr, nc, None))
                        if board[nr][nc] is not None:
                            break
                        nr += dr
                        nc += dc

            elif pt == 'R':
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    while in_bounds(nr, nc):
                        if is_own(board[nr][nc], color):
                            break
                        moves.append((r, c, nr, nc, None))
                        if board[nr][nc] is not None:
                            break
                        nr += dr
                        nc += dc

            elif pt == 'Q':
                for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                               (0, 1), (1, -1), (1, 0), (1, 1)]:
                    nr, nc = r + dr, c + dc
                    while in_bounds(nr, nc):
                        if is_own(board[nr][nc], color):
                            break
                        moves.append((r, c, nr, nc, None))
                        if board[nr][nc] is not None:
                            break
                        nr += dr
                        nc += dc

            elif pt == 'K':
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if in_bounds(nr, nc) and not is_own(board[nr][nc], color):
                            moves.append((r, c, nr, nc, None))

    # Castling
    if castling_rights:
        if color == 'white':
            king_row = 7
            if castling_rights.get('K') and board[king_row][4] == 'K':
                if (board[king_row][5] is None and board[king_row][6] is None
                        and board[king_row][7] == 'R'):
                    if (not is_square_attacked(board, king_row, 4, 'black')
                            and not is_square_attacked(board, king_row, 5, 'black')
                            and not is_square_attacked(board, king_row, 6, 'black')):
                        moves.append((king_row, 4, king_row, 6, None))
            if castling_rights.get('Q') and board[king_row][4] == 'K':
                if (board[king_row][3] is None and board[king_row][2] is None
                        and board[king_row][1] is None and board[king_row][0] == 'R'):
                    if (not is_square_attacked(board, king_row, 4, 'black')
                            and not is_square_attacked(board, king_row, 3, 'black')
                            and not is_square_attacked(board, king_row, 2, 'black')):
                        moves.append((king_row, 4, king_row, 2, None))
        else:
            king_row = 0
            if castling_rights.get('k') and board[king_row][4] == 'k':
                if (board[king_row][5] is None and board[king_row][6] is None
                        and board[king_row][7] == 'r'):
                    if (not is_square_attacked(board, king_row, 4, 'white')
                            and not is_square_attacked(board, king_row, 5, 'white')
                            and not is_square_attacked(board, king_row, 6, 'white')):
                        moves.append((king_row, 4, king_row, 6, None))
            if castling_rights.get('q') and board[king_row][4] == 'k':
                if (board[king_row][3] is None and board[king_row][2] is None
                        and board[king_row][1] is None and board[king_row][0] == 'r'):
                    if (not is_square_attacked(board, king_row, 4, 'white')
                            and not is_square_attacked(board, king_row, 3, 'white')
                            and not is_square_attacked(board, king_row, 2, 'white')):
                        moves.append((king_row, 4, king_row, 2, None))

    return moves


def apply_move(board, move, castling_rights=None, en_passant_target=None):
    """Apply a move to the board. Returns (new_board, new_castling, new_ep, captured_piece).
    Move format: (from_r, from_c, to_r, to_c, promotion_piece_or_None)
    """
    fr, fc, tr, tc, promo = move
    new_board = [row[:] for row in board]
    new_castling = dict(castling_rights) if castling_rights else {'K': False, 'Q': False, 'k': False, 'q': False}
    new_ep = None
    piece = new_board[fr][fc]
    captured = new_board[tr][tc]

    # En passant capture
    if piece and piece.upper() == 'P' and en_passant_target and (tr, tc) == en_passant_target:
        # Remove the captured pawn
        cap_row = fr  # The pawn being captured is on the same row as the moving pawn
        new_board[cap_row][tc] = None
        captured = 'p' if is_white(piece) else 'P'

    # Move the piece
    new_board[tr][tc] = piece
    new_board[fr][fc] = None

    # Pawn promotion
    if promo is not None:
        new_board[tr][tc] = promo

    # Pawn double advance -> set en passant target
    if piece and piece.upper() == 'P' and abs(tr - fr) == 2:
        new_ep = ((fr + tr) // 2, fc)

    # Castling: move the rook
    if piece and piece.upper() == 'K' and abs(tc - fc) == 2:
        if tc == 6:  # Kingside
            new_board[fr][5] = new_board[fr][7]
            new_board[fr][7] = None
        elif tc == 2:  # Queenside
            new_board[fr][3] = new_board[fr][0]
            new_board[fr][0] = None

    # Update castling rights
    if piece == 'K':
        new_castling['K'] = False
        new_castling['Q'] = False
    elif piece == 'k':
        new_castling['k'] = False
        new_castling['q'] = False
    if piece == 'R' or (fr == 7 and fc == 7):
        if fr == 7 and fc == 7:
            new_castling['K'] = False
    if piece == 'R' or (fr == 7 and fc == 0):
        if fr == 7 and fc == 0:
            new_castling['Q'] = False
    if piece == 'r' or (fr == 0 and fc == 7):
        if fr == 0 and fc == 7:
            new_castling['k'] = False
    if piece == 'r' or (fr == 0 and fc == 0):
        if fr == 0 and fc == 0:
            new_castling['q'] = False
    # Also revoke if rook is captured
    if tr == 7 and tc == 7:
        new_castling['K'] = False
    if tr == 7 and tc == 0:
        new_castling['Q'] = False
    if tr == 0 and tc == 7:
        new_castling['k'] = False
    if tr == 0 and tc == 0:
        new_castling['q'] = False

    return new_board, new_castling, new_ep, captured


def get_all_legal_moves(board, color, castling_rights=None, en_passant_target=None):
    """Get all legal moves for a color (filters out moves that leave king in check)."""
    if castling_rights is None:
        castling_rights = {'K': False, 'Q': False, 'k': False, 'q': False}
    pseudo = _generate_pseudo_legal_moves(board, color, castling_rights, en_passant_target)
    legal = []
    for move in pseudo:
        new_board, _, _, _ = apply_move(board, move, castling_rights, en_passant_target)
        if not is_in_check(new_board, color):
            legal.append(move)
    return legal


def is_checkmate(board, color, castling_rights=None, en_passant_target=None):
    """Check if the given color is in checkmate."""
    if not is_in_check(board, color):
        return False
    return len(get_all_legal_moves(board, color, castling_rights, en_passant_target)) == 0


def is_stalemate(board, color, castling_rights=None, en_passant_target=None):
    """Check if the given color is in stalemate."""
    if is_in_check(board, color):
        return False
    return len(get_all_legal_moves(board, color, castling_rights, en_passant_target)) == 0


def _evaluate_board(board):
    """Evaluate board position. Positive = white advantage, negative = black advantage."""
    score = 0
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece is None:
                continue
            # Material
            score += PIECE_VALUES[piece]
            # Piece-square table
            pt = piece.upper()
            if pt in PST:
                if piece.isupper():
                    score += PST[pt][r][c]
                else:
                    # Mirror vertically for black
                    score -= PST[pt][7 - r][c]
    return score


def _order_moves(board, moves, color):
    """Order moves for better alpha-beta pruning (captures first, then checks)."""
    scored = []
    for move in moves:
        fr, fc, tr, tc, promo = move
        s = 0
        target = board[tr][tc]
        if target is not None:
            # MVV-LVA: prioritize capturing high-value pieces with low-value pieces
            s += abs(PIECE_VALUES.get(target, 0)) * 10 - abs(PIECE_VALUES.get(board[fr][fc], 0))
        if promo is not None:
            s += 800
        scored.append((s, move))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


class ChessAI:
    """Chess AI using minimax with alpha-beta pruning."""

    def __init__(self, depth=DEPTH_MEDIUM):
        self.depth = depth
        self.nodes_searched = 0

    def get_move(self, board, color, castling_rights=None, en_passant_target=None):
        """Find the best move for the given color.
        Returns (from_sq, to_sq, promotion_piece) where from_sq and to_sq are (row, col).
        """
        if castling_rights is None:
            castling_rights = initial_castling_rights()
        self.nodes_searched = 0
        best_move = None
        best_score = -math.inf if color == 'white' else math.inf

        legal_moves = get_all_legal_moves(board, color, castling_rights, en_passant_target)
        if not legal_moves:
            return None

        legal_moves = _order_moves(board, legal_moves, color)

        alpha = -math.inf
        beta = math.inf

        for move in legal_moves:
            new_board, new_castling, new_ep, _ = apply_move(
                board, move, castling_rights, en_passant_target
            )
            if color == 'white':
                score = self._minimax(new_board, self.depth - 1, alpha, beta,
                                      False, new_castling, new_ep)
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, score)
            else:
                score = self._minimax(new_board, self.depth - 1, alpha, beta,
                                      True, new_castling, new_ep)
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, score)

        if best_move is None:
            return None

        fr, fc, tr, tc, promo = best_move
        return ((fr, fc), (tr, tc), promo)

    def _minimax(self, board, depth, alpha, beta, maximizing, castling_rights, en_passant_target):
        """Minimax with alpha-beta pruning."""
        self.nodes_searched += 1
        color = 'white' if maximizing else 'black'

        # Terminal checks
        if is_checkmate(board, color, castling_rights, en_passant_target):
            # The side to move is in checkmate, so the other side wins
            return -99999 if maximizing else 99999

        if is_stalemate(board, color, castling_rights, en_passant_target):
            return 0

        if depth == 0:
            return _evaluate_board(board)

        legal_moves = get_all_legal_moves(board, color, castling_rights, en_passant_target)
        legal_moves = _order_moves(board, legal_moves, color)

        if maximizing:
            max_eval = -math.inf
            for move in legal_moves:
                new_board, new_castling, new_ep, _ = apply_move(
                    board, move, castling_rights, en_passant_target
                )
                eval_score = self._minimax(new_board, depth - 1, alpha, beta,
                                           False, new_castling, new_ep)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for move in legal_moves:
                new_board, new_castling, new_ep, _ = apply_move(
                    board, move, castling_rights, en_passant_target
                )
                eval_score = self._minimax(new_board, depth - 1, alpha, beta,
                                           True, new_castling, new_ep)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval


def get_legal_moves_for_piece(board, r, c, castling_rights=None, en_passant_target=None):
    """Get all legal destination squares for a specific piece."""
    piece = board[r][c]
    if piece is None:
        return []
    color = piece_color(piece)
    all_moves = get_all_legal_moves(board, color, castling_rights, en_passant_target)
    return [(m[2], m[3], m[4]) for m in all_moves if m[0] == r and m[1] == c]


def get_captured_pieces(board):
    """Compare board to initial position and return captured pieces for each side."""
    initial = {
        'white': {'P': 8, 'N': 2, 'B': 2, 'R': 2, 'Q': 1, 'K': 1},
        'black': {'p': 8, 'n': 2, 'b': 2, 'r': 2, 'q': 1, 'k': 1},
    }
    current_white = {}
    current_black = {}
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p is None:
                continue
            if p.isupper():
                current_white[p] = current_white.get(p, 0) + 1
            else:
                current_black[p] = current_black.get(p, 0) + 1

    captured_by_black = []  # white pieces captured
    captured_by_white = []  # black pieces captured
    for p, count in initial['white'].items():
        diff = count - current_white.get(p, 0)
        captured_by_black.extend([p] * max(0, diff))
    for p, count in initial['black'].items():
        diff = count - current_black.get(p, 0)
        captured_by_white.extend([p] * max(0, diff))

    return captured_by_white, captured_by_black
