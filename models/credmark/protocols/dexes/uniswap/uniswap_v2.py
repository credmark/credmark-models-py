# pylint: disable=line-too-long

from credmark.cmf.model import Model
from credmark.cmf.types import (
    Address,
    Contract,
    Contracts,
    Maybe,
    Network,
    Records,
    Some,
    Token,
    Tokens,
)
from credmark.dto import EmptyInputSkipTest

from models.credmark.protocols.dexes.uniswap.uniswap_v2_meta import UniswapV2PoolMeta
from models.dtos.pool import DexPoolInput, PoolPriceInfo
from models.dtos.price import DexPoolPriceInput, DexPriceTokenInput, DexProtocol, PriceWeight

# uniswap-v2 / sushiswap / pancakeswap-v2

# - .get-factory
# - .get-pool-by-pair
# - .all-pools
# - .all-pools-events
# - .all-pools-ledger
# - .get-pools
# - .get-pools-ledger
# - .get-pools-tokens
# - .get-ring0-ref-price
# - .get-pool-info-token-price


class UniswapV2FactoryMeta:
    FACTORY_ADDRESS = {
        k: Address("0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f") for k in [Network.Mainnet]
    }
    PROTOCOL = DexProtocol.UniswapV2


class UniswapV2Pool(Contract):
    class Config:
        schema_extra = {
            "examples": [{"address": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"}]  # USDC / WETH
        }


class UniswapV2DexPoolPriceInput(UniswapV2Pool, DexPoolPriceInput):
    class Config:
        schema_extra = {
            "examples": [
                {
                    "address": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",  # USDC / WETH
                    "price_slug": "uniswap-v2.get-weighted-price",
                    "ref_price_slug": "uniswap-v2.get-ring0-ref-price",
                    "weight_power": 4.0,
                    "protocol": "uniswap-v2",
                }
            ]
        }


UNISWAPV2_VERSION = "0.1"


@Model.describe(
    slug="uniswap-v2.get-factory",
    version=UNISWAPV2_VERSION,
    display_name="Uniswap V2 - get factory",
    description="Returns the address of Uniswap V2 factory contract",
    category="protocol",
    subcategory="uniswap-v2",
    output=Contract,
)
class UniswapV2GetFactory(UniswapV2PoolMeta, UniswapV2FactoryMeta):
    def run(self, _) -> Contract:
        return self.get_factory(self.FACTORY_ADDRESS[self.context.network])


@Model.describe(
    slug="uniswap-v2.get-pool-by-pair",
    version=UNISWAPV2_VERSION,
    display_name="Uniswap V2 get pool for a pair of tokens",
    description=("Returns the addresses of the pool of input tokens"),
    category="protocol",
    subcategory="uniswap-v2",
    input=DexPoolInput,
    output=Maybe[Contract],
)
class UniswapV2GetPool(UniswapV2PoolMeta, UniswapV2FactoryMeta):
    def run(self, input: DexPoolInput) -> Maybe[Contract]:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_pair(factory_addr, input.token0.address, input.token1.address)


@Model.describe(
    slug="uniswap-v2.all-pools",
    version=UNISWAPV2_VERSION,
    display_name="Uniswap V2 all pools",
    description="Returns the addresses of all pools on Uniswap V2 protocol",
    category="protocol",
    subcategory="uniswap-v2",
    input=EmptyInputSkipTest,
    output=Some[Address],
)
class UniswapV2AllPools(UniswapV2PoolMeta, UniswapV2FactoryMeta):
    def run(self, _) -> Some[Address]:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_all_pairs(factory_addr)


@Model.describe(
    slug="uniswap-v2.all-pools-events",
    version=UNISWAPV2_VERSION,
    display_name="Uniswap V2 all pools",
    description="Returns the addresses of all pools on Uniswap V2 protocol",
    category="protocol",
    subcategory="uniswap-v2",
    input=EmptyInputSkipTest,
    output=Records,
)
class UniswapV2AllPoolsEvents(UniswapV2PoolMeta, UniswapV2FactoryMeta):
    def run(self, _) -> Records:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_all_pairs_events(
            factory_addr, _from_block=0, _to_block=self.context.block_number
        )


@Model.describe(
    slug="uniswap-v2.all-pools-ledger",
    version=UNISWAPV2_VERSION,
    display_name="Uniswap v2 Token Pools - from ledger",
    description="The Uniswap v2 pools that support a token contract",
    category="protocol",
    subcategory="uniswap-v2",
    input=EmptyInputSkipTest,
    output=Records,
)
class UniswapV2AllPoolsLedger(UniswapV2PoolMeta, UniswapV2FactoryMeta):
    def run(self, _) -> Records:
        return self.get_all_pools_ledger(self.FACTORY_ADDRESS[self.context.network])


@Model.describe(
    slug="uniswap-v2.get-pools",
    version=UNISWAPV2_VERSION,
    display_name="Uniswap v2 Token Pools",
    description="The Uniswap v2 pools that support a token contract",
    category="protocol",
    subcategory="uniswap-v2",
    input=Token,
    output=Contracts,
)
class UniswapV2GetPoolsForToken(UniswapV2PoolMeta, UniswapV2FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(factory_addr, self.PROTOCOL, [input.address])
        return Contracts.from_addresses(pools)


@Model.describe(
    slug="uniswap-v2.get-pools-ledger",
    version=UNISWAPV2_VERSION,
    display_name="Uniswap v2 Token Pools",
    description="The Uniswap v2 pools that support a token contract - use ledger",
    category="protocol",
    subcategory="uniswap-v2",
    input=Token,
    output=Contracts,
)
class UniswapV2GetPoolsForTokenLedger(UniswapV2PoolMeta, UniswapV2FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_pools_for_tokens_ledger(factory_addr, self.PROTOCOL, input.address)


@Model.describe(
    slug="uniswap-v2.get-pools-tokens",
    version=UNISWAPV2_VERSION,
    display_name="Uniswap v2 Pools for Tokens",
    description="The Uniswap v2 pools for multiple tokens",
    category="protocol",
    subcategory="uniswap-v2",
    input=Tokens,
    output=Contracts,
)
class UniswapV2GetPoolsForTokens(UniswapV2PoolMeta, UniswapV2FactoryMeta):
    def run(self, input: Tokens) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(
            factory_addr, self.PROTOCOL, [tok.address for tok in input.tokens]
        )
        return Contracts.from_addresses(list(set(pools)))


@Model.describe(
    slug="uniswap-v2.get-ring0-ref-price",
    version=UNISWAPV2_VERSION,
    display_name="Uniswap v2 Ring0 Reference Price",
    description="The Uniswap v2 pools that support the ring0 tokens",
    category="protocol",
    subcategory="uniswap-v2",
    input=PriceWeight,
    output=dict,
)
class UniswapV2GetRing0RefPrice(UniswapV2PoolMeta, UniswapV2FactoryMeta):
    def run(self, input: PriceWeight) -> dict:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_ref_price(factory_addr, self.PROTOCOL, input.weight_power)


@Model.describe(
    slug="uniswap-v2.get-pool-info-token-price",
    version=UNISWAPV2_VERSION,
    display_name="Uniswap v2 Token Pools",
    description="Gather price and liquidity information from pools for a Token",
    category="protocol",
    subcategory="uniswap-v2",
    input=DexPriceTokenInput,
    output=Some[PoolPriceInfo],
)
class UniswapV2GetTokenPriceInfo(UniswapV2PoolMeta, UniswapV2FactoryMeta):
    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        pools = self.context.run_model("uniswap-v2.get-pools", input, return_type=Contracts)
        return self.get_pools_info(
            input,
            pools,
            model_slug="uniswap-v2.get-pool-price-info",
            price_slug="uniswap-v2.get-weighted-price",
            ref_price_slug="uniswap-v2.get-ring0-ref-price",
            _protocol=self.PROTOCOL,
        )
