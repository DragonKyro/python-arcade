"""Tests for ai.battleship_ai module."""

import pytest
from ai.battleship_ai import BattleshipAI


@pytest.fixture
def ai():
    return BattleshipAI(grid_size=10)


STANDARD_SHIPS = [5, 4, 3, 3, 2]


class TestPlaceShips:
    def test_all_ships_placed(self, ai):
        ai.place_ships(STANDARD_SHIPS)
        assert len(ai.ships) == len(STANDARD_SHIPS)

    def test_ship_sizes_correct(self, ai):
        ai.place_ships(STANDARD_SHIPS)
        for ship, expected_size in zip(ai.ships, STANDARD_SHIPS):
            assert len(ship) == expected_size

    def test_no_overlaps(self, ai):
        ai.place_ships(STANDARD_SHIPS)
        all_cells = []
        for ship in ai.ships:
            all_cells.extend(ship)
        assert len(all_cells) == len(set(all_cells)), "Ships overlap"

    def test_within_grid(self, ai):
        ai.place_ships(STANDARD_SHIPS)
        for ship in ai.ships:
            for r, c in ship:
                assert 0 <= r < ai.grid_size
                assert 0 <= c < ai.grid_size

    def test_board_has_ship_cells(self, ai):
        ai.place_ships(STANDARD_SHIPS)
        ship_count = sum(
            1 for r in range(ai.grid_size) for c in range(ai.grid_size)
            if ai.board[r][c] == BattleshipAI.SHIP
        )
        assert ship_count == sum(STANDARD_SHIPS)


class TestGetShot:
    def test_returns_valid_coordinates(self, ai):
        shot = ai.get_shot()
        assert shot is not None
        r, c = shot
        assert 0 <= r < ai.grid_size
        assert 0 <= c < ai.grid_size

    def test_no_duplicate_shots(self, ai):
        shots = set()
        for _ in range(20):
            shot = ai.get_shot()
            assert shot not in shots, "Duplicate shot returned"
            shots.add(shot)
            ai.report_result(shot[0], shot[1], False)

    def test_exhausts_all_cells(self, ai):
        """AI should be able to fire at every cell without error."""
        total = ai.grid_size * ai.grid_size
        for _ in range(total):
            shot = ai.get_shot()
            assert shot is not None
            ai.report_result(shot[0], shot[1], False)
        # After all cells exhausted
        assert ai.get_shot() is None


class TestHuntToTarget:
    def test_target_mode_after_hit(self, ai):
        shot = ai.get_shot()
        ai.report_result(shot[0], shot[1], hit=True)
        assert ai.mode == "target"

    def test_next_shot_adjacent_after_hit(self, ai):
        r, c = 5, 5
        # Force a specific first shot
        ai.all_shots.add((r, c))
        ai.report_result(r, c, hit=True)
        next_shot = ai.get_shot()
        nr, nc = next_shot
        # Should be orthogonally adjacent to the hit
        assert abs(nr - r) + abs(nc - c) == 1


class TestReceiveShot:
    def test_miss(self, ai):
        ai.place_ships([2])
        # Find an empty cell
        for r in range(ai.grid_size):
            for c in range(ai.grid_size):
                if ai.board[r][c] == BattleshipAI.EMPTY:
                    hit, sunk = ai.receive_shot(r, c)
                    assert hit is False
                    assert sunk is None
                    return

    def test_hit_not_sunk(self, ai):
        ai.place_ships([3])
        ship = ai.ships[0]
        cell = list(ship)[0]
        hit, sunk = ai.receive_shot(cell[0], cell[1])
        assert hit is True
        assert sunk is None  # ship has 3 cells, only 1 hit

    def test_hit_and_sunk(self, ai):
        ai.place_ships([1])
        ship = ai.ships[0]
        cell = list(ship)[0]
        hit, sunk = ai.receive_shot(cell[0], cell[1])
        assert hit is True
        assert sunk is not None
        assert sunk == ship


class TestAllShipsSunk:
    def test_not_sunk_initially(self, ai):
        ai.place_ships(STANDARD_SHIPS)
        assert ai.all_ships_sunk() is False

    def test_sunk_after_all_hit(self, ai):
        ai.place_ships([2])
        for ship in ai.ships:
            for r, c in ship:
                ai.receive_shot(r, c)
        assert ai.all_ships_sunk() is True

    def test_no_ships_means_sunk(self, ai):
        # No ships placed: all_ships_sunk should be True (no SHIP cells)
        assert ai.all_ships_sunk() is True
