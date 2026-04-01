"""
AI for Ludo.
Pure Python, no arcade imports.

Heuristic-based AI that decides which piece to move given the current board state.
"""

import random


class LudoAI:
    """Ludo AI using heuristic scoring to choose which piece to move."""

    def choose_piece(self, pieces, dice, board_state):
        """Choose which piece index to move.

        Args:
            pieces: list of dicts for this player's pieces, each with:
                - "state": "home", "track", "finish_lane", "finished"
                - "track_pos": int (0-51 global position on track, or -1)
                - "finish_pos": int (0-5 position in finish lane, or -1)
                - "steps_from_entry": int (how many steps taken since entering track)
            dice: int, the dice roll value (1-6).
            board_state: dict with:
                - "opponent_positions": list of global track positions occupied by opponents
                - "safe_squares": set of global track positions that are safe
                - "finish_lane_length": int (6)
                - "track_length": int (52)
                - "player_entry": int (global track entry position for this player)
                - "steps_to_finish_entry": int (steps from entry to finish lane entrance)

        Returns:
            int: index of the piece to move (0-3), or -1 if no valid move.
        """
        valid_moves = self._get_valid_moves(pieces, dice, board_state)
        if not valid_moves:
            return -1

        best_idx = -1
        best_score = float("-inf")

        for idx in valid_moves:
            score = self._score_move(idx, pieces, dice, board_state)
            if score > best_score:
                best_score = score
                best_idx = idx

        return best_idx

    def _get_valid_moves(self, pieces, dice, board_state):
        """Return list of piece indices that can legally move."""
        valid = []
        for i, p in enumerate(pieces):
            if p["state"] == "finished":
                continue
            if p["state"] == "home":
                if dice == 6:
                    valid.append(i)
            elif p["state"] == "track":
                steps_after = p["steps_from_entry"] + dice
                steps_to_finish = board_state["steps_to_finish_entry"]
                finish_len = board_state["finish_lane_length"]
                if steps_after <= steps_to_finish + finish_len:
                    valid.append(i)
            elif p["state"] == "finish_lane":
                new_finish = p["finish_pos"] + dice
                if new_finish <= board_state["finish_lane_length"]:
                    valid.append(i)
        return valid

    def _score_move(self, idx, pieces, dice, board_state):
        """Score a potential move. Higher is better."""
        p = pieces[idx]
        score = 0.0
        opponents = board_state["opponent_positions"]
        safe = board_state["safe_squares"]
        track_len = board_state["track_length"]
        steps_to_finish = board_state["steps_to_finish_entry"]
        finish_len = board_state["finish_lane_length"]

        if p["state"] == "home":
            # Entering the track is generally good
            score += 50.0
            entry = board_state["player_entry"]
            if entry in opponents:
                # Can capture on entry
                score += 80.0
            return score

        if p["state"] == "finish_lane":
            new_finish = p["finish_pos"] + dice
            if new_finish == finish_len:
                # Finishing a piece is highest priority
                score += 200.0
            else:
                score += 100.0 + new_finish * 5
            return score

        # Track movement
        steps_after = p["steps_from_entry"] + dice
        new_global = (board_state["player_entry"] + steps_after) % track_len

        if steps_after > steps_to_finish:
            # Entering finish lane
            finish_pos = steps_after - steps_to_finish
            if finish_pos == finish_len:
                score += 200.0  # Finishing
            else:
                score += 100.0 + finish_pos * 5
            return score

        # Check for capture
        if new_global in opponents and new_global not in safe:
            score += 80.0

        # Prefer advancing pieces closer to finish
        progress = steps_after / steps_to_finish
        score += progress * 40.0

        # Avoid landing on unsafe squares with opponents nearby
        if new_global not in safe:
            # Check if opponents are within 6 squares behind us
            danger = 0
            for opp_pos in opponents:
                for d in range(1, 7):
                    if (opp_pos + d) % track_len == new_global:
                        danger += 1
            if danger > 0:
                score -= danger * 15.0
        else:
            score += 10.0  # Safe square bonus

        # Slight randomness to avoid predictability
        score += random.uniform(0, 3.0)

        return score
