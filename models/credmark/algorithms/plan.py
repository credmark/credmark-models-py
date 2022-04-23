

from abc import abstractmethod
from credmark.cmf.model.errors import (
    ModelRunError,
)

from credmark.cmf.types import (
    Token,
    BlockNumber,
    Price,
)

from credmark.cmf.types.series import BlockSeries

import pandas as pd

from typing import (
    Type,
    Generic,
    Optional,
    Tuple,
)

from datetime import (
    date,
    datetime,
    timezone,
)

from models.credmark.algorithms.chef import (
    Chef,
    Kitchen,
    PlanT,
    ChefT,
)

from models.credmark.algorithms.recipe import (
    Recipe,
    validate_as_of,
    BlockData,
)


class Plan(Generic[ChefT, PlanT]):  # pylint:disable=too-many-instance-attributes
    def check_kwargs(self, **kwargs):
        assert 'chef_return_type' not in kwargs and 'plan_return_type' not in kwargs

    def __init__(self,  # pylint:disable=too-many-arguments
                 tag: str,
                 target_key: str,
                 use_kitchen: bool,
                 plan_return_type: Type[PlanT],
                 chef_return_type: Type[ChefT],
                 name: Optional[str] = None,
                 chef=None,
                 context=None,
                 reset_cache: bool = False,
                 use_cache: bool = True,
                 verbose: bool = False,
                 **input_to_plan):
        """
        Plan can be initialized with
        1) use_kitchen = True and context
        2) use_kitchen = False and context: create own chef
        3) use_kitchen = False and chef: use the chef
        """

        self._chef = None
        self._is_chef_internal = None
        self._result = None

        self._tag = tag
        self._target_key = target_key
        self._input_to_plan = input_to_plan

        self._name = name if name is not None else self.__class__.__name__
        self._chef_input = chef
        self._context = context
        self._reset_cache = reset_cache
        self._use_kitchen = use_kitchen
        self._use_cache = use_cache
        self._verbose = verbose

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
        self._release_chef()

    def _acquire_chef(self, chef, context, name, reset_cache, use_cache, verbose):
        if self._use_kitchen:
            self._chef = Kitchen().get(context,
                                       name,
                                       reset_cache=reset_cache,
                                       use_cache=use_cache,
                                       verbose=verbose)
            self._is_chef_internal = False
        else:
            if context is None and chef is not None:
                self._chef = chef
                self._is_chef_internal = False
            elif context is not None and chef is None:
                self._chef = Chef(context,
                                  name,
                                  reset_cache=reset_cache,
                                  use_cache=use_cache,
                                  verbose=verbose)
                self._is_chef_internal = True
            else:
                raise ModelRunError(f'! Missing either context or chef to '
                                    f'execute a {self.__class__.__name__}')

    def _release_chef(self):
        # When initialization is not complete, chef may not be ready.
        # in __init__(), set self._chef = None before potential initialization problems.
        if self._chef is not None:
            if self._verbose:
                self._chef.cache_status()
            self._chef = None

    def post_proc(self, _context, output_from_chef: ChefT) -> PlanT:
        raise ModelRunError(
            'Please add explicit post_proc to convert from '
            f'{self._chef_return_type} to {self._plan_return_type} '
            f'in class={self.__class__.__name__}')

    def error_handle(self, _context, err: Exception) -> Tuple[str, PlanT]:
        """
        status code to return
        1. E: trigger the error.
        2. S: Skip with plan result
        3. C: Continue with chef result (to be post-proc and cached)
        """
        raise err

    def create_recipe(self, cache_keywords, method, input):
        recipe = Recipe(cache_keywords=cache_keywords,
                        target_key=self._target_key,
                        method=method,
                        input=input,
                        post_proc=self.post_proc,
                        error_handle=self.error_handle,
                        chef_return_type=self._chef_return_type,
                        plan_return_type=self._plan_return_type)
        return recipe

    def execute(self) -> PlanT:
        if self._chef is None:
            if self._result is not None:
                return self._result
            else:
                raise ValueError

        try:
            if self._verbose:
                self._chef.context.logger.info(f'| Started executing {self._target_key}')
            self._result = self.define()
            if self._verbose:
                self._chef.context.logger.info(f'| Finished executing {self._target_key}')

        except Exception:
            self._chef.context.logger.error(
                f'! Exception during executing {self._target_key}. Force releasing Chef.')
            if self._use_kitchen:
                Kitchen().save_cache()
            else:
                self.chef.save_cache()
            raise
        else:
            return self._result
        finally:
            self._release_chef()

    @ abstractmethod
    def define(self) -> PlanT:
        ...


class GeneralHistoricalPlan(Plan[ChefT, PlanT]):
    def __init__(self, **kwargs):
        if 'name' not in kwargs:
            raise ModelRunError('GeneralHistoricalPlan needs to be initialized with name=')
        kwargs['name'] = f'{self.__class__.__name__}.{kwargs["name"]}'
        super().__init__(**kwargs)

    def define(self) -> PlanT:
        method = self._input_to_plan['method']
        slug = self._input_to_plan['slug']
        input = self._input_to_plan.get('input', {})
        block_number = self._input_to_plan['block_number']
        input_keys = self._input_to_plan['input_keys']

        recipe = self.create_recipe(
            cache_keywords=[method, slug, block_number] + input_keys,
            method=method,
            input={'slug': slug,
                   **({} if input == {} else {'input': input}),
                   'block_number': block_number})
        return self.chef.cook(recipe)


class BlockFromTimePlan(Plan[BlockNumber, dict]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs,
                         chef_return_type=BlockNumber,
                         plan_return_type=dict)

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
    def __init__(self, **kwargs):
        super().__init__(**kwargs,
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

        block_plan = BlockFromTimePlan(
            tag=self._tag,
            target_key=f'BlockFromTimestamp.{self._tag}.{as_of_timestamp}',
            use_kitchen=self._use_kitchen,
            chef=self._chef_input,
            context=self._context,
            reset_cache=self._reset_cache,
            use_cache=self._use_cache,
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


class TokenEODPlan(Plan[BlockData[Price], dict]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs,
                         name=f'{self.__class__.__name__}.{kwargs["target_key"]}',
                         chef_return_type=BlockData[Price],
                         plan_return_type=dict)

    def post_proc(self, _context, output_from_chef: BlockData[Price]) -> dict:
        block_table = self._input_to_plan['block_table']
        dish = block_table.copy()

        for (block_number, price_ret) in output_from_chef.data:
            for k, v in price_ret.dict().items():
                dish.loc[dish.blockNumber == block_number, f'{self._target_key}.{k}'] = v

        if self._tag == 'eod':
            return {'raw': dish,
                    'extracted': dish[f'{self._target_key}.price'][0]}

        elif self._tag == 'eod.var':
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

    def define(self) -> dict:
        if self._tag == 'eod':
            as_of = self._input_to_plan['as_of']
            window = '1 day'
            interval = '1 day'
            rolling_interval = 0
        elif self._tag == 'eod.var':
            as_of = self._input_to_plan['as_of']
            window = self._input_to_plan['window']
            interval = self._input_to_plan['interval']
            rolling_interval = self._input_to_plan['rolling_interval']
        else:
            raise ModelRunError(f'! Unknown {self._tag=}')

        block_plan = HistoricalBlockPlan(
            tag=self._tag,
            target_key=f'HistoricalBlock.{as_of}.{window}.{interval}',
            use_kitchen=self._use_kitchen,
            chef=self._chef_input,
            context=self._context,
            reset_cache=self._reset_cache,
            use_cache=self._use_cache,
            verbose=self._verbose,
            as_of=as_of,
            window=window,
            interval=interval)

        pre_plan_results = block_plan.execute()

        block_numbers = pre_plan_results['block_numbers']
        block_table = pre_plan_results['block_table']

        self._input_to_plan['block_table'] = block_table

        # Sort block from early to recent
        # So we could
        # 1) fail earlier when there was no data available, and
        # 2) saving time of retrive contract.meta data once at the early block

        input_token = self._input_to_plan['input_token']
        if isinstance(input_token, Token):
            method = 'run_model[blocks]'
        else:
            raise ModelRunError(f'! Unsupported artifact {input_token=}')
        model_slug = 'token.price-ext'

        # other choices for slug:
        # - 'token.price-ext',
        # - 'uniswap-v3.get-average-price',
        # - 'token.price',
        sorted_block_numbers = sorted(block_numbers)
        rec = self.create_recipe(
            cache_keywords=[method,
                            model_slug,
                            self._target_key,
                            [rolling_interval, sorted_block_numbers]],
            method=method,
            input={'slug': model_slug,
                   'input': input_token,
                   'block_numbers': sorted_block_numbers})

        rec_result = self.chef.cook(rec)
        return rec_result
