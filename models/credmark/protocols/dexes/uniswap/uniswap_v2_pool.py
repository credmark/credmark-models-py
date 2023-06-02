# pylint: disable=too-many-lines, unsubscriptable-object, line-too-long

from typing import List

import numpy as np
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import (
    Address,
    Contract,
    Maybe,
    Portfolio,
    Position,
    PriceWithQuote,
    Token,
    Tokens,
)
from credmark.dto import DTO
from web3.exceptions import (
    ABIFunctionNotFound,
    ContractLogicError,
)

from models.credmark.protocols.dexes.uniswap.uniswap_ref_price_meta import UniswapRefPriceMeta
from models.dtos.pool import PoolPriceInfo
from models.dtos.price import DexPoolPriceInput
from models.dtos.tvl import TVLInfo
from models.tmp_abi_lookup import UNISWAP_V2_POOL_ABI


class UniswapV2Pool(Contract):
    class Config:
        schema_extra = {
            "examples": [{"address": "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852"}]
        }


class UniswapV2DexPoolPriceInput(UniswapV2Pool, DexPoolPriceInput):
    class Config:
        schema_extra = {
            'examples': [{"address": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
                          "price_slug": "uniswap-v2.get-weighted-price",
                          "ref_price_slug": "uniswap-v2.get-ring0-ref-price",
                          "weight_power": 4.0,
                          "protocol": "uniswap-v2"},

                         {"address": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
                          "price_slug": "uniswap-v2.get-weighted-price",
                          "ref_price_slug": None,  # use None to not use reference price
                          "weight_power": 4.0,
                          "protocol": "uniswap-v2"}]
        }

# credmark-dev run uniswap-v2.get-pool-price-info


@Model.describe(slug='uniswap-v2.get-pool-price-info',
                version='1.23',
                display_name='Uniswap v2 Token Pool Price Info',
                description='Gather price and liquidity information from pool',
                category='protocol',
                subcategory='uniswap-v2',
                input=UniswapV2DexPoolPriceInput,
                output=Maybe[PoolPriceInfo])
class UniswapPoolPriceInfo(UniswapRefPriceMeta):
    """
    Model to be shared between Uniswap V2 and SushiSwap and PancakeSwap V2
    """

    def run(self, input: UniswapV2DexPoolPriceInput) -> Maybe[PoolPriceInfo]:
        pool = input
        pool = (Contract(address=input.address)
                .set_abi(abi=UNISWAP_V2_POOL_ABI, set_loaded=True))

        reserves = pool.functions.getReserves().call()
        if reserves == [0, 0, 0]:
            return Maybe[PoolPriceInfo].none()

        # Pool initial setup
        token0_addr = Address(pool.functions.token0().call())
        token1_addr = Address(pool.functions.token1().call())

        try:
            token0 = Token(address=token0_addr).as_erc20(set_loaded=True)
            token0_symbol = token0.symbol
        except (OverflowError, ContractLogicError):
            token0 = Token(address=token0_addr).as_erc20()
            token0_symbol = token0.symbol

        try:
            token1 = Token(address=token1_addr).as_erc20(set_loaded=True)
            token1_symbol = token1.symbol
        except (OverflowError, ContractLogicError):
            token1 = Token(address=token1_addr).as_erc20()
            token1_symbol = token1.symbol

        scaled_reserve0 = token0.scaled(reserves[0])
        scaled_reserve1 = token1.scaled(reserves[1])

        # https://uniswap.org/blog/uniswap-v3-dominance
        # Appendix B: methodology
        try:
            tick_price0 = scaled_reserve1 / scaled_reserve0
            tick_price1 = 1 / tick_price0
        except (FloatingPointError, ZeroDivisionError):
            tick_price0 = 0
            tick_price1 = 0

        full_tick_liquidity0 = scaled_reserve0
        one_tick_liquidity0 = np.abs(
            1 / np.sqrt(1 + 0.0001) - 1) * full_tick_liquidity0

        full_tick_liquidity1 = scaled_reserve1
        one_tick_liquidity1 = (np.sqrt(1 + 0.0001) - 1) * full_tick_liquidity1

        # ref_price calculation
        ref_price, tick_price0, tick_price1 = self.get_ref_price(
            input,
            token0_addr, token1_addr,
            token0_symbol, token1_symbol,
            tick_price0, tick_price1,
            None
        )

        pool_price_info = PoolPriceInfo(src=input.price_slug,
                                        price0=tick_price0,
                                        price1=tick_price1,
                                        one_tick_liquidity0=one_tick_liquidity0,
                                        one_tick_liquidity1=one_tick_liquidity1,
                                        full_tick_liquidity0=full_tick_liquidity0,
                                        full_tick_liquidity1=full_tick_liquidity1,
                                        token0_address=token0_addr,
                                        token1_address=token1_addr,
                                        token0_symbol=token0_symbol,
                                        token1_symbol=token1_symbol,
                                        ref_price=ref_price,
                                        pool_address=input.address,
                                        tick_spacing=1)

        return Maybe[PoolPriceInfo](just=pool_price_info)


class UniswapV2PoolInfo(DTO):
    pool_address: Address
    tokens: Tokens
    tokens_name: List[str]
    tokens_symbol: List[str]
    tokens_decimals: List[int]
    tokens_balance: List[float]
    tokens_price: List[PriceWithQuote]
    ratio: float


@Model.describe(slug='uniswap-v2.get-pool-info',
                version="1.11",
                display_name="Uniswap/SushiSwap get details for a pool",
                description="Returns the token details of the pool",
                category='protocol',
                subcategory='uniswap-v2',
                input=UniswapV2Pool,
                output=UniswapV2PoolInfo)
class UniswapGetPoolInfo(Model):
    def run(self, input: UniswapV2Pool) -> UniswapV2PoolInfo:
        pool = input
        try:
            _ = pool.abi
        except ModelDataError:
            pool = Contract(address=input.address).set_abi(
                abi=UNISWAP_V2_POOL_ABI, set_loaded=True)

        token0 = Token(address=pool.functions.token0().call())
        token1 = Token(address=pool.functions.token1().call())
        # getReserves = contract.functions.getReserves().call()

        token0_balance = token0.balance_of_scaled(input.address.checksum)
        token1_balance = token1.balance_of_scaled(input.address.checksum)
        # token0_reserve = token0.scaled(getReserves[0])
        # token1_reserve = token1.scaled(getReserves[1])

        prices = []
        prices.append(self.context.run_model(
            'price.dex-maybe',
            input={'base': token0},
            return_type=Maybe[PriceWithQuote]).just)
        prices.append(self.context.run_model(
            'price.dex-maybe',
            input={'base': token1},
            return_type=Maybe[PriceWithQuote]).just)

        value0 = prices[0].price * token0_balance
        value1 = prices[1].price * token1_balance

        if value0 == 0 and value1 == 0:
            balance_ratio = 0
        else:
            balance_ratio = value0 * value1 / (((value0 + value1)/2)**2)

        pool_info = UniswapV2PoolInfo(
            pool_address=input.address,
            tokens=Tokens(tokens=[token0, token1]),
            tokens_name=[token0.name, token1.name],
            tokens_symbol=[token0.symbol, token1.symbol],
            tokens_decimals=[token0.decimals, token1.decimals],
            tokens_balance=[token0_balance, token1_balance],
            tokens_price=prices,
            ratio=balance_ratio
        )

        return pool_info


@Model.describe(slug='uniswap-v2.pool-tvl',
                version='1.8',
                display_name='Uniswap/SushiSwap Token Pool TVL',
                description='Gather price and liquidity information from pools',
                category='protocol',
                subcategory='uniswap-v2',
                input=UniswapV2Pool,
                output=TVLInfo)
class UniswapV2PoolTVL(Model):
    def run(self, input: UniswapV2Pool) -> TVLInfo:
        pool_info = self.context.run_model('uniswap-v2.get-pool-info',
                                           input=input,
                                           return_type=UniswapV2PoolInfo)
        positions = []
        prices = []
        tvl = 0.0

        prices = []
        for token_info, tok_price, bal in zip(pool_info.tokens,
                                              pool_info.tokens_price,
                                              pool_info.tokens_balance):
            prices.append(tok_price)
            tvl += bal * tok_price.price
            positions.append(Position(asset=token_info, amount=bal))

        try:
            pool_name = input.functions.name().call()
        except (ABIFunctionNotFound, ModelDataError):
            pool_name = 'Uniswap V3'

        tvl_info = TVLInfo(
            address=input.address,
            name=pool_name,
            portfolio=Portfolio(positions=positions),
            tokens_symbol=pool_info.tokens_symbol,
            prices=prices,
            tvl=tvl
        )

        return tvl_info


class UniswapV2PoolLPPosition(DTO):
    token0: Token
    token1: Token
    token0_amount: float
    token1_amount: float
    token0_reserve: float
    token1_reserve: float
    total_supply_scaled: float


@Model.describe(slug='uniswap-v2.lp-amount',
                version='0.2',
                display_name=('Decompose a UniswapV2Pair into its underlying tokens'),
                description='To calculate the value of a UniswapV2 LP token from its underlying tokens',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=UniswapV2Pool,
                output=UniswapV2PoolLPPosition,)
class PriceDexUniswapV2(Model):
    """
    Return token's price from
    """

    def run(self, input: UniswapV2Pool) -> UniswapV2PoolLPPosition:
        pool = Token(input.address)
        if pool.contract_name == 'UniswapV2Pair':
            token0 = Token(pool.functions.token0().call())
            token1 = Token(pool.functions.token1().call())
            total_supply_scaled = pool.total_supply_scaled
            token0_reserve, token1_reserve,  _blockTimestampLast = pool.functions.getReserves().call()
            token0_balance_scaled = token0.scaled(token0_reserve)
            token1_balance_scaled = token1.scaled(token1_reserve)
            self.logger.info(
                f'token0_balance_scaled: {token0_balance_scaled}, {token0.balance_of_scaled(pool.address.checksum)}')
            self.logger.info(
                f'token1_balance_scaled: {token1_balance_scaled}, {token1.balance_of_scaled(pool.address.checksum)}')
            return UniswapV2PoolLPPosition(
                token0=token0,
                token1=token1,
                token0_amount=token0_balance_scaled / total_supply_scaled,
                token1_amount=token1_balance_scaled / total_supply_scaled,
                token0_reserve=token0_balance_scaled,
                token1_reserve=token1_balance_scaled,
                total_supply_scaled=total_supply_scaled,
            )

        raise ModelDataError(f'Contract {input.address} is not a UniswapV2Pair')
