from credmark.cmf.model import Model

from typing import (List)

from credmark.dto import (
    DTO,
    EmptyInput,
    IterableListGenericDTO,
)


from credmark.cmf.types import (
    Position,
    Token,
    Portfolio,
)

from models.credmark.algorithms.value_at_risk.dto import (
    ContractVaRInput,
    PortfolioVaRInput,
)


class CompoundV2PoolInfo(DTO):
    tokenSymbol: str
    cTokenSymbol: str
    token: Token
    cToken: Token
    tokenDecimal: int
    cTokenDecimal: int
    tokenPrice: float
    tokenPriceSrc: str
    cash: float
    totalBorrows: float
    totalReserves: float
    totalSupply: float
    exchangeRate: float
    invExchangeRate: float
    totalLiability: float
    borrowRate: float
    supplyRate: float
    reserveFactor: float
    isListed: bool
    collateralFactor: float
    isComped: bool
    block_number: int
    block_datetime: str


class CompoundV2PoolInfos(IterableListGenericDTO[CompoundV2PoolInfo]):
    infos: List[CompoundV2PoolInfo]
    _iterator: str = 'infos'


@Model.describe(slug="finance.var-compound",
                version="1.1",
                display_name="Compound V2 VaR",
                description="Calcualte the VaR of Compound contract of its net asset",
                input=ContractVaRInput,
                output=dict)
class CompoundGetVAR(Model):
    """
    VaR of Compound based on its inventory of tokens.
    The exposure of Compound is the number of tokens borrowed (totalLiability)
    less than it lends out (cToken.totalBorrows).

    - totalLiability = cToken.totalSupply / invExchangeRate, negated to a negative sign
    - totalBorrows, positive sign as an asset to Compound.
    - totalLiabiltiy - totalBorrows ~= (cash - totalReserves)

    Reference:
    https://docs.credmark.com/risk-insights/research/aave-and-compound-historical-var
    """

    def run(self, input: ContractVaRInput) -> dict:
        poolsinfo = self.context.run_model('compound-v2.all-pools-info',
                                           input=EmptyInput(),
                                           return_type=CompoundV2PoolInfos)
        positions = []
        for poolinfo in poolsinfo:
            amount = (poolinfo.totalBorrows - poolinfo.totalLiability)
            positions.append(Position(amount=amount, asset=poolinfo.token))

        portfolio = Portfolio(positions=positions)

        var_input = PortfolioVaRInput(portfolio=portfolio, **input)
        return self.context.run_model(slug='finance.var-portfolio-historical',
                                      input=var_input,
                                      return_type=dict)
