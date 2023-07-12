
# pylint: disable=too-many-lines, unsubscriptable-object, line-too-long
from abc import abstractmethod
from datetime import datetime
from typing import Tuple

import numpy as np
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import Address, BlockNumberOutOfRangeError, Contract, Contracts, Maybe, Records, Some, Token
from credmark.cmf.types.compose import MapInputsOutput
from web3.exceptions import (
    BadFunctionCallOutput,
    ContractLogicError,
)

from models.dtos.pool import PoolPriceInfo
from models.dtos.price import (
    DexPriceTokenInput,
    DexProtocol,
    DexProtocolInput,
    PoolDexPoolPriceInput,
    PrimaryTokenPairsInput,
    PrimaryTokenPairsOutput,
)
from models.tmp_abi_lookup import UNISWAP_V2_FACTORY_ABI, UNISWAP_V2_POOL_ABI


class UniswapV2PoolMeta(Model):
    @abstractmethod
    def run(self, input):
        ...

    @staticmethod
    def get_factory(factory_addr: Address):
        factory = Contract(address=factory_addr).set_abi(UNISWAP_V2_FACTORY_ABI, set_loaded=True)
        return factory

    @staticmethod
    def get_pool(pair_addr: Address):
        return Contract(address=pair_addr).set_abi(UNISWAP_V2_POOL_ABI, set_loaded=True)

    def get_pools_by_pair(self, factory_addr: Address, token_pairs: list[tuple[Address, Address]]) -> list[Address]:
        factory = self.get_factory(factory_addr)

        pools = []
        for token0_addr, token1_addr in token_pairs:
            try:
                pair_addr = Address(factory.functions.getPair(
                    token0_addr.checksum, token1_addr.checksum).call())
            except (BlockNumberOutOfRangeError, BadFunctionCallOutput, ModelDataError):
                # Uniswap V2: if self.context.block_number < 10000835
                # SushiSwap: if self.context.block_number < 10794229
                continue  # before its creation

            if pair_addr.is_null():
                continue

            cc = self.get_pool(pair_addr)
            try:
                _ = cc.abi
                _ = cc.functions.token0().call()
                _ = cc.functions.token1().call()
            except (BlockNumberOutOfRangeError, BadFunctionCallOutput):
                continue
            except ModelDataError:
                pass
            pools.append(pair_addr)

        return pools

    def get_all_pairs(self, factory_addr: Address):
        factory = self.get_factory(factory_addr)
        allPairsLength = factory.functions.allPairsLength().call()
        pair_addresses = []

        error_count = 0
        for i in range(allPairsLength):
            try:
                pair_address = factory.functions.allPairs(i).call()
                pair_addresses.append(Address(pair_address).checksum)
            except Exception:
                error_count += 1

        self.logger.info(f'There are {error_count} errors in total {allPairsLength} pools.')
        return Some[Address](some=pair_addresses)

    POOLS_COLUMNS = ['block_number', 'log_index',
                     'transaction_hash', 'pool_address', 'token0', 'token1']

    def get_all_pools_ledger(self, factory_addr: Address):
        factory = self.get_factory(factory_addr)

        start_time = datetime.now()
        with factory.ledger.events.PairCreated as q:
            df_ts = []
            offset = 0

            while True:
                df_tt = q.select(
                    columns=q.columns,
                    order_by=q.BLOCK_NUMBER.comma_(q.EVT_PAIR),
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
                  .drop_duplicates(subset='evt_pair', keep='last')
                  .astype({'block_number': 'int', 'log_index': 'int'}))
        self.logger.info(
            f'time spent {datetime.now() - start_time} to fetch {all_df.shape[0]} records')

        all_addresses = set(all_df.evt_pair.tolist())
        assert all_df.shape[0] == len(all_addresses)

        all_df_sel = (all_df
                      .rename(columns={'evt_pair': 'pool_address',
                                       'evt_token0': 'token0',
                                       'evt_token1': 'token1', })
                      .loc[:, self.POOLS_COLUMNS])

        return Records.from_dataframe(all_df_sel)

    def get_all_pairs_events(self, factory_addr: Address, _from_block, _to_block):
        factory = self.get_factory(factory_addr)
        deployed_block_number = self.context.run_model('token.deployment',
                                                       {'address': factory_addr, "ignore_proxy": True}
                                                       )['deployed_block_number']
        start_time = datetime.now()
        df = pd.DataFrame(factory.fetch_events(factory.events.PairCreated,
                                               from_block=max(deployed_block_number-1, _from_block),
                                               # from_block=_to_block - 10_000,
                                               to_block=_to_block,
                                               by_range=1_000_000))
        self.logger.info(f'time spent {datetime.now() - start_time} to fetch {df.shape[0]} records')
        df['transactionHash'] = df['transactionHash'].apply(lambda x: x.hex())
        df.rename(columns={
            'blockNumber': 'block_number',
            'logIndex': 'log_index',
            'transactionHash': 'transaction_hash',
            'pair': 'pool_address'}, inplace=True)
        if not df.empty:
            return Records.from_dataframe(df.loc[:, self.POOLS_COLUMNS])
        return Records.empty()

    def get_pair(self, factory_addr: Address, token0_address: Address, token1_address: Address):
        pools = self.get_pools_by_pair(factory_addr, [(token0_address, token1_address)])
        if len(pools) == 0:
            return Maybe[Contract].none()
        return Maybe(just=Contract(pools[0]))

    def get_pools_for_tokens(self, factory_addr: Address, _protocol, input_addresses: list[Address]) -> list[Address]:
        token_pairs = self.context.run_model('dex.primary-token-pairs',
                                             PrimaryTokenPairsInput(
                                                 addresses=input_addresses, protocol=_protocol),
                                             return_type=PrimaryTokenPairsOutput, local=True).pairs
        return self.get_pools_by_pair(factory_addr, token_pairs)

    def get_pools_for_tokens_ledger(self, factory_addr: Address, _protocol, input_address: Address) -> Contracts:
        token_pairs = self.context.run_model('dex.primary-token-pairs',
                                             PrimaryTokenPairsInput(
                                                 addresses=[input_address], protocol=_protocol),
                                             return_type=PrimaryTokenPairsOutput, local=True).pairs

        factory = self.get_factory(factory_addr)
        with factory.ledger.events.PairCreated as q:
            tp0 = token_pairs[0]
            eq_conds = q.EVT_TOKEN0.eq(tp0[0].checksum).and_(
                q.EVT_TOKEN1.eq(tp0[1].checksum)).parentheses_()

            for tp1 in token_pairs[1:]:
                new_eq = q.EVT_TOKEN0.eq(tp1[0].checksum).and_(
                    q.EVT_TOKEN1.eq(tp1[1].checksum)).parentheses_()
                eq_conds = eq_conds.or_(new_eq)

            df_ts = []
            offset = 0
            while True:
                df_tt = q.select(columns=[q.EVT_PAIR, q.BLOCK_NUMBER],
                                 where=eq_conds,
                                 order_by=q.BLOCK_NUMBER.comma_(q.EVT_PAIR),
                                 limit=5000,
                                 offset=offset).to_dataframe()

                if df_tt.shape[0] > 0:
                    df_ts.append(df_tt)
                if df_tt.shape[0] < 5000:
                    break
                offset += 5000

            if len(df_ts) == 0:
                return Contracts.empty()

            all_df = pd.concat(df_ts, axis=0)

        evt_pair = all_df['evt_pair']  # type: ignore

        return Contracts(contracts=[Contract(c) for c in evt_pair])

    def __get_pool_info_ring0(self, pool_addr: Address) -> Tuple[float, float, float, float]:
        pool = self.get_pool(pool_addr)
        reserves = pool.functions.getReserves().call()

        if reserves == [0, 0, 0]:
            return 0, 0, 0, 0

        token0_addr = pool.functions.token0().call()
        token1_addr = pool.functions.token1().call()

        try:
            token0 = Token(address=Address(token0_addr)).as_erc20(set_loaded=True)
        except (OverflowError, ContractLogicError):
            token0 = Token(address=Address(token0_addr)).as_erc20()

        try:
            token1 = Token(address=Address(token1_addr)).as_erc20(set_loaded=True)
        except (OverflowError, ContractLogicError):
            token1 = Token(address=Address(token1_addr)).as_erc20()

        scaled_reserve0 = token0.scaled(reserves[0])
        scaled_reserve1 = token1.scaled(reserves[1])

        try:
            tick_price0 = scaled_reserve1 / scaled_reserve0
            tick_price1 = 1. / tick_price0
        except (FloatingPointError, ZeroDivisionError):
            tick_price0 = 0.
            tick_price1 = 0.

        full_tick_liquidity0 = scaled_reserve0
        one_tick_liquidity0 = np.abs(
            1. / np.sqrt(1. + 0.0001) - 1.) * full_tick_liquidity0

        full_tick_liquidity1 = scaled_reserve1
        one_tick_liquidity1 = (np.sqrt(1. + 0.0001) - 1.) * full_tick_liquidity1

        return (tick_price0, one_tick_liquidity0, tick_price1, one_tick_liquidity1)

    def get_ref_price(self, factory_addr: Address, _protocol: DexProtocol, weight_power: float):
        ring0_tokens = sorted(self.context.run_model('dex.ring0-tokens',
                                                     DexProtocolInput(protocol=_protocol),
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
                pools = self.get_pools_by_pair(factory_addr, token_pairs)

                if len(pools) == 0:
                    missing_relations.extend(
                        [(token0_address, token1_address), (token1_address, token0_address)])
                    continue

                # print((token1_address, token2_address, len(pools.contracts), pools))
                pool_info = pd.DataFrame(
                    data=[self.__get_pool_info_ring0(addr) for addr in pools],
                    columns=['tick_price0', 'one_tick_liquidity0',
                             'tick_price1', 'one_tick_liquidity1'])

                if pool_info.shape[0] > 1:
                    ratio0 = (pool_info.tick_price0 * pool_info.one_tick_liquidity0 ** weight_power).sum() / \
                        (pool_info.one_tick_liquidity0 ** weight_power).sum()
                    ratio1 = (pool_info.tick_price1 * pool_info.one_tick_liquidity1 ** weight_power).sum() / \
                        (pool_info.one_tick_liquidity1 ** weight_power).sum()
                else:
                    ratio0 = pool_info['tick_price0'][0]
                    ratio1 = pool_info['tick_price1'][0]

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
            candidate_prices.append(
                ((candidate_price.max() / candidate_price.min(), -candidate_price.max(), candidate_price.min()),  # sort key
                 candidate_price / candidate_price.max())  # normalized price
            )

        ring0_token_symbols = {Token(t).symbol: t for t in valid_tokens_list}

        return dict(zip(
            valid_tokens_list,
            sorted(candidate_prices, key=lambda x: x[0])[0][1])) | ring0_token_symbols

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

        infos = _use_for(local=False)
        return Some[PoolPriceInfo](some=infos)
