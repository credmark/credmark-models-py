import pandas as pd
from datetime import datetime, tzinfo, timezone

from credmark.cmf.model import Model
from credmark.cmf.types import (
    Token,
)
from credmark.cmf.types.block_number import BlockNumber


"""
credmark-dev run contrib.price-history -i '{"address":"0x090185f2135308BaD17527004364eBcC2D37e5F6"}' -j -l uniswap-v3.get-pool-price-info,uniswap-v3.get-pool-info

credmark-dev run contrib.price-history -i '{"address":"0x090185f2135308BaD17527004364eBcC2D37e5F6"}' -j -l token.pool-price-info,uniswap-v3.get-pool-price-info,uniswap-v3.get-pool-info | tee tmp/spell.json
"""


@Model.describe(slug="contrib.price-history",
                version="1.0",
                display_name="Price History",
                description="Price History",
                input=Token,
                output=dict)
class PriceHistory(Model):
    def run(self, input: Token) -> dict:
        block_time = datetime(2022, 1, 28, 23, 59, 59, tzinfo=timezone.utc)
        bb = BlockNumber.from_timestamp(block_time)
        res = self.context.run_model(
            'token.pool-price-info',
            input=input,
            block_number=bb)

        df = pd.DataFrame(res['pool_price_infos'])

        res = self.context.historical.run_model_historical(
            'token.price',
            window='120 days',
            interval='1 days',
            model_input=input)

        price_series = []
        for n in range(len(res.series) - 1):
            block_time = (datetime.fromtimestamp(res.series[n].blockTimestamp)
                          .strftime('%Y-%m-%d %H:%M:%S'))
            price_series.append((block_time, res.series[n].output, res.series[n].blockNumber))

        return {'price_series': price_series}
