# pylint:disable=invalid-name, missing-function-docstring, too-many-instance-attributes, line-too-long

"""
Uni V3 Pool
"""

import math
import sys
from typing import Optional, cast

import pandas as pd
from credmark.cmf.model import ModelContext
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import Address, Contract, Token
from credmark.dto import DTO

from models.credmark.protocols.dexes.uniswap.uni_pool_base import UniswapPoolBase, fetch_events_with_cols
from models.credmark.protocols.dexes.uniswap.uniswap_v3_pool import fix_univ3_pool
from models.credmark.protocols.dexes.uniswap.univ3_math import calculate_onetick_liquidity, in_range, out_of_range
from models.dtos.pool import PoolPriceInfoWithVolume


class Tick(DTO):
    """
    // 1.0001^tick is token1/token0.
    let price0 = bigDecimalExponated(BigDecimal.fromString('1.0001'), BigInt.fromI32(tickIdx))
    tick.price0 = price0
    tick.price1 = safeDiv(ONE_BD, price0)
    """

    liquidityGross: int
    liquidityNet: int

    def is_zero(self):
        return self.liquidityGross == 0 and self.liquidityNet == 0


class UniV3Pool(UniswapPoolBase):
    """
    Uniswap V3 Pool
    """

    EVENT_LIST = ['Initialize', 'Collect', 'CollectProtocol', 'Flash', 'Swap', 'Mint', 'Burn']

    def __init__(self, pool_addr: Address, _protocol: str, _pool_data: Optional[dict] = None):
        self._balance = {}
        self._call_balance = 0
        self._call_balance_skip = 0

        super().__init__(self.EVENT_LIST, _protocol)
        if self.protocol == 'uniswap-v3':
            self.src = 'uniswap-v3.get-weighted-price'
        elif self.protocol == 'pancakeswap-v3':
            self.src = 'pancakeswap-v3.get-weighted-price'
        elif self.protocol == 'quickswap-v3':
            self.src = 'quickswap-v3.get-weighted-price'
        else:
            raise NotImplementedError(self.protocol)

        self.pool = Contract(address=pool_addr)
        self.pool = fix_univ3_pool(self.pool)

        self.tick_spacing = cast(int, self.pool.functions.tickSpacing().call())

        self.token0_addr = cast(str, self.pool.functions.token0().call()).lower()
        self.token1_addr = cast(str, self.pool.functions.token1().call()).lower()

        try:
            self.token0 = Token(Address(self.token0_addr).checksum)
            self.token0_decimals = self.token0.decimals
            self.token0_symbol = self.token0.symbol
        except ModelDataError:
            self.token0 = Token(Address(
                self.token0_addr).checksum).as_erc20(set_loaded=True)
            self.token0_decimals = self.token0.decimals
            self.token0_symbol = self.token0.symbol

        try:
            self.token1 = Token(Address(self.token1_addr).checksum)
            self.token1_decimals = self.token1.decimals
            self.token1_symbol = self.token1.symbol
        except ModelDataError:
            self.token1 = Token(address=Address(
                self.token1_addr).checksum).as_erc20(set_loaded=True)
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
            self.token0_flash = 0
            self.token1_flash = 0

            self.token0_reserve = 0
            self.token1_reserve = 0
        else:
            self.load(_pool_data)

            # Over time token0_reserve and token1_reserve will receive more than the liquidity amount
            # Let's sync when we update.
            if self.previous_block_number is not None:
                # context = ModelContext.current_context()
                # with context.enter(self.previous_block_number):
                #    self.token0_reserve = self.token0.balance_of(self.pool.address.checksum)
                #    self.token1_reserve = self.token1.balance_of(self.pool.address.checksum)

                def _one_time_collect_refresh():
                    if self.pool.abi is None:
                        raise ValueError(f'Pool abi missing for {self.pool.address}')

                    self.df_evt['Collect'] = fetch_events_with_cols(
                        self.pool, self.pool.events.Collect,
                        'Collect', 0, self.previous_block_number,
                        self.pool.abi.events.Collect.args,
                        True, 3)

                    if self.df_evt['Collect'].empty:
                        self.token0_collect = int(0)
                        self.token1_collect = int(0)
                    else:
                        self.token0_collect = sum(self.df_evt['Collect'].amount0.to_list())
                        self.token1_collect = sum(self.df_evt['Collect'].amount1.to_list())

                # _one_time_collect_refresh()

            def _rebuild_reserve_from_liquidity():
                # INCOMPLETE: Not easy as we also need the reward
                df_ticks = (pd.DataFrame(self.ticks).T
                            .reset_index(drop=False)
                            .assign(liquidityGross=lambda x: [y[1] for y in x[0]],
                                    liquidityNet=lambda x: [y[1] for y in x[1]])
                            .drop(columns=[0, 1])
                            .sort_values('index'))

                df_ticks.loc[:, 'liquidityCumsum'] = df_ticks.liquidityNet.cumsum()
                df_ticks.loc[:, 'upperTick'] = df_ticks['index'].shift(-1)

                t0 = 0
                t1 = 0
                for row in df_ticks.itertuples():
                    if math.isnan(row.upperTick):
                        continue
                    if row.index <= self.pool_tick < row.upperTick:
                        t0_t, t1_t = in_range(row.liquidityCumsum,
                                              row.upperTick, row.index, self.pool_tick)
                    else:
                        t0_t, t1_t = out_of_range(row.liquidityCumsum, row.upperTick, row.index)
                    t0 += t0_t
                    t1 += t1_t
                    print((t0, t1, t0_t, t1_t))

    def __del__(self):
        if self._call_balance != 0:
            print(f'Saved call to balance_of @ {self.block_number} '
                  f'({self._call_balance_skip}/{self._call_balance})',
                  file=sys.stderr, flush=True)

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
                'token0_flash': self.token0_flash,
                'token1_flash': self.token1_flash,

                'token0_reserve': self.token0_reserve,
                'token1_reserve': self.token1_reserve,
                }

    def load(self, _pool_data):
        self.pool_tick = _pool_data['pool_tick']
        self.pool_sqrtPrice = _pool_data['pool_sqrtPrice']
        self.pool_liquidity = _pool_data['pool_liquidity']
        self.ticks = {int(float(k)): Tick(**v)
                      for k, v in _pool_data['ticks'].items()}
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
        self.token0_collect = _pool_data['token0_collect']
        self.token0_collect_prot = _pool_data['token0_collect_prot']
        self.token1_add = _pool_data['token1_add']
        self.token1_remove = _pool_data['token1_remove']
        self.token1_collect = _pool_data['token1_collect']
        self.token1_collect_prot = _pool_data['token1_collect_prot']

        self.token0_reserve = _pool_data['token0_reserve']
        self.token1_reserve = _pool_data['token1_reserve']

        self.token0_flash = _pool_data.get('token0_flash', 0)
        self.token1_flash = _pool_data.get('token1_flash', 0)

    def _self_check_events(self, df_comb_evt):
        token0_balance = \
            sum(self.df_evt['Mint'].amount0.to_list()) - \
            sum(self.df_evt['Collect'].amount0.to_list()) - \
            (0 if self.df_evt['CollectProtocol'].empty else sum(self.df_evt['CollectProtocol'].amount0.to_list())) + \
            sum(self.df_evt['Swap'].amount0.to_list())
        token1_balance = \
            sum(self.df_evt['Mint'].amount1.to_list()) - \
            sum(self.df_evt['Collect'].amount1.to_list()) - \
            (0 if self.df_evt['CollectProtocol'].empty else sum(self.df_evt['CollectProtocol'].amount1.to_list())) + \
            sum(self.df_evt['Swap'].amount1.to_list())

        if not df_comb_evt.empty:
            context = ModelContext.current_context()
            with context.fork(block_number=int(df_comb_evt.blockNumber.max())):
                token0_reserve = self.token0.balance_of(self.pool.address.checksum)
                token1_reserve = self.token1.balance_of(self.pool.address.checksum)

            try:
                assert token0_balance <= token0_reserve
                assert token1_balance <= token1_reserve
            except AssertionError as err:
                raise err

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
            self.pool_tick,
            self.tick_spacing,
            self.token0,
            self.token1,
            self.pool_liquidity,
            _liquidityNet)

        ratio_price0, ratio_price1 = self.sqrtPriceX96toTokenPrices(
            self.pool_sqrtPrice)

        # Use reserve to cap the one tick liquidity
        # Example: 0xf1d2172d6c6051960a289e0d7dca9e16b65bfc64, around block 17272381, May 16 2023 8pm GMT+8

        if self.block_number is None:
            raise ValueError('Block number is not set')

        # TODO: the reserve is fetched at the point of event.
        # The reserve may change after the event (question to be answered)
        # Token: 0xd46ba6d942050d489dbd938a2c909a5d5039a161 AMPL
        # Pool: 0x86d257cdb7bc9c0df10e84c8709697f92770b335
        self._call_balance += 1
        try_balance = self._balance.get(int(self.block_number))
        if try_balance:
            self._call_balance_skip += 1
            self.token0_reserve, self.token1_reserve = try_balance
        else:
            context = ModelContext.current_context()
            with context.fork(block_number=int(self.block_number)):
                self.token0_reserve = self.token0.balance_of(self.pool.address.checksum)
                self.token1_reserve = self.token1.balance_of(self.pool.address.checksum)
                self._balance[int(self.block_number)] = self.token0_reserve, self.token1_reserve

        reserve0_scaled = self.token0.scaled(self.token0_reserve)
        reserve1_scaled = self.token1.scaled(self.token1_reserve)

        # Adjust liquidity to the max of the reserve
        if reserve0_scaled < one_tick_liquidity0_adj or reserve1_scaled < one_tick_liquidity1_adj:
            balance2liquidity0_ratio = reserve0_scaled / one_tick_liquidity0_adj
            balance2liquidity1_ratio = reserve1_scaled / one_tick_liquidity1_adj
            if balance2liquidity0_ratio < balance2liquidity1_ratio:
                one_tick_liquidity0 = reserve0_scaled
                one_tick_liquidity1 = balance2liquidity0_ratio * one_tick_liquidity1_adj
            else:
                one_tick_liquidity0 = balance2liquidity1_ratio * one_tick_liquidity0_adj
                one_tick_liquidity1 = reserve1_scaled
        else:
            one_tick_liquidity0 = one_tick_liquidity0_adj
            one_tick_liquidity1 = one_tick_liquidity1_adj

        # if np.isclose(one_tick_liquidity0_adj, 0) or np.isclose(one_tick_liquidity1_adj, 0):
        #    ratio_price0 = 0
        #    ratio_price1 = 0

        pool_price_info = PoolPriceInfoWithVolume(
            src=self.src,
            price0=ratio_price0,
            price1=ratio_price1,
            one_tick_liquidity0=one_tick_liquidity0,
            one_tick_liquidity1=one_tick_liquidity1,
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

            reserve0=reserve0_scaled,
            reserve1=reserve1_scaled,
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

        if tickLower not in self.ticks:
            self.ticks[tickLower] = Tick(liquidityGross=0, liquidityNet=0)

        if tickUpper not in self.ticks:
            self.ticks[tickUpper] = Tick(liquidityGross=0, liquidityNet=0)

        self.ticks[tickLower].liquidityGross += amount
        self.ticks[tickLower].liquidityNet += amount
        self.ticks[tickUpper].liquidityGross += amount
        self.ticks[tickUpper].liquidityNet -= amount

        if tickLower <= self.pool_tick < tickUpper:
            self.pool_liquidity += amount

        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())

    def proc_burn(self, event_row):
        tickLower = event_row['tickLower']
        tickUpper = event_row['tickUpper']
        amount = event_row['amount']
        amount0 = event_row['amount0']
        amount1 = event_row['amount1']

        if amount == 0 and amount0 == 0 and amount1 == 0:
            return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())

        self.token0_remove += amount0
        self.token1_remove += amount1
        # token0_reserve / token1_reserve changes is moved to proc_collect

        self.ticks[tickLower].liquidityGross -= amount
        self.ticks[tickLower].liquidityNet -= amount
        self.ticks[tickUpper].liquidityGross -= amount
        self.ticks[tickUpper].liquidityNet += amount

        if self.ticks[tickLower].is_zero():
            del self.ticks[tickLower]

        if self.ticks[tickUpper].is_zero():
            del self.ticks[tickUpper]

        if tickLower <= self.pool_tick < tickUpper:
            self.pool_liquidity -= amount

        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())

    def proc_swap(self, event_row):
        self.pool_liquidity = event_row['liquidity']
        self.pool_tick = event_row['tick']
        self.pool_sqrtPrice = event_row['sqrtPriceX96']

        amount0 = event_row['amount0']
        amount1 = event_row['amount1']

        self.token0_in += 0 if amount0 < 0 else amount0
        self.token0_out += (- amount0) if amount0 < 0 else 0
        self.token1_in += 0 if amount1 < 0 else amount1
        self.token1_out += (- amount1) if amount1 < 0 else 0

        self.token0_reserve += amount0
        self.token1_reserve += amount1

        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())

    def proc_collect(self, event_row):
        amount0 = event_row['amount0']
        amount1 = event_row['amount1']

        self.token0_collect += amount0
        self.token1_collect += amount1

        # collect is amount from burn + fee
        self.token0_reserve -= amount0
        self.token1_reserve -= amount1

        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())

    def proc_collect_prot(self, event_row):
        amount0 = event_row['amount0']
        amount1 = event_row['amount1']

        self.token0_collect_prot += amount0
        self.token1_collect_prot += amount1

        self.token0_reserve -= amount0
        self.token1_reserve -= amount1

        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())

    def proc_flash(self, event_row):
        # -amount0 (usual negative) + paid0 = paid back amount0

        self.token0_reserve += event_row['paid0']
        self.token1_reserve += event_row['paid1']

        self.token0_flash += event_row['amount0']
        self.token1_flash += event_row['amount1']

        # The amount is to be collected later.
        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())
