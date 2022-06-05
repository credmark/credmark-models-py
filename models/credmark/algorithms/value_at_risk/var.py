from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError

from credmark.cmf.types import PriceList, Price


from models.credmark.algorithms.value_at_risk.dto import (
    VaRHistoricalInput,
    PortfolioVaRInput,
)

from models.credmark.algorithms.value_at_risk.risk_method import calc_var

import numpy as np
import scipy.stats as sps


@Model.describe(slug='finance.var-portfolio-historical',
                version='1.3',
                display_name='Value at Risk - for a portfolio',
                description='Calculate VaR based on input portfolio',
                input=PortfolioVaRInput,
                output=dict)
class VaRPortfolio(Model):
    def run(self, input: PortfolioVaRInput) -> dict:
        portfolio = input.portfolio

        pl_assets = set()
        price_lists = []
        for position in portfolio:
            if position.asset.address not in pl_assets:
                historial_price = self.context.historical.run_model_historical(
                    model_slug='price.cmf',
                    model_input=position.asset,
                    window=input.window,
                    model_return_type=Price)
                if len(historial_price.series) > 1:
                    assert (historial_price.series[0].blockNumber -
                            historial_price.series[1].blockNumber < 0)
                # Reverse the order of data so the recent in the front.
                ps = [p.output.price for p in historial_price if p.output.price is not None][::-1]
                if len(ps) < len(historial_price.series):
                    raise ModelRunError(
                        'Received None output for token price.'
                        'Check the series '
                        f'{[(p.output.price,p.blockNumber) for p in historial_price]}')
                price_list = PriceList(prices=ps,
                                       tokenAddress=position.asset.address,
                                       src=list({p.output.src for p in historial_price})[0])
                price_lists.append(price_list)
                pl_assets.add(position.asset.address)

        var_input = VaRHistoricalInput(
            portfolio=portfolio,
            priceLists=price_lists,
            interval=input.interval,
            confidence=input.confidence,
        )

        return self.context.run_model(slug='finance.var-engine-historical',
                                      input=var_input,
                                      return_type=dict)


@Model.describe(slug='finance.var-engine-historical',
                version='1.4',
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
        total_value = 0
        value_list = []

        all_ppl_arr = np.array([])
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
            total_value += value
            value_list.append((token.address, amount, np_priceList[0], total_value))
            ret_series = np_priceList[:-input.interval] / np_priceList[input.interval:] - 1
            # ppl: potential profit&loss
            ppl_vector = value * ret_series

            if all_ppl_arr.shape[0] == 0:
                all_ppl_arr = ppl_vector[:, np.newaxis]
            else:
                ppl_vec_len = ppl_vector.shape[0]
                all_ppl_vec_len = all_ppl_arr.shape[0]
                if all_ppl_vec_len != ppl_vec_len:
                    raise ModelRunError(
                        f'Input priceList for {token.address} has '
                        f'difference lengths has {ppl_vec_len} != {all_ppl_vec_len}')

                all_ppl_arr = np.column_stack([all_ppl_arr, ppl_vector])

        output = {}

        all_ppl_vec = all_ppl_arr.sum(axis=1)

        weights = np.ones(len(input.portfolio.positions))
        for i in range(len(input.portfolio.positions)):
            linreg_result = sps.linregress(all_ppl_arr[:, i], all_ppl_vec)
            weights[i] = linreg_result.slope
        weights /= weights.sum()

        output['cvar'] = weights
        var_result = calc_var(all_ppl_vec, input.confidence)
        output['var'] = var_result.var

        output['total_value'] = total_value
        output['value_list'] = value_list
        return output
