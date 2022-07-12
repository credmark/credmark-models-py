import numpy as np
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import Address, Contract, Contracts, Some, Price, Token
from credmark.cmf.types.block_number import BlockNumberOutOfRangeError
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO
from models.credmark.tokens.token import fix_erc20_token
from models.dtos.price import PoolPriceInfo, DexPoolPriceInput
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


@Model.describe(slug='uniswap-v3.get-pools',
                version='1.2',
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                input=Token,
                output=Contracts)
class UniswapV3GetPoolsForToken(Model):
    UNISWAP_V3_FACTORY_ADDRESS = {
        1: "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    }

    def run(self, input: Token) -> Contracts:
        fees = [100, 500, 3000, 10000]
        primary_tokens = [Token(symbol='DAI'),
                          Token(symbol='USDT'),
                          Token(symbol='WETH'),
                          Token(symbol='USDC')]

        if self.context.chain_id != 1:
            return Contracts(contracts=[])

        try:
            addr = self.UNISWAP_V3_FACTORY_ADDRESS[self.context.chain_id]
            uniswap_factory = Contract(address=addr)
            pools = []
            for fee in fees:
                for primary_token in primary_tokens:
                    if input.address and primary_token.address:
                        pool = uniswap_factory.functions.getPool(
                            input.address.checksum,
                            primary_token.address.checksum,
                            fee).call()
                        if pool != Address.null():
                            cc = Contract(address=pool, abi=UNISWAP_V3_POOL_ABI)
                            try:
                                _ = cc.abi
                            except ModelDataError:
                                pass
                            pools.append(cc)

            return Contracts(contracts=pools)
        except (BadFunctionCallOutput, BlockNumberOutOfRangeError):
            return Contracts(contracts=[])


@Model.describe(slug='uniswap-v3.get-pool-info',
                version='1.4',
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

        token0_balance = token0.scaled(token0.functions.balanceOf(input.address).call())
        token1_balance = token1.scaled(token1.functions.balanceOf(input.address).call())

        # Liquidity for virutal amount of x and y
        liquidity = pool.functions.liquidity().call()

        # To calculate liquidity within the range of tick

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

        amount0 = liquidity * (1 / sp - 1 / sb)
        amount1 = liquidity * (sp - sa)

        # Scale the amounts to the token's unit
        _adjusted_amount0 = token0.scaled(amount0)
        _adjusted_amount1 = token1.scaled(amount1)

        # Below shall be equal for the tick liquidity
        # Reference: UniswapV3 whitepaper Eq. 2.2
        assert np.isclose(
            (amount0 + liquidity / sb) * (amount1 + liquidity * sa),
            float(liquidity * liquidity))

        # https://uniswap.org/blog/uniswap-v3-dominance
        # Appendix B: methodology
        tick_liquidity_0 = amount0 + amount1 / p_current
        tick_liquidity_1 = tick_liquidity_0 * p_current

        tick_liquidity_0_scaled = token0.scaled(tick_liquidity_0)
        tick_liquidity_1_scaled = token1.scaled(tick_liquidity_1)

        # Calculate the virtual liquidity
        # Reference: UniswapV3 whitepaper Eq. 2.1
        virtual_x = token0.scaled(liquidity / sp)
        virtual_y = token1.scaled(liquidity * sp)

        res = {
            "address": input.address,
            "sqrtPriceX96": sqrtPriceX96,
            "tick": tick,
            'tick_bottom': tick_bottom,
            'tick_top': tick_top,
            "observationIndex": slot0[2],
            "observationCardinality": slot0[3],
            "observationCardinalityNext": slot0[4],
            "feeProtocol": slot0[5],
            "unlocked": slot0[6],
            "token0": token0,
            "token1": token1,
            'token0_balance': token0_balance,
            'token1_balance': token1_balance,
            'token0_symbol': token0_symbol,
            'token1_symbol': token1_symbol,
            "liquidity": liquidity,
            'tick_liquidity_token0': tick_liquidity_0_scaled,
            'tick_liquidity_token1': tick_liquidity_1_scaled,
            "fee": fee,
            'virtual_liquidity_token0': virtual_x,
            'virtual_liquidity_token1': virtual_y,
            'tick_spacing': tick_spacing,
            'sqrt_current_price': sp,
            'sqrt_lower_price': sa,
            'sqrt_upper_price': sb,
        }
        return UniswapV3PoolInfo(**res)


@Model.describe(slug='uniswap-v3.get-pool-price-info',
                version='0.4',
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
                                      return_type=UniswapV3PoolInfo)

        weth_price = None

        info.token0 = fix_erc20_token(info.token0)
        info.token1 = fix_erc20_token(info.token1)
        # decimal only available for ERC20s
        if not info.token0.decimals or not info.token1.decimals:
            raise ModelRunError((f'Details on token0 {info.token0.decimals=} '
                                 f'or token1 {info.token1.decimals=} are incomplete.'))

        scale_multiplier = (10 ** (info.token0.decimals - info.token1.decimals))
        tick_price = 1.0001 ** info.tick * scale_multiplier
        tick_liquidity = info.tick_liquidity_token0
        virtual_liquidity = info.virtual_liquidity_token0
        ratio_price = info.sqrtPriceX96 * info.sqrtPriceX96 / (2 ** 192) * scale_multiplier

        inverse = False
        if input.token.address == info.token1.address:
            tick_price = 1/tick_price
            ratio_price = 1/ratio_price
            inverse = True
            tick_liquidity = info.tick_liquidity_token1
            virtual_liquidity = info.virtual_liquidity_token1

        weth_multiplier = 1.0
        weth = Token(symbol='WETH')
        if input.token.address != weth.address:
            if weth.address in (info.token1.address, info.token0.address):
                if weth_price is None:
                    weth_price = self.context.run_model('price.quote',
                                                        {"base": weth},
                                                        return_type=Price)
                    if weth_price.price is None:
                        raise ModelRunError('Can not retriev price for WETH')

                    weth_price = weth_price.price
                weth_multiplier = weth_price

        tick_price *= weth_multiplier
        ratio_price *= weth_multiplier

        pool_price_info = PoolPriceInfo(src=self.slug,
                                        price=tick_price,
                                        liquidity=virtual_liquidity,
                                        tick_liquidity=tick_liquidity,
                                        weth_multiplier=weth_multiplier,
                                        inverse=inverse,
                                        token0_address=info.token0.address,
                                        token1_address=info.token1.address,
                                        token0_symbol=info.token0.symbol,
                                        token1_symbol=info.token1.symbol,
                                        token0_decimals=info.token0.decimals,
                                        token1_decimals=info.token1.decimals,
                                        pool_address=info.address)
        return pool_price_info


@ Model.describe(slug='uniswap-v3.get-pool-info-token-price',
                 version='1.8',
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
                                       return_type=Contracts)

        model_slug = 'uniswap-v3.get-pool-price-info'
        model_inputs = [DexPoolPriceInput(token=input, pool=pool)
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
                        f'Error with {model_slug}(input={model_inputs[pool_n]}). ' +
                        p.error.message)
                else:
                    raise ModelRunError('compose.map-inputs: output/error cannot be both None')
            return infos

        def _use_for():
            infos = []
            for minput in model_inputs:
                pi = self.context.run_model(model_slug, minput, return_type=PoolPriceInfo)
                infos.append(pi)
            return infos

        infos = _use_compose()

        return Some[PoolPriceInfo](some=infos)
