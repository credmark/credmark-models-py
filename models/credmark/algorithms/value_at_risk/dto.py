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


class AccountVaRInput(ContractVaRInput):
    address: Address


class UniswapPoolVaRInput(ContractVaRInput):
    lower_range: float = DTOField(
        description='Lower bound to the current price for V3 pool')
    upper_range: float = DTOField(
        description="Upper bound to the current price for V3 pool")
    pool: Contract


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
