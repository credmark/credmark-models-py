from typing import List
from credmark.cmf.model import Model
from credmark.cmf.model.errors import (
    ModelDataError, ModelRunError, create_instance_from_error_dict)
from credmark.dto import DTOField
from credmark.cmf.types import (Currency, Maybe, NativeToken, Network, Price, PriceWithQuote,
                                Some, Token, MapBlocksOutput)
from credmark.cmf.types.compose import (MapBlockTimeSeriesOutput,
                                        MapInputsOutput)
from models.dtos.price import (PRICE_DATA_ERROR_DESC, Address,
                               PriceHistoricalInput, PriceHistoricalInputs,
                               PriceInput)


@Model.describe(slug='price.quote-historical-multiple',
                version='1.7',
                display_name='Token Price - Quoted - Historical',
                description='Credmark Supported Price Algorithms',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=PriceHistoricalInputs,
                output=MapBlockTimeSeriesOutput[Some[PriceWithQuote]],
                errors=PRICE_DATA_ERROR_DESC)
class PriceQuoteHistoricalMultiple(Model):
    def run(self, input: PriceHistoricalInputs) -> MapBlockTimeSeriesOutput[Some[PriceWithQuote]]:
        price_historical_result = self.context.run_model(
            slug='compose.map-block-time-series',
            input={"modelSlug": 'price.quote-multiple',
                   "modelInput": {'some': input.some},
                   "endTimestamp": self.context.block_number.timestamp,
                   "interval": input.interval,
                   "count": input.count,
                   "exclusive": input.exclusive},
            return_type=MapBlockTimeSeriesOutput[Some[PriceWithQuote]])

        for result in price_historical_result:
            if result.error is not None:
                self.logger.error(result.error)
                raise create_instance_from_error_dict(result.error.dict())

        return price_historical_result


@Model.describe(slug='price.quote-historical',
                version='1.2',
                display_name='Token Price - Quoted - Historical',
                description='Credmark Supported Price Algorithms',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price', 'historical'],
                input=PriceHistoricalInput,
                output=MapBlockTimeSeriesOutput[PriceWithQuote],
                errors=PRICE_DATA_ERROR_DESC)
class PriceQuoteHistorical(Model):
    def run(self, input: PriceHistoricalInput) -> MapBlockTimeSeriesOutput[PriceWithQuote]:
        price_historical_result = self.context.run_model(
            slug='compose.map-block-time-series',
            input={"modelSlug": 'price.quote',
                   "modelInput": PriceInput(base=input.base, quote=input.quote),
                   "endTimestamp": self.context.block_number.timestamp,
                   "interval": input.interval,
                   "count": input.count,
                   "exclusive": input.exclusive},
            return_type=MapBlockTimeSeriesOutput[PriceWithQuote])

        for result in price_historical_result:
            if result.error is not None:
                self.logger.error(result.error)
                raise create_instance_from_error_dict(result.error.dict())

        return price_historical_result


@Model.describe(slug='price.quote-multiple-maybe',
                version='0.1',
                display_name='Token Price - Quoted',
                description='Credmark Supported Price Algorithms',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=Some[PriceInput],
                output=Some[PriceWithQuote],
                errors=PRICE_DATA_ERROR_DESC)
class PriceQuoteMultipleMaybe(Model):
    def run(self, input: Some[PriceInput]) -> Some[Maybe[PriceWithQuote]]:
        price_slug = 'price.quote-maybe'

        def _use_compose():
            token_prices_run = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': price_slug, 'modelInputs': input.some},
                return_type=MapInputsOutput[PriceInput, Maybe[PriceWithQuote]])

            prices = []
            for p in token_prices_run:
                if p.output is not None:
                    prices.append(p.output)
                elif p.error is not None:
                    self.logger.error(p.error)
                    raise create_instance_from_error_dict(p.error.dict())
                else:
                    raise ModelRunError(
                        'compose.map-inputs: output/error cannot be both None')

            return Some[Maybe[PriceWithQuote]](some=prices)

        def _use_for():
            prices = [self.context.run_model(price_slug, input=m, return_type=Maybe[PriceWithQuote])
                      for m in input]
            return Some[Maybe[PriceWithQuote]](some=prices)

        return _use_for()


@Model.describe(slug='price.quote-multiple',
                version='1.10',
                display_name='Token Price - Quoted',
                description='Credmark Supported Price Algorithms',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=Some[PriceInput],
                output=Some[PriceWithQuote],
                errors=PRICE_DATA_ERROR_DESC)
class PriceQuoteMultiple(Model):
    def run(self, input: Some[PriceInput]) -> Some[PriceWithQuote]:
        price_slug = 'price.quote'

        def _use_compose():
            token_prices_run = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': price_slug, 'modelInputs': input.some},
                return_type=MapInputsOutput[PriceInput, PriceWithQuote])

            prices = []
            for p in token_prices_run:
                if p.output is not None:
                    prices.append(p.output)
                elif p.error is not None:
                    self.logger.error(p.error)
                    raise create_instance_from_error_dict(p.error.dict())
                else:
                    raise ModelRunError('compose.map-inputs: output/error cannot be both None')

            return Some[PriceWithQuote](some=prices)

        def _use_for():
            prices = [self.context.run_model(price_slug, input=m, return_type=PriceWithQuote)
                      for m in input]
            return Some[PriceWithQuote](some=prices)

        return _use_for()


class PriceBlocksInput(PriceInput):
    block_numbers: List[int] = DTOField(description='List of blocks to run')


@Model.describe(slug='price.quote-maybe-blocks',
                version='0.1',
                display_name='Token Price - Quoted',
                description='Credmark Supported Price Algorithms',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=PriceBlocksInput,
                output=MapBlocksOutput[Maybe[PriceWithQuote]],
                errors=PRICE_DATA_ERROR_DESC)
class PriceQuoteMaybeBlock(Model):
    def run(self, input: PriceBlocksInput) -> MapBlocksOutput[Maybe[PriceWithQuote]]:
        max_input_block_numbers = max(input.block_numbers)
        if self.context.block_number > max_input_block_numbers:
            return self.context.run_model(self.slug,
                                          input,
                                          return_type=MapBlocksOutput[Maybe[PriceWithQuote]],
                                          block_number=max_input_block_numbers)
        elif self.context.block_number < max_input_block_numbers:
            raise ModelRunError(f'Request block number ({max_input_block_numbers}) is '
                                f'larger than current block number {self.context.block_number}')

        pi = PriceInput(base=input.base, quote=input.quote)
        pp = self.context.run_model('compose.map-blocks',
                                    {"modelSlug": "price.quote-maybe",
                                     "modelInput": pi,
                                     "blockNumbers": input.block_numbers},
                                    return_type=MapBlocksOutput[Maybe[PriceWithQuote]])

        return pp


@Model.describe(slug='price.quote-maybe',
                version='0.4',
                display_name='Token Price - Quoted - Maybe',
                description='Credmark Supported Price Algorithms',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=PriceInput,
                output=Maybe[PriceWithQuote])
class PriceQuoteMaybe(Model):
    """
    Return token's price in Maybe
    """

    def run(self, input: PriceInput) -> Maybe[PriceWithQuote]:
        try:
            price = self.context.run_model('price.quote', input=input, return_type=PriceWithQuote)
            return Maybe[PriceWithQuote](just=price)
        except (ModelRunError, ModelDataError) as _err:
            pass
        return Maybe.none()


@Model.describe(slug='price.quote',
                version='1.11',
                display_name='Token Price - Quoted',
                description='Credmark Supported Price Algorithms',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=PriceInput,
                output=PriceWithQuote,
                errors=PRICE_DATA_ERROR_DESC)
class PriceQuote(Model):
    """
    Return token's price
    """

    CONVERT_TO_WRAP = {
        Network.Mainnet: {
            Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'):
            {'symbol': 'WETH'},
            Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB'):
            {'symbol': 'WBTC'},
        }
    }

    def wrapper(self, token):
        new_token = self.CONVERT_TO_WRAP[self.context.network].get(token.address, None)
        if new_token is not None:
            return Currency(**new_token)
        return token

    def replace_underlying(self, token):
        if isinstance(token, Token) and not isinstance(token, NativeToken):
            addr_maybe = self.context.run_model('token.underlying-maybe',
                                                input=token,
                                                return_type=Maybe[Address],
                                                local=True)
            if addr_maybe.just is not None:
                return Currency(address=addr_maybe.just)
        return token

    def get_price_usd(self, input):
        # We already tried base with quote in USD.
        # When quote is non-USD, we try to obtain base's price quote in USD
        if input.quote != Currency(symbol='USD'):
            price_usd_maybe = self.context.run_model('price.oracle-chainlink-maybe',
                                                     input=input.quote_usd(),
                                                     return_type=Maybe[PriceWithQuote],
                                                     local=True)
            if price_usd_maybe.just is not None:
                return price_usd_maybe.just

        price_usd_maybe = self.context.run_model('price.dex-curve-fi-maybe',
                                                 input=input.base,
                                                 return_type=Maybe[Price],
                                                 local=True)
        if price_usd_maybe.just is not None:
            return PriceWithQuote.usd(**price_usd_maybe.just.dict())

        price_usd = self.context.run_model('price.dex-blended',
                                           input=self.wrapper(input.base),
                                           return_type=PriceWithQuote)

        return price_usd

    def run(self, input: PriceInput) -> PriceWithQuote:
        input.base = self.replace_underlying(input.base)
        input.quote = self.replace_underlying(input.quote)

        # 1. Try chainlink (include check for same base and quote)
        if input.base.address >= input.quote.address:
            price_maybe = self.context.run_model('price.oracle-chainlink-maybe',
                                                 input=input,
                                                 return_type=Maybe[PriceWithQuote],
                                                 local=True)
            if price_maybe.just is not None:
                return price_maybe.just
        else:
            price_maybe = self.context.run_model('price.oracle-chainlink-maybe',
                                                 input=input.inverse(),
                                                 return_type=Maybe[PriceWithQuote],
                                                 local=True)
            if price_maybe.just is not None:
                return price_maybe.just.inverse(input.quote.address)

        # 2. Try price with single-side of USD
        # 2.1 For the case of one of input is USD
        if input.base == Currency(symbol='USD'):
            price_usd = self.get_price_usd(input.inverse()).inverse(input.quote.address)
        else:
            price_usd = self.get_price_usd(input)

        if Currency(symbol='USD') in [input.base, input.quote]:
            return price_usd

        # 2.2 For the case of neither input is USD
        quote_usd = self.context.run_model(
            self.slug,
            {'base': input.quote},
            return_type=PriceWithQuote)
        return price_usd.cross(quote_usd.inverse(input.quote.address))
