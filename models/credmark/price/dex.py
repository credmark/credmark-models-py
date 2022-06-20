# pylint: disable=locally-disabled, unused-import
from abc import abstractmethod
from typing import List
import pandas as pd
from credmark.cmf.model import Model, ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError, ModelRunError

from credmark.cmf.types import Price, Token
from credmark.cmf.types.compose import (MapBlockTimeSeriesOutput,
                                        MapInputsInput, MapInputsOutput)
from models.dtos.price import PoolPriceAggregatorInput, PoolPriceInfos

PRICE_DATA_ERROR_DESC = ModelDataErrorDesc(
    code=ModelDataError.Codes.NO_DATA,
    code_desc='No pools to aggregate for token price')


@Model.describe(slug='price.pool-aggregator',
                version='1.1',
                display_name='Token Price from DEX pools, weighted by liquidity',
                description='Aggregate prices from pools weighted by liquidity',
                input=PoolPriceAggregatorInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class PoolPriceAggregator(Model):
    def run(self, input: PoolPriceAggregatorInput) -> Price:
        if len(input.pool_price_infos) == 0:
            raise ModelDataError(f'No pool to aggregate for {input.token}')

        df = pd.DataFrame(input.dict()['pool_price_infos'])

        if len(input.pool_price_infos) == 1:
            return Price(price=input.pool_price_infos[0].price, src=input.price_src)

        product_of_price_liquidity = (df.price * df.liquidity ** input.weight_power).sum()
        sum_of_liquidity = (df.liquidity ** input.weight_power).sum()
        price = product_of_price_liquidity / sum_of_liquidity
        return Price(price=price, src=input.price_src)


class PriceWeight:
    WEIGHT_POWER = 1.0
    # TODO: more price weight-related methods


class DexWeightedPrice(Model, PriceWeight):
    @abstractmethod
    def run(self, input):
        ...

    def aggregate_pool(self, model_slug, input: Token):
        pool_price_infos = self.context.run_model(model_slug,
                                                  input=input)
        pool_aggregator_input = PoolPriceAggregatorInput(token=input,
                                                         **pool_price_infos,
                                                         price_src=self.slug,
                                                         weight_power=self.WEIGHT_POWER)
        return self.context.run_model('price.pool-aggregator',
                                      input=pool_aggregator_input,
                                      return_type=Price)


@Model.describe(slug='uniswap-v3.get-weighted-price',
                version='1.1',
                display_name='Uniswap v3 - get price weighted by liquidity',
                description='The Uniswap v3 pools that support a token contract',
                input=Token,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class UniswapV3WeightedPrice(DexWeightedPrice):
    def run(self, input: Token) -> Price:
        return self.aggregate_pool('uniswap-v3.get-pool-price-info', input)


@Model.describe(slug='uniswap-v2.get-weighted-price',
                version='1.1',
                display_name='Uniswap v2 - get price weighted by liquidity',
                description='The Uniswap v2 pools that support a token contract',
                input=Token,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class UniswapV2WeightedPrice(DexWeightedPrice):
    def run(self, input: Token) -> Price:
        return self.aggregate_pool('uniswap-v2.get-pool-price-info', input)


@Model.describe(slug='sushiswap.get-weighted-price',
                version='1.1',
                display_name='Sushi v2 (Uniswap V2) - get price weighted by liquidity',
                description='The Sushi v2 pools that support a token contract',
                input=Token,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class SushiV2GetAveragePrice(DexWeightedPrice):
    def run(self, input: Token) -> Price:
        return self.aggregate_pool('sushiswap.get-pool-price-info', input)


@ Model.describe(slug='price.dex-blended',
                 version='1.2',
                 display_name='Token price - Credmark',
                 description='The Current Credmark Supported Price Algorithms',
                 developer='Credmark',
                 input=Token,
                 output=Price,
                 errors=PRICE_DATA_ERROR_DESC)
class PriceFromDexModel(Model, PriceWeight):
    """
    Return token's price
    """
    DEX_POOL_PRICE_INFO_MODELS: List[str] = ['uniswap-v2.get-pool-price-info',
                                             'sushiswap.get-pool-price-info',
                                             'uniswap-v3.get-pool-price-info']

    def run(self, input: Token) -> Price:
        all_pool_infos_results = self.context.run_model(
            slug='compose.map-inputs',
            input=MapInputsInput(
                modelSlug='compose.map-inputs',
                modelInputs=[{"modelSlug": slug, "modelInputs": [input]}
                             for slug in self.DEX_POOL_PRICE_INFO_MODELS]),
            return_type=MapInputsOutput[dict, MapInputsOutput[dict, PoolPriceInfos]]
        )
        all_pool_infos = []
        for dex_n, dex_result in enumerate(all_pool_infos_results):
            if dex_result.error is not None:
                raise ModelRunError(**dex_result.error.dict())
            if dex_result.output is None:
                raise ModelRunError(f'Empty result for {self.DEX_POOL_PRICE_INFO_MODELS[dex_n]}')

            for pool_result in dex_result.output:
                if pool_result.error is not None:
                    self.logger.error(pool_result.error)
                    raise ModelRunError(pool_result.error.message)
                if pool_result.output is None:
                    self.logger.error(pool_result.error)
                    raise ModelRunError(f'None result for {pool_result.input}')

                all_pool_infos.extend(pool_result.output)

        non_zero_pools = {ii.src for ii in all_pool_infos if ii.liquidity > 0}
        zero_pools = {ii.src for ii in all_pool_infos if ii.liquidity == 0}
        pool_aggregator_input = PoolPriceAggregatorInput(
            token=input,
            pool_price_infos=all_pool_infos,
            price_src=(f'{self.slug}|'
                       f'Non-zero:{",".join(non_zero_pools)}|'
                       f'Zero:{",".join(zero_pools)}'),
            weight_power=self.WEIGHT_POWER)
        return self.context.run_model('price.pool-aggregator',
                                      input=pool_aggregator_input,
                                      return_type=Price)
