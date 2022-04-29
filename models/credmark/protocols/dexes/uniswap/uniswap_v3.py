import numpy as np
from web3.exceptions import (
    BadFunctionCallOutput,
)

from credmark.cmf.model import Model
from credmark.cmf.model.errors import (
    ModelDataError,
    ModelRunError,
)
from credmark.cmf.types import (
    Price,
    Token,
    Address,
    Contract,
    Contracts,
)

from credmark.dto import DTO

from models.tmp_abi_lookup import (
    UNISWAP_V3_POOL_ABI,
    WETH9_ADDRESS,
)

from models.dtos.price import PoolPriceInfo, PoolPriceInfos


class UniswapV3PoolInfo(DTO):
    address: Address
    sqrtPriceX96: float
    tick: int
    observationIndex: int
    observationCardinality: int
    observationCardinalityNext: int
    feeProtocol: int
    unlocked: bool
    liquidity: str
    tick_liquidity_token0: float
    tick_liquidity_token1: float
    virtual_liquidity_token0: float
    virtual_liquidity_token1: float
    fee: int
    token0: Token
    token1: Token


@Model.describe(slug='uniswap-v3.get-pools',
                version='1.1',
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract',
                input=Token,
                output=Contracts)
class UniswapV3GetPoolsForToken(Model):
    UNISWAP_V3_FACTORY_ADDRESS = {
        1: "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    }

    def run(self, input: Token) -> Contracts:
        fees = [3000, 10000]
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
                            # TODO: ABI for 0x2a84e2bd2e961b1557d6e516ca647268b432cba4
                            # is not loaded in DB
                            pools.append(Contract(address=pool,
                                                  abi=UNISWAP_V3_POOL_ABI).info)

            return Contracts(contracts=pools)
        except BadFunctionCallOutput:
            # Or use this condition: if self.context.block_number < 12369621:
            return Contracts(contracts=[])


@Model.describe(slug='uniswap-v3.get-pool-info',
                version='1.1',
                display_name='Uniswap v3 Token Pools Info',
                description='The Uniswap v3 pools that support a token contract',
                input=Contract,
                output=UniswapV3PoolInfo)
class UniswapV3GetPoolInfo(Model):
    UNISWAP_BASE = 1.0001

    def tick_to_price(self, tick):
        return pow(self.UNISWAP_BASE, tick)

    def run(self, input: Contract) -> UniswapV3PoolInfo:
        try:
            input.abi
        except ModelDataError:
            input = Contract(address=input.address, abi=UNISWAP_V3_POOL_ABI).info

        pool = input

        slot0 = pool.functions.slot0().call()
        fee = pool.functions.fee().call()
        ticks = pool.functions.ticks(slot0[1]).call()

        token0_addr = pool.functions.token0().call()
        token1_addr = pool.functions.token1().call()
        token0 = Token(address=token0_addr)
        token1 = Token(address=token1_addr)

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

        amount0 = liquidity * (sb - sp) / (sp * sb)
        amount1 = liquidity * (sp - sa)

        # Below shall be equal for the tick liquidity
        # Reference: UniswapV3 whitepaper Eq. 2.2
        assert np.isclose(
            (amount0 + liquidity / sb) * (amount1 + liquidity * sa),
            float(liquidity * liquidity))

        # Scale the amounts to the token's unit
        adjusted_amount0 = token0.scaled(amount0)
        adjusted_amount1 = token1.scaled(amount1)

        # Calculate the virtual liquidity
        # Reference: UniswapV3 whitepaper Eq. 2.1
        virtual_x = token0.scaled(liquidity / sp)
        virtual_y = token1.scaled(liquidity * sp)

        res = {
            "address": input.address,
            "sqrtPriceX96": slot0[0],
            "tick": tick,
            "observationIndex": slot0[2],
            "observationCardinality": slot0[3],
            "observationCardinalityNext": slot0[4],
            "feeProtocol": slot0[5],
            "unlocked": slot0[6],
            "token0": token0,
            "token1": token1,
            "liquidity": liquidity,
            'tick_liquidity_token0': adjusted_amount0,
            'tick_liquidity_token1': adjusted_amount1,
            "fee": fee,
            'liquidityGross': ticks[0],
            'liquidityNet': ticks[1],
            'virtual_liquidity_token0': virtual_x,
            'virtual_liquidity_token1': virtual_y,
        }
        return UniswapV3PoolInfo(**res)


@Model.describe(slug='uniswap-v3.get-pool-price-info',
                version='1.1',
                display_name='Uniswap v3 Token Pools Price ',
                description='Gather price and liquidity information from pools',
                input=Token,
                output=PoolPriceInfos)
class UniswapV3GetPoolPriceInfo(Model):
    def run(self, input: Token) -> PoolPriceInfos:
        pools = self.context.run_model('uniswap-v3.get-pools',
                                       input,
                                       return_type=Contracts)

        infos = [
            self.context.run_model('uniswap-v3.get-pool-info',
                                   p,
                                   return_type=UniswapV3PoolInfo)
            for p in pools
        ]

        prices_with_info = []
        weth_price = None
        for info in infos:
            # decimal only available for ERC20s
            if info.token0.decimals and info.token1.decimals:
                scale_multiplier = (10 ** (info.token0.decimals - info.token1.decimals))
                tick_price = 1.0001 ** info.tick * scale_multiplier
                _tick_liquidity = info.tick_liquidity_token1
                virtual_liquidity = info.virtual_liquidity_token1
                ratio_price = info.sqrtPriceX96 * info.sqrtPriceX96 / (2 ** 192) * scale_multiplier

                inverse = False
                if input.address == info.token1.address:
                    tick_price = 1/tick_price
                    ratio_price = 1/ratio_price
                    inverse = True
                    _tick_liquidity = info.tick_liquidity_token0
                    virtual_liquidity = info.virtual_liquidity_token0

                weth_multiplier = 1.0
                if input.address != WETH9_ADDRESS:
                    if WETH9_ADDRESS in (info.token1.address, info.token0.address):
                        if weth_price is None:
                            weth_price = self.context.run_model('uniswap-v3.get-weighted-price',
                                                                {"address": WETH9_ADDRESS},
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
                                                weth_multiplier=weth_multiplier,
                                                inverse=inverse,
                                                token0_address=info.token0.address,
                                                token1_address=info.token1.address,
                                                token0_symbol=info.token0.symbol,
                                                token1_symbol=info.token1.symbol,
                                                token0_decimals=info.token0.decimals,
                                                token1_decimals=info.token1.decimals,
                                                pool_address=info.address)
                prices_with_info.append(pool_price_info)

        return PoolPriceInfos(pool_price_infos=prices_with_info)
