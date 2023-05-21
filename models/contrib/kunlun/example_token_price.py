from credmark.cmf.model import Model
from credmark.cmf.types import Price, Some

from models.dtos.pool import PoolPriceInfo
from models.dtos.price import DexPoolAggregationInput, DexPriceTokenInput


@Model.describe(slug='contrib.example-token-price',
                version='1.1',
                display_name='Token Price - weighted by liquidity',
                description='The Current Credmark Supported Price Algorithm',
                developer='Credmark',
                input=DexPriceTokenInput,
                output=Price)
class TokenPriceModel(Model):
    """
    Return token's price
    """

    WEIGHT_POWER = 4

    def run(self, input: DexPriceTokenInput) -> Price:
        all_pool_infos = self.context.run_model('price.dex-pool',
                                                input=input,
                                                return_type=Some[PoolPriceInfo])

        # DexPoolAggregationInput is a DTO that embodies
        # -   token
        # -   pricing setup, and
        # -   pool information

        pool_aggregator_input = DexPoolAggregationInput(
            **all_pool_infos.dict(),
            **input.dict())

        return self.context.run_model('price.pool-aggregator',
                                      input=pool_aggregator_input,
                                      return_type=Price)
