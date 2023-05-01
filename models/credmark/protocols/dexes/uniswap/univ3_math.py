"""
UniV3 Math
"""

# pylint:disable=invalid-name, missing-function-docstring

from math import log

import numpy as np

# out-of-range


# v3/TickMath.sol
UNISWAP_TICK = 1.0001

UNISWAP_V3_MIN_TICK = -887272
UNISWAP_V3_MAX_TICK = 887272


def out_of_range(liquidity, sb, sa):
    amount0 = int(liquidity * (sb - sa) / (sb * sa))
    amount1 = int(liquidity * (sb - sa))
    return amount0, amount1


def in_range(liquidity, sb, sa, sp):
    amount0 = int(liquidity * (sb - sp) / (sb * sp))
    amount1 = int(liquidity * (sp - sa))
    return amount0, amount1


def tick_to_price(tick):
    """
    tick to price
    """
    return pow(UNISWAP_TICK, tick)


def price_to_tick(price):
    """
    price to tick
    """
    return log(price) / log(UNISWAP_TICK)


def calculate_onetick_liquidity(
        current_tick, tick_spacing,
        token0, token1,
        liquidity, _liquidityNet):
    """
    Calculate tick liquidity

    _liquidityNet: when tick is on the tick_bottom or tick_top
    """

    # Compute the tick range near the current tick
    tick_bottom = current_tick // tick_spacing * tick_spacing
    tick_top = tick_bottom + tick_spacing
    assert tick_bottom <= current_tick <= tick_top

    # Compute the current price
    # p_current = 1.0001 ** tick
    # tick = log(p_current) / log(1.0001)
    p_current = tick_to_price(current_tick)

    # Let's say currentTick is 5, the liquidity profile looks like this:
    #             2  -> Liquidity = Liquidity at tick3  - LiquidityNet at tick2
    #             3  -> Liquidity = Liquidity at tick4  - LiquidityNet at tick3
    #             4  -> Liquidity = Liquidity at tick5  - LiquidityNet at tick4
    # currentTick 5  -> Liquidity = pools Liquidity
    #             6  -> Liquidity = Liquidity at tick5  + LiquidityNet at tick6
    #             7  -> Liquidity = Liquidity at tick6  + LiquidityNet at tick7

    # Compute square roots of prices corresponding to the bottom and top ticks
    sa = tick_to_price(tick_bottom / 2)
    sb = tick_to_price(tick_top / 2)
    sp = p_current ** 0.5

    # Liquidity in 1 tick
    in_tick_amount0, in_tick_amount1 = in_range(liquidity, sb, sa, sp)

    # Scale the amounts to the token's unit
    adjusted_in_tick_amount0 = token0.scaled(in_tick_amount0)
    adjusted_in_tick_amount1 = token1.scaled(in_tick_amount1)

    # Below shall be equal for the tick liquidity
    # Reference: UniswapV3 whitepaper Eq. 2.2

    # Disabled for some pools with small quantity of in_tick tokens.
    # Example:
    # uniswap-v3.get-pool-info -b 15301016
    # -i '{"address":"0x5c0f97e0ed70e0163b799533ce142f650e39a3e6",
    #      "price_slug": "uniswap-v3.get-weighted-price"}'

    # assert np.isclose(
    #     (in_tick_amount0 + liquidity / sb) * (in_tick_amount1 + liquidity * sa),
    #    float(liquidity * liquidity))

    ratio_left = (in_tick_amount0 + liquidity / sb) * (in_tick_amount1 + liquidity * sa)
    ratio_right = float(liquidity * liquidity)

    try:
        assert np.isclose(ratio_left, ratio_right)
    except AssertionError:
        compare_ratio = ratio_left/ratio_right
        assert 0.99 < compare_ratio < 1.01

    sa_p = tick_to_price((current_tick - 1) / 2)
    sb_p = tick_to_price((current_tick + 1) / 2)

    # Liquidity in 1 tick
    if current_tick == tick_bottom:
        __tick1_amount0, tick1_amount1 = out_of_range(
            liquidity-_liquidityNet, sp, sa_p)
        tick1_amount0, __tick1_amount1 = in_range(liquidity, sb_p, sp, sp)
    elif current_tick == tick_top:
        __tick1_amount0, tick1_amount1 = in_range(liquidity, sp, sa_p, sp)
        tick1_amount0, __tick1_amount1 = out_of_range(
            liquidity+_liquidityNet, sb_p, sp)
    else:
        tick1_amount0, tick1_amount1 = in_range(liquidity, sb_p, sa_p, sp)
        # equivalent to
        # _tick1_amount0 == 0, _tick1_amount1 = in_range(liquidity, sp, sa_p, sp)
        # tick1_amount0, _tick1_amount1 == 0 = in_range(liquidity, sb_p, sp, sp)

    # We match the two tokens' liquidity for the minimal available, a fix for the illiquid pools.
    tick1_amount0_adj = min(tick1_amount0, tick1_amount1 / sp / sp)
    tick1_amount1_adj = min(tick1_amount0 * sp * sp, tick1_amount1)

    one_tick_liquidity0_adj = token0.scaled(tick1_amount0_adj)
    one_tick_liquidity1_adj = token1.scaled(tick1_amount1_adj)

    return (one_tick_liquidity0_adj, one_tick_liquidity1_adj,
            adjusted_in_tick_amount0, adjusted_in_tick_amount1)
