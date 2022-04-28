from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError

from models.credmark.algorithms.value_at_risk.dto import (
    VaRHistoricalInput,
)

from models.credmark.algorithms.value_at_risk.risk_method import calc_var

import numpy as np


@Model.describe(slug='finance.var-engine-historical',
                version='1.1',
                display_name='Value at Risk',
                description='Value at Risk',
                input=VaRHistoricalInput,
                output=dict)
class VaREngineHistorical(Model):
    """
    This is the final step that consumes portfolio and the prices
    to calculate VaR(s) according to the VaR parameters.
    The prices in priceLists is asssumed be sorted in descending order in time.
    """

    def run(self, input: VaRHistoricalInput) -> dict:

        all_ppl_vec = None
        for pos in input.portfolio.positions:
            token = pos.asset
            amount = pos.amount

            priceLists = [pl for pl in input.priceLists if pl.tokenAddress == token.address]

            if len(priceLists) != 1:
                raise ModelRunError(f'There is no or more than 1 pricelist for {token.address=}')

            np_priceList = np.array(priceLists[0].prices)

            if input.interval > np_priceList.shape[0]-2:
                raise ModelRunError(
                    f'Interval {input.interval} is shall be of at most input list '
                    f'({np_priceList.shape[0]}-2) long.')

            value = amount * np_priceList[0]
            ret_series = np_priceList[:-input.interval] / np_priceList[input.interval:] - 1
            ppl_vector = value * ret_series
            if all_ppl_vec is None:
                all_ppl_vec = ppl_vector
            else:
                ppl_vec_len = ppl_vector.shape[0]
                all_ppl_vec_len = all_ppl_vec.shape[0]
                if all_ppl_vec_len != ppl_vec_len:
                    raise ModelRunError(
                        f'Input priceList for {token.address} has '
                        f'difference lengths has {ppl_vec_len} != {all_ppl_vec_len}')

                all_ppl_vec += ppl_vector

        output = {}
        for conf in input.confidences:
            output[conf] = calc_var(all_ppl_vec, conf)

        return output
