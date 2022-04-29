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
    interval: int
    confidences: List[float]
    _iterator: str = PrivateAttr('priceLists')


class ContractVaRInput(DTO):
    asOf: date
    window: str
    interval: int
    confidences: List[float]

    class Config:
        schema_extra = {
            'examples': [{'asOf': '2022-02-17',
                          'window': '2 days',
                          'interval': 1,
                          'confidences': [0.01, 0.05]
                          }]
        }
