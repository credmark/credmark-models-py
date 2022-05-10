from datetime import datetime
from credmark.cmf.model import Model
from credmark.dto import DTO, DTOField
from credmark.cmf.types import Token, Price

import numpy as np
import pandas as pd


class SharpRatioInput(DTO):
    token: Token
    window: str = DTOField("360 days")
    risk_free_rate: float


@Model.describe(slug="finance.sharpe-ratio-token",
                version="1.0",
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
        token = input.token
        window = input.window
        risk_free_rate = input.risk_free_rate

        pl = self.context.historical.run_model_historical('token.price',
                                                          model_input=token,
                                                          window=window,
                                                          model_return_type=Price)

        df_pl = pd.DataFrame(pl.dict()['series']).sort_values(['blockNumber'], ascending=False)
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
        avg_6m_ret = (pd.Series(annualized_return)
                      .rolling(return_rolling_interval)
                      .mean()[return_rolling_interval-1:])

        st_dev = (avg_6m_ret.rolling(return_rolling_interval)
                  .std()
                  [(return_rolling_interval-1):])

        sharpe_ratio = (avg_6m_ret[return_rolling_interval-1:] - risk_free_rate) / st_dev

        ret_dict = {"sharpe_ratio": sharpe_ratio.to_list()[0],
                    'window': window,
                    'return_rolling_interval': return_rolling_interval,
                    'blockTime': str(df_pl.blockTime[0]),
                    'block_number': int(df_pl.blockNumber[0]),
                    'blockTimestamp': int(df_pl.blockTimestamp[0]),
                    'token_address': input.token.address,
                    }
        return ret_dict
