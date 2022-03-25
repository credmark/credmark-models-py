from credmark.dto import (
    DTO
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


class MarketObject(DTO):
    key: str
    artifact: Any


class Tradeable:
    def __init__(self, tid):
        self._tid = tid

    @property
    def tid(self):
        return self._tid

    @abstractmethod
    def requires(self) -> Generator[MarketObject, None, None]:
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

    def requires(self) -> Generator[MarketObject, None, None]:
        mkt_obj = MarketObject(key=f'token.{self._token.address}.{self._token.symbol}',
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

    def requires(self) -> Generator[MarketObject, None, None]:
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
            if not pos.token.address:
                raise ModelRunError(f'Input position is invalid, {input}')

            t = TokenTradeable(pos_n, pos.token, pos.amount, init_price=0)
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
