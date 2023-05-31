# pylint: disable=locally-disabled, invalid-name, line-too-long

from abc import abstractmethod
from datetime import datetime

import numpy as np
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import Address, BlockNumberOutOfRangeError, Contract, Contracts, Maybe, Records, Some, Token
from credmark.cmf.types.compose import MapInputsOutput
from web3.exceptions import BadFunctionCallOutput

from models.dtos.pool import PoolPriceInfo
from models.dtos.price import (
    DexPriceTokenInput,
    DexProtocol,
    DexProtocolInput,
    PoolDexPoolPriceInput,
    PrimaryTokenPairsInput,
    PrimaryTokenPairsOutput,
)
from models.tmp_abi_lookup import UNISWAP_V3_FACTORY_ABI, UNISWAP_V3_POOL_ABI

np.seterr(all='raise')


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

    def get_pools_by_pair(self, factory_addr: Address, token_pairs: list[tuple[Address, Address]], pool_fees: list[int]) -> list[Address]:
        uniswap_factory = self.get_factory(factory_addr)
        pools = []
        for token0_addr, token1_addr in token_pairs:
            for fee in pool_fees:
                try:
                    pool_addr = Address(uniswap_factory.functions
                                        .getPool(token0_addr.checksum, token1_addr.checksum, fee)
                                        .call())
                except (BlockNumberOutOfRangeError, BadFunctionCallOutput, ModelDataError):
                    continue  # before its creation

                if pool_addr.is_null():
                    continue

                try:
                    cc = self.get_pool(pool_addr)
                    _ = cc.abi
                    _ = cc.functions.token0().call()
                    _ = cc.functions.token1().call()
                except (BlockNumberOutOfRangeError, BadFunctionCallOutput):
                    continue  # access it before its creation
                except ModelDataError:
                    pass
                pools.append(pool_addr)
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

    def get_pools_for_tokens(self, factory_addr: Address, _protocol, input_addresses: list[Address], pool_fees) -> list[Address]:
        token_pairs = self.context.run_model('dex.primary-token-pairs',
                                             PrimaryTokenPairsInput(addresses=input_addresses, protocol=_protocol),
                                             return_type=PrimaryTokenPairsOutput).pairs
        return self.get_pools_by_pair(factory_addr, token_pairs, pool_fees)

    def get_pools_for_tokens_ledger(self, factory_addr: Address, _protocol, input_address: Address, fees: list[int]):
        token_pairs = self.context.run_model('dex.primary-token-pairs',
                                             PrimaryTokenPairsInput(addresses=[input_address], protocol=_protocol),
                                             return_type=PrimaryTokenPairsOutput).pairs
        token_pairs_fee = [(*tp, fees) for tp in token_pairs]

        factory = self.get_factory(factory_addr)
        with factory.ledger.events.PoolCreated as q:
            tp0 = token_pairs_fee[0]
            eq_conds = (q.EVT_TOKEN0.eq(tp0[0].checksum)
                        .and_(q.EVT_TOKEN1.eq(tp0[1].checksum))
                        .and_(q.EVT_FEE.as_bigint().in_(tp0[2]))
                        .parentheses_())

            for tp1 in token_pairs_fee[1:]:
                new_eq = (q.EVT_TOKEN0.eq(tp1[0].checksum)
                          .and_(q.EVT_TOKEN1.eq(tp1[1].checksum))
                          .and_(q.EVT_FEE.as_bigint().in_(tp1[2]))
                          .parentheses_())
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

            if len(df_ts) == 0:
                return Contracts.empty()

            all_df = pd.concat(df_ts)

        evt_pool = all_df['evt_pool']

        return Contracts(contracts=[Contract(c) for c in evt_pool])

    def get_ref_price(self, factory_addr, _protocol: DexProtocol, weight_power: float, pool_fees: list[int]):
        ring0_tokens = sorted(
            self.context.run_model(
                'dex.ring0-tokens',
                DexProtocolInput(protocol=_protocol),
                return_type=Some[Address]).some)

        ratios = {}
        valid_tokens = set()
        missing_relations = []
        for token0_address in ring0_tokens:
            for token1_address in ring0_tokens:
                # Uniswap builds pools with token0 < token1
                if token0_address.to_int() >= token1_address.to_int():
                    continue
                token_pairs = [(token0_address, token1_address)]
                pools = self.get_pools_by_pair(factory_addr, token_pairs, pool_fees=pool_fees)

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

    def get_pools_info(
            self,
            input: DexPriceTokenInput,
            pools: Contracts,
            model_slug,
            price_slug,
            ref_price_slug,
            _protocol) -> Some[PoolPriceInfo]:

        model_inputs = [
            PoolDexPoolPriceInput(
                address=pool.address,
                price_slug=price_slug,
                ref_price_slug=ref_price_slug,
                weight_power=input.weight_power,
                protocol=_protocol)
            for pool in pools]

        def _use_compose():
            pool_infos = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': model_slug,
                       'modelInputs': model_inputs},
                return_type=MapInputsOutput[dict, Maybe[PoolPriceInfo]])

            infos = []
            for pool_n, p in enumerate(pool_infos):
                if p.output is not None:
                    if p.output.just is not None:
                        infos.append(p.output.just)
                elif p.error is not None:
                    self.logger.error(p.error)
                    raise ModelRunError(
                        (f'Error with models({self.context.block_number}).' +
                         f'{model_slug.replace("-","_")}({model_inputs[pool_n]}). ' +
                         p.error.message))
                else:
                    raise ModelRunError(
                        'compose.map-inputs: output/error cannot be both None')
            return infos

        def _use_for(local):
            infos = []
            for m_input in model_inputs:
                pi = self.context.run_model(model_slug,
                                            m_input,
                                            return_type=Maybe[PoolPriceInfo],
                                            local=local)
                if pi.is_just():
                    infos.append(pi.just)
            return infos

        infos = _use_compose()
        return Some[PoolPriceInfo](some=infos)
