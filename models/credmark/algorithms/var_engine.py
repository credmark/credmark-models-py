from datetime import (
    datetime,
    timezone,
)

import credmark.model
from credmark.model import ModelRunError

from credmark.types import (
    Address
)

from models.credmark.algorithms.risk import (
    calc_es,
    calc_var,
    PortfolioManager,
    Market,
)

from models.credmark.algorithms.dto import (
    PPLAggregationInput,
    VaRPortfolioInput,
    VaRPortfolioAndPriceInput,
    VaROutput,
)

from models.credmark.algorithms.base import (
    ValueAtRiskBase
)

import os

import numpy as np


@credmark.model.describe(slug='finance.ppl-aggregation',
                         version='1.0',
                         display_name='Value at Risk - Calculate VaR from PPL',
                         description='Value at Risk - Calculate VaR from PPL',
                         input=PPLAggregationInput,
                         output=dict)
class PPLAggregation(credmark.model.Model):
    def run(self, input: PPLAggregationInput) -> dict:
        if input.var_or_es == 'es':
            res = {conf: calc_es(input.ppl, conf) for conf in input.confidence}
        elif input.var_or_es == 'var':
            res = {conf: calc_var(input.ppl, conf) for conf in input.confidence}
        else:
            raise ModelRunError('Input field var_or_es is not either es or var.')
        return {'result': res, 'var_or_es': input.var_or_es}


@credmark.model.describe(slug='finance.var-engine-price',
                         version='1.0',
                         display_name='Value at Risk - from portfolio and prices',
                         description='Value at Risk - from portfolio and prices',
                         input=VaRPortfolioAndPriceInput,
                         output=VaROutput)
class ValueAtRiskEnginePortfolioAndPrice(ValueAtRiskBase):
    def run(self, input: VaRPortfolioAndPriceInput) -> VaROutput:
        """
        VaR takes in a portfolio with positions, prices and VaR parameters.
        It calculates the usd value of the portfolio for the asOf dates.
        It then calculates the change in value over the window period,
        it returns the one that hits the input confidence levels.
        """

        dict_as_of = self.set_window(input)
        as_ofs = dict_as_of['as_ofs']

        parsed_intervals = [(self.context.historical
                             .parse_timerangestr(ii)) for ii in input.intervals]
        unique_ivl_keys = list(set([x[0] for x in parsed_intervals]))
        if unique_ivl_keys.__len__() != 1:
            raise ModelRunError(
                f'There is more than one type of interval in input intervals={unique_ivl_keys}')

        base_mkt = {}
        for pl in input.priceList:
            key_col = f'Token.{Address(pl.tokenAddress)}'
            base_mkt[key_col] = {}
            base_mkt[key_col]['extracted'] = pl.prices[0]
        base_mkt = Market(base_mkt)

        var_result = {}
        for as_of in as_ofs:
            as_of_str = as_of.strftime('%Y-%m-%d')
            var_result[as_of_str] = {}
            as_of_dt = datetime.combine(as_of, datetime.max.time(), tzinfo=timezone.utc)

            pm = PortfolioManager.from_portfolio(as_of_dt, input.portfolio, self.context)
            # base_mkt =
            _ = pm.value(base_mkt)

            for ((_, ivl_n), ivl) in zip(parsed_intervals, input.intervals):
                var_result[as_of_str][ivl] = {}
                mkt_scenarios = {}
                for pl in input.priceList:
                    key_col = f'Token.{Address(pl.tokenAddress)}'
                    mkt_scenarios[key_col] = {}
                    mkt_scenarios[key_col]['extracted'] = np.array(pl.prices[:-ivl_n]) / np.array(pl.prices[ivl_n:])
                mkt_scenarios = Market(mkt_scenarios)

                value_scen_df = pm.value_scenarios(base_mkt, mkt_scenarios)

                ppl = (value_scen_df.groupby(by=['SCEN_ID'], as_index=False)  # type: ignore
                       .agg({'VALUE': ['sum']}))
                var_result[as_of_str][ivl] = {
                    conf: calc_var(ppl[('VALUE', 'sum')].to_numpy(), conf)
                    for conf in input.confidences
                }

        if input.dev_mode:
            df_res_p = self.res_to_df(var_result)
            df_res_p.to_csv(os.path.join('tmp', 'df_res.csv'), index=False)

        var_output = VaROutput(window=input.window, var=var_result)

        return var_output


@credmark.model.describe(slug='finance.var-engine',
                         version='1.0',
                         display_name='Value at Risk - from portfolio and date',
                         description='Value at Risk - from portfolio and date',
                         input=VaRPortfolioInput,
                         output=VaROutput)
class ValueAtRiskEnginePortfolio(ValueAtRiskBase):
    def run(self, input: VaRPortfolioInput) -> VaROutput:
        """
            VaR takes in a portfolio with positions, and VaR parameters.
            Default value for as_of is the previous day of the input block.
            It will download the prices and calculate VaR for the permutation of VaR parameters:
                position (1) x
                window (1) x
                asOf (multiple) x
                interval (multiple) x
                confidences (multiple)
        """

        dict_as_of = self.set_window(input)
        as_ofs = dict_as_of['as_ofs']

        parsed_intervals = [(self.context.historical
                             .parse_timerangestr(ii)) for ii in input.intervals]
        unique_ivl_keys = list(set([x[0] for x in parsed_intervals]))
        if unique_ivl_keys.__len__() != 1:
            raise ModelRunError(
                f'There is more than one type of interval in input intervals={unique_ivl_keys}')

        minimal_interval = f'1 {unique_ivl_keys[0]}'

        var_result = {}
        for as_of in as_ofs:
            as_of_str = as_of.strftime('%Y-%m-%d')
            var_result[as_of_str] = {}
            as_of_dt = datetime.combine(as_of, datetime.max.time(), tzinfo=timezone.utc)

            pm = PortfolioManager.from_portfolio(as_of_dt, input.portfolio, self.context)
            base_mkt = pm.prepare_market('eod', as_of=as_of_dt)
            _ = pm.value(base_mkt)

            for ((_, ivl_n), ivl) in zip(parsed_intervals, input.intervals):
                var_result[as_of_str][ivl] = {}
                mkt_scenarios = pm.prepare_market('eod_var_scenario',
                                                  as_of=as_of_dt,
                                                  window=[input.window, minimal_interval],
                                                  interval=minimal_interval,
                                                  rolling_interval=ivl_n)

                breakpoint()

                value_scen_df = pm.value_scenarios(base_mkt, mkt_scenarios)

                ppl = (value_scen_df.groupby(by=['SCEN_ID'], as_index=False)  # type: ignore
                       .agg({'VALUE': ['sum']}))
                var_result[as_of_str][ivl] = {
                    conf: calc_var(ppl[('VALUE', 'sum')].to_numpy(), conf)
                    for conf in input.confidences
                }

        if input.dev_mode:
            df_res_p = self.res_to_df(var_result)
            df_res_p.to_csv(os.path.join('tmp', 'df_res.csv'), index=False)

        var_output = VaROutput(window=input.window, var=var_result)

        return var_output
