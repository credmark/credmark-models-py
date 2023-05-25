# pylint: disable=line-too-long

from enum import Enum
from typing import List, Optional

from credmark.cmf.model import ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import Currency, FiatCurrency, Some, Token
from credmark.cmf.types.compose import MapBlockTimeSeriesInput
from credmark.dto import DTO, DTOField

from models.dtos.pool import PoolPriceInfo


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

    base: Currency = DTOField(description='Base token address to get the value for')
    quote: Currency = DTOField(FiatCurrency(symbol='USD'),
                               description='Quote token address to count the value')

    def inverse(self):
        return __class__(base=self.quote, quote=self.base)

    def quote_usd(self):
        return __class__(base=self.base, quote=Currency(symbol='USD'))

    def quote_eth(self):
        return __class__(base=self.base, quote=Currency(symbol='ETH`'))

    class Config:
        schema_extra = {
            'examples': [{"base": {"symbol": "CRV"}, '_test_multi_chain': {'chain_id': 1}},
                         {'base': {'symbol': 'USD'}},
                         {'base': {'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'},
                          'quote': {'symbol': 'USD'}},
                         {"base": "0xc40f949f8a4e094d1b49a23ea9241d289b7b2819",
                             '_test_multi_chain': {'chain_id': 10, 'block_number': None}},
                         {"base": 'ETH', '_test_multi_chain': {'chain_id': 10, 'block_number': None}},
                         {"base": "0x17fc002b466eec40dae837fc4be5c67993ddbd6f",
                             '_test_multi_chain': {'chain_id': 42161, 'block_number': None}},
                         {"base": 'ETH', '_test_multi_chain': {'chain_id': 42161, 'block_number': None}},
                         {"base": "0xabc9547b534519ff73921b1fba6e672b5f58d083",
                             '_test_multi_chain': {'chain_id': 43114, 'block_number': None}},
                         {"base": "0xb86abcb37c3a4b64f74f59301aff131a1becc787",
                             '_test_multi_chain': {'chain_id': 56, 'block_number': None}},
                         {"base": "0x5559edb74751a0ede9dea4dc23aee72cca6be3d5",
                             '_test_multi_chain': {'chain_id': 137, 'block_number': None}},
                         {"base": 'WETH', '_test_multi_chain': {'chain_id': 137, 'block_number': None}},
                         ],
            'test_multi_chain': True
        }


class PriceSource(str, Enum):
    CEX = 'cex'
    DEX = 'dex'


class PriceInputWithPreference(PriceInput):
    prefer: PriceSource = DTOField(
        PriceSource.CEX, description='Preferred source')
    try_other_chains: bool = DTOField(
        False, description='If prices are not found on the input chain, try other chains for prices.')


class PriceMultipleInput(DTO):
    slug: str = DTOField(description='Slug of the price model')
    some: List[PriceInputWithPreference]

    class Config:
        schema_extra = {
            'examples': [{
                'slug': 'price.quote-maybe',
                'some': [{'base': {'symbol': 'CRV'}},
                         {'base': {'symbol': 'AAVE', "quote": "JPY"}},
                         {'base': {'address': '0x6b175474e89094c44da98b954eedeac495271d0f',
                                   "quote": "CNY"}}]}]
        }


class PriceHistoricalInput(PriceInputWithPreference, MapBlockTimeSeriesInput):
    modelSlug: str = DTOField('price.quote', hidden=True)
    modelInput: dict = DTOField({}, hidden=True)
    endTimestamp: int = DTOField(0, hidden=True)

    class Config:
        schema_extra = {
            "examples": [{"base": {"symbol": "AAVE"}, "interval": 86400, "count": 1, "exclusive": True}]
        }


class PricesHistoricalInput(Some[PriceInputWithPreference], MapBlockTimeSeriesInput):
    modelSlug: str = DTOField('price.quote', hidden=True)
    modelInput: dict = DTOField({}, hidden=True)
    endTimestamp: int = DTOField(0, hidden=True)

    class Config:
        schema_extra = {
            "examples": [{"some": [{"base": {"symbol": "AAVE"}},
                                   {"base": {"address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"}}],
                          "interval": 86400, "count": 20, "exclusive": True}],
        }


class PriceWeight(DTO):
    weight_power: float = DTOField(4.0, ge=0.0)
    debug: bool = DTOField(False, description='Turn on debug log')


class DexPriceTokenInput(Token, PriceWeight):
    class Config:
        schema_extra = {
            'examples': [{'address': '0x6b175474e89094c44da98b954eedeac495271d0f'},  # DAI
                         {"symbol": "WETH"},
                         {"symbol": "WETH", "weight_power": 4.0, "debug": False}, ]
        }


class DexPricePoolInput(PriceWeight):
    price_slug: str
    ref_price_slug: Optional[str]


class DexPoolAggregationInput(DexPriceTokenInput, Some[PoolPriceInfo]):
    class Config:
        schema_extra = {
            'examples': [
                {"some": [
                    {"src": "uniswap-v2.get-weighted-price", "price0": 0.9528107174897676, "price1": 1.0495263976821705,
                     "one_tick_liquidity0": 0.001685478240180313, "one_tick_liquidity1": 0.0016060220264204467,
                     "full_tick_liquidity0": 33.712093, "full_tick_liquidity1": 32.12124351941178,
                        "token0_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "token1_address": "0xd533a949740bb3306d119cc777fa900ba034cd52",
                        "token0_symbol": "USDC", "token1_symbol": "CRV", "pool_address": "0x210a97ba874a8e279c95b350ae8ba143a143c159",
                        "ref_price": 1.0006473790684685, "tick_spacing": 1},
                    {"src": "uniswap-v2.get-weighted-price", "price0": 0.9511103469743591, "price1": 1.0514027138713893,
                     "one_tick_liquidity0": 0.0003462790926172877, "one_tick_liquidity1": 0.00032936609499925525,
                     "full_tick_liquidity0": 6.926101266677137, "full_tick_liquidity1": 6.58748657892884,
                        "token0_address": "0x6b175474e89094c44da98b954eedeac495271d0f", "token1_address": "0xd533a949740bb3306d119cc777fa900ba034cd52",
                        "token0_symbol": "DAI", "token1_symbol": "CRV", "pool_address": "0xf00f7a64b170d41789c6f16a7eb680a75a050e6d",
                        "ref_price": 0.99962940609268, "tick_spacing": 1},
                ],
                    "weight_power": 4.0, "debug": False, "address": "0xd533a949740bb3306d119cc777fa900ba034cd52"}
            ]
        }


PRICE_DATA_ERROR_DESC = ModelDataErrorDesc(
    code=ModelDataError.Codes.NO_DATA,
    code_desc='No pool to aggregate for token price')


class PriceBlocksInput(PriceInputWithPreference):
    block_numbers: List[int] = DTOField(description='List of blocks to run')

    class Config:
        schema_extra = {
            "examples": [
                {'base': {'symbol': 'CRV'}, 'quote': {'symbol': 'USD'}, 'block_numbers': [16_000_000, 16_001_000]},
            ]
        }
