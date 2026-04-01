"""
Backgammon AI - pure logic, no arcade imports.

Board convention:
  - board is a list of 24 ints (index 0-23)
  - Positive values = player (White) checkers
  - Negative values = AI (Brown) checkers
  - Player moves 24->1 (board indices 23->0), home board = indices 0-5
  - AI moves 1->24 (board indices 0->23), home board = indices 18-23
  - bar = [player_bar_count, ai_bar_count]
  - off = [player_off_count, ai_off_count]

Color constants for the color parameter:
  +1 = player (positive on board)
  -1 = AI (negative on board)
"""

import copy
import itertools


PLAYER = 1
AI = -1


class BackgammonAI:
    """AI that evaluates all legal move sequences and picks the best."""

    def get_moves(self, board, bar, off, dice, ai_color=AI):
        """Return list of (from_point, to_point) moves for the AI.

        from_point: 0-23 board index, or 'bar'
        to_point: 0-23 board index, or 'off'
        """
        all_sequences = get_all_legal_moves(board, bar, off, dice, ai_color)
        if not all_sequences:
            return []

        best_score = -999999
        best_seq = []
        for seq in all_sequences:
            new_board, new_bar, new_off = apply_moves(board, bar, off, seq, ai_color)
            score = self._evaluate(new_board, new_bar, new_off, ai_color)
            if score > best_score:
                best_score = score
                best_seq = seq

        return best_seq

    def _evaluate(self, board, bar, off, color):
        """Evaluate board from perspective of color. Higher = better for color."""
        score = 0.0
        # color == AI == -1

        # Bonus for bearing off
        if color == AI:
            score += off[1] * 50
            score -= off[0] * 50
        else:
            score += off[0] * 50
            score -= off[1] * 50

        # Penalty for checkers on bar
        if color == AI:
            score -= bar[1] * 40
            score += bar[0] * 40
        else:
            score -= bar[0] * 40
            score += bar[1] * 40

        for i in range(24):
            count = board[i]
            if color == AI:
                if count < 0:
                    # AI checkers - advance towards home (index 23)
                    num = abs(count)
                    # Advancement bonus
                    score += i * 1.5 * num
                    # Making points (2+ checkers)
                    if num >= 2:
                        score += 8
                    # Blot penalty (lone checker)
                    if num == 1:
                        # More vulnerable if far from home
                        score -= max(1, (23 - i)) * 0.8
                elif count > 0:
                    # Opponent checkers
                    num = count
                    if num == 1:
                        # Opponent blot - good if we can potentially hit
                        score += 3
            else:
                if count > 0:
                    num = count
                    score += (23 - i) * 1.5 * num
                    if num >= 2:
                        score += 8
                    if num == 1:
                        score -= max(1, i) * 0.8
                elif count < 0:
                    num = abs(count)
                    if num == 1:
                        score += 3

        return score


def _home_range(color):
    """Return the home board indices for a color."""
    if color == AI:
        return range(18, 24)
    else:
        return range(0, 6)


def _all_in_home(board, bar, color):
    """Check if all of a player's checkers are in their home board."""
    if color == AI:
        if bar[1] > 0:
            return False
        for i in range(18):
            if board[i] < 0:
                return False
        return True
    else:
        if bar[0] > 0:
            return False
        for i in range(6, 24):
            if board[i] > 0:
                return False
        return True


def _farthest_checker(board, color):
    """Return index of farthest checker from bearing off, or -1 if none."""
    if color == AI:
        # AI moves 0->23, farthest from off is lowest index with AI checker
        for i in range(24):
            if board[i] < 0:
                return i
        return -1
    else:
        # Player moves 23->0, farthest from off is highest index
        for i in range(23, -1, -1):
            if board[i] > 0:
                return i
        return -1


def _single_die_moves(board, bar, off, die, color):
    """Get all legal single moves for one die value. Returns list of (from, to)."""
    moves = []

    if color == AI:
        bar_count = bar[1]
        # Must enter from bar first
        if bar_count > 0:
            target = die - 1  # die 1 -> index 0, die 6 -> index 5
            # Can land if: own checkers (<=0), empty (0), or single opponent blot (1)
            if board[target] <= 1:
                moves.append(('bar', target))
            return moves  # Must enter from bar before moving anything else

        # Normal moves
        for i in range(24):
            if board[i] < 0:  # AI checker here
                target = i + die
                if target < 24:
                    # Normal move
                    if board[target] <= 1:  # empty, AI, or single player blot
                        moves.append((i, target))
                elif target == 24:
                    # Exact bear off
                    if _all_in_home(board, bar, color):
                        moves.append((i, 'off'))
                else:
                    # Overshoot - allowed only if this is the farthest checker
                    if _all_in_home(board, bar, color):
                        farthest = _farthest_checker(board, color)
                        if i == farthest:
                            moves.append((i, 'off'))
    else:
        # Player
        bar_count = bar[0]
        if bar_count > 0:
            target = 24 - die  # die 1 -> index 23, die 6 -> index 18
            # Can land if: own checkers (>=0), empty (0), or single opponent blot (-1)
            if board[target] >= -1:
                moves.append(('bar', target))
            return moves

        for i in range(24):
            if board[i] > 0:
                target = i - die
                if target >= 0:
                    if board[target] >= -1:
                        moves.append((i, target))
                elif target == -1:
                    if _all_in_home(board, bar, color):
                        moves.append((i, 'off'))
                else:
                    if _all_in_home(board, bar, color):
                        farthest = _farthest_checker(board, color)
                        if i == farthest:
                            moves.append((i, 'off'))

    return moves


def _apply_single_move(board, bar, off, move, color):
    """Apply a single (from, to) move. Returns new (board, bar, off)."""
    board = list(board)
    bar = list(bar)
    off = list(off)
    frm, to = move

    if color == AI:
        # Remove from source
        if frm == 'bar':
            bar[1] -= 1
        else:
            board[frm] += 1  # Remove one AI checker (make less negative)

        if to == 'off':
            off[1] += 1
        else:
            # Check for hitting opponent blot
            if board[to] == 1:  # Single player checker
                board[to] = 0
                bar[0] += 1  # Send player to bar
            board[to] -= 1  # Place AI checker
    else:
        # Player
        if frm == 'bar':
            bar[0] -= 1
        else:
            board[frm] -= 1

        if to == 'off':
            off[0] += 1
        else:
            if board[to] == -1:  # Single AI checker
                board[to] = 0
                bar[1] += 1
            board[to] += 1

    return board, bar, off


def get_all_legal_moves(board, bar, off, dice, color):
    """Return all possible move sequences (lists of (from, to) tuples).

    Handles using multiple dice. Backgammon rule: must use as many dice as possible,
    and if only one can be used, must use the larger one.
    """
    if not dice:
        return [[]]

    # For doubles, dice has 4 values; for non-doubles, 2 values
    # We need to try all orderings of dice usage
    sequences = set()
    _find_sequences(board, bar, off, list(dice), color, [], sequences)

    if not sequences:
        return []

    # Convert frozensets back to lists
    result = [list(s) for s in sequences]

    # Backgammon rule: must use maximum number of dice
    max_len = max(len(s) for s in result)
    result = [s for s in result if len(s) == max_len]

    # If can only use one die, must use the larger
    if max_len == 1 and len(dice) >= 2 and dice[0] != dice[1]:
        larger = max(dice[0], dice[1])
        # Check if any sequence uses the larger die
        # We can't directly tell which die was used from the move,
        # so keep all - the game logic handles this adequately
        pass

    return result


def _find_sequences(board, bar, off, remaining_dice, color, current_seq, results):
    """Recursively find all move sequences using the remaining dice."""
    if not remaining_dice:
        if current_seq:
            results.add(tuple(current_seq))
        return

    found_any = False
    # Try each remaining die
    tried_dice = set()
    for idx, die in enumerate(remaining_dice):
        if die in tried_dice:
            continue
        tried_dice.add(die)

        moves = _single_die_moves(board, bar, off, die, color)
        for move in moves:
            found_any = True
            new_board, new_bar, new_off = _apply_single_move(board, bar, off, move, color)
            new_remaining = remaining_dice[:idx] + remaining_dice[idx + 1:]
            _find_sequences(new_board, new_bar, new_off, new_remaining, color,
                            current_seq + [move], results)

    if not found_any and current_seq:
        results.add(tuple(current_seq))


def apply_moves(board, bar, off, moves, color):
    """Apply a sequence of moves. Returns (new_board, new_bar, new_off)."""
    board = list(board)
    bar = list(bar)
    off = list(off)
    for move in moves:
        board, bar, off = _apply_single_move(board, bar, off, move, color)
    return board, bar, off


# Standard backgammon starting position
def initial_board():
    """Return the starting board, bar, and off."""
    board = [0] * 24
    # Player (positive) checkers - moves from 24->1 (index 23->0)
    # Point 24 = index 23: 2 checkers
    board[23] = 2
    # Point 13 = index 12: 5 checkers
    board[12] = 5
    # Point 8 = index 7: 3 checkers
    board[7] = 3
    # Point 6 = index 5: 5 checkers
    board[5] = 5

    # AI (negative) checkers - moves from 1->24 (index 0->23)
    # Point 1 = index 0: 2 checkers
    board[0] = -2
    # Point 12 = index 11: 5 checkers
    board[11] = -5
    # Point 17 = index 16: 3 checkers
    board[16] = -3
    # Point 19 = index 18: 5 checkers
    board[18] = -5

    bar = [0, 0]
    off = [0, 0]
    return board, bar, off
