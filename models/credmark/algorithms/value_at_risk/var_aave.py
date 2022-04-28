import json
from datetime import datetime, timezone

from credmark.cmf.model import Model
from credmark.dto import EmptyInput

from credmark.cmf.types import (
    Position,
    Portfolio,
    BlockNumber,
    PriceList,
)

from models.credmark.algorithms.value_at_risk.dto import (
    HistoricalPriceInput,
    VaRHistoricalInput,
    ContractVaRInput,
)


from models.credmark.protocols.lending.aave.aave_v2 import (
    AaveDebtInfos,
)


@Model.describe(slug="finance.var-aave",
                version="1.0",
                display_name="Aave V2 VaR",
                description="Calcualte the VaR of Aave contract of its net asset",
                input=ContractVaRInput,
                output=dict)
class AaveV2GetVAR(Model):
    """
    VaR of Aave based on its inventory of tokens.
    The exposure of Aave is the number of tokens borrowed (totalDebt)
    less than the total numbe of tokens (totalSupply) deposited.

    - totalSupply of aToken is Aave's liability / loaner's asset, hence a negative sign
    - totalDebt is Aava's asset / borrower's liability, hence a positive sign

    Reference:
    https://docs.credmark.com/risk-insights/research/aave-and-compound-historical-var
    """

    def run(self, input: ContractVaRInput) -> dict:
        asof_dt = datetime.combine(input.asOf, datetime.max.time(), tzinfo=timezone.utc)
        asof_block_number = BlockNumber.from_timestamp(asof_dt)

        debts = self.context.run_model('aave-v2.lending-pool-assets',
                                       input=EmptyInput(),
                                       return_type=AaveDebtInfos,
                                       block_number=asof_block_number)

        n_debts = len(debts.aaveDebtInfos)
        positions = []
        for n_dbt, dbt in enumerate(debts):
            self.logger.debug(f'{n_dbt+1}/{n_debts} {dbt.aToken.address=} '
                              f'{dbt.totalLiquidity_qty=} '
                              f'from {dbt.totalSupply_qty=}-{dbt.totalDebt_qty=}')
            # Note below is taking the negated totalLiquidity as -totalSupply_qty + totalDebt_qty
            # See the doc of this class
            positions.append(Position(amount=-dbt.totalLiquidity_qty, asset=dbt.token))
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
