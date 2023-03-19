# pylint:disable=invalid-name

from collections import namedtuple
from credmark.cmf.types import Address, Network

# For mainnet, Ropsten, Rinkeby, Görli, and Kovan
V2_FACTORY_ADDRESS = {
    k: Address('0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f')
    for k in
    [Network.Mainnet, Network.Ropsten, Network.Rinkeby, Network.Görli, Network.Kovan]}


V3_POS_NFT = {
    k: '0xc36442b4a4522e871399cd717abdd847ab11fe88'
    for k in [
        Network.Mainnet, Network.Polygon, Network.Optimism, Network.ArbitrumOne,
        Network.Ropsten, Network.Rinkeby, Network.Görli, Network.Kovan
    ]
}

V3_FACTORY_ADDRESS = {
    k: Address('0x1F98431c8aD98523631AE4a59f267346ea31F984')
    for k in [
        Network.Mainnet, Network.Polygon, Network.Optimism, Network.ArbitrumOne,
        Network.Ropsten, Network.Rinkeby, Network.Görli, Network.Kovan
    ]
}

V3_QUOTER_ADDRESS = {
    k: "0xb27308f9f90d607463bb33ea1bebb41c27ce5ab6"
    for k in [
        Network.Mainnet, Network.Polygon, Network.Optimism, Network.ArbitrumOne,
        Network.Ropsten, Network.Rinkeby, Network.Görli, Network.Kovan
    ]
}

V3_SWAP_ROUTER_ADDRESS = {
    k: "0xE592427A0AEce92De3Edee1F18E0157C05861564"
    for k in [
        Network.Mainnet, Network.Polygon, Network.Optimism, Network.ArbitrumOne,
        Network.Ropsten, Network.Rinkeby, Network.Görli, Network.Kovan
    ]
}


V3_POOL_FEES = [100, 500, 3000, 10000]

V3_TICK = namedtuple(
    "V3_TICK",
    ("liquidityGross liquidityNet feeGrowthOutside0X128 feeGrowthOutside1X128 "
     "tickCumulativeOutside secondsPerLiquidityOutsideX128 secondsOutside "
     "initialized"))

V3_POS = namedtuple(
    "V3_POS",
    ("nonce operator token0 token1 fee tickLower tickUpper liquidity "
        "feeGrowthInside0LastX128 feeGrowthInside1LastX128 tokensOwed0 tokensOwed1"))
