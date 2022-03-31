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
    PriceList,
)

from credmark.dto import (
    DTO,
    DTOField,
)

# TODO: to be merged to framework


class VaRParameters(DTO):
    """
    VaRParameters contains only the VaR model parameters
    """
    as_ofs: Optional[List[date]]
    as_of_is_range: bool = DTOField(False)
    window: str
    intervals: List[str] = DTOField(...)
    confidences: List[float] = DTOField(..., ge=0.0, le=1.0)  # accepts multiple values
    dev_mode: bool = DTOField(False)
    reset_cache: bool = DTOField(False)
    verbose: bool = DTOField(False)

    class Config:
        validate_assignment = True


class VaRPortfolioInput(VaRParameters):
    """
    VaRPortfolioInput: calcualte VaR for a fixed portfolio
    """
    portfolio: Portfolio

    class Config:
        validate_assignment = True


class VaRPortfolioAndPriceInput(DTO):
    """
    VaRPortfolioAndPriceInput: calcualte VaR for a fixed portfolio and price input
    """
    portfolio: Portfolio
    priceList: List[PriceList] = DTOField(default=[], description='List of prices')
    n_window: int
    n_intervals: List[int] = DTOField(...)
    confidences: List[float] = DTOField(..., ge=0.0, le=1.0)  # accepts multiple values
    dev_mode: bool = DTOField(False)
    reset_cache: bool = DTOField(False)
    verbose: bool = DTOField(False)

    class Config:
        validate_assignment = True


class VaRPortfolioAndPriceOutput(DTO):
    n_window: int
    # n_shifted/n_interval/confidence -> var
    var: Dict[int, Dict[int, Dict[float, float]]]


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
