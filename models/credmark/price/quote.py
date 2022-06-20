from credmark.cmf.model import Model, ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import FiatCurrency, Price, Token
from credmark.cmf.types.compose import (MapBlockTimeSeriesOutput,
                                        MapInputsOutput)
from models.dtos.price import (Address,
                               PriceHistoricalInput,
                               PriceHistoricalInputs,
                               PriceHistoricalOutputs,
                               PriceInput, PriceInputs,
                               PriceMaybe, Prices)

PRICE_DATA_ERROR_DESC = ModelDataErrorDesc(
    code=ModelDataError.Codes.NO_DATA,
    code_desc='No pools to aggregate for token price')


@Model.describe(slug='price.quote-historical-multiple',
                version='1.0',
                display_name='Token Price - Quoted - Historical',
                description='Credmark Supported Price Algorithms',
                developer='Credmark',
                input=PriceHistoricalInputs,
                output=PriceHistoricalOutputs,
                errors=PRICE_DATA_ERROR_DESC)
class PriceQuoteHistoricalMultiple(Model):
    def run(self, input: PriceHistoricalInputs) -> PriceHistoricalOutputs:
        partial_input = {'interval': input.interval,
                         'count': input.count,
                         'exclusive': input.exclusive}
        price_historical_result = self.context.run_model(
            slug='compose.map-inputs',
            input={'modelSlug': 'price.quote-historical',
                   'modelInputs': [one_input.dict() | partial_input for one_input in input.inputs]},
            return_type=MapInputsOutput[PriceHistoricalInput,
                                        MapBlockTimeSeriesOutput[Price]])  # type: ignore

        series = []
        for result in price_historical_result:
            if result.error is not None:
                self.logger.error(result.error)
                raise ModelDataError(result.error.message)
            if result.output is None:
                raise ModelRunError(f'None result with {result.input}')
            series.append(result.output)

        return PriceHistoricalOutputs(series=series)


@Model.describe(slug='price.quote-historical',
                version='1.0',
                display_name='Token Price - Quoted - Historical',
                description='Credmark Supported Price Algorithms',
                developer='Credmark',
                input=PriceHistoricalInput,
                output=MapBlockTimeSeriesOutput[Price],
                errors=PRICE_DATA_ERROR_DESC)
class PriceQuoteHistorical(Model):
    def run(self, input: PriceHistoricalInput) -> MapBlockTimeSeriesOutput[Price]:
        price_historical_result = self.context.run_model(
            slug='compose.map-block-time-series',
            input={"modelSlug": 'price.quote',
                   "modelInput": PriceInput(base=input.base, quote=input.quote),
                   "endTimestamp": self.context.block_number.timestamp,
                   "interval": input.interval,
                   "count": input.count,
                   "exclusive": input.exclusive},
            return_type=MapBlockTimeSeriesOutput[Price])

        for result in price_historical_result:
            if result.error is not None:
                self.logger.error(result.error)
                raise ModelDataError(result.error.message)

        return price_historical_result


@Model.describe(slug='price.quote-multiple',
                version='1.3',
                display_name='Token Price - Quoted',
                description='Credmark Supported Price Algorithms',
                developer='Credmark',
                input=PriceInputs,
                output=Prices,
                errors=PRICE_DATA_ERROR_DESC)
class PriceQuoteMultiple(Model):
    def run(self, input: PriceInputs) -> Prices:
        token_prices_run = self.context.run_model(
            slug='compose.map-inputs',
            input={'modelSlug': 'price.quote', 'modelInputs': input.inputs},
            return_type=MapInputsOutput[PriceInput, Price])

        print(token_prices_run)
        prices = []
        for p in token_prices_run:
            if p.error is not None:
                self.logger.error(p.error)
                raise ModelRunError(p.error.message)
            if p.output is None:
                raise ModelRunError(f'Unable to get price for {p.input}')
            prices.append(p.output)

        return Prices(prices=prices)


@ Model.describe(slug='price',
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


@ Model.describe(slug='price.quote',
                 version='1.3',
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
        price_maybe = self.context.run_model('price.oracle-chainlink-maybe',
                                             input=input,
                                             return_type=PriceMaybe)
        if price_maybe.price is not None:
            return price_maybe.price

        if isinstance(input.base, FiatCurrency) and isinstance(input.quote, FiatCurrency):
            raise ModelDataError(f'No feed available for '
                                 f'{input.base.symbol}/{input.quote.symbol}')

        if isinstance(input.base, FiatCurrency):
            price_other = self.context.run_model(self.slug,
                                                 input=input.inverse(),
                                                 return_type=Price)
            return price_other.inverse()

        price_maybe = self.context.run_model('price.oracle-chainlink-maybe',
                                             input=input.quote_usd(),
                                             return_type=PriceMaybe)

        if price_maybe.price is not None:
            return price_maybe.price

        price_usd_maybe = self.context.run_model('price.dex-curve-fi-maybe',
                                                 input=input.base,
                                                 return_type=PriceMaybe)
        if price_usd_maybe.price is not None:
            price_usd = price_usd_maybe.price
        else:
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
