from typing import List, Optional, Generic, TypeVar
from credmark.cmf.types import Address, Currency, FiatCurrency, Token, Price
from credmark.dto import DTO, GenericDTO, DTOField, PrivateAttr, IterableListGenericDTO
from credmark.cmf.types.compose import MapBlockTimeSeriesInput

DTOCLS = TypeVar('DTOCLS')


class Prices(IterableListGenericDTO[Price]):
    prices: List[Price]
    _iterator: str = 'prices'


class Maybe(GenericDTO, Generic[DTOCLS]):
    just: Optional[DTOCLS] = DTOField(None)


class PriceInput(DTO):
    """
    In FX, the pair is quoted as base/quote for 1 base = x quote
    e.g. 1883.07 ETH / USD means 1883.07 USD for 1 ETH.

    *Base* token to get the value in the quote token
    *Quote* token to determine the value of the base token.

    If quote is not provided, default to the native token of the chain, i.e. ETH for Ethereum.

    Fiat is expressed in the currency code in ISO 4217.

    Base and quote can be either Token (symbol or address)
    or code (BTC, ETH, and all fiat, like USD, EUR, CNY, etc.)

    For fiat, with USD being the most active traded currency.
    It's direct quoting with (x USD/DOM) for x DOM = 1 USD, e.g. USD/JPY;
    and indirect quoting with (x DOM/USD) for x USD = 1 DOM, e.g. GBP/USD.

    For DeFi, we call it a direct quoting when the native token is the base.
    e.g. ETH / USD
    """

    base: Currency = \
        DTOField(description='Base token address to get the value for')
    quote: Currency = \
        DTOField(FiatCurrency(symbol='USD'),
                 description='Quote token address to count the value')

    def inverse(self):
        return PriceInput(base=self.quote, quote=self.base)

    def quote_usd(self):
        return PriceInput(base=self.base, quote=Currency(symbol='USD'))

    def quote_eth(self):
        return PriceInput(base=self.base, quote=Currency(symbol='ETH`'))

    class Config:
        schema_extra = {
            'examples': [{'base': {'symbol': 'USD'}},
                         {'base': {'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'},
                          'quote': {'symbol': 'USD'}}]
        }


class PriceInputs(IterableListGenericDTO[PriceInput]):
    inputs: List[PriceInput]
    _iterator: str = 'inputs'


class PriceHistoricalInput(PriceInput, MapBlockTimeSeriesInput):
    modelSlug: str = DTOField('price.quote', hidden=True)
    modelInput: dict = DTOField({}, hidden=True)
    endTimestamp: int = DTOField(0, hidden=True)


class PriceHistoricalInputs(PriceInputs, MapBlockTimeSeriesInput):
    modelSlug: str = DTOField('price.quote', hidden=True)
    modelInput: dict = DTOField({}, hidden=True)
    endTimestamp: int = DTOField(0, hidden=True)


class PoolPriceInfo(DTO):
    """
    @src: source
    @price: price derived from pool of stablecoin and WETH9
    @liquidity: Available liquidity in the pool for the token
    @weth_multiplier: WETH price used if one token is WETH9
    @inverse: True if token is the second token in the pool
    @token0_address: token0's address
    @token1_address: token1's address
    @token0_symbol: token0's symbol
    @token1_symbol: token1's symbol
    @token0_decimals: token0's decimals
    @token1_decimals: token1's decimals
    @pool_address: pool's address
    """
    src: str
    price: float
    liquidity: float
    weth_multiplier: float
    inverse: bool
    token0_address: Address
    token1_address: Address
    token0_symbol: str
    token1_symbol: str
    token0_decimals: int
    token1_decimals: int
    pool_address: Address


class PoolPriceInfos(IterableListGenericDTO[PoolPriceInfo]):
    pool_price_infos: List[PoolPriceInfo] = []
    _iterator: str = PrivateAttr('pool_price_infos')


class PoolPriceAggregatorInput(PoolPriceInfos):
    token: Token
    weight_power: float = DTOField(1.0, ge=1.0)
    price_src: str
