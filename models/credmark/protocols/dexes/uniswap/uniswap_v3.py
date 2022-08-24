# pylint: disable=locally-disabled, unused-import

from collections import namedtuple
from math import log

import numpy as np
import numpy.linalg as nplin
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (Address, Contract, Contracts, Network, Price,
                                Some, Token)
from credmark.cmf.types.block_number import BlockNumberOutOfRangeError
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO, EmptyInput
from models.credmark.tokens.token import fix_erc20_token
from models.dtos.price import (DexPricePoolInput, DexPriceTokenInput,
                               PoolPriceInfo)
from models.tmp_abi_lookup import UNISWAP_V3_POOL_ABI
from scipy.optimize import minimize
from web3.exceptions import BadFunctionCallOutput

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


@Model.describe(slug='uniswap-v3.get-pools',
                version='1.5',
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                input=Token,
                output=Contracts)
class UniswapV3GetPools(Model):
    UNISWAP_V3_FACTORY_ADDRESS = {
        Network.Mainnet: "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    }

    def run(self, input: Token) -> Contracts:
        fees = [100, 500, 3000, 10000]
        try:
            primary_tokens = self.context.run_model('dex.primary-tokens',
                                                    input=EmptyInput(),
                                                    return_type=Some[Address],
                                                    local=True).some

            # For stablecoins, exclude use WETH pools.
            # In those pools, the price for stablecoins in those pools will always be 1.
            weth_address = Token('WETH').address
            if input.address not in primary_tokens and input.address != weth_address:
                primary_tokens.append(weth_address)

            addr = self.UNISWAP_V3_FACTORY_ADDRESS[self.context.network]
            uniswap_factory = Contract(address=addr)
            pools = []
            for fee in fees:
                for primary_token in primary_tokens:
                    if input.address == primary_token:
                        continue
                    if input.address.to_int() < primary_token.to_int():
                        token_pair = input.address.checksum, primary_token.checksum
                    else:
                        token_pair = primary_token.checksum, input.address.checksum
                    pool = uniswap_factory.functions.getPool(*token_pair, fee).call()
                    if not Address(pool).is_null():
                        cc = Contract(address=pool, abi=UNISWAP_V3_POOL_ABI)
                        try:
                            _ = cc.abi
                        except BlockNumberOutOfRangeError:
                            continue
                        except ModelDataError:
                            pass
                        pools.append(cc)

            return Contracts(contracts=pools)
        except (BadFunctionCallOutput, BlockNumberOutOfRangeError):
            return Contracts(contracts=[])


Tick = namedtuple("Tick",
                  ("liquidityGross liquidityNet feeGrowthOutside0X128 feeGrowthOutside1X128 "
                   "tickCumulativeOutside secondsPerLiquidityOutsideX128 secondsOutside "
                   "initialized"))


# pylint:disable=invalid-name
# out-of-range
def out_of_range(liquidity, sb, sa):
    amount0 = int(liquidity * (sb - sa) / (sb * sa))
    amount1 = int(liquidity * (sb - sa))
    return amount0, amount1


def in_range(liquidity, sb, sa, sp):
    amount0 = int(liquidity * (sb - sp) / (sb * sp))
    amount1 = int(liquidity * (sp - sa))
    return amount0, amount1


@Model.describe(slug='uniswap-v3.get-pool-info',
                version='1.10',
                display_name='Uniswap v3 Token Pools Info',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                input=Contract,
                output=UniswapV3PoolInfo)
class UniswapV3GetPoolInfo(Model):
    UNISWAP_BASE = 1.0001
    # v3/TickMath.sol
    MIN_TICK = -887272
    MAX_TICK = 887272

    # tick spacing
    # 1
    # 10
    # 60
    # 200

    def tick_to_price(self, tick):
        return pow(self.UNISWAP_BASE, tick)

    def price_to_tick(self, price):
        return log(price) / log(self.UNISWAP_BASE)

    def run(self, input: Contract) -> UniswapV3PoolInfo:
        #pylint:disable=locally-disabled, too-many-locals
        primary_tokens = self.context.run_model('dex.primary-tokens',
                                                input=EmptyInput(),
                                                return_type=Some[Address],
                                                local=True).some

        # Count WETH-pool as primary pool
        primary_tokens.append(Token('WETH').address)

        try:
            _ = input.abi
        except ModelDataError:
            input = Contract(address=input.address, abi=UNISWAP_V3_POOL_ABI)

        pool = input

        slot0 = pool.functions.slot0().call()
        sqrtPriceX96 = slot0[0]
        current_tick = slot0[1]

        fee = pool.functions.fee().call()
        ticks = Tick(*pool.functions.ticks(current_tick).call())
        _liquidityGross = ticks.liquidityGross
        _liquidityNet = ticks.liquidityNet

        token0_addr = pool.functions.token0().call()
        token1_addr = pool.functions.token1().call()
        token0 = Token(address=Address(token0_addr).checksum)
        token1 = Token(address=Address(token1_addr).checksum)
        token0 = fix_erc20_token(token0)
        token1 = fix_erc20_token(token1)
        token0_symbol = token0.symbol
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

        # 1. Liquidity for virutal amount of x and y
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
        p_current = self.tick_to_price(current_tick)

        # lets say currentTick is 5 , then Liquiditys are like this:
        #             2  -> Liquidity = Liquidity at tick3  - LiquidityNet at tick2
        #             3  -> Liquidity = Liquidity at tick4  - LiquidityNet at tick3
        #             4  -> Liquidity = Liquidity at tick5  - LiquidityNet at tick4
        # currentTick 5  -> Liquidity = pools Liquidity
        #             6  -> Liquidity = Liquidity at tick5  + LiquidityNet at tick6
        #             7  -> Liquidity = Liquidity at tick6  + LiquidityNet at tick7

        # Compute square roots of prices corresponding to the bottom and top ticks
        sa = self.tick_to_price(tick_bottom / 2)
        sb = self.tick_to_price(tick_top / 2)
        sp = p_current ** 0.5

        # Liquidity in 1 tick
        in_tick_amount0, in_tick_amount1 = in_range(liquidity, sb, sa, sp)

        # Scale the amounts to the token's unit
        adjusted_in_tick_amount0 = token0.scaled(in_tick_amount0)
        adjusted_in_tick_amount1 = token1.scaled(in_tick_amount1)

        lower_tick_info = Tick(*pool.functions.ticks(tick_bottom).call())
        lower_liquidityNet = lower_tick_info.liquidityNet
        upper_tick_info = Tick(*pool.functions.ticks(tick_top).call())
        upper_liquidityNet = upper_tick_info.liquidityNet

        saa = self.tick_to_price((tick_bottom-tick_spacing) / 2)
        sbb = self.tick_to_price((tick_top+tick_spacing) / 2)

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

        # assert np.isclose(
        #     (in_tick_amount0 + liquidity / sb) * (in_tick_amount1 + liquidity * sa),
        #    float(liquidity * liquidity))

        ratio_left = (in_tick_amount0 + liquidity / sb) * (in_tick_amount1 + liquidity * sa)
        ratio_right = float(liquidity * liquidity)

        try:
            assert np.isclose(ratio_left, ratio_right)
        except AssertionError:
            compare_ratio = ratio_left/ratio_right
            assert 0.99 < compare_ratio < 1.01

        sa_p = self.tick_to_price((current_tick - 1) / 2)
        sb_p = self.tick_to_price((current_tick + 1) / 2)

        # Liquidity in 1 tick
        if current_tick == tick_bottom:
            __tick1_amount0, tick1_amount1 = out_of_range(liquidity-_liquidityNet, sp, sa_p)
            tick1_amount0, __tick1_amount1 = in_range(liquidity, sb_p, sp, sp)
        elif current_tick == tick_top:
            __tick1_amount0, tick1_amount1 = in_range(liquidity, sp, sa_p, sp)
            tick1_amount0, __tick1_amount1 = out_of_range(liquidity+_liquidityNet, sb_p, sp)
        else:
            tick1_amount0, tick1_amount1 = in_range(liquidity, sb_p, sa_p, sp)
            # equivalent to
            # _tick1_amount0 == 0, _tick1_amount1 = in_range(liquidity, sp, sa_p, sp)
            # tick1_amount0, _tick1_amount1 == 0 = in_range(liquidity, sb_p, sp, sp)

        one_tick_liquidity0_ori = token0.scaled(tick1_amount0)
        one_tick_liquidity1_ori = token1.scaled(tick1_amount1)

        # We match the two tokens' liquidity for the minimal available, a fix for the iliquid pools.
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

        scale_multiplier = (10 ** (token0.decimals - token1.decimals))
        tick_price0 = 1.0001 ** current_tick * scale_multiplier

        _tick_price_bottom0 = 1.0001 ** tick_bottom * scale_multiplier
        _tick_price_top0 = 1.0001 ** tick_top * scale_multiplier

        ratio_price0 = sqrtPriceX96 * sqrtPriceX96 / (2 ** 192) * scale_multiplier

        tick_price1 = 1/tick_price0
        ratio_price1 = 1/ratio_price0

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
                version='1.3',
                display_name='Uniswap v3 Token Pools Info for Price',
                description='Extract price information for a UniV3 pool',
                category='protocol',
                subcategory='uniswap-v3',
                input=DexPricePoolInput,
                output=PoolPriceInfo)
class UniswapV3GetTokenPoolPriceInfo(Model):
    def run(self, input: DexPricePoolInput) -> PoolPriceInfo:
        info = self.context.run_model('uniswap-v3.get-pool-info',
                                      input=input,
                                      return_type=UniswapV3PoolInfo,
                                      local=True)

        tick_price0 = info.tick_price0
        one_tick_liquidity0 = info.one_tick_liquidity0

        tick_price1 = 1/tick_price0
        one_tick_liquidity1 = info.one_tick_liquidity1

        ref_price = 1.0
        weth_address = Token('WETH').address

        # 1. If both are stablecoins (non-WETH): use the relative ratio between each other.
        #    So we are able to support depegged SB (like USDT in May 13th 2022)
        # 2. If SB-WETH: use SB to price WETH
        # 3. If WETH-X: use WETH to price
        # 4. If SB-X: use SB to price

        if info.is_primary_pool:
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
                    raise ModelRunError('Can not retriev price for WETH')

        pool_price_info = PoolPriceInfo(src=input.price_slug,
                                        price0=tick_price0,
                                        price1=tick_price1,
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
                version='1.15',
                display_name='Uniswap v3 Token Pools Price ',
                description='Gather price and liquidity information from pools',
                category='protocol',
                subcategory='uniswap-v3',
                input=DexPriceTokenInput,
                output=Some[PoolPriceInfo])
class UniswapV3GetTokenPoolInfo(Model):
    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        pools = self.context.run_model('uniswap-v3.get-pools',
                                       input,
                                       return_type=Contracts,
                                       local=True)

        model_slug = 'uniswap-v3.get-pool-price-info'
        model_inputs = [DexPricePoolInput(address=pool.address,
                                          price_slug='uniswap-v3.get-weighted-price',
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
                    raise ModelRunError('compose.map-inputs: output/error cannot be both None')
            return infos

        def _use_for(local):
            infos = []
            for minput in model_inputs:
                pi = self.context.run_model(model_slug, minput, return_type=PoolPriceInfo,
                                            local=local)
                infos.append(pi)
            return infos

        infos = _use_for(local=True)

        return Some[PoolPriceInfo](some=infos)


class TokenPrice(Price):
    address: Address
    symbol: str


@Model.describe(slug='uniswap-v3.get-weighted-price-primary-tokens',
                version='0.1',
                display_name='Uniswap V3 - Obtain value of stable coins',
                description='Derive value of each coin from their 2-pools',
                category='protocol',
                subcategory='dex',
                tags=['uniswap-v2', 'uniswap-v3', 'sushiswap', 'stablecoin'],
                output=Some[TokenPrice])
class DexPrimaryTokensUniV3(Model):
    def run(self, _) -> Some[TokenPrice]:
        primary_tokens = self.context.run_model('dex.primary-tokens',
                                                input=EmptyInput(),
                                                return_type=Some[Address],
                                                local=True).some

        # tokens = primary_tokens[:2]
        # tokens = primary_tokens[1:]
        # tokens = [primary_tokens[0], primary_tokens[2]]
        tokens = primary_tokens

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
                      price_t=lambda x, addr=str(tok_addr): x.price0.where(
                          x.token0_address == addr,
                          x.price1),
                      tick_liquidity_t=lambda x, addr=str(tok_addr): x.one_tick_liquidity0.where(
                          x.token0_address == addr,
                          x.one_tick_liquidity1),
                      other_token_t=lambda x, addr=str(tok_addr): x.token0_address.where(
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
                       .price_x_liq
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
        except Exception as _err:
            pass

        # try linear system
        b = np.zeros(shape=(len(tokens), 1))
        try:
            _lin_result = nplin.solve(a, b)
        except Exception as _err:
            pass

        # (pd.concat(all_dfs)
        # .to_csv(f'tmp/primary_{self.context.block_number}_{len(primary_tokens)}.csv'))

        return Some(some=[TokenPrice(price=v, src=self.slug, address=k, symbol=Token(k).symbol)
                          for k, v in prices.items()])
