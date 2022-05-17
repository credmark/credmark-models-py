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
    confidences: List[float]
    _iterator: str = PrivateAttr('priceLists')


class ContractVaRInput(DTO):
    window: str
    interval: int
    confidences: List[float]
    price_model: str = DTOField('token.price', description='price model slug')

    class Config:
        schema_extra = {
            'examples': [
                {'window': '2 days',
                 'interval': 1,
                 'confidences': [0.01, 0.05]
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
