# pylint: disable=line-too-long

from credmark.cmf.model import Model
from credmark.cmf.types import Address, Contract, Contracts, Maybe, Network, Records, Some, Token, Tokens
from credmark.dto import EmptyInputSkipTest

from models.credmark.protocols.dexes.uniswap.uniswap_v2_meta import UniswapV2PoolMeta
from models.dtos.pool import DexPoolInput, PoolPriceInfo
from models.dtos.price import DexPoolPriceInput, DexPriceTokenInput, DexProtocol, PriceWeight


class SushiSwapFactoryMeta:
    FACTORY_ADDRESS = {
        Network.Mainnet: Address('0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac'),
    } | {
        k: Address('0xc35DADB65012eC5796536bD9864eD8773aBc74C4')
        for k in [Network.Rinkeby, Network.Görli, Network.Kovan]
    }
    PROTOCOL = DexProtocol.SushiSwap


class SushiSwapPool(Contract):
    class Config:
        schema_extra = {
            "examples": [{'address': '0x6a091a3406E0073C3CD6340122143009aDac0EDa'}]
        }


SUSHISWAPV3_VERSION = '0.1'


class SushiSwapDexPoolPriceInput(SushiSwapPool, DexPoolPriceInput):
    class Config:
        schema_extra = {
            'examples': [{"address": "0x6a091a3406E0073C3CD6340122143009aDac0EDa",  # ILV-WETH
                          "price_slug": "sushiswap.get-weighted-price",
                          "ref_price_slug": "sushiswap.get-ring0-ref-price",
                          "weight_power": 4.0,
                          "protocol": "sushiswap"}]
        }


@Model.describe(slug="sushiswap.get-factory",
                version=SUSHISWAPV3_VERSION,
                display_name="SushiSwap - get factory",
                description="Returns the address of SushiSwap factory contract",
                category='protocol',
                subcategory='sushi',
                output=Contract)
class SushiSwapGetFactory(UniswapV2PoolMeta, SushiSwapFactoryMeta):
    def run(self, _) -> Contract:
        return self.get_factory(self.FACTORY_ADDRESS[self.context.network])


@Model.describe(slug="sushiswap.get-pool-by-pair",
                version=SUSHISWAPV3_VERSION,
                display_name="SushiSwap get pool for a pair of tokens",
                description=("Returns the addresses of the pool of input tokens"),
                category='protocol',
                subcategory='sushi',
                input=DexPoolInput,
                output=Maybe[Contract])
class SushiSwapGetPair(UniswapV2PoolMeta, SushiSwapFactoryMeta):
    def run(self, input: DexPoolInput) -> Maybe[Contract]:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_pair(factory_addr, input.token0.address, input.token1.address)


@Model.describe(slug="sushiswap.all-pools",
                version=SUSHISWAPV3_VERSION,
                display_name="SushiSwap all pairs",
                description="Returns the addresses of all pairs on SushiSwap protocol",
                category='protocol',
                subcategory='sushi',
                input=EmptyInputSkipTest,
                output=Some[Address])
class SushiSwapAllPairs(UniswapV2PoolMeta, SushiSwapFactoryMeta):
    def run(self, _) -> Some[Address]:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_all_pairs(factory_addr)


@Model.describe(slug="sushiswap.all-pools-events",
                version=SUSHISWAPV3_VERSION,
                display_name="SushiSwap all pairs from events",
                description="Returns the addresses of all pairs on SushiSwap protocol from events",
                category='protocol',
                subcategory='sushi',
                input=EmptyInputSkipTest,
                output=Records)
class SushiSwapAllPairsEvents(UniswapV2PoolMeta, SushiSwapFactoryMeta):
    def run(self, _) -> Records:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_all_pairs_events(
            factory_addr, _from_block=0, _to_block=self.context.block_number)


@Model.describe(slug='sushiswap.all-pools-ledger',
                version=SUSHISWAPV3_VERSION,
                display_name='SushiSwap Token Pools - from ledger',
                description='The SushiSwap pools that support a token contract',
                category='protocol',
                subcategory='sushi',
                input=EmptyInputSkipTest,
                output=Records)
class SushiSwapAllPairsLedger(UniswapV2PoolMeta, SushiSwapFactoryMeta):
    def run(self, _) -> Records:
        return self.get_all_pools_ledger(self.FACTORY_ADDRESS[self.context.network])


@Model.describe(slug='sushiswap.get-pools',
                version=SUSHISWAPV3_VERSION,
                display_name='SushiSwap Token Pools',
                description='The SushiSwap pool pools that support a token contract',
                category='protocol',
                subcategory='sushi',
                input=Token,
                output=Contracts)
class SushiSwapGetPoolsForToken(UniswapV2PoolMeta, SushiSwapFactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(factory_addr, self.PROTOCOL, [input.address])
        return Contracts.from_addresses(pools)


@Model.describe(slug='sushiswap.get-pools-ledger',
                version=SUSHISWAPV3_VERSION,
                display_name='SushiSwap Token Pools',
                description='The SushiSwap pools that support a token contract - use ledger',
                category='protocol',
                subcategory='sushi',
                input=Token,
                output=Contracts)
class SushiSwapV2GetPoolsForTokenLedger(UniswapV2PoolMeta, SushiSwapFactoryMeta):
    def run(self, input: Token) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_pools_for_tokens_ledger(
            factory_addr, self.PROTOCOL, input.address)


@Model.describe(slug='sushiswap.get-pools-tokens',
                version=SUSHISWAPV3_VERSION,
                display_name='SushiSwap Pools for Tokens',
                description='The SushiSwap pools for multiple tokens',
                category='protocol',
                subcategory='sushi',
                input=Tokens,
                output=Contracts)
class SushiSwapGetPoolsForTokens(UniswapV2PoolMeta, SushiSwapFactoryMeta):
    def run(self, input: Tokens) -> Contracts:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        pools = self.get_pools_for_tokens(
            factory_addr, self.PROTOCOL, [tok.address for tok in input.tokens])
        return Contracts.from_addresses(list(set(pools)))


@Model.describe(slug='sushiswap.get-ring0-ref-price',
                version=SUSHISWAPV3_VERSION,
                display_name='SushiSwap Ring0 Reference Price',
                description='The SushiSwap pools that support the ring0 tokens',
                category='protocol',
                subcategory='sushi',
                input=PriceWeight,
                output=dict)
class SushiSwapGetRing0RefPrice(UniswapV2PoolMeta, SushiSwapFactoryMeta):
    def run(self, input: PriceWeight) -> dict:
        factory_addr = self.FACTORY_ADDRESS[self.context.network]
        return self.get_ref_price(factory_addr, self.PROTOCOL, input.weight_power)


@Model.describe(slug='sushiswap.get-pool-info-token-price',
                version=SUSHISWAPV3_VERSION,
                display_name='SushiSwap Token Pools',
                description='Gather price and liquidity information from pools for a Token',
                category='protocol',
                subcategory='sushi',
                input=DexPriceTokenInput,
                output=Some[PoolPriceInfo])
class SushiSwapGetTokenPriceInfo(UniswapV2PoolMeta, SushiSwapFactoryMeta):
    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        pools = self.context.run_model('sushiswap.get-pools', input,
                                       return_type=Contracts)
        return self.get_pools_info(input,
                                   pools,
                                   model_slug='uniswap-v2.get-pool-price-info',
                                   price_slug='sushiswap.get-weighted-price',
                                   ref_price_slug='sushiswap.get-ring0-ref-price',
                                   _protocol=self.PROTOCOL)
