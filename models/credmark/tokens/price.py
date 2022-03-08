import credmark.model
from credmark.types import Price, Token


@credmark.model.describe(slug='price',
                         version='1.0',
                         display_name='Token Price',
                         description='The Current Credmark Supported Price Algorithm',
                         input=Token,
                         output=Price)
class PriceModel(credmark.model.Model):
    def run(self, input: Token) -> Price:
        return self.context.run_model('uniswap-v3-get-average-price', input, return_type=Price)
