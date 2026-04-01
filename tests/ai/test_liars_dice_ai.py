"""Tests for ai.liars_dice_ai module."""

import pytest
from ai.liars_dice_ai import LiarsDiceAI


@pytest.fixture(params=['easy', 'medium', 'hard'])
def ai(request):
    return LiarsDiceAI(difficulty=request.param)


class TestReturnFormat:
    def test_opening_bid_format(self, ai):
        action = ai.decide(own_dice=[2, 3, 4, 5, 6], num_total_dice=10,
                           current_bid=None, num_players_remaining=2)
        assert action[0] == 'bid'
        assert len(action) == 3
        _, qty, face = action
        assert isinstance(qty, int)
        assert isinstance(face, int)
        assert qty >= 1
        assert 1 <= face <= 6

    def test_response_is_bid_or_liar(self, ai):
        action = ai.decide(own_dice=[1, 2, 3, 4, 5], num_total_dice=10,
                           current_bid=(3, 4), num_players_remaining=2)
        assert action[0] in ('bid', 'liar')
        if action[0] == 'bid':
            assert len(action) == 3
        else:
            assert len(action) == 1


class TestBidIsHigher:
    def test_bid_raises_quantity_or_face(self, ai):
        """A new bid must be higher than the current bid."""
        current_bid = (2, 3)
        for _ in range(20):
            action = ai.decide(own_dice=[3, 3, 3, 1, 1], num_total_dice=10,
                               current_bid=current_bid, num_players_remaining=2)
            if action[0] == 'bid':
                _, qty, face = action
                # Valid raise: higher qty on same face, or same+ qty on higher face
                assert (qty > current_bid[0]) or (face > current_bid[1] and qty >= current_bid[0]), \
                    f"Bid ({qty}, {face}) is not higher than ({current_bid[0]}, {current_bid[1]})"
                break
        # If it always calls liar in 20 tries, that's also valid behavior


class TestOpeningBid:
    def test_first_bid_is_valid(self, ai):
        for _ in range(10):
            action = ai.decide(own_dice=[2, 4, 4, 6, 1], num_total_dice=10,
                               current_bid=None, num_players_remaining=3)
            assert action[0] == 'bid'
            _, qty, face = action
            assert qty >= 1
            assert qty <= 10
            assert 1 <= face <= 6


class TestCallsLiarOnImpossible:
    def test_calls_liar_on_impossible_bid(self):
        """If bid exceeds total dice, AI should call liar."""
        ai = LiarsDiceAI(difficulty='medium')
        # Bid of 11 sixes with only 10 dice total - impossible
        action = ai.decide(own_dice=[1, 2, 3, 4, 5], num_total_dice=10,
                           current_bid=(11, 6), num_players_remaining=2)
        assert action == ('liar',)

    def test_calls_liar_on_very_unlikely_bid(self):
        """High bid with no matching dice should often trigger liar call."""
        ai = LiarsDiceAI(difficulty='easy')  # easy is most conservative
        # AI has no 5s and no 1s, bid is 8 fives out of 10 dice
        liar_count = 0
        for _ in range(20):
            action = ai.decide(own_dice=[2, 2, 3, 3, 4], num_total_dice=10,
                               current_bid=(8, 5), num_players_remaining=2)
            if action[0] == 'liar':
                liar_count += 1
        assert liar_count > 10, "AI should frequently call liar on unlikely bids"


class TestBidQuantityBounded:
    def test_bid_does_not_exceed_total_dice(self, ai):
        for _ in range(20):
            action = ai.decide(own_dice=[1, 1, 1, 1, 1], num_total_dice=10,
                               current_bid=(2, 3), num_players_remaining=2)
            if action[0] == 'bid':
                _, qty, face = action
                assert qty <= 10
