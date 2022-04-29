from datetime import (
    date
)

from credmark.cmf.model import Model

from credmark.cmf.types import (
    Token,
    PriceList,
)

from credmark.dto import (
    DTO
)

from models.credmark.algorithms.value_at_risk.dto import (
    HistoricalPriceInput
)

import numpy as np
import numpy.random as npr
import pandas as pd


class SharpeRatioInput(DTO):
    asOf: date
    window: str
    token: Token


FIXED_RFR_RATE = 0.0202


@Model.describe(slug="finance.sharpe-ratio",
                version="1.0",
                display_name="Sharpe",
                description="Sharpe",
                input=SharpeRatioInput,
                output=dict)
class SharpeRatio(Model):

    def run(self, input: SharpeRatioInput) -> dict:

        hp_input = HistoricalPriceInput(token=input.token,
                                        window=input.window,
                                        asOf=input.asOf)
        historical_prices = self.context.run_model(slug='finance.example-historical-price',
                                                   input=hp_input,
                                                   return_type=PriceList)
        npr.default_rng(568921)
        dummy_prices = npr.uniform(2, 3, 362)
        historical_prices = PriceList(prices=dummy_prices.tolist(),
                                      tokenAddress=input.token.address, src='self')
        np_historical_prices = np.array(historical_prices.prices)

        # We assume price data in descending order.
        daily_return = np_historical_prices[:-1] / np_historical_prices[1:] - 1
        annualized_return = daily_return * 19.10497
        avg_6m_ret = pd.Series(annualized_return).rolling(180).mean()[180:]
        st_dev = pd.Series(avg_6m_ret).rolling(180).std()[180:]
        sharpe_ratio = (avg_6m_ret[180:] - FIXED_RFR_RATE) / st_dev

        return {"sharpe_ratio": sharpe_ratio.tolist()}
