# pylint: disable=line-too-long

from datetime import datetime
from typing import List, Optional, Tuple

from credmark.cmf.types import Address, Contract, Portfolio, PriceList, Token
from credmark.dto import (
    DTO,
    DTOField,
    IterableListGenericDTO,
    PrivateAttr,
    cross_examples,
)

from models.credmark.algorithms.value_at_risk.risk_method import VaROutput


class VaRHistoricalInput(IterableListGenericDTO[PriceList]):
    portfolio: Portfolio
    priceLists: List[PriceList]
    interval: int
    confidence: float
    _iterator: str = PrivateAttr('priceLists')

    class Config:
        schema_extra = {
            'description': 'Historical VaR input - priceList need not to have prices for all positions in the portfolio',
            'examples': [
                {'portfolio': {'positions': [
                    {'amount': 100.0, 'asset': {'address': '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9'}},
                    {'amount': 100.0, 'asset': {'address': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'}},
                    {'amount': 1.0, 'asset': {'address': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'}}]},
                 'priceLists': [
                     {'prices': [float(i) for i in range(1, 31+1)],
                      'tokenAddress': '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9', 'src': 'finance.example-historical-price'},
                    {'prices': [float(i) for i in range(1, 31+1)],
                         'tokenAddress': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'src': 'finance.example-historical-price'}],
                 'interval': 3,
                 'confidence': 0.01}
            ]}


class VaRHistoricalOutput(DTO):
    class ValueList(DTO):
        token: Token
        amount: float
        price: float
        value: float

    cvar: List[float] = DTOField(description='VaR components')
    var: float = DTOField(description='VaR')
    total_value: float = DTOField(description='VaR')
    value_list: List[ValueList] = DTOField(
        description='List of portfolio items')

    @classmethod
    def default(cls):
        return cls(cvar=[], var=VaROutput.default().var, total_value=0, value_list=[])


class VaRInput(DTO):
    window: str
    interval: int
    confidence: float

    class Config:
        schema_extra = {
            'examples': [
                {'window': '3 days',
                 'interval': 1,
                 'confidence': 0.5
                 }]
        }


class PortfolioVaRInput(VaRInput):
    portfolio: Portfolio

    class Config:
        schema_extra = {
            'examples': [{"window": "20 days", "interval": 1, "confidence": 0.01,
                          "portfolio": {"positions":
                                        [{"amount": 10, "asset": {"address": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"}}]
                                        }}]
        }


class AccountVaRInput(VaRInput):
    address: Address

    class Config:
        schema_extra = {
            'examples': cross_examples(
                VaRInput.Config.schema_extra['examples'],
                [{'address': v}
                 for v in ['0x5291fBB0ee9F51225f0928Ff6a83108c86327636',
                           '0x912a0a41b820e1fa660fb6ec07fff493e015f3b2']],
                limit=10)
        }


class UniswapPoolVaRInput(VaRInput):
    lower_range: float = DTOField(
        description='Lower bound to the current price for V3 pool')
    upper_range: float = DTOField(
        description="Upper bound to the current price for V3 pool")
    pool: Contract

    class Config:
        schema_extra = {
            'examples': [{"pool": {"address": "0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8"},  # USDC-WETH  Uniswap V3
                          "window": "30 days", "interval": 1, "confidence": 0.05, "lower_range": 0.03, "upper_range": 0.03},
                         {"pool": {"address": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"},  # USDC-WETH Uniswap V2
                         "window": "30 days", "interval": 10, "confidence": 0.01, "lower_range": 0.01, "upper_range": 0.01},
                         ]


        }


class DexVaR(DTO):
    var: float
    scenarios: List[datetime]
    ppl: List[float]
    weights: List[float]


class UniswapPoolVaROutput(DTO):
    pool: Contract
    tokens_address: List[Address]
    tokens_symbol: List[str]
    ratio: float
    IL_type: str
    lp_range: Optional[Tuple[float, float]]
    var: DexVaR
    var_without_il: DexVaR
    var_il: DexVaR
