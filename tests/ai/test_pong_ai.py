"""Tests for ai.pong_ai module."""

import pytest
from ai.pong_ai import PongAI


@pytest.fixture(params=['easy', 'medium', 'hard'])
def ai(request):
    return PongAI(difficulty=request.param)


class TestReturnType:
    def test_returns_numeric(self, ai):
        result = ai.get_move(
            paddle_y=300, ball_x=100, ball_y=200,
            ball_dx=5, ball_dy=3,
            screen_height=600, paddle_height=80,
        )
        assert isinstance(result, (int, float))

    def test_returns_within_screen(self, ai):
        result = ai.get_move(
            paddle_y=300, ball_x=100, ball_y=200,
            ball_dx=5, ball_dy=3,
            screen_height=600, paddle_height=80,
        )
        half = 80 / 2
        assert half <= result <= 600 - half + ai.settings['max_speed']


class TestDifficultyDifferences:
    def test_easy_has_lower_max_speed(self):
        easy = PongAI('easy')
        hard = PongAI('hard')
        assert easy.settings['max_speed'] < hard.settings['max_speed']

    def test_easy_has_more_random_offset(self):
        easy = PongAI('easy')
        hard = PongAI('hard')
        assert easy.settings['random_offset'] > hard.settings['random_offset']

    def test_easy_no_prediction(self):
        easy = PongAI('easy')
        assert easy.settings['prediction'] is False

    def test_hard_has_prediction(self):
        hard = PongAI('hard')
        assert hard.settings['prediction'] is True

    def test_invalid_difficulty_defaults_to_medium(self):
        ai = PongAI('impossible')
        assert ai.difficulty == 'medium'


class TestBallTracking:
    def test_tracks_ball_moving_toward_ai(self):
        """When ball moves toward AI (dx > 0), target should shift toward ball_y."""
        ai = PongAI('hard')
        # Ball moving right toward AI
        result = ai.get_move(
            paddle_y=300, ball_x=200, ball_y=100,
            ball_dx=5, ball_dy=0,
            screen_height=600, paddle_height=80,
        )
        # Target should be moving toward ball_y (100), so less than current paddle_y (300)
        assert result < 300

    def test_ball_moving_away(self):
        """When ball moves away (dx <= 0), easy AI drifts toward center."""
        ai = PongAI('easy')
        result = ai.get_move(
            paddle_y=100, ball_x=200, ball_y=500,
            ball_dx=-5, ball_dy=0,
            screen_height=600, paddle_height=80,
        )
        # Easy AI drifts toward center (300) when ball moves away
        assert result > 100  # moving toward center

    def test_speed_cap_applied(self):
        """Movement should be limited by max_speed."""
        ai = PongAI('easy')
        max_speed = ai.settings['max_speed']
        result = ai.get_move(
            paddle_y=300, ball_x=200, ball_y=100,
            ball_dx=5, ball_dy=0,
            screen_height=600, paddle_height=80,
        )
        assert abs(result - 300) <= max_speed + 0.01
