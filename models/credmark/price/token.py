

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


@ Model.describe(slug='price.token',
                 version='1.2',
                 display_name='Token price - Credmark',
                 description='The Current Credmark Supported Price Algorithms',
                 developer='Credmark',
                 input=Token,
                 output=Price,
                 errors=PRICE_DATA_ERROR_DESC)
class TokenPriceModel(Model, PriceWeight):
    """
    Return token's price
    """

    def run(self, input: Token) -> Price:
