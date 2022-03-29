import os

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


@credmark.model.describe(slug='finance.var-aave',
                         version='1.0',
                         display_name='Value at Risk for Aave',
                         description='Value at Risk for Aave',
                         input=VaRParameters,
                         output=VaROutput)
class ValueAtRiskAave(ValueAtRiskBase):

    def run(self, input: VaRParameters) -> VaROutput:
        """
        ValueAtRiskAave evaluates the risk of the assets that Aave holds as_of a day
        """

        dict_as_of = self.set_window(input)
        as_ofs = dict_as_of['as_ofs']
        max_date = dict_as_of['max_date']
        min_date = dict_as_of['min_date']

        window = ''
        var_result = {}
        for as_of in as_ofs:
            eod = self.eod_block(as_of)

            debts = self.context.run_model(
                'aave.lending-pool-assets',
                return_type=AaveDebtInfos,  # type: ignore
                block_number=eod['block'])

            portfolio = []
            self.logger.info('Aave net asset = Asset - liability')
            for dbt in debts:
                dbt.aToken = Token(address=dbt.aToken.address)
                aTokenSupply = dbt.aToken.functions.totalSupply().call()
                net_amt = aTokenSupply - dbt.totalDebt
                self.logger.info(f'{dbt.aToken.address=} {net_amt=} '
                                 f'from {aTokenSupply=}-{dbt.totalDebt=}')
                portfolio.append(Position(amount=net_amt, asset=dbt.token))

            # For DEBUG on certain type of token
            # portfolio = [p for p in portfolio
            # if p.asset.address == '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2']

            var_input = VaRPortfolioInput(portfolio=Portfolio(positions=portfolio),
                                          window=input.window,
                                          intervals=input.intervals,
                                          confidences=input.confidences,
                                          as_ofs=[as_of.strftime('%Y-%m-%d')],
                                          as_of_is_range=False,
                                          dev_mode=False)

            var_out = self.context.run_model(
                'finance.var-engine',  # 'finance.var',
                input=var_input,
                return_type=VaROutput)
            if window == '':
                window = var_out.window
            else:
                if window != var_out.window:
                    raise ModelRunError(
                        f'All results\'s window shall be the same, '
                        f'but ({var_out.window=})!=({window=})')
            var_result |= var_out.var

        if input.dev_mode:
            df_res_p = self.res_to_df(var_result)
            df_res_p.to_csv(os.path.join(
                'tmp',
                f'df_var_aave_{window}_{input.intervals}'
                f'_{min_date:%Y-%m-%d}_{max_date:%Y-%m-%d}.csv'), index=False)

        return VaROutput(window=window,
                         var=var_result)
