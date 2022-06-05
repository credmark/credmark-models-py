from typing import List

from credmark.dto import (
    DTO,
    DTOField,
    IterableListGenericDTO,
    PrivateAttr,
    cross_examples,
)

from credmark.cmf.types import (
    Portfolio,
    Contract,
    Token,
    PriceList,
)


class HistoricalPriceInput(DTO):
    token: Token
    window: str  # e.g. '30 day'


class VaRHistoricalInput(IterableListGenericDTO[PriceList]):
    portfolio: Portfolio
    priceLists: List[PriceList]
    interval: int
    confidence: float
    _iterator: str = PrivateAttr('priceLists')


class ContractVaRInput(DTO):
    window: str
    interval: int
    confidence: float

    class Config:
        schema_extra = {
            'examples': [
                {'window': '2 days',
                 'interval': 1,
                 'confidence': 0.01
                 }]
        }


class PortfolioVaRInput(ContractVaRInput):
    portfolio: Portfolio

    class Config:
        schema_extra = {
            'examples': cross_examples(ContractVaRInput.Config.schema_extra['examples'],
                                       [{'portfolio': v}
                                           for v in Portfolio.Config.schema_extra['examples']],
                                       limit=10)
        }


class UniswapPoolVaRInput(ContractVaRInput):
    lower_range: float = DTOField(description='Lower bound to the current price for V3 pool')
    upper_range: float = DTOField(description="Upper bound to the current price for V3 pool")
    pool: Contract
