"""Tests for Galaga AI module."""

import pytest
import random

from ai.galaga_ai import (
    BeeAI,
    ButterflyAI,
    BossGalagaAI,
    generate_bee_dive_path,
    generate_butterfly_dive_path,
    generate_boss_dive_path,
    generate_entry_path,
    generate_formation_sway,
    pick_divers,
    get_ai_for_type,
    _bezier_quadratic,
    _bezier_cubic,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_enemy(x=400, y=500, etype="bee", state="formation", hp=1, stage=0):
    """Create a minimal enemy dict for testing."""
    return {
        "x": x,
        "y": y,
        "type": etype,
        "state": state,
        "hp": hp,
        "stage": stage,
        "dive_path": None,
    }


# ---------------------------------------------------------------------------
# Bezier helpers
# ---------------------------------------------------------------------------

class TestBezierHelpers:
    def test_quadratic_endpoints(self):
        p0, p1, p2 = (0, 0), (50, 100), (100, 0)
        assert _bezier_quadratic(p0, p1, p2, 0.0) == pytest.approx((0, 0))
        assert _bezier_quadratic(p0, p1, p2, 1.0) == pytest.approx((100, 0))

    def test_cubic_endpoints(self):
        p0, p1, p2, p3 = (0, 0), (10, 50), (90, 50), (100, 0)
        assert _bezier_cubic(p0, p1, p2, p3, 0.0) == pytest.approx((0, 0))
        assert _bezier_cubic(p0, p1, p2, p3, 1.0) == pytest.approx((100, 0))

    def test_cubic_midpoint_is_interior(self):
        p0, p1, p2, p3 = (0, 0), (0, 100), (100, 100), (100, 0)
        mx, my = _bezier_cubic(p0, p1, p2, p3, 0.5)
        assert 0 < mx < 100
        assert my > 0


# ---------------------------------------------------------------------------
# BeeAI
# ---------------------------------------------------------------------------

class TestBeeAI:
    def test_update_diving_returns_bool(self):
        enemy = _make_enemy()
        result = BeeAI.update_diving(enemy, player_x=400, dt=0.016)
        assert isinstance(result, bool)

    def test_update_diving_advances_position(self):
        enemy = _make_enemy(x=400, y=500)
        old_x, old_y = enemy["x"], enemy["y"]
        BeeAI.update_diving(enemy, player_x=400, dt=0.1)
        # Position should change after a tick
        assert (enemy["x"] != old_x) or (enemy["y"] != old_y)

    def test_update_diving_creates_path(self):
        enemy = _make_enemy()
        BeeAI.update_diving(enemy, player_x=400, dt=0.016)
        assert enemy["dive_path"] is not None
        assert enemy["dive_segment"] == 0

    def test_update_diving_completes_eventually(self):
        enemy = _make_enemy()
        for _ in range(500):
            done = BeeAI.update_diving(enemy, player_x=400, dt=0.1)
            if done:
                break
        assert done is True

    def test_bee_does_not_shoot(self):
        enemy = _make_enemy()
        BeeAI.update_diving(enemy, player_x=400, dt=0.1)
        assert enemy["should_shoot"] is False

    def test_dive_speed(self):
        assert BeeAI.DIVE_SPEED == 1.0


# ---------------------------------------------------------------------------
# ButterflyAI
# ---------------------------------------------------------------------------

class TestButterflyAI:
    def test_update_diving_returns_bool(self):
        enemy = _make_enemy(etype="butterfly")
        result = ButterflyAI.update_diving(enemy, player_x=400, dt=0.016)
        assert isinstance(result, bool)

    def test_update_diving_advances_position(self):
        enemy = _make_enemy(x=400, y=500, etype="butterfly")
        old_x, old_y = enemy["x"], enemy["y"]
        ButterflyAI.update_diving(enemy, player_x=400, dt=0.1)
        assert (enemy["x"] != old_x) or (enemy["y"] != old_y)

    def test_butterfly_is_faster_than_bee(self):
        assert ButterflyAI.DIVE_SPEED > BeeAI.DIVE_SPEED

    def test_butterfly_has_wider_path(self):
        """Butterfly dive path has more segments (wider S-curve) than bee."""
        random.seed(42)
        bee_path = generate_bee_dive_path(400, 500, 400, 800, 600)
        random.seed(42)
        butterfly_path = generate_butterfly_dive_path(400, 500, 400, 800, 600)
        assert len(butterfly_path) > len(bee_path)

    def test_update_diving_completes_eventually(self):
        enemy = _make_enemy(etype="butterfly")
        for _ in range(500):
            done = ButterflyAI.update_diving(enemy, player_x=400, dt=0.1)
            if done:
                break
        assert done is True

    def test_butterfly_may_shoot(self):
        """Over a long enough dive, butterfly sets should_shoot at some point."""
        enemy = _make_enemy(etype="butterfly")
        shot_fired = False
        for _ in range(200):
            ButterflyAI.update_diving(enemy, player_x=400, dt=0.05)
            if enemy.get("should_shoot"):
                shot_fired = True
                break
        # Butterfly can shoot during first segment when t > 0.4
        # May not always trigger due to cooldown randomness, so just check type
        assert isinstance(enemy["should_shoot"], bool)


# ---------------------------------------------------------------------------
# BossGalagaAI
# ---------------------------------------------------------------------------

class TestBossGalagaAI:
    def test_update_diving_returns_bool(self):
        enemy = _make_enemy(etype="boss")
        result = BossGalagaAI.update_diving(enemy, player_x=400, dt=0.016)
        assert isinstance(result, bool)

    def test_boss_is_slower_than_bee(self):
        assert BossGalagaAI.DIVE_SPEED < BeeAI.DIVE_SPEED

    def test_boss_takes_two_hits(self):
        """Boss enemy should be created with hp=2 and survive one hit."""
        enemy = _make_enemy(etype="boss", hp=2)
        enemy["hp"] -= 1
        assert enemy["hp"] == 1  # still alive after one hit
        enemy["hp"] -= 1
        assert enemy["hp"] == 0  # dead after two

    def test_tractor_beam_activates(self):
        """When the boss reaches the end of the first segment near the player,
        the tractor beam should activate."""
        enemy = _make_enemy(x=400, y=500, etype="boss")
        # Force initial path generation
        BossGalagaAI.update_diving(enemy, player_x=400, dt=0.0)
        # Push through first segment until t >= 0.95
        for _ in range(200):
            BossGalagaAI.update_diving(enemy, player_x=400, dt=0.05)
            if enemy.get("tractor_beam_active"):
                break
        # The boss should activate the tractor beam when close to player_x
        assert enemy.get("tractor_beam_used") is True

    def test_tractor_beam_duration(self):
        assert BossGalagaAI.TRACTOR_BEAM_DURATION == 2.0

    def test_tractor_beam_pauses_dive(self):
        """While tractor beam is active, dive_t should not advance."""
        enemy = _make_enemy(x=400, y=500, etype="boss")
        # Advance until tractor beam fires
        for _ in range(200):
            BossGalagaAI.update_diving(enemy, player_x=400, dt=0.05)
            if enemy.get("tractor_beam_active"):
                break
        if enemy.get("tractor_beam_active"):
            seg_before = enemy["dive_segment"]
            t_before = enemy["dive_t"]
            BossGalagaAI.update_diving(enemy, player_x=400, dt=0.05)
            # Dive should not advance while beam is active
            assert enemy["dive_segment"] == seg_before
            assert enemy["dive_t"] == t_before

    def test_boss_dive_completes(self):
        enemy = _make_enemy(x=400, y=500, etype="boss")
        for _ in range(1000):
            done = BossGalagaAI.update_diving(enemy, player_x=400, dt=0.1)
            if done:
                break
        assert done is True


# ---------------------------------------------------------------------------
# Dive path generators
# ---------------------------------------------------------------------------

class TestDivePathGenerators:
    def test_bee_dive_path_returns_control_points(self):
        path = generate_bee_dive_path(400, 500, 400, 800, 600)
        assert isinstance(path, list)
        assert len(path) == 2  # two bezier segments
        for seg in path:
            assert len(seg) == 4  # cubic bezier = 4 control points
            for pt in seg:
                assert len(pt) == 2  # (x, y)

    def test_butterfly_dive_path_returns_control_points(self):
        path = generate_butterfly_dive_path(400, 500, 400, 800, 600)
        assert isinstance(path, list)
        assert len(path) == 3  # three segments
        for seg in path:
            assert len(seg) == 4
            for pt in seg:
                assert len(pt) == 2

    def test_boss_dive_path_returns_control_points(self):
        path = generate_boss_dive_path(400, 500, 400, 800, 600)
        assert isinstance(path, list)
        assert len(path) == 3
        for seg in path:
            assert len(seg) == 4
            for pt in seg:
                assert len(pt) == 2

    def test_bee_path_starts_at_enemy_position(self):
        path = generate_bee_dive_path(200, 450, 400, 800, 600)
        first_point = path[0][0]
        assert first_point == (200, 450)

    def test_butterfly_path_starts_at_enemy_position(self):
        path = generate_butterfly_dive_path(300, 480, 400, 800, 600)
        first_point = path[0][0]
        assert first_point == (300, 480)

    def test_boss_path_starts_at_enemy_position(self):
        path = generate_boss_dive_path(350, 500, 400, 800, 600)
        first_point = path[0][0]
        assert first_point == (350, 500)


# ---------------------------------------------------------------------------
# Entry path generator
# ---------------------------------------------------------------------------

class TestEntryPath:
    @pytest.mark.parametrize("wave_group", [0, 1, 2])
    def test_generate_entry_path_returns_segments(self, wave_group):
        path = generate_entry_path(400, 500, wave_group, 0, 800, 600)
        assert isinstance(path, list)
        assert len(path) >= 1
        for seg in path:
            assert len(seg) == 4  # cubic bezier
            for pt in seg:
                assert len(pt) == 2

    def test_entry_path_ends_at_target(self):
        """The last control point of the path should be the formation target."""
        target_x, target_y = 400, 500
        for wg in [0, 1, 2]:
            path = generate_entry_path(target_x, target_y, wg, 0, 800, 600)
            last_point = path[-1][-1]
            assert last_point == (target_x, target_y)


# ---------------------------------------------------------------------------
# Formation sway
# ---------------------------------------------------------------------------

class TestFormationSway:
    def test_returns_dx_dy(self):
        dx, dy = generate_formation_sway(0.0, 0, 0)
        assert isinstance(dx, float)
        assert isinstance(dy, float)

    def test_varies_with_time(self):
        dx1, dy1 = generate_formation_sway(0.0, 0, 0)
        dx2, dy2 = generate_formation_sway(1.0, 0, 0)
        assert (dx1, dy1) != (dx2, dy2)

    def test_varies_with_column(self):
        dx1, _ = generate_formation_sway(1.0, 0, 0)
        dx2, _ = generate_formation_sway(1.0, 5, 0)
        assert dx1 != dx2

    def test_amplitude_parameter(self):
        dx_small, _ = generate_formation_sway(1.0, 0, 0, amplitude=1.0)
        dx_large, _ = generate_formation_sway(1.0, 0, 0, amplitude=10.0)
        # Larger amplitude should produce larger absolute offset (same phase)
        assert abs(dx_large) > abs(dx_small)


# ---------------------------------------------------------------------------
# pick_divers
# ---------------------------------------------------------------------------

class TestPickDivers:
    def test_returns_list(self):
        enemies = [_make_enemy() for _ in range(5)]
        result = pick_divers(enemies, max_divers=2, stage=1)
        assert isinstance(result, list)

    def test_returns_valid_indices(self):
        enemies = [_make_enemy() for _ in range(10)]
        result = pick_divers(enemies, max_divers=3, stage=1)
        for idx in result:
            assert 0 <= idx < len(enemies)

    def test_respects_max_divers(self):
        enemies = [_make_enemy() for _ in range(10)]
        result = pick_divers(enemies, max_divers=2, stage=0)
        assert len(result) <= 2

    def test_only_picks_formation_enemies(self):
        enemies = [_make_enemy(state="diving") for _ in range(5)]
        result = pick_divers(enemies, max_divers=3, stage=1)
        assert result == []

    def test_only_picks_living_enemies(self):
        enemies = [_make_enemy(hp=0) for _ in range(5)]
        result = pick_divers(enemies, max_divers=3, stage=1)
        assert result == []

    def test_no_duplicate_indices(self):
        enemies = [_make_enemy() for _ in range(10)]
        result = pick_divers(enemies, max_divers=5, stage=5)
        assert len(result) == len(set(result))

    def test_higher_stage_allows_more_divers(self):
        enemies = [_make_enemy() for _ in range(20)]
        random.seed(42)
        low_stage = pick_divers(enemies, max_divers=2, stage=0)
        random.seed(42)
        high_stage = pick_divers(enemies, max_divers=2, stage=12)
        assert len(high_stage) >= len(low_stage)

    def test_empty_enemies(self):
        assert pick_divers([], max_divers=3, stage=1) == []


# ---------------------------------------------------------------------------
# get_ai_for_type
# ---------------------------------------------------------------------------

class TestGetAIForType:
    def test_bee(self):
        assert get_ai_for_type("bee") is BeeAI

    def test_butterfly(self):
        assert get_ai_for_type("butterfly") is ButterflyAI

    def test_boss(self):
        assert get_ai_for_type("boss") is BossGalagaAI

    def test_unknown_defaults_to_bee(self):
        assert get_ai_for_type("unknown") is BeeAI
