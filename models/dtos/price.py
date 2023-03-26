from typing import Optional
from credmark.cmf.model import ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import (Contract, Currency, FiatCurrency,
                                Some, Token, Tokens)
from credmark.cmf.types.compose import MapBlockTimeSeriesInput
from credmark.dto import DTO, DTOField
from models.dtos.pool import PoolPriceInfo
from enum import Enum


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
        return __class__(base=self.quote, quote=self.base)

    def quote_usd(self):
        return __class__(base=self.base, quote=Currency(symbol='USD'))

    def quote_eth(self):
        return __class__(base=self.base, quote=Currency(symbol='ETH`'))

    class Config:
        schema_extra = {
            'examples': [{'base': {'symbol': 'USD'}},
                         {'base': {'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'},
                          'quote': {'symbol': 'USD'}}]
        }


class PriceSource(str, Enum):
    CEX = 'cex'
    DEX = 'dex'


class PriceInputWithPreference(PriceInput):
    prefer: PriceSource = DTOField(PriceSource.CEX, description='Preferred source')


class PriceHistoricalInput(PriceInputWithPreference, MapBlockTimeSeriesInput):
    modelSlug: str = DTOField('price.quote', hidden=True)
    modelInput: dict = DTOField({}, hidden=True)
    endTimestamp: int = DTOField(0, hidden=True)


class PriceHistoricalInputs(Some[PriceInputWithPreference], MapBlockTimeSeriesInput):
    modelSlug: str = DTOField('price.quote', hidden=True)
    modelInput: dict = DTOField({}, hidden=True)
    endTimestamp: int = DTOField(0, hidden=True)


class PriceWeight(DTO):
    weight_power: float = DTOField(4.0, ge=0.0)
    debug: bool = DTOField(False, description='Turn on debug log')


class DexPriceTokenInput(Token, PriceWeight):
    ...


class DexPriceTokensInput(Tokens, PriceWeight):
    ...


class DexPricePoolInput(Contract, PriceWeight):
    price_slug: str
    ref_price_slug: Optional[str]


class DexPoolAggregationInput(DexPriceTokenInput, Some[PoolPriceInfo]):
    ...


PRICE_DATA_ERROR_DESC = ModelDataErrorDesc(
    code=ModelDataError.Codes.NO_DATA,
    code_desc='No pool to aggregate for token price')
