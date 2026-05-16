"""Tests for mudgame/systems/loot.py — pure loot resolution."""

import random
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path bootstrap (same pattern as other test files in this project)
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mudgame.systems.loot import resolve_loot_drops, resolve_credit_drop


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rng(seed: int) -> random.Random:
    return random.Random(seed)


# ---------------------------------------------------------------------------
# resolve_loot_drops
# ---------------------------------------------------------------------------

class TestResolveLootDrops:
    def test_empty_table_returns_empty(self):
        assert resolve_loot_drops([]) == []

    def test_certain_drop_always_included(self):
        table = [{"item": "iron_shard", "chance": 1.0}]
        result = resolve_loot_drops(table)
        assert result == ["iron_shard"]

    def test_impossible_drop_never_included(self):
        table = [{"item": "iron_shard", "chance": 0.0}]
        result = resolve_loot_drops(table)
        assert result == []

    def test_multiple_certain_drops(self):
        table = [
            {"item": "iron_shard", "chance": 1.0},
            {"item": "scrap_metal", "chance": 1.0},
        ]
        result = resolve_loot_drops(table)
        assert result == ["iron_shard", "scrap_metal"]

    def test_mixed_table_respects_chance(self):
        # Seed so we know what the RNG produces.
        rng = _rng(42)
        table = [
            {"item": "always", "chance": 1.0},
            {"item": "never",  "chance": 0.0},
            {"item": "maybe",  "chance": 0.5},
        ]
        result = resolve_loot_drops(table, rng=rng)
        assert "always" in result
        assert "never" not in result
        # "maybe" depends on the seed; just verify it's a valid key if present.
        assert all(k in ("always", "maybe") for k in result)

    def test_rng_determines_outcome_reproducibly(self):
        table = [{"item": "gem", "chance": 0.5}]
        r1 = resolve_loot_drops(table, rng=_rng(7))
        r2 = resolve_loot_drops(table, rng=_rng(7))
        assert r1 == r2

    def test_different_seeds_can_differ(self):
        table = [{"item": "gem", "chance": 0.5}]
        outcomes = {
            tuple(resolve_loot_drops(table, rng=_rng(s))) for s in range(20)
        }
        # With 20 seeds there should be at least one drop and one non-drop.
        assert () in outcomes or ("gem",) in outcomes  # vacuous true guard
        assert len(outcomes) >= 2, "Different seeds should yield different outcomes"

    def test_returns_list_not_generator(self):
        table = [{"item": "x", "chance": 1.0}]
        result = resolve_loot_drops(table)
        assert isinstance(result, list)

    def test_preserves_drop_order(self):
        table = [
            {"item": "a", "chance": 1.0},
            {"item": "b", "chance": 1.0},
            {"item": "c", "chance": 1.0},
        ]
        assert resolve_loot_drops(table) == ["a", "b", "c"]

    def test_partial_drop_from_large_table(self):
        # All entries certain except the middle one which is impossible.
        table = [
            {"item": "a", "chance": 1.0},
            {"item": "b", "chance": 0.0},
            {"item": "c", "chance": 1.0},
        ]
        assert resolve_loot_drops(table) == ["a", "c"]


# ---------------------------------------------------------------------------
# resolve_credit_drop
# ---------------------------------------------------------------------------

class TestResolveCreditDrop:
    def test_min_equals_max_returns_exact(self):
        result = resolve_credit_drop({"min": 50, "max": 50})
        assert result == 50

    def test_result_within_range(self):
        rng = _rng(0)
        for _ in range(100):
            result = resolve_credit_drop({"min": 10, "max": 40}, rng=rng)
            assert 10 <= result <= 40

    def test_zero_range(self):
        assert resolve_credit_drop({"min": 0, "max": 0}) == 0

    def test_reproducible_with_seeded_rng(self):
        drop = {"min": 5, "max": 100}
        r1 = resolve_credit_drop(drop, rng=_rng(123))
        r2 = resolve_credit_drop(drop, rng=_rng(123))
        assert r1 == r2

    def test_different_seeds_produce_variation(self):
        drop = {"min": 1, "max": 1000}
        results = {resolve_credit_drop(drop, rng=_rng(s)) for s in range(20)}
        assert len(results) > 1, "Expected variation across seeds"

    def test_returns_int(self):
        result = resolve_credit_drop({"min": 1, "max": 10})
        assert isinstance(result, int)

    def test_large_range_distribution(self):
        rng = _rng(99)
        drop = {"min": 0, "max": 1000}
        results = [resolve_credit_drop(drop, rng=rng) for _ in range(200)]
        # Basic sanity: mean should be roughly 500 with enough samples.
        mean = sum(results) / len(results)
        assert 300 < mean < 700, f"Distribution looks skewed: mean={mean}"
