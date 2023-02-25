"""
Uni V3 Pool
"""

# pylint:disable=invalid-name, missing-function-docstring, too-many-instance-attributes, line-too-long, unused-import

from datetime import datetime

from typing import Optional

import numpy as np
import pandas as pd
from credmark.cmf.ipython import CmfInit, create_cmf_context
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import Address, Contract, Token
from credmark.dto import DTO
from models.credmark.protocols.dexes.uniswap.univ3_math import calculate_onetick_liquidity
from models.dtos.pool import PoolPriceInfoWithVolume

from models.tmp_abi_lookup import UNISWAP_V3_POOL_ABI


class Tick(DTO):
    """
    // 1.0001^tick is token1/token0.
    let price0 = bigDecimalExponated(BigDecimal.fromString('1.0001'), BigInt.fromI32(tickIdx))
    tick.price0 = price0
    tick.price1 = safeDiv(ONE_BD, price0)
    """

    liquidityGross: int
    liquidityNet: int


def fetch_events(pool, event, event_name, _from_block, _to_block, _cols):
    start_t = datetime.now()
    df = pd.DataFrame(pool.fetch_events(
        event,
        from_block=_from_block,
        to_block=_to_block))
    end_t = datetime.now() - start_t
    print((event_name, 'node', pool.address, _from_block, _to_block, end_t, df.shape))

    if df.empty:
        return pd.DataFrame()

    df = (df.sort_values(['blockNumber', 'logIndex'])
            .loc[:, ['blockNumber', 'logIndex'] + _cols]
            .assign(event=event_name))
    return df


class UniV3Pool:
    """
    Uniswap V3 Pool
    """

    def __init__(self, pool_addr: Address, _pool_data: Optional[dict] = None):
        self.pool = Contract(address=pool_addr)
        self.pool.set_abi(UNISWAP_V3_POOL_ABI)

        self.tick_spacing = self.pool.functions.tickSpacing().call()

        self.token0_addr = self.pool.functions.token0().call().lower()
        self.token1_addr = self.pool.functions.token1().call().lower()
        self.token0 = Token(address=Address(self.token0_addr).checksum)
        self.token1 = Token(address=Address(self.token1_addr).checksum)

        try:
            self.token0_decimals = self.token0.decimals
            self.token0_symbol = self.token0.symbol
        except ModelDataError:
            self.token0 = self.token0.as_erc20(force=True)
            self.token0_decimals = self.token0.decimals
            self.token0_symbol = self.token0.symbol

        try:
            self.token1_decimals = self.token1.decimals
            self.token1_symbol = self.token1.symbol
        except ModelDataError:
            self.token1 = self.token1.as_erc20(force=True)
            self.token1_decimals = self.token1.decimals
            self.token1_symbol = self.token1.symbol

        if _pool_data is None:
            self.pool_tick = None
            self.pool_sqrtPrice = None
            self.pool_liquidity = None
            self.ticks = {}
            self.block_number = None
            self.log_index = None

            self.previous_block_number = None
            self.previous_log_index = None
            self.previous_price_info = None

            self.token0_in = 0
            self.token0_out = 0
            self.token1_in = 0
            self.token1_out = 0

            self.token0_add = 0
            self.token0_remove = 0
            self.token0_collect = 0
            self.token0_collect_prot = 0
            self.token1_add = 0
            self.token1_remove = 0
            self.token1_collect = 0
            self.token1_collect_prot = 0

            self.token0_reserve = 0
            self.token1_reserve = 0
        else:
            self.load(_pool_data)

    def __del__(self):
        del self.token0
        del self.token1

    def save(self):
        return {'pool_tick': self.pool_tick, 'pool_sqrtPrice': self.pool_sqrtPrice, 'pool_liquidity': self.pool_liquidity, 'ticks': self.ticks,
                'block_number': self.block_number, 'log_index': self.log_index,
                'previous_block_number': self.previous_block_number,
                'previous_log_index': self.previous_log_index,
                'previous_price_info': self.previous_price_info.dict() if self.previous_price_info is not None else None,
                'token0_in': self.token0_in,
                'token0_out': self.token0_out,
                'token1_in': self.token1_in,
                'token1_out': self.token1_out,

                'token0_add': self.token0_add,
                'token0_remove': self.token0_remove,
                'token0_collect': self.token0_collect,
                'token0_collect_prot': self.token0_collect_prot,
                'token1_add': self.token1_add,
                'token1_remove': self.token1_remove,
                'token1_collect': self.token1_collect,
                'token1_collect_prot': self.token1_collect_prot,

                'token0_reserve': self.token0_reserve,
                'token1_reserve': self.token1_reserve,
                }

    def load(self, _pool_data):
        self.pool_tick = _pool_data['pool_tick']
        self.pool_sqrtPrice = _pool_data['pool_sqrtPrice']
        self.pool_liquidity = _pool_data['pool_liquidity']
        self.ticks = {int(float(k)): Tick(**v) for k, v in _pool_data['ticks'].items()}
        self.block_number = _pool_data['block_number']
        self.log_index = _pool_data['log_index']

        self.previous_block_number = _pool_data['previous_block_number']
        self.previous_log_index = _pool_data['previous_log_index']
        self.previous_price_info = (
            PoolPriceInfoWithVolume(**_pool_data['previous_price_info'])
            if _pool_data['previous_price_info'] is not None
            else None)

        self.token0_in = _pool_data['token0_in']
        self.token0_out = _pool_data['token0_out']
        self.token1_in = _pool_data['token1_in']
        self.token1_out = _pool_data['token1_out']

        self.token0_add = _pool_data['token0_add']
        self.token0_remove = _pool_data['token0_remove']
        self.token0_collect = _pool_data['token0_collect_prot']
        self.token0_collect_prot = _pool_data['token0_collect_prot']
        self.token1_add = _pool_data['token1_add']
        self.token1_remove = _pool_data['token1_remove']
        self.token1_collect = _pool_data['token1_collect']
        self.token1_collect_prot = _pool_data['token1_collect_prot']

        self.token0_reserve = _pool_data['token0_reserve']
        self.token1_reserve = _pool_data['token1_reserve']

    def load_events(self, from_block, to_block):
        pool = self.pool
        if pool.abi is None:
            raise ValueError(f'Pool abi missing for {pool.address}')

        df_init_evt = fetch_events(pool, pool.events.Initialize, 'Initialize',
                                   from_block, to_block, pool.abi.events.Initialize.args)
        df_collect_evt = fetch_events(pool, pool.events.Collect, 'Collect', from_block,
                                      to_block, pool.abi.events.Collect.args)
        df_collect_prot_evt = fetch_events(pool, pool.events.CollectProtocol,
                                           'CollectProtocol', from_block, to_block, pool.abi.events.CollectProtocol.args)
        df_flash_evt = fetch_events(pool, pool.events.Flash, 'Flash', from_block, to_block, pool.abi.events.Flash.args)
        df_mint_evt = fetch_events(pool, pool.events.Mint, 'Mint', from_block, to_block, pool.abi.events.Mint.args)
        df_burn_evt = fetch_events(pool, pool.events.Burn, 'Burn', from_block, to_block, pool.abi.events.Burn.args)
        df_swap_evt = fetch_events(pool, pool.events.Swap, 'Swap', from_block, to_block, pool.abi.events.Swap.args)

        df_comb_evt = pd.concat([df_init_evt, df_mint_evt, df_burn_evt, df_swap_evt,
                                df_collect_evt, df_collect_prot_evt, df_flash_evt])

        if df_comb_evt.empty:
            return df_comb_evt

        df_comb_evt = df_comb_evt.sort_values(['blockNumber', 'logIndex']).reset_index(drop=True)
        print((df_init_evt.shape[0], df_mint_evt.shape[0], df_burn_evt.shape[0], df_swap_evt.shape[0], df_comb_evt.shape[0],
               df_collect_evt.shape[0], df_collect_prot_evt.shape[0], df_flash_evt.shape[0]))
        return df_comb_evt

    def sqrtPriceX96toTokenPrices(self, sqrtPrice96):
        num = sqrtPrice96 * sqrtPrice96
        denom = 2 ** 192
        price0 = num / denom * 10 ** (self.token0_decimals - self.token1_decimals)
        try:
            price1 = 1 / price0
        except (FloatingPointError, ZeroDivisionError):
            price1 = 0
            price0 = 0

        return price0, price1

    def get_pool_price_info(self):
        if self.pool_tick is not None and self.pool_tick in self.ticks:
            _liquidityNet = self.ticks[self.pool_tick].liquidityNet
        else:
            _liquidityNet = 0

        (one_tick_liquidity0_adj, one_tick_liquidity1_adj,
         adjusted_in_tick_amount0, adjusted_in_tick_amount1) = calculate_onetick_liquidity(
            self.pool_tick, self.tick_spacing,
            self.token0, self.token1,
            self.pool_liquidity, _liquidityNet)

        ratio_price0, ratio_price1 = self.sqrtPriceX96toTokenPrices(self.pool_sqrtPrice)

        # if np.isclose(one_tick_liquidity0_adj, 0) or np.isclose(one_tick_liquidity1_adj, 0):
        #    ratio_price0 = 0
        #    ratio_price1 = 0

        pool_price_info = PoolPriceInfoWithVolume(
            src='uniswap-v3.get-weighted-price',
            price0=ratio_price0,
            price1=ratio_price1,
            one_tick_liquidity0=one_tick_liquidity0_adj,
            one_tick_liquidity1=one_tick_liquidity1_adj,
            full_tick_liquidity0=adjusted_in_tick_amount0,
            full_tick_liquidity1=adjusted_in_tick_amount1,
            token0_address=self.token0.address,
            token1_address=self.token1.address,
            token0_symbol=self.token0_symbol,
            token1_symbol=self.token1_symbol,
            ref_price=1,
            pool_address=self.pool.address,
            tick_spacing=self.tick_spacing,

            token0_in=self.token0.scaled(self.token0_in),
            token0_out=self.token0.scaled(self.token0_out),
            token1_in=self.token1.scaled(self.token1_in),
            token1_out=self.token1.scaled(self.token1_out),

            token0_add=self.token0.scaled(self.token0_add),
            token0_remove=self.token0.scaled(self.token0_remove),
            token0_collect=self.token0.scaled(self.token0_collect),
            token0_collect_prot=self.token0.scaled(self.token0_collect_prot),
            token1_add=self.token1.scaled(self.token1_add),
            token1_remove=self.token1.scaled(self.token1_remove),
            token1_collect=self.token1.scaled(self.token1_collect),
            token1_collect_prot=self.token1.scaled(self.token1_collect_prot),

            reserve0=self.token0.scaled(self.token0_reserve),
            reserve1=self.token1.scaled(self.token1_reserve),
        )

        self.previous_block_number = self.block_number
        self.previous_log_index = self.log_index
        self.previous_price_info = pool_price_info

        return pool_price_info

    def proc_events(self, df_events):
        for _n, event_row in df_events.iterrows():
            self.block_number = event_row['blockNumber']
            self.log_index = event_row['logIndex']

            if event_row['event'] == 'Initialize':
                yield self.proc_initialize(event_row)
            elif event_row['event'] == 'Burn':
                yield self.proc_burn(event_row)
            elif event_row['event'] == 'Mint':
                yield self.proc_mint(event_row)
            elif event_row['event'] == 'Swap':
                yield self.proc_swap(event_row)
            elif event_row['event'] == 'Collect':
                yield self.proc_collect(event_row)
            elif event_row['event'] == 'CollectProtocol':
                yield self.proc_collect_prot(event_row)
            elif event_row['event'] == 'Flash':
                yield self.proc_flash(event_row)
            else:
                raise ValueError(f'Unknown event {event_row["event"]}')

    def proc_initialize(self, event_row):
        self.pool_tick = event_row['tick']
        self.pool_sqrtPrice = event_row['sqrtPriceX96']
        self.pool_liquidity = 0
        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())

    def proc_mint(self, event_row):
        tickLower = event_row['tickLower']
        tickUpper = event_row['tickUpper']
        amount = event_row['amount']
        amount0 = event_row['amount0']
        amount1 = event_row['amount1']

        self.token0_add += amount0
        self.token1_add += amount1
        self.token0_reserve += amount0
        self.token1_reserve += amount1

        lowerTick = self.ticks.get(tickLower, Tick(liquidityGross=0, liquidityNet=0))
        upperTick = self.ticks.get(tickUpper, Tick(liquidityGross=0, liquidityNet=0))

        lowerTick.liquidityGross = lowerTick.liquidityGross + amount
        lowerTick.liquidityNet = lowerTick.liquidityNet + amount
        upperTick.liquidityGross = upperTick.liquidityGross + amount
        upperTick.liquidityNet = upperTick.liquidityNet - amount

        self.ticks[tickLower] = lowerTick
        self.ticks[tickUpper] = upperTick

        if tickLower <= self.pool_tick and tickUpper > self.pool_tick:
            self.pool_liquidity += amount

        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())

    def proc_burn(self, event_row):
        tickLower = event_row['tickLower']
        tickUpper = event_row['tickUpper']
        amount = event_row['amount']
        amount0 = event_row['amount0']
        amount1 = event_row['amount1']

        self.token0_remove += amount0
        self.token1_remove += amount1
        self.token0_reserve -= amount0
        self.token1_reserve -= amount1

        lowerTick = self.ticks[tickLower]
        upperTick = self.ticks[tickUpper]

        lowerTick.liquidityGross = lowerTick.liquidityGross - amount
        lowerTick.liquidityNet = lowerTick.liquidityNet - amount
        upperTick.liquidityGross = upperTick.liquidityGross - amount
        upperTick.liquidityNet = upperTick.liquidityNet + amount

        self.ticks[tickLower] = lowerTick
        self.ticks[tickUpper] = upperTick

        if tickLower <= self.pool_tick and tickUpper > self.pool_tick:
            self.pool_liquidity -= event_row['amount']

        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())

    def proc_swap(self, event_row):
        self.pool_liquidity = event_row['liquidity']
        self.pool_tick = event_row['tick']
        self.pool_sqrtPrice = event_row['sqrtPriceX96']

        self.token0_in += 0 if event_row['amount0'] < 0 else event_row['amount0']
        self.token0_out += -event_row['amount0'] if event_row['amount0'] < 0 else 0
        self.token1_in += 0 if event_row['amount1'] < 0 else event_row['amount1']
        self.token1_out += -event_row['amount1'] if event_row['amount1'] < 0 else 0

        self.token0_reserve += event_row['amount0']
        self.token1_reserve += event_row['amount1']

        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())

    def proc_collect(self, event_row):
        self.token0_collect += event_row['amount0']
        self.token1_collect += event_row['amount1']

        # collect is part of burn. not double-count to reduce token0_reserve and token1_reserve

        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())

    def proc_collect_prot(self, event_row):
        self.token0_collect_prot += event_row['amount0']
        self.token1_collect_prot += event_row['amount1']

        self.token0_reserve -= event_row['amount0']
        self.token1_reserve -= event_row['amount1']

        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())

    def proc_flash(self, event_row):
        # -amount0 (usual negative) + paid0 = paid back amount0

        # self.token0_reserve += event_row['paid0']
        # self.token1_reserve += event_row['paid1']

        # The amount is to be collected later.

        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())
