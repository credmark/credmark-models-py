from datetime import timedelta

from credmark.cmf.model import Model
from credmark.cmf.types import Address, BlockNumber, Token
from credmark.dto import EmptyInput


@Model.describe(slug='contrib.kunlun-demo',
                version='1.0',
                display_name='My Model',
                description="Description of the model.",
                input=EmptyInput,
                output=dict)
class ContribModel(Model):
    def run(self, _: EmptyInput) -> dict:
        usdc = Token('USDC')
        usdc_addr: Address = usdc.address
        block_datetime = self.context.block_number.timestamp_datetime
        usdc_price = self.context.run_model('price.quote', input={'base': usdc_addr})

        aave = Token('AAVE')
        block_number_1day_earlier = BlockNumber.from_datetime(
            self.context.block_number.timestamp_datetime - timedelta(days=1))

        aave_price = self.context.run_model(
            'price.quote',
            input={'base': aave},
            block_number=block_number_1day_earlier)

        return {
            'USDC': usdc,
            'USDC_price': usdc_price['price'],
            'USDC_price_1day_earlier': aave_price['price'],
            'block_timestamp': block_datetime,
            'block_number_1day_earlier': block_number_1day_earlier,
            'block_number_datetime_1day_earlier': block_number_1day_earlier.timestamp_datetime
        }
