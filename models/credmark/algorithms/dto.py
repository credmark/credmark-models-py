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
    Position,
    Address,
    Token,
    Contract,
)

from credmark.dto import (
    DTO,
    DTOField,
    EmptyInput,
)


class VaRPortfolioInput(DTO):
    """
    VaRPortfolioInput: calcualte VaR for a fixed portfolio
    """
    portfolio: Portfolio
    asOfs: Optional[List[date]]
    asof_is_range: Optional[bool] = DTOField(False)
    dev_mode: Optional[bool] = DTOField(False)
    window: str
    intervals: List[str] = DTOField(...)
    confidences: List[float] = DTOField(..., ge=0.0, le=1.0)  # accepts multiple values

    class Config:
        validate_assignment = True


class VaROutput(DTO):
    window: str
    # asOf/interval/confidence -> var
    var: Dict[str, Dict[str, Dict[float, float]]]


class VaRPPL(DTO):
    ppl: List[float]


class PPLAggregationInput(DTO):
    ppl: List[float]
    confidence: List[float]
    var_or_es: Literal['es', 'var'] = DTOField('es')


class VaRParameters(DTO):
    """
    VaRParameters contains only the VaR model parameters
    """
    window: str
    intervals: List[str] = DTOField(...)
    dev_mode: Optional[bool] = DTOField(False)

    class Config:
        validate_assignment = True


class VaRAggregation(DTO):
    confidences: List[float] = DTOField(..., ge=0.0, le=1.0)  # accepts multiple values


class VaRPPLAggregation(DTO):
    asOf: date
