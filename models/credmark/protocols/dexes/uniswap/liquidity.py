from math import floor, log
from typing import Dict, Optional

import matplotlib.pyplot as plt
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.types import Address, Contract, Token
from credmark.dto import DTO, DTOField


class V3PoolLiquidityByTicksInput(Contract):
    min_tick: Optional[int] = DTOField(None, description='(Optional) minimal tick to search')
    max_tick: Optional[int] = DTOField(None, description='(Optional) maximum tick to search')


class V3PoolLiquidityByTicksOutput(DTO):
    liquidity: Dict[int, int] = DTOField(description='Liquidity mapped to ticks')
    change_on_tick: Dict[int, int] = DTOField(description='Liquidity change on every tick')
    liquidity_pos_on_tick: Dict[int, int] = DTOField(description='Liquidity position on every tick')
    current_tick: int
    tick_spacing: int


@Model.describe(slug='uniswap-v3.get-liquidity-by-ticks',
                version='1.8',
                display_name='Uniswap v3 - Liquidity',
                description='Liquidity at every range - restored from Mint/Burn events',
                category='protocol',
                subcategory='uniswap-v3',
                input=V3PoolLiquidityByTicksInput,
                output=V3PoolLiquidityByTicksOutput)
class UniswapV3LiquidityHistorical(Model):
    MIN_TICK = -887272
    MAX_TICK = 887272

    def run(self, input: V3PoolLiquidityByTicksInput) -> V3PoolLiquidityByTicksOutput:
        pool_contract = input

        current_liquidity = pool_contract.functions.liquidity().call()
        slot0 = pool_contract.functions.slot0().call()
        current_tick = slot0[1]

        tick_spacing = pool_contract.functions.tickSpacing().call()
        tick_bottom = current_tick // tick_spacing * tick_spacing
        tick_top = tick_bottom + tick_spacing
        assert tick_bottom <= current_tick <= tick_top

        liquidity_on_tick = {}
        change_on_tick = {}
        liquidity_pos_on_tick = {}

        liquidity = current_liquidity
        x = 0
        tick_b = tick_bottom

        min_tick = self.MIN_TICK if input.min_tick is None else input.min_tick
        max_tick = self.MAX_TICK if input.max_tick is None else input.max_tick

        while tick_b >= min_tick:
            ticks = pool_contract.functions.ticks(tick_b).call()
            if ticks[1] != 0:
                change_on_tick[tick_b] = ticks[1]
                liquidity -= ticks[1]
                liquidity_on_tick[tick_b] = liquidity
            if ticks[0] != 0:
                liquidity_pos_on_tick[tick_b] = ticks[0]
            x += 1
            tick_b = tick_bottom - tick_spacing * x

        liquidity_on_tick = dict(sorted(liquidity_on_tick.items()))
        change_on_tick = dict(sorted(change_on_tick.items()))
        liquidity_pos_on_tick = dict(sorted(liquidity_pos_on_tick.items()))

        liquidity = current_liquidity
        x = 1
        tick_b = tick_bottom + tick_spacing
        while tick_b <= max_tick:
            ticks = pool_contract.functions.ticks(tick_b).call()
            if ticks[1] != 0:
                change_on_tick[tick_b] = ticks[1]
                liquidity += ticks[1]
                liquidity_on_tick[tick_b] = liquidity
            if ticks[0] != 0:
                liquidity_pos_on_tick[tick_b] = ticks[0]
            x += 1
            tick_b = tick_bottom + tick_spacing * x

        return V3PoolLiquidityByTicksOutput(
            liquidity=liquidity_on_tick,
            change_on_tick=change_on_tick,
            liquidity_pos_on_tick=liquidity_pos_on_tick,
            current_tick=current_tick,
            tick_spacing=tick_spacing)


def plot_liquidity(context):
    pool = Contract(address='0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640')

    current_liquidity = pool.functions.liquidity().call()
    _tick_spacing = pool.functions.tickSpacing().call()

    slot0 = pool.functions.slot0().call()
    current_tick = slot0[1]

    out = context.run_model(
        'uniswap-v3.get-liquidity-by-ticks',
        {"address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
         "min_tick": current_tick-1000,
         "max_tick": current_tick+1000})

    (pd.DataFrame([(int(k), int(v)) for k, v in out['liquidity'].items()],
                  columns=['tick', 'liquidity'])
        .plot('tick', 'liquidity')
     )
    plt.scatter(current_tick, current_liquidity, color='red')
    plt.show()


UNISWAP_BASE = 1.0001


def tick_to_price(tick):
    """
    tick to price
    """
    return pow(UNISWAP_BASE, tick)


def price_to_tick(price):
    """
    price to tick
    """
    return log(price) / log(UNISWAP_BASE)


def get_amount_in_ticks(logger, pool_contract: 'Contract', token0: 'Token', token1: 'Token', change_on_tick: Dict[int, int], should_print_tick=False):
    # pylint:disable=line-too-long
    """
    Reference: https://github.com/atiselsts/uniswap-v3-liquidity-math/blob/master/subgraph-liquidity-range-example.py
    """

    decimals0 = token0.decimals
    decimals1 = token1.decimals

    slot0 = pool_contract.functions.slot0().call()
    current_tick = slot0[1]
    current_price = tick_to_price(current_tick)
    adjusted_current_price = current_price / (10 ** (decimals1 - decimals0))

    tick_spacing = pool_contract.functions.tickSpacing().call()

    current_range_bottom_tick = floor(current_tick / tick_spacing) * tick_spacing
    current_price = tick_to_price(current_tick)

    liquidity = 0

    token_amounts = []

    min_tick = min(change_on_tick.keys())
    max_tick = max(change_on_tick.keys())

    for tick in range(min_tick, max_tick, tick_spacing):
        liquidity += change_on_tick.get(tick, 0)

        tick_bottom = tick
        tick_top = tick_bottom + tick_spacing

        sa = tick_to_price(tick_bottom // 2)
        sb = tick_to_price(tick_top // 2)

        # Compute the amounts of tokens potentially in the range
        amount1 = int(liquidity * (sb - sa))
        amount0 = int(amount1 / (sb * sa))

        if tick < current_range_bottom_tick:
            token_amounts.append((tick, amount0, amount1, liquidity))
        elif tick == current_range_bottom_tick:
            # Print the real amounts of the two assets needed to be swapped to move out of the current tick range
            sp = tick_to_price(current_tick / 2)
            amount0 = int(liquidity * (sb - sp) / (sp * sb))
            amount1 = int(liquidity * (sp - sa))

            token_amounts.append((tick, amount0, amount1, liquidity))
            logger.info(f"{amount0:.2f} {token0} and {amount1:.2f} {token1} remaining in the current tick range")
        else:
            token_amounts.append((tick, amount0, amount1, liquidity))
            if should_print_tick:
                adjusted_amount0 = amount0 / (10 ** decimals0)
                adjusted_amount1 = amount1 / (10 ** decimals1)
                logger.info(f"{adjusted_amount0:.2f} {token0} locked, potentially worth {adjusted_amount1:.2f} {token1}")

        tick += tick_spacing

    token0_bal = token0.balance_of(pool_contract.address.checksum)
    token1_bal = token1.balance_of(pool_contract.address.checksum)
    token0_dec = 10**decimals0
    token1_dec = 10**decimals1

    df_pool = (
        pd.DataFrame(token_amounts, columns=['tick', 'token0', 'token1', 'liquidity'])
        .assign(token0_locked=lambda x: x.token0,
                token1_locked=lambda x: x.token1)
        .assign(token0_locked=lambda x, t=current_range_bottom_tick: x.token0_locked.where(x.tick >= t, 0),
                token1_locked=lambda x, t=current_range_bottom_tick: x.token1_locked.where(x.tick <= t, 0))
        .assign(token0_scaled=lambda x, dec=token0_dec: x.token0 / dec,
                token1_scaled=lambda x, dec=token1_dec: x.token1 / dec,
                token0_prop=lambda x, bal=token0_bal: x.token0 / bal,
                token1_prop=lambda x, bal=token1_bal: x.token1 / bal)
        .assign(token0_locked_scaled=lambda x, dec=token0_dec: x.token0_locked / dec,
                token1_locked_scaled=lambda x, dec=token1_dec: x.token1_locked / dec,
                token0_locked_prop=lambda x, bal=token0_bal: x.token0_locked / bal,
                token1_locked_prop=lambda x, bal=token1_bal: x.token1_locked / bal
                )
    )
    return df_pool


@ Model.describe(slug='uniswap-v3.get-amount-in-ticks',
                 version='1.8',
                 display_name='Uniswap v3 - Liquidity',
                 description='Liquidity at every range - restored from Mint/Burn events',
                 category='protocol',
                 subcategory='uniswap-v3',
                 input=V3PoolLiquidityByTicksInput,
                 output=dict)
class UniswapV3AmountInTicks(Model):
    def run(self, input: V3PoolLiquidityByTicksInput) -> dict:
        liquidity_by_ticks = self.context.run_model(
            'uniswap-v3.get-liquidity-by-ticks', input, return_type=V3PoolLiquidityByTicksOutput)

        pool_contract = input
        token0_addr = pool_contract.functions.token0().call()
        token1_addr = pool_contract.functions.token1().call()
        token0 = Token(address=Address(token0_addr).checksum)
        token1 = Token(address=Address(token1_addr).checksum)

        df_pool = get_amount_in_ticks(self.logger, pool_contract, token0, token1, liquidity_by_ticks.change_on_tick)

        breakpoint()

        return df_pool.to_dict()


def plot_liquidity_amount(context):
    pool = Contract(address='0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640')

    slot0 = pool.functions.slot0().call()
    current_tick = slot0[1]

    out = context.run_model(
        'uniswap-v3.get-amount-in-ticks',
        {"address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
         "min_tick": current_tick-1000,
         "max_tick": current_tick+1000},
        block_number=12377278)

    df_pool = pd.DataFrame(out)
    df_pool.token0_locked_prop.sum()  # close to 1
    df_pool.token1_locked_prop.sum()  # close to 1

    (df_pool
        .astype({'token0_locked': 'float64', 'token1_locked': 'float64'})
        .plot(x='tick',
              y=['liquidity', 'token0_locked', 'token1_locked'],
              sharex=True,
              subplots=True,
              kind='line'))
    plt.show()

    out = context.run_model(
        'uniswap-v3.get-amount-in-ticks',
        {"address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
         "min_tick": 186730,
         "max_tick": 198080},
        block_number=12377278)

    out = context.run_model(
        'uniswap-v3.get-amount-in-ticks',
        {"address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"})
