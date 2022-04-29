# pylint:disable=locally-disabled,line-too-long

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError

import os
import json
import numpy as np

from models.credmark.algorithms.risk import (
    GeneralHistoricalPlan
)

from models.dtos.price import PoolPriceInfos


@Model.describe(slug='finance.var-prices',
                version='1.0',
                display_name='Value at Risk - prices',
                description='Value at Risk - prices',
                input=Token,
                output=dict)
class ValueAtRiskPrices(Model):
    def run(self, input: dict) -> dict:
        use_kitchen = True
        verbose = True
        block_number = int(self.context.block_number)

        pool_price_info = GeneralHistoricalPlan(
            tag='eod',
            target_key=f'TokenPoolPriceInfo.{block_number}',
            name='token.pool-price-info',
            use_kitchen=use_kitchen,
            chef_return_type=PoolPriceInfos,
            plan_return_type=PoolPriceInfos,
            context=self.context,
            verbose=verbose,
            method='run_model',
            slug='token.pool-price-info',
            model_version='1.1',
            input=input,
            block_number=block_number,
            input_keys=[input.address],
        )
        comptroller = pool_price_info.execute()

        return {}
