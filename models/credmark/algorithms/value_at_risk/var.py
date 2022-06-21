import numpy as np
import scipy.stats as sps
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import PriceList
from models.credmark.algorithms.value_at_risk.dto import (PortfolioVaRInput,
                                                          VaRHistoricalInput)
from models.credmark.algorithms.value_at_risk.risk_method import calc_var
from models.dtos.price import PriceHistoricalOutputs


@Model.describe(slug='finance.var-portfolio-historical',
                version='1.3',
                display_name='Value at Risk - for a portfolio',
                description='Calculate VaR based on input portfolio',
                input=PortfolioVaRInput,
                output=dict)
class VaRPortfolio(Model):
    def run(self, input: PortfolioVaRInput) -> dict:
        portfolio = input.portfolio

        assets_to_quote = set()
        for position in portfolio:
            if position.asset.address not in assets_to_quote:
                assets_to_quote.add(position.asset.address)

        t_unit, count = self.context.historical.parse_timerangestr(input.window)
        interval = self.context.historical.range_timestamp(t_unit, 1)

        assets_to_quote_list = list(assets_to_quote)
        token_historical_prices_run = self.context.run_model(
            slug='price.quote-historical-multiple',
            input={"inputs": [{'base': {'address': tok_addr}} for tok_addr in assets_to_quote_list],
                   "interval": interval,
                   "count": count,
                   "exclusive": False},
            return_type=PriceHistoricalOutputs)

        price_lists = []
        for asset_addr, hp in zip(assets_to_quote_list, token_historical_prices_run):
            ps = (hp.to_dataframe(fields=[('price', lambda p:p.price), ('src', lambda p:p.src), ])
                  .sort_values('blockNumber', ascending=False)
                  .reset_index(drop=True))

            price_list = PriceList(prices=ps['price'].to_list(),
                                   tokenAddress=asset_addr,
                                   src=ps['src'].to_list()[0])

            price_lists.append(price_list)

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
