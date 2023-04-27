# pylint:disable=try-except-raise, no-member
from typing import List

from credmark.cmf.model import Model
from credmark.cmf.model.errors import (
    ModelDataError,
    ModelRunError,
    create_instance_from_error_dict,
)
from credmark.cmf.types import (
    Address,
    Currency,
    MapBlocksOutput,
    Maybe,
    NativeToken,
    Network,
    Price,
    PriceWithQuote,
    Some,
    Token,
)
from credmark.cmf.types.compose import MapBlockTimeSeriesOutput, MapInputsOutput
from credmark.dto import DTOField

from models.dtos.price import (
    PRICE_DATA_ERROR_DESC,
    PriceHistoricalInput,
    PriceHistoricalInputs,
    PriceInput,
    PriceInputWithPreference,
    PriceMultipleInput,
)


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
                   "modelInput": PriceInputWithPreference(base=input.base,
                                                          quote=input.quote,
                                                          prefer=input.prefer),
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
                version='0.2',
                display_name='Token Price - Quoted',
                description='Credmark Supported Price Algorithms',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=Some[PriceInputWithPreference],
                output=Some[Maybe[PriceWithQuote]],
                errors=PRICE_DATA_ERROR_DESC)
class PriceQuoteMultipleMaybe(Model):
    def run(self, input: Some[PriceInputWithPreference]) -> Some[Maybe[PriceWithQuote]]:
        price_slug = 'price.quote-maybe'

        def _use_compose():
            token_prices_run = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': price_slug, 'modelInputs': input.some},
                return_type=MapInputsOutput[PriceInputWithPreference, Maybe[PriceWithQuote]])

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

        return _use_compose()


@Model.describe(slug='price.multiple-maybe',
                version='0.1',
                display_name='Token Price - Quoted',
                description='Credmark Supported Price Algorithms',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=PriceMultipleInput,
                output=Some[Maybe[PriceWithQuote]],
                errors=PRICE_DATA_ERROR_DESC)
class PriceMultipleMaybeWithSlug(Model):
    def run(self, input: PriceMultipleInput) -> Some[Maybe[PriceWithQuote]]:
        price_slug = input.slug

        def _use_compose():
            token_prices_run = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': price_slug, 'modelInputs': input.some},
                return_type=MapInputsOutput[PriceInputWithPreference, Maybe[PriceWithQuote]])

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
            prices = [
                self.context.run_model(
                    price_slug,
                    input=m,
                    return_type=Maybe[PriceWithQuote])
                for m in input.some]
            return Some[Maybe[PriceWithQuote]](some=prices)

        return _use_compose()


@Model.describe(slug='price.quote-multiple',
                version='1.10',
                display_name='Token Price - Quoted',
                description='Credmark Supported Price Algorithms',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=Some[PriceInputWithPreference],
                output=Some[PriceWithQuote],
                errors=PRICE_DATA_ERROR_DESC)
class PriceQuoteMultiple(Model):
    def run(self, input: Some[PriceInputWithPreference]) -> Some[PriceWithQuote]:
        price_slug = 'price.quote'

        def _use_compose():
            token_prices_run = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': price_slug, 'modelInputs': input.some},
                return_type=MapInputsOutput[PriceInputWithPreference, PriceWithQuote])

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

            return Some[PriceWithQuote](some=prices)

        def _use_for():
            prices = [self.context.run_model(price_slug, input=m, return_type=PriceWithQuote)
                      for m in input]
            return Some[PriceWithQuote](some=prices)

        return _use_for()


class PriceBlocksInput(PriceInputWithPreference):
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

        pi = PriceInputWithPreference(
            base=input.base, quote=input.quote, prefer=input.prefer)
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
                input=PriceInputWithPreference,
                output=Maybe[PriceWithQuote])
class PriceQuoteMaybe(Model):
    """
    Return token's price in Maybe
    """

    def run(self, input: PriceInputWithPreference) -> Maybe[PriceWithQuote]:
        try:
            price = self.context.run_model(
                'price.quote', input=input, return_type=PriceWithQuote)
            return Maybe[PriceWithQuote](just=price)
        except (ModelRunError, ModelDataError):
            pass
        return Maybe.none()


@Model.describe(slug='price.quote',
                version='1.11',
                display_name=('Credmark Token Price with preference of cex or dex (default), '
                              'fiat conversion for non-USD from Chainlink'),
                description='Credmark Token Price from cex or dex',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=PriceInputWithPreference,
                output=PriceWithQuote,
                errors=PRICE_DATA_ERROR_DESC)
class PriceQuote(Model):
    def run(self, input: PriceInputWithPreference) -> PriceWithQuote:
        pi = {"base": input.base.address, "quote": input.quote.address}
        if input.prefer == 'cex':
            model1, label1 = 'price.cex-maybe', 'cex'
            model2, label2 = 'price.dex-maybe', 'dex'
        else:
            model1, label1 = 'price.dex-maybe', 'dex'
            model2, label2 = 'price.cex-maybe', 'cex'

        try:
            price_maybe1 = self.context.run_model(
                model1, pi, return_type=Maybe[PriceWithQuote])
            if price_maybe1.just is not None:
                price = price_maybe1.just
                price.src = label1 + '|' + \
                    (price.src if price.src is not None else '')
                return price
            else:
                price_maybe2 = self.context.run_model(
                    model2, pi, return_type=Maybe[PriceWithQuote])
                if price_maybe2.just is not None:
                    price = price_maybe2.just
                    price.src = label2 + '|' + \
                        (price.src if price.src is not None else '')
                    return price
                else:
                    raise ModelRunError(
                        f'[{self.context.block_number}] No price can be found for {input}')
        except ModelRunError:
            raise
            # cex_cross = PriceCexCross(self.context)
            # price = cex_cross.run(input)
            # price.src = 'dex|' + (price.src if price.src is not None else '')
            # return price


class PriceCommon:
    WRAP_TOKEN = {
        Network.Mainnet: {
            Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'):
            {'symbol': 'WETH'},
            Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB'):
            {'symbol': 'WBTC'},
        }
    }

    UNWRAP_TOKEN = {
        Network.Mainnet: {
            'WETH': Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'),
            'WBTC': Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB')
        }
    }

    EXCEPTION_TOKEN = {
        Network.Mainnet: {
            # Wormhole SOL (problematic ABI/proxy)
            Address('0xD31a59c85aE9D8edEFeC411D448f90841571b89c'),
            # Wormhole BNB (problematic ABI/proxy)
            Address('0x418d75f65a02b3d53b2418fb8e1fe493759c7605'),
        }
    }

    @staticmethod
    def is_native(context, token):
        return token.address in __class__.WRAP_TOKEN.get(context.network, {})

    @staticmethod
    def wrap_token(context, token):
        new_token = __class__.WRAP_TOKEN.get(
            context.network, {}).get(token.address, None)
        if new_token is not None:
            return Currency(**new_token)
        return token

    @staticmethod
    def unwrap_token(context, token):
        if __class__.is_native(context, token):
            return token

        if token.address in __class__.EXCEPTION_TOKEN.get(context.network, {}):
            return token

        new_token = __class__.UNWRAP_TOKEN.get(
            context.network, {}).get(token.symbol, None)
        if new_token is not None:
            if Token(token.symbol).address == token.address:
                return Currency(new_token)
        return token

    @staticmethod
    def replace_underlying(context, token):
        if isinstance(token, Token) and not isinstance(token, NativeToken):
            addr_maybe = context.run_model('token.underlying-maybe',
                                           input=token,
                                           return_type=Maybe[Address],
                                           local=True)
            if addr_maybe.just is not None:
                return Currency(address=addr_maybe.just)
        return token

    @staticmethod
    def get_price_usd_for_base(context, input, no_dex):
        # We already tried base with quote in USD.
        # When quote is non-USD, we try to obtain base's price quote in USD
        if input.quote != Currency(symbol='USD'):
            input_quote_usd = input.quote_usd()
            input_quote_usd.base = __class__.unwrap_token(
                context, input_quote_usd.base)
            price_usd_maybe = context.run_model('price.oracle-chainlink-maybe',
                                                input=input_quote_usd,
                                                return_type=Maybe[PriceWithQuote],
                                                local=True)
            if price_usd_maybe.just is not None:
                return price_usd_maybe.just

        if no_dex:
            raise ModelRunError(
                f'No chainlink source for this token {input.base.address}')

        return __class__.get_price_usd_from_dex(context, input.base)

    @staticmethod
    def get_price_usd_from_dex(context, input_base):
        try:
            price_usd = context.run_model('price.dex-db-prefer',
                                          input=__class__.wrap_token(
                                              context, input_base),
                                          return_type=PriceWithQuote,
                                          local=True)
            return price_usd

        except (ModelRunError, ModelDataError):
            price_usd_maybe = context.run_model('price.dex-curve-fi-maybe',
                                                input=input_base,
                                                return_type=Maybe[Price],
                                                local=True)

            if price_usd_maybe.just is not None:
                return PriceWithQuote.usd(**price_usd_maybe.just.dict())
            else:
                raise


class NoDEX:
    no_dex = True


class AllowDEX:
    no_dex = False


class PriceCexModel(Model, PriceCommon):
    def run(self, input: PriceInput) -> PriceWithQuote:
        input.base = __class__.replace_underlying(self.context, input.base)
        input.quote = __class__.replace_underlying(self.context, input.quote)

        # 1. Try chainlink (include check for same base and quote)
        input_unwrap = input.copy()
        input_unwrap.base = __class__.unwrap_token(self.context, input.base)
        input_unwrap.quote = __class__.unwrap_token(self.context, input.quote)

        if input.base.address >= input.quote.address:
            price_maybe = self.context.run_model('price.oracle-chainlink-maybe',
                                                 input=input_unwrap,
                                                 return_type=Maybe[PriceWithQuote],
                                                 local=True)
            if price_maybe.just is not None:
                return price_maybe.just
        else:
            price_maybe = self.context.run_model('price.oracle-chainlink-maybe',
                                                 input=input_unwrap.inverse(),
                                                 return_type=Maybe[PriceWithQuote],
                                                 local=True)
            if price_maybe.just is not None:
                return price_maybe.just.inverse(input.quote.address)

        # 2. Try price with single-side of USD
        # 2.1 For the case of one of input is USD
        if input.base == Currency(symbol='USD'):
            price_usd = __class__.get_price_usd_for_base(
                self.context,
                input.inverse(),
                no_dex=True).inverse(input.quote.address)
        else:
            price_usd = __class__.get_price_usd_for_base(
                self.context,
                input,
                no_dex=self.no_dex)  # type: ignore

        if Currency(symbol='USD') in [input.base, input.quote]:
            return price_usd

        # Reaching here, price_usd is price in USD for base
        # Now let's calculate price in USD for quote

        # 2.2 For the case of neither input is USD
        quote_usd = self.context.run_model(
            self.slug,
            {'base': input.quote},
            return_type=PriceWithQuote)
        return price_usd.cross(quote_usd.inverse(input.quote.address))


@Model.describe(slug='price.cex',
                version='0.1',
                display_name='Credmark Token Price and fiat conversion from Chainlink',
                description='Price and fiat conversion for non-USD from Chainlink',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=PriceInput,
                output=PriceWithQuote,
                errors=PRICE_DATA_ERROR_DESC)
class PriceCex(PriceCexModel, NoDEX):
    """
    Return token's price and fiat conversion for non-USD from Chainlink
    """


@Model.describe(slug='price.cex-maybe',
                version='0.1',
                display_name='Credmark Token Price and fiat conversion from Chainlink [Maybe]',
                description='Price and fiat conversion for non-USD from Chainlink [Maybe]',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=PriceInput,
                output=Maybe[PriceWithQuote])
class PriceCexMaybe(Model):
    """
    Return token's price in Maybe
    """

    def run(self, input: PriceInput) -> Maybe[PriceWithQuote]:
        try:
            price = self.context.run_model(
                'price.cex', input=input, return_type=PriceWithQuote)
            return Maybe[PriceWithQuote](just=price)
        except (ModelRunError, ModelDataError):
            return Maybe.none()


class PriceCexCross(PriceCexModel, AllowDEX):
    """
    Return token's price and fiat conversion for non-USD from Chainlink
    """


@Model.describe(slug='price.dex-maybe',
                version='0.2',
                display_name=('Credmark Token Price from Dex with '
                              'Chainlink for fiat conversion [Maybe]'),
                description='Price from Dex with fiat conversion for non-USD [Maybe]',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=PriceInput,
                output=Maybe[PriceWithQuote])
class PriceDexMaybe(Model):
    """
    Return token's price in Maybe
    """

    def run(self, input: PriceInput) -> Maybe[PriceWithQuote]:
        try:
            price = self.context.run_model(
                'price.dex', input=input, return_type=PriceWithQuote)
            return Maybe[PriceWithQuote](just=price)
        except (ModelRunError, ModelDataError):
            return Maybe.none()


@Model.describe(slug='price.dex',
                version='0.2',
                display_name=('Credmark Token Price from Dex with '
                              'Chainlink for fiat conversion'),
                description='Price from Dex with fiat conversion for non-USD',
                developer='Credmark',
                category='protocol',
                tags=['token', 'price'],
                input=PriceInput,
                output=PriceWithQuote,
                errors=PRICE_DATA_ERROR_DESC)
class PriceDex(Model, PriceCommon):
    """
    Return token's price from Dex with Chainlink for fiat conversion
    """

    def run(self, input: PriceInput) -> PriceWithQuote:
        usd_currency = Currency(symbol="USD")
        usd_address = usd_currency.address

        input.base = __class__.replace_underlying(self.context, input.base)
        input.quote = __class__.replace_underlying(self.context, input.quote)

        # 1. Use chainlink when both are fiat
        if input.base.fiat and input.quote.fiat:
            return self.context.run_model('price.cex',
                                          input=input,
                                          return_type=PriceWithQuote,
                                          )

        # 2. Use chainlink when either half is fiat
        if input.quote.fiat:
            price_usd = __class__.get_price_usd_from_dex(
                self.context, input.base)

            if input.quote == usd_currency:
                return price_usd
            else:
                price_quote = self.context.run_model('price.cex',
                                                     input={
                                                         'base': input.quote},
                                                     return_type=PriceWithQuote)
                return price_usd.cross(price_quote)

        if input.base.fiat:
            price_usd = __class__.get_price_usd_from_dex(
                self.context, input.quote)

            if input.base == usd_currency:
                return price_usd.inverse(input.quote.address)
            else:
                price_quote = self.context.run_model('price.cex',
                                                     input={
                                                         'base': input.base},
                                                     return_type=PriceWithQuote)
                return price_usd.inverse(usd_address).cross(price_quote)

        # 3. Use only dex
        price_usd_base = __class__.get_price_usd_from_dex(
            self.context, input.base)
        price_usd_quote = __class__.get_price_usd_from_dex(
            self.context, input.quote)

        return PriceWithQuote(price=price_usd_base.price / price_usd_quote.price,
                              quoteAddress=input.quote.address,
                              src=f'{price_usd_base.src}/{price_usd_quote.src}')
