import json
from datetime import datetime, timezone

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
    BlockNumber,
    PriceList,
)

from models.credmark.algorithms.value_at_risk.dto import (
    HistoricalPriceInput,
    VaRHistoricalInput,
    ContractVaRInput,
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
                version="1.0",
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
        asof_dt = datetime.combine(input.asOf, datetime.max.time(), tzinfo=timezone.utc)
        asof_block_number = BlockNumber.from_timestamp(asof_dt)

        poolsinfo = self.context.run_model('compound-v2.all-pools-info',
                                           input=EmptyInput(),
                                           return_type=CompoundV2PoolInfos,
                                           block_number=asof_block_number)
        positions = []
        for poolinfo in poolsinfo:
            amount = (poolinfo.totalBorrows - poolinfo.totalLiability)
            positions.append(Position(amount=amount, asset=poolinfo.token))

        portfolio = Portfolio(positions=positions)

        pls = []
        pl_assets = set()

        for pos in portfolio:
            if pos.asset.address not in pl_assets:
                historical_price_input = HistoricalPriceInput(token=pos.asset,
                                                              window=input.window,
                                                              asOf=input.asOf)
                pl = self.context.run_model(slug='finance.example-historical-price',
                                            input=json.loads(historical_price_input.json()),
                                            return_type=PriceList)
                pls.append(pl)
                pl_assets.add(pos.asset.address)

        self.logger.info('')
        var_input = VaRHistoricalInput(
            portfolio=portfolio,
            priceLists=pls,
            interval=input.interval,
            confidences=input.confidences,
        )
        return self.context.run_model(slug='finance.var-engine-historical',
                                      input=var_input,
                                      return_type=dict)
