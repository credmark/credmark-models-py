from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import Address, Contract, Contracts, Token
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO, EmptyInput
from models.credmark.protocols.dexes.uniswap.uniswap_v2 import \
    UniswapV2PoolMeta
from models.dtos.price import Maybe, PoolPriceInfo, PoolPriceInfos


@Model.describe(slug="sushiswap.get-v2-factory",
                version="1.0",
                display_name="Sushiswap - get factory",
                description="Returns the address of Suishiswap factory contract",
                category='protocol',
                subcategory='sushi',
                input=EmptyInput,
                output=Contract)
class SushiswapV2Factory(Model):
    SUSHISWAP_V2_FACTORY_ADDRESS = {
        1: '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac',
    } | {
        k: '0xc35DADB65012eC5796536bD9864eD8773aBc74C4' for k in [3, 4, 5, 42]
    }

    def run(self, _) -> Contract:
        addr = self.SUSHISWAP_V2_FACTORY_ADDRESS[self.context.chain_id]
        cc = Contract(address=addr)
        _ = cc.abi
        return cc


@Model.describe(slug='sushiswap.get-pools',
                version='1.1',
                display_name='Sushiswap v2 Pools',
                description='The Sushiswap pools where a token is traded',
                category='protocol',
                subcategory='sushi',
                input=Token,
                output=Contracts)
class SushiswapGetPoolsForToken(Model, UniswapV2PoolMeta):
    def run(self, input: Token) -> Contracts:
        contract = Contract(**self.context.models.sushiswap.get_v2_factory())
        return self.get_uniswap_pools(input, contract.address)


@Model.describe(slug="sushiswap.all-pools",
                version="1.1",
                display_name="Sushiswap all pairs",
                description="Returns the addresses of all pairs on Suhsiswap protocol",
                category='protocol',
                subcategory='sushi')
class SushiswapAllPairs(Model):
    def run(self, input) -> dict:
        contract = Contract(**self.context.models.sushiswap.get_v2_factory())
        allPairsLength = contract.functions.allPairsLength().call()
        sushiswap_pairs_addresses = []

        error_count = 0
        for i in range(allPairsLength):
            try:
                pair_address = contract.functions.allPairs(i).call()
                sushiswap_pairs_addresses.append(Address(pair_address).checksum)
            except Exception as _err:
                error_count += 1

        self.logger.warning(f'There are {error_count} errors in total {allPairsLength} pools.')

        return {"result": sushiswap_pairs_addresses,
                'all_pairs_lenght': allPairsLength,
                'error_count': error_count}


class SushiSwapPool(DTO):
    token0: Token
    token1: Token


@Model.describe(slug="sushiswap.get-pool",
                version="1.0",
                display_name="Sushiswap get pool for a pair of tokens",
                description=("Returns the addresses of the pool of "
                             "both tokens on Suhsiswap protocol"),
                category='protocol',
                subcategory='sushi',
                input=SushiSwapPool)
class SushiswapGetPair(Model):
    def run(self, input: SushiSwapPool):
        self.logger.info(f'{input=}')
        contract = Contract(**self.context.models.sushiswap.get_v2_factory())

        if input.token0.address and input.token1.address:
            token0 = input.token0.address.checksum
            token1 = input.token1.address.checksum

            pair_pool = contract.functions.getPair(token0, token1).call()
            return {'pool': pair_pool}
        else:
            return {}


@Model.describe(slug='sushiswap.get-pool-info-token-price',
                version='1.2',
                display_name='Sushiswap Token Pools Price ',
                description='Gather price and liquidity information from pools',
                category='protocol',
                subcategory='sushi',
                input=Token,
                output=PoolPriceInfos)
class SushiswapGetTokenPriceInfo(Model):
    def run(self, input: Token) -> PoolPriceInfos:
        pools = self.context.run_model('sushiswap.get-pools',
                                       input,
                                       return_type=Contracts)

        # TODO: Too depths issue
        def _use_compose():
            model_slug = 'uniswap-v2.get-price-pool-info'
            model_inputs = [{'token': input, 'pool': pool} for pool in pools]
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
                        f'Error with {model_slug}(input={model_inputs[pool_n]}). ' +
                        p.error.message)
                else:
                    raise ModelRunError('compose.map-inputs: output/error cannot be both None')
            return infos

        def _use_for():
            model_slug = 'uniswap-v2.get-price-pool-info'
            model_inputs = [{'token': input, 'pool': pool} for pool in pools]
            infos = []
            for minput in model_inputs:
                pi = self.context.run_model(model_slug,
                                            minput,
                                            return_type=Maybe[PoolPriceInfo])
                if pi.is_just():
                    infos.append(pi.just)
            return infos

        infos = _use_compose()

        return PoolPriceInfos(infos=infos)
