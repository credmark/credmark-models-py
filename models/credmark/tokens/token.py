# pylint: disable=locally-disabled, unused-import

import credmark.model
from credmark.model.errors import ModelDataError
from credmark.types import (
    Address,
    Token,
    Account,
    Position,
    Price,
    Contract,
    Accounts,
    Contracts
)

from credmark.types.data.token_wei import (
    TokenWei
)
from credmark.types.models.ledger import (
    TokenTransferTable
)

from credmark.dto import (
    DTO,
    DTOField,
    IterableListGenericDTO
)
from typing import List, Union


@credmark.model.describe(
    slug="token.info",
    version="1.0",
    display_name="Token Information",
    developer="Credmark",
    input=Token,
    output=Token
)
class TokenInfoModel(credmark.model.Model):
    def run(self, input: Token) -> Token:
        return input.info


@credmark.model.describe(slug='price',
                         version='1.1',
                         display_name='Token Price',
                         description='DEPRECATED - use token.price',
                         input=Token,
                         output=Price)
class PriceModel(credmark.model.Model):
    def run(self, input: Token) -> Price:
        return self.context.run_model('token.price', input, return_type=Price)


@credmark.model.describe(slug='token.price',
                         version='1.0',
                         display_name='Token Price',
                         description='The Current Credmark Supported Price Algorithm',
                         developer='Credmark',
                         input=Token,
                         output=Price)
class TokenPriceModel(credmark.model.Model):
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
        return Price(price=average_price)


@credmark.model.describe(slug='token.holders',
                         version='1.0',
                         display_name='Token Holders',
                         description='The number of holders of a Token',
                         input=Token,
                         output=dict)
class TokenHolders(credmark.model.Model):
    def run(self, input: Token) -> dict:
        # TODO: Get Holders
        return {"result": 0}


@credmark.model.describe(slug='token.swap-pools',
                         version='1.0',
                         display_name='Swap Pools for Token',
                         description='All swap pools available for the current Token',
                         input=Token,
                         output=Contracts)
class TokenSwapPools(credmark.model.Model):
    def run(self, input: Token) -> Contracts:
        response = Contracts(contracts=[])
        response.contracts.extend(Contracts(**self.context.models.uniswap_v3.get_pools(input)))
        response.contracts.extend(Contracts(**self.context.models.uniswap_v2.get_pools(input)))
        response.contracts.extend(Contracts(**self.context.models.sushiswap.get_pools(input)))
        return response


@credmark.model.describe(slug='token.swap-pool-volume',
                         version='1.0',
                         display_name='Token Volume',
                         description='The current volume for a swap pool',
                         input=Contract,
                         output=dict)
class TokenSwapPoolVolume(credmark.model.Model):
    def run(self, input: Token) -> dict:
        # TODO: Get All Credmark Supported swap Pools for a token
        return {"result": 0}


@credmark.model.describe(slug='token.overall-volume',
                         version='1.0',
                         display_name='Token Volume',
                         description='The Current Credmark Supported trading volume algorithm',
                         input=Token,
                         output=dict)
class TokenVolume(credmark.model.Model):
    def run(self, input: Token) -> dict:
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


@credmark.model.describe(slug='token.categorized-supply',
                         version='1.0',
                         display_name='Token Categorized Supply',
                         description='The categorized supply for a token',
                         input=CategorizedSupplyRequest,
                         output=CategorizedSupplyResponse)
class TokenCirculatingSupply(credmark.model.Model):
    def run(self, input: CategorizedSupplyRequest) -> CategorizedSupplyResponse:
        if input.token.price_usd is None:
            raise ModelDataError('Input token price is None')
        response = CategorizedSupplyResponse(**input.dict())
<<<<<<< HEAD
        total_supply_scaled = input.token.scaled(input.token.total_supply)
        token_price = Price(**self.context.models.token.price(input.token))
        if token_price is None:
            raise ModelDataError(f"No Price for {response.token}")
=======
        if response.token.price_usd is None:
            raise ModelDataError('Response token price is None')

        total_supply_scaled = input.token.total_supply().scaled
        token_price: Union[Price, None] = self.context.models.token.price(input.token)

>>>>>>> 29b05fb (fix typing with examples)
        for c in response.categories:
            for account in c.accounts:
                c.amountScaled += response.token.scaled(
                    response.token.functions.balanceOf(account.address))
            if token_price is not None and token_price.price is not None:
                c.valueUsd = c.amountScaled * token_price.price
        response.categories.append(CategorizedSupplyResponse.CategorizedSupplyCategory(
            accounts=Accounts(accounts=[]),
            categoryName='uncategorized',
            categoryType='uncategorized',
            circulating=True,
            amountScaled=total_supply_scaled -
            sum([c.amountScaled for c in response.categories])
        ))
<<<<<<< HEAD
        response.circulatingSupplyScaled = sum(
            [c.amountScaled for c in response.categories if c.circulating])
        if isinstance(token_price.price, float):
            if isinstance(response.circulatingSupplyScaled, float):
                response.circulatingSupplyUsd = response.circulatingSupplyScaled * token_price.price
=======

        all_circulating = [c.amountScaled for c in response.categories if c.circulating]
        if len(all_circulating) > 0:
            response.circulatingSupplyScaled = sum(all_circulating)
        else:
            response.circulatingSupplyScaled = 0
        response.circulatingSupplyUsd = response.circulatingSupplyScaled * input.token.price_usd
>>>>>>> 29b05fb (fix typing with examples)
        return response
