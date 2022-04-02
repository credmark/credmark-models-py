from abc import abstractmethod
import pickle
import os
from credmark.model import (
    ModelRunError,
)

from credmark.types import (
    Portfolio,
    Token,
    BlockSeries,
    BlockNumber,
    Price,
)

from credmark.dto import (
    DTO,
    GenericDTO,
)

import pandas as pd
import itertools
import json
from typing import (
    Callable,
    List,
    Any,
    Generator,
    Type,
    TypeVar,
    Generic,
    Optional,
    Dict,
    Tuple,
)
from datetime import (
    date,
    datetime,
    timezone,
)


class Singleton:
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance


class MarketTarget(DTO):
    key: str  # ensure unique in market oject
    artifact: Any


# pylint:disable=locally-disabled,too-many-instance-attributes


class PydanticJSONEncoder(json.JSONEncoder):
    """
    A JSON encoder that will handle DTO types embedded
    in other data structures such as dicts or lists.

    Use it as the cls passed to json dump(s):
      json.dump(result, cls=PydanticJSONEncoder)
    """

    def default(self, o):
        if isinstance(o, DTO):
            return o.dict()
        return json.JSONEncoder.default(self, o)


P = TypeVar('P')  # Plan return type
C = TypeVar('C')  # Chef return type


class Recipe(GenericDTO, Generic[C, P]):
    cache_keywords: List[Any]  # Unique keywords in Plan's Cache
    target_key: str  # Unique key in Market
    method: str
    input: dict
    post_proc: Callable[[Any, C], P]
    chef_return_type: Type[C]
    plan_return_type: Type[P]


class Chef(Generic[C, P]):
    __SEP__ = '|#|'
    __RETRY__ = 3
    __CACHE_UNSAVE_LIMIT__ = 1000  # entries before cache is saved
    __CACHE_UNSAVE_TIME__ = 100  # seconds before cache is saved

    def __init__(self,
                 context,
                 name,
                 reset_cache=False,
                 use_cache=True,
                 verbose=False):
        if name is None or name == '':
            raise ModelRunError('! Chef needs to be initialized with a non-empty name.')
        self._cache_file = os.path.join('tmp', f'chef_cache_chain_id_{context.chain_id}_{name}.pkl')
        self._cache = {}
        self._cache_hit = 0
        self._total_hit = 0
        self._context = context
        self._use_cache = use_cache
        self._cache_unsaved = 0
        self._cache_last_saved = datetime.now().timestamp()
        self._reset_cache = reset_cache
        self._verbose = verbose

        if self._verbose:
            if self._reset_cache:
                self._context.logger.info(
                    f'+- Call Chef({hex(id(self))}) on {self._cache_file} '
                    f'in reset mode overwriting existing')
            else:
                self._context.logger.info(
                    f'+- Call Chef({hex(id(self))}) on {self._cache_file}')
        if self._use_cache:
            self._load_cache()

    def __del__(self):
        if self._verbose:
            self.cache_status()
        self.save_cache()
        if self._verbose:
            self._context.logger.info(f'+- Free Chef({hex(id(self))}) on {self._cache_file}')

    def _load_cache(self):
        try:
            if os.path.isfile(self._cache_file):
                with open(self._cache_file, 'rb') as handle:
                    self._cache = pickle.load(handle)
                    self._cache_unsaved = 0
                    self._cache_last_saved = datetime.now().timestamp()
                    self.cache_info(' Opened')
        except EOFError:
            self._context.logger.warning(
                f'* Cache from {self._cache_file} is corrupted. Reset.')
            self.save_cache()

    def save_cache(self):
        if self._use_cache:
            if self._cache_unsaved > 0:
                cache_dir = os.path.dirname(self._cache_file)
                if not os.path.isdir(cache_dir):
                    os.mkdir(cache_dir)
                with open(self._cache_file, 'wb') as handle:
                    if '__log__' in self._cache:
                        self._cache['__log__'].append(datetime.now())
                    else:
                        self._cache['__log__'] = [datetime.now()]
                    pickle.dump(self._cache, handle, protocol=pickle.HIGHEST_PROTOCOL)
                    self._cache_unsaved = 0
                    self._cache_last_saved = datetime.now().timestamp()
                    self.cache_info(' Closed')

    def cache_info(self, message=''):
        if self._verbose:
            cache_log = self._cache.get('__log__', [datetime.now()])
            cache_log_info = (f'[{min(cache_log):%Y-%m-%d %H:%M:%S}] to '
                              f'[{max(cache_log):%Y-%m-%d %H:%M:%S}] '
                              f'for saved {len(cache_log)} times '
                              f'with {len(self._cache)} entries.')
            self._context.logger.info(f'* Cache from {self._cache_file} '
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

    def create_cache_key(self, words):
        cache_key = self.__SEP__.join([str(w) for w in words])
        return cache_key

    def get_cache_entry(self, chain_id, cache_key, rec) -> dict[str, Any]:
        method = rec.method
        if chain_id not in self._cache:
            self._cache[chain_id] = {}
        if method not in self._cache[chain_id]:
            self._cache[chain_id][method] = {}
        if cache_key not in self._cache[chain_id][method]:
            self._cache[chain_id][method][cache_key] = {}
        return self._cache[chain_id][method][cache_key]

    def find_cache_entry(self, chain_id, cache_key, rec):
        method = rec.method
        input = rec.input
        if chain_id not in self._cache:
            return False, None

        if method not in self._cache[chain_id]:
            return False, None

        if cache_key not in self._cache[chain_id][method]:
            return False, None

        cache_entry = self._cache[chain_id][method][cache_key]
        if cache_entry['method'] == method:
            if cache_entry['chain_id'] == chain_id:
                if cache_entry['input'] == json.dumps(input, cls=PydanticJSONEncoder):
                    return True, cache_entry['untyped']

        return False, None

    def verify_input_and_key(self, input_key, rec):
        return (input_key in rec.input and rec.input[input_key] is not None and
                rec.input[input_key] in rec.cache_keywords)

    def cache_status(self):
        if self.total_hit != 0:
            self._context.logger.info(
                f'* Cache hit {self.cache_hit} for {self.total_hit} requests '
                f'rate={self.cache_hit/self.total_hit*100:.1f}%')

    def perform(self, rec: Recipe[C, P]) -> C:
        try:
            if rec.method == 'block_number.from_timestamp':
                assert self.verify_input_and_key('timestamp', rec)
                result = self._context.block_number.from_timestamp(**rec.input)
                return result

            elif rec.method == 'run_model':
                assert self.verify_input_and_key('block_number', rec)
                result = self._context.run_model(**rec.input,
                                                 return_type=rec.chef_return_type)
                return result
            elif rec.method == 'run_model_historical':
                # cond1: snap_clock and timestamp
                # cond2: snap_clock and end_timestamp
                # cond3: end_timestamp
                # cond4: no end_stampstamp given, but end_timestamp needs to be given.
                cond1 = self.verify_input_and_key('snap_clock', rec) and\
                    self.context.block_number.timestamp in rec.cache_keywords
                cond2 = self.verify_input_and_key('end_timestamp', rec) and\
                    self.verify_input_and_key('end_timestamp', rec)
                cond3 = self.verify_input_and_key('end_timestamp', rec)
                cond4 = self.context.block_number.timestamp in rec.cache_keywords
                assert cond1 | cond2 | cond3 | cond4
                result = self._context.historical.run_model_historical(
                    **rec.input,
                    model_return_type=rec.chef_return_type)
                return result
            else:
                raise ModelRunError(f'! Unknown {rec.method=}')
        except AssertionError:
            raise ModelRunError(
                f'cache_key may not be unique for {rec.method=} with {rec.input=} '
                f'in {rec.cache_keywords=}')

    def cook(self, rec: Recipe[C, P]) -> P:
        result = None
        cache_key = self.create_cache_key(rec.cache_keywords)

        if self._use_cache and not self._reset_cache:
            cache_find_status, cache_result = self.find_cache_entry(
                int(self._context.chain_id), cache_key, rec)

            if cache_find_status and cache_result is not None:
                if self._verbose:
                    self.context.logger.info(f'< Chef({hex(id(self))}) grabs < {cache_key}')
                self._cache_hit += 1
                self._total_hit += 1

                if issubclass(rec.plan_return_type, DTO) and isinstance(cache_result, str):
                    return rec.plan_return_type(**json.loads(cache_result))
                elif isinstance(cache_result, rec.plan_return_type):
                    return cache_result
                else:
                    return cache_result

        if self._verbose:
            self.context.logger.info(f'> Chef({hex(id(self))}) cooks > {cache_key}')

        retry_c = 0
        result = None
        while retry_c < self.__RETRY__:
            try:
                result = self.perform(rec)
                break
            except Exception as err:
                if retry_c == self.__RETRY__ - 1:
                    raise
                self.context.logger.error(
                    f'Met exception with .perform() {err=}. '
                    f'Re-trying {retry_c+1} of {self.__RETRY__}.')
                retry_c += 1

        if result is not None:
            post_result = rec.post_proc(self._context, result)

            if isinstance(post_result, DTO) and issubclass(rec.chef_return_type, DTO):
                untyped_post_result = post_result.json()
            else:
                untyped_post_result = post_result

            if self._use_cache:
                cache_entry = self.get_cache_entry(int(self._context.chain_id), cache_key, rec)
                cache_entry['untyped'] = untyped_post_result
                cache_entry['method'] = rec.method
                cache_entry['input'] = json.dumps(rec.input, cls=PydanticJSONEncoder)
                cache_entry['chain_id'] = int(self._context.chain_id)

                # Leave this in the end so wrong data doesn't not corrupt cache
                self._cache_unsaved += 1

                if (self._cache_unsaved >= self.__CACHE_UNSAVE_LIMIT__ or
                        datetime.now().timestamp() >=
                        self._cache_last_saved + self.__CACHE_UNSAVE_TIME__):
                    self.save_cache()

            self._total_hit += 1

            return post_result

        raise ModelRunError('Result is None')


class Kitchen(Singleton):
    _pool: Dict[Tuple[Any, str, bool, bool, bool], Chef] = {}

    def get(self, context, name, reset_cache, use_cache, verbose):
        key = (context, name, reset_cache, use_cache, verbose)
        if key not in self._pool:
            self._pool[key] = Chef(context,
                                   name,
                                   reset_cache=reset_cache,
                                   use_cache=use_cache,
                                   verbose=verbose)
        return self._pool[key]

    def save_cache(self):
        """
        Call during catch an error.
        """
        for chef in self._pool.values():
            chef.save_cache()

    def __del__(self):
        for chef in self._pool.values():
            del chef


def validate_as_of(as_of):
    return isinstance(as_of, datetime) and as_of.tzinfo is not None

# pylint:disable=locally-disabled,too-many-arguments


class Plan(Generic[C, P]):
    _chef_return_type: Type[C]
    _plan_return_type: Type[P]

    def check_kwargs(self, **kwargs):
        assert 'chef_return_type' not in kwargs and 'plan_return_type' not in kwargs

    def __init__(self,
                 tag,
                 target_key: str,
                 plan_return_type: Type[P],
                 chef_return_type: Type[C],
                 name: Optional[str] = None,
                 chef=None,
                 context=None,
                 use_kitchen: bool = True,
                 reset_cache: bool = False,
                 use_cache: bool = True,
                 verbose: bool = False,
                 **input_to_plan):
        self._chef = None
        self._chef_internal = None
        self._result = None

        self._tag = tag
        self._target_key = target_key
        self._input_to_plan = input_to_plan
        self._use_kitchen = use_kitchen
        self._verbose = verbose
        self._name = name if name is not None else self.__class__.__name__

        if plan_return_type is None:
            raise ModelRunError('! Missing return_type to initialize Plan')
        if chef_return_type is None:
            raise ModelRunError('! Missing chef_return_type to initialize Plan')

        self._plan_return_type = plan_return_type
        self._chef_return_type = chef_return_type
        self._acquire_chef(chef, context, name=self._name, reset_cache=reset_cache,
                           use_cache=use_cache, verbose=verbose)

    @property
    def chef(self):
        if self._chef is not None:
            return self._chef
        else:
            raise ModelRunError('! Chef is not around')

    def __del__(self):
        # when initialization is not complete, chef may not be ready
        self._release_chef()

    def _acquire_chef(self, chef, context, name, reset_cache, use_cache, verbose):
        if context is None and chef is not None:
            self._chef = chef
            self._chef_internal = False
        elif context is not None and chef is None:
            if self._use_kitchen:
                self._chef = Kitchen().get(context,
                                           name,
                                           reset_cache=reset_cache,
                                           use_cache=use_cache,
                                           verbose=verbose)
                self._chef_internal = False
            else:
                self._chef = Chef(context,
                                  name,
                                  reset_cache=reset_cache,
                                  use_cache=use_cache,
                                  verbose=verbose)
                self._chef_internal = True
        else:
            raise ModelRunError(f'! Missing either context or chef to '
                                f'execute a {self.__class__.__name__}')

    def _release_chef(self):
        if self._chef is not None:
            if self._verbose:
                self._chef.context.logger.info(f'| Finished executing {self._target_key}')
                self._chef.cache_status()
            if self._chef_internal:
                del self._chef
            self._chef = None

    def post_proc(self, _context, output_from_chef: C) -> P:
        return self._plan_return_type(output_from_chef)

    def create_recipe(self, cache_keywords, method, input):
        recipe = Recipe(cache_keywords=cache_keywords,
                        target_key=self._target_key,
                        method=method,
                        input=input,
                        post_proc=self.post_proc,
                        chef_return_type=self._chef_return_type,
                        plan_return_type=self._plan_return_type)
        return recipe

    def execute(self) -> P:
        if self._chef is None:
            if self._result is not None:
                return self._result
            else:
                raise ValueError

        if self._verbose:
            self._chef.context.logger.info(f'| Started executing {self._target_key}')

        try:
            self._result = self.define()
        except Exception:
            self._chef.context.logger.error(
                f'Exception during executing {self._target_key}. Force releasing Chef.')
            if self._use_kitchen:
                Kitchen().save_cache()
            else:
                self._chef.save_cache()
            raise
        else:
            return self._result
        finally:
            self._release_chef()

    @ abstractmethod
    def define(self) -> P:
        ...


class BlockFromTimePlan(Plan[BlockNumber, dict]):
    def __init__(self, *args, **kwargs):
        self.check_kwargs(**kwargs)
        super().__init__(*args, **kwargs, chef_return_type=BlockNumber, plan_return_type=dict)

    def post_proc(self, _context, output_from_chef: BlockNumber) -> dict:
        eod_block = int(output_from_chef)
        result = {'block_number': int(eod_block),
                  'timestamp': self._input_to_plan['eod_time_stamp'],
                  }
        return result

    def define(self) -> dict:
        # Original method
        # dt_eod = datetime.combine(dt_input, datetime.max.time(), tzinfo=timezone.utc)
        # eod_time_stamp = int(dt_eod.timestamp())
        # eod_block = self.context.block_number.from_timestamp(eod_time_stamp)
        # return {'block': eod_block,
        #         'timestamp': eod_time_stamp, }

        method = 'block_number.from_timestamp'

        dt_input = self._input_to_plan.get('date', None)
        dtt_input = self._input_to_plan.get('datetime', None)
        timestamp = self._input_to_plan.get('timestamp', None)
        if dt_input is not None and isinstance(dt_input, date):
            dt_eod = datetime.combine(dt_input, datetime.max.time(), tzinfo=timezone.utc)
            eod_time_stamp = int(dt_eod.timestamp())
        elif dtt_input is not None and isinstance(dt_input, datetime):
            dt_eod = datetime.replace(dtt_input, tzinfo=timezone.utc)
            eod_time_stamp = int(dt_eod.timestamp())
        elif timestamp is not None and isinstance(timestamp, (int, float)):
            eod_time_stamp = int(timestamp)
        else:
            raise ModelRunError(
                f'Missing either date or timestamp in input for {self.__class__.__name__} '
                f'{self._input_to_plan=}')

        self._input_to_plan['eod_time_stamp'] = eod_time_stamp

        recipe = self.create_recipe(
            cache_keywords=[method, eod_time_stamp],
            method=method,
            input={'timestamp': eod_time_stamp})
        result = self.chef.cook(recipe)
        return result


class HistoricalBlockPlan(Plan[BlockSeries[dict], dict]):
    def __init__(self, *args, **kwargs):
        self.check_kwargs(**kwargs)
        super().__init__(*args,
                         **kwargs,
                         chef_return_type=BlockSeries[dict],
                         plan_return_type=dict)

    def post_proc(self, _context, output_from_chef: BlockSeries[dict]) -> dict:
        blocks = output_from_chef.dict()
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
        model_slug = 'finance.get-one'
        as_of = self._input_to_plan['as_of']
        window = self._input_to_plan['window']
        interval = self._input_to_plan['interval']

        if validate_as_of(as_of):
            as_of_timestamp = as_of.timestamp()
        elif isinstance(as_of, date) and self._tag == 'eod':
            dt_from_date = datetime.combine(as_of, datetime.max.time(), tzinfo=timezone.utc)
            as_of_timestamp = int(dt_from_date.timestamp())
        else:
            raise ModelRunError(f'! Unsupported {as_of=}')

        block_plan = BlockFromTimePlan(self._tag,
                                       f'BlockFromTimestamp.{self._tag}.{as_of_timestamp}',
                                       context=self.chef.context,
                                       verbose=self._verbose,
                                       timestamp=as_of_timestamp)
        __as_of_block = block_plan.execute()['block_number']

        recipe = self.create_recipe(
            cache_keywords=[method, model_slug, window, interval, as_of_timestamp],
            method=method,
            input={'model_slug': model_slug,
                   'window': window,
                   'interval': interval,
                   'end_timestamp': as_of_timestamp})

        result = self.chef.cook(recipe)
        return result


class TokenEODPlan(Plan[Price, dict]):
    def __init__(self, *args, **kwargs):
        self.check_kwargs(**kwargs)
        super().__init__(*args,
                         **kwargs,
                         chef_return_type=Price,
                         plan_return_type=dict)

    def define(self) -> dict:
        if self._tag == 'eod':
            as_of = self._input_to_plan['as_of']
            window = '1 day'
            interval = '1 day'
        elif self._tag == 'eod_var_scenario':
            window = self._input_to_plan['window']
            as_of = self._input_to_plan['as_of']
            interval = self._input_to_plan['interval']
        else:
            raise ModelRunError(f'! Unknown {self._tag=}')

        input_token = self._input_to_plan['input_token']
        if isinstance(input_token, Token):
            method = 'run_model'
        else:
            raise ModelRunError(f'! Unsupported artifact {input_token=}')
        model_slug = 'token.price-ext'

        block_plan = HistoricalBlockPlan(self._tag,
                                         f'HistoricalBlock.{self._tag}.{as_of}.{window}.{interval}',
                                         context=self.chef.context,
                                         verbose=self._verbose,
                                         as_of=as_of,
                                         window=window,
                                         interval=interval)

        pre_plan_results = block_plan.execute()

        block_numbers = pre_plan_results['block_numbers']
        block_table = pre_plan_results['block_table']

        # Sort block from early to recent
        # So we could
        # 1) fail earlier when there was no data available, and
        # 2) saving time of retrive contract.meta data once at the early block

        dish = block_table.copy()
        for block_number in sorted(block_numbers):
            # other choices for slug:
            # - 'token.price-ext',
            # - 'uniswap-v3.get-average-price',
            # - 'token.price',
            rec = self.create_recipe(
                cache_keywords=[method, model_slug, self._target_key, block_number],
                method=method,
                input={'slug': model_slug,
                       'input': input_token,
                       'block_number': block_number})

            rec_result = self.chef.cook(rec)

            for k, v in rec_result.items():
                dish.loc[dish.blockNumber == rec.input['block_number'],
                         f'{rec.target_key}.{k}'] = v

        if self._tag == 'eod':
            return {'raw': dish,
                    'extracted': dish[f'{self._target_key}.price'][0]}

        elif self._tag == 'eod_var_scenario':
            price_series = dish[f'{self._target_key}.price']
            rolling_interval = self._input_to_plan['rolling_interval']
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

        # DEPRECATED Code of retriving price
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
                 context,
                 use_kitchen,
                 reset_cache,
                 verbose,
                 use_cache):
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
        if self._chef is not None and not self._use_kitchen:
            del self._chef

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
            self._context.logger.info(f'# Preparing market with {len(mkt_target)=} for {tag}')

        mkt = Market()

        if not self._use_kitchen:
            context_or_chef = {'chef': self._chef}
        else:
            context_or_chef = {'context': self._context}

        for target in mkt_target:
            pl = TokenEODPlan(tag,
                              target.key,
                              **context_or_chef,
                              use_kitchen=self._use_kitchen,
                              reset_cache=self._reset_cache,
                              verbose=self._verbose,
                              input_token=target.artifact,
                              **input_to_plan)
            mkt[target.key] = pl.execute()

        if self._verbose:
            self._context.logger.info(
                f'# Finished preparing for market with {len(mkt_target)=} for {tag}')

        return mkt

    def value(self, mkt: Market, as_df=True, **input_to_value):
        values = []
        new_as_of = input_to_value.get('as_of', self._as_of)

        for t in self._trades:
            v = t.value(new_as_of, mkt)
            values.append((t.tid, v))
        df_res = pd.DataFrame(values, columns=['TRADE_ID', 'VALUE'])
        if as_df:
            return df_res
        return df_res.loc[:, ['TRADE_ID', 'VALUE']].to_dict()

    def value_scenarios(self, mkt: Market, mkt_scenarios: Market, as_df=True, **input_to_value):
        values = []
        new_as_of = input_to_value.get('as_of', self._as_of)

        for t in self._trades:
            v = t.value_scenarios(new_as_of, mkt, mkt_scenarios)
            values.extend(zip(itertools.count(1), itertools.repeat(t.tid), v))
        df_res = (pd.DataFrame(values, columns=['SCEN_ID', 'TRADE_ID', 'VALUE'])
                  .sort_values(['SCEN_ID', 'TRADE_ID'])
                  .reset_index(drop=True))
        if as_df:
            return df_res
        return df_res.to_dict(orient='index')
