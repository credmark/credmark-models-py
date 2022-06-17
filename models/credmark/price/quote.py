from credmark.cmf.types import (
    Token,
    Price,
    FiatCurrency,
)

from credmark.cmf.model import Model, ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from models.dtos.price import PriceInput, Address

PRICE_DATA_ERROR_DESC = ModelDataErrorDesc(
    code=ModelDataError.Codes.NO_DATA,
    code_desc='No pools to aggregate for token price')


@Model.describe(slug='price',
                version='1.0',
                display_name='Token Price',
                description='DEPRECATED - use price.quote',
                input=Token,
                output=Price)
class PriceModel(Model):
    """
    Return token's price (DEPRECATED) - use price.quote
    """

    def run(self, input: Token) -> Price:
        return self.context.run_model('price.quote', input, return_type=Price)


@Model.describe(slug='price.quote',
                version='1.2',
                display_name='Token Price - Quoted',
                description='Credmark Supported Price Algorithms',
                developer='Credmark',
                input=PriceInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class PriceQuote(Model):
    """
    Return token's price
    """
    CONVERT_FOR_TOKEN_PRICE = {
        1: {
            Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'):
            Address('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'),
            Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB'):
            Address('0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'),
        }
    }

    def run(self, input: PriceInput) -> Price:
        try:
            return self.context.run_model('price.oracle-chainlink',
                                          input=input,
                                          return_type=Price)
        except ModelRunError:
            if isinstance(input.base, FiatCurrency) and isinstance(input.quote, FiatCurrency):
                raise ModelDataError(f'No feed available for '
                                     f'{input.base.symbol}/{input.quote.symbol}')

            if isinstance(input.base, FiatCurrency):
                price_other = self.context.run_model(self.slug,
                                                     input=input.inverse(),
                                                     return_type=Price)
                return price_other.inverse()

            try:
                price_usd = self.context.run_model(
                    'price.oracle-chainlink',
                    input={'base': input.base, 'quote': FiatCurrency(symbol='USD')},
                    return_type=Price)
            except ModelRunError:
                try:
                    price_usd = self.context.run_model('price.dex-curve-fi',
                                                       input=input.base,
                                                       return_type=Price)
                except ModelRunError:
                    price_usd = self.context.run_model('price.dex-blended',
                                                       input=input.base,
                                                       return_type=Price)

            if input.quote == FiatCurrency(symbol='USD'):
                return price_usd
            else:
                quote_usd = self.context.run_model(
                    self.slug,
                    {'base': input.quote},
                    return_type=Price)
                return price_usd.cross(quote_usd.inverse())
