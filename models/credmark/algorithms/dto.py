from datetime import (
    date
)

from typing import (
    List,
    Optional,
    Dict,
    Literal,
)

from credmark.types import (
    Portfolio,
    Price,
    Address,
    Account,
)

from credmark.dto import (
    DTO,
    DTOField,
    cross_examples,
)

# TODO: to be merged to framework


class PriceList(DTO):
    prices: List[Price]
    tokenAddress: Address

    class Config:
        schema_extra: dict = {
            'examples': cross_examples(Price.Config.schema_extra['examples'],
                                       Account.Config.schema_extra['examples'])
        }


class VaRParameters(DTO):
    """
    VaRParameters contains only the VaR model parameters
    """
    as_ofs: Optional[List[date]]
    as_of_is_range: Optional[bool] = DTOField(False)
    window: str
    intervals: List[str] = DTOField(...)
    confidences: List[float] = DTOField(..., ge=0.0, le=1.0)  # accepts multiple values
    dev_mode: Optional[bool] = DTOField(False)

    class Config:
        validate_assignment = True


class VaRPortfolioInput(VaRParameters):
    """
    VaRPortfolioInput: calcualte VaR for a fixed portfolio
    """
    portfolio: Portfolio

    class Config:
        validate_assignment = True


class VaRPortfolioAndPriceInput(VaRPortfolioInput):
    """
    VaRPortfolioInput: calcualte VaR for a fixed portfolio
    """
    priceList: List[PriceList] = DTOField(default=[], description='List of prices')

    class Config:
        validate_assignment = True


class VaROutput(DTO):
    window: str
    # as_of/interval/confidence -> var
    var: Dict[str, Dict[str, Dict[float, float]]]


class VaRPPL(DTO):
    ppl: List[float]


class PPLAggregationInput(DTO):
    ppl: List[float]
    confidence: List[float]
    var_or_es: Literal['es', 'var'] = DTOField('es')


class VaRAggregation(DTO):
    confidences: List[float] = DTOField(..., ge=0.0, le=1.0)  # accepts multiple values


class VaRPPLAggregation(DTO):
    as_of: date
