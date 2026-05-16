"""Tests for CHA-driven economy helpers."""

from __future__ import annotations

from mudgame.systems.economy import (
    adjusted_buy_price,
    adjusted_sell_price,
    buy_price_multiplier,
    sell_price_multiplier,
)


def test_buy_multiplier_neutral_at_cha_10():
    assert buy_price_multiplier(10) == 1.0


def test_buy_multiplier_discount_above_10():
    assert buy_price_multiplier(15) == 0.9


def test_buy_multiplier_surcharge_below_10():
    assert buy_price_multiplier(8) == 1.04


def test_buy_multiplier_clamped():
    assert buy_price_multiplier(30) == 0.8
    assert buy_price_multiplier(0) == 1.2


def test_sell_multiplier_neutral_at_cha_10():
    assert sell_price_multiplier(10) == 0.5


def test_sell_multiplier_scales_and_clamps():
    assert sell_price_multiplier(15) == 0.55
    assert sell_price_multiplier(30) == 0.6
    assert sell_price_multiplier(0) == 0.4


def test_adjusted_buy_price_rounds_and_min_one():
    assert adjusted_buy_price(75, 15) == 68
    assert adjusted_buy_price(1, 30) == 1


def test_adjusted_sell_price_rounds_and_min_one():
    assert adjusted_sell_price(75, 15) == 41
    assert adjusted_sell_price(1, 30) == 1


def test_non_positive_prices_return_zero():
    assert adjusted_buy_price(0, 10) == 0
    assert adjusted_sell_price(0, 10) == 0
