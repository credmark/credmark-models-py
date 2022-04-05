from typing import (
    List,
)

from datetime import (
    date,
)

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError

from credmark.dto import (
    DTO,
    IterableListGenericDTO,
    PrivateAttr,
)

from credmark.cmf.types import (
    Portfolio,
    Token,
    PriceList,
    Position,
)

from models.credmark.algorithms.risk_method import calc_var

import numpy as np


class HistoricalPriceInput(DTO):
    token: Token
    window: str  # e.g. '30 day'
    asOf: date


@Model.describe(slug='finance.example-historical-price',
                version='1.0',
                display_name='Value at Risk - Get Price Historical',
                description='Value at Risk - Get Price Historical',
                input=HistoricalPriceInput,
                output=PriceList)
class VaRPriceHistorical(Model):
    def run(self, input: HistoricalPriceInput) -> PriceList:
        token = input.token
        _w_k, w_i = self.context.historical.parse_timerangestr(input.window)

        # TODO: dummy data now, pending on server-side historical data implementation.
        return PriceList(
            prices=list(range(1, w_i+2)),
            tokenAddress=token.address,
            src=self.slug
        )


class VaRHistoricalInput(IterableListGenericDTO[PriceList]):
    portfolio: Portfolio
    priceLists: List[PriceList]
    interval: int  # 1 or 2 or 10
    confidences: List[float]
    _iterator: str = PrivateAttr('priceLists')


@Model.describe(slug='finance.var-engine-historical',
                version='1.0',
                display_name='Value at Risk',
                description='Value at Risk',
                input=VaRHistoricalInput,
                output=dict)
class VaREngineHistorical(Model):
    def run(self, input: VaRHistoricalInput) -> dict:

        all_ppl_vec = None
        for pos in input.portfolio.positions:
            token = pos.asset
            amount = pos.amount

            priceLists = [pl for pl in input.priceLists if pl.tokenAddress == token.address]

            if len(priceLists) != 1:
                raise ModelRunError(f'There is no pricelist for {token.address=}')

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


class DemoContractVaRInput(DTO):
    asOf: date
    window: str
    interval: int  # 1 or 2 or 10
    confidences: List[float]


@Model.describe(slug='finance.example-var-contract',
                version='1.0',
                display_name='Value at Risk',
                description='Value at Risk',
                input=DemoContractVaRInput,
                output=dict)
class DemoContractVaR(Model):
    """
    For below Demo VaR of 100 Aave + 100 USDC + 1 USDC
    Token price is assumed $1 each.
    Token price series is 1...31
    Windows is 30 days
    Interval is 3 days
    We shall have -142.6095 (0.01) -113.565 (0.05)

    # Demo command
    credmark-dev run finance.example-var-contract --input \
    '{"asOf": "2022-02-17", "window": "30 days", "interval": 3, "confidences": [0.01,0.05]}' \
    -l finance.example-var-contract,finance.example-historical-price,finance.var-engine-historical \
    -b 14234904 --format_json
    """

    def run(self, input: DemoContractVaRInput) -> dict:
        # Get the portfolio as of the input.asOf. Below is example input.
        portfolio = Portfolio(
            positions=[
                Position(asset=Token(symbol='AAVE'), amount=100),
                Position(asset=Token(symbol='USDC'), amount=100),
                Position(asset=Token(symbol='USDC'), amount=1)]
        )

        pls = []
        pl_assets = set()
        for pos in portfolio:
            if pos.asset.address not in pl_assets:
                historical_price_input = HistoricalPriceInput(token=pos.asset,
                                                              window=input.window,
                                                              asOf=input.asOf)
                pl = self.context.run_model(slug='finance.example-historical-price',
                                            input=historical_price_input,
                                            return_type=PriceList)
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
