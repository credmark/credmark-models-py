from typing import (
    Union,
    Optional,
)

import credmark.model
from credmark.dto import (
    DTO,
)
from credmark.types import (
    Price,
    Token,
    Address,
    Contract,
    Contracts,
    BlockSeries,
)

from .....tmp_abi_lookup import UNISWAP_V2_SWAP_ABI

UNISWAP_V2_FACTORY_ADDRESS = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"


@credmark.model.describe(slug='uniswap-v2.get-pools',
                         version='1.0',
                         display_name='Uniswap v2 Token Pools',
                         description='The Uniswap v2 pools that support a token contract',
                         input=Token,
                         output=Contracts)
class UniswapV2GetPoolsForToken(credmark.model.Model):

    def run(self, input: Token) -> Contracts:

        factory = Contract(address=UNISWAP_V2_FACTORY_ADDRESS)
        tokens = [Token(symbol="USDC"),
                  Token(symbol="WETH"),
                  Token(symbol="DAI"),
                  Token(symbol="USDT")]
        contracts = []
        for token in tokens:
            pair_address = factory.functions.getPair(input.address, token.address).call()
            if not pair_address == Address.null():
                contracts.append(Contract(address=pair_address, abi=UNISWAP_V2_SWAP_ABI))
        return Contracts(contracts=contracts)


@credmark.model.describe(slug='uniswap-v2.get-average-price',
                         version='1.0',
                         display_name='Uniswap v2 Token Price',
                         description='The Uniswap v2 price, averaged by liquidity',
                         input=Token,
                         output=Price)
class UniswapV2GetAveragePrice(credmark.model.Model):
    def run(self, input: Token) -> Price:
        pools = self.context.run_model('uniswap-v2.get-pools',
                                       input,
                                       return_type=Contracts)

        prices = []
        reserves = []
        weth_price = None
        for pool in pools:
            reserves = pool.functions.getReserves().call()

            if input.address == pool.functions.token0().call():
                token1 = Token(address=pool.functions.token1().call())
                reserve = reserves[0]
                price = (reserves[1] / (10 ** token1.decimals)) / \
                    (reserves[0] / (10**input.decimals))
                if token1.symbol == 'WETH':
                    if weth_price is None:
                        weth_price = self.context.run_model('uniswap-v2.get-average-price',
                                                            token1,
                                                            return_type=Price).price
                    price = price * weth_price
            else:
                token0 = Token(address=pool.functions.token0().call())
                reserve = reserves[1]
                price = (reserves[0] / (10 ** token0.decimals)) / \
                    (reserves[1] / (10**input.decimals))
                if token0.symbol == 'WETH':
                    if weth_price is None:
                        weth_price = self.context.run_model('uniswap-v2.get-average-price',
                                                            token0,
                                                            return_type=Price).price
                    price = price * weth_price

            prices.append((price, reserve))
        if len(prices) == 0:
            return Price(price=None)
        return Price(price=sum([p * r for (p, r) in prices]) / sum([r for (p, r) in prices]))


class HistoricalPriceDTO(DTO):
    token: Token
    window: Union[str, list[str]]
    interval: Optional[str]


@credmark.model.describe(slug='uniswap-v2.get-historical-price',
                         version='1.0',
                         input=HistoricalPriceDTO,
                         output=BlockSeries[Price])
class UniswapV3GetAveragePrice30Day(credmark.model.Model):

    def run(self, input: HistoricalPriceDTO) -> BlockSeries[Price]:

        return self.context.historical.run_model_historical('uniswap-v2.get-average-price',
                                                            window=input.window,
                                                            interval=input.interval,
                                                            model_input=input.token)
