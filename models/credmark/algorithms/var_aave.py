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
    VaROutput,
)

from models.credmark.algorithms.risk import (
    ValueAtRiskBase,
    Plan,
    Recipe,
    MarketTarget,
)


class AaveDebtHistorical(Plan):
    def post_proc(self, context, data):
        debts = AaveDebtInfos(**data)
        positions = []
        context.logger.info('Aave net asset = Asset - liability')
        n_debts = len(data['aaveDebtInfos'])  # type: ignore
        for n_dbt, dbt in enumerate(debts):
            context.logger.info(f'{n_dbt+1}/{n_debts} '
                                f'Token info: {dbt.token.symbol=} {dbt.token.address=} '
                                f'{dbt.token.name=} {dbt.token.total_supply=} '
                                f'{dbt.token.decimals=}')
            dbt.aToken = Token(address=dbt.aToken.address)
            aTokenSupply = dbt.aToken.functions.totalSupply().call()
            net_amt = aTokenSupply - dbt.totalDebt
            context.logger.info(f'{dbt.aToken.address=} {net_amt=} '
                                f'from {aTokenSupply=}-{dbt.totalDebt=}')
            positions.append(Position(amount=net_amt, asset=dbt.token))
        return Portfolio(positions=positions)

    def define(self):
        method = 'run_model'
        slug = 'aave.lending-pool-assets'
        block_number = self._data['block_number']

        recipe = Recipe(cache_key=f'{method}.{slug}.{block_number}',
                        target_key=self._target.key,
                        method=method,
                        input={'slug': slug,
                               'block_number': block_number},
                        post_proc=self.post_proc,
                        return_type=self._return_type,
                        )
        return self.chef.cook(recipe)


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
            as_of_str = as_of.strftime('%Y-%m-%d')
            eod = self.eod_block(as_of)

            tag = 'eod'
            aave_tgt = MarketTarget(key=f'AaveDebtHistorical.{tag}.{eod["block"]}', artifact=None)

            aave_debts_plan = AaveDebtHistorical(tag,
                                                 aave_tgt,
                                                 slug='AaveDebtHistorical',
                                                 context=self.context,
                                                 verbose=True,
                                                 return_type=Portfolio,
                                                 block_number=eod['block'])
            portfolio = aave_debts_plan.execute()

            self.logger.info(
                f'Loaded Aave portfolio of {len(portfolio.positions)} '  # type: ignore
                f'assets as of {as_of_str}')

            # For DEBUG on certain type of token
            # portfolio = [p for p in portfolio
            # if p.asset.address == '0x0000000000085d4780B73119b644AE5ecd22b376']

            var_input = VaRPortfolioInput(portfolio=portfolio,  # type: ignore
                                          window=input.window,
                                          intervals=input.intervals,
                                          confidences=input.confidences,
                                          as_ofs=[as_of_str],
                                          as_of_is_range=False,
                                          dev_mode=True)

            var_out = self.context.run_model(
                # 'finance.var-reference',
                'finance.var-engine',
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
