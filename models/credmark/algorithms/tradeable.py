from abc import abstractmethod
from datetime import (
    date,
    datetime,
    timezone,
)

from typing import (
    Callable,
    List,
    Any,
    Generator,
    Tuple,
    Union,
    Type,
)

import itertools

import pandas as pd

from credmark.dto import (
    DTO,
    DTOField,
)

from credmark.types import (
    Portfolio,
    Token,
)

from credmark.model import (
    ModelRunError,
)

import os
import pickle


class MarketTarget(DTO):
    key: str  # ensure unique in market oject
    artifact: Any


class Recipe(DTO):
    cache_key: str  # ensure unique in global cache
    target_key: str  # key for MarketTarget
    method: str
    input: dict
    post_proc: Callable = DTOField(default=lambda _context, data: data)
    return_type: Union[Type[DTO], None] = DTOField(default=None)


class Chef:
    def __init__(self, context, slug, reset_cache=False, use_cache=True, verbose=False):
        if slug is None or slug == '':
            raise ModelRunError('! Chef needs to be initialized with a non-empty slug.')
        self._cache_file = os.path.join('tmp', f'chef_cache_chain_id_{context.chain_id}_{slug}.pkl')
        self._cache = {'__log__': [datetime.now()]}
        self._cache_hit = 0
        self._total_hit = 0
        self._context = context
        self._use_cache = use_cache
        self._cache_saved = False
        self._reset_cache = reset_cache
        self._verbose = verbose

        if self._verbose:
            if self._reset_cache:
                self._context.logger.info(
                    f'=== Dispatched Chef({hex(id(self))}) on {self._cache_file} in reset mode overwriting existing')
            else:
                self._context.logger.info(
                    f'=== Dispatched Chef({hex(id(self))}) on {self._cache_file}')
        if self._use_cache:
            self._load_cache()

    def __del__(self):
        if self._use_cache:
            if self._verbose:
                self.cache_status()
            if not self._cache_saved:
                self._save_cache()
        if self._verbose:
            self._context.logger.info(f'=== Released Chef({hex(id(self))}) on {self._cache_file}')

    def _load_cache(self):
        try:
            if os.path.isfile(self._cache_file):
                with open(self._cache_file, 'rb') as handle:
                    self._cache = pickle.load(handle)
                    self._cache_saved = True
                    self.cache_info(' opened')
        except EOFError:
            self._context.logger.warning(
                f'* Local cache from {self._cache_file} is corrupted. Reset.')
            self._save_cache()

    def _save_cache(self):
        if not self._cache_saved:
            cache_dir = os.path.dirname(self._cache_file)
            if not os.path.isdir(cache_dir):
                os.mkdir(cache_dir)
            with open(self._cache_file, 'wb') as handle:
                self._cache['__log__'].append(datetime.now())
                pickle.dump(self._cache, handle, protocol=pickle.HIGHEST_PROTOCOL)
                self._cache_saved = True
                self.cache_info(' closed')

    def cache_info(self, message=''):
        if self._verbose:
            cache_log = self._cache.get('__log__', [datetime.now()])
            cache_log_info = (f'[{min(cache_log):%Y-%m-%d %H:%M:%S}] to '
                              f'[{max(cache_log):%Y-%m-%d %H:%M:%S}] '
                              f'for saved {len(cache_log)} times '
                              f'with {len(self._cache)} entries.')
            self._context.logger.info(f'* Local cache from {self._cache_file} '
                                      f'with {cache_log_info}'
                                      f'{message}')

    @ property
    def context(self):
        return self._context

    @ property
    def cache_hit(self):
        return self._cache_hit

    @ property
    def total_hit(self):
        return self._total_hit

    def cache_status(self):
        if self.total_hit != 0:
            self._context.logger.info(
                f'* Local cache hit {self.cache_hit} for {self.total_hit} requests '
                f'rate={self.cache_hit/self.total_hit*100:.1f}%')

    def cook(self, rec: Recipe):
        result = None
        if self._use_cache and not self._reset_cache and rec.cache_key in self._cache:
            if self._verbose:
                self.context.logger.info(f'> Chef({hex(id(self))}) takes {rec.cache_key}')
            result = self._cache[rec.cache_key]
            self._cache_hit += 1
            self._total_hit += 1
            if rec.return_type is not None and issubclass(rec.return_type, DTO):
                return rec.return_type(**result)
            else:
                return result
        else:
            if self._verbose:
                self.context.logger.info(f'> Chef({hex(id(self))}) cooks {rec.cache_key}')

            if rec.method == 'run_model':
                result = self._context.run_model(**rec.input)
            elif rec.method == 'run_model_historical':
                result = self._context.historical.run_model_historical(
                    **rec.input)
            elif rec.method == 'block_number.from_timestamp':
                result = self._context.block_number.from_timestamp(**rec.input)
            else:
                raise ModelRunError(f'! Unknown {rec.method=}')
            result = rec.post_proc(self._context, result)
            if (isinstance(result, DTO) and
                    rec.return_type is not None and issubclass(rec.return_type, DTO)):
                untyped_result = result.dict()
            else:
                untyped_result = result
            self._cache[rec.cache_key] = untyped_result
            self._cache_saved = False
            self._total_hit += 1

        return result


def validate_as_of(as_of):
    return isinstance(as_of, datetime) and as_of.tzinfo is not None


class Plan:
    def __init__(self,
                 tag,
                 target: MarketTarget,
                 slug: Union[str, None] = None,
                 context=None,
                 chef=None,
                 return_type=None,
                 reset_cache: bool = False,
                 verbose: bool = False,
                 **data):
        self._tag = tag
        self._target = target
        self._data = data
        self._return_type = return_type
        self._result = None
        self._verbose = verbose

        self._chef = None
        self._chef_internal = None
        self._acquire_chef(chef, context, slug=slug, reset_cache=reset_cache, verbose=verbose)

    @property
    def chef(self):
        if self._chef is not None:
            return self._chef
        else:
            raise ModelRunError('! Chef is not around')

    def __del__(self):
        self._release_chef()

    def _acquire_chef(self, chef, context, slug, reset_cache, verbose):
        if context is None and chef is not None:
            self._chef = chef
            self._chef_internal = False
        elif context is not None and chef is None:
            self._chef = Chef(context, slug, reset_cache, verbose=verbose)
            self._chef_internal = True
        else:
            raise ModelRunError(f'! Missing either context or chef to '
                                f'execute a {self.__class__.__name__}')

    def _release_chef(self):
        if self._chef is not None:
            if self._verbose:
                self._chef.context.logger.info(f'| Finished executing {self._target.key}')
            if self._chef_internal:
                del self._chef
            else:
                if self._verbose:
                    self._chef.cache_status()
            self._chef = None

    def post_proc(self, _context, data):
        return data

    def execute(self):
        if self._chef is None:
            return self._result

        if self._verbose:
            self._chef.context.logger.info(f'| Started executing {self._target.key}')
        self._result = self.define()
        self._release_chef()
        return self._result  # type: ignore

    @abstractmethod
    def define(self):
        ...


class BlockFromTimestampPlan(Plan):
    def define(self) -> int:
        method = 'block_number.from_timestamp'
        timestamp = self._data['timestamp']

        recipe = Recipe(cache_key=f'{method}.{timestamp}',
                        target_key=self._target.key,
                        method=method,
                        input={'timestamp': timestamp})
        result = self.chef.cook(recipe)
        return result


class HistoricalBlockPlan(Plan):
    def post_proc(self, _context, data):
        blocks = data.dict()
        df_blocks = (pd.DataFrame(blocks['series'])
                     .drop(columns=['output'])
                     .sort_values(['blockNumber'], ascending=False)
                     .reset_index(drop=True))

        df_blocks.loc[:, 'blockTime'] = df_blocks.blockTimestamp.apply(
            lambda x: datetime.fromtimestamp(x, timezone.utc))
        df_blocks.loc[:, 'sampleTime'] = df_blocks.sampleTimestamp.apply(
            lambda x: datetime.fromtimestamp(x, timezone.utc))

        block_numbers = df_blocks.blockNumber.to_list()
        return {'block_numbers': block_numbers,
                'block_table': df_blocks}

    def define(self) -> dict:
        method = 'run_model_historical'
        slug = 'example.echo'
        as_of = self._data['as_of']
        window = self._data['window']
        interval = self._data['interval']

        if validate_as_of(as_of):
            as_of_timestamp = as_of.timestamp()
        elif isinstance(as_of, date) and self._tag == 'eod':
            dt_from_date = datetime.combine(as_of, datetime.max.time(), tzinfo=timezone.utc)
            as_of_timestamp = int(dt_from_date.timestamp())
        else:
            raise ModelRunError(f'! Unsupported {as_of=}')

        tgt_key = f'BlockFromTimestamp.{self._tag}.{as_of_timestamp}'
        target = MarketTarget(key=tgt_key, artifact=None)
        block_plan = BlockFromTimestampPlan(self._tag,
                                            target,
                                            slug='BlockFromTimestampPlan',
                                            context=self.chef.context,
                                            verbose=self._verbose,
                                            timestamp=as_of_timestamp)
        __as_of_block = block_plan.execute()

        recipe = Recipe(cache_key=f'{method}.{slug}.{window}.{interval}.{as_of_timestamp}',
                        target_key=self._target.key,
                        method=method,
                        input={'model_input': '',
                               'model_slug': slug,
                               'window': window,
                               'interval': interval,
                               'end_timestamp': as_of_timestamp},
                        post_proc=self.post_proc,
                        return_type=self._return_type
                        )

        result = self.chef.cook(recipe)
        return result


class EODPlan(Plan):
    def define(self) -> dict:
        if self._tag == 'eod':
            as_of = self._data['as_of']
            window = '1 day'
            interval = '1 day'
        elif self._tag == 'eod_var_scenario':
            window = self._data['window']
            as_of = self._data['as_of']
            interval = self._data['interval']
        else:
            raise ModelRunError(f'! Unknown {self._tag=}')

        tgt_key = f'HistoricalBlock.{self._tag}.{as_of}.{window}.{interval}'
        target = MarketTarget(key=tgt_key, artifact=None)
        pre_plan = HistoricalBlockPlan(self._tag,
                                       target,
                                       slug='HistoricalBlockPlan',
                                       context=self.chef.context,
                                       verbose=self._verbose,
                                       as_of=as_of,
                                       window=window,
                                       interval=interval)

        pre_plan_results = pre_plan.execute()

        block_numbers = pre_plan_results['block_numbers']  # type: ignore
        block_table = pre_plan_results['block_table']  # type: ignore

        dish = block_table.copy()
        for block_number in block_numbers:
            if isinstance(self._target.artifact, Token):
                method = 'run_model'
            else:
                raise ModelRunError(f'! Unsupported artifact {self._target.artifact=}')

            # other choices for slug:
            # - 'token.price-ext',
            # - 'uniswap-v3.get-average-price',
            # - 'token.price',
            slug = 'token.price-ext'
            rec = Recipe(cache_key=f'{method}.{slug}.{self._target.key}.{block_number}',
                         target_key=self._target.key,
                         method=method,
                         input={'slug': slug,
                                'input': self._target.artifact,
                                'block_number': block_number},
                         )

            rec_result = self.chef.cook(rec)
            for k, v in rec_result.items():  # type: ignore
                dish.loc[dish.blockNumber == rec.input['block_number'],
                         f'{rec.target_key}.{k}'] = v

        if self._tag == 'eod':
            return {'raw': dish,
                    'extracted': dish[f'{self._target.key}.price'][0]}

        elif self._tag == 'eod_var_scenario':
            price_series = dish[f'{self._target.key}.price']
            rolling_interval = self._data['rolling_interval']
            if rolling_interval is not None:
                val_leading = price_series[:-rolling_interval].to_numpy()
                val_lagging = price_series[rolling_interval:].to_numpy()
                ret_series = val_leading / val_lagging
            else:
                raise ModelRunError('! rolling_interval undefined for VaR scenario generation.')
            return {'raw': dish,
                    'extracted': ret_series}

        raise ModelRunError(f'! Unknown {self._tag=}')


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
    def value(self, new_as_of, mkt, mkt_adj=lambda x: x) -> float:
        pass

    @ abstractmethod
    def value_scenarios(self, new_as_of, mkt, mkt_scenarios) -> pd.Series:
        pass


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

    def value(self, new_as_of, mkt, mkt_adj=lambda x: x) -> float:
        """
        TokenTrade's value does not change with the new_as_of to the Tradeable's own as_of
        Other type of trade could have time value.
        """

        # DEPRECATED code of retriving price
        # idx_last = mkt_piece.index.get_loc(
        #   mkt_piece.index[mkt_piece['blockTime'] <= new_as_of][0])
        # curent_price = mkt_piece[f'{self.key}.price'].iloc[idx_last]

        curent_price = mkt_adj(mkt[self.key]['extracted'])
        pnl = curent_price - self._init_price
        pnl *= self._amount
        return pnl

    def value_scenarios(self, new_as_of, mkt, mkt_scenarios) -> pd.Series:
        base_pnl = self.value(new_as_of, mkt)
        scen_pnl = []
        scenarios = mkt_scenarios[self.key]['extracted']
        for scen in scenarios:
            new_pnl = self.value(new_as_of, mkt, lambda x, scen=scen: x * scen)
            scen_pnl.append(new_pnl)
        return pd.Series(scen_pnl) - base_pnl


class ContractTradeable(Tradeable):
    def __init__(self, as_of, tid):
        super().__init__(as_of, tid)

    def requires(self) -> Generator[MarketTarget, None, None]:
        yield from []

    def value(self, new_as_of, mkt, mkt_adj=lambda x: x) -> float:
        return 0

    def value_scenarios(self, new_as_of, mkt, mkt_scenarios) -> pd.Series:
        return pd.Series([0 for _ in mkt_scenarios])


# PortfolioManage shall request to Market to build the market information


class Market(dict):
    pass

# TODO: to be merged with framework's Portfolio


class PortfolioManager:
    def __init__(self,
                 trades: List[Tradeable],
                 as_of,
                 slug,
                 reset_cache,
                 context=None,
                 chef=None,
                 verbose=False):
        self._trades = trades
        self._as_of = as_of
        self._verbose = verbose
        if context is None and chef is not None:
            self._chef = chef
        elif context is not None and chef is None:
            self._chef = Chef(context, slug, reset_cache=reset_cache, verbose=verbose)
        else:
            raise ModelRunError(f'! Missing either context or chef to '
                                f'initialize a {self.__class__.__name__}')

    @ classmethod
    def from_portfolio(cls,
                       as_of,
                       portfolio: Portfolio,
                       context,
                       slug,
                       reset_cache=False,
                       verbose=False):
        trades = []
        for (pos_n, pos) in enumerate(portfolio.positions):
            if not pos.asset.address:
                raise ModelRunError(f'! Input position is invalid, {input}')

            tid = f'{pos_n}.{pos.asset.address}'
            t = TokenTradeable(tid, [], as_of, pos.asset, pos.amount, init_price=0)
            trades.append(t)
        return cls(trades, as_of, slug, reset_cache=reset_cache, context=context, verbose=verbose)

    def requires(self) -> Generator[Tuple[str, MarketTarget], None, None]:
        key_set = set()
        for t in self._trades:
            for req in t.requires():
                if req.key not in key_set:
                    key_set.add(req.key)
                    yield req.key, req

    def prepare_market(self, tag, **data):
        mkt_target = dict(self.requires())
        if self._verbose:
            self._chef.context.logger.info(f'# Preparing market with {len(mkt_target)=} for {tag}')
        mkt = Market({key: EODPlan(tag,
                                   target,
                                   chef=self._chef,
                                   verbose=self._verbose,
                                   **data).execute()
                      for key, target in mkt_target.items()})
        if self._verbose:
            self._chef.context.logger.info(
                f'# Finished preparing for market with {len(mkt_target)=} for {tag}')
        return mkt

    def value(self, mkt: Market, as_df=True, **data):
        values = []
        new_as_of = data.get('as_of', self._as_of)

        for t in self._trades:
            v = t.value(new_as_of, mkt)
            values.append((t.tid, v))
        df_res = pd.DataFrame(values, columns=['TRADE_ID', 'VALUE'])
        if as_df:
            return df_res
        return df_res.loc[:, ['TRADE_ID', 'VALUE']].to_dict()

    def value_scenarios(self, mkt: Market, mkt_scenarios: Market, as_df=True, **data):
        values = []
        new_as_of = data.get('as_of', self._as_of)

        for t in self._trades:
            v = t.value_scenarios(new_as_of, mkt, mkt_scenarios)
            values.extend(zip(itertools.count(1), itertools.repeat(t.tid), v))
        df_res = (pd.DataFrame(values, columns=['SCEN_ID', 'TRADE_ID', 'VALUE'])
                  .sort_values(['SCEN_ID', 'TRADE_ID'])
                  .reset_index(drop=True))
        if as_df:
            return df_res
        return df_res.to_dict(orient='index')
