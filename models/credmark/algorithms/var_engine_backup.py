from typing import (
    List,
    Optional,
    Dict,
    Union,
)

from datetime import (
    datetime,
    timezone,
    date,
)

import credmark.model

from credmark.model import ModelRunError

from credmark.dto import (
    DTO,
    DTOField,
)

from credmark.types import (
    Portfolio,
    Price,
    Address,
)

from models.credmark.algorithms.risk import (
    PortfolioManager,
    TokenTradeable,
    Market,
    calc_var,
)

import numpy as np
import pandas as pd


class PriceList(DTO):
    price: Price
    token: Address


class VaRParameter(DTO):
    """
    ContractVaRInput omits the input of portfolio
    """
    window: str
    intervals: List[str] = DTOField(...)
    confidences: List[float] = DTOField(..., ge=0.0, le=1.0)  # accepts multiple values
    asOfs: Optional[List[date]]
    asOf_is_range: Optional[bool] = DTOField(False)
    outputPrice: Optional[bool] = DTOField(False)
    dev_mode: Optional[bool] = DTOField(False)

    class Config:
        validate_assignment = True


class VaRInput(VaRParameter):
    portfolio: Portfolio

    class Config:
        validate_assignment = True


class VaROutput(DTO):
    window: str
    # asOf/interval/confidence -> var
    var: Dict[str, Dict[str, Dict[float, float]]]


@credmark.model.describe(slug='finance.var-engine',
                         version='1.0',
                         display_name='Value at Risk',
                         description='Value at Risk',
                         input=VaRInput,
                         output=VaROutput)
class ValueAtRisk(credmark.model.Model):
    def run(self, input: VaRInput) -> VaROutput:
        """
            Var takes in a portfolio object,
            a price window, and
            some intervals/confidences/asOfs
            default value for asOf is the date of the input block.

            It calculates the usd value of the portfolio for each of the blockstamps/timestamps.
            It then calculates the change in value over the window period for each timestamp,
            it returns the one that hits the input confidence levels.
        """

        current_block = self.context.block_number
        if input.asOfs:
            min_date = min(input.asOfs)
            max_date = max(input.asOfs)
            if input.asOf_is_range:
                asOfs = [dt.to_pydatetime()  # .replace(tzinfo=timezone.utc)
                         for dt in pd.date_range(min_date, max_date)]
            else:
                asOfs = input.asOfs
            block_hist = self.context.ledger.get_block_number_of_date(max_date)

            if not block_hist:
                block_time = self.context.ledger.get_date_of_block(current_block)
                raise ModelRunError(
                    (f'max(input.asOf)={max_date:%Y-%m-%d} is later than input block\'s timestamp, '
                     f'{current_block} on {block_time:%Y-%m-%d}.'))
        else:
            block_hist = current_block
            min_date = self.context.ledger.get_date_of_block(block_hist)
            max_date = min_date
            asOfs = [min_date]

        self.logger.info(f'{min_date=:%Y-%m-%d} {max_date=:%Y-%m-%d} {input.asOfs=} {block_hist=}')

        window = input.window
        w_k, w_i = self.context.historical.parse_timerangestr(window)
        w_seconds = self.context.historical.range_timestamp(w_k, w_i)

        if min_date == max_date:
            new_window = [window]
        else:
            asOf_range = f'{(max_date - min_date).days} days'
            new_window = [asOf_range, window]

        parsed_intervals = [
            self.context.historical.parse_timerangestr(ii) for ii in input.intervals]
        interval_keys, interval_nums = zip(*parsed_intervals)
        unique_ivl_keys = list(set(interval_keys))
        if unique_ivl_keys.__len__() != 1:
            raise ModelRunError(
                f'There is more than one type of interval in input intervals={input.intervals}')

        minimal_interval = f'1 {unique_ivl_keys[0]}'
        minimal_interval_seconds = self.context.historical.range_timestamp(unique_ivl_keys[0], 1)

        df_hist = pd.DataFrame()
        key_cols = []

        trades = []
        for (pos_n, pos) in enumerate(input.portfolio.positions):
            if not pos.token.address:
                raise ModelRunError(f'Input position is invalid, {input}')

            t = TokenTradeable(pos_n, pos.token, pos.amount, init_price=0)
            trades.append(t)

        port = PortfolioManager(trades)

        for tk in port.requires():
            tk_key = tk['key']
            tk_token = tk['token']
            if tk_key in df_hist:
                continue

            historical = self.context.run_model(
                'uniswap-v3.get-historical-price',
                input={
                    'token': tk_token,
                    'window': new_window,
                    'interval': minimal_interval,
                },
                block_number=block_hist)

            for p in historical['series']:
                p['price'] = p['output']['price']
                del p['output']

            df_tk = (pd.DataFrame(historical['series'])
                     .sort_values(['blockNumber'], ascending=False)
                     .rename(columns={'price': tk_key})
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

            key_cols.append(tk_key)
            if input.dev_mode:
                self.logger.info(df_hist)
                df_hist.to_csv('df_hist.csv', index=False)

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
            dict_current = Market(df_current.to_dict())
            df_base = port.value([dict_current], as_dict=True)

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

        return result


@credmark.model.describe(slug='finance.var-engine-aave',
                         version='1.0',
                         display_name='Value at Risk',
                         description='Value at Risk',
                         input=VaRParameter,
                         output=dict)
class ValueAtRiskAave(credmark.model.Model):
    def run(self, input: VaRParameter) -> dict:
        """
        ValueAtRiskAave evaluates the risk of the assets that Aave holds asOf a day
        """
        self.context.run_model()

        return {}
