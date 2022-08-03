import numpy as np
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (Address, Contract, Contracts, Network, Price,
                                Some, Token)
from credmark.cmf.types.token import get_token_from_configuration
from credmark.cmf.types.block_number import BlockNumberOutOfRangeError
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO
from models.credmark.tokens.token import fix_erc20_token
from models.dtos.price import DexPoolPriceInput, PoolPriceInfo
from models.tmp_abi_lookup import UNISWAP_V3_POOL_ABI
from web3.exceptions import BadFunctionCallOutput

np.seterr(all='raise')


class UniswapV3PoolInfo(DTO):
    address: Address
    sqrtPriceX96: float
    tick: int
    tick_bottom: int
    tick_top: int
    observationIndex: int
    observationCardinality: int
    observationCardinalityNext: int
    feeProtocol: int
    unlocked: bool
    liquidity: float
    tick_liquidity_token0: float
    tick_liquidity_token1: float
    virtual_liquidity_token0: float
    virtual_liquidity_token1: float
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


@Model.describe(slug='uniswap-v3.get-pools',
                version='1.4',
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                input=Token,
                output=Contracts)
class UniswapV3GetPoolsForToken(Model):
    PRIMARY_TOKENS = {
        Network.Mainnet:
        [Address(get_token_from_configuration('1', 'USDC')['address']),  # type: ignore
         Address(get_token_from_configuration('1', 'WETH')['address']),  # type: ignore
         Address(get_token_from_configuration('1', 'DAI')['address'])]  # type: ignore
    }

    UNISWAP_V3_FACTORY_ADDRESS = {
        Network.Mainnet: "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    }

    def run(self, input: Token) -> Contracts:
        fees = [100, 500, 3000, 10000]
        if self.context.chain_id != 1:
            return Contracts(contracts=[])

        try:
            addr = self.UNISWAP_V3_FACTORY_ADDRESS[self.context.network]
            uniswap_factory = Contract(address=addr)
            pools = []
            for fee in fees:
                for primary_token in self.PRIMARY_TOKENS[self.context.network]:
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


@ Model.describe(slug='uniswap-v3.get-pool-info',
                 version='1.8',
                 display_name='Uniswap v3 Token Pools Info',
                 description='The Uniswap v3 pools that support a token contract',
                 category='protocol',
                 subcategory='uniswap-v3',
                 input=Contract,
                 output=UniswapV3PoolInfo)
class UniswapV3GetPoolInfo(Model):
    UNISWAP_BASE = 1.0001

    def tick_to_price(self, tick):
        return pow(self.UNISWAP_BASE, tick)

    def run(self, input: Contract) -> UniswapV3PoolInfo:
        try:
            _ = input.abi
        except ModelDataError:
            input = Contract(address=input.address, abi=UNISWAP_V3_POOL_ABI)

        pool = input

        slot0 = pool.functions.slot0().call()
        sqrtPriceX96 = slot0[0]
        fee = pool.functions.fee().call()
        ticks = pool.functions.ticks(slot0[1]).call()
        _liquidityGross = ticks[0]
        _liquidityNet = ticks[1]

        token0_addr = pool.functions.token0().call()
        token1_addr = pool.functions.token1().call()
        token0 = Token(address=token0_addr)
        token1 = Token(address=token1_addr)
        token0 = fix_erc20_token(token0)
        token1 = fix_erc20_token(token1)
        token0_symbol = token0.symbol
        token1_symbol = token1.symbol

        token0_balance = token0.balance_of_scaled(input.address)
        token1_balance = token1.balance_of_scaled(input.address)

        # 1. Liquidity for virutal amount of x and y
        liquidity = pool.functions.liquidity().call()

        # 2. To calculate liquidity within the range of tick
        # Get the current tick and tick_spacing for the pool (set based on the fee)
        tick = slot0[1]
        tick_spacing = pool.functions.tickSpacing().call()
        # Compute the current price
        p_current = self.tick_to_price(tick)

        # Compute the tick range near the current tick
        tick_bottom = (np.floor(tick / tick_spacing)) * tick_spacing
        tick_top = tick_bottom + tick_spacing
        assert tick_bottom <= tick <= tick_top

        # Compute square roots of prices corresponding to the bottom and top ticks
        sa = self.tick_to_price(tick_bottom // 2)
        sb = self.tick_to_price(tick_top // 2)
        sp = p_current ** 0.5

        in_tick_amount0 = liquidity * (1 / sp - 1 / sb)
        in_tick_amount1 = liquidity * (sp - sa)

        # Scale the amounts to the token's unit
        adjusted_in_tick_amount0 = token0.scaled(in_tick_amount0)
        adjusted_in_tick_amount1 = token1.scaled(in_tick_amount1)

        # Below shall be equal for the tick liquidity
        # Reference: UniswapV3 whitepaper Eq. 2.2
        assert np.isclose(
            (in_tick_amount0 + liquidity / sb) * (in_tick_amount1 + liquidity * sa),
            float(liquidity * liquidity))

        # https://uniswap.org/blog/uniswap-v3-dominance
        # Appendix B: methodology
        _tick_liquidity_combined_in_0 = in_tick_amount0 + in_tick_amount1 / p_current
        _tick_liquidity_combined_in_1 = _tick_liquidity_combined_in_0 * p_current

        _tick_liquidity_combined_s_in_0 = token0.scaled(_tick_liquidity_combined_in_0)
        _tick_liquidity_combined_s_in_1 = token1.scaled(_tick_liquidity_combined_in_1)

        # Calculate the virtual liquidity
        # Reference: UniswapV3 whitepaper Eq. 2.1
        virtual_x = token0.scaled(liquidity / sp)
        virtual_y = token1.scaled(liquidity * sp)

        scale_multiplier = (10 ** (token0.decimals - token1.decimals))
        tick_price0 = 1.0001 ** tick * scale_multiplier
        ratio_price0 = sqrtPriceX96 * sqrtPriceX96 / (2 ** 192) * scale_multiplier

        tick_price1 = 1/tick_price0
        ratio_price1 = 1/ratio_price0

        return UniswapV3PoolInfo(
            address=input.address,
            sqrtPriceX96=sqrtPriceX96,
            tick=tick,
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
            tick_liquidity_token0=adjusted_in_tick_amount0,
            tick_liquidity_token1=adjusted_in_tick_amount1,
            fee=fee,
            virtual_liquidity_token0=virtual_x,
            virtual_liquidity_token1=virtual_y,
            tick_spacing=tick_spacing,
            sqrt_current_price=sp,
            sqrt_lower_price=sa,
            sqrt_upper_price=sb,
            tick_price0=tick_price0,
            tick_price1=tick_price1,
            ratio_price0=ratio_price0,
            ratio_price1=ratio_price1)


@ Model.describe(slug='uniswap-v3.get-pool-price-info',
                 version='0.8',
                 display_name='Uniswap v3 Token Pools Info for Price',
                 description='Extract price information for a UniV3 pool',
                 category='protocol',
                 subcategory='uniswap-v3',
                 input=DexPoolPriceInput,
                 output=PoolPriceInfo)
class UniswapV3GetTokenPoolPriceInfo(Model):
    def run(self, input: DexPoolPriceInput) -> PoolPriceInfo:
        info = self.context.run_model('uniswap-v3.get-pool-info',
                                      input=input.pool,
                                      return_type=UniswapV3PoolInfo,
                                      local=True)
        weth_price = None

        tick_price = info.tick_price0
        tick_liquidity = info.tick_liquidity_token0
        _virtual_liquidity = info.virtual_liquidity_token0
        ratio_price = info.ratio_price0

        _inverse = False
        if input.token.address == info.token1.address:
            tick_price = 1/tick_price
            ratio_price = 1/ratio_price
            _inverse = True
            tick_liquidity = info.tick_liquidity_token1
            _virtual_liquidity = info.virtual_liquidity_token1

        weth_multiplier = 1.0
        weth_address = Token('WETH').address
        if input.token.address != weth_address:
            if weth_address in (info.token1.address, info.token0.address):
                if weth_price is None:
                    weth_price = self.context.run_model(input.price_slug,
                                                        {'address': weth_address},
                                                        return_type=Price,
                                                        local=True)
                    if weth_price.price is None:
                        raise ModelRunError('Can not retriev price for WETH')

                    weth_price = weth_price.price
                weth_multiplier = weth_price

        tick_price *= weth_multiplier
        ratio_price *= weth_multiplier

        pool_price_info = PoolPriceInfo(src=self.slug,
                                        price=tick_price,
                                        tick_liquidity=tick_liquidity,
                                        token0_address=info.token0.address,
                                        token1_address=info.token1.address,
                                        token0_symbol=info.token0_symbol,
                                        token1_symbol=info.token1_symbol,
                                        weth_multiplier=weth_multiplier,
                                        pool_address=input.pool.address)
        return pool_price_info


@ Model.describe(slug='uniswap-v3.get-pool-info-token-price',
                 version='1.12',
                 display_name='Uniswap v3 Token Pools Price ',
                 description='Gather price and liquidity information from pools',
                 category='protocol',
                 subcategory='uniswap-v3',
                 input=Token,
                 output=Some[PoolPriceInfo])
class UniswapV3GetTokenPoolInfo(Model):
    def run(self, input: Token) -> Some[PoolPriceInfo]:
        pools = self.context.run_model('uniswap-v3.get-pools',
                                       input,
                                       return_type=Contracts,
                                       local=True)

        model_slug = 'uniswap-v3.get-pool-price-info'
        model_inputs = [DexPoolPriceInput(token=input,
                                          pool=pool,
                                          price_slug='uniswap-v3.get-weighted-price')
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

        def _use_for():
            infos = []
            for minput in model_inputs:
                pi = self.context.run_model(model_slug, minput, return_type=PoolPriceInfo)
                infos.append(pi)
            return infos

        def _use_local():
            infos = []
            for minput in model_inputs:
                pi = self.context.run_model(model_slug, minput, return_type=PoolPriceInfo,
                                            local=True)
                infos.append(pi)
            return infos

        infos = _use_local()

        return Some[PoolPriceInfo](some=infos)
