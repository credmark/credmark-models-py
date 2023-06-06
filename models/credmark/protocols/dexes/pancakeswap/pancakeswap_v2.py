# pylint: disable=line-too-long

from credmark.cmf.model import Model
from credmark.cmf.types import Address, Contract, Contracts, Maybe, Network, Records, Some, Token, Tokens
from credmark.dto import EmptyInputSkipTest

from models.credmark.protocols.dexes.uniswap.uniswap_v2_meta import UniswapV2PoolMeta
from models.dtos.pool import DexPoolInput, PoolPriceInfo
from models.dtos.price import DexPoolPriceInput, DexPriceTokenInput, DexProtocol, PriceWeight


class PancakeSwapV2FactoryMeta:
    FACTORY_ADDRESS = {
        Network.BSC: Address('0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'),
        Network.Mainnet: Address('0x1097053Fd2ea711dad45caCcc45EfF7548fCB362'),
    }
    ROUTER_ADDRESS = {
        Network.BSC: Address('0x10ED43C718714eb63d5aA57B78B54704E256024E'),
        Network.Mainnet: Address('0xEfF92A263d31888d860bD50809A8D171709b7b1c'),
    }
    PROTOCOL = DexProtocol.PancakeSwapV2


class PancakeSwapV2Pool(Contract):
    class Config:
        schema_extra = {
            "examples": [{'address': '0x2594566669abc983e286aa5c20468ab903287448'}]
        }


PANCAKESWAP_V2_VERSION = '0.1'


class PancakeSwapV2DexPoolPriceInput(PancakeSwapV2Pool, DexPoolPriceInput):
    class Config:
        schema_extra = {
            'examples': [{"address": "0x2594566669abc983e286aa5c20468ab903287448",  # AAVE-USDC
                          "price_slug": "pancakeswap-v2.get-weighted-price",
                          "ref_price_slug": "pancakeswap-v2.get-ring0-ref-price",
                          "weight_power": 4.0,
                          "protocol": "pancakeswap-v2"}]
        }


@Model.describe(slug="pancakeswap-v2.get-factory",
                version=PANCAKESWAP_V2_VERSION,
                display_name="PancakeSwapV2 - get factory",
                description="Returns the address of PancakeSwapV2 factory contract",
                category='protocol',
                subcategory='pancakeswap-v2',
                output=Contract)
class PancakeSwapV2GetFactory(UniswapV2PoolMeta, PancakeSwapV2FactoryMeta):
    def run(self, _) -> Contract:
        return self.get_factory(self.FACTORY_ADDRESS[self.context.network])


@Model.describe(slug="pancakeswap-v2.get-pool-by-pair",
                version=PANCAKESWAP_V2_VERSION,
                display_name="PancakeSwapV2 get pool for a pair of tokens",
                description=("Returns the addresses of the pool of input tokens"),
                category='protocol',
                subcategory='pancakeswap-v2',
                input=DexPoolInput,
                output=Maybe[Contract])
class PancakeSwapV2GetPair(UniswapV2PoolMeta, PancakeSwapV2FactoryMeta):
    def run(self, input: DexPoolInput) -> Maybe[Contract]:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_pair(factory_addr, input.token0.address, input.token1.address)


@Model.describe(slug="pancakeswap-v2.all-pools",
                version=PANCAKESWAP_V2_VERSION,
                display_name="PancakeSwapV2 all pairs",
                description="Returns the addresses of all pairs on PancakeSwapV2 protocol",
                category='protocol',
                subcategory='pancakeswap-v2',
                input=EmptyInputSkipTest,
                output=Some[Address])
class PancakeSwapV2AllPairs(UniswapV2PoolMeta, PancakeSwapV2FactoryMeta):
    def run(self, _) -> Some[Address]:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_all_pairs(factory_addr)


@Model.describe(slug="pancakeswap-v2.all-pools-events",
                version=PANCAKESWAP_V2_VERSION,
                display_name="PancakeSwap V2 all pairs from events",
                description=("Returns the addresses of all pairs on "
                             "PancakeSwap V2 protocol from events"),
                category='protocol',
                subcategory='pancakeswap-v2',
                input=EmptyInputSkipTest,
                output=Records)
class PancakeSwapV2AllPairsEvents(UniswapV2PoolMeta, PancakeSwapV2FactoryMeta):
    def run(self, _) -> Records:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_all_pairs_events(
            factory_addr, _from_block=0, _to_block=self.context.block_number)


@Model.describe(slug='pancakeswap-v2.all-pools-ledger',
                version=PANCAKESWAP_V2_VERSION,
                display_name='PancakeSwap V2 Token Pools - from ledger',
                description='The PancakeSwap V2 pools that support a token contract',
                category='protocol',
                subcategory='pancakeswap-v2',
                input=EmptyInputSkipTest,
                output=Records)
class PancakeSwapV2AllPairsLedger(UniswapV2PoolMeta, PancakeSwapV2FactoryMeta):
    def run(self, _) -> Records:
        return self.get_all_pools_ledger(self.FACTORY_ADDRESS[self.context.network])


@Model.describe(slug='pancakeswap-v2.get-pools',
                version=PANCAKESWAP_V2_VERSION,
                display_name='PancakeSwapV2 Token Pools',
                description='The PancakeSwapV2 pool pools that support a token contract',
                category='protocol',
                subcategory='pancakeswap-v2',
                input=Token,
                output=Contracts)
class PancakeSwapV2GetPoolsForToken(UniswapV2PoolMeta, PancakeSwapV2FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(factory_addr, self.PROTOCOL, [input.address])
        return Contracts.from_addresses(pools)


@Model.describe(slug='pancakeswap-v2.get-pools-ledger',
                version=PANCAKESWAP_V2_VERSION,
                display_name='PancakeSwapV2 Token Pools',
                description='The PancakeSwapV2 pools that support a token contract - use ledger',
                category='protocol',
                subcategory='pancakeswap-v2',
                input=Token,
                output=Contracts)
class PancakeSwapV2GetPoolsForTokenLedger(UniswapV2PoolMeta, PancakeSwapV2FactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_pools_for_tokens_ledger(
            factory_addr, self.PROTOCOL, input.address)


@Model.describe(slug='pancakeswap-v2.get-pools-tokens',
                version=PANCAKESWAP_V2_VERSION,
                display_name='PancakeSwapV2 Pools for Tokens',
                description='The PancakeSwapV2 pools for multiple tokens',
                category='protocol',
                subcategory='pancakeswap-v2',
                input=Tokens,
                output=Contracts)
class PancakeSwapV2GetPoolsForTokens(UniswapV2PoolMeta, PancakeSwapV2FactoryMeta):
    def run(self, input: Tokens) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(
            factory_addr, self.PROTOCOL, [tok.address for tok in input.tokens])
        return Contracts.from_addresses(list(set(pools)))


@Model.describe(slug='pancakeswap-v2.get-ring0-ref-price',
                version=PANCAKESWAP_V2_VERSION,
                display_name='PancakeSwapV2 Ring0 Reference Price',
                description='The PancakeSwapV2 pools that support the ring0 tokens',
                category='protocol',
                subcategory='pancakeswap-v2',
                input=PriceWeight,
                output=dict)
class PancakeSwapV2GetRing0RefPrice(UniswapV2PoolMeta, PancakeSwapV2FactoryMeta):
    def run(self, input: PriceWeight) -> dict:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_ref_price(factory_addr, self.PROTOCOL, input.weight_power)


@Model.describe(slug='pancakeswap-v2.get-pool-info-token-price',
                version=PANCAKESWAP_V2_VERSION,
                display_name='PancakeSwapV2 Token Pools',
                description='Gather price and liquidity information from pools for a Token',
                category='protocol',
                subcategory='pancakeswap-v2',
                input=DexPriceTokenInput,
                output=Some[PoolPriceInfo])
class PancakeSwapV2GetTokenPriceInfo(UniswapV2PoolMeta, PancakeSwapV2FactoryMeta):
    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        pools = self.context.run_model('pancakeswap-v2.get-pools', input,
                                       return_type=Contracts)
        return self.get_pools_info(input,
                                   pools,
                                   model_slug='uniswap-v2.get-pool-price-info',
                                   price_slug='pancakeswap-v2.get-weighted-price',
                                   ref_price_slug='pancakeswap-v2.get-ring0-ref-price',
                                   _protocol=self.PROTOCOL)
