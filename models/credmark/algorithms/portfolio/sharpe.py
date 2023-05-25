# pylint: disable=line-too-long
from datetime import datetime

import numpy as np
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.types import Address, Price, Token
from credmark.cmf.types.series import BlockSeries
from credmark.dto import DTO

np.seterr(all='raise')


class SharpRatioInput(DTO):
    token: Token
    prices: BlockSeries[Price]
    risk_free_rate: float

    class Config:
        schema_extra = {
            'example': {"token": {"address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"},
                        "prices": {"series": [
                            {"blockNumber": "10", "blockTimestamp": "10",
                             "sampleTimestamp": "10", "output": {"price": 4.2, "src": ""}},
                            {"blockNumber": "9", "blockTimestamp": "9",
                             "sampleTimestamp": "9", "output": {"price": 3.2, "src": ""}},
                            {"blockNumber": "8", "blockTimestamp": "8",
                             "sampleTimestamp": "8", "output": {"price": 6.2, "src": ""}},
                            {"blockNumber": "7", "blockTimestamp": "7",
                             "sampleTimestamp": "7", "output": {"price": 3.2, "src": ""}},
                            {"blockNumber": "6", "blockTimestamp": "6",
                             "sampleTimestamp": "6", "output": {"price": 1.2, "src": ""}},
                            {"blockNumber": "5", "blockTimestamp": "5",
                             "sampleTimestamp": "5", "output": {"price": 8.2, "src": ""}},
                            {"blockNumber": "4", "blockTimestamp": "4",
                             "sampleTimestamp": "4", "output": {"price": 5.2, "src": ""}},
                            {"blockNumber": "3", "blockTimestamp": "3",
                             "sampleTimestamp": "3", "output": {"price": 7.2, "src": ""}},
                            {"blockNumber": "2", "blockTimestamp": "2",
                             "sampleTimestamp": "2", "output": {"price": 3.2, "src": ""}},
                            {"blockNumber": "1", "blockTimestamp": "1", "sampleTimestamp": "1",
                             "output": {"price": 9.2, "src": ""}}],
                "errors": []}, "risk_free_rate": 0.02}
        }


class SharpRatioOutput(DTO):
    token_address: Address
    sharpe_ratio: float
    avg_return: float
    risk_free_rate: float
    ret_stdev: float
    return_rolling_interval: int
    blockTime: str
    block_number: int
    blockTimestamp: int


@Model.describe(slug="finance.sharpe-ratio-token",
                version="1.4",
                display_name="Sharpe ratio for a token's historical price performance",
                description=("Sharpe ratio is return (averaged returns, annualized) "
                             "versus risk (std. dev. of return)"),
                category='financial',
                input=SharpRatioInput,
                output=SharpRatioOutput)
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

    def run(self, input: SharpRatioInput) -> SharpRatioOutput:
        risk_free_rate = input.risk_free_rate

        df_pl = (pd.DataFrame(input.prices.dict()['series'])
                 .sort_values(['blockNumber'], ascending=False))
        df_pl.loc[:, 'price'] = df_pl.output.apply(lambda p: p['price'])
        df_pl.loc[:, 'blockTime'] = df_pl.blockTimestamp.apply(
            datetime.utcfromtimestamp)
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
                  [(return_rolling_interval-1):]).to_list()[0]

        avg_ret = avg_rolling_ret[return_rolling_interval-1:].to_list()[0]
        avg_ret_minus_risk_free = avg_ret - risk_free_rate

        sharpe_ratio = avg_ret_minus_risk_free / st_dev

        output = SharpRatioOutput(
            token_address=input.token.address,
            sharpe_ratio=sharpe_ratio,
            avg_return=avg_ret,
            risk_free_rate=risk_free_rate,
            ret_stdev=st_dev,
            return_rolling_interval=return_rolling_interval,
            blockTime=str(df_pl.blockTime[0]),
            block_number=int(df_pl.blockNumber[0]),
            blockTimestamp=int(df_pl.blockTimestamp[0]),
        )
        return output

# account_sharpe_type, [actual: base on past PnL, last: using last positions]
# extension: extend to fill the length.
