from datetime import (
    date,
)

from credmark.dto import (
    DTO,
    EmptyInput,
)

from abc import abstractmethod
from typing import (
    List,
    Any,
    Generator,
)

import pandas as pd

from credmark.types import (
    Portfolio,
)

from credmark.model import (
    ModelRunError,
)

import os
import pickle


class MarketTarget(DTO):
    key: str
    artifact: Any


class Recipe(DTO):
    key: str
    artifact: Any
    tag: str
    window: str
    interval: str
    asOf: date


class Plan:
    @abstractmethod
    def create(self, MarketTarget, tag):
        pass

    @abstractmethod
    def post_proc(self):
        pass


class Cook:
    def __init__(self):
        self._cache_file = os.path.join('tmp', 'chain.cache.pkl')

    def load_cache(self):
        with open(self._cache_file, 'rb') as handle:
            self._cache = pickle.load(handle)

    def save_cache(self):
        with open('filename.pickle', 'wb') as handle:
            pickle.dump(self._cache, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def getBlockasOf(self, context, window, interval, asOf_block_number):
        res = context.historial_utils.run_model_history('finance.get-one',
                                                        window=window,
                                                        interval=interval,
                                                        model_input=EmptyInput,
                                                        block_number=asOf_block_number
                                                        )
        print('get_block_for_asOf: res')
        breakpoint()
        return res

    def cook(self, context, recipe):
        result = {}
        for rr in recipe:
            if rr.key not in result:
                if rr.key in self._cache:
                    result[rr.key] = self._cache[rr.key]
                else:
                    price = context.run_model_historical('token.price-ext',  # 'uniswap-v3.get-average-price',  # 'token.price',
                                                         model_input=rr.artifact,
                                                         block_number=rr.asOf_block_number)
                    result[rr.key] = price
                    self._cache[rr.key] = price
                    self.save_cache()
        return result


class EODPlan(Plan):
    def init(self, context, mkt: MarketTarget, tag, asOf):
        self._recipe = [Recipe(key=f'{mkt.key}.{tag}.{asOf:%Y-%m-%d}',
                               artifact=mkt.artifact,
                               tag=tag,
                               asOf=asOf,
                               window='1 day',
                               interval='1 day')]

    def post_proc(self):
        return super().execute()


class VaRPlan(Plan):
    def create(self, mkt: MarketTarget, tag, window, interval):
        return Recipe(key=f'{mkt.key}.{tag}.{asOf:%Y-%m-%d}',
                      artifact=mkt.artifact,
                      tag=tag,
                      asOf=asOf)


tag = 'eod'


class Tradeable:
    def __init__(self, tid):
        self._tid = tid

    @property
    def tid(self):
        return self._tid

    @abstractmethod
    def requires(self) -> Generator[MarketTarget, None, None]:
        pass

    @abstractmethod
    def value(self, mkt) -> float:
        pass


class TokenTradeable(Tradeable):
    def __init__(self, tid, token, amount, init_price):
        super().__init__(tid)
        self._token = token
        self._amount = amount
        self._init_price = init_price

    def requires(self) -> Generator[MarketTarget, None, None]:
        mkt_obj = MarketTarget(key=f'token.{self._token.address}.{self._token.symbol}',
                               artifact=self._token)
        yield mkt_obj

    def value(self, mkt) -> float:
        key_col = (self._token.address, self._token.symbol)
        pnl = mkt.get(key_col) - self._init_price
        pnl *= self._amount
        return pnl


class ContractTradeable(Tradeable):
    def __init__(self, tid):
        super().__init__(tid)

    def requires(self) -> Generator[MarketTarget, None, None]:
        yield from []

    def value(self, mkt) -> float:
        return 0


# PortfolioManage shall request to Market to build the market information


class Market(dict):
    pass

# TODO: to be merged with framework's Portfolio


class PortfolioManager:
    def __init__(self, trades: List[Tradeable]):
        self._trades = trades

    @ classmethod
    def from_portfolio(cls, portfolio: Portfolio):
        trades = []
        for (pos_n, pos) in enumerate(portfolio.positions):
            if not pos.asset.address:
                raise ModelRunError(f'Input position is invalid, {input}')

            t = TokenTradeable(pos_n, pos.asset, pos.amount, init_price=0)
            trades.append(t)
        return cls(trades)

    def requires(self):
        key_set = set()
        for t in self._trades:
            for req in t.requires():
                if req.key not in key_set:
                    key_set.add(req.key)
                    yield req.key, req.artifact

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
