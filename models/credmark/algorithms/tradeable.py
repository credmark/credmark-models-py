from abc import abstractmethod
from credmark.cmf.model.errors import (
    ModelRunError,
)

from credmark.cmf.types import (
    Portfolio,
)

from credmark.dto import (
    DTO,
)

from datetime import (
    datetime
)

import pandas as pd
import itertools
from typing import (
    List,
    Any,
    Generator,

)

from models.credmark.algorithms.recipe import (
    RiskObject,
    validate_as_of,
)

from models.credmark.algorithms.chef import (
    Chef,
    kitchen,
)

from models.credmark.algorithms.plan import (
    TokenEODPlan,
)


class MarketTarget(DTO):
    key: str  # ensure unique in market oject
    artifact: Any


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
    def requires(self) -> Generator[MarketTarget, None, None]:
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
    def __init__(self, tid, traces, as_of, token, amount, init_price):
        super().__init__(tid, traces)
        assert validate_as_of(as_of)
        self._as_of = as_of
        self._token = token
        self._amount = amount
        self._init_price = init_price
        self._key = f'Token.{self._token.address}'

    @ property
    def key(self):
        return self._key

    def requires(self) -> Generator[MarketTarget, None, None]:
        mkt_target = MarketTarget(key=self.key,
                                  artifact=self._token)
        yield mkt_target

    def value(self,
              as_of: datetime,
              tag: str,
              mkt: Market,
              mkt_adj=lambda x: x) -> float:
        """
        TokenTrade's value does not change with the as_of to the Tradeable's own as_of
        Other type of trade could have time value.
        """

        # DEPRECATED Code of retriving price
        # idx_last = mkt_piece.index.get_loc(
        #   mkt_piece.index[mkt_piece['blockTime'] <= as_of][0])
        # curent_price = mkt_piece[f'{self.key}.price'].iloc[idx_last]

        curent_price = mkt_adj(mkt[(tag, self.key)]['extracted'])
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


class ContractTradeable(Tradeable):
    def __init__(self, as_of, tid):
        super().__init__(as_of, tid)

    def requires(self) -> Generator[MarketTarget, None, None]:
        yield from []

    def value(self,
              as_of: datetime,
              tag: str,
              mkt: Market,
              mkt_adj=lambda x: x) -> float:
        return 0

    def value_scenarios(self,
                        as_of: datetime,
                        tag: str,
                        tag_scenario: str,
                        mkt: Market,
                        mkt_scenarios: Market) -> pd.Series:
        return pd.Series([0 for _ in mkt_scenarios])


# PortfolioManage shall request to Market to build the market information

# TODO: to be merged with framework's Portfolio


class PortfolioManager(RiskObject):
    def __init__(self,
                 trades: List[Tradeable],
                 as_of,
                 context,
                 use_kitchen,
                 reset_cache,
                 verbose,
                 use_cache):
        """
        Initialize PortfolioManager with
        1. use_kitchen = True and context: connect to a kitchen
        2. use_kitchen = False and context: dispatch own chef
        3. (not implementeed) use_kitchen = False and chef: call an existing chef
        """

        self._chef = None
        self._trades = trades
        self._as_of = as_of
        self._verbose = verbose
        self._reset_cache = reset_cache
        self._use_kitchen = use_kitchen

        if context is None:
            raise ModelRunError(f'! Missing context to '
                                f'initialize a {self.__class__.__name__}')
        self._context = context

        if not self._use_kitchen:
            self._chef = Chef(self._context,
                              self.__class__.__name__,
                              reset_cache=reset_cache,
                              use_cache=use_cache,
                              verbose=verbose)

    def __del__(self):
        if self._use_kitchen:
            kitchen.save_cache()
        if self._chef is not None:
            self._chef.save_cache()
        if self._verbose:
            self._context.logger.info(f'# {self.name_id} Closed.')

    @ classmethod
    def from_portfolio(cls,
                       as_of,
                       portfolio: Portfolio,
                       context,
                       use_kitchen=True,
                       reset_cache=False,
                       use_cache=True,
                       verbose=False):
        trades = []
        for (pos_n, pos) in enumerate(portfolio.positions):
            if not pos.asset.address:
                raise ModelRunError(f'! Input position is invalid, {input}')

            tid = f'{pos_n}.{pos.asset.address}'
            t = TokenTradeable(tid, [], as_of, pos.asset, pos.amount, init_price=0)
            trades.append(t)
        return cls(trades,
                   as_of,
                   context=context,
                   use_kitchen=use_kitchen,
                   reset_cache=reset_cache,
                   verbose=verbose,
                   use_cache=use_cache)

    def requires(self) -> Generator[MarketTarget, None, None]:
        key_set = set()
        for t in self._trades:
            for req in t.requires():
                if req.key not in key_set:
                    key_set.add(req.key)
                    yield req

    def prepare_market(self, tag, **input_to_plan):
        mkt_target = list(self.requires())

        if self._verbose:
            self._context.logger.info(
                f'# {self.name_id} Preparing market with {len(mkt_target)=} for {tag}')

        mkt = Market()

        if not self._use_kitchen:
            context_or_chef = {'chef': self._chef}
        else:
            context_or_chef = {'context': self._context}

        for target in mkt_target:
            pl = TokenEODPlan(tag=tag,
                              target_key=target.key,
                              use_kitchen=self._use_kitchen,
                              **context_or_chef,
                              reset_cache=self._reset_cache,
                              verbose=self._verbose,
                              input_token=target.artifact,
                              **input_to_plan)
            mkt[(tag, target.key)] = pl.execute()

        if self._verbose:
            self._context.logger.info(
                f'# {self.name_id} Finished preparing for market with {len(mkt_target)=} for {tag}')

        return mkt

    def value(self,
              tag: str,
              mkt: Market,
              as_df=True,
              **input_to_value):
        values = []
        as_of = input_to_value.get('as_of', self._as_of)

        for t in self._trades:
            v = t.value(as_of, tag, mkt)
            values.append((t.tid, v))
        df_res = pd.DataFrame(values, columns=['TRADE_ID', 'VALUE'])
        if as_df:
            return df_res
        return df_res.loc[:, ['TRADE_ID', 'VALUE']].to_dict()

    def value_scenarios(self,
                        tag: str,
                        tag_scenario: str,
                        mkt: Market,
                        mkt_scenarios: Market,
                        as_df=True,
                        **input_to_value):
        values = []
        as_of = input_to_value.get('as_of', self._as_of)

        for t in self._trades:
            v = t.value_scenarios(as_of, tag, tag_scenario, mkt, mkt_scenarios)
            values.extend(zip(itertools.count(1), itertools.repeat(t.tid), v))
        df_res = (pd.DataFrame(values, columns=['SCEN_ID', 'TRADE_ID', 'VALUE'])
                  .sort_values(['SCEN_ID', 'TRADE_ID'])
                  .reset_index(drop=True))
        if as_df:
            return df_res
        return df_res.to_dict(orient='index')
