# pylint: disable=locally-disabled, invalid-name, line-too-long

from abc import abstractmethod
from datetime import datetime

import numpy as np
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import Address, Contract, Contracts, Maybe, Price, Records, Some, Token, Tokens
from credmark.cmf.types.block_number import BlockNumberOutOfRangeError
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO, EmptyInputSkipTest
from web3.exceptions import BadFunctionCallOutput, ContractLogicError

from models.credmark.price.dex import get_primary_token_tuples
from models.credmark.protocols.dexes.uniswap.constant import (
    V3_FACTORY_ADDRESS,
    V3_POOL_FEES,
)
from models.dtos.pool import DexPoolInput, PoolPriceInfo
from models.dtos.price import DexPoolPriceInput, DexPriceTokenInput, DexProtocol, DexProtocolInput
from models.tmp_abi_lookup import UNISWAP_V3_FACTORY_ABI, UNISWAP_V3_POOL_ABI

np.seterr(all='raise')


# - .get-factory
# - .get-pool
# - .all-pools (not in V3)
# - .all-pools-events
# - .all-pools-ledger
# - .get-pools
# - .get-pools-ledger
# - .get-pools-tokens
# - .get-ring0-ref-price
# - .get-pool-info-token-price


class UniswapV3FactoryMeta:
    FACTORY_ADDRESS = V3_FACTORY_ADDRESS
    PROTOCOL = DexProtocol.UniswapV3
    WEIGHT_POWER = 4.0
    POOL_FEES = V3_POOL_FEES


class UniswapV3PoolMeta(Model):
    @abstractmethod
    def run(self, input):
        ...

    @staticmethod
    def get_factory(factory_addr: Address):
        factory = Contract(address=factory_addr).set_abi(UNISWAP_V3_FACTORY_ABI, set_loaded=True)
        return factory

    @staticmethod
    def get_pool(pair_addr: Address):
        return Contract(address=pair_addr).set_abi(UNISWAP_V3_POOL_ABI, set_loaded=True)

    def __get_pools_by_pair(self, factory_addr: Address, token_pairs: list[tuple[Address, Address]], pool_fees: list[int]) -> list[Address]:
        uniswap_factory = self.get_factory(factory_addr)
        pools = []
        for token_pair in token_pairs:
            for fee in pool_fees:
                pool_addr = uniswap_factory.functions.getPool(*token_pair, fee).call()
                if not Address(pool_addr).is_null():
                    cc = self.get_pool(pool_addr)
                    try:
                        _ = cc.abi
                        _ = cc.functions.token0().call()
                        _ = cc.functions.token1().call()
                    except BlockNumberOutOfRangeError:
                        continue  # access it before its creation
                    except BadFunctionCallOutput:
                        continue
                    except ModelDataError:
                        pass
                    pools.append(Address(pool_addr))
        return pools

    POOLS_COLUMNS = ['block_number', 'log_index', 'transaction_hash',
                     'pool_address', 'token0', 'token1', 'fee', 'tickSpacing']

    def get_all_pools_ledger(self, factory_addr: Address):
        factory = self.get_factory(factory_addr)

        start_time = datetime.now()
        with factory.ledger.events.PoolCreated as q:
            df_ts = []
            offset = 0

            while True:
                df_tt = q.select(
                    columns=q.columns,
                    order_by=q.BLOCK_NUMBER.comma_(q.EVT_POOL),
                    limit=5000,
                    offset=offset).to_dataframe()

                if df_tt.shape[0] > 0:
                    df_ts.append(df_tt)
                if df_tt.shape[0] < 5000:
                    break
                offset += 5000
        all_df = (pd
                  .concat(df_ts).sort_values(['block_number', 'log_index'])
                  .reset_index(drop=True)
                  .drop_duplicates(subset='evt_pool', keep='last')
                  .astype({'block_number': 'int', 'log_index': 'int'}))
        self.logger.info(f'time spent {datetime.now() - start_time} to fetch {all_df.shape[0]} records')

        all_addresses = set(all_df.evt_pool.tolist())
        assert all_df.shape[0] == len(all_addresses)
        return Records.from_dataframe(
            all_df
            .rename(columns={'evt_pool': 'pool_address',
                             'evt_token0': 'token0',
                             'evt_token1': 'token1',
                             'evt_fee': 'fee',
                             'evt_tickSpacing': 'tickSpacing'})
            .loc[:, self.POOLS_COLUMNS])

    def get_all_pairs_events(self, factory_addr: Address, _from_block, _to_block):
        factory = self.get_factory(factory_addr)
        deployed_block_number = self.context.run_model('token.deployment',
                                                       {'address': factory_addr, "ignore_proxy": True}
                                                       )['deployed_block_number']
        start_time = datetime.now()
        df = pd.DataFrame(factory.fetch_events(factory.events.PoolCreated,
                          from_block=max(deployed_block_number-1, _from_block),
                          to_block=_to_block, by_range=100_000))
        self.logger.info(f'time spent {datetime.now() - start_time} to fetch {df.shape[0]} records')
        df['transactionHash'] = df['transactionHash'].apply(lambda x: x.hex())
        df.rename(columns={
            'blockNumber': 'block_number',
            'logIndex': 'log_index',
            'transactionHash': 'transaction_hash',
            'pool': 'pool_address'}, inplace=True)
        if not df.empty:
            return Records.from_dataframe(df.loc[:, self.POOLS_COLUMNS])
        return Records.empty()

    def get_pair(self, factory_addr: Address, token0_address, token1_address, pool_fees):
        return self.__get_pools_by_pair(factory_addr, [(token0_address, token1_address)], pool_fees)

    def get_pools_for_tokens(self, factory_addr: Address, _protocol, input_addresses: list[Address], pool_fees) -> list[Address]:
        token_pairs = get_primary_token_tuples(self.context, _protocol, input_addresses)
        return self.__get_pools_by_pair(factory_addr, token_pairs, pool_fees)

    def get_pools_for_tokens_ledger(self, factory_addr: Address, _protocol, input_address: Address, fees: list[int]):
        factory = self.get_factory(factory_addr)
        token_pairs = get_primary_token_tuples(self.context, _protocol, [input_address])
        token_pairs_fee = [(*tp, fees) for tp in token_pairs]

        with factory.ledger.events.PoolCreated as q:
            tp = token_pairs_fee[0]
            eq_conds = (q.EVT_TOKEN0.eq(tp[0]).and_(q.EVT_TOKEN1.eq(tp[1]))
                         .and_(q.EVT_FEE.as_bigint().in_(tp[2])).parentheses_())

            for tp in token_pairs_fee[1:]:
                new_eq = (q.EVT_TOKEN0.eq(tp[0]).and_(q.EVT_TOKEN1.eq(tp[1]))
                           .and_(q.EVT_FEE.as_bigint().in_(tp[2])).parentheses_())
                eq_conds = eq_conds.or_(new_eq)

            df_ts = []
            offset = 0
            while True:
                df_tt = q.select(
                    columns=[q.EVT_POOL, q.BLOCK_NUMBER],
                    aggregates=[(q.EVT_FEE.as_bigint(), q.EVT_FEE)],
                    where=eq_conds,
                    order_by=q.BLOCK_NUMBER.comma_(q.EVT_POOL),
                    limit=5000,
                    offset=offset).to_dataframe()

                if df_tt.shape[0] > 0:
                    df_ts.append(df_tt)
                if df_tt.shape[0] < 5000:
                    break
                offset += 5000

            all_df = pd.concat(df_ts)

        evt_pool = all_df['evt_pool']

        return Contracts(contracts=[Contract(c) for c in evt_pool])

    def get_ref_price(self, factory_addr, _protocol: DexProtocol, weight_power: float, pool_fees: list[int]) -> float:
        ring0_tokens = sorted(self.context.run_model(
            'dex.ring0-tokens', DexProtocolInput(protocol=_protocol),
            return_type=Some[Address], local=True).some)

        ratios = {}
        valid_tokens = set()
        missing_relations = []
        for token0_address in ring0_tokens:
            for token1_address in ring0_tokens:
                # Uniswap builds pools with token0 < token1
                if token0_address.to_int() >= token1_address.to_int():
                    continue
                token_pairs = [(token0_address, token1_address)]
                pools = self.__get_pools_by_pair(factory_addr, token_pairs, pool_fees=pool_fees)

                if len(pools) == 0:
                    missing_relations.extend(
                        [(token0_address, token1_address), (token1_address, token0_address)])
                    continue

                pools_info = [self.context.run_model('uniswap-v3.get-pool-info', input={'address': p}) for p in pools]
                pools_info_sel = [[p,
                                   *[pi[k] for k in ['ratio_price0', 'one_tick_liquidity0', 'ratio_price1', 'one_tick_liquidity1']]]
                                  for p, pi in zip(pools, pools_info)]

                pool_info = pd.DataFrame(data=pools_info_sel,
                                         columns=['address', 'ratio_price0', 'one_tick_liquidity0', 'ratio_price1', 'one_tick_liquidity1'])

                if pool_info.shape[0] > 1:
                    ratio0 = (pool_info.ratio_price0 * pool_info.one_tick_liquidity0 ** weight_power).sum() / \
                        (pool_info.one_tick_liquidity0 ** weight_power).sum()
                    ratio1 = (pool_info.ratio_price1 * pool_info.one_tick_liquidity1 ** weight_power).sum() / \
                        (pool_info.one_tick_liquidity1 ** weight_power).sum()
                else:
                    ratio0 = pool_info['ratio_price0'][0]
                    ratio1 = pool_info['ratio_price1'][0]

                ratios[(token0_address, token1_address)] = ratio0
                ratios[(token1_address, token0_address)] = ratio1
                valid_tokens.add(token0_address)
                valid_tokens.add(token1_address)

        valid_tokens_list = sorted(list(valid_tokens))

        if len(valid_tokens_list) == len(ring0_tokens):
            try:
                assert len(ring0_tokens) < 4
            except AssertionError:
                raise ModelDataError(
                    'Not implemented Calculate for missing relations for more than 3 ring0 tokens') from None

            for token0_address, token1_address in missing_relations:
                other_token = list(set(ring0_tokens) - {token0_address, token1_address})[0]
                ratios[(token0_address, token1_address)] = ratios[(token0_address, other_token)] * \
                    ratios[(other_token, token1_address)]

        corr_mat = np.ones((len(valid_tokens_list), len(valid_tokens_list)))
        for tok1_n, tok1 in enumerate(valid_tokens_list):
            for tok2_n, tok2 in enumerate(valid_tokens_list):
                if tok2_n != tok1_n and (tok1, tok2) in ratios:
                    corr_mat[tok1_n, tok2_n] = ratios[(tok1, tok2)]

        candidate_prices = []
        for pivot_token in valid_tokens_list:
            candidate_price = np.array([ratios[(token, pivot_token)]
                                        if token != pivot_token else 1
                                        for token in valid_tokens_list])
            candidate_prices.append((
                (candidate_price.max() / candidate_price.min(), -candidate_price.max(), candidate_price.min()),  # sort key
                candidate_price / candidate_price.max())  # normalized price
            )

        ring0_token_symbols = [Token(t).symbol for t in ring0_tokens]

        return dict(zip(
            valid_tokens_list,
            sorted(candidate_prices, key=lambda x: x[0])[0][1])) | dict(zip(ring0_token_symbols, ring0_tokens))


@Model.describe(slug="uniswap-v3.get-factory",
                version="0.1",
                display_name="Uniswap V3 - get factory",
                description="Returns the address of Uniswap V3 factory contract",
                category='protocol',
                subcategory='uniswap-v3',
                output=Contract)
class UniswapV3GetFactory(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, _) -> Contract:
        return self.get_factory(self.FACTORY_ADDRESS[self.context.network])


@Model.describe(slug="uniswap-v3.get-pool",
                version="1.3",
                display_name="Uniswap V3 get pool for a pair of tokens",
                description=("Returns the addresses of the pool of input tokens"),
                category='protocol',
                subcategory='uniswap-v3',
                input=DexPoolInput,
                output=Contracts)
class UniswapV3GetPair(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, input: DexPoolInput) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pair(factory_addr, input.token0.address, input.token1.address, self.POOL_FEES)
        return Contracts.from_addresses(pools)


@Model.describe(slug="uniswap-v3.all-pools-events",
                version="0.1",
                display_name="Uniswap v3 all pairs",
                description="Returns the addresses of all pairs on Uniswap V3 protocol",
                category='protocol',
                subcategory='uniswap-v3',
                input=EmptyInputSkipTest,
                output=Records)
class UniswapV3AllPairsEvents(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, _) -> Records:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_all_pairs_events(
            factory_addr, _from_block=0, _to_block=self.context.block_number)


@Model.describe(slug='uniswap-v3.all-pools-ledger',
                version='1.4',
                display_name='Uniswap v3 Token Pools - from ledger',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                input=EmptyInputSkipTest,
                output=Records)
class UniswapV3AllPoolsLedger(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, _) -> Records:
        return self.get_all_pools_ledger(self.FACTORY_ADDRESS[self.context.network])


# TODO: test
@Model.describe(slug='uniswap-v3.get-pools',
                version='1.7',
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                input=Token,
                output=Contracts)
class UniswapV3GetPoolsForToken(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(factory_addr, self.PROTOCOL, [input.address], self.POOL_FEES)
        return Contracts.from_addresses(pools)


@Model.describe(slug='uniswap-v3.get-pools-ledger',
                version='1.7',
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                input=Token,
                output=Contracts)
class UniswapV3GetPoolsLedger(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_pools_for_tokens_ledger(
            factory_addr, self.PROTOCOL, input.address, self.POOL_FEES)


@Model.describe(slug='uniswap-v3.get-pools-tokens',
                version='1.7',
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                input=Tokens,
                output=Contracts)
class UniswapV3GetPoolsTokens(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, input: Tokens) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(factory_addr, self.PROTOCOL,
                                          [tok.address for tok in input.tokens], self.POOL_FEES)
        return Contracts.from_addresses(list(set(pools)))


@Model.describe(slug='uniswap-v3.get-ring0-ref-price',
                version='0.8',
                display_name='Uniswap v3 Ring0 Reference Price',
                description='The Uniswap v3 pools that support the ring0 tokens',
                category='protocol',
                subcategory='uniswap-v3',
                output=dict)
class UniswapV3GetRing0RefPrice(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, _) -> dict:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_ref_price(factory_addr, self.PROTOCOL, self.WEIGHT_POWER, self.POOL_FEES)


@Model.describe(slug='uniswap-v3.get-pool-info-token-price',
                version='1.19',
                display_name='Uniswap v3 Token Pools Price ',
                description='Gather price and liquidity information from pools',
                category='protocol',
                subcategory='uniswap-v3',
                input=DexPriceTokenInput,
                output=Some[PoolPriceInfo])
class UniswapV3GetTokenPoolInfo(Model, UniswapV3FactoryMeta):
    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        pools = self.context.run_model(
            'uniswap-v3.get-pools', input, return_type=Contracts, local=True)

        model_slug = 'uniswap-v3.get-pool-price-info'
        model_inputs = [UniswapV3DexPoolPriceInput(
            address=pool.address,
            price_slug='uniswap-v3.get-weighted-price',
            ref_price_slug='uniswap-v3.get-ring0-ref-price',
            weight_power=input.weight_power,
            debug=input.debug,
            protocol=self.PROTOCOL)
            for pool in pools.contracts]

        def _use_compose():
            pool_infos = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': model_slug,
                       'modelInputs': model_inputs},
                return_type=MapInputsOutput[dict, PoolPriceInfo])

            infos = []
            for pool_n, p in enumerate(pool_infos):
                if p.output is not None:
                    infos.append(p.output)
                elif p.error is not None:
                    self.logger.error(p.error)
                    raise ModelRunError(
                        (f'Error with models({self.context.block_number}).'
                         f'{model_slug.replace("-","_")}({model_inputs[pool_n]}). ' +
                         p.error.message))
                else:
                    raise ModelRunError(
                        'compose.map-inputs: output/error cannot be both None')
            return infos

        def _use_for(local):
            infos = []
            for m_input in model_inputs:
                pi = self.context.run_model(model_slug, m_input, return_type=PoolPriceInfo,
                                            local=local)
                infos.append(pi)
            return infos

        infos = _use_for(local=True)

        return Some[PoolPriceInfo](some=infos)
