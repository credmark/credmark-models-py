# pylint: disable=too-many-lines, unsubscriptable-object, line-too-long
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (
    Address,
    Contract,
    Contracts,
    Maybe,
    Portfolio,
    Position,
    Price,
    PriceWithQuote,
    Some,
    Token,
    Tokens,
)
from credmark.cmf.types.block_number import BlockNumberOutOfRangeError
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO
from web3.exceptions import (
    ABIFunctionNotFound,
    BadFunctionCallOutput,
    ContractLogicError,
)

from models.credmark.price.dex import get_primary_token_tuples
from models.credmark.protocols.dexes.uniswap.constant import V2_FACTORY_ADDRESS
from models.dtos.pool import PoolPriceInfo
from models.dtos.price import DexPricePoolInput, DexPriceTokenInput
from models.dtos.tvl import TVLInfo
from models.tmp_abi_lookup import UNISWAP_V2_POOL_ABI


class UniswapV2Contract(Contract):
    class Config:
        schema_extra = {
            "examples": [{"address": "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852"}]
        }


class UniswapV2DexPricePoolInput(UniswapV2Contract, DexPricePoolInput):
    price_slug: str
    ref_price_slug: Optional[str]

    class Config:
        schema_extra = {
            'examples': [{"address": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
                          "price_slug": "uniswap-v2.get-weighted-price",
                          "ref_price_slug": "uniswap-v2.get-ring0-ref-price"}]
        }


class UniswapV2PoolMeta:
    @staticmethod
    def get_uniswap_pools_by_pair(_context, factory_addr: Address, token_pairs) -> list[Address]:
        factory = Contract(address=factory_addr)

        contracts = []
        try:
            for token_pair in token_pairs:
                pair_addr = factory.functions.getPair(*token_pair).call()
                if not Address(pair_addr).is_null():
                    cc = Contract(address=pair_addr).set_abi(
                        UNISWAP_V2_POOL_ABI, set_loaded=True)
                    try:
                        _ = cc.abi
                        _ = cc.functions.token0().call()
                    except BlockNumberOutOfRangeError:
                        continue  # before its creation
                    except ModelDataError:
                        pass
                    contracts.append(Address(pair_addr))

            return contracts
        except (BadFunctionCallOutput, BlockNumberOutOfRangeError):
            # Or use this condition: if self.context.block_number < 10000835 # Uniswap V2
            # Or use this condition: if self.context.block_number < 10794229 # SushiSwap
            return []

    @staticmethod
    def get_uniswap_pools(_context, factory_addr: Address, input_addresses: list[Address]) -> list[Address]:
        token_pairs = get_primary_token_tuples(_context, input_addresses)
        return UniswapV2PoolMeta.get_uniswap_pools_by_pair(_context, factory_addr, token_pairs)

    @staticmethod
    def get_uniswap_pools_ledger(context, factory_addr: Address, input_address: Address) -> Contracts:
        factory = Contract(address=factory_addr)
        token_pairs = get_primary_token_tuples(context, [input_address])

        with factory.ledger.events.PairCreated as q:
            tp = token_pairs[0]
            eq_conds = q.EVT_TOKEN0.eq(tp[0]).and_(
                q.EVT_TOKEN1.eq(tp[1])).parentheses_()
            for tp in token_pairs[1:]:
                new_eq = q.EVT_TOKEN0.eq(tp[0]).and_(
                    q.EVT_TOKEN1.eq(tp[1])).parentheses_()
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

            all_df = pd.concat(df_ts, axis=0)

        evt_pair = all_df['evt_pair']  # type: ignore

        return Contracts(contracts=[Contract(c) for c in evt_pair])

    WEIGHT_POWER = 4

    @staticmethod
    def get_uniswap_pool_info(_context, pool_addr: Address) -> Tuple[float, float, float, float]:
        pool = Contract(address=pool_addr).set_abi(
            abi=UNISWAP_V2_POOL_ABI, set_loaded=True)

        reserves = pool.functions.getReserves().call()

        if reserves == [0, 0, 0]:
            return 0, 0, 0, 0

        token0_addr = pool.functions.token0().call()
        token1_addr = pool.functions.token1().call()

        try:
            token0 = Token(address=Address(token0_addr)
                           ).as_erc20(set_loaded=True)
        except (OverflowError, ContractLogicError):
            token0 = Token(address=Address(token0_addr)).as_erc20()

        try:
            token1 = Token(address=Address(token1_addr)
                           ).as_erc20(set_loaded=True)
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

    @staticmethod
    def get_ref_price(_context, factory_addr: Address):
        ring0_tokens = sorted(_context.run_model('dex.ring0-tokens', {},
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
                pools = UniswapV2PoolMeta.get_uniswap_pools_by_pair(
                    _context, factory_addr, token_pairs)

                if len(pools) == 0:
                    missing_relations.extend(
                        [(token0_address, token1_address), (token1_address, token0_address)])
                    continue

                # print((token1_address, token2_address, len(pools.contracts), pools))
                pool_info = pd.DataFrame(
                    data=[UniswapV2PoolMeta.get_uniswap_pool_info(_context, addr) for addr in pools],
                    columns=['tick_price0', 'one_tick_liquidity0',
                             'tick_price1', 'one_tick_liquidity1'])

                if pool_info.shape[0] > 1:
                    ratio0 = (pool_info.tick_price0 * pool_info.one_tick_liquidity0 ** UniswapV2PoolMeta.WEIGHT_POWER).sum() / \
                        (pool_info.one_tick_liquidity0 **
                         UniswapV2PoolMeta.WEIGHT_POWER).sum()
                    ratio1 = (pool_info.tick_price1 * pool_info.one_tick_liquidity1 ** UniswapV2PoolMeta.WEIGHT_POWER).sum() / \
                        (pool_info.one_tick_liquidity1 **
                         UniswapV2PoolMeta.WEIGHT_POWER).sum()
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
                assert len(ring0_tokens) == 3
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

        ring0_token_symbols = [Token(t).symbol for t in ring0_tokens]

        return dict(zip(
            valid_tokens_list,
            sorted(candidate_prices, key=lambda x: x[0])[0][1])) | dict(zip(ring0_token_symbols, ring0_tokens))


@Model.describe(slug='uniswap-v2.get-ring0-ref-price',
                version='0.7',
                display_name='Uniswap v2 Ring0 Reference Price',
                description='The Uniswap v2 pools that support the ring0 tokens',
                category='protocol',
                subcategory='uniswap-v2',
                output=dict)
class UniswapV2GetRing0RefPrice(Model, UniswapV2PoolMeta):
    def run(self, _) -> dict:
        factory_addr = V2_FACTORY_ADDRESS[self.context.network]
        return self.get_ref_price(self.context, factory_addr)


@Model.describe(slug='uniswap-v2.get-pools',
                version='1.10',
                display_name='Uniswap v2 Token Pools',
                description='The Uniswap v2 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v2',
                input=Token,
                output=Contracts)
class UniswapV2GetPoolsForToken(Model, UniswapV2PoolMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = V2_FACTORY_ADDRESS[self.context.network]
        pools = self.get_uniswap_pools(self.context, factory_addr, [input.address])
        return Contracts.from_addresses(pools)


@Model.describe(slug='uniswap-v2.get-pools-tokens',
                version='1.10',
                display_name='Uniswap v2 Pools for Tokens',
                description='The Uniswap v2 pools that support token contract',
                category='protocol',
                subcategory='uniswap-v2',
                input=Tokens,
                output=Contracts)
class UniswapV2GetPoolsForTokens(Model, UniswapV2PoolMeta):
    def run(self, input: Tokens) -> Contracts:
        factory_addr = V2_FACTORY_ADDRESS[self.context.network]
        pools = self.get_uniswap_pools(self.context,
                                       factory_addr,
                                       [tok.address for tok in input.tokens])
        return Contracts.from_addresses(list(set(pools)))


@Model.describe(slug='uniswap-v2.get-pools-ledger',
                version='0.2',
                display_name='Uniswap v2 Token Pools',
                description='The Uniswap v2 pools that support a token contract - use ledger',
                category='protocol',
                subcategory='uniswap-v2',
                input=Token,
                output=Contracts)
class UniswapV2GetPoolsForTokenLedger(Model, UniswapV2PoolMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = V2_FACTORY_ADDRESS[self.context.network]
        return self.get_uniswap_pools_ledger(self.context, factory_addr, input.address)


@Model.describe(slug='uniswap-v2.get-pool-price-info',
                version='1.16',
                display_name='Uniswap v2 Token Pool Price Info',
                description='Gather price and liquidity information from pool',
                category='protocol',
                subcategory='uniswap-v2',
                input=UniswapV2DexPricePoolInput,
                output=Maybe[PoolPriceInfo])
class UniswapPoolPriceInfo(Model):
    """
    Model to be shared between Uniswap V2 and SushiSwap
    """

    def run(self, input: UniswapV2DexPricePoolInput) -> Maybe[PoolPriceInfo]:
        pool = input
        try:
            _ = pool.abi
        except ModelDataError:
            pool = Contract(address=input.address).set_abi(
                abi=UNISWAP_V2_POOL_ABI, set_loaded=True)

        ring0_tokens = self.context.run_model(
            'dex.ring0-tokens', {}, return_type=Some[Address], local=True).some

        weth_address = Token('WETH').address

        reserves = pool.functions.getReserves().call()
        if reserves == [0, 0, 0]:
            return Maybe[PoolPriceInfo].none()

        token0_addr = pool.functions.token0().call()
        token1_addr = pool.functions.token1().call()

        try:
            token0 = Token(address=Address(token0_addr)
                           ).as_erc20(set_loaded=True)
            token0_symbol = token0.symbol
        except (OverflowError, ContractLogicError):
            token0 = Token(address=Address(token0_addr)).as_erc20()
            token0_symbol = token0.symbol

        try:
            token1 = Token(address=Address(token1_addr)
                           ).as_erc20(set_loaded=True)
            token1_symbol = token1.symbol
        except (OverflowError, ContractLogicError):
            token1 = Token(address=Address(token1_addr)).as_erc20()
            token1_symbol = token1.symbol

        scaled_reserve0 = token0.scaled(reserves[0])
        scaled_reserve1 = token1.scaled(reserves[1])

        # https://uniswap.org/blog/uniswap-v3-dominance
        # Appendix B: methodology
        try:
            tick_price0 = scaled_reserve1 / scaled_reserve0
            tick_price1 = 1 / tick_price0
        except (FloatingPointError, ZeroDivisionError):
            tick_price0 = 0
            tick_price1 = 0

        full_tick_liquidity0 = scaled_reserve0
        one_tick_liquidity0 = np.abs(
            1 / np.sqrt(1 + 0.0001) - 1) * full_tick_liquidity0

        full_tick_liquidity1 = scaled_reserve1
        one_tick_liquidity1 = (np.sqrt(1 + 0.0001) - 1) * full_tick_liquidity1

        ref_price = 1.0

        # 1. If both are stablecoins (non-WETH): do nothing
        # 2. If SB-WETH/WBTC: use SB to price WETH/WBTC
        # 3. If WETH-WBTC: use WETH to price WBTC
        # 4. If SB/WETH/WBTC-X: use SB/WETH/WBTC to price

        is_ring0_pool = token0.address in ring0_tokens and token1.address in ring0_tokens

        if is_ring0_pool:
            if input.ref_price_slug is not None:
                ref_price_ring0 = self.context.run_model(
                    input.ref_price_slug, {}, return_type=dict)
                # Use the reference price to scale the tick price. Note the cross-reference is used here.
                # token0 = tick_price0 * token1 = tick_price0 * ref_price of token1
                tick_price0 *= ref_price_ring0[token1.address]
                tick_price1 *= ref_price_ring0[token0.address]
        elif token0.address == weth_address and token1.address in ring0_tokens:
            ref_price = self.context.run_model(
                slug=input.price_slug,
                input=DexPriceTokenInput(
                    **token1.dict(),
                    weight_power=input.weight_power,
                    debug=input.debug),
                return_type=Price,
                local=True).price
        elif token1.address == weth_address and token0.address in ring0_tokens:
            ref_price = self.context.run_model(
                slug=input.price_slug,
                input=DexPriceTokenInput(
                    **token0.dict(),
                    weight_power=input.weight_power,
                    debug=input.debug),
                return_type=Price,
                local=True).price
        # elif token0.address == weth_address and token1.address == wbtc_address:
        # use token0 as reference token
        # elif token1.address == weth_address and token0.address == wbtc_address:
        # use token1 as reference token
        else:
            if token0.address in ring0_tokens + [weth_address]:
                primary_address = token0.address
            elif token1.address in ring0_tokens + [weth_address]:
                primary_address = token1.address
            else:
                primary_address = Address.null()

            if not primary_address.is_null():
                ref_price = self.context.run_model(
                    slug=input.price_slug,
                    input=DexPriceTokenInput(
                        address=primary_address,
                        weight_power=input.weight_power,
                        debug=input.debug),
                    return_type=Price,
                    local=True).price
                if ref_price is None:
                    raise ModelRunError(f'Can not retrieve price for '
                                        f'{Token(address=primary_address)}')
            else:
                self.logger.warning(
                    'There is no primary token in this pool: '
                    f'{token0.address}/{token0.symbol} and {token1.address}/{token1.symbol}')
                ref_price = 0

        pool_price_info = PoolPriceInfo(src=input.price_slug,
                                        price0=tick_price0,
                                        price1=tick_price1,
                                        one_tick_liquidity0=one_tick_liquidity0,
                                        one_tick_liquidity1=one_tick_liquidity1,
                                        full_tick_liquidity0=full_tick_liquidity0,
                                        full_tick_liquidity1=full_tick_liquidity1,
                                        token0_address=token0.address,
                                        token1_address=token1.address,
                                        token0_symbol=token0_symbol,
                                        token1_symbol=token1_symbol,
                                        ref_price=ref_price,
                                        pool_address=input.address,
                                        tick_spacing=1)

        return Maybe[PoolPriceInfo](just=pool_price_info)


@Model.describe(slug='uniswap-v2.get-pool-info-token-price',
                version='1.15',
                display_name='Uniswap v2 Token Pools',
                description='Gather price and liquidity information from pools for a Token',
                category='protocol',
                subcategory='uniswap-v2',
                input=DexPriceTokenInput,
                output=Some[PoolPriceInfo])
class UniswapV2GetTokenPriceInfo(Model):
    def get_pools_info(
            self,
            input: DexPriceTokenInput,
            pools: Contracts) -> Some[PoolPriceInfo]:
        model_slug = 'uniswap-v2.get-pool-price-info'
        model_inputs = [
            UniswapV2DexPricePoolInput(
                address=pool.address,
                price_slug='uniswap-v2.get-weighted-price',
                ref_price_slug='uniswap-v2.get-ring0-ref-price',
                weight_power=input.weight_power,
                debug=input.debug)
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

        infos = _use_for(local=True)
        return Some[PoolPriceInfo](some=infos)

    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        pools = self.context.run_model(
            'uniswap-v2.get-pools', input, return_type=Contracts, local=True)

        return self.get_pools_info(input, pools)


class UniswapV2PoolInfo(DTO):
    pool_address: Address
    tokens: Tokens
    tokens_name: List[str]
    tokens_symbol: List[str]
    tokens_decimals: List[int]
    tokens_balance: List[float]
    tokens_price: List[PriceWithQuote]
    ratio: float


@Model.describe(slug="uniswap-v2.get-pool-info",
                version="1.10",
                display_name="Uniswap/SushiSwap get details for a pool",
                description="Returns the token details of the pool",
                category='protocol',
                subcategory='uniswap-v2',
                input=UniswapV2Contract,
                output=UniswapV2PoolInfo)
class UniswapGetPoolInfo(Model):
    def run(self, input: UniswapV2Contract) -> UniswapV2PoolInfo:
        pool = input
        try:
            _ = pool.abi
        except ModelDataError:
            pool = Contract(address=input.address).set_abi(
                abi=UNISWAP_V2_POOL_ABI, set_loaded=True)

        token0 = Token(address=pool.functions.token0().call())
        token1 = Token(address=pool.functions.token1().call())
        # getReserves = contract.functions.getReserves().call()

        token0_balance = token0.balance_of_scaled(input.address.checksum)
        token1_balance = token1.balance_of_scaled(input.address.checksum)
        # token0_reserve = token0.scaled(getReserves[0])
        # token1_reserve = token1.scaled(getReserves[1])

        prices = []
        prices.append(self.context.run_model(
            'price.dex-maybe',
            input={'base': token0},
            return_type=Maybe[PriceWithQuote]).just)
        prices.append(self.context.run_model(
            'price.dex-maybe',
            input={'base': token1},
            return_type=Maybe[PriceWithQuote]).just)

        value0 = prices[0].price * token0_balance
        value1 = prices[1].price * token1_balance

        balance_ratio = value0 * value1 / (((value0 + value1)/2)**2)

        pool_info = UniswapV2PoolInfo(
            pool_address=input.address,
            tokens=Tokens(tokens=[token0, token1]),
            tokens_name=[token0.name, token1.name],
            tokens_symbol=[token0.symbol, token1.symbol],
            tokens_decimals=[token0.decimals, token1.decimals],
            tokens_balance=[token0_balance, token1_balance],
            tokens_price=prices,
            ratio=balance_ratio
        )

        return pool_info


@Model.describe(slug='uniswap-v2.pool-tvl',
                version='1.8',
                display_name='Uniswap/SushiSwap Token Pool TVL',
                description='Gather price and liquidity information from pools',
                category='protocol',
                subcategory='uniswap-v2',
                input=UniswapV2Contract,
                output=TVLInfo)
class UniswapV2PoolTVL(Model):
    def run(self, input: UniswapV2Contract) -> TVLInfo:
        pool_info = self.context.run_model('uniswap-v2.get-pool-info',
                                           input=input,
                                           return_type=UniswapV2PoolInfo)
        positions = []
        prices = []
        tvl = 0.0

        prices = []
        for token_info, tok_price, bal in zip(pool_info.tokens,
                                              pool_info.tokens_price,
                                              pool_info.tokens_balance):
            prices.append(tok_price)
            tvl += bal * tok_price.price
            positions.append(Position(asset=token_info, amount=bal))

        try:
            pool_name = input.functions.name().call()
        except (ABIFunctionNotFound, ModelDataError):
            pool_name = 'Uniswap V3'

        tvl_info = TVLInfo(
            address=input.address,
            name=pool_name,
            portfolio=Portfolio(positions=positions),
            tokens_symbol=pool_info.tokens_symbol,
            prices=prices,
            tvl=tvl
        )

        return tvl_info


class UniswapV2PoolLPPosition(DTO):
    token0: Token
    token1: Token
    token0_amount: float
    token1_amount: float
    token0_reserve: float
    token1_reserve: float
    total_supply_scaled: float


@Model.describe(slug='uniswap-v2.lp-amount',
                version='0.2',
                display_name=('Decompose a UniswapV2Pair into its underlying tokens'),
                description='To calculate the value of a UniswapV2 LP token from its underlying tokens',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=UniswapV2Contract,
                output=UniswapV2PoolLPPosition,)
class PriceDexUniswapV2(Model):
    """
    Return token's price from
    """

    def run(self, input: UniswapV2Contract) -> UniswapV2PoolLPPosition:
        pool = Token(input.address)
        if pool.contract_name == 'UniswapV2Pair':
            token0 = Token(pool.functions.token0().call())
            token1 = Token(pool.functions.token1().call())
            total_supply_scaled = pool.total_supply_scaled
            token0_reserve, token1_reserve,  _blockTimestampLast = pool.functions.getReserves().call()
            token0_balance_scaled = token0.scaled(token0_reserve)
            token1_balance_scaled = token1.scaled(token1_reserve)
            self.logger.info(
                f'token0_balance_scaled: {token0_balance_scaled}, {token0.balance_of_scaled(pool.address.checksum)}')
            self.logger.info(
                f'token1_balance_scaled: {token1_balance_scaled}, {token1.balance_of_scaled(pool.address.checksum)}')
            return UniswapV2PoolLPPosition(
                token0=token0,
                token1=token1,
                token0_amount=token0_balance_scaled / total_supply_scaled,
                token1_amount=token1_balance_scaled / total_supply_scaled,
                token0_reserve=token0_balance_scaled,
                token1_reserve=token1_balance_scaled,
                total_supply_scaled=total_supply_scaled,
            )

        raise ModelDataError(f'Contract {input.address} is not a UniswapV2Pair')
