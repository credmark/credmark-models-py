from datetime import datetime
from credmark.cmf.model import Model
from credmark.dto import DTO
from credmark.cmf.types import Token, Price
from credmark.cmf.types.series import BlockSeries

import numpy as np
import pandas as pd


class SharpRatioInput(DTO):
    token: Token
    prices: BlockSeries[Price]
    risk_free_rate: float


@Model.describe(slug="finance.sharpe-ratio-token",
                version="1.2",
                display_name="Sharpe ratio for a token's historical price performance",
                description=("Sharpe ratio is return (averaged returns, annualized) "
                             "versus risk (std. dev. of return)"),
                input=SharpRatioInput,
                output=dict)
class SharpeRatioToken(Model):
    """
    Calculate Sharpe ratio for a single token's past historical price performance.
    The rolling days is used in
    1) calculating averaging returns first and
    2) calculating the std. dev. of averaged returns

    We set the window to be 2 times of the rolling days such that we will obtain 1 sharpe ratio.

    rolling: 2
    window:  4 days
    price:   p p p p
    return:    v v v
    average:     m m
    std:           s
    sharpe-ratio:  r

    """

    def run(self, input: SharpRatioInput) -> dict:
        risk_free_rate = input.risk_free_rate

        df_pl = (pd.DataFrame(input.prices.dict()['series'])
                 .sort_values(['blockNumber'], ascending=False))
        df_pl.loc[:, 'price'] = df_pl.output.apply(lambda p: p['price'])
        df_pl.loc[:, 'blockTime'] = df_pl.blockTimestamp.apply(datetime.utcfromtimestamp)
        df_pl = (df_pl.loc[:, ['blockNumber', 'blockTimestamp', 'blockTime', 'price']]
                 .reset_index(drop=True))

        # If the number of rows is odd, we remove the last row (data in descending).
        if df_pl.shape[0] & 0x1:
            df_pl = df_pl[:-1]
        return_rolling_interval = int(df_pl.shape[0]/2)

        np_historical_prices = df_pl.price.to_numpy()
        daily_return = np_historical_prices[:-1] / np_historical_prices[1:] - 1

        annualized_return = daily_return * np.sqrt(365)
        avg_rolling_ret = (pd.Series(annualized_return)
                      .rolling(return_rolling_interval)
                      .mean()[return_rolling_interval-1:])

        st_dev = (avg_rolling_ret.rolling(return_rolling_interval)
                  .std()
                  [(return_rolling_interval-1):])

        avg_ret = avg_rolling_ret[return_rolling_interval-1:]
        avg_ret_minus_risk_free = avg_ret - risk_free_rate

        sharpe_ratio = avg_ret_minus_risk_free / st_dev

        ret_dict = {'token_address': input.token.address,
                    'sharpe_ratio': sharpe_ratio.to_list()[0],
                    'avg_return': avg_ret,
                    'risk_free_rate': risk_free_rate,
                    'ret_stdev': st_dev,
                    'return_rolling_interval': return_rolling_interval,
                    'blockTime': str(df_pl.blockTime[0]),
                    'block_number': int(df_pl.blockNumber[0]),
                    'blockTimestamp': int(df_pl.blockTimestamp[0]),
                    }
        return ret_dict
