from credmark.cmf.types import Address
from credmark.dto import DTO


class PoolPriceInfo(DTO):
    """
    @src: source
    @price: price derived from pool of stablecoin and WETH9
    @liquidity: Available liquidity in the pool for the token
    @weth_multiplier: WETH price used if one token is WETH9
    @inverse: True if token is the second token in the pool
    @token0_address: token0's address
    @token1_address: token1's address
    @token0_symbol: token0's symbol
    @token1_symbol: token1's symbol
    @token0_decimals: token0's decimals
    @token1_decimals: token1's decimals
    @pool_address: pool's address
    """
    src: str
    price0: float
    price1: float
    one_tick_liquidity0: float
    one_tick_liquidity1: float
    full_tick_liquidity0: float
    full_tick_liquidity1: float
    token0_address: Address
    token1_address: Address
    token0_symbol: str
    token1_symbol: str
    pool_address: Address
    ref_price: float
    tick_spacing: int


class PoolPriceInfoWithVolume(PoolPriceInfo):
    """
    extended
    """
    token0_in: float
    token0_out: float
    token1_in: float
    token1_out: float

    token0_add: float
    token0_remove: float
    token0_collect: float
    token0_collect_prot: float
    token1_add: float
    token1_remove: float
    token1_collect: float
    token1_collect_prot: float

    reserve0: float
    reserve1: float
