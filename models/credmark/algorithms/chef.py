import pickle
import hashlib
import os
from credmark.cmf.model.errors import (
    ModelRunError,
    ModelDataError,
)

from credmark.dto import (
    DTO,
)

import json
import copy

from typing import (
    Any,
    Generic,
    Optional,
    Dict,
    Tuple,
    Union,
    List,
    get_type_hints,
)
from datetime import (
    datetime,

)

from models.credmark.algorithms.recipe import (
    Recipe,
    RiskObject,
    PlanT,
    ChefT,
)


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


class Chef(Generic[ChefT, PlanT], RiskObject):  # pylint:disable=too-many-instance-attributes
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
                    f'/- Call {self.name_id}) on {self._cache_file} '
                    f'in reset mode overwriting existing')
            else:
                self._context.logger.info(
                    f'/- Call {self.name_id} on {self._cache_file}')
        if self._reset_cache:
            self._cache_unsaved = 1
            self.save_cache()
        if self._use_cache:
            self._load_cache()

    def __del__(self):
        if self._verbose:
            self.cache_status()
        self.save_cache()
        if self._verbose:
            self._context.logger.info(f'\\- Free {self.name_id} on {self._cache_file}')

    def _load_cache(self):
        try:
            if os.path.isfile(self._cache_file):
                with open(self._cache_file, 'rb') as handle:
                    self._cache = pickle.load(handle)
                    self._cache_unsaved = 0
                    self._cache_last_saved = datetime.now().timestamp()
                    self.cache_info('loaded')
        except EOFError:
            self._context.logger.warning(
                f'* {self.name_id} cache from {self._cache_file} is corrupted. Reset.')
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
                    if '__count__' in self._cache:
                        self._cache['__count__'] += self._cache_unsaved
                    else:
                        self._cache['__count__'] = self._cache_unsaved

                    pickle.dump(self._cache, handle, protocol=pickle.HIGHEST_PROTOCOL)
                    self._cache_unsaved = 0
                    self._cache_last_saved = datetime.now().timestamp()
                    self.cache_info('saved')

    def cache_info(self, message=''):
        if self._verbose:
            cache_log = self._cache.get('__log__', [datetime.now()])
            cache_count = self._cache.get('__count__', 0)
            cache_log_info = (f'[{min(cache_log):%Y-%m-%d %H:%M:%S}] to '
                              f'[{max(cache_log):%Y-%m-%d %H:%M:%S}] '
                              f'for saved {len(cache_log)} times '
                              f'with {cache_count} entries.')
            self._context.logger.info(f'* {self.name_id} {message} cache from '
                                      f'{self._cache_file} with {cache_log_info}')

    @ property
    def context(self):
        return self._context

    @ property
    def cache_hit(self):
        return self._cache_hit

    @ property
    def total_hit(self):
        return self._total_hit

    def create_cache_key(self, words: List[Any]) -> str:
        cache_key = self.__SEP__.join([str(w) for w in words])
        return cache_key

    def get_cache_entry(self,
                        chain_id: int,
                        cache_key: str,
                        rec: Recipe[ChefT, PlanT]) -> dict[str, Any]:
        method = rec.method
        if chain_id not in self._cache:
            self._cache[chain_id] = {}
        if method not in self._cache[chain_id]:
            self._cache[chain_id][method] = {}
        cache_key_hash = hashlib.sha3_512(cache_key.encode('utf-8')).hexdigest()
        if cache_key_hash not in self._cache[chain_id][method]:
            self._cache[chain_id][method][cache_key_hash] = {}
        return self._cache[chain_id][method][cache_key_hash]

    def find_cache_entry(self,
                         chain_id: int,
                         cache_key: str,
                         rec: Recipe[ChefT, PlanT]) -> Tuple[bool, Optional[Any]]:
        method = rec.method
        input = rec.input
        if chain_id not in self._cache:
            return False, None

        if method not in self._cache[chain_id]:
            return False, None

        cache_key_hash = hashlib.sha3_512(cache_key.encode('utf-8')).hexdigest()
        if cache_key_hash not in self._cache[chain_id][method]:
            return False, None

        cache_entry = self._cache[chain_id][method][cache_key_hash]
        if cache_entry['method'] == method:
            if cache_entry['chain_id'] == chain_id:
                if cache_entry['input'] == json.dumps(input, cls=PydanticJSONEncoder):
                    return True, cache_entry['untyped']

        if self._verbose:
            self.context.logger.info(f'{method=}: {cache_entry["method"]}')
            self.context.logger.info(f'{chain_id=}: {cache_entry["chain_id"]}')
            self.context.logger.info(f'{json.dumps(input, cls=PydanticJSONEncoder)}: '
                                     f'{cache_entry["input"]}')
            self.context.logger.warn(f'? {self.name_id} Chef tried to grab but '
                                     f'needs re-cook {cache_key}>')
        return False, None

    def verify_input_and_key(self, input_key, rec):
        if rec.cache_keywords[0] != rec.method:
            raise ModelRunError(
                f'First keyword {rec.cache_keywords=} needs to '
                f'be the method of Recipe {rec.method=}')

        return (input_key in rec.input and rec.input[input_key] is not None and
                rec.input[input_key] in rec.cache_keywords)

    def cache_status(self):
        if self.total_hit != 0:
            self._context.logger.info(
                f'* {self.name_id} cache hit {self.cache_hit} for {self.total_hit} requests '
                f'rate={self.cache_hit/self.total_hit*100:.1f}%')

    def perform(self,
                rec: Recipe[ChefT, PlanT],
                is_catch_runtime_error: bool) -> Tuple[str, Union[ChefT, PlanT]]:
        try:
            if rec.method == 'block_number.from_timestamp':
                assert self.verify_input_and_key('timestamp', rec)
                result = self._context.block_number.from_timestamp(**rec.input)
                return 'P', result

            elif rec.method == 'run_model':
                assert self.verify_input_and_key('block_number', rec)
                result = self._context.run_model(**rec.input,
                                                 return_type=rec.chef_return_type)
                return 'P', result
            elif rec.method == 'run_model[blocks]':
                if 'block_numbers' not in rec.input:
                    raise ModelRunError(f'Missing "block_numbers" in Recipe\'s '
                                        f'input for {rec.method=}')

                rec_input_copy = copy.copy(rec.input)
                block_numbers = rec_input_copy.pop('block_numbers')

                rec_cache_keywords = copy.copy(rec.cache_keywords)
                rec_cache_keywords[0] = 'run_model'
                if block_numbers not in rec_cache_keywords[-1]:
                    raise ModelDataError(
                        f'The last item of {rec.cache_keywords=} '
                        f'must contain the {block_numbers=}')
                del rec_cache_keywords[-1]

                type_hints = get_type_hints(rec.chef_return_type)
                sub_type = type_hints['data'].__args__[0].__args__[1]

                rec_copy = Recipe[sub_type, sub_type](
                    cache_keywords=rec_cache_keywords,
                    target_key=rec.target_key,
                    method='run_model',
                    input=rec_input_copy,
                    post_proc=lambda _context, output_from_chef: output_from_chef,
                    error_handle=rec.error_handle,
                    chef_return_type=sub_type,
                    plan_return_type=sub_type
                )

                sub_results = []
                for block_number in block_numbers:
                    rec_copy.cache_keywords = rec_cache_keywords + [block_number]
                    rec_copy.input['block_number'] = block_number
                    result = self.cook(rec_copy)
                    sub_results.append((block_number, result))
                return 'P', rec.chef_return_type(data=sub_results)

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

                # For run_model_historical, we ensure plan_return_type is used in the BlockSeries[]
                result = self._context.historical.run_model_historical(
                    **rec.input,
                    model_return_type=rec.plan_return_type)
                return 'P', result
            else:
                raise ModelRunError(f'! Unknown {rec.method=}')
        except AssertionError:
            raise ModelRunError(
                f'cache_key may not be unique for {rec.method=} with {rec.input=} '
                f'in {rec.cache_keywords=}')
        except (ModelDataError, ModelRunError) as err:
            if is_catch_runtime_error:
                status_code, result = rec.error_handle(self._context, err)

                if status_code == 'E':
                    raise err

                if status_code in ['S', 'C']:
                    return status_code, result

                raise ModelRunError(f'Unknown status code {status_code} while handling {err}')
            raise err

    def cook(self, rec: Recipe[ChefT, PlanT]) -> PlanT:
        result = None
        cache_key = self.create_cache_key(rec.cache_keywords)

        if self._use_cache and not self._reset_cache:
            cache_find_status, cache_result = self.find_cache_entry(
                int(self._context.chain_id), cache_key, rec)

            if cache_find_status and cache_result is not None:
                if self._verbose:
                    self.context.logger.info(f'< {self.name_id} grabs < {cache_key}')
                self._cache_hit += 1
                self._total_hit += 1

                if issubclass(rec.plan_return_type, DTO) and isinstance(cache_result, str):
                    return rec.plan_return_type(**json.loads(cache_result))
                elif isinstance(cache_result, rec.plan_return_type):
                    return cache_result
                else:
                    return cache_result

        if self._verbose:
            self.context.logger.info(f'> {self.name_id} cooks > {cache_key}')

        retry_c = 0
        result = None
        status_code = ''
        while retry_c < self.__RETRY__:
            try:
                # is_catch_runtime_error = retry_c == self.__RETRY__ - 1
                status_code, result = self.perform(rec, True)
                break
            except Exception as err:
                if retry_c == self.__RETRY__ - 1:
                    raise
                self.context.logger.error(
                    f'Met exception with .perform() {err=}. '
                    f'Re-trying {retry_c+2} of {self.__RETRY__}.')
                retry_c += 1

        if status_code == 'S' and isinstance(result, rec.plan_return_type):
            return result

        elif status_code in ['P', 'C'] and isinstance(result, rec.chef_return_type):
            if isinstance(result, rec.plan_return_type):
                post_result = result
            else:
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
        else:
            raise ModelRunError('Result is None')


class Singleton:
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance


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
        self.save_cache()
        for key, _value in self._pool.items():
            del self._pool[key]


kitchen = Kitchen()
