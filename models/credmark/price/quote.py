from credmark.cmf.model import Model, ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import Currency, FiatCurrency, Price, Token, NativeToken
from credmark.cmf.types.compose import (MapBlockTimeSeriesOutput,
                                        MapInputsOutput)
from models.dtos.price import (Address, AddressMaybe,
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

        prices = []
        for p in token_prices_run:
            if p.error is not None:
                self.logger.error(p.error)
                raise ModelRunError(p.error.message)
            if p.output is None:
                raise ModelRunError(f'Unable to get price for {p.input}')
            prices.append(p.output)

        return Prices(prices=prices)


@Model.describe(slug='price',
                version='1.0',
                display_name='Token Price in USD',
                description='DEPRECATED - use price.quote',
                input=Token,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class PriceModelDeprecated(Model):
    """
    Return token's price (DEPRECATED) - use price.quote
    """

    def run(self, input: Token) -> Price:
        return self.context.run_model('price.quote', {'base': input}, return_type=Price)


@Model.describe(slug='token.price',
                version='1.0',
                display_name='Token Price in USD',
                description='DEPRECATED - use price.quote',
                input=Token,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class TokenPriceModelDeprecated(Model):
    """
    Return token's price (DEPRECATED) - use price.quote
    """

    def run(self, input: Token) -> Price:
        return self.context.run_model('price.quote', {'base': input}, return_type=Price)


@Model.describe(slug='price.quote',
                version='1.6',
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

    CONVERT_TO_WRAP = {
        1: {
            Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'):
            {'symbol': 'WETH'},
            Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB'):
            {'symbol': 'WBTC'},
        }
    }

    def replace_wrap(self, token):
        new_token = self.CONVERT_TO_WRAP[self.context.chain_id].get(token.address, None)
        if new_token is not None:
            return Currency(**new_token)
        return token

    def replace_underlying(self, token):
        if isinstance(token, Token) and not isinstance(token, NativeToken):
            addr_maybe = self.context.run_model('token.underlying',
                                                input=token,
                                                return_type=AddressMaybe)
            if addr_maybe.address is not None:
                return Currency(address=addr_maybe.address)
        return token

    def run(self, input: PriceInput) -> Price:
        input.base = self.replace_underlying(input.base)
        input.quote = self.replace_underlying(input.quote)

        price_maybe = self.context.run_model('price.oracle-chainlink-maybe',
                                             input=input,
                                             return_type=PriceMaybe)
        if price_maybe.price is not None:
            return price_maybe.price

        price_usd_maybe = self.context.run_model('price.oracle-chainlink-maybe',
                                                 input=input.quote_usd(),
                                                 return_type=PriceMaybe)

        if price_usd_maybe.price is not None:
            price_usd = price_usd_maybe.price
        else:
            price_usd_maybe = self.context.run_model('price.dex-curve-fi-maybe',
                                                     input=input.base,
                                                     return_type=PriceMaybe)
            if price_usd_maybe.price is not None:
                price_usd = price_usd_maybe.price
            else:
                new_base = self.replace_wrap(input.base)
                price_usd = self.context.run_model('price.dex-blended',
                                                   input=new_base,
                                                   return_type=Price)

        if input.quote == FiatCurrency(symbol='USD'):
            return price_usd
        else:
            quote_usd = self.context.run_model(
                self.slug,
                {'base': input.quote},
                return_type=Price)
            return price_usd.cross(quote_usd.inverse())
