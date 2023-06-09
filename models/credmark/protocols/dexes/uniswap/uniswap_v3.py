from credmark.cmf.model import Model
from credmark.cmf.types import Contract, Contracts, Records, Some, Token, Tokens
from credmark.dto import EmptyInputSkipTest

from models.credmark.protocols.dexes.uniswap.constant import (
    V3_FACTORY_ADDRESS,
    V3_POOL_FEES,
)
from models.credmark.protocols.dexes.uniswap.uniswap_v3_meta import UniswapV3PoolMeta
from models.dtos.pool import DexPoolInput, PoolPriceInfo
from models.dtos.price import DexPoolPriceInput, DexPriceTokenInput, DexProtocol, PriceWeight
from models.tmp_abi_lookup import UNISWAP_V3_FACTORY_ABI

# uniswap-v3
# - .get-factory
# - .get-pools-by-pair
# - .all-pools-events
# - .all-pools-ledger
# - .get-pools
# - .get-pools-ledger
# - .get-pools-tokens
# - .get-ring0-ref-price
# - .get-pool-info-token-price


class UniswapV3FactoryMeta:
    FACTORY_ADDRESS = V3_FACTORY_ADDRESS
    PROTOCOL = DexProtocol.UniswapV3
    POOL_FEES = V3_POOL_FEES
    FACTORY_ABI = UNISWAP_V3_FACTORY_ABI


class UniswapV3Pool(Contract):
    class Config:
        schema_extra = {
            # CRV / WETH
            "examples": [{'address': '0xFC99D1c02D27DE07DfE0dCd878CDe86ee59c5f6B',
                          '_test_multi': {'chain_id': 137}}],
            'test_multi': True,

        }


class UniswapV3DexPoolPriceInput(UniswapV3Pool, DexPoolPriceInput):
    class Config:
        schema_extra = {
            'examples': [{"address": "0xFC99D1c02D27DE07DfE0dCd878CDe86ee59c5f6B",  # USDC / WETH
                          "price_slug": "uniswap-v3.get-weighted-price",
                          "ref_price_slug": "uniswap-v3.get-ring0-ref-price",
                          "weight_power": 4.0,
                          "protocol": "uniswap-v3",
                          '_test_multi': {'chain_id': 137}}],
            'test_multi': True,
        }


UNISWAPV3_VERSION = '0.1'


@Model.describe(slug="uniswap-v3.get-factory",
                version=UNISWAPV3_VERSION,
                display_name="Uniswap V3 - get factory",
                description="Returns the address of Uniswap V3 factory contract",
                category='protocol',
                subcategory='uniswap-v3',
                output=Contract)
class UniswapV3GetFactory(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, _) -> Contract:
        return self.get_factory(self.FACTORY_ADDRESS[self.context.network], self.FACTORY_ABI)


@Model.describe(slug="uniswap-v3.get-pools-by-pair",
                version=UNISWAPV3_VERSION,
                display_name="Uniswap V3 get pool for a pair of tokens",
                description=("Returns the addresses of the pool of input tokens"),
                category='protocol',
                subcategory='uniswap-v3',
                input=DexPoolInput,
                output=Contracts)
class UniswapV3GetPool(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, input: DexPoolInput) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_by_pair(factory_addr, self.FACTORY_ABI,
                                       [(input.token0.address, input.token1.address)],
                                       self.POOL_FEES)
        return Contracts.from_addresses(pools)


@Model.describe(slug="uniswap-v3.all-pools-events",
                version=UNISWAPV3_VERSION,
                display_name="Uniswap v3 all pairs",
                description="Returns the addresses of all pairs on Uniswap V3 protocol",
                category='protocol',
                subcategory='uniswap-v3',
                input=EmptyInputSkipTest,
                output=Records)
class UniswapV3AllPoolsEvents(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, _) -> Records:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_all_pairs_events(
            factory_addr, self.FACTORY_ABI, _from_block=0, _to_block=self.context.block_number)


@Model.describe(slug='uniswap-v3.all-pools-ledger',
                version=UNISWAPV3_VERSION,
                display_name='Uniswap v3 Token Pools - from ledger',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                input=EmptyInputSkipTest,
                output=Records)
class UniswapV3AllPoolsLedger(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, _) -> Records:
        return self.get_all_pools_ledger(self.FACTORY_ADDRESS[self.context.network],
                                         self.FACTORY_ABI)


@Model.describe(slug='uniswap-v3.get-pools',
                version=UNISWAPV3_VERSION,
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                input=Token,
                output=Contracts)
class UniswapV3GetPoolsForToken(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(factory_addr, self.FACTORY_ABI,
                                          self.PROTOCOL, [input.address],
                                          self.POOL_FEES)
        return Contracts.from_addresses(pools)


@Model.describe(slug='uniswap-v3.get-pools-ledger',
                version=UNISWAPV3_VERSION,
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract - use ledger',
                category='protocol',
                subcategory='uniswap-v3',
                input=Token,
                output=Contracts)
class UniswapV3GetPoolsForTokenLedger(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_pools_for_tokens_ledger(
            factory_addr, self.FACTORY_ABI, self.PROTOCOL, input.address, self.POOL_FEES)


@Model.describe(slug='uniswap-v3.get-pools-tokens',
                version=UNISWAPV3_VERSION,
                display_name='Uniswap v3 Token Pools',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                input=Tokens,
                output=Contracts)
class UniswapV3GetPoolsForTokens(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, input: Tokens) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(
            factory_addr, self.FACTORY_ABI, self.PROTOCOL,
            [tok.address for tok in input.tokens], self.POOL_FEES)
        return Contracts.from_addresses(list(set(pools)))


@Model.describe(slug='uniswap-v3.get-ring0-ref-price',
                version=UNISWAPV3_VERSION,
                display_name='Uniswap v3 Ring0 Reference Price',
                description='The Uniswap v3 pools that support the ring0 tokens',
                category='protocol',
                subcategory='uniswap-v3',
                input=PriceWeight,
                output=dict)
class UniswapV3GetRing0RefPrice(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, input: PriceWeight) -> dict:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_ref_price(factory_addr, self.FACTORY_ABI,
                                  self.PROTOCOL, input.weight_power, self.POOL_FEES)


@Model.describe(slug='uniswap-v3.get-pool-info-token-price',
                version=UNISWAPV3_VERSION,
                display_name='Uniswap v3 Token Pools Price ',
                description='Gather price and liquidity information from pools',
                category='protocol',
                subcategory='uniswap-v3',
                input=DexPriceTokenInput,
                output=Some[PoolPriceInfo])
class UniswapV3GetTokenPoolInfo(UniswapV3PoolMeta, UniswapV3FactoryMeta):
    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        pools = self.context.run_model('uniswap-v3.get-pools', input,
                                       return_type=Contracts)
        return self.get_pools_info(input,
                                   pools,
                                   model_slug='uniswap-v3.get-pool-price-info',
                                   price_slug='uniswap-v3.get-weighted-price',
                                   ref_price_slug='uniswap-v3.get-ring0-ref-price',
                                   _protocol=self.PROTOCOL)
