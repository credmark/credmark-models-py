from datetime import (
    date
)

from typing import (
    List,
    Dict,
    Literal,
)

from credmark.cmf.types import (
    Portfolio,
    PriceList,
)

from credmark.dto import (
    DTO,
    DTOField,
)

# TODO: to be merged to framework


class ChefControl(DTO):
    reset_cache: bool = DTOField(default=False)
    use_cache: bool = DTOField(default=True)
    use_kitchen: bool = DTOField(default=True)


class RunControl(DTO):
    run_name: str = DTOField(default='VaR')
    dev_mode: bool = DTOField(default=False)
    verbose: bool = DTOField(default=False)


class VaRParameters(DTO):
    """
    VaRParameters contains only the VaR model parameters
    """
    as_ofs: List[date] = DTOField(default=[])
    as_of_is_range: bool = DTOField(default=False)
    window: str
    intervals: List[str] = DTOField(...)
    confidences: List[float] = DTOField(..., ge=0.0, le=1.0)  # accepts multiple values
    var_or_es: Literal['es', 'var'] = DTOField(default='es')

    class Config:
        validate_assignment = True


class VaRParametersInt(DTO):
    n_window: int
    n_intervals: List[int] = DTOField(...)
    confidences: List[float] = DTOField(..., ge=0.0, le=1.0)  # accepts multiple values
    var_or_es: Literal['es', 'var'] = DTOField('es')


class VaRPortfolioInput(VaRParameters, RunControl, ChefControl):
    """
    VaRPortfolioInput: calcualte VaR for a fixed portfolio
    """
    portfolio: Portfolio

    class Config:
        validate_assignment = True


class VaROutput(DTO):
    window: str
    # as_of/interval/confidence -> var
    var: Dict[str, Dict[str, Dict[float, float]]]


class AaveVaR(VaRParameters, RunControl, ChefControl):
    aave_history: bool = DTOField(False)


class VaRPortfolioAndPriceInput(VaRParametersInt, RunControl, ChefControl):
    """
    VaRPortfolioAndPriceInput: calcualte VaR for a fixed portfolio and price input
    """
    portfolio: Portfolio
    priceList: List[PriceList] = DTOField(default=[], description='List of prices')

    class Config:
        validate_assignment = True


class VaRPortfolioAndPriceOutput(DTO):
    n_window: int
    # n_shifted/n_interval/confidence -> var
    var: Dict[int, Dict[int, Dict[float, float]]]


class VaRPPL(DTO):
    ppl: List[float]


class PPLAggregationInput(VaRPPL):
    ppl: List[float]
    confidence: List[float]
    var_or_es: Literal['es', 'var'] = DTOField('es')
