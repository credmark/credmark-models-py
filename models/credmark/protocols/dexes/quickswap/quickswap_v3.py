from credmark.cmf.model import Model
from credmark.cmf.types import Address, Contract, Contracts, Network, Records, Some, Token, Tokens
from credmark.dto import EmptyInputSkipTest

from models.credmark.protocols.dexes.uniswap.uniswap_v3_meta import UniswapV3PoolMeta
from models.dtos.pool import DexPoolInput, PoolPriceInfo
from models.dtos.price import DexPriceTokenInput, DexProtocol, PriceWeight
from models.tmp_abi_lookup import QUICKSWAP_V3_FACTORY_ABI


class QuickSwapV3FactoryMeta:
    FACTORY_ADDRESS = {
        Network.Polygon: Address('0x411b0fAcC3489691f28ad58c47006AF5E3Ab3A28')
    }
    PROTOCOL = DexProtocol.QuickSwapV3
    POOL_FEES = []
    FACTORY_ABI = QUICKSWAP_V3_FACTORY_ABI


QUICKSWAP_V3_VERSION = '0.1'


@Model.describe(slug="quickswap-v3.get-factory",
                version=QUICKSWAP_V3_VERSION,
                display_name="QuickSwap V3 - get factory",
                description="Returns the address of QuickSwap V3 factory contract",
                category='protocol',
                subcategory='quickswap-v3',
                output=Contract)
class QuickSwapV3GetFactory(UniswapV3PoolMeta, QuickSwapV3FactoryMeta):
    def run(self, _) -> Contract:
        return self.get_factory(self.FACTORY_ADDRESS[self.context.network], self.FACTORY_ABI)


@Model.describe(slug="quickswap-v3.get-pools-by-pair",
                version=QUICKSWAP_V3_VERSION,
                display_name="QuickSwap V3 get pool for a pair of tokens",
                description=("Returns the addresses of the pool of input tokens"),
                category='protocol',
                subcategory='quickswap-v3',
                input=DexPoolInput,
                output=Contracts)
class QuickSwapV3GetPool(UniswapV3PoolMeta, QuickSwapV3FactoryMeta):
    def run(self, input: DexPoolInput) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_by_pair(
            factory_addr, self.FACTORY_ABI,
            [(input.token0.address, input.token1.address)],
            self.POOL_FEES)
        return Contracts.from_addresses(pools)


@Model.describe(slug="quickswap-v3.all-pools-events",
                version=QUICKSWAP_V3_VERSION,
                display_name="QuickSwap V3 all pairs",
                description="Returns the addresses of all pairs on QuickSwap V3 protocol",
                category='protocol',
                subcategory='quickswap-v3',
                input=EmptyInputSkipTest,
                output=Records)
class QuickSwapV3AllPoolsEvents(UniswapV3PoolMeta, QuickSwapV3FactoryMeta):
    def run(self, _) -> Records:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_all_pairs_events(
            factory_addr, self.FACTORY_ABI,
            _from_block=0, _to_block=self.context.block_number)


@Model.describe(slug='quickswap-v3.all-pools-ledger',
                version=QUICKSWAP_V3_VERSION,
                display_name='QuickSwap V3 Token Pools - from ledger',
                description='The QuickSwap V3 pools that support a token contract',
                category='protocol',
                subcategory='quickswap-v3',
                input=EmptyInputSkipTest,
                output=Records)
class QuickSwapV3AllPoolsLedger(UniswapV3PoolMeta, QuickSwapV3FactoryMeta):
    def run(self, _) -> Records:
        return self.get_all_pools_ledger(
            self.FACTORY_ADDRESS[self.context.network], self.FACTORY_ABI)


@Model.describe(slug='quickswap-v3.get-pools',
                version=QUICKSWAP_V3_VERSION,
                display_name='QuickSwap V3 Token Pools',
                description='The QuickSwap V3 pools that support a token contract',
                category='protocol',
                subcategory='quickswap-v3',
                input=Token,
                output=Contracts)
class QuickSwapV3GetPoolsForToken(UniswapV3PoolMeta, QuickSwapV3FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(
            factory_addr, self.FACTORY_ABI, self.PROTOCOL, [input.address],
            self.POOL_FEES)
        return Contracts.from_addresses(pools)


@Model.describe(slug='quickswap-v3.get-pools-ledger',
                version=QUICKSWAP_V3_VERSION,
                display_name='QuickSwap V3 Token Pools',
                description='The QuickSwap V3 pools that support a token contract - use ledger',
                category='protocol',
                subcategory='quickswap-v3',
                input=Token,
                output=Contracts)
class QuickSwapV3GetPoolsForTokenLedger(UniswapV3PoolMeta, QuickSwapV3FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_pools_for_tokens_ledger(
            factory_addr, self.FACTORY_ABI, self.PROTOCOL, input.address, self.POOL_FEES)


@Model.describe(slug='quickswap-v3.get-pools-tokens',
                version=QUICKSWAP_V3_VERSION,
                display_name='QuickSwap V3 Token Pools',
                description='The QuickSwap V3 pools that support a token contract',
                category='protocol',
                subcategory='quickswap-v3',
                input=Tokens,
                output=Contracts)
class QuickSwapV3GetPoolsForTokens(UniswapV3PoolMeta, QuickSwapV3FactoryMeta):
    def run(self, input: Tokens) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(
            factory_addr, self.FACTORY_ABI, self.PROTOCOL,
            [tok.address for tok in input.tokens], self.POOL_FEES)
        return Contracts.from_addresses(list(set(pools)))


@Model.describe(slug='quickswap-v3.get-ring0-ref-price',
                version=QUICKSWAP_V3_VERSION,
                display_name='QuickSwap V3 Ring0 Reference Price',
                description='The QuickSwap V3 pools that support the ring0 tokens',
                category='protocol',
                subcategory='quickswap-v3',
                input=PriceWeight,
                output=dict)
class QuickSwapV3GetRing0RefPrice(UniswapV3PoolMeta, QuickSwapV3FactoryMeta):
    def run(self, input: PriceWeight) -> dict:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_ref_price(factory_addr, self.FACTORY_ABI, self.PROTOCOL,
                                  input.weight_power, self.POOL_FEES)


@Model.describe(slug='quickswap-v3.get-pool-info-token-price',
                version=QUICKSWAP_V3_VERSION,
                display_name='QuickSwap V3 Token Pools Price ',
                description='Gather price and liquidity information from pools',
                category='protocol',
                subcategory='quickswap-v3',
                input=DexPriceTokenInput,
                output=Some[PoolPriceInfo])
class QuickSwapV3GetTokenPoolInfo(UniswapV3PoolMeta, QuickSwapV3FactoryMeta):
    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        pools = self.context.run_model('quickswap-v3.get-pools', input,
                                       return_type=Contracts)
        return self.get_pools_info(input,
                                   pools,
                                   model_slug='uniswap-v3.get-pool-price-info',
                                   price_slug='quickswap-v3.get-weighted-price',
                                   ref_price_slug='quickswap-v3.get-ring0-ref-price',
                                   _protocol=self.PROTOCOL)
