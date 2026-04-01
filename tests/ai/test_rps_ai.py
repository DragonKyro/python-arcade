"""Tests for ai.rps_ai module."""

import pytest
from ai.rps_ai import RPSAI, VALID_MOVES, COUNTERS


@pytest.fixture
def ai():
    return RPSAI()


class TestBasicValidity:
    def test_returns_valid_move_empty_history(self, ai):
        move = ai.get_move([])
        assert move in VALID_MOVES

    def test_returns_valid_move_with_history(self, ai):
        move = ai.get_move(["rock", "paper", "scissors"])
        assert move in VALID_MOVES

    def test_returns_string(self, ai):
        move = ai.get_move([])
        assert isinstance(move, str)


class TestFrequencyCounter:
    def test_counters_all_rock(self, ai):
        """If history is all 'rock', AI should return 'paper'."""
        history = ["rock"] * 10
        move = ai.get_move(history)
        assert move == "paper"

    def test_counters_all_paper(self, ai):
        history = ["paper"] * 10
        move = ai.get_move(history)
        assert move == "scissors"

    def test_counters_all_scissors(self, ai):
        history = ["scissors"] * 10
        move = ai.get_move(history)
        assert move == "rock"

    def test_counters_most_frequent(self, ai):
        # rock appears 5 times, paper 3, scissors 2
        history = ["rock"] * 5 + ["paper"] * 3 + ["scissors"] * 2
        move = ai.get_move(history)
        assert move == COUNTERS["rock"]  # paper

    def test_single_move_history(self, ai):
        for m in VALID_MOVES:
            result = ai.get_move([m])
            assert result == COUNTERS[m]
