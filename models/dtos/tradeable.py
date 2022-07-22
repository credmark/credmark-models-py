from abc import abstractmethod
from datetime import datetime
from typing import Any, Generator, Optional

from credmark.dto import DTO
from credmark.cmf.types import BlockNumber


class MarketTarget(DTO):
    """
    Used by PortfolioManage to build the market
    """
    key: str  # ensure unique in market oject
    artifact: Any
    block_number: BlockNumber


class Market(dict):
    pass


class Tradeable:
    def __init__(self, tid, traces):
        """
        traces is a table stores all properties of the trade in time sequence.
        """
        self.__tid = tid
        self.__traces = traces

    @ property
    def tid(self):
        return self.__tid

    @ property
    def traces(self):
        return self.__traces

    @ abstractmethod
    def requires(self, block_number: BlockNumber) -> Generator[MarketTarget, None, None]:
        pass

    @ abstractmethod
    def value(self,
              as_of: datetime,
              tag: str,
              mkt: Market,
              mkt_adj=lambda x: x) -> float:
        ...

    @ abstractmethod
    def value_scenarios(self,
                        as_of: datetime,
                        tag: str,
                        tag_scenario: str,
                        mkt: Market,
                        mkt_scenarios: Market) -> pd.Series:
        ...


class TokenTradeable(Tradeable):
    def __init__(self, tid, traces, token, amount, init_price, block_number: BlockNumber, end_block_number: Optional[BlockNumber]):
        super().__init__(tid, traces)
        self._token = token
        self._amount = amount
        self._init_price = init_price
        self._block_number = block_number
        self._end = end_block_number
        self._key = f'Token.{self._token.address}'

    @ property
    def key(self):
        return self._key

    def requires(self, block_number: BlockNumber) -> Generator[MarketTarget, None, None]:
        mkt_target = MarketTarget(key=self.key,
                                  artifact=self._token,
                                  block_number=block_number)
        yield mkt_target

    def value(self,
              block_number: BlockNumber,
              tag: str,
              mkt: Market,
              mkt_adj=lambda x: x) -> float:
        """
        TokenTrade's value does not change with the as_of to the Tradeable's own as_of
        Other type of trade could have time value.
        """
        curent_price = mkt_adj(mkt[(block_number, tag, self.key)]['extracted'])
        pnl = curent_price - self._init_price
        pnl *= self._amount
        return pnl

    def value_scenarios(self,
                        as_of: datetime,
                        tag: str,
                        tag_scenario: str,
                        mkt: Market,
                        mkt_scenarios: Market) -> pd.Series:
        base_pnl = self.value(as_of, tag, mkt)
        scen_pnl = []
        scenarios = mkt_scenarios[(tag_scenario, self.key)]['extracted']
        for scen in scenarios:
            new_pnl = self.value(as_of, tag, mkt, lambda x, scen=scen: x * scen)
            scen_pnl.append(new_pnl)
        return pd.Series(scen_pnl) - base_pnl
