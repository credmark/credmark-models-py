from credmark.cmf.model import Model, ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError, ModelInputError, ModelRunError
from credmark.cmf.types import Address, Currency, Maybe, Network, Price, PriceWithQuote

from models.credmark.price.data.chainlink_feeds import CHAINLINK_OVERRIDE_FEED
from models.dtos.price import PriceInput

PRICE_DATA_ERROR_DESC = ModelDataErrorDesc(
    code=ModelDataError.Codes.NO_DATA,
    code_desc='No possible feed/routing for token pair')


@Model.describe(slug='price.oracle-chainlink-maybe',
                version='1.3',
                display_name='Token Price - from Oracle',
                description='Get token\'s price from Oracle - return None if not found',
                category='protocol',
                subcategory='chainlink',
                tags=['price'],
                input=PriceInput,
                output=Maybe[PriceWithQuote])
class PriceOracleChainlinkMaybe(Model):
    def run(self, input: PriceInput) -> Maybe[PriceWithQuote]:
        try:
            price = self.context.run_model('price.oracle-chainlink',
                                           input=input,
                                           return_type=PriceWithQuote,
                                           local=True)
            return Maybe[PriceWithQuote](just=price)
        except ModelRunError:
            return Maybe.none()


@Model.describe(slug='price.oracle-chainlink',
                version='1.13',
                display_name='Token Price - from Oracle',
                description='Get token\'s price from Oracle',
                category='protocol',
                subcategory='chainlink',
                tags=['price'],
                input=PriceInput,
                output=PriceWithQuote,
                errors=PRICE_DATA_ERROR_DESC)
class PriceOracleChainlink(Model):
    ROUTING_ADDRESSES = {
        Network.Mainnet: [
            Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'),  # ETH
            Address('0x0000000000000000000000000000000000000348'),  # USD
            Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB'),  # BTC
        ],
    }

    WRAP_TOKEN = {
        Network.Mainnet: {
            # WETH => ETH
            Address('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'):
            {'symbol': 'ETH'},
            # WBTC => BTC
            Address('0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'):
            {'symbol': 'BTC'},
        },
        Network.BSC: {
            # WBNB => BNB
            Address('0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'):
            {'address': '0x0000000000000000010000100100111001000010'},
        },
        Network.Polygon: {
            # WMATIC => MATIC
            Address('0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270'):
            {'address': '0x0000000000000000000000000000000000001010'},
            # WBTC => BTC
            Address('0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6'):
            {'address': '0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'},
            # WETH => ETH
            Address('0x7ceb23fd6bc0add59e62ac25578270cff1b9f619'):
            {'address': '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'},
        },
    }

    """
    Return the value of base token in amount of quote tokens
    """

    def check_wrap(self, token):
        if token.address in self.WRAP_TOKEN.get(self.context.network, []):
            return Currency(**self.WRAP_TOKEN[self.context.network][token.address])
        return token

    def replace_input(self, input):
        new_input = PriceInput(base=input.base, quote=input.quote)
        new_input.base = self.check_wrap(new_input.base)
        new_input.quote = self.check_wrap(new_input.quote)
        return new_input

    # pylint: disable=too-many-return-statements, too-many-branches
    def run(self, input: PriceInput) -> PriceWithQuote:
        new_input = self.replace_input(input)
        base = new_input.base
        quote = new_input.quote

        if base.address is None or quote.address is None:
            raise ModelInputError(f'{input} does not carry valid address')

        if base == quote:
            return PriceWithQuote(price=1, src=f'{self.slug}|Equal', quoteAddress=quote.address)

        if self.context.network == Network.Mainnet:
            price_maybe = self.context.run_model('chainlink.price-from-registry-maybe',
                                                 input=new_input,
                                                 return_type=Maybe[PriceWithQuote],
                                                 local=True)
            if price_maybe.just is not None:
                return price_maybe.just

        try_override_base = CHAINLINK_OVERRIDE_FEED[self.context.network].get(
            base.address, None)
        if try_override_base is not None:
            if 'ens' in try_override_base:
                override_ens = try_override_base['ens']
                override_quote = Currency(**try_override_base['quote'])

                p0 = self.context.run_model('chainlink.price-by-ens',
                                            input=override_ens,
                                            return_type=Price,
                                            local=True)
            elif 'feed' in try_override_base:
                override_feed = try_override_base['feed']
                override_quote = Currency(**try_override_base['quote'])

                p0 = self.context.run_model('chainlink.price-by-feed',
                                            input=override_feed,
                                            return_type=Price,
                                            local=True)
            else:
                raise ModelRunError(f'Unknown override {try_override_base}')

            pq0 = PriceWithQuote(**p0.dict(), quoteAddress=quote.address)

            if override_quote.address == quote.address:
                return pq0
            else:
                pq1 = self.context.run_model(self.slug,
                                             input={
                                                 'base': override_quote, 'quote': quote},
                                             return_type=PriceWithQuote)
                return pq0.cross(pq1)

        try_override_quote = CHAINLINK_OVERRIDE_FEED[self.context.network].get(
            quote.address, None)
        if try_override_quote is not None:
            if 'ens' in try_override_quote:
                override_ens = try_override_quote['ens']
                override_quote = Currency(**try_override_quote['quote'])

                p0 = self.context.run_model('chainlink.price-by-ens',
                                            input=override_ens,
                                            return_type=Price,
                                            local=True)
            elif 'feed' in try_override_quote:
                override_feed = try_override_quote['feed']
                override_quote = Currency(**try_override_quote['quote'])

                p0 = self.context.run_model('chainlink.price-by-feed',
                                            input=override_feed,
                                            return_type=Price,
                                            local=True)
            else:
                raise ModelRunError(f'Unknown override {try_override_quote}')

            pq0 = PriceWithQuote(
                **p0.dict(), quoteAddress=quote.address).inverse(quote.address)
            if override_quote.address == base.address:
                return pq0
            else:
                pq1 = self.context.run_model(self.slug,
                                             input={
                                                 'base': override_quote, 'quote': base},
                                             return_type=PriceWithQuote)
                pq1 = pq1.inverse(override_quote.address)
            return pq0.cross(pq1)

        p1 = None
        r1 = None
        for rt_addr in self.ROUTING_ADDRESSES.get(self.context.network, []):
            if rt_addr not in (quote.address, base.address):
                price_input = PriceInput(
                    base=base, quote=Currency(address=rt_addr))

                pq1_maybe = self.context.run_model('chainlink.price-from-registry-maybe',
                                                   input=price_input,
                                                   return_type=Maybe[PriceWithQuote],
                                                   local=True)
                if pq1_maybe.just is not None:
                    p1 = pq1_maybe.just
                    r1 = rt_addr
                    break

        if p1 is not None:
            p2 = None
            r2 = None
            for rt_addr in self.ROUTING_ADDRESSES.get(self.context.network, []):
                if rt_addr not in (quote.address, base.address):
                    price_input = PriceInput(
                        base=Currency(address=rt_addr), quote=quote)

                    pq2_maybe = self.context.run_model('chainlink.price-from-registry-maybe',
                                                       input=price_input,
                                                       return_type=Maybe[PriceWithQuote],
                                                       local=True)
                    if pq2_maybe.just is not None:
                        p2 = pq2_maybe.just
                        r2 = rt_addr
                        break

            if p2 is not None:
                if r1 == r2:
                    return p1.cross(p2)
                else:
                    bridge_price = self.context.run_model(
                        self.slug,
                        input={'base': {"address": r1},
                               'quote': {"address": r2}},
                        return_type=PriceWithQuote)
                    return p1.cross(bridge_price).cross(p2)

        if new_input == input:
            raise ModelRunError(f'No possible feed/routing for token pair '
                                f'{input.base}/{input.quote}')

        raise ModelRunError(f'No possible feed/routing for token pair '
                            f'{input.base}/{input.quote}, '
                            f'replaced by {new_input.base}/{new_input.quote}')
