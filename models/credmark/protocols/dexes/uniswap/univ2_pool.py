# pylint:disable=invalid-name, missing-function-docstring, too-many-instance-attributes, line-too-long, too-many-statements

"""
Uni V2 Pool
"""

from typing import Optional

import numpy as np
from credmark.cmf.model import ModelContext
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import Address, Contract, Maybe, Token

from models.credmark.protocols.dexes.uniswap.uni_pool_base import UniswapPoolBase
from models.dtos.pool import PoolPriceInfoWithVolume
from models.tmp_abi_lookup import UNISWAP_V2_POOL_ABI


class UniV2Pool(UniswapPoolBase):
    """
    Uniswap V2 Pool
    """

    EVENT_LIST = ['Sync', 'Swap', 'Mint', 'Burn']

    def __init__(self, pool_addr: Address, _protocol: str, _pool_data: Optional[dict] = None):
        super().__init__(self.EVENT_LIST, _protocol)
        if self.protocol == 'uniswap-v2':
            self.src = 'uniswap-v2.get-weighted-price'
        elif self.protocol == 'sushiswap':
            self.src = 'sushiswap.get-weighted-price'
        elif self.protocol == 'pancakeswap-v2':
            self.src = 'pancakeswap-v2.get-weighted-price'
        elif self.protocol == 'quickswap-v2':
            self.src = 'quickswap-v2.get-weighted-price'
        else:
            raise NotImplementedError(self.protocol)

        self.pool = Contract(address=pool_addr).set_abi(UNISWAP_V2_POOL_ABI, set_loaded=True)

        self.tick_spacing = 1

        self.token0_addr = self.pool.functions.token0().call().lower()
        self.token1_addr = self.pool.functions.token1().call().lower()

        self.df_evt = {}

        context = ModelContext.current_context()

        try:
            self.token0 = Token(Address(self.token0_addr).checksum)
            self.token0_decimals = self.token0.decimals
            self.token0_symbol = self.token0.symbol
        except (ModelDataError, OverflowError):
            try:
                self.token0 = Token(Address(
                    self.token0_addr).checksum).as_erc20(set_loaded=True, use_alt=True)
                self.token0_decimals = self.token0.decimals
                self.token0_symbol = self.token0.symbol
            except (ModelDataError, OverflowError):
                try:
                    self.token0 = Token(Address(
                        self.token0_addr).checksum).as_erc20(set_loaded=True)
                    self.token0_decimals = self.token0.decimals
                    self.token0_symbol = self.token0.symbol
                except (ModelDataError, OverflowError):
                    deployment = context.run_model(
                        'token.deployment-maybe', {'address': self.token0_addr}, return_type=Maybe[dict])
                    if not deployment.just:
                        raise ValueError(
                            f"Unable to find token deployment for {self.token0}") from None

                    deployment_block_number = deployment.just["deployed_block_number"]
                    with context.fork(block_number=deployment_block_number) as _past_context:
                        self.token0 = Token(Address(
                            self.token0_addr).checksum).as_erc20(set_loaded=True)
                        self.token0_decimals = self.token0.decimals
                        self.token0_symbol = self.token0.symbol

        try:
            self.token1 = Token(Address(self.token1_addr).checksum)
            self.token1_decimals = self.token1.decimals
            self.token1_symbol = self.token1.symbol
        except (ModelDataError, OverflowError):
            try:
                self.token1 = Token(address=Address(
                    self.token1_addr).checksum).as_erc20(set_loaded=True, use_alt=True)
                self.token1_decimals = self.token1.decimals
                self.token1_symbol = self.token1.symbol
            except (ModelDataError, OverflowError):
                try:
                    self.token1 = Token(address=Address(
                        self.token1_addr).checksum).as_erc20(set_loaded=True)
                    self.token1_decimals = self.token1.decimals
                    self.token1_symbol = self.token1.symbol
                except (ModelDataError, OverflowError):
                    deployment = context.run_model(
                        'token.deployment-maybe', {'address': self.token1_addr}, return_type=Maybe[dict])
                    if not deployment.just:
                        raise ValueError(
                            f"Unable to find token deployment for {self.token1}") from None

                    deployment_block_number = deployment.just["deployed_block_number"]
                    with context.fork(block_number=deployment_block_number) as _past_context:
                        self.token1 = Token(address=Address(
                            self.token1_addr).checksum).as_erc20(set_loaded=True)
                        self.token1_decimals = self.token1.decimals
                        self.token1_symbol = self.token1.symbol

        if _pool_data is None:
            self.reserve0 = 0
            self.reserve1 = 0

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
        pass

    def save(self):
        return {'block_number': self.block_number, 'log_index': self.log_index,
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
                'reserve0': self.reserve0,
                'reserve1': self.reserve1,
                }

    def load(self, _pool_data):
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

        self.reserve0 = _pool_data['reserve0']
        self.reserve1 = _pool_data['reserve1']

    def get_pool_price_info(self):
        full_tick_liquidity0 = self.token0.scaled(self.reserve0)
        full_tick_liquidity1 = self.token1.scaled(self.reserve1)
        one_tick_liquidity0 = np.abs(
            1 / np.sqrt(1 + 0.0001) - 1) * full_tick_liquidity0
        one_tick_liquidity1 = (np.sqrt(1 + 0.0001) - 1) * full_tick_liquidity1

        # When both liquidity are low, we set price to 0
        # if np.isclose(one_tick_liquidity0, 0) or np.isclose(one_tick_liquidity1, 0):
        #    ratio_price0 = 0
        #    ratio_price1 = 0
        try:
            ratio_price0 = full_tick_liquidity1 / full_tick_liquidity0
            ratio_price1 = 1 / ratio_price0
        except (FloatingPointError, ZeroDivisionError):
            ratio_price0 = 0
            ratio_price1 = 0

        pool_price_info = PoolPriceInfoWithVolume(
            src=self.src,
            price0=ratio_price0,
            price1=ratio_price1,
            one_tick_liquidity0=one_tick_liquidity0,
            one_tick_liquidity1=one_tick_liquidity1,
            full_tick_liquidity0=full_tick_liquidity0,
            full_tick_liquidity1=full_tick_liquidity1,
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

            if event_row['event'] == 'Sync':
                yield self.proc_sync(event_row)
            elif event_row['event'] == 'Swap':
                yield self.proc_swap(event_row)
            elif event_row['event'] == 'Burn':
                yield self.proc_burn(event_row)
            elif event_row['event'] == 'Mint':
                yield self.proc_mint(event_row)
            else:
                raise ValueError(f'Unknown event {event_row["event"]}')

    def proc_sync(self, event_row):
        self.reserve0 = event_row['reserve0']
        self.reserve1 = event_row['reserve1']

        # some pools' reserve may not match with all burn/mint amount, use sync
        self.token0_reserve = event_row['reserve0']
        self.token1_reserve = event_row['reserve1']
        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())

    def proc_swap(self, event_row):
        self.token0_in += event_row['amount0In']
        self.token0_out += event_row['amount0Out']
        self.token1_in += event_row['amount1In']
        self.token1_out += event_row['amount1Out']

        # self.token0_reserve += event_row['amount0In'] - event_row['amount0Out']
        # self.token1_reserve += event_row['amount1In'] - event_row['amount1Out']

        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())

    def proc_burn(self, event_row):
        self.token0_remove += event_row['amount0']
        self.token1_remove += event_row['amount1']

        # self.token0_reserve -= event_row['amount0']
        # self.token1_reserve -= event_row['amount1']

        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())

    def proc_mint(self, event_row):
        self.token0_add += event_row['amount0']
        self.token1_add += event_row['amount1']

        # self.token0_reserve += event_row['amount0']
        # self.token1_reserve += event_row['amount1']

        return (event_row['blockNumber'], event_row['logIndex'], self.get_pool_price_info())
