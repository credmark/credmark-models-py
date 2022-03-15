from typing import (
    List,
    Tuple,
    Optional
)

import credmark.model

from credmark.model import ModelRunError

from credmark.types.dto import (
    DTO,
    DTOField,
)

from credmark.types import (
    Portfolio,
    Price,
    Address,
)

import numpy as np
import pandas as pd


class PriceList(DTO):
    price: Price
    token: Address


class VaRInput(DTO):
    portfolio: Portfolio
    window: str
    interval: Optional[str]
    confidence: List[float] = DTOField(..., gt=0.0, lt=1.0)  # accepts multiple values

    class Config:
        validate_assignment = True


class VaROutput(DTO):
    var: List[Tuple[float, float]]


@credmark.model.describe(slug='finance.var',
                         version='1.0',
                         display_name='Value at Risk',
                         description='Value at Risk',
                         input=VaRInput,
                         output=VaROutput)
class Var(credmark.model.Model):
    @staticmethod
    def calc_var(ppl, lvl):
        ppl_d = ppl.copy()
        ppl_d.sort()
        len_ppl_d = ppl_d.shape[0]
        pos_f = lvl * len_ppl_d
        lower = int(np.floor(pos_f))
        upper = int(np.ceil(pos_f))
        return ppl_d[lower-1] * (upper - pos_f) + ppl_d[upper-1] * (pos_f - lower)

    def run(self, input: VaRInput) -> VaROutput:
        """
            Var takes in a portfolio object,
            a list of prices per token into the past,
            a price window,
            and a worst case percentage.

            It calculates the usd value of the portfolio for each of the blockstamps/timestamps.
            It then calculates the change in value over the window period for each timestamp,
            it returns the one that hits the input percentage.
        """

        df_value = pd.DataFrame()
        for pos in input.portfolio.positions:
            if not pos.token.symbol:
                raise ModelRunError(f'Input position is invalid, {input}')

            historical = self.context.run_model(
                'uniswap.v3-get-historical-price',
                {
                    'token': pos.token,
                    'window': input.window,
                    'interval': input.interval,
                })
            for p in historical['series']:
                p['price'] = p['output']['price']
                del p['output']

            df = pd.DataFrame(historical['series']).sort_values(
                ['blockNumber'], ascending=False)
            ret = df.price[:-1].to_numpy() / df.price[1:].to_numpy() - 1

            # Optional: the last block_number in df may not equal to the input block_number.
            # specify block_number=df.blockNumber.max() with run_model() to get the match price.
            current = self.context.run_model(
                'price', pos.token, return_type=Price)

            current_value = pos.amount * current.price
            value_changes = ret * current_value
            if pos.token.symbol in df_value:
                df_value.loc[:, pos.token.symbol] += value_changes
            else:
                df_value.loc[:, pos.token.symbol] = value_changes

        ppl = df_value.sum(axis=1).to_numpy()

        var = []
        for conf in input.confidence:
            var.append((self.calc_var(ppl, conf), conf))

        result = VaROutput(var=var)

        return result
