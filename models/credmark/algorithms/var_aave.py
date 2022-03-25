import credmark.model

from credmark.types import (
    Position,
    Portfolio,
)

from models.credmark.protocols.lending.aave.aave_v2 import (
    AaveDebtInfos,
)

from models.credmark.algorithms.dto import (
    VaRParameters,
    VaRPortfolioInput,
    VaROutput
)


@credmark.model.describe(slug='finance.var-aave',
                         version='1.0',
                         display_name='Value at Risk',
                         description='Value at Risk',
                         input=VaRParameters,
                         output=dict)
class ValueAtRiskAave(credmark.model.Model):
    def run(self, input: VaRParameters) -> dict:
        """
        ValueAtRiskAave evaluates the risk of the assets that Aave holds asOf a day
        """
        block_hist = self.context.block_number.from_datetime(input.asOf)

        debts = self.context.run_model(
            'aave.lending-pool-assets', input=None, return_type=AaveDebtInfos, block_number=block_hist)

        portfolio = []
        for dbt in debts:
            net_amt = debts[0].aToken.functions.totalSupply().call() - debts[0].totalDebt
            portfolio.append(Position(amount=net_amt, token=dbt.token))

        var_input = VaRPortfolioInput(portfolio=Portfolio(positions=portfolio),
                                      window=input.window,
                                      intervals=input.intervals,
                                      confidences=input.confidences,
                                      asOfs=[input.asOf.strftime('%Y-%m-%d')],
                                      asof_is_range=False,
                                      dev_mode=input.dev_mode)

        var = self.context.run_model('finance.var', input=var_input, return_type=VaROutput)
        return var
