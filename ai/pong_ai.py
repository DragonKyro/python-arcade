"""
Pong AI controller.
Pure game logic - no arcade imports.
"""

import random


class PongAI:
    """AI opponent for Pong with configurable difficulty."""

    DIFFICULTY_SETTINGS = {
        'easy': {
            'max_speed': 3,
            'random_offset': 40,
            'prediction': False,
            'rest_chance': 0.3,  # chance to drift toward center instead of tracking
        },
        'medium': {
            'max_speed': 5,
            'random_offset': 15,
            'prediction': True,
            'rest_chance': 0.0,
        },
        'hard': {
            'max_speed': 7,
            'random_offset': 5,
            'prediction': True,
            'rest_chance': 0.0,
        },
    }

    def __init__(self, difficulty='medium'):
        if difficulty not in self.DIFFICULTY_SETTINGS:
            difficulty = 'medium'
        self.difficulty = difficulty
        self.settings = self.DIFFICULTY_SETTINGS[difficulty]
        # Cached random offset, refreshed periodically
        self._offset = 0.0
        self._offset_timer = 0

    def _refresh_offset(self):
        """Generate a new random aiming offset."""
        r = self.settings['random_offset']
        self._offset = random.uniform(-r, r)

    def _predict_y(self, ball_x, ball_y, ball_dx, ball_dy, target_x, screen_height):
        """Predict the ball's y-position when it reaches target_x, accounting for wall bounces."""
        if ball_dx == 0:
            return ball_y

        # Time to reach target_x
        t = (target_x - ball_x) / ball_dx
        if t < 0:
            return ball_y

        # Predicted y before bouncing
        predicted_y = ball_y + ball_dy * t

        # Simulate bounces off top/bottom walls
        # The ball bounces between 0 and screen_height
        if screen_height <= 0:
            return ball_y

        # Normalize into the bounce cycle
        # Each full cycle is 2 * screen_height
        cycle = 2 * screen_height
        predicted_y = predicted_y % cycle
        if predicted_y < 0:
            predicted_y += cycle

        if predicted_y > screen_height:
            predicted_y = cycle - predicted_y

        return predicted_y

    def get_move(self, paddle_y, ball_x, ball_y, ball_dx, ball_dy,
                 screen_height, paddle_height):
        """Return the target y-position for the AI paddle center.

        Parameters
        ----------
        paddle_y : float
            Current center-y of the AI paddle.
        ball_x, ball_y : float
            Current ball position.
        ball_dx, ball_dy : float
            Current ball velocity components.
        screen_height : float
            Height of the play area.
        paddle_height : float
            Height of the AI paddle.

        Returns
        -------
        float
            Target y for the paddle center, clamped by max_speed from current position.
        """
        max_speed = self.settings['max_speed']

        # Refresh random offset periodically
        self._offset_timer += 1
        if self._offset_timer > 30:
            self._offset_timer = 0
            self._refresh_offset()

        # Determine target y
        if ball_dx <= 0:
            # Ball moving away from AI
            if self.difficulty == 'easy':
                # Drift toward center when ball going away
                target_y = screen_height / 2
            else:
                # Stay roughly where we are, slight drift to center
                target_y = paddle_y + (screen_height / 2 - paddle_y) * 0.05
        else:
            # Ball coming toward AI
            if self.difficulty == 'easy':
                # Sometimes rest at center instead of tracking
                if random.random() < self.settings['rest_chance']:
                    target_y = screen_height / 2
                else:
                    target_y = ball_y + self._offset
            elif self.settings['prediction']:
                # Predict where the ball will arrive at the AI paddle x
                # We don't know paddle_x here, so predict for right side
                # The caller should handle the exact x; we predict for
                # screen_width equivalent (ball is heading right)
                target_y = self._predict_y(
                    ball_x, ball_y, ball_dx, ball_dy,
                    ball_x + 400,  # rough estimate; works because prediction scales
                    screen_height,
                ) + self._offset
            else:
                target_y = ball_y + self._offset

        # Clamp target within screen bounds (keeping paddle fully visible)
        half = paddle_height / 2
        target_y = max(half, min(screen_height - half, target_y))

        # Apply speed cap — paddle can only move max_speed per frame
        diff = target_y - paddle_y
        if abs(diff) > max_speed:
            target_y = paddle_y + max_speed * (1 if diff > 0 else -1)

        return target_y
