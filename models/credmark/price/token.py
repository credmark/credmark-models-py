from credmark.cmf.types import (
    Token,
    Price
)

from credmark.cmf.model import Model, ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from models.dtos.price import TokenPriceInput, ChainlinkAddress

PRICE_DATA_ERROR_DESC = ModelDataErrorDesc(
    code=ModelDataError.Codes.NO_DATA,
    code_desc='No pools to aggregate for token price')


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


@Model.describe(slug='token.price',
                version='1.2',
                display_name='Token price - Credmark',
                description='The Current Credmark Supported Price Algorithms',
                developer='Credmark',
                input=TokenPriceInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class TokenPriceModel(Model):
    """
    Return token's price
    """

    def cross_price(self, price0: Price, price1: Price) -> Price:
        return Price(price=price0.price * price1.price, src=f'{price0.src},{price1.src}')

    def inverse_price(self, price: Price) -> Price:
        price.price = 1 / price.price
        price.src = f'{price.src}|Inverse'
        return price

    def run(self, input: TokenPriceInput) -> Price:
        base = input.address
        quote = input.quote_address

        breakpoint()

        try:
            return self.context.run_model('price.oracle-chainlink',
                                          input={'base': base, 'quote': quote},
                                          return_type=Price)
        except ModelRunError:
            try:
                price_usd = self.context.run_model('price.oracle-chainlink',
                                                   input={'base': base, 'quote': 'USD'},
                                                   return_type=Price)
            except ModelRunError:
                try:
                    price_usd = self.context.run_model('price.dex-curve-fi',
                                                       input=input,
                                                       return_type=Price)
                except ModelRunError:
                    price_usd = self.context.run_model('price.dex-blended',
                                                       input=input,
                                                       return_type=Price)

            if quote == ChainlinkAddress('USD'):
                return price_usd
            else:
                quote_usd = self.context.run_model(
                    self.slug,
                    {'address': quote, 'quote_address': 'USD'},
                    return_type=Price)
                return self.cross_price(price_usd, self.inverse_price(quote_usd))
