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


@Model.describe(
    slug="token.info",
    version="1.0",
    display_name="Token Information",
    developer="Credmark",
    input=Token,
    output=Token
)
class TokenInfoModel(Model):
    """
    Return token's information
    """

    def run(self, input: Token) -> Token:
        return input.info


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
            return Price(price=average_price, src=self.slug)
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


@Model.describe(slug='token.holders',
                version='1.0',
                display_name='Token Holders',
                description='The number of holders of a Token',
                input=Token,
                output=dict)
class TokenHolders(Model):
    def run(self, _input: Token) -> dict:
        # TODO: Get Holders
        return {"result": 0}


@Model.describe(slug='token.swap-pools',
                version='1.0',
                display_name='Swap Pools for Token',
                description='All swap pools available for the current Token',
                input=Token,
                output=Contracts)
class TokenSwapPools(Model):
    def run(self, input: Token) -> Contracts:
        response = Contracts(contracts=[])
        response.contracts.extend(Contracts(**self.context.models.uniswap_v3.get_pools(input)))
        response.contracts.extend(Contracts(**self.context.models.uniswap_v2.get_pools(input)))
        response.contracts.extend(Contracts(**self.context.models.sushiswap.get_pools(input)))
        return response


@Model.describe(slug='token.swap-pool-volume',
                version='1.0',
                display_name='Token Volume',
                description='The current volume for a swap pool',
                input=Contract,
                output=dict)
class TokenSwapPoolVolume(Model):
    def run(self, input: Token) -> dict:
        # TODO: Get All Credmark Supported swap Pools for a token
        return {"result": 0}


@Model.describe(slug='token.overall-volume',
                version='1.0',
                display_name='Token Volume',
                description='The Current Credmark Supported trading volume algorithm',
                input=Token,
                output=dict)
class TokenVolume(Model):
    def run(self, input) -> dict:
        # TODO: Get Overall Volume
        return {"result": 0}


class CategorizedSupplyRequest(IterableListGenericDTO):
    class CategorizedSupplyCategory(DTO):
        accounts: Accounts
        categoryName: str
        categoryType: str = ''
        circulating: bool = False

    categories: List[CategorizedSupplyCategory]
    _iterator: str = 'categories'
    token: Token


class CategorizedSupplyResponse(CategorizedSupplyRequest):
    class CategorizedSupplyCategory(CategorizedSupplyRequest.CategorizedSupplyCategory):
        amountScaled: float = 0.0
        valueUsd: float = 0.0
    categories: List[CategorizedSupplyCategory]
    _iterator: str = 'categories'
    circulatingSupplyScaled: float = 0.0
    circulatingSupplyUsd: float = 0.0


@Model.describe(slug='token.categorized-supply',
                version='1.0',
                display_name='Token Categorized Supply',
                description='The categorized supply for a token',
                input=CategorizedSupplyRequest,
                output=CategorizedSupplyResponse)
class TokenCirculatingSupply(Model):
    def run(self, input: CategorizedSupplyRequest) -> CategorizedSupplyResponse:
        response = CategorizedSupplyResponse(**input.dict())
        total_supply_scaled = input.token.scaled(input.token.total_supply)
        token_price = Price(**self.context.models.token.price(input.token))
        if token_price is None:
            raise ModelDataError(f"No Price for {response.token}")
        for c in response.categories:
            for account in c.accounts:
                bal = response.token.functions.balanceOf(account.address).call()
                c.amountScaled += response.token.scaled(bal)
            if token_price is not None and token_price.price is not None:
                c.valueUsd = c.amountScaled * token_price.price
        response.categories.append(CategorizedSupplyResponse.CategorizedSupplyCategory(
            accounts=Accounts(accounts=[]),
            categoryName='uncategorized',
            categoryType='uncategorized',
            circulating=True,
            amountScaled=total_supply_scaled - sum([c.amountScaled for c in response.categories])
        ))
        response.circulatingSupplyScaled = sum(
            [c.amountScaled for c in response.categories if c.circulating])
        if isinstance(token_price.price, float):
            if isinstance(response.circulatingSupplyScaled, float):
                response.circulatingSupplyUsd = response.circulatingSupplyScaled * token_price.price
        return response
