from credmark.cmf.model import Model, ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import Address, Contract, Currency, Price
from models.dtos.price import PriceInput, PriceMaybe

PRICE_DATA_ERROR_DESC = ModelDataErrorDesc(
    code=ModelDataError.Codes.NO_DATA,
    code_desc='No possible feed/routing for token pair')


@Model.describe(slug='price.oracle-chainlink-maybe',
                version='1.0',
                display_name='Token Price - from Oracle',
                description='Get token\'s price from Oracle - return None if not found',
                input=PriceInput,
                output=PriceMaybe)
class PriceOracleChainlinkMaybe(Model):
    def run(self, input: PriceInput) -> PriceMaybe:
        try:
            price = self.context.run_model('price.oracle-chainlink',
                                           input=input,
                                           return_type=Price)
            return PriceMaybe(price=price)
        except ModelRunError:
            return PriceMaybe(price=None)


@Model.describe(slug='price.oracle-chainlink',
                version='1.5',
                display_name='Token Price - from Oracle',
                description='Get token\'s price from Oracle',
                input=PriceInput,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class PriceOracleChainlink(Model):
    # The native token on other chain, give a direct address of feed.
    # TODO: find the token address so to find the feed in Chainlink's registry
    OVERRIDE_FEED = {
        1: {
            # WAVAX: avax-usd.data.eth
            Address('0x85f138bfEE4ef8e540890CFb48F620571d67Eda3'):
            ({'address': '0xFF3EEb22B5E3dE6e705b44749C2559d704923FD7'},
             {'symbol': 'USD'}),
            # WSOL: sol-usd.data.eth
            Address('0xD31a59c85aE9D8edEFeC411D448f90841571b89c'):
            ({'address': '0x4ffc43a60e009b551865a93d232e33fce9f01507'},
             {'symbol': 'USD'}),
            # BNB: bnb-usd.data.eth
            Address('0xB8c77482e45F1F44dE1745F52C74426C631bDD52'):
            ({'address': '0x14e613ac84a31f709eadbdf89c6cc390fdc9540a'},
             {'symbol': 'USD'}),
            # WCELO:
            Address('0xE452E6Ea2dDeB012e20dB73bf5d3863A3Ac8d77a'):
            ({'address': '0x10d35efa5c26c3d994c511576641248405465aef'},
             {'symbol': 'USD'}),
            # BTM
            Address('0xcb97e65f07da24d46bcdd078ebebd7c6e6e3d750'):
            ({'address': '0x9fccf42d21ab278e205e7bb310d8979f8f4b5751'},
             {'symbol': 'USD'}),
            # IOST
            Address('0xfa1a856cfa3409cfa145fa4e20eb270df3eb21ab'):
            ({'address': '0xd0935838935349401c73a06fcde9d63f719e84e5'},
             {'symbol': 'USD'}),
            # WBTC: only with BTC for WBTC/BTC
            # Address('0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'):
            # ({'address':'0xfdFD9C85aD200c506Cf9e21F1FD8dd01932FBB23'},
            #  {'symbol':'BTC'}),
        }
    }

    ROUTING_ADDRESSES = [
        Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'),  # ETH
        Address('0x0000000000000000000000000000000000000348'),  # USD
        Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB'),  # BTC
    ]

    WRAP_TOKEN = {
        1: {
            # WETH => ETH
            Address('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'):
            {'symbol': 'ETH'},
            # BTC => WBTC: there is feed for BTC
            # Address('0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'):
            # Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB'),
        }
    }

    """
    Return the value of base token in amount of quote tokens
    """

    def check_wrap(self, token):
        if token.address in self.WRAP_TOKEN[self.context.chain_id]:
            return Currency(**self.WRAP_TOKEN[self.context.chain_id][token.address])
        return token

    def replace_input(self, input):
        new_input = PriceInput(base=input.base, quote=input.quote)
        new_input.base = self.check_wrap(new_input.base)
        new_input.quote = self.check_wrap(new_input.quote)
        return new_input

    def run(self, input: PriceInput) -> Price:  # pylint: disable=too-many-return-statements)
        new_input = self.replace_input(input)
        base = new_input.base
        quote = new_input.quote

        if base.address is None or quote.address is None:
            raise ModelDataError(f'{input} does not carry valid address')

        if base == quote:
            return Price(price=1, src=f'{self.slug}|Equal')

        price_result = self.context.run_model('chainlink.price-from-registry-maybe',
                                              input=new_input, return_type=PriceMaybe)
        if price_result.price is not None:
            return price_result.price

        override_base = self.OVERRIDE_FEED[self.context.chain_id].get(base.address, None)
        if override_base is not None:
            override_feed = Contract(**override_base[0])
            override_quote = Currency(**override_base[1])

            p0 = self.context.run_model('chainlink.price-by-feed',
                                        input=override_feed,
                                        return_type=Price)
            if override_quote.address == quote.address:
                return p0
            else:
                p1 = self.context.run_model(self.slug,
                                            input={'base': override_base[1], 'quote': quote},
                                            return_type=Price)
                return p0.cross(p1)

        override_quote = self.OVERRIDE_FEED[self.context.chain_id].get(quote.address, None)
        if override_quote is not None:
            override_feed = Contract(**override_quote[0])
            override_quote = Currency(**override_quote[1])

            p0 = self.context.run_model('chainlink.price-by-feed',
                                        input=override_feed,
                                        return_type=Price).inverse()
            if override_quote.address == base.address:
                return p0
            else:
                p1 = self.context.run_model(self.slug,
                                            input={'base': override_quote, 'quote': base},
                                            return_type=Price).inverse()
            return p0.cross(p1)

        for r1 in self.ROUTING_ADDRESSES:
            p0 = None
            if r1 != quote:
                price_input = PriceInput(base=base, quote=Currency(address=r1))
                p0_maybe = self.context.run_model('chainlink.price-from-registry-maybe',
                                                  input=price_input,
                                                  return_type=PriceMaybe)
                if p0_maybe.price is not None:
                    p0 = p0_maybe.price

                    for r2 in self.ROUTING_ADDRESSES:
                        if r2 != base:
                            price_input = PriceInput(base=Currency(address=r2), quote=quote)
                            p1_maybe = self.context.run_model('chainlink.price-from-registry-maybe',
                                                              input=price_input,
                                                              return_type=PriceMaybe)
                            if p1_maybe.price is not None:
                                p1 = p1_maybe.price

                                if r1 == r2:
                                    return p0.cross(p1)
                                else:
                                    bridge_price = self.context.run_model(
                                        self.slug,
                                        input={'base': {"address": r1},
                                               'quote': {"address": r2}},
                                        return_type=Price)
                                    return p0.cross(bridge_price).cross(p1)

        if new_input == input:
            raise ModelRunError(f'No possible feed/routing for token pair '
                                f'{input.base}/{input.quote}')
        else:
            raise ModelRunError(f'No possible feed/routing for token pair '
                                f'{input.base}/{input.quote}, '
                                f'replaced by {new_input.base}/{new_input.quote}')
