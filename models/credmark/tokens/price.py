# pylint: disable=locally-disabled, unused-import
import pandas as pd
from typing import List

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import (
    Token,
    Price,
    Contract,
    Accounts,
    Contracts,
)

from credmark.dto import DTO, IterableListGenericDTO

from models.dtos.price import PoolPriceAggregatorInput, PoolPriceInfos


@Model.describe(slug='price',
                version='1.0',
                display_name='Token Price',
                description='DEPRECATED - use token.price',
                input=Token,
                output=Price)
class PriceModel(Model):
    """
    Return token's price (DEPRECATED) - use token.price
    """

    def run(self, input: Token) -> Price:
        return self.context.run_model('token.price', input, return_type=Price)


@Model.describe(slug='price.pool-aggregator',
                version='1.1',
                display_name='Token Price from DEX pools, weighted by liquidity',
                description='Aggregate prices from pools weighted by liquidity',
                input=PoolPriceAggregatorInput,
                output=Price)
class PoolPriceAggregator(Model):
    def run(self, input: PoolPriceAggregatorInput) -> Price:
        if len(input.pool_price_infos) == 0:
            return Price(price=None, src=input.price_src)

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


@Model.describe(slug='uniswap-v3.get-weighted-price',
                version='1.1',
                display_name='Uniswap v3 - get price weighted by liquidity',
                description='The Uniswap v3 pools that support a token contract',
                input=Token,
                output=Price)
class UniswapV3GetAveragePrice(Model, PriceWeight):
    def run(self, input: Token) -> Price:
        pool_price_infos = self.context.run_model('uniswap-v3.get-pool-price-info',
                                                  input=input)
        pool_aggregator_input = PoolPriceAggregatorInput(**pool_price_infos,
                                                         price_src=self.slug,
                                                         weight_power=self.WEIGHT_POWER)
        return self.context.run_model('price.pool-aggregator',
                                      input=pool_aggregator_input,
                                      return_type=Price)


@Model.describe(slug='uniswap-v2.get-weighted-price',
                version='1.1',
                display_name='Uniswap v2 - get price weighted by liquidity',
                description='The Uniswap v2 pools that support a token contract',
                input=Token,
                output=Price)
class UniswapV2GetAveragePrice(Model, PriceWeight):
    def run(self, input: Token) -> Price:
        pool_price_infos = self.context.run_model('uniswap-v2.get-pool-price-info',
                                                  input=input)
        pool_aggregator_input = PoolPriceAggregatorInput(**pool_price_infos,
                                                         price_src=self.slug,
                                                         weight_power=self.WEIGHT_POWER)
        return self.context.run_model('price.pool-aggregator',
                                      input=pool_aggregator_input,
                                      return_type=Price)


@Model.describe(slug='sushiswap.get-weighted-price',
                version='1.1',
                display_name='Sushi v2 (Uniswap V2) - get price weighted by liquidity',
                description='The Sushi v2 pools that support a token contract',
                input=Token,
                output=Price)
class SushiV2GetAveragePrice(Model, PriceWeight):
    def run(self, input: Token) -> Price:
        pool_price_infos = self.context.run_model('sushiswap.get-pool-price-info',
                                                  input=input)
        pool_aggregator_input = PoolPriceAggregatorInput(**pool_price_infos,
                                                         price_src=self.slug,
                                                         weight_power=self.WEIGHT_POWER)
        return self.context.run_model('price.pool-aggregator',
                                      input=pool_aggregator_input,
                                      return_type=Price)


@ Model.describe(slug='token.pool-price-info',
                 version='1.1',
                 display_name='Token Price - all pools',
                 description='The Current Credmark Supported Price Algorithm',
                 developer='Credmark',
                 input=Token,
                 output=PoolPriceInfos)
class TokenPoolPriceInfo(Model):
    def run(self, input: Token) -> PoolPriceInfos:
        pool_price_infos_univ2 = self.context.run_model('uniswap-v2.get-pool-price-info',
                                                        input=input)
        pool_price_infos_sushi = self.context.run_model('sushiswap.get-pool-price-info',
                                                        input=input)
        pool_price_infos_univ3 = self.context.run_model('uniswap-v3.get-pool-price-info',
                                                        input=input)
        all_infos = (pool_price_infos_univ2['pool_price_infos'] +
                     pool_price_infos_sushi['pool_price_infos'] +
                     pool_price_infos_univ3['pool_price_infos'])

        return PoolPriceInfos(pool_price_infos=all_infos)


@ Model.describe(slug='token.price',
                 version='1.1',
                 display_name='Token Price - weighted by liquidity',
                 description='The Current Credmark Supported Price Algorithm',
                 developer='Credmark',
                 input=Token,
                 output=Price)
class TokenPriceModel(Model, PriceWeight):
    """
    Return token's price
    """

    def run(self, input: Token) -> Price:
        all_pool_infos = self.context.run_model('token.pool-price-info',
                                                input=input,
                                                return_type=PoolPriceInfos)
        non_zero_pools = {ii.src for ii in all_pool_infos.pool_price_infos if ii.liquidity > 0}
        pool_aggregator_input = PoolPriceAggregatorInput(
            pool_price_infos=all_pool_infos.pool_price_infos,
            price_src=f'{self.slug}:{"|".join(non_zero_pools)}',
            weight_power=self.WEIGHT_POWER)
        return self.context.run_model('price.pool-aggregator',
                                      input=pool_aggregator_input,
                                      return_type=Price)
