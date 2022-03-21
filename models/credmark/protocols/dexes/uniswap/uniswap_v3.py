from typing import (
    Optional,
    Union,
)

import credmark.model
from credmark.types import (
    Price,
    Token,
    Address,
    Contract,
    Contracts,
    BlockSeries,
)

from credmark.dto import DTO

from models.tmp_abi_lookup import (
    UNISWAP_V3_FACTORY_ABI,
    UNISWAP_V3_FACTORY_ADDRESS,
    UNISWAP_V3_POOL_ABI,
    WETH9_ADDRESS,
)


class UniswapV3PoolInfo(DTO):
    address: Address
    sqrtPriceX96: str
    tick: int
    observationIndex: int
    observationCardinality: int
    observationCardinalityNext: int
    feeProtocol: int
    unlocked: bool
    liquidity: str
    fee: int
    token0: Token
    token1: Token


@credmark.model.describe(slug='uniswap-v3.get-pools',
                         version='1.0',
                         display_name='Uniswap v3 Token Pools',
                         description='The Uniswap v3 pools that support a token contract',
                         input=Token,
                         output=Contracts)
class UniswapV3GetPoolsForToken(credmark.model.Model):

    def run(self, input: Token) -> Contracts:

        fees = [500, 3000, 10000]
        primary_tokens = [Token(symbol='DAI'),
                          Token(symbol='WETH'),
                          Token(symbol='USDC'),
                          Token(symbol='USDT')]

        if self.context.chain_id != 1:
            return Contracts(contracts=[])

        uniswap_factory = Contract(address=UNISWAP_V3_FACTORY_ADDRESS,
                                   abi=UNISWAP_V3_FACTORY_ABI).instance

        pools = []

        for fee in fees:
            for primary_token in primary_tokens:
                if input.address and primary_token.address:
                    pool = uniswap_factory.functions.getPool(
                        input.address.checksum, primary_token.address.checksum, fee).call()
                    if pool != "0x0000000000000000000000000000000000000000":
                        pools.append(Contract(address=pool))

        return Contracts(contracts=pools)


@credmark.model.describe(slug='uniswap-v3.get-pool-info',
                         version='1.0',
                         display_name='Uniswap v3 Token Pools',
                         description='The Uniswap v3 pools that support a token contract',
                         input=Contract,
                         output=UniswapV3PoolInfo)
class UniswapV3GetPoolInfo(credmark.model.Model):
    def run(self, input: Contract) -> UniswapV3PoolInfo:
        input.abi = UNISWAP_V3_POOL_ABI
        pool = input.instance

        slot0 = pool.functions.slot0().call()
        token0 = pool.functions.token0().call()
        token1 = pool.functions.token1().call()
        liquidity = pool.functions.liquidity().call()
        fee = pool.functions.fee().call()
        res = {
            "address": input.address,
            "sqrtPriceX96": slot0[0],
            "tick": slot0[1],
            "observationIndex": slot0[2],
            "observationCardinality": slot0[3],
            "observationCardinalityNext": slot0[4],
            "feeProtocol": slot0[5],
            "unlocked": slot0[6],
            "token0": Token(address=token0),
            "token1": Token(address=token1),
            "liquidity": liquidity,
            "fee": fee
        }

        return UniswapV3PoolInfo(**res)


@credmark.model.describe(slug='uniswap-v3.get-average-price',
                         version='1.0',
                         display_name='Uniswap v3 Token Pools',
                         description='The Uniswap v3 pools that support a token contract',
                         input=Token,
                         output=Price)
class UniswapV3GetAveragePrice(credmark.model.Model):
    def run(self, input: Token) -> Price:
        pools = self.context.run_model('uniswap-v3.get-pools',
                                       input,
                                       return_type=Contracts)

        infos = [
            self.context.run_model('uniswap-v3.get-pool-info',
                                   p,
                                   return_type=UniswapV3PoolInfo)
            for p in pools
        ]

        prices = []
        weth_prices = None
        for info in infos:
            # decimal only available for ERC20s
            if info.token0.decimals and info.token1.decimals:
                tick_price = 1.0001 ** info.tick * \
                    (10 ** (info.token0.decimals - info.token1.decimals))
                if input.address == info.token1.address:
                    tick_price = 1/tick_price

                if input.address != WETH9_ADDRESS:
                    if WETH9_ADDRESS in (info.token1.address, info.token0.address):
                        if weth_prices is None:
                            weth_prices = self.context.run_model('uniswap-v3.get-average-price',
                                                                 {"address": WETH9_ADDRESS},
                                                                 return_type=Price).price
                        tick_price = tick_price * weth_prices

                prices.append(tick_price)

        if len(prices) == 0:
            return Price(price=None)

        price = sum(prices) / len(prices)

        return Price(price=price)


class HistoricalPriceDTO(DTO):
    token: Token
    window: Union[str, list[str]]
    interval: Optional[str]


@credmark.model.describe(slug='uniswap-v3.get-historical-price',
                         version='1.0',
                         input=HistoricalPriceDTO,
                         output=BlockSeries[Price])
class UniswapV3GetAveragePrice30Day(credmark.model.Model):

    def run(self, input: HistoricalPriceDTO) -> BlockSeries[Price]:

        return self.context.historical.run_model_historical('uniswap-v3.get-average-price',
                                                            window=input.window,
                                                            interval=input.interval,
                                                            model_input=input.token)
