from datetime import (
    datetime,
    timezone,
    date,
)

import credmark.model
from credmark.model import ModelRunError

from credmark.dto import (
    DTO,
)

from models.credmark.algorithms.risk import (
    calc_var,
    calc_es,
    PortfolioManager,
)

from models.credmark.algorithms.dto import (
    VaRPortfolioInput,
    VaROutput,
    PPLAggregationInput,
)

import os
import numpy as np
import pandas as pd


@credmark.model.describe(slug='finance.var-portfolio-ppl',
                         version='1.0',
                         display_name='Value at Risk - calculate PPL',
                         description='Value at Risk - calculate PPL',
                         input=VaRPortfolioInput,
                         output=VaROutput)
class ValueAtRiskPPL(credmark.model.Model):
    def run(self, input: VaRPortfolioInput) -> VaROutput:
        """
            VaR takes in a portfolio object,
            A market object shall contain all the prices.
            Generate PPL
            default value for asOf is the date of the input block.

            It calculates the usd value of the portfolio for each of the blockstamps/timestamps.
            It then calculates the change in value over the window period for each timestamp,
            it returns the one that hits the input confidence levels.
        """

        pm = PortfolioManager.from_portfolio(input.portfolio)

        mkt_reqs = dict(pm.requires())
        mkt_keys = mkt_reqs.keys()

        breakpoint()

        asOf_str = asOf.strftime('%Y-%m-%d')
        asOf_eod = datetime.combine(asOf, datetime.time.max(), tzinfo=timezone.utc)
        idx_last = df_hist.index.get_loc(
            df_hist.index[df_hist['blockTime'] <= asOf_eod][0])  # type: ignore
        df_current = df_hist.loc[:, mkt_keys].iloc[idx_last, :]
        dict_current = Market(df_current.to_dict())
        df_base = port.value([dict_current], as_dict=True)

        var[asOf_str] = {}

        # create scenarios
        port.value(historical_mkts, df_base)

        # perform valuation

        for tk in pm.requires():

            for ivl_k, ivl_n, ivl_str in zip(interval_keys, interval_nums, input.intervals):
                ivl_seconds = self.context.historical.range_timestamp(ivl_k, ivl_n)  # type: ignore
                step_ivl = int(np.floor(ivl_seconds / minimal_interval_seconds))
                n_ivl = int(np.floor(w_seconds / ivl_seconds))

                df_hist_ivl = df_hist.iloc[idx_last:(
                    idx_last+n_ivl*step_ivl):step_ivl].copy()  # type: ignore

                df_hist_ivl_p_only = df_hist_ivl.loc[:, key_cols]

                df_ret = df_hist_ivl_p_only.iloc[:-1, :].reset_index(drop=True) / \
                    df_hist_ivl_p_only.iloc[1:, :].reset_index(drop=True)

                df_ret = df_ret.apply(lambda x: x - 1)
                # assert np.all(df_ret.copy().rolling(1).agg(lambda x : x.prod()) == df_ret.copy())

                historical_mkts = [((r + 1) * df_current).to_dict() for _, r in df_ret.iterrows()]

                var[asOf_str][ivl_str] = {}
                df_historical_values = port.value(historical_mkts, df_base)
                df_historical_values.loc[:, 'SCEN_ID'] += 1

                ppl = df_historical_values.groupby('SCEN_ID').value.sum().to_numpy()

                for conf in input.confidences:
                    v = calc_var(ppl, conf)
                    var[asOf_str][ivl_str][conf] = v
                    res_arr.append((ivl_str, conf, asOf_str, v))

                if input.dev_mode:
                    df_current.to_csv('df_current.csv')
                    df_hist_ivl.to_csv('df_hist_ivl.csv')
                    df_ret.to_csv('df_ret.csv')

        result = VaROutput(window=window, var=var)

        df_res = (pd.DataFrame(res_arr, columns=['asOf', 'interval', 'confidence', 'var'])
                  .sort_values(by=['interval', 'confidence', 'asOf', 'var'],
                               ascending=[True, True, False, True]))
        df_res.to_csv('df_res.csv')


@credmark.model.describe(slug='finance.ppl-aggregation',
                         version='1.0',
                         display_name='Value at Risk - Calculate VaR from PPL',
                         description='Value at Risk - Calculate VaR from PPL',
                         input=PPLAggregationInput,
                         output=dict)
class PPLAggregation(credmark.model.Model):
    def run(self, input: PPLAggregationInput) -> dict:
        if input.var_or_es == 'es':
            res = [calc_es(input.ppl, conf) for conf in input.confidence]
        elif input.var_or_es == 'var':
            res = [calc_var(input.ppl, conf) for conf in input.confidence]
        else:
            raise ModelRunError('Input field var_or_es is not either es or var.')
        return {'result': res, 'var_or_es': input.var_or_es}


@credmark.model.describe(slug='finance.var-portfolio-fetch-price',
                         version='1.0',
                         display_name='Value at Risk - Portfolio - fetch price',
                         description='Value at Risk',
                         input=VaRPortfolioInput,
                         output=VaROutput)
class ValueAtRiskFetchPrice(credmark.model.Model):
    def run(self, input: VaRPortfolioInput) -> dict:
        parsed_intervals = [
            self.context.historical.parse_timerangestr(ii) for ii in input.intervals]
        interval_keys, interval_nums = zip(*parsed_intervals)
        unique_ivl_keys = list(set(interval_keys))
        if unique_ivl_keys.__len__() != 1:
            raise ModelRunError(
                f'There is more than one type of interval in input intervals={input.intervals}')

        minimal_interval = f'1 {unique_ivl_keys[0]}'
        minimal_interval_seconds = self.context.historical.range_timestamp(unique_ivl_keys[0], 1)

        current_block = self.context.block_number
        current_block_date = self.context.block_number.timestamp_datetime.date()
        if input.asOfs:
            min_date = min(input.asOfs)
            max_date = max(input.asOfs)

            if max_date >= current_block_date:
                raise ModelRunError(
                    (f'max(input.asOf)={max_date:%Y-%m-%d} shall be earlier than the input block, '
                     f'{current_block} on {current_block_date:%Y-%m-%d}.'))

            if input.asOfsRange:
                asOfs = [dt.to_pydatetime().replace(tzinfo=timezone.utc)
                         for dt in pd.date_range(min_date, max_date)][::-1]
            else:
                asOfs = input.asOfs

        else:
            min_date, max_date = current_block_date, current_block_date
            asOfs = [min_date]

        window = input.window
        w_k, w_i = self.context.historical.parse_timerangestr(window)
        w_seconds = self.context.historical.range_timestamp(w_k, w_i)

        # TODO: pending for time range fix
        # current_to_asOf_range = f'{(current_block_date - max_date).days} days'
        # window_from_current = [..., current_to_asOf_range]
        if min_date == max_date:
            window_from_max_asOf = [window]
        else:
            asOf_range = f'{(max_date - min_date).days} days'
            window_from_max_asOf = [window, asOf_range]

        block_max_asOf = self.context.block_number.from_datetime(max_date)
        self.logger.info(
            f'{min_date=:%Y-%m-%d} {max_date=:%Y-%m-%d} {input.asOfs=} {current_block_date=:%Y-%m-%d} {window_from_max_asOf=} {block_max_asOf=}')

        df_hist = pd.DataFrame()
        key_cols = []

        for pos in input.portfolio.positions:
            if not pos.token.address:
                raise ModelRunError(f'Input position is invalid, {input}')

            key_col = f'{pos.token.address}.{pos.token.symbol}'
            if key_col in df_hist:
                continue

            historical = (self.context.historical
                          .run_model_historical('uniswap-v3.get-average-price',  # 'token.price',
                                                window=window_from_max_asOf,
                                                interval=minimal_interval,
                                                model_input=pos.token,
                                                block_number=block_max_asOf)
                          .dict())

            for p in historical['series']:
                p['price'] = p['output']['price']
                del p['output']

            df_tk = (pd.DataFrame(historical['series'])
                     .sort_values(['blockNumber'], ascending=False)
                     .rename(columns={'price': key_col})
                     .reset_index(drop=True))

            df_tk.loc[:, 'blockTime'] = df_tk.blockTimestamp.apply(
                lambda x: datetime.fromtimestamp(x, timezone.utc))
            df_tk.loc[:, 'sampleTime'] = df_tk.sampleTimestamp.apply(
                lambda x: datetime.fromtimestamp(x, timezone.utc))

            if df_hist.empty:
                df_hist = df_tk
            else:
                df_hist = df_hist.merge(df_tk, on=['blockNumber',
                                                   'blockTimestamp',
                                                   'sampleTimestamp',
                                                   'blockTime',
                                                   'sampleTime'], how='outer')
                for col in df_hist.columns:
                    assert df_hist.loc[:, col].isnull().sum() == 0

            key_cols.append(key_col)
            if input.dev_mode:
                self.logger.info(key_col)
                self.logger.info(df_tk)
                if not os.path.isdir('tmp'):
                    os.mkdir('tmp')
                df_hist.to_csv(os.path.join('tmp', 'df_hist.csv'), index=False)


#             a price window, and
#            some intervals/confidences/asOfs

class VaRPPLInput(DTO):
    asOf: date
    window: str
    interval: str


"""
== == == == == == == == == == == == == == ==

 var = {}
  res_arr = []
   for asOf in asOfs:
        asOf_str = asOf.strftime('%Y-%m-%d')
        var[asOf_str] = {}
        asOf_last = datetime(asOf.year, asOf.month, asOf.day,
                             23, 59, 59, tzinfo=timezone.utc)
        idx_last = df_hist.index.get_loc(
            df_hist.index[df_hist['blockTime'] <= asOf_last][0])  # type: ignore
        df_current = df_hist.loc[:, key_cols].iloc[idx_last, :]
        dict_current = df_current.to_dict()

        window_n_ivl = int(np.floor(w_seconds / minimal_interval_seconds))
        for ivl_k, ivl_n, ivl_str in zip(interval_keys, interval_nums, input.intervals):
            ivl_seconds = self.context.historical.range_timestamp(ivl_k, ivl_n)  # type: ignore
            step_ivl = int(ivl_seconds / minimal_interval_seconds)

            df_hist_ivl = df_hist.iloc[idx_last:(
                idx_last+window_n_ivl+1)].copy()  # type: ignore

            df_hist_ivl_p_only = df_hist_ivl.loc[:, key_cols]

            df_ret = df_hist_ivl_p_only.iloc[:-step_ivl, :].reset_index(drop=True) / \
                df_hist_ivl_p_only.iloc[step_ivl:, :].reset_index(drop=True)

            df_ret = df_ret.apply(lambda x: x - 1)
            # assert np.all(df_ret.copy().rolling(1).agg(lambda x : x.prod()) == df_ret.copy())

            var[asOf_str][ivl_str] = {}
            df_value = pd.DataFrame()
            for pos in input.portfolio.positions:
                key_col = f'{pos.token.address}.{pos.token.symbol}'
                ret = df_ret[key_col].to_numpy()
                current_value = pos.amount * dict_current[key_col]
                value_changes = ret * current_value
                if key_col not in df_value:
                    df_value.insert(0, (key_col), value_changes)
                else:
                    df_value[key_col] += value_changes
            ppl = df_value.sum(axis=1).to_numpy()

            for conf in input.confidences:
                v = calc_var(ppl, conf)
                var[asOf_str][ivl_str][conf] = v
                res_arr.append((ivl_str, conf, asOf_str, v))

            if input.dev_mode:
                df_current.to_csv(os.path.join('tmp', 'df_current.csv'), index=False)
                df_hist_ivl.to_csv(os.path.join('tmp', 'df_hist_ivl.csv'), index=False)
                df_ret.to_csv(os.path.join('tmp', 'df_ret.csv'), index=False)

    result = VaROutput(window=window, var=var)

    if input.dev_mode:
        df_res = (pd.DataFrame(res_arr, columns=['interval', 'confidence', 'asOf', 'var'])
                  .sort_values(by=['interval', 'confidence', 'asOf', 'var'],
                               ascending=[True, True, False, True]))
        df_res_p = (df_res.pivot(index=['asOf'],
                                 columns=['confidence', 'interval'],
                                 values='var')
                    .sort_values('asOf', ascending=False)
                    .sort_index(axis=1)
                    .reset_index(drop=False))

        df_res_p.to_csv(os.path.join('tmp', 'df_res.csv'), index=False)

    return result
"""
