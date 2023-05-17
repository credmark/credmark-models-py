# pylint: disable=locally-disabled, invalid-name, line-too-long

import math

import numpy as np
import numpy.linalg as nplin
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import Address, Contract, Contracts, Price, Some, Token
from credmark.cmf.types.block_number import BlockNumberOutOfRangeError
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO, EmptyInput
from scipy.optimize import minimize
from web3.exceptions import BadFunctionCallOutput, ContractLogicError

from models.credmark.price.dex import get_primary_token_tuples
from models.credmark.protocols.dexes.uniswap.constant import (
    V3_FACTORY_ADDRESS,
    V3_POOL_FEES,
    V3_TICK,
)
from models.credmark.protocols.dexes.uniswap.univ3_math import (
    in_range,
    out_of_range,
    tick_to_price,
)
from models.dtos.pool import PoolPriceInfo
from models.dtos.price import DexPricePoolInput, DexPriceTokenInput
from models.tmp_abi_lookup import UNISWAP_V3_POOL_ABI

np.seterr(all='raise')


class UniswapV3PoolInfo(DTO):
    address: Address
    sqrtPriceX96: float
    current_tick: int
    tick_bottom: int
    tick_top: int
    observationIndex: int
    observationCardinality: int
    observationCardinalityNext: int
    feeProtocol: int
    unlocked: bool
    liquidity: float
    full_tick_liquidity0: float
    full_tick_liquidity1: float
    lower_tick_liquidity0: float
    lower_tick_liquidity1: float
    upper_tick_liquidity0: float
    upper_tick_liquidity1: float
    one_tick_liquidity0_ori: float
    one_tick_liquidity1_ori: float
    one_tick_liquidity0: float
    one_tick_liquidity1: float
    virtual_liquidity0: float
    virtual_liquidity1: float
    fee: int
    token0: Token
    token1: Token
    token0_balance: float
    token1_balance: float
    token0_symbol: str
    token1_symbol: str
    tick_spacing: int
    sqrt_current_price: float
    sqrt_lower_price: float
    sqrt_upper_price: float
    ratio_price0: float
    ratio_price1: float
    tick_price0: float
    tick_price1: float
    is_primary_pool: bool
    primary_address: Address


def get_uniswap_v3_pools_by_pair(_context, factory_addr: Address, token_pairs) -> Contracts:
    uniswap_factory = Contract(address=factory_addr)
    pools = []
    for token_pair in token_pairs:
        for fee in V3_POOL_FEES:
            pool_addr = uniswap_factory.functions.getPool(
                *token_pair, fee).call()
            if not Address(pool_addr).is_null():
                cc = Contract(address=pool_addr).set_abi(
                    abi=UNISWAP_V3_POOL_ABI, set_loaded=True)
                try:
                    _ = cc.abi
                    _ = cc.functions.token0().call()
                except BlockNumberOutOfRangeError:
                    continue  # before its creation
                except ModelDataError:
                    pass

                pools.append(cc)
    return Contracts(contracts=pools)


@Model.describe(slug='uniswap-v3.get-pools',
                version='1.6',
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                input=Token,
                output=Contracts)
class UniswapV3GetPools(Model):
    def run(self, input: Token) -> Contracts:
        try:
            token_pairs = get_primary_token_tuples(self.context, input.address)
            return get_uniswap_v3_pools_by_pair(self.context, V3_FACTORY_ADDRESS[self.context.network], token_pairs)
        except (BadFunctionCallOutput, BlockNumberOutOfRangeError):
            return Contracts(contracts=[])


@Model.describe(slug='uniswap-v3.get-ring0-ref-price',
                version='0.6',
                display_name='Uniswap v3 Ring0 Reference Price',
                description='The Uniswap v3 pools that support the ring0 tokens',
                category='protocol',
                subcategory='uniswap-v3',
                output=dict)
class UniswapV3GetRing0RefPrice(Model):
    WEIGHT_POWER = 4.0

    def run(self, _: EmptyInput) -> dict:
        factory_addr = V3_FACTORY_ADDRESS[self.context.network]

        ring0_tokens = self.context.run_model(
            'dex.ring0-tokens', {}, return_type=Some[Address], local=True).some

        ratios = {}
        valid_tokens = set()
        missing_relations = []
        for token0_address in ring0_tokens:
            for token1_address in ring0_tokens:
                # Uniswap builds pools with token0 < token1
                if token0_address.to_int() >= token1_address.to_int():
                    continue
                token_pairs = [(token0_address, token1_address)]
                pools = get_uniswap_v3_pools_by_pair(
                    self.context, factory_addr, token_pairs)

                if len(pools.contracts) == 0:
                    missing_relations.extend(
                        [(token0_address, token1_address), (token1_address, token0_address)])
                    continue

                pools_info = [self.context.run_model(
                    'uniswap-v3.get-pool-info', input=p) for p in pools.contracts]
                pools_info_sel = [[p.address,
                                   *[pi[k] for k in ['ratio_price0', 'one_tick_liquidity0', 'ratio_price1', 'one_tick_liquidity1']]]
                                  for p, pi in zip(pools.contracts, pools_info, strict=True)]

                pool_info = pd.DataFrame(data=pools_info_sel,
                                         columns=['address', 'ratio_price0', 'one_tick_liquidity0', 'ratio_price1', 'one_tick_liquidity1'])

                if pool_info.shape[0] > 1:
                    ratio0 = (pool_info.ratio_price0 * pool_info.one_tick_liquidity0 ** self.WEIGHT_POWER).sum() / \
                        (pool_info.one_tick_liquidity0 ** self.WEIGHT_POWER).sum()
                    ratio1 = (pool_info.ratio_price1 * pool_info.one_tick_liquidity1 ** self.WEIGHT_POWER).sum() / \
                        (pool_info.one_tick_liquidity1 ** self.WEIGHT_POWER).sum()
                else:
                    ratio0 = pool_info['ratio_price0'][0]
                    ratio1 = pool_info['ratio_price1'][0]

                ratios[(token0_address, token1_address)] = ratio0
                ratios[(token1_address, token0_address)] = ratio1
                valid_tokens.add(token0_address)
                valid_tokens.add(token1_address)

        valid_tokens_list = list(valid_tokens)
        if len(valid_tokens_list) == len(ring0_tokens):
            try:
                assert len(ring0_tokens) == 3
            except AssertionError:
                raise ModelDataError(
                    'Not implemented Calculate for missing relations for more than 3 ring0 tokens') from None

            for token0_address, token1_address in missing_relations:
                other_token = list(set(ring0_tokens) -
                                   {token0_address, token1_address})[0]
                ratios[(token0_address, token1_address)] = ratios[(token0_address, other_token)] * \
                    ratios[(other_token, token1_address)]

        candidate_prices = []
        for pivot_token in valid_tokens_list:
            candidate_price = np.array([ratios[(token, pivot_token)]
                                        if token != pivot_token else 1
                                        for token in valid_tokens_list])
            candidate_prices.append(
                ((candidate_price.max() / candidate_price.min(), -candidate_price.max(), candidate_price.min()),
                 candidate_price / candidate_price.max()))

        ring0_token_symbols = [Token(t).symbol for t in ring0_tokens]

        return dict(zip(
            valid_tokens_list,
            sorted(candidate_prices, key=lambda x: x[0])[0][1], strict=True)) | dict(zip(ring0_token_symbols, ring0_tokens, strict=True))


@Model.describe(slug='uniswap-v3.get-pools-ledger',
                version='1.7',
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                input=Token,
                output=Contracts)
class UniswapV3GetPoolsLedger(Model):
    def run(self, input: Token) -> Contracts:
        factory = Contract(V3_FACTORY_ADDRESS[self.context.network])
        input_address = input.address
        token_pairs = get_primary_token_tuples(self.context, input_address)
        token_pairs_fee = [(*tp, V3_POOL_FEES) for tp in token_pairs]

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


@Model.describe(slug='uniswap-v3.get-all-pools',
                version='1.6',
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                output=Contracts)
class UniswapV3AllPools(Model):
    def run(self, _: EmptyInput) -> Contracts:
        deployer = Contract(V3_FACTORY_ADDRESS[self.context.network])

        with deployer.ledger.events.PoolCreated as q:
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

        all_df = pd.concat(df_ts)
        all_addresses = set(all_df.evt_pool.tolist())

        return Contracts(contracts=[Contract(addr) for addr in all_addresses])


@Model.describe(slug='uniswap-v3.get-pool-info',
                version='1.15',
                display_name='Uniswap v3 Token Pools Info',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                input=Contract,
                output=UniswapV3PoolInfo)
class UniswapV3GetPoolInfo(Model):

    # tick spacing
    # 1
    # 10
    # 60
    # 200

    def run(self, input: Contract) -> UniswapV3PoolInfo:
        # pylint:disable=locally-disabled, too-many-locals, too-many-statements
        primary_tokens = self.context.run_model(
            'dex.ring0-tokens', {}, return_type=Some[Address], local=True).some

        # Count WETH-pool as primary pool
        primary_tokens.append(Token('WETH').address)

        try:
            _ = input.abi
        except ModelDataError:
            input = Contract(address=input.address).set_abi(
                UNISWAP_V3_POOL_ABI, set_loaded=True)

        pool = input

        slot0 = pool.functions.slot0().call()
        sqrtPriceX96 = slot0[0]
        current_tick = slot0[1]

        fee = pool.functions.fee().call()
        ticks = V3_TICK(*pool.functions.ticks(current_tick).call())
        _liquidityGross = ticks.liquidityGross
        _liquidityNet = ticks.liquidityNet

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

        is_primary_pool = token0.address in primary_tokens and token1.address in primary_tokens
        if token0.address in primary_tokens:
            primary_address = token0.address
        elif token1.address in primary_tokens:
            primary_address = token1.address
        else:
            primary_address = Address.null()

        token0_balance = token0.balance_of_scaled(input.address.checksum)
        token1_balance = token1.balance_of_scaled(input.address.checksum)

        # 1. Liquidity for virtual amount of x and y
        liquidity = pool.functions.liquidity().call()

        # 2. To calculate liquidity within the range of tick
        # Get the current tick and tick_spacing for the pool (set based on the fee)
        tick_spacing = pool.functions.tickSpacing().call()

        # Compute the tick range near the current tick
        tick_bottom = current_tick // tick_spacing * tick_spacing
        tick_top = tick_bottom + tick_spacing
        assert tick_bottom <= current_tick <= tick_top

        # Compute the current price
        # p_current = 1.0001 ** tick
        # tick = log(p_current) / log(1.0001)
        p_current = tick_to_price(current_tick)

        # Let's say currentTick is 5, then liquidity profile looks like this:
        #             2  -> Liquidity = Liquidity at tick3  - LiquidityNet at tick2
        #             3  -> Liquidity = Liquidity at tick4  - LiquidityNet at tick3
        #             4  -> Liquidity = Liquidity at tick5  - LiquidityNet at tick4
        # currentTick 5  -> Liquidity = pools Liquidity
        #             6  -> Liquidity = Liquidity at tick5  + LiquidityNet at tick6
        #             7  -> Liquidity = Liquidity at tick6  + LiquidityNet at tick7

        # Compute square roots of prices corresponding to the bottom and top ticks
        sa = tick_to_price(tick_bottom / 2)
        sb = tick_to_price(tick_top / 2)
        sp = p_current ** 0.5

        # Liquidity in 1 tick
        in_tick_amount0, in_tick_amount1 = in_range(liquidity, sb, sa, sp)

        # Scale the amounts to the token's unit
        adjusted_in_tick_amount0 = token0.scaled(in_tick_amount0)
        adjusted_in_tick_amount1 = token1.scaled(in_tick_amount1)

        lower_tick_info = V3_TICK(*pool.functions.ticks(tick_bottom).call())
        lower_liquidityNet = lower_tick_info.liquidityNet
        upper_tick_info = V3_TICK(*pool.functions.ticks(tick_top).call())
        upper_liquidityNet = upper_tick_info.liquidityNet

        saa = tick_to_price((tick_bottom-tick_spacing) / 2)
        sbb = tick_to_price((tick_top+tick_spacing) / 2)

        lower_tick_amount0, lower_tick_amount1 = out_of_range(
            liquidity-lower_liquidityNet, sa, saa)
        upper_tick_amount0, upper_tick_amount1 = out_of_range(
            liquidity+upper_liquidityNet, sbb, sb)

        lower_tick_amount0 = token0.scaled(lower_tick_amount0)
        lower_tick_amount1 = token1.scaled(lower_tick_amount1)
        upper_tick_amount0 = token0.scaled(upper_tick_amount0)
        upper_tick_amount1 = token1.scaled(upper_tick_amount1)

        # Below shall be equal for the tick liquidity
        # Reference: UniswapV3 whitepaper Eq. 2.2

        # Disabled for some pools with small quantity of in_tick tokens.
        # Example:
        # uniswap-v3.get-pool-info -b 15301016
        # -i '{"address":"0x5c0f97e0ed70e0163b799533ce142f650e39a3e6",
        #      "price_slug": "uniswap-v3.get-weighted-price"}'

        # assert math.isclose(
        #     (in_tick_amount0 + liquidity / sb) * (in_tick_amount1 + liquidity * sa),
        #    float(liquidity * liquidity))

        ratio_left = (in_tick_amount0 + liquidity / sb) * (in_tick_amount1 + liquidity * sa)
        ratio_right = float(liquidity * liquidity)

        try:
            assert math.isclose(ratio_left, ratio_right)
        except AssertionError:
            compare_ratio = ratio_left/ratio_right
            assert 0.99 < compare_ratio < 1.01

        sa_p = tick_to_price((current_tick - 1) / 2)
        sb_p = tick_to_price((current_tick + 1) / 2)

        # Liquidity in 1 tick
        if current_tick == tick_bottom:
            __tick1_amount0, tick1_amount1 = out_of_range(
                liquidity-_liquidityNet, sp, sa_p)
            tick1_amount0, __tick1_amount1 = in_range(liquidity, sb_p, sp, sp)
        elif current_tick == tick_top:
            __tick1_amount0, tick1_amount1 = in_range(liquidity, sp, sa_p, sp)
            tick1_amount0, __tick1_amount1 = out_of_range(
                liquidity+_liquidityNet, sb_p, sp)
        else:
            tick1_amount0, tick1_amount1 = in_range(liquidity, sb_p, sa_p, sp)
            # equivalent to
            # _tick1_amount0 == 0, _tick1_amount1 = in_range(liquidity, sp, sa_p, sp)
            # tick1_amount0, _tick1_amount1 == 0 = in_range(liquidity, sb_p, sp, sp)

        one_tick_liquidity0_ori = token0.scaled(tick1_amount0)
        one_tick_liquidity1_ori = token1.scaled(tick1_amount1)

        # We match the two tokens' liquidity for the minimal available, a fix for the illiquid pools.
        tick1_amount0_adj = min(tick1_amount0, tick1_amount1 / sp / sp)
        tick1_amount1_adj = min(tick1_amount0 * sp * sp, tick1_amount1)

        one_tick_liquidity0_adj = token0.scaled(tick1_amount0_adj)
        one_tick_liquidity1_adj = token1.scaled(tick1_amount1_adj)

        # Combined liquidity
        # https://uniswap.org/blog/uniswap-v3-dominance
        # Appendix B: methodology
        _tick_liquidity_combined0 = in_tick_amount0 + in_tick_amount1 / p_current
        _tick_liquidity_combined1 = _tick_liquidity_combined0 * p_current

        # Calculate the virtual liquidity
        # Reference: UniswapV3 whitepaper Eq. 2.1
        virtual_x = token0.scaled(liquidity / sp)
        virtual_y = token1.scaled(liquidity * sp)

        scale_multiplier = 10 ** (token0.decimals - token1.decimals)
        tick_price0 = tick_to_price(current_tick) * scale_multiplier
        if math.isclose(0, tick_price0):
            tick_price1 = 0
        else:
            tick_price1 = 1/tick_price0

        _tick_price_bottom0 = tick_to_price(tick_bottom) * scale_multiplier
        _tick_price_top0 = tick_to_price(tick_top) * scale_multiplier

        ratio_price0 = sqrtPriceX96 * sqrtPriceX96 / (2 ** 192) * scale_multiplier
        try:
            ratio_price1 = 1/ratio_price0
        except (FloatingPointError, ZeroDivisionError):
            ratio_price0 = 0
            ratio_price1 = 0

        return UniswapV3PoolInfo(
            address=input.address,
            sqrtPriceX96=sqrtPriceX96,
            current_tick=current_tick,
            tick_bottom=tick_bottom,
            tick_top=tick_top,
            observationIndex=slot0[2],
            observationCardinality=slot0[3],
            observationCardinalityNext=slot0[4],
            feeProtocol=slot0[5],
            unlocked=slot0[6],
            token0=token0,
            token1=token1,
            token0_balance=token0_balance,
            token1_balance=token1_balance,
            token0_symbol=token0_symbol,
            token1_symbol=token1_symbol,
            liquidity=liquidity,
            full_tick_liquidity0=adjusted_in_tick_amount0,
            full_tick_liquidity1=adjusted_in_tick_amount1,
            lower_tick_liquidity0=lower_tick_amount0,
            lower_tick_liquidity1=lower_tick_amount1,
            upper_tick_liquidity0=upper_tick_amount0,
            upper_tick_liquidity1=upper_tick_amount1,
            one_tick_liquidity0_ori=one_tick_liquidity0_ori,
            one_tick_liquidity1_ori=one_tick_liquidity1_ori,
            one_tick_liquidity0=one_tick_liquidity0_adj,
            one_tick_liquidity1=one_tick_liquidity1_adj,
            fee=fee,
            virtual_liquidity0=virtual_x,
            virtual_liquidity1=virtual_y,
            tick_spacing=tick_spacing,
            sqrt_current_price=sp,
            sqrt_lower_price=sa,
            sqrt_upper_price=sb,
            tick_price0=tick_price0,
            tick_price1=tick_price1,
            ratio_price0=ratio_price0,
            ratio_price1=ratio_price1,
            is_primary_pool=is_primary_pool,
            primary_address=primary_address)


@Model.describe(slug='uniswap-v3.get-pool-price-info',
                version='1.8',
                display_name='Uniswap v3 Token Pools Info for Price',
                description='Extract price information for a UniV3 pool',
                category='protocol',
                subcategory='uniswap-v3',
                input=DexPricePoolInput,
                output=PoolPriceInfo)
class UniswapV3GetTokenPoolPriceInfo(Model):
    def run(self, input: DexPricePoolInput) -> PoolPriceInfo:
        info = self.context.run_model(
            'uniswap-v3.get-pool-info', input=Contract(**input.dict()),
            return_type=UniswapV3PoolInfo, local=True)

        ratio_price0 = info.ratio_price0
        ratio_price1 = info.ratio_price1

        # Use reserve to cap the one tick liquidity
        # Example: 0xf1d2172d6c6051960a289e0d7dca9e16b65bfc64, around block 17272381, May 16 2023 8pm GMT+8

        if info.token0_balance < info.one_tick_liquidity0 or info.token1_balance < info.one_tick_liquidity1:
            balance2liquidity0_ratio = info.token0_balance / info.one_tick_liquidity0
            balance2liquidity1_ratio = info.token1_balance / info.one_tick_liquidity1
            if balance2liquidity0_ratio < balance2liquidity1_ratio:
                one_tick_liquidity0 = info.token0_balance
                one_tick_liquidity1 = balance2liquidity0_ratio * info.one_tick_liquidity1
            else:
                one_tick_liquidity0 = balance2liquidity1_ratio * info.one_tick_liquidity0
                one_tick_liquidity1 = info.token1_balance
        else:
            one_tick_liquidity0 = info.one_tick_liquidity0
            one_tick_liquidity1 = info.one_tick_liquidity1

        ref_price = 1.0
        weth_address = Token('WETH').address

        # 1. If both are stablecoins (non-WETH): use the relative ratio between each other.
        #    So we are able to support de-pegged stablecoin (like USDT in May 13th 2022)
        # 2. If SB-WETH: use SB to price WETH
        # 3. If WETH-X: use WETH to price
        # 4. If SB-X: use SB to price

        if info.is_primary_pool:
            if weth_address not in [info.token0.address, info.token1.address]:
                if input.ref_price_slug is not None:
                    ref_price_ring0 = self.context.run_model(
                        input.ref_price_slug, {}, return_type=dict)
                    # Use the reference price to scale the tick price. Note the cross-reference is used here.
                    # token0 = tick_price0 * token1 = tick_price0 * ref_price of token1
                    ratio_price0 *= ref_price_ring0[info.token1.address]
                    ratio_price1 *= ref_price_ring0[info.token0.address]

            if info.token0.address == weth_address:
                ref_price = self.context.run_model(
                    slug=input.price_slug,
                    input=DexPriceTokenInput(
                        **info.token1.dict(),
                        weight_power=input.weight_power,
                        debug=input.debug),
                    return_type=Price,
                    local=True).price

            if info.token1.address == weth_address:
                ref_price = self.context.run_model(
                    slug=input.price_slug,
                    input=DexPriceTokenInput(
                        **info.token0.dict(),
                        weight_power=input.weight_power,
                        debug=input.debug),
                    return_type=Price,
                    local=True).price
        else:
            if not info.primary_address.is_null():
                ref_price = self.context.run_model(
                    slug=input.price_slug,
                    input=DexPriceTokenInput(
                        address=info.primary_address,
                        weight_power=input.weight_power,
                        debug=input.debug),
                    return_type=Price,
                    local=True).price
                if ref_price is None:
                    raise ModelRunError('Can not retrieve price for WETH')

        pool_price_info = PoolPriceInfo(src=input.price_slug,
                                        price0=ratio_price0,
                                        price1=ratio_price1,
                                        one_tick_liquidity0=one_tick_liquidity0,
                                        one_tick_liquidity1=one_tick_liquidity1,
                                        full_tick_liquidity0=info.full_tick_liquidity0,
                                        full_tick_liquidity1=info.full_tick_liquidity1,
                                        token0_address=info.token0.address,
                                        token1_address=info.token1.address,
                                        token0_symbol=info.token0_symbol,
                                        token1_symbol=info.token1_symbol,
                                        ref_price=ref_price,
                                        pool_address=input.address,
                                        tick_spacing=info.tick_spacing)
        return pool_price_info


@Model.describe(slug='uniswap-v3.get-pool-info-token-price',
                version='1.18',
                display_name='Uniswap v3 Token Pools Price ',
                description='Gather price and liquidity information from pools',
                category='protocol',
                subcategory='uniswap-v3',
                input=DexPriceTokenInput,
                output=Some[PoolPriceInfo])
class UniswapV3GetTokenPoolInfo(Model):
    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        pools = self.context.run_model(
            'uniswap-v3.get-pools', input, return_type=Contracts, local=True)

        model_slug = 'uniswap-v3.get-pool-price-info'
        model_inputs = [DexPricePoolInput(address=pool.address,
                                          price_slug='uniswap-v3.get-weighted-price',
                                          ref_price_slug='uniswap-v3.get-ring0-ref-price',
                                          weight_power=input.weight_power,
                                          debug=input.debug)
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


class TokenPrice(Price):
    address: Address
    symbol: str


@Model.describe(slug='uniswap-v3.get-weighted-price-primary-tokens',
                version='0.3',
                display_name='Uniswap V3 - Obtain value of stable coins',
                description='Derive value of each coin from their 2-pools',
                category='protocol',
                subcategory='dex',
                tags=['uniswap-v2', 'uniswap-v3', 'sushiswap', 'stablecoin'],
                output=Some[TokenPrice])
class DexPrimaryTokensUniV3(Model):
    def run(self, _) -> Some[TokenPrice]:
        ring0_tokens = self.context.run_model(
            'dex.ring0-tokens', {}, return_type=Some[Address], local=True).some

        # tokens = primary_tokens[:2]
        # tokens = primary_tokens[1:]
        # tokens = [primary_tokens[0], primary_tokens[2]]
        tokens = ring0_tokens

        prices = {}
        weights = []
        all_dfs = []
        for tok_addr in tokens:
            pool_infos = self.context.run_model('uniswap-v3.get-pool-info-token-price',
                                                input={'address': tok_addr},
                                                return_type=Some[PoolPriceInfo])

            df = (pool_infos
                  .to_dataframe()
                  .assign(
                      token_t=tok_addr,
                      price_t=lambda x, addr=tok_addr: x.price0.where(
                          x.token0_address == addr,
                          x.price1),
                      tick_liquidity_t=lambda x, addr=tok_addr: x.one_tick_liquidity0.where(
                          x.token0_address == addr,
                          x.one_tick_liquidity1),
                      other_token_t=lambda x, addr=tok_addr: x.token0_address.where(
                          x.token0_address != addr,
                          x.token1_address))
                  .assign(tick_liquidity_norm=(lambda x:
                                               x.tick_liquidity_t / x.tick_liquidity_t.sum()))
                  .assign(price_x_liq=lambda x: x.price_t * x.tick_liquidity_norm)
                  .query('other_token_t.isin(@tokens)')
                  )

            all_dfs.append(df)

            weight = {}
            weight[tok_addr] = -df.tick_liquidity_norm.sum()
            weight |= (df
                       .groupby('other_token_t')
                       ["price_x_liq"]
                       .sum()
                       .to_dict())
            prices[tok_addr] = df.price_x_liq.sum()

            weights.append(weight)

        a = np.array([
            [w.get(tok_addr, 0) for tok_addr in tokens]
            for w in weights])

        def opt_target(x):
            return ((x - 1)**2).sum()
            # (a.dot(x)**2).sum() +

        # try optimize
        x0 = np.zeros(shape=(len(tokens), 1))
        try:
            _opt_result = minimize(opt_target, x0, method='nelder-mead',
                                   options={'xatol': 1e-8, 'disp': False})
        except Exception:
            pass

        # try linear system
        b = np.zeros(shape=(len(tokens), 1))
        try:
            _lin_result = nplin.solve(a, b)
        except Exception:
            pass

        # (pd.concat(all_dfs)
        # .to_csv(f'tmp/primary_{self.context.block_number}_{len(primary_tokens)}.csv'))

        return Some(some=[TokenPrice(price=v, src=self.slug, address=k, symbol=Token(k).symbol)
                          for k, v in prices.items()])
