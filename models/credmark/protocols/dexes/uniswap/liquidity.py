# pylint:disable=invalid-name

from math import floor
from typing import Dict, Optional

import matplotlib.pyplot as plt
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import Address, Contract, Token
from credmark.dto import DTO, DTOField

from models.credmark.protocols.dexes.uniswap.uniswap_v3_pool import fix_univ3_pool
from models.credmark.protocols.dexes.uniswap.univ3_math import (
    UNISWAP_TICK,
    UNISWAP_V3_MAX_TICK,
    UNISWAP_V3_MIN_TICK,
    tick_to_price,
)


class UniswapV3PoolLiquidityByTicksInput(Contract):
    min_tick: int = DTOField(
        UNISWAP_V3_MIN_TICK, description='(Optional) minimal tick to search')
    max_tick: int = DTOField(
        UNISWAP_V3_MAX_TICK, description='(Optional) maximum tick to search')

    class Config:
        schema_extra = {
            'examples': [{"address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                          "min_tick": 202180-1000,
                          "max_tick": 202180+1000}]
        }


class UniswapV3PoolLiquidityByTicksOutput(DTO):
    liquidity: Dict[int, int] = DTOField(
        description='Liquidity mapped to ticks')
    change_on_tick: Dict[int, int] = DTOField(
        description='Liquidity change on every tick')
    liquidity_pos_on_tick: Dict[int, int] = DTOField(
        description='Liquidity position on every tick')
    current_tick: int
    current_liquidity: int
    tick_spacing: int


@Model.describe(slug='uniswap-v3.get-liquidity-by-ticks',
                version='0.2',
                display_name='Uniswap v3 - Liquidity',
                description='Liquidity at every range - restored from Mint/Burn events',
                category='protocol',
                subcategory='uniswap-v3',
                input=UniswapV3PoolLiquidityByTicksInput,
                output=UniswapV3PoolLiquidityByTicksOutput)
class UniswapV3LiquidityHistorical(Model):
    def collect_ticks(self, pool_contract, min_tick, max_tick, tick_bottom, tick_spacing):
        ticks_b = []
        ticks_b_calls = []

        x = 0
        tick_b = tick_bottom
        while tick_b >= min_tick:
            ticks_b_calls.append(pool_contract.functions.ticks(tick_b))
            ticks_b.append(tick_b)
            x += 1
            tick_b = tick_bottom - tick_spacing * x

        x = 1
        tick_b = tick_bottom + tick_spacing
        while tick_b <= max_tick:
            ticks_b_calls.append(pool_contract.functions.ticks(tick_b))
            ticks_b.append(tick_b)
            x += 1
            tick_b = tick_bottom + tick_spacing * x

        m = self.context.multicall
        ticks_b_result = m.try_aggregate_unwrap(ticks_b_calls)
        ticks_b_dict = dict(zip(ticks_b, ticks_b_result))
        return ticks_b_dict

    def run(self, input: UniswapV3PoolLiquidityByTicksInput) -> UniswapV3PoolLiquidityByTicksOutput:
        pool_contract = input

        pool_contract = fix_univ3_pool(pool_contract)

        if pool_contract.abi is None:
            raise ModelRunError('ABI is not set')

        current_liquidity = pool_contract.functions.liquidity().call()
        if 'slot0' in pool_contract.abi.functions:
            slot0 = pool_contract.functions.slot0().call()
        elif 'globalState' in pool_contract.abi.functions:  # QuickSwap
            slot0 = pool_contract.functions.globalState().call()
        else:
            raise ModelRunError('Unable to query V3 pool state, '
                                'neither Uniswap/PancakeSwap nor QuickSwap')

        current_tick = slot0[1]

        tick_spacing = pool_contract.functions.tickSpacing().call()
        tick_bottom = current_tick // tick_spacing * tick_spacing
        tick_top = tick_bottom + tick_spacing
        assert tick_bottom <= current_tick <= tick_top

        liquidity_on_tick = {}
        change_on_tick = {}
        liquidity_pos_on_tick = {}

        min_tick = input.min_tick
        max_tick = input.max_tick

        # [ min_tick - tick_bottom - current_tick - tick_top - max_tick ]

        # collect tick data
        ticks_dict = self.collect_ticks(pool_contract, min_tick,
                                        max_tick, tick_bottom, tick_spacing)

        liquidity = current_liquidity
        x = 0
        tick_b = tick_bottom
        while tick_b >= min_tick:
            # Replaced: ticks = pool_contract.functions.ticks(tick_b).call()
            ticks = ticks_dict[tick_b]
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
            # Replaced: ticks = pool_contract.functions.ticks(tick_b).call()
            ticks = ticks_dict[tick_b]
            if ticks[1] != 0:
                change_on_tick[tick_b] = ticks[1]
                liquidity += ticks[1]
                liquidity_on_tick[tick_b] = liquidity
            if ticks[0] != 0:
                liquidity_pos_on_tick[tick_b] = ticks[0]
            x += 1
            tick_b = tick_bottom + tick_spacing * x

        return UniswapV3PoolLiquidityByTicksOutput(
            liquidity=liquidity_on_tick,
            change_on_tick=change_on_tick,
            liquidity_pos_on_tick=liquidity_pos_on_tick,
            current_tick=current_tick,
            current_liquidity=current_liquidity,
            tick_spacing=tick_spacing)


def plot_liquidity(context,
                   pool_addr='0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640',
                   upper_range=1000,
                   lower_range=1000):
    pool = fix_univ3_pool(Contract(address=pool_addr))

    current_liquidity = pool.functions.liquidity().call()
    _tick_spacing = pool.functions.tickSpacing().call()

    if pool.abi is None:
        raise ModelRunError('ABI is not set')

    if 'slot0' in pool.abi.functions:
        slot0 = pool.functions.slot0().call()
    elif 'globalState' in pool.abi.functions:  # QuickSwap
        slot0 = pool.functions.globalState().call()
    else:
        raise ModelRunError('Unable to query V3 pool state, '
                            'neither Uniswap/PancakeSwap nor QuickSwap')
    current_tick = slot0[1]

    out = context.run_model(
        'uniswap-v3.get-liquidity-by-ticks',
        {"address": pool_addr,
         "min_tick": current_tick-lower_range,
         "max_tick": current_tick+upper_range},
        block_number=context.block_number)

    df_pool_mode = (pd.DataFrame([(int(k), int(v)) for k, v in out['liquidity'].items()],
                                 columns=['tick', 'liquidity'])
                    .astype({'liquidity': 'float64'}))

    df_pool_mode.plot('tick', 'liquidity')  # type: ignore

    plt.scatter(current_tick, current_liquidity, color='red')
    plt.show()

    return df_pool_mode, pool


# pylint:disable=too-many-arguments
def get_amount_in_ticks(logger,
                        pool_contract: 'Contract',
                        token0: 'Token',
                        token1: 'Token',
                        change_on_tick: Dict[int, int],
                        min_tick: int,
                        max_tick: int,
                        should_print_tick=False):
    # pylint:disable=line-too-long, too-many-locals
    """
    Reference: https://github.com/atiselsts/uniswap-v3-liquidity-math/blob/master/subgraph-liquidity-range-example.py

    Example:

    credmark-dev run uniswap-v3.get-liquidity-by-ticks -i '{"address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", "min_tick": 201670, "max_tick": 201710}' -j -b 17462529

    "output": {
        "liquidity": {
            "201670": 20330381308202323617,
            "201680": 20329534234532284054,
            "201690": 20322880984516160007, <= for [201680-201690]
            "201700": 19416166311043464783, <= for [201690-201700]
            "201710": 19238384479126856389
        },
        "change_on_tick": {
            "201670": -847073670039563,
            "201680": -6653250016124047,
            "201690": 475672022322741251,
            "201700": -1382386695795436475,
            "201710": -177781831916608394
        },
        "liquidity_pos_on_tick": {
            "201670": 1453239534246639,
            "201680": 6723980100072201,
            "201690": 686798573520275475,
            "201700": 1884321528554965515,
            "201710": 177980976302859136
        },
        "current_tick": 201699,
        "current_liquidity": 20798553006838901258,
        "tick_spacing": 10
    }

    The current tick is 201699 and current range is [201690 - 201700].
    For liquidity,
    - When tick is lower the current tick, it's the liquidity for range [t-10, t].
    - When tick is higher the current tick, it's the liquidity for range [t, t+10].

    For change_on_tick, it is the net change when liquidity cross.
    - For tick lowe the current tick, current liquidity - net change.
    - For tick higher than the current tick, it's current liquidity + net change.
    """

    decimals0 = token0.decimals
    decimals1 = token1.decimals

    if pool_contract.abi is None:
        raise ModelRunError('ABI is not set')

    if 'slot0' in pool_contract.abi.functions:
        slot0 = pool_contract.functions.slot0().call()
    elif 'globalState' in pool_contract.abi.functions:  # QuickSwap
        slot0 = pool_contract.functions.globalState().call()
    else:
        raise ModelRunError('Unable to query V3 pool state, '
                            'neither Uniswap/PancakeSwap nor QuickSwap')

    current_tick = slot0[1]

    current_price = tick_to_price(current_tick)
    _adjusted_current_price = current_price / (10 ** (decimals1 - decimals0))

    tick_spacing = pool_contract.functions.tickSpacing().call()

    current_range_bottom_tick = floor(
        current_tick / tick_spacing) * tick_spacing
    current_price = tick_to_price(current_tick)

    liquidity = 0

    token_amounts = []

    min_tick = (min_tick
                if len(change_on_tick.keys()) == 0
                else min(change_on_tick.keys()))
    max_tick = (max_tick
                if len(change_on_tick.keys()) == 0
                else max(change_on_tick.keys()))

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
            logger.info(
                f"{amount0:.2f} {token0} and {amount1:.2f} {token1} remaining in the current tick range")
        else:
            token_amounts.append((tick, amount0, amount1, liquidity))
            if should_print_tick:
                adjusted_amount0 = amount0 / (10 ** decimals0)
                adjusted_amount1 = amount1 / (10 ** decimals1)
                logger.info(
                    f"{adjusted_amount0:.2f} {token0} locked, potentially worth {adjusted_amount1:.2f} {token1}")

        tick += tick_spacing

    token0_bal = token0.balance_of(pool_contract.address.checksum)
    token1_bal = token1.balance_of(pool_contract.address.checksum)
    token0_dec = 10**decimals0
    token1_dec = 10**decimals1

    df_pool = (
        pd.DataFrame(
            token_amounts,
            columns=['tick', 'token0', 'token1', 'liquidity'])
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
                token1_locked_prop=lambda x, bal=token1_bal: x.token1_locked / bal))

    return df_pool


@Model.describe(slug='uniswap-v3.get-amount-in-ticks',
                version='0.1',
                display_name='Uniswap v3 - Liquidity',
                description='Liquidity at every range - restored from Mint/Burn events',
                category='protocol',
                subcategory='uniswap-v3',
                input=UniswapV3PoolLiquidityByTicksInput,
                output=dict)
class UniswapV3AmountInTicks(Model):
    def run(self, input: UniswapV3PoolLiquidityByTicksInput) -> dict:
        liquidity_by_ticks = self.context.run_model(
            'uniswap-v3.get-liquidity-by-ticks',
            input,
            return_type=UniswapV3PoolLiquidityByTicksOutput)

        pool_contract = fix_univ3_pool(input)

        token0_addr = pool_contract.functions.token0().call()
        token1_addr = pool_contract.functions.token1().call()
        token0 = Token(address=Address(token0_addr).checksum)
        token1 = Token(address=Address(token1_addr).checksum)

        df_pool = get_amount_in_ticks(self.logger,
                                      pool_contract,
                                      token0, token1,
                                      liquidity_by_ticks.change_on_tick,
                                      min_tick=input.min_tick,
                                      max_tick=input.max_tick)

        return df_pool.to_dict()


def plot_liquidity_amount(context,
                          pool_addr='0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640',
                          upper_range: Optional[int] = 1000,
                          lower_range: Optional[int] = 1000):

    pool = fix_univ3_pool(Contract(address=pool_addr))

    token0_addr = pool.functions.token0().call()
    token1_addr = pool.functions.token1().call()
    token0 = Token(address=Address(token0_addr).checksum)
    token1 = Token(address=Address(token1_addr).checksum)

    scale_multiplier = 10 ** (token0.decimals - token1.decimals)

    def tick_to_price_with_scaling(tick, scale_multiplier=scale_multiplier):
        return UNISWAP_TICK ** tick * scale_multiplier

    if pool.abi is None:
        raise ModelRunError('ABI is not set')

    if 'slot0' in pool.abi.functions:
        slot0 = pool.functions.slot0().call()
    elif 'globalState' in pool.abi.functions:  # QuickSwap
        slot0 = pool.functions.globalState().call()
    else:
        raise ModelRunError('Unable to query V3 pool state, '
                            'neither Uniswap/PancakeSwap nor QuickSwap')

    current_tick = slot0[1]
    current_price = tick_to_price_with_scaling(current_tick)

    context.logger.info(f'{current_tick=} {current_price=}')

    out = context.run_model(
        'uniswap-v3.get-amount-in-ticks',
        {"address": pool.address,
         "min_tick": (UNISWAP_V3_MIN_TICK if lower_range is None
                      else max(current_tick-lower_range, UNISWAP_V3_MIN_TICK)),
         "max_tick": (UNISWAP_V3_MAX_TICK if upper_range is None
                      else min(current_tick+upper_range, UNISWAP_V3_MAX_TICK))},
        block_number=context.block_number)

    df_pool = pd.DataFrame(out)
    df_pool.token0_locked_prop.sum()  # close to 1
    df_pool.token1_locked_prop.sum()  # close to 1

    df_pool_mod = (
        df_pool
        .astype({'token0_locked': 'float64', 'token1_locked': 'float64', 'liquidity': 'float64'})
        .assign(price=lambda x: tick_to_price_with_scaling(x.tick)))

    (df_pool_mod.plot(x='tick',
                      y=['liquidity', 'token0_locked', 'token1_locked'],
                      sharex=True,
                      subplots=True,
                      kind='line'))
    plt.title(pool_addr)
    plt.show()

    (df_pool_mod.plot(x='price',
                      y=['liquidity', 'token0_locked_scaled', 'token1_locked_scaled',
                          'token0_locked_prop', 'token1_locked_prop'],
                      sharex=True,
                      subplots=True,
                      kind='line'))
    plt.title(pool_addr)
    plt.plot(current_price, df_pool_mod.token1_locked_prop.max())
    plt.show()

    return df_pool_mod, pool
