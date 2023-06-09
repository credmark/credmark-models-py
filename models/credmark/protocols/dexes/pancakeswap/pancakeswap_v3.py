from credmark.cmf.model import Model
from credmark.cmf.types import Address, Contract, Contracts, Network, Records, Some, Token, Tokens
from credmark.dto import EmptyInputSkipTest

from models.credmark.protocols.dexes.uniswap.uniswap_v3_meta import UniswapV3PoolMeta
from models.dtos.pool import DexPoolInput, PoolPriceInfo
from models.dtos.price import DexPoolPriceInput, DexPriceTokenInput, DexProtocol, PriceWeight
from models.tmp_abi_lookup import PANCAKESWAP_V3_FACTORY_ABI


class PancakeSwapV3FactoryMeta:
    FACTORY_ADDRESS = {
        k: Address('0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865')
        for k in [Network.BSC, Network.Mainnet, Network.Görli]
    }
    PROTOCOL = DexProtocol.PancakeSwapV3
    POOL_FEES = [100, 500, 2500, 10000]
    FACTORY_ABI = PANCAKESWAP_V3_FACTORY_ABI


class PancakeSwapV3Pool(Contract):
    class Config:
        schema_extra = {
            "examples": [{'address': '0x6E229C972d9F69c15Bdc7B07f385D2025225E72b'}]
        }


class PancakeSwapV3DexPoolPriceInput(PancakeSwapV3Pool, DexPoolPriceInput):
    class Config:
        schema_extra = {
            'examples': [{"address": "0x6E229C972d9F69c15Bdc7B07f385D2025225E72b",  # MASK / USDC
                          "price_slug": "pancakeswap-v3.get-weighted-price",
                          "ref_price_slug": "pancakeswap-v3.get-ring0-ref-price",
                          "weight_power": 4.0,
                          "protocol": "pancakeswap-v3"}]
        }


PANCAKESWAP_V3_VERSION = '0.1'


@Model.describe(slug="pancakeswap-v3.get-factory",
                version=PANCAKESWAP_V3_VERSION,
                display_name="PancakeSwap V3 - get factory",
                description="Returns the address of PancakeSwap V3 factory contract",
                category='protocol',
                subcategory='pancakeswap-v3',
                output=Contract)
class PancakeSwapV3GetFactory(UniswapV3PoolMeta, PancakeSwapV3FactoryMeta):
    def run(self, _) -> Contract:
        return self.get_factory(self.FACTORY_ADDRESS[self.context.network], self.FACTORY_ABI)


@Model.describe(slug="pancakeswap-v3.get-pools-by-pair",
                version=PANCAKESWAP_V3_VERSION,
                display_name="PancakeSwap V3 get pool for a pair of tokens",
                description=("Returns the addresses of the pool of input tokens"),
                category='protocol',
                subcategory='pancakeswap-v3',
                input=DexPoolInput,
                output=Contracts)
class PancakeSwapV3GetPool(UniswapV3PoolMeta, PancakeSwapV3FactoryMeta):
    def run(self, input: DexPoolInput) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_by_pair(
            factory_addr, self.FACTORY_ABI, [(input.token0.address, input.token1.address)],
            self.POOL_FEES)
        return Contracts.from_addresses(pools)


@Model.describe(slug="pancakeswap-v3.all-pools-events",
                version=PANCAKESWAP_V3_VERSION,
                display_name="PancakeSwap v3 all pairs",
                description="Returns the addresses of all pairs on PancakeSwap V3 protocol",
                category='protocol',
                subcategory='pancakeswap-v3',
                input=EmptyInputSkipTest,
                output=Records)
class PancakeSwapV3AllPoolsEvents(UniswapV3PoolMeta, PancakeSwapV3FactoryMeta):
    def run(self, _) -> Records:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_all_pairs_events(
            factory_addr, self.FACTORY_ABI, _from_block=0, _to_block=self.context.block_number)


@Model.describe(slug='pancakeswap-v3.all-pools-ledger',
                version=PANCAKESWAP_V3_VERSION,
                display_name='PancakeSwap v3 Token Pools - from ledger',
                description='The PancakeSwap v3 pools that support a token contract',
                category='protocol',
                subcategory='pancakeswap-v3',
                input=EmptyInputSkipTest,
                output=Records)
class PancakeSwapV3AllPoolsLedger(UniswapV3PoolMeta, PancakeSwapV3FactoryMeta):
    def run(self, _) -> Records:
        return self.get_all_pools_ledger(self.FACTORY_ADDRESS[self.context.network],
                                         self.FACTORY_ABI)


@Model.describe(slug='pancakeswap-v3.get-pools',
                version=PANCAKESWAP_V3_VERSION,
                display_name='PancakeSwap v3 Token Pools',
                description='The PancakeSwap v3 pools that support a token contract',
                category='protocol',
                subcategory='pancakeswap-v3',
                input=Token,
                output=Contracts)
class PancakeSwapV3GetPoolsForToken(UniswapV3PoolMeta, PancakeSwapV3FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(
            factory_addr, self.FACTORY_ABI, self.PROTOCOL, [input.address],
            self.POOL_FEES)
        return Contracts.from_addresses(pools)


@Model.describe(slug='pancakeswap-v3.get-pools-ledger',
                version=PANCAKESWAP_V3_VERSION,
                display_name='PancakeSwap v3 Token Pools',
                description='The PancakeSwap v3 pools that support a token contract - use ledger',
                category='protocol',
                subcategory='pancakeswap-v3',
                input=Token,
                output=Contracts)
class PancakeSwapV3GetPoolsForTokenLedger(UniswapV3PoolMeta, PancakeSwapV3FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_pools_for_tokens_ledger(
            factory_addr, self.FACTORY_ABI, self.PROTOCOL,
            input.address, self.POOL_FEES)


@Model.describe(slug='pancakeswap-v3.get-pools-tokens',
                version=PANCAKESWAP_V3_VERSION,
                display_name='PancakeSwap v3 Token Pools',
                description='The PancakeSwap v3 pools that support a token contract',
                category='protocol',
                subcategory='pancakeswap-v3',
                input=Tokens,
                output=Contracts)
class PancakeSwapV3GetPoolsForTokens(UniswapV3PoolMeta, PancakeSwapV3FactoryMeta):
    def run(self, input: Tokens) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(
            factory_addr, self.FACTORY_ABI, self.PROTOCOL,
            [tok.address for tok in input.tokens], self.POOL_FEES)
        return Contracts.from_addresses(list(set(pools)))


@Model.describe(slug='pancakeswap-v3.get-ring0-ref-price',
                version=PANCAKESWAP_V3_VERSION,
                display_name='PancakeSwap v3 Ring0 Reference Price',
                description='The PancakeSwap v3 pools that support the ring0 tokens',
                category='protocol',
                subcategory='pancakeswap-v3',
                input=PriceWeight,
                output=dict)
class PancakeSwapV3GetRing0RefPrice(UniswapV3PoolMeta, PancakeSwapV3FactoryMeta):
    def run(self, input: PriceWeight) -> dict:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_ref_price(
            factory_addr, self.FACTORY_ABI, self.PROTOCOL,
            input.weight_power, self.POOL_FEES)


@Model.describe(slug='pancakeswap-v3.get-pool-info-token-price',
                version=PANCAKESWAP_V3_VERSION,
                display_name='PancakeSwap v3 Token Pools Price ',
                description='Gather price and liquidity information from pools',
                category='protocol',
                subcategory='pancakeswap-v3',
                input=DexPriceTokenInput,
                output=Some[PoolPriceInfo])
class PancakeSwapV3GetTokenPoolInfo(UniswapV3PoolMeta, PancakeSwapV3FactoryMeta):
    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        pools = self.context.run_model('pancakeswap-v3.get-pools', input,
                                       return_type=Contracts)
        return self.get_pools_info(input,
                                   pools,
                                   model_slug='uniswap-v3.get-pool-price-info',
                                   price_slug='pancakeswap-v3.get-weighted-price',
                                   ref_price_slug='pancakeswap-v3.get-ring0-ref-price',
                                   _protocol=self.PROTOCOL)
