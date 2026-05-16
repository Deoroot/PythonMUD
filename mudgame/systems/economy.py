"""Economy helpers.

Pure functions used to derive vendor prices from base item prices and CHA.
"""

from __future__ import annotations


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def buy_price_multiplier(cha: int) -> float:
    """Return buy-price multiplier based on CHA.

    Rules:
    - CHA 10 is neutral (1.00).
    - Each CHA above 10 gives a 2% discount (cap: 20% at 0.80).
    - Each CHA below 10 gives a 2% surcharge (cap: 20% at 1.20).
    """
    delta = cha - 10
    return _clamp(1.0 - (delta * 0.02), 0.80, 1.20)


def sell_price_multiplier(cha: int) -> float:
    """Return sell-price multiplier based on CHA.

    Base sell value is 50% of listed price at CHA 10.
    Each CHA point above/below 10 shifts this by 1%, clamped to 40%-60%.
    """
    delta = cha - 10
    return _clamp(0.50 + (delta * 0.01), 0.40, 0.60)


def adjusted_buy_price(base_price: int, cha: int, discount: float = 0.0) -> int:
    """Return integer buy price after CHA multiplier and optional background discount.

    *discount* is subtracted from the CHA-derived multiplier before clamping,
    allowing it to push below the normal 0.80 floor (hard floor: 0.70).
    """
    if base_price <= 0:
        return 0
    mult = _clamp(buy_price_multiplier(cha) - discount, 0.70, 1.20)
    return max(1, int(round(base_price * mult)))


def adjusted_sell_price(base_price: int, cha: int, sell_bonus: float = 0.0) -> int:
    """Return integer sell payout after CHA multiplier and optional background bonus.

    *sell_bonus* is added after the CHA clamp, raising the effective ceiling
    beyond the normal 0.60 cap (e.g. Frontier Contractor reaches 0.65).
    """
    if base_price <= 0:
        return 0
    return max(1, int(round(base_price * (sell_price_multiplier(cha) + sell_bonus))))
