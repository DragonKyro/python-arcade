import copy


class MancalaAI:
    """Mancala (Kalah variant) AI using minimax with alpha-beta pruning."""

    DEPTH_LIMIT = 8

    def get_move(self, pits, stores, ai_side):
        """Return the best pit index (0-5) for the AI to play.

        Args:
            pits: [player_pits(6), ai_pits(6)] — each a list of 6 ints.
            stores: [player_store, ai_store].
            ai_side: 1 (AI is second row).

        Returns:
            int: pit index 0-5 for the AI's chosen move.
        """
        best_score = float("-inf")
        best_move = None

        for pit in range(6):
            if pits[ai_side][pit] == 0:
                continue
            new_pits, new_stores, extra_turn, _ = sow(pits, stores, ai_side, pit)
            if extra_turn:
                # AI gets another turn — maximize again
                score = self._minimax(
                    new_pits, new_stores, self.DEPTH_LIMIT - 1,
                    float("-inf"), float("inf"), True, ai_side,
                )
            else:
                score = self._minimax(
                    new_pits, new_stores, self.DEPTH_LIMIT - 1,
                    float("-inf"), float("inf"), False, ai_side,
                )
            if score > best_score:
                best_score = score
                best_move = pit

        return best_move

    def _minimax(self, pits, stores, depth, alpha, beta, maximizing, ai_side):
        """Minimax with alpha-beta pruning.

        maximizing=True means it is the AI's turn.
        """
        player_side = 1 - ai_side

        # Terminal check: if either side is empty the game is over
        if all(s == 0 for s in pits[0]) or all(s == 0 for s in pits[1]):
            # Remaining stones go to the respective side's store
            final_stores = list(stores)
            for side in range(2):
                final_stores[side] += sum(pits[side])
            return self._evaluate(final_stores, ai_side)

        if depth == 0:
            return self._evaluate(stores, ai_side)

        current_side = ai_side if maximizing else player_side

        if maximizing:
            max_eval = float("-inf")
            for pit in range(6):
                if pits[current_side][pit] == 0:
                    continue
                new_pits, new_stores, extra_turn, _ = sow(
                    pits, stores, current_side, pit
                )
                if extra_turn:
                    val = self._minimax(
                        new_pits, new_stores, depth - 1, alpha, beta, True, ai_side
                    )
                else:
                    val = self._minimax(
                        new_pits, new_stores, depth - 1, alpha, beta, False, ai_side
                    )
                max_eval = max(max_eval, val)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float("inf")
            for pit in range(6):
                if pits[current_side][pit] == 0:
                    continue
                new_pits, new_stores, extra_turn, _ = sow(
                    pits, stores, current_side, pit
                )
                if extra_turn:
                    val = self._minimax(
                        new_pits, new_stores, depth - 1, alpha, beta, False, ai_side
                    )
                else:
                    val = self._minimax(
                        new_pits, new_stores, depth - 1, alpha, beta, True, ai_side
                    )
                min_eval = min(min_eval, val)
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return min_eval

    @staticmethod
    def _evaluate(stores, ai_side):
        """Evaluate board from AI's perspective: AI store minus opponent store."""
        player_side = 1 - ai_side
        return stores[ai_side] - stores[player_side]


def sow(pits, stores, side, pit_index):
    """Sow stones from the given pit using Kalah rules.

    Args:
        pits: [side0_pits(6), side1_pits(6)].
        stores: [side0_store, side1_store].
        side: 0 or 1 — the side that is moving.
        pit_index: 0-5 — which pit on that side to sow from.

    Returns:
        (new_pits, new_stores, extra_turn, capture_happened)
    """
    new_pits = [list(row) for row in pits]
    new_stores = list(stores)

    stones = new_pits[side][pit_index]
    new_pits[side][pit_index] = 0

    current_side = side
    current_pit = pit_index
    extra_turn = False
    capture_happened = False
    opponent = 1 - side

    while stones > 0:
        # Advance to the next position counter-clockwise
        current_pit += 1

        if current_side == side and current_pit == 6:
            # Reached own store
            new_stores[side] += 1
            stones -= 1
            if stones == 0:
                extra_turn = True
                break
            # Move to opponent's side, starting at pit 0
            current_side = opponent
            current_pit = 0
            new_pits[current_side][current_pit] += 1
            stones -= 1
        elif current_side == opponent and current_pit == 6:
            # Skip opponent's store, go back to own side
            current_side = side
            current_pit = 0
            new_pits[current_side][current_pit] += 1
            stones -= 1
        else:
            new_pits[current_side][current_pit] += 1
            stones -= 1

    # Check capture: last stone lands in an empty pit on the sowing side
    if (
        not extra_turn
        and current_side == side
        and 0 <= current_pit < 6
        and new_pits[side][current_pit] == 1
    ):
        opposite_pit = 5 - current_pit
        if new_pits[opponent][opposite_pit] > 0:
            capture_happened = True
            captured = new_pits[opponent][opposite_pit] + new_pits[side][current_pit]
            new_stores[side] += captured
            new_pits[opponent][opposite_pit] = 0
            new_pits[side][current_pit] = 0

    return (new_pits, new_stores, extra_turn, capture_happened)
