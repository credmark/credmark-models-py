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
    confidences: List[float]
    _iterator: str = PrivateAttr('priceLists')


class ContractVaRInput(DTO):
    window: str
    interval: int
    confidences: List[float]
    price_model: str = DTOField('chainlink.price-usd', description='price model slug')

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


class UniswapPoolVaRInput(ContractVaRInput):
    lower_range: float = DTOField(default=0.05, description='Lower bound to the current price')
    uppper_range: float = DTOField(default=0.05, description="Upper bound to the current price")
    pool: Contract
