import credmark.model
from credmark.model import ModelRunError

from credmark.types import (
    Position,
    Portfolio,
    Token,
)

from models.credmark.protocols.lending.aave.aave_v2 import (
    AaveDebtInfos,
)

from models.credmark.algorithms.dto import (
    VaRParameters,
    VaRPortfolioInput,
    VaROutput
)

from models.credmark.algorithms.base import (
    ValueAtRiskBase,
)
from models.tmp_abi_lookup import ERC_20_ABI


@credmark.model.describe(slug='finance.var-aave',
                         version='1.0',
                         display_name='Value at Risk',
                         description='Value at Risk',
                         input=VaRParameters,
                         output=VaROutput)
class ValueAtRiskAave(ValueAtRiskBase):

    def run(self, input: VaRParameters) -> VaROutput:
        """
        ValueAtRiskAave evaluates the risk of the assets that Aave holds asOf a day
        """

        dict_asOf = self.set_window(input)
        asOfs = dict_asOf['asOfs']

        window = ''
        var_consol = {}
        for asOf in asOfs:
            eod = self.eod_block(asOf)

            debts = self.context.run_model(
                'aave.lending-pool-assets',
                return_type=AaveDebtInfos,  # type: ignore
                block_number=eod['block'])

            portfolio = []
            self.logger.info('Aave net asset = Asset - liability')
            for dbt in debts:
                dbt.aToken = Token(address=dbt.aToken.address, abi=ERC_20_ABI)
                aTokenSupply = dbt.aToken.functions.totalSupply().call()
                net_amt = aTokenSupply - dbt.totalDebt
                self.logger.info(f'{dbt.aToken.address=} {net_amt=} '
                                 f'from {aTokenSupply=}-{dbt.totalDebt=}')
                portfolio.append(Position(amount=net_amt, asset=dbt.token))

            var_input = VaRPortfolioInput(portfolio=Portfolio(positions=portfolio),
                                          window=input.window,
                                          intervals=input.intervals,
                                          confidences=input.confidences,
                                          asOfs=[asOf.strftime('%Y-%m-%d')],
                                          asOf_is_range=False,
                                          dev_mode=input.dev_mode)

            var_out = self.context.run_model(
                'finance.var', input=var_input, return_type=VaROutput)
            if window == '':
                window = var_out.window
            else:
                if window != var_out.window:
                    raise ModelRunError(
                        f'All results\'s window shall be the same, '
                        f'but ({var_out.window=})!=({window=})')
            for k, v in var_out.var.items():
                var_consol[k] = v

        return VaROutput(window=window,
                         var=var_consol)
