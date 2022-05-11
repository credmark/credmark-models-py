from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError

from credmark.cmf.types import PriceList, Price


from models.credmark.algorithms.value_at_risk.dto import (
    VaRHistoricalInput,
    PortfolioVaRInput,
)

from models.credmark.algorithms.value_at_risk.risk_method import calc_var

import numpy as np


@Model.describe(slug='finance.var-portfolio-historical',
                version='1.0',
                display_name='Value at Risk - for a portfolio',
                description='Calculate VaR based on input portfolio',
                input=PortfolioVaRInput,
                output=dict)
class VaRPortfolio(Model):
    def run(self, input: PortfolioVaRInput) -> dict:
        portfolio = input.portfolio

        pls = []
        pl_assets = set()
        for pos in portfolio:
            if pos.asset.address not in pl_assets:
                hp = self.context.historical.run_model_historical(model_slug='token.price',
                                                                  model_input=pos.asset,
                                                                  window=input.window,
                                                                  model_return_type=Price)
                ps = [p.output.price for p in hp if p.output.price is not None][::-1]
                if len(ps) < len(hp.series):
                    raise ModelRunError('Received None output for token price.'
                                        'Check the series '
                                        f'{[(p.output.price,p.blockNumber) for p in hp]}')
                pl = PriceList(prices=ps,
                               tokenAddress=pos.asset.address,
                               src=list({p.output.src for p in hp})[0])
                pls.append(pl)
                pl_assets.add(pos.asset.address)

        var_input = VaRHistoricalInput(
            portfolio=portfolio,
            priceLists=pls,
            interval=input.interval,
            confidences=input.confidences,
        )

        return self.context.run_model(slug='finance.var-engine-historical',
                                      input=var_input,
                                      return_type=dict)


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
