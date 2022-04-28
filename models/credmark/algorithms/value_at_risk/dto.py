from datetime import date
from typing import List

from credmark.dto import (
    DTO,
    IterableListGenericDTO,
    PrivateAttr,
)

from credmark.cmf.types import (
    Portfolio,
    Token,
    PriceList,
)


class HistoricalPriceInput(DTO):
    token: Token
    window: str  # e.g. '30 day'
    asOf: date


class VaRHistoricalInput(IterableListGenericDTO[PriceList]):
    portfolio: Portfolio
    priceLists: List[PriceList]
    interval: int  # 1 or 2 or 10
    confidences: List[float]
    _iterator: str = PrivateAttr('priceLists')


class ContractVaRInput(DTO):
    asOf: date
    window: str
    interval: int  # 1 or 2 or 10
    confidences: List[float]
