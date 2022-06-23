from credmark.cmf.model import Model, ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import Currency, FiatCurrency, Price, Token, NativeToken
from credmark.cmf.types.compose import (MapBlockTimeSeriesOutput,
                                        MapInputsOutput)
from models.dtos.price import (Address,
                               Maybe,
                               PriceHistoricalInput,
                               PriceHistoricalInputs,
                               PriceHistoricalOutputs,
                               PriceInput,
                               PriceInputs,
                               Prices)

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
        model_slug = 'price.quote-historical'
        model_inputs = [one_input.dict() | partial_input for one_input in input.inputs]
        price_historical_result = self.context.run_model(
            slug='compose.map-inputs',
            input={'modelSlug': model_slug,
                   'modelInputs': model_inputs},
            return_type=MapInputsOutput[PriceHistoricalInput,
                                        MapBlockTimeSeriesOutput[Price]])  # type: ignore

        series = []
        for res_n, result in enumerate(price_historical_result):
            if result.output is not None:
                series.append(result.output)
            elif result.error is not None:
                self.logger.error(result.error)
                raise ModelRunError(
                    f'Error for {model_slug}({model_inputs[res_n]}). ' +
                    result.error.message)
            else:
                raise ModelRunError('compose.map-inputs: output/error cannot be both None')

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
            if p.error is None and p.output is not None:
                prices.append(p.output)
            else:
                self.logger.error(p.error)
                if p.error is not None:
                    raise ModelRunError(p.error.message)

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
            addr_maybe = self.context.run_model('token.underlying-maybe',
                                                input=token,
                                                return_type=Maybe[Address])
            if addr_maybe.just is not None:
                return Currency(address=addr_maybe.just)
        return token

    def get_price_usd(self, input):
        if input.quote == Currency(symbol='USD'):
            price_usd_maybe = Maybe[Price](just=None)
        else:
            price_usd_maybe = self.context.run_model('price.oracle-chainlink-maybe',
                                                     input=input.quote_usd(),
                                                     return_type=Maybe[Price])

        if price_usd_maybe.just is not None:
            price_usd = price_usd_maybe.just
        else:
            price_usd_maybe = self.context.run_model('price.dex-curve-fi-maybe',
                                                     input=input.base,
                                                     return_type=Maybe[Price])
            if price_usd_maybe.just is not None:
                price_usd = price_usd_maybe.just
            else:
                price_usd = self.context.run_model(
                    'price.dex-blended',
                    input=self.replace_wrap(input.base),
                    return_type=Price)

        return price_usd

    def run(self, input: PriceInput) -> Price:
        input.base = self.replace_underlying(input.base)
        input.quote = self.replace_underlying(input.quote)

        # Cache for the flip pair by keeping an order
        if input.base.address > input.quote.address:
            price_maybe = self.context.run_model('price.oracle-chainlink-maybe',
                                                 input=input,
                                                 return_type=Maybe[Price])
            if price_maybe.just is not None:
                return price_maybe.just
        else:
            price_maybe = self.context.run_model('price.oracle-chainlink-maybe',
                                                 input=input.inverse(),
                                                 return_type=Maybe[Price])
            if price_maybe.just is not None:
                return price_maybe.just.inverse()

        if input.base == Currency(symbol='USD'):
            price_usd = self.get_price_usd(input.inverse()).inverse()
        else:
            price_usd = self.get_price_usd(input)

        if input.quote == Currency(symbol='USD') or Currency(symbol='USD'):
            return price_usd
        else:
            quote_usd = self.context.run_model(
                self.slug,
                {'base': input.quote},
                return_type=Price)
            return price_usd.cross(quote_usd.inverse())
