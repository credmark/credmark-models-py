# pylint: disable=locally-disabled, unsupported-membership-test, pointless-string-statement, line-too-long, invalid-name
from abc import abstractmethod

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (
    Address,
    Maybe,
    Network,
    Price,
    PriceWithQuote,
    Some,
    Token,
)
from credmark.cmf.types.compose import MapInputsOutput

from models.dtos.pool import PoolPriceInfo
from models.dtos.price import (
    PRICE_DATA_ERROR_DESC,
    DexPoolAggregationInput,
    DexPriceTokenInput,
)

DEX_PRICE_MODEL_VERSION = '1.28'


@Model.describe(slug='price.pool-aggregator',
                version=DEX_PRICE_MODEL_VERSION,
                display_name='Token Price from DEX pools, weighted by liquidity',
                description='Aggregate prices from pools weighted by liquidity',
                category='dex',
                subcategory='price',
                tags=['price'],
                input=DexPoolAggregationInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class PoolPriceAggregator(Model):
    def run(self, input: DexPoolAggregationInput) -> Price:
        all_pool_infos = input.some

        if len(all_pool_infos) == 0:
            raise ModelRunError(
                f'[{self.context.block_number}] No pool to aggregate for {input}')

        non_zero_pools = [
            ii.pool_address for ii in all_pool_infos
            if (ii.token0_address == input.address and ii.one_tick_liquidity0 > 1e-8) or
               (ii.token1_address == input.address and ii.one_tick_liquidity1 > 1e-8)]

        zero_pools = [
            ii.pool_address for ii in all_pool_infos
            if (ii.token0_address == input.address and ii.one_tick_liquidity0 <= 1e-8) or
               (ii.token1_address == input.address and ii.one_tick_liquidity1 <= 1e-8)]

        df = (input
              .to_dataframe()
              .assign(
                  price_t=lambda x: x.price0.where(x.token0_address == input.address,
                                                   x.price1) * x.ref_price,
                  tick_liquidity_t=lambda x: x.one_tick_liquidity0.where(
                      x.token0_address == input.address, x.one_tick_liquidity1),
                  tick_liquidity_other=lambda x: x.one_tick_liquidity0.where(
                      x.token0_address != input.address, x.one_tick_liquidity1))
              )

        price_src = (f'{",".join([x.split(".")[0] for x in df.src.unique()])}|'
                     f'Non-zero:{len(non_zero_pools)}|'
                     f'Zero:{len(zero_pools)}')

        sum_of_liquidity_t = df.tick_liquidity_t.sum()
        _sum_of_liquidity_other = df.tick_liquidity_other.sum()

        if sum_of_liquidity_t <= 1e-8:
            raise ModelDataError(f'There is no liquidity ({sum_of_liquidity_t} <= 1e-8) in {len(zero_pools)} pools '
                                 f'for {input.address}.')

        if len(input.some) == 1:
            return Price(price=df.price_t[0], src=price_src)

        # self.logger.info(df)

        product_of_price_liquidity_power = (
            df.price_t * df.tick_liquidity_t ** input.weight_power).sum()
        sum_of_liquidity_power = (
            df.tick_liquidity_t ** input.weight_power).sum()
        price = product_of_price_liquidity_power / sum_of_liquidity_power
        return Price(price=price, src=f'{price_src}|{input.weight_power}')


class DexWeightedPrice(Model):
    @abstractmethod
    def run(self, input):
        ...

    def aggregate_pool(self, model_slug, input: DexPriceTokenInput):
        pool_price_infos = self.context.run_model(model_slug, input)

        pool_aggregator_input = DexPoolAggregationInput(**input.dict(),
                                                        **pool_price_infos)

        return PoolPriceAggregator(self.context).run(pool_aggregator_input)


@Model.describe(slug='uniswap-v3.get-weighted-price-maybe',
                version=DEX_PRICE_MODEL_VERSION,
                display_name='Uniswap v3 - get price weighted by liquidity',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                tags=['price'],
                input=DexPriceTokenInput,
                output=Maybe[Price],
                errors=PRICE_DATA_ERROR_DESC)
class UniswapV3WeightedPriceMaybe(DexWeightedPrice):
    def run(self, input: DexPriceTokenInput) -> Maybe[Price]:
        try:
            price = self.context.run_model('uniswap-v3.get-weighted-price',
                                           input=input,
                                           return_type=Price)
            return Maybe(just=price)
        except ModelRunError as err:
            if 'No pool to aggregate' in err.data.message:
                return Maybe.none()
            raise


@Model.describe(slug='uniswap-v3.get-weighted-price',
                version=DEX_PRICE_MODEL_VERSION,
                display_name='Uniswap v3 - get price weighted by liquidity',
                description='The Uniswap v3 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v3',
                tags=['price'],
                input=DexPriceTokenInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class UniswapV3WeightedPrice(DexWeightedPrice):
    def run(self, input: DexPriceTokenInput) -> Price:
        return self.aggregate_pool('uniswap-v3.get-pool-info-token-price', input)


@Model.describe(slug='uniswap-v2.get-weighted-price',
                version=DEX_PRICE_MODEL_VERSION,
                display_name='Uniswap v2 - get price weighted by liquidity',
                description='The Uniswap v2 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v2',
                tags=['price'],
                input=DexPriceTokenInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class UniswapV2WeightedPrice(DexWeightedPrice):
    def run(self, input: DexPriceTokenInput) -> Price:
        return self.aggregate_pool('uniswap-v2.get-pool-info-token-price', input)


@Model.describe(slug='sushiswap.get-weighted-price',
                version=DEX_PRICE_MODEL_VERSION,
                display_name='Sushi (Uniswap V2) - get price weighted by liquidity',
                description='The Sushi v2 pools that support a token contract',
                category='protocol',
                subcategory='sushi-v2',
                tags=['price'],
                input=DexPriceTokenInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class SushiV2GetAveragePrice(DexWeightedPrice):
    def run(self, input: DexPriceTokenInput) -> Price:
        return self.aggregate_pool('sushiswap.get-pool-info-token-price', input)


@Model.describe(slug='pancakeswap-v2.get-weighted-price',
                version=DEX_PRICE_MODEL_VERSION,
                display_name='PancakeSwap V2 (Uniswap V2) - get price weighted by liquidity',
                description='The Pancake pools that support a token contract',
                category='protocol',
                subcategory='pancake',
                tags=['price'],
                input=DexPriceTokenInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class PancakeV2GetAveragePrice(DexWeightedPrice):
    def run(self, input: DexPriceTokenInput) -> Price:
        return self.aggregate_pool('pancakeswap-v2.get-pool-info-token-price', input)


@Model.describe(slug='pancakeswap-v3.get-weighted-price',
                version=DEX_PRICE_MODEL_VERSION,
                display_name='PancakeSwap V3 (Uniswap V3) - get price weighted by liquidity',
                description='The Pancake pools that support a token contract',
                category='protocol',
                subcategory='pancake',
                tags=['price'],
                input=DexPriceTokenInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class PancakeV3GetAveragePrice(DexWeightedPrice):
    def run(self, input: DexPriceTokenInput) -> Price:
        return self.aggregate_pool('pancakeswap-v3.get-pool-info-token-price', input)


@Model.describe(slug='price.dex-blended-maybe',
                version=DEX_PRICE_MODEL_VERSION,
                display_name='Token price - Credmark',
                description='The Current Credmark Supported Price Algorithms',
                developer='Credmark',
                category='price',
                subcategory='dex',
                tags=['dex', 'price'],
                input=DexPriceTokenInput,
                output=Maybe[PriceWithQuote])
class PriceFromDexModelMaybe(Model):
    """
    Return token's price
    """

    def run(self, input: Token) -> Maybe[PriceWithQuote]:
        try:
            price = self.context.run_model('price.dex-blended',
                                           input=input,
                                           return_type=PriceWithQuote)
            return Maybe(just=price)
        except ModelRunError as err:
            if 'No pool to aggregate' in err.data.message:
                return Maybe.none()
            raise


@Model.describe(slug='price.dex-blended',
                version=DEX_PRICE_MODEL_VERSION,
                display_name='Credmark Token Price from Dex',
                description='The Current Credmark Supported Price Algorithms',
                developer='Credmark',
                category='price',
                subcategory='dex',
                tags=['dex', 'price'],
                input=DexPriceTokenInput,
                output=PriceWithQuote,
                errors=PRICE_DATA_ERROR_DESC)
class PriceFromDexModel(Model):
    """
    Return token's price
    """

    def run(self, input: DexPriceTokenInput) -> PriceWithQuote:
        try:
            all_pool_infos = self.context.run_model('price.dex-pool',
                                                    input=input,
                                                    return_type=Some[PoolPriceInfo],
                                                    local=True).some

            pool_aggregator_input = DexPoolAggregationInput(**input.dict(), some=all_pool_infos)

            price = PoolPriceAggregator(self.context).run(pool_aggregator_input)

            # Above code replaced code below as a saving to a model call
            # price = self.context.run_model('price.pool-aggregator',
            #                              input=pool_aggregator_input,
            #                              return_type=Price,
            #                              local=True)

            return PriceWithQuote.usd(**price.dict())
        except (ModelDataError, ModelRunError):
            addr_maybe = self.context.run_model('token.underlying-maybe',
                                                input=input,
                                                return_type=Maybe[Address],
                                                local=True)
            if addr_maybe.just is not None:
                input.address = addr_maybe.just
                return self.context.run_model(self.slug, input, return_type=PriceWithQuote)

            raise


@Model.describe(slug='price.dex-pool',
                version=DEX_PRICE_MODEL_VERSION,
                display_name='',
                description='The Current Credmark Supported Price Algorithms',
                developer='Credmark',
                category='price',
                subcategory='dex',
                tags=['dex', 'price'],
                input=DexPriceTokenInput,
                output=Some[PoolPriceInfo])
class PriceInfoFromDex(Model):
    DEX_POOL_PRICE_INFO_MODELS: dict[Network, list[str]] = {
        Network.Mainnet: ['uniswap-v2.get-pool-info-token-price',
                          'sushiswap.get-pool-info-token-price',
                          'uniswap-v3.get-pool-info-token-price'],
        Network.BSC: ['pancakeswap-v2.get-pool-info-token-price',
                      'pancakeswap-v3.get-pool-info-token-price'], }

    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        # For testing with other power, set this = default power for the token here
        # if input.address == '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': # WETH
        #    input.weight_power = 4.0
        # if input.address == '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9':  # AAVE
        #    input.weight_power = 4.0

        model_inputs = [{"modelSlug": slug,
                         "modelInputs": [input]}
                        for slug in self.DEX_POOL_PRICE_INFO_MODELS[self.context.network]]

        def _use_compose():
            all_pool_infos_results = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': 'compose.map-inputs',
                       'modelInputs': model_inputs},
                return_type=MapInputsOutput[dict, MapInputsOutput[dict, Some[PoolPriceInfo]]])

            all_pool_infos = []
            for dex_n, dex_result in enumerate(all_pool_infos_results):
                if dex_result.output is not None:
                    for pool_result in dex_result.output:
                        if pool_result.output is not None:
                            all_pool_infos.extend(pool_result.output)
                        elif pool_result.error is not None:
                            self.logger.error(pool_result.error)
                            raise ModelRunError(
                                (f'Error with models({self.context.block_number}).' +
                                 f'{model_inputs[dex_n]["modelSlug"].replace("-","_")}' +
                                 f'({pool_result.input}). ' +
                                 pool_result.error.message))
                elif dex_result.error is not None:
                    self.logger.error(dex_result.error)
                    raise ModelRunError(
                        (f'Error with models({self.context.block_number}).' +
                         f'{model_inputs[dex_n]}. ' +
                         dex_result.error.message))
                else:
                    raise ModelRunError(
                        'compose.map-inputs: output/error cannot be both None')
            return all_pool_infos

        def _use_for(local):
            all_pool_infos = []
            for m_input in model_inputs:
                infos = self.context.run_model(m_input['modelSlug'],
                                               m_input['modelInputs'][0],
                                               Some[PoolPriceInfo],
                                               local=local)
                all_pool_infos.extend(infos.some)
            return all_pool_infos

        return Some[PoolPriceInfo](some=_use_for(False))


@Model.describe(slug='price.dex-db-prefer',
                version=DEX_PRICE_MODEL_VERSION,
                display_name='Credmark Token Price from Dex (Prefer to use DB)',
                description='Retrieve price from DB or call model',
                developer='Credmark',
                category='price',
                subcategory='dex',
                tags=['dex', 'price'],
                input=Token,
                output=PriceWithQuote,
                errors=PRICE_DATA_ERROR_DESC)
class PriceFromDexPreferModel(Model):
    """
    Return token's price from Dex with Chainlink as fallback

    **`price.quote`** calls `chainlink`, `curve` then `price.dex-db-prefer`

    **`price.cex`** calls `chainlink` only.
    **'price.dex'** calls `price.dex-db-prefer` then calls `curve`
    price.dex-db-prefer` calls `price.dex-db`, then `price.dex-blended` (uniswap v2 / v3 and sushiswap)

    """

    def run(self, input: Token) -> PriceWithQuote:
        try:
            price_dex = self.context.run_model(
                'price.dex-db', input=input)
            if price_dex['liquidity'] > 1e-8:
                return PriceWithQuote.usd(price=price_dex['price'], src=price_dex['protocol'])
            raise ModelDataError(f'There is no liquidity ({price_dex["liquidity"]}) for {input.address}.')
        except (ModelDataError, ModelRunError) as err:
            # ModelRunError => "No pool to aggregate for" from price.dex-blended
            # ModelDataError => "No price for" from price.dex-db
            if "No price for" in err.data.message or "No pool to aggregate for" in err.data.message:
                return self.context.run_model(
                    'price.dex-blended',
                    input={'address': input.address},
                    return_type=PriceWithQuote)
            raise
