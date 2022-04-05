from ctypes.wintypes import PPOINTL
from typing import (
    List,
)

from datetime import (
    datetime,
    timezone,
    date,
)

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError

from credmark.dto import (
    DTO,
    DTOField,
    IterableListGenericDTO,
    PrivateAttr,
)

from credmark.cmf.types import (
    Portfolio,
    Price,
    Address,
    Token,
    Position,
    PriceList,
)

import numpy as np


class HistoricalPriceInput(DTO):
    token: Token
    window: str  # e.g. '30 day'
    asOf: date


@Model.describe(slug='finance.var-price-historical',
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
            prices=list(range(1, w_i)),
            tokenAddress=token.address,
            src=self.slug
        )


class VaRHistoricalInput(IterableListGenericDTO[PriceList]):
    portfolio: Portfolio
    priceLists: List[PriceList]
    interval: int  # 1 or 2 or 10
    _iterator: str = PrivateAttr('priceLists')


@Model.describe(slug='finance.var-engine-historical',
                version='1.0',
                display_name='Value at Risk',
                description='Value at Risk',
                input=HistoricalPriceInput,
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

            np_priceList = np.array(priceLists[0])

            if input.interval > np_priceList.shape[0]-2:
                raise ModelRunError(
                    'Interval {interval} is shall be of at most input list ({np_priceList.shape[0]}-2) long.')

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

        v = calc_var(ppl, conf)


class XXXContractVaRInput(DTO):
    portfolio: Portfolio
    asOf: date
    window: str
    interval: int  # 1 or 2 or 10
