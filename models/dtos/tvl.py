from typing import List

from credmark.cmf.types import Address, Contract, Portfolio, PriceWithQuote
from credmark.dto import DTO


class TVLInfo(Contract):
    name: str
    portfolio: Portfolio
    prices: List[PriceWithQuote]
    tokens_symbol: List[str]
    tvl: float


class LendingPoolPortfolios(DTO):
    supply: Portfolio
    debt: Portfolio
    net: Portfolio
    prices: dict[Address, PriceWithQuote]
    supply_value: float
    debt_value: float
    net_value: float
    tvl: float
