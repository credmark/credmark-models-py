import pandas as pd
from pyrsistent import b
from web3.exceptions import (
    BadFunctionCallOutput,
)

from credmark.cmf.model import Model
from credmark.cmf.model.errors import (
    ModelDataError,
    ModelRunError,
)
from credmark.cmf.types import (
    Price,
    Token,
    Address,
    Contract,
    Contracts,
)

from credmark.dto import DTO

from models.tmp_abi_lookup import (
    UNISWAP_V3_POOL_ABI,
    UNISWAP_V3_FACTORY_ADDRESS,
    WETH9_ADDRESS,
)


class UniswapV3PoolInfo(DTO):
    address: Address
    sqrtPriceX96: float
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


@Model.describe(slug='uniswap-v3.get-pools',
                version='1.1',
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract',
                input=Token,
                output=Contracts)
class UniswapV3GetPoolsForToken(Model):
    def run(self, input: Token) -> Contracts:
        fees = [3000, 10000]
        primary_tokens = [Token(symbol='DAI'),
                          Token(symbol='USDT'),
                          Token(symbol='WETH'),
                          Token(symbol='USDC')]

        if self.context.chain_id != 1:
            return Contracts(contracts=[])

        try:
            uniswap_factory = Contract(address=UNISWAP_V3_FACTORY_ADDRESS)
            pools = []
            for fee in fees:
                for primary_token in primary_tokens:
                    if input.address and primary_token.address:
                        pool = uniswap_factory.functions.getPool(
                            input.address.checksum,
                            primary_token.address.checksum,
                            fee).call()
                        if pool != Address.null():
                            # TODO: ABI for 0x2a84e2bd2e961b1557d6e516ca647268b432cba4
                            # is not loaded in DB
                            pools.append(Contract(address=pool,
                                                  abi=UNISWAP_V3_POOL_ABI).info)

            return Contracts(contracts=pools)
        except BadFunctionCallOutput:
            # Or use this condition: if self.context.block_number < 12369621:
            return Contracts(contracts=[])


@Model.describe(slug='uniswap-v3.get-pool-info',
                version='1.1',
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract',
                input=Contract,
                output=UniswapV3PoolInfo)
class UniswapV3GetPoolInfo(Model):
    def run(self, input: Contract) -> UniswapV3PoolInfo:
        try:
            input.abi
        except ModelDataError:
            input = Contract(address=input.address, abi=UNISWAP_V3_POOL_ABI).info

        pool = input

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


@Model.describe(slug='uniswap-v3.get-average-price',
                version='1.0',
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract',
                input=Token,
                output=Price)
class UniswapV3GetAveragePrice(Model):
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

        prices_with_info = []
        weth_price = None
        for info in infos:
            # decimal only available for ERC20s
            if info.token0.decimals and info.token1.decimals:
                scale_multiplier = (10 ** (info.token0.decimals - info.token1.decimals))
                tick_price = 1.0001 ** info.tick * scale_multiplier

                if input.address == info.token1.address:
                    tick_price = 1/tick_price

                ratio_price = info.sqrtPriceX96 * info.sqrtPriceX96 / (2 ** 192) * scale_multiplier

                if input.address == info.token1.address:
                    ratio_price = 1/ratio_price

                weth_multipler = 1
                if input.address != WETH9_ADDRESS:
                    if WETH9_ADDRESS in (info.token1.address, info.token0.address):
                        if weth_price is None:
                            weth_price = self.context.run_model(self.slug,
                                                                {"address": WETH9_ADDRESS},
                                                                return_type=Price)
                            if weth_price.price is None:
                                raise ModelRunError('Can not retriev price for WETH')
                        weth_multipler = weth_price.price

                tick_price *= weth_multipler
                ratio_price *= weth_multipler

                prices_with_info.append((tick_price,
                                         ratio_price,
                                         info.address,
                                         info.tick,
                                         info.sqrtPriceX96,
                                         info.liquidity,
                                         info.fee,
                                         weth_multipler,
                                         info.token0.address, info.token1.address,
                                         info.token0.symbol, info.token1.symbol,
                                         info.token0.decimals, info.token1.decimals))

        if len(prices_with_info) == 0:
            return Price(price=None, src=self.slug)

        df = pd.DataFrame(prices_with_info,
                          columns=['tick_price', 'ratio_price', 'pool', 'tick', 'sqrtPriceX96',
                                   'liquidity', 'fee', 'weth_multiplier',
                                   'token0', 'token1', 't0', 't1', 't0dec', 't1dec'])
        df.liquidity = df.liquidity.astype(float)
        self.logger.debug(df.to_json())
        price = (df.tick_price * df.liquidity).sum() / df.liquidity.sum()
        return Price(price=price, src=self.slug)
