# pylint: disable=line-too-long

from credmark.cmf.model import Model
from credmark.cmf.types import Address, Contract, Contracts, Maybe, Network, Records, Some, Token, Tokens
from credmark.dto import EmptyInputSkipTest

from models.credmark.protocols.dexes.uniswap.uniswap_v2_meta import UniswapV2PoolMeta
from models.dtos.pool import DexPoolInput, PoolPriceInfo
from models.dtos.price import DexPoolPriceInput, DexPriceTokenInput, DexProtocol, PriceWeight


class QuickSwapV2FactoryMeta:
    FACTORY_ADDRESS = {
        Network.Polygon: Address('0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32'),
    }
    ROUTER_ADDRESS = {
        Network.Polygon: Address('0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff'),
    }
    PROTOCOL = DexProtocol.QuickSwapV2


class QuickSwapV2Pool(Contract):
    class Config:
        schema_extra = {
            "examples": [{'address': '0xAE81FAc689A1b4b1e06e7ef4a2ab4CD8aC0A087D'}]  # MATIC / USDC
        }


class QuickSwapV2DexPoolPriceInput(QuickSwapV2Pool, DexPoolPriceInput):
    class Config:
        schema_extra = {
            'examples': [{"address": "0xAE81FAc689A1b4b1e06e7ef4a2ab4CD8aC0A087D",  # MATIC / USDC
                          "price_slug": "quickswap-v2.get-weighted-price",
                          "ref_price_slug": "quickswap-v2.get-ring0-ref-price",
                          "weight_power": 4.0,
                          "protocol": "quickswap-v2"}]
        }


QUICKSWAP_V2_VERSION = '0.1'


@Model.describe(slug="quickswap-v2.get-factory",
                version=QUICKSWAP_V2_VERSION,
                display_name="QuickSwapV2 - get factory",
                description="Returns the address of QuickSwapV2 factory contract",
                category='protocol',
                subcategory='quickswap-v2',
                output=Contract)
class QuickSwapV2GetFactory(UniswapV2PoolMeta, QuickSwapV2FactoryMeta):
    def run(self, _) -> Contract:
        return self.get_factory(self.FACTORY_ADDRESS[self.context.network])


@Model.describe(slug="quickswap-v2.get-pool-by-pair",
                version=QUICKSWAP_V2_VERSION,
                display_name="QuickSwapV2 get pool for a pair of tokens",
                description=("Returns the addresses of the pool of input tokens"),
                category='protocol',
                subcategory='quickswap-v2',
                input=DexPoolInput,
                output=Maybe[Contract])
class QuickSwapV2GetPair(UniswapV2PoolMeta, QuickSwapV2FactoryMeta):
    def run(self, input: DexPoolInput) -> Maybe[Contract]:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_pair(factory_addr, input.token0.address, input.token1.address)


@Model.describe(slug="quickswap-v2.all-pools",
                version=QUICKSWAP_V2_VERSION,
                display_name="QuickSwapV2 all pairs",
                description="Returns the addresses of all pairs on QuickSwapV2 protocol",
                category='protocol',
                subcategory='quickswap-v2',
                input=EmptyInputSkipTest,
                output=Some[Address])
class QuickSwapV2AllPairs(UniswapV2PoolMeta, QuickSwapV2FactoryMeta):
    def run(self, _) -> Some[Address]:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_all_pairs(factory_addr)


@Model.describe(slug="quickswap-v2.all-pools-events",
                version=QUICKSWAP_V2_VERSION,
                display_name="PancakeSwap V2 all pairs from events",
                description=("Returns the addresses of all pairs on "
                             "PancakeSwap V2 protocol from events"),
                category='protocol',
                subcategory='quickswap-v2',
                input=EmptyInputSkipTest,
                output=Records)
class QuickSwapV2AllPairsEvents(UniswapV2PoolMeta, QuickSwapV2FactoryMeta):
    def run(self, _) -> Records:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_all_pairs_events(
            factory_addr, _from_block=0, _to_block=self.context.block_number)


@Model.describe(slug='quickswap-v2.all-pools-ledger',
                version=QUICKSWAP_V2_VERSION,
                display_name='PancakeSwap V2 Token Pools - from ledger',
                description='The PancakeSwap V2 pools that support a token contract',
                category='protocol',
                subcategory='quickswap-v2',
                input=EmptyInputSkipTest,
                output=Records)
class QuickSwapV2AllPairsLedger(UniswapV2PoolMeta, QuickSwapV2FactoryMeta):
    def run(self, _) -> Records:
        return self.get_all_pools_ledger(self.FACTORY_ADDRESS[self.context.network])


@Model.describe(slug='quickswap-v2.get-pools',
                version=QUICKSWAP_V2_VERSION,
                display_name='QuickSwapV2 Token Pools',
                description='The QuickSwapV2 pool pools that support a token contract',
                category='protocol',
                subcategory='quickswap-v2',
                input=Token,
                output=Contracts)
class QuickSwapV2GetPoolsForToken(UniswapV2PoolMeta, QuickSwapV2FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(factory_addr, self.PROTOCOL, [input.address])
        return Contracts.from_addresses(pools)


@Model.describe(slug='quickswap-v2.get-pools-ledger',
                version=QUICKSWAP_V2_VERSION,
                display_name='QuickSwapV2 Token Pools',
                description='The QuickSwapV2 pools that support a token contract - use ledger',
                category='protocol',
                subcategory='quickswap-v2',
                input=Token,
                output=Contracts)
class QuickSwapV2GetPoolsForTokenLedger(UniswapV2PoolMeta, QuickSwapV2FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_pools_for_tokens_ledger(
            factory_addr, self.PROTOCOL, input.address)


@Model.describe(slug='quickswap-v2.get-pools-tokens',
                version=QUICKSWAP_V2_VERSION,
                display_name='QuickSwapV2 Pools for Tokens',
                description='The QuickSwapV2 pools for multiple tokens',
                category='protocol',
                subcategory='quickswap-v2',
                input=Tokens,
                output=Contracts)
class QuickSwapV2GetPoolsForTokens(UniswapV2PoolMeta, QuickSwapV2FactoryMeta):
    def run(self, input: Tokens) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(
            factory_addr, self.PROTOCOL, [tok.address for tok in input.tokens])
        return Contracts.from_addresses(list(set(pools)))


@Model.describe(slug='quickswap-v2.get-ring0-ref-price',
                version=QUICKSWAP_V2_VERSION,
                display_name='QuickSwapV2 Ring0 Reference Price',
                description='The QuickSwapV2 pools that support the ring0 tokens',
                category='protocol',
                subcategory='quickswap-v2',
                input=PriceWeight,
                output=dict)
class QuickSwapV2GetRing0RefPrice(UniswapV2PoolMeta, QuickSwapV2FactoryMeta):
    def run(self, input: PriceWeight) -> dict:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_ref_price(factory_addr, self.PROTOCOL, input.weight_power)


@Model.describe(slug='quickswap-v2.get-pool-info-token-price',
                version=QUICKSWAP_V2_VERSION,
                display_name='QuickSwapV2 Token Pools',
                description='Gather price and liquidity information from pools for a Token',
                category='protocol',
                subcategory='quickswap-v2',
                input=DexPriceTokenInput,
                output=Some[PoolPriceInfo])
class QuickSwapV2GetTokenPriceInfo(UniswapV2PoolMeta, QuickSwapV2FactoryMeta):
    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        pools = self.context.run_model('quickswap-v2.get-pools', input,
                                       return_type=Contracts)
        return self.get_pools_info(input,
                                   pools,
                                   model_slug='uniswap-v2.get-pool-price-info',
                                   price_slug='quickswap-v2.get-weighted-price',
                                   ref_price_slug='quickswap-v2.get-ring0-ref-price',
                                   _protocol=self.PROTOCOL)
