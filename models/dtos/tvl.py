from typing import List

from credmark.cmf.types import Contract, Portfolio, PriceWithQuote


class TVLInfo(Contract):
    name: str
    portfolio: Portfolio
    prices: List[PriceWithQuote]
    tokens_symbol: List[str]
    tvl: float
