from credmark.cmf.model import Model, ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (
    Account,
    Address,
    Price,
)

from models.dtos.price import PriceInput, ChainlinkAddress

PRICE_DATA_ERROR_DESC = ModelDataErrorDesc(
    code=ModelDataError.Codes.NO_DATA,
    code_desc='No pools to aggregate for token price')


@Model.describe(slug='price.oracle-chainlink',
                version='1.2',
                display_name='Token Price - from Oracle',
                description='Get token\'s price from Oracle',
                input=PriceInput,
                output=Price)
class PriceOracle(Model):

    NATIVE_TOKEN = {
        1: Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'),
    }

    # The native token on other chain, give a direct address of feed.
    # TODO: find the token address so to find the feed in Chainlink's registry
    OVERRIDE_FEED = {
        1: {
            # WAVAX: avax-usd.data.eth
            Address('0x85f138bfEE4ef8e540890CFb48F620571d67Eda3'):
            ('0xFF3EEb22B5E3dE6e705b44749C2559d704923FD7', 'USD'),
            # WSOL: sol-usd.data.eth
            Address('0xD31a59c85aE9D8edEFeC411D448f90841571b89c'):
            ('0x4ffc43a60e009b551865a93d232e33fce9f01507', 'USD'),
            # BNB: bnb-usd.data.eth
            Address('0xB8c77482e45F1F44dE1745F52C74426C631bDD52'):
            ('0x14e613ac84a31f709eadbdf89c6cc390fdc9540a', 'USD'),
            # WCELO:
            Address('0xE452E6Ea2dDeB012e20dB73bf5d3863A3Ac8d77a'):
            ('0x10d35efa5c26c3d994c511576641248405465aef', 'USD'),
            # BTM
            Address('0xcb97e65f07da24d46bcdd078ebebd7c6e6e3d750'):
            ('0x9fccf42d21ab278e205e7bb310d8979f8f4b5751', 'USD'),
            # IOST
            Address('0xfa1a856cfa3409cfa145fa4e20eb270df3eb21ab'):
            ('0xd0935838935349401c73a06fcde9d63f719e84e5', 'USD'),
            # WBTC: only with BTC for WBTC/BTC
            # Address('0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'):
            # ('0xfdFD9C85aD200c506Cf9e21F1FD8dd01932FBB23', 'BTC'),
            # WETH:
            Address('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'):
            ('0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419', 'USD')
        }
    }

    ROUTING_ADDRESSES = [
        Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'),  # ETH
        Address('0x0000000000000000000000000000000000000348'),  # USD
        Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB'),  # BTC
    ]

    WRAP_TOKEN = {
        1: {
            # ETH => WETH
            Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'):
            Address('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'),
            # BTC => WBTC
            Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB'):
            Address('0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'),
        }
    }
    """
    Return the value of base token in amount of quote tokens
    """

    def cross_price(self, price0: Price, price1: Price) -> Price:
        return Price(price=price0.price * price1.price, src=f'{price0.src},{price1.src}')

    def run(self, _: PriceInput) -> Price:  # pylint: disable=too-many-return-statements)
        base = _.base
        if _.quote is None:
            quote = self.NATIVE_TOKEN[self.context.chain_id]
        else:
            quote = _.quote

        if base == quote:
            return Price(price=1, src=f'{self.slug}|Equal')

        try:
            return self.context.run_model('chainlink.price-by-registry',
                                          input={'base': base, 'quote': quote},
                                          return_type=Price)
        except ModelRunError:
            try:
                p = self.context.run_model('chainlink.price-by-registry',
                                           input={'base': quote, 'quote': base},
                                           return_type=Price)
                p.price = 1 / p.price
                p.src = f'{p.src}|Inverse'
                return p
            except ModelRunError:
                override_base = self.OVERRIDE_FEED[self.context.chain_id].get(base, None)
                override_quote = self.OVERRIDE_FEED[self.context.chain_id].get(quote, None)

                if override_base is not None:
                    p0 = self.context.run_model('chainlink.price-by-feed',
                                                input=Account(address=Address(override_base[0])),
                                                return_type=Price)
                    if ChainlinkAddress(override_base[-1]) == quote:
                        return p0
                    else:
                        p1 = self.context.run_model(
                            self.slug,
                            input={'base': override_base[-1], 'quote': quote},
                            return_type=Price)
                        return self.cross_price(p0, p1)

                if override_quote is not None:
                    p0 = self.context.run_model('chainlink.price-by-feed',
                                                input=Account(address=Address(override_quote[0])),
                                                return_type=Price)
                    p0.price = 1 / p0.price
                    p0.src = f'{p0.src}|Inverse'
                    if ChainlinkAddress(override_quote[-1]) == base:
                        return p0
                    else:
                        p1 = self.context.run_model(
                            self.slug,
                            input={'base': override_quote[-1], 'quote': base},
                            return_type=Price)
                        p1.price = 1 / p1.price
                        p1.src = f'{p1.src}|Inverse'
                    return self.cross_price(p0, p1)

                for r1 in self.ROUTING_ADDRESSES:
                    for r2 in self.ROUTING_ADDRESSES:
                        p0 = None
                        p1 = None
                        if r1 != quote:
                            try:
                                p0 = self.context.run_model(
                                    'chainlink.price-by-registry',
                                    input={'base': base, 'quote': r1},
                                    return_type=Price)
                            except ModelRunError:
                                try:
                                    p0 = self.context.run_model(
                                        'chainlink.price-by-registry',
                                        input={'base': r1, 'quote': base},
                                        return_type=Price)
                                    p0.price = 1 / p0.price
                                    p0.src = f'{p0.src}|Inverse'
                                except ModelRunError:
                                    continue

                        if r2 != base:
                            try:
                                p1 = self.context.run_model(
                                    'chainlink.price-by-registry',
                                    input={'base': r2, 'quote': quote},
                                    return_type=Price)
                            except ModelRunError:
                                try:
                                    p1 = self.context.run_model(
                                        'chainlink.price-by-registry',
                                        input={'base': quote, 'quote': r2},
                                        return_type=Price)
                                    p1.price = 1 / p1.price
                                    p1.src = f'{p1.src}|Inverse'
                                except ModelRunError:
                                    p1 = None

                        if p0 is not None and p1 is not None:
                            if r1 == r2:
                                return self.cross_price(p0, p1)
                            else:
                                bridge_price = self.context.run_model(
                                    self.slug,
                                    input={'base': r1, 'quote': r2},
                                    return_type=Price)
                                return self.cross_price(self.cross_price(p0, bridge_price), p1)

                raise ModelRunError(f'No possible routing for token pair {base}/{quote}')
