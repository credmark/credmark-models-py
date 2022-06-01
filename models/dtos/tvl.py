from typing import List
from credmark.cmf.types import Contract, Portfolio, Price


class TVLInfo(Contract):
    name: str
    portfolio: Portfolio
    prices: List[Price]
    tokens_symbol: List[str]
    tvl: float
