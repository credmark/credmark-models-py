from datetime import (
    datetime,
    timezone,
)

import os
import numpy as np
import pandas as pd

import credmark.model

from credmark.types import (
    Token,
    Address,
)

from credmark.model import ModelRunError

from models.credmark.algorithms.risk import (
    calc_var
)

from models.credmark.algorithms.dto import (
    VaRPortfolioInput,
    VaROutput
)

from models.credmark.algorithms.base import (
    ValueAtRiskBase
)
from models.tmp_abi_lookup import ERC_20_ABI


@credmark.model.describe(slug='finance.var',
                         version='1.0',
                         display_name='Value at Risk',
                         description='Value at Risk',
                         input=VaRPortfolioInput,
                         output=VaROutput)
class ValueAtRisk(ValueAtRiskBase):
    def run(self, input: VaRPortfolioInput) -> VaROutput:
        """
            Var takes in a portfolio object,
            a price window, and
            some intervals/confidences/asOfs
            default value for asOf is the date of the input block.

            It calculates the usd value of the portfolio for each of the blockstamps/timestamps.
            It then calculates the change in value over the window period for each timestamp,
            it returns the one that hits the input confidence levels.
        """
        parsed_intervals = [(self.context.historical
                             .parse_timerangestr(ii)) for ii in input.intervals]
        unique_ivl_keys = list(set([x[0] for x in parsed_intervals]))
        if unique_ivl_keys.__len__() != 1:
            raise ModelRunError(
                f'There is more than one type of interval in input intervals={unique_ivl_keys}')

        minimal_interval = f'1 {unique_ivl_keys[0]}'
        minimal_interval_seconds = self.context.historical.range_timestamp(unique_ivl_keys[0], 1)

        w_k, w_i = self.context.historical.parse_timerangestr(input.window)
        w_seconds = self.context.historical.range_timestamp(w_k, w_i)

        dict_asOf = self.set_window(input)
        asOfs = dict_asOf['asOfs']
        _block_max_asOf = dict_asOf['block_max_asOf']
        timestamp_max_asOf = dict_asOf['timestamp_max_asOf']
        window_from_max_asOf = dict_asOf['window_from_max_asOf']

        df_hist = pd.DataFrame()
        key_cols = []

        for pos in input.portfolio.positions:
            if pos.asset.address == Address('0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2'):
                # FIXME: MKR abi for symol
                pos.asset = Token(address=pos.asset.address, abi='[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[],"name":"stop","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"guy","type":"address"},{"name":"wad","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"owner_","type":"address"}],"name":"setOwner","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"src","type":"address"},{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"guy","type":"address"},{"name":"wad","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"wad","type":"uint256"}],"name":"burn","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"name_","type":"bytes32"}],"name":"setName","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"src","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"stopped","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"authority_","type":"address"}],"name":"setAuthority","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"guy","type":"address"},{"name":"wad","type":"uint256"}],"name":"burn","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"wad","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"push","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"src","type":"address"},{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"move","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[],"name":"start","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"authority","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"guy","type":"address"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"src","type":"address"},{"name":"guy","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"src","type":"address"},{"name":"wad","type":"uint256"}],"name":"pull","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"inputs":[{"name":"symbol_","type":"bytes32"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"name":"guy","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"guy","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Burn","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"authority","type":"address"}],"name":"LogSetAuthority","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"owner","type":"address"}],"name":"LogSetOwner","type":"event"},{"anonymous":true,"inputs":[{"indexed":true,"name":"sig","type":"bytes4"},{"indexed":true,"name":"guy","type":"address"},{"indexed":true,"name":"foo","type":"bytes32"},{"indexed":true,"name":"bar","type":"bytes32"},{"indexed":false,"name":"wad","type":"uint256"},{"indexed":false,"name":"fax","type":"bytes"}],"name":"LogNote","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"from","type":"address"},{"indexed":true,"name":"to","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"owner","type":"address"},{"indexed":true,"name":"spender","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Approval","type":"event"}]')
            else:
                pos.asset = Token(address=pos.asset.address, abi=ERC_20_ABI)

            if not pos.asset.address:
                raise ModelRunError(f'Input position is invalid, {input}')

            key_col = f'{pos.asset.address}'
            if key_col in df_hist:
                continue

            self.logger.info(f'Start loading {pos.asset.address}')
            historical = (self.context.historical
                          .run_model_historical('token.price-ext',  # 'uniswap-v3.get-average-price',  # 'token.price',
                                                window=window_from_max_asOf,
                                                interval=minimal_interval,
                                                model_input=pos.asset,
                                                end_timestamp=timestamp_max_asOf)
                          .dict())
            self.logger.info(f'Finished loading {pos.asset.address}')

            for p in historical['series']:
                p['price'] = p['output']['price']
                p['src'] = p['output']['src']
                del p['output']

            df_tk = (pd.DataFrame(historical['series'])
                     .sort_values(['blockNumber'], ascending=False)
                     .rename(columns={'price': key_col, 'src': key_col+'.src'})
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
                self.logger.info(f'\n{df_tk}')
                if not os.path.isdir('tmp'):
                    os.mkdir('tmp')
                df_hist.to_csv(os.path.join('tmp', 'df_hist.csv'), index=False)

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
            for (ivl_k, ivl_n), ivl_str in zip(parsed_intervals, input.intervals):
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
                    key_col = f'{pos.asset.address}'
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

        result = VaROutput(window=input.window, var=var)

        df_res = (pd.DataFrame(res_arr, columns=['interval', 'confidence', 'asOf', 'var'])
                  .sort_values(by=['interval', 'confidence', 'asOf', 'var'],
                               ascending=[True, True, False, True]))
        df_res.loc[:, 'interval'] = df_res.interval.apply(self.context.historical.parse_timerangestr)
        df_res_p = (df_res.pivot(index=['asOf'],
                                 columns=['confidence', 'interval'],
                                 values='var')
                    .sort_values('asOf', ascending=False)
                    .sort_index(axis=1)
                    .reset_index(drop=False))
        if input.dev_mode:
            df_res_p.to_csv(os.path.join('tmp', 'df_res.csv'), index=False)

        return result
