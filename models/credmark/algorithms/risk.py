# Risk Engine v1
# - v1 Implement some TradeFi ideas here.
# - v2 Shall bring stateless eth here.

from abc import abstractmethod
from typing import (
    List,
)

import itertools

import numpy as np
import pandas as pd

from credmark.model import ModelRunError


class Tradeable:
    def __init__(self, tid):
        self._tid = tid

    @property
    def tid(self):
        return self._tid

    @abstractmethod
    def requires(self):
        pass

    @abstractmethod
    def value(self, mkt):
        pass


class TokenTradeable(Tradeable):
    def __init__(self, tid, token, amount, init_price):
        super().__init__(tid)
        self._token = token
        self._amount = amount
        self._init_price = init_price

    def requires(self):
        yield [{'token': self._token,
                'key': f'token.{self._token.address}.{self._token.symbol}'}]

    def value(self, mkt):
        key_col = (self._token.address, self._token.symbol)
        pnl = mkt.get(key_col) - self._init_price
        pnl *= self._amount
        return pnl


class ContractTradeable(Tradeable):
    def __init__(self, tid):
        super().__init__(tid)

    def requires(self):
        pass

    def value(self, mkt):
        return 0


# PortfolioManage shall request to Market to build the market information
class Market(dict):
    pass


class PortfolioManager:
    def __init__(self, trades: List[Tradeable]):
        self._trades = trades

    def requires(self):
        all_required = [t.requires() for t in self._trades]
        # breakpoint()
        merged_required = itertools.chain.from_iterable(all_required)
        for x in set(merged_required):
            yield x

    def value(self, mkts: List[Market], dict_base=None, as_dict=False):
        values = []
        for t in self._trades:
            for (scen_id, m) in enumerate(mkts):
                v = t.value(m)
                if dict_base:
                    v -= dict_base[t.tid]
                values.append((scen_id, t.tid, v))

        df_res = pd.DataFrame(values, columns=['SCEN_ID', 'TRADE_ID', 'VALUE'])
        if as_dict:
            # breakpoint()
            return df_res.loc[:, ['TRADE_ID', 'VALUE']].to_dict()
        return df_res


def calc_var(ppl, lvl):
    if lvl < 0 or lvl > 1:
        raise ModelRunError(f'Invalid confidence level {lvl=}')

    len_ppl_d = ppl.shape[0]
    if len_ppl_d <= 1:
        raise ModelRunError(f'PPL is too short to calculate VaR {ppl=}')

    ppl_d = ppl.copy()
    ppl_d.sort()
    if lvl == 0:
        return ppl_d[0]
    if lvl == 1:
        return ppl_d[-1]

    pos_f = lvl * (len_ppl_d - 1)
    if np.isclose(pos_f, 0):
        return ppl_d[0]
    if np.isclose(pos_f, len_ppl_d - 1):
        return ppl_d[-1]
    lower = int(np.floor(pos_f))
    upper = lower+1
    res = ppl_d[lower] * (upper - pos_f) + ppl_d[upper] * (pos_f - lower)
    return res
