from datetime import datetime

from credmark.cmf.model import Model
from credmark.cmf.types import (
    Token,
)


@Model.describe(slug="contrib.price-history",
                version="1.0",
                display_name="Price History",
                description="Price History",
                input=Token,
                output=dict)
class PriceHistory(Model):

    def run(self, input: Token) -> dict:
        res = self.context.historical.run_model_historical(
            'token.price-ext',
            window='10 days',
            interval='1 days',
            model_input=input)

        price_series = []
        for n in range(len(res.series) - 1):
            block_time = (datetime.fromtimestamp(res.series[n].blockTimestamp)
                          .strftime('%Y-%m-%d %H:%M:%S'))
            price_series.append((block_time, res.series[n].output))

        return {'price_series': price_series}
