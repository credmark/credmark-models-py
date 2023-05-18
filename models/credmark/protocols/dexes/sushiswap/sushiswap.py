from typing import Optional

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import Address, Contract, Contracts, Maybe, Network, Some, Token
from credmark.cmf.types.block_number import BlockNumberOutOfRangeError
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO, EmptyInput

from models.credmark.protocols.dexes.uniswap.uniswap_v2 import UniswapV2PoolMeta
from models.dtos.pool import PoolPriceInfo
from models.dtos.price import DexPricePoolInput, DexPriceTokenInput


class SushiswapContract(Contract):
    class Config:
        schema_extra = {
            "examples": [{'address': '0x6a091a3406E0073C3CD6340122143009aDac0EDa'}]
        }


class SushiswapDexPricePoolInput(SushiswapContract, DexPricePoolInput):
    price_slug: str
    ref_price_slug: Optional[str]

    class Config:
        schema_extra = {
            'examples': [{"address": "0x6a091a3406E0073C3CD6340122143009aDac0EDa",  # ILV-WETH
                          "price_slug": "sushiswap.get-weighted-price",
                          "ref_price_slug": "sushiswap.get-ring0-ref-price"}]
        }


@Model.describe(slug="sushiswap.get-v2-factory",
                version="1.0",
                display_name="Sushiswap - get factory",
                description="Returns the address of Sushiswap factory contract",
                category='protocol',
                subcategory='sushi',
                output=Contract)
class SushiswapV2Factory(Model):
    SUSHISWAP_V2_FACTORY_ADDRESS = {
        Network.Mainnet: Address('0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac'),
    } | {
        k: Address('0xc35DADB65012eC5796536bD9864eD8773aBc74C4')
        for k in [Network.Rinkeby, Network.Görli, Network.Kovan]
    }

    def run(self, _) -> Contract:
        addr = __class__.SUSHISWAP_V2_FACTORY_ADDRESS[self.context.network]
        cc = Contract(address=addr)
        _ = cc.abi
        return cc


@Model.describe(slug='sushiswap.get-pools',
                version='1.7',
                display_name='Sushiswap v2 Pools',
                description='The Sushiswap pools where a token is traded',
                category='protocol',
                subcategory='sushi',
                input=Token,
                output=Contracts)
class SushiswapGetPoolsForToken(Model, UniswapV2PoolMeta):
    def run(self, input: Token) -> Contracts:
        try:
            factory = self.context.run_model(
                'sushiswap.get-v2-factory', {},
                return_type=Contract, local=True)
            return self.get_uniswap_pools(self.context, factory.address, input.address)
        except BlockNumberOutOfRangeError:
            pass

        return Contracts(contracts=[])


@Model.describe(slug='sushiswap.get-ring0-ref-price',
                version='0.7',
                display_name='Uniswap v2 Token Pools',
                description='The Uniswap v2 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v2',
                output=dict)
class UniswapV2GetRing0RefPrice(Model, UniswapV2PoolMeta):
    def run(self, _: EmptyInput) -> dict:
        factory_addr = self.context.run_model(
            'sushiswap.get-v2-factory', {},
            return_type=Contract, local=True)
        return self.get_ref_price(self.context, factory_addr.address)


@Model.describe(slug='sushiswap.get-pools-ledger',
                version='0.2',
                display_name='Sushiswap v2 Pools',
                description='The Sushiswap pools where a token is traded',
                category='protocol',
                subcategory='sushi',
                input=Token,
                output=Contracts)
class SushiswapGetPoolsForTokenLedger(Model, UniswapV2PoolMeta):
    def run(self, input: Token) -> Contracts:
        try:
            factory = self.context.run_model(
                'sushiswap.get-v2-factory', {},
                return_type=Contract, local=True)
            return self.get_uniswap_pools_ledger(self.context, factory.address, input.address)
        except BlockNumberOutOfRangeError:
            pass

        return Contracts(contracts=[])


@Model.describe(slug="sushiswap.all-pools",
                version="1.2",
                display_name="Sushiswap all pairs",
                description="Returns the addresses of all pairs on Sushiswap protocol",
                category='protocol',
                subcategory='sushi')
class SushiswapAllPairs(Model):
    def run(self, _: EmptyInput) -> dict:
        contract = Contract(
            **self.context.models(local=True).sushiswap.get_v2_factory())
        allPairsLength = contract.functions.allPairsLength().call()
        sushiswap_pairs_addresses = []

        error_count = 0
        for i in range(allPairsLength):
            try:
                pair_address = contract.functions.allPairs(i).call()
                sushiswap_pairs_addresses.append(
                    Address(pair_address).checksum)
            except Exception:
                error_count += 1

        self.logger.warning(
            f'There are {error_count} errors in total {allPairsLength} pools.')

        return {"result": sushiswap_pairs_addresses,
                'all_pairs_length': allPairsLength,
                'error_count': error_count}


class SushiSwapPool(DTO):
    token0: Token
    token1: Token


@Model.describe(slug="sushiswap.get-pool",
                version="1.0",
                display_name="Sushiswap get pool for a pair of tokens",
                description=("Returns the addresses of the pool of "
                             "both tokens on Sushiswap protocol"),
                category='protocol',
                subcategory='sushi',
                input=SushiSwapPool)
class SushiswapGetPair(Model):
    def run(self, input: SushiSwapPool):
        self.logger.info(f'{input=}')
        contract = Contract(
            **self.context.models(local=True).sushiswap.get_v2_factory())

        if input.token0.address and input.token1.address:
            token0 = input.token0.address.checksum
            token1 = input.token1.address.checksum

            pair_pool = contract.functions.getPair(token0, token1).call()
            return {'pool': pair_pool}
        else:
            return {}


@Model.describe(slug='sushiswap.get-pool-info-token-price',
                version='1.14',
                display_name='Sushiswap Token Pools Price ',
                description='Gather price and liquidity information from pools',
                category='protocol',
                subcategory='sushi',
                input=DexPriceTokenInput,
                output=Some[PoolPriceInfo])
class SushiswapGetTokenPriceInfo(Model):
    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        pools = self.context.run_model('sushiswap.get-pools',
                                       input,
                                       return_type=Contracts,
                                       local=True)

        model_slug = 'uniswap-v2.get-pool-price-info'
        model_inputs = [
            SushiswapDexPricePoolInput(
                address=pool.address,
                price_slug='sushiswap.get-weighted-price',
                ref_price_slug='sushiswap.get-ring0-ref-price',
                weight_power=input.weight_power,
                debug=input.debug)
            for pool in pools]

        def _use_compose():
            pool_infos = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': model_slug,
                       'modelInputs': model_inputs},
                return_type=MapInputsOutput[dict, Maybe[PoolPriceInfo]])

            infos = []
            for pool_n, p in enumerate(pool_infos):
                if p.output is not None:
                    if p.output.is_just():
                        infos.append(p.output.just)
                elif p.error is not None:
                    self.logger.error(p.error)
                    raise ModelRunError(
                        (f'Error with models({self.context.block_number}).' +
                         f'{model_slug.replace("-","_")}({model_inputs[pool_n]}). ' +
                         p.error.message))
                else:
                    raise ModelRunError(
                        'compose.map-inputs: output/error cannot be both None')
            return infos

        def _use_for(local):
            infos = []
            for m_input in model_inputs:
                pi = self.context.run_model(model_slug,
                                            m_input,
                                            return_type=Maybe[PoolPriceInfo],
                                            local=local)
                if pi.is_just():
                    infos.append(pi.just)
            return infos

        infos = _use_for(local=True)

        return Some[PoolPriceInfo](some=infos)
