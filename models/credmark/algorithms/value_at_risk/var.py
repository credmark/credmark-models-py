import numpy as np
import scipy.stats as sps
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import Account, Price, PriceList, TokenPosition
from credmark.cmf.types.compose import MapBlockTimeSeriesOutput
from models.credmark.accounts.account import CurveLPPosition
from models.credmark.algorithms.value_at_risk.dto import (AccountVaRInput,
                                                          PortfolioVaRInput,
                                                          VaRHistoricalInput)
from models.credmark.algorithms.value_at_risk.risk_method import (VaROutput,
                                                                  calc_var)
from models.dtos.price import Prices


@Model.describe(
    slug="account.var",
    version="0.2",
    display_name="VaR for an account",
    description="VaR for an account",
    developer="Credmark",
    category='financial',
    input=AccountVaRInput,
    output=dict)
class AccountVaR(Model):
    def run(self, input: AccountVaRInput) -> dict:
        portfolio = self.context.run_model('account.portfolio',
                                           Account(address=input.address))

        positions = [TokenPosition(**p) if 'lp_position' not in p else CurveLPPosition(**p)
                     for p in portfolio['positions']]
        port_var_input = {'portfolio': {'positions': positions},
                          'window': input.window,
                          'interval': input.interval,
                          'confidence': input.confidence}
        return self.context.run_model('finance.var-portfolio-historical',
                                      port_var_input)


@Model.describe(slug='finance.var-portfolio-historical',
                version='1.5',
                display_name='Value at Risk - for a portfolio',
                description='Calculate VaR based on input portfolio',
                input=PortfolioVaRInput,
                output=dict)
class VaRPortfolio(Model):
    def run(self, input: PortfolioVaRInput) -> dict:
        portfolio = input.portfolio

        assets_to_quote = set()
        for position in portfolio:
            if isinstance(position, CurveLPPosition):
                for lp_pos in position.lp_position:
                    if lp_pos.asset.address not in assets_to_quote:
                        assets_to_quote.add(lp_pos.asset.address)
            if position.asset.address not in assets_to_quote:
                assets_to_quote.add(position.asset.address)

        t_unit, count = self.context.historical.parse_timerangestr(input.window)
        interval = self.context.historical.range_timestamp(t_unit, 1)

        assets_to_quote_list = list(assets_to_quote)

        # TODO: kept two versions to see how r8unner's performance can avoid timeout
        def _use_compose_map():
            tok_hp = self.context.run_model(
                slug='price.quote-historical-multiple',
                input={"inputs": [{'base': {'address': tok_addr}}
                                  for tok_addr in assets_to_quote_list],
                       "interval": interval,
                       "count": count,
                       "exclusive": False},
                return_type=MapBlockTimeSeriesOutput[Prices])

            price_lists = []
            for tok_n, asset_addr in enumerate(assets_to_quote_list):
                ps = (tok_hp.to_dataframe(fields=[('price', lambda p, n=tok_n:p[n].price),
                                                  ('src', lambda p, n=tok_n:p.prices[n].src), ])
                      .sort_values('blockNumber', ascending=False)
                      .reset_index(drop=True))

                price_list = PriceList(prices=ps['price'].to_list(),
                                       tokenAddress=asset_addr,
                                       src=ps['src'].to_list()[0])

                price_lists.append(price_list)
            return price_lists

        def _use_for():
            price_lists = []
            for asset_addr in assets_to_quote_list:
                tok_hp = self.context.run_model(
                    slug='price.quote-historical',
                    input={'base': {'address': asset_addr},
                           "interval": interval,
                           "count": count,
                           "exclusive": False},
                    return_type=MapBlockTimeSeriesOutput[Price])

                ps = (tok_hp.to_dataframe(fields=[('price', lambda p:p.price),
                                                  ('src', lambda p:p.src), ])
                      .sort_values('blockNumber', ascending=False)
                      .reset_index(drop=True))

                price_list = PriceList(prices=ps['price'].to_list(),
                                       tokenAddress=asset_addr,
                                       src=ps['src'].to_list()[0])

                price_lists.append(price_list)

            return price_lists

        price_lists = _use_for()

        var_input = {
            'portfolio': portfolio,
            'priceLists': price_lists,
            'interval': input.interval,
            'confidence': input.confidence}

        return self.context.run_model(slug='finance.var-engine-historical',
                                      input=var_input,
                                      return_type=dict)


@Model.describe(slug='finance.var-engine-historical',
                version='1.5',
                display_name='Value at Risk',
                description='Value at Risk',
                category='financial',
                input=VaRHistoricalInput,
                output=dict)
class VaREngineHistorical(Model):
    """
    This is the final step that consumes portfolio and the prices
    to calculate VaR(s) according to the VaR parameters.
    The prices in priceLists is asssumed be sorted in descending order in time.
    """

    value_list = []
    total_value = 0
    all_ppl_arr = np.array([])

    def calculate_ppl(self, token, amount, input):
        priceLists = [pl for pl in input.priceLists if pl.tokenAddress == token.address]

        if len(priceLists) != 1:
            raise ModelRunError(f'There is no or more than 1 pricelist for {token.address=}')

        np_priceList = np.array(priceLists[0].prices)

        if input.interval > np_priceList.shape[0]-2:
            raise ModelRunError(
                f'Interval {input.interval} is shall be of at most input list '
                f'({np_priceList.shape[0]}-2) long.')

        value = amount * np_priceList[0]
        self.total_value += value
        self.value_list.append((token.address, amount, np_priceList[0], value))
        ret_series = np_priceList[:-input.interval] / np_priceList[input.interval:] - 1
        # ppl: potential profit&loss
        ppl_vector = value * ret_series
        return ppl_vector

    def fill_ppl(self, ppl_vector, token):
        if self.all_ppl_arr.shape[0] == 0:
            self.all_ppl_arr = ppl_vector[:, np.newaxis]
        else:
            ppl_vec_len = ppl_vector.shape[0]
            all_ppl_vec_len = self.all_ppl_arr.shape[0]
            if all_ppl_vec_len != ppl_vec_len:
                raise ModelRunError(
                    f'Input priceList for {token.address} has '
                    f'difference lengths has {ppl_vec_len} != {all_ppl_vec_len}')

            self.all_ppl_arr = np.column_stack([self.all_ppl_arr, ppl_vector])

    def run(self, input: VaRHistoricalInput) -> dict:
        self.value_list = []
        self.total_value = 0
        self.all_ppl_arr = np.array([])

        for _pos_n, pos in enumerate(input.portfolio):
            if isinstance(pos, CurveLPPosition):
                lp_vec_ppl = None
                for _lp_pos_n, lp_pos in enumerate(pos.lp_position):
                    token = lp_pos.asset
                    amount = lp_pos.amount
                    ppl_vector = self.calculate_ppl(token, amount, input)
                    if lp_vec_ppl is None:
                        lp_vec_ppl = ppl_vector
                    else:
                        lp_vec_ppl += ppl_vector
                self.fill_ppl(lp_vec_ppl, pos.asset)
            else:
                token = pos.asset
                amount = pos.amount
                ppl_vector = self.calculate_ppl(token, amount, input)
                self.fill_ppl(ppl_vector, token)

        output = {}

        if self.all_ppl_arr.shape[0] == 0:
            return {'cvar': [], 'var': VaROutput.default(), 'total_vlaue': 0, 'value_list': []}

        all_ppl_vec = self.all_ppl_arr.sum(axis=1)
        weights = np.ones(len(input.portfolio.positions))
        for i in range(len(input.portfolio.positions)):
            try:
                linreg_result = sps.linregress(all_ppl_vec, self.all_ppl_arr[:, i])
                weights[i] = linreg_result.slope
            except ValueError as err:
                if 'Cannot calcualte a linear regression if all x values are identical' in str(err):
                    weights[i] = 0
        weights /= weights.sum()

        output['cvar'] = weights
        var_result = calc_var(all_ppl_vec, input.confidence)
        output['var'] = var_result.var

        output['total_value'] = self.total_value
        output['value_list'] = self.value_list
        return output
