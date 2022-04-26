# pylint: disable=locally-disabled, unused-import
from typing import List

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import (
    Token,
    Price,
    Contract,
    Accounts,
    Contracts,
)

from credmark.dto import DTO, IterableListGenericDTO


@Model.describe(slug='price',
                version='1.1',
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
                version='1.0',
                display_name='Token Price',
                description='The Current Credmark Supported Price Algorithm',
                developer='Credmark',
                input=Token,
                output=Price)
class TokenPriceModel(Model):
    """
    Return token's price
    """

    def run(self, input: Token) -> Price:
        prices = []
        uniswap_v2 = Price(**self.context.models.uniswap_v2.get_average_price(input))
        if uniswap_v2.price is not None:
            prices.append(uniswap_v2)
        uniswap_v3 = Price(**self.context.models.uniswap_v3.get_average_price(input))
        if uniswap_v3.price is not None:
            prices.append(uniswap_v3)
        sushiswap = Price(**self.context.models.sushiswap.get_average_price(input))
        if sushiswap.price is not None:
            prices.append(sushiswap)
        average_price = 0
        if len(prices) > 0:
            average_price = sum([p.price for p in prices]) / len(prices)
            srcs = '|'.join([p.src for p in prices])
            return Price(price=average_price, src=self.slug+':'+srcs)
        else:
            return Price(price=None, src=self.slug)


@Model.describe(slug='token.price-ext',
                version='1.0',
                display_name='Token Price',
                description='The Current Credmark Supported Price Algorithm (fast)',
                developer='Credmark',
                input=Token,
                output=Price)
class TokenPriceModelExt(Model):
    """
    Return token's price with immediate available source.
    """

    def run(self, input: Token) -> Price:
        # Token initialization test
        # _ = input.proxy_for
        # _ = input.decimals
        # _ = input.functions.implementation.call()

        uniswap_v2 = Price(**self.context.models.uniswap_v2.get_average_price(input))
        if uniswap_v2.price is not None:
            return uniswap_v2
        uniswap_v3 = Price(**self.context.models.uniswap_v3.get_average_price(input))
        if uniswap_v3.price is not None:
            return uniswap_v3
        sushiswap = Price(**self.context.models.sushiswap.get_average_price(input))
        if sushiswap.price is not None:
            return sushiswap
        return Price(price=None, src=self.slug)
