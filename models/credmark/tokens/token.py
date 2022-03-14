
import credmark.model
from credmark.types import Address, Token, Account, Position, Price, Contract, Accounts, Contracts
from credmark.types.data.token_wei import TokenWei
from credmark.types.dto import DTO, DTOField, IterableListGenericDTO
from typing import List


class TokenInfo(DTO):
    token: Token
    total_supply_wei: int
    total_supply: float


@credmark.model.describe(
    slug="token.info",
    version="1.0",
    display_name="Token Information",
    developer="Credmark",
    input=Token,
    output=TokenInfo
)
class TokenInfoModel(credmark.model.Model):
    def run(self, input: Token) -> TokenInfo:
        input.load()
        total_supply = input.total_supply()
        return TokenInfo(
            token=input,
            total_supply=total_supply.scaled,
            total_supply_wei=total_supply
        )


@credmark.model.describe(slug='price',
                         version='1.0',
                         display_name='Token Price',
                         description='The Current Credmark Supported Price Algorithm',
                         input=Token,
                         output=Price)
class PriceModel(credmark.model.Model):
    def run(self, input: Token) -> Price:
        return self.context.run_model('uniswap-v3.get-average-price', input, return_type=Price)


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
        # TODO: Get All Credmark Supported swap Pools for a token
        response = Contracts(contracts=[])
        response.contracts.extend(
            self.context.run_model('uniswap-v3.get-pools', input, return_type=Contracts)
        )
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
        response = CategorizedSupplyResponse(**input.dict())
        total_supply_scaled = input.token.total_supply().scaled

        for c in response.categories:
            for account in c.accounts:
                c.amountScaled += response.token.balance_of(account.address).scaled
            c.valueUsd = c.amountScaled * response.token.price_usd
        response.categories.append(CategorizedSupplyResponse.CategorizedSupplyCategory(
            accounts=Accounts(accounts=[]),
            categoryName='uncategorized',
            categoryType='uncategorized',
            circulating=True,
            amountScaled=total_supply_scaled - sum([c.amountScaled for c in response.categories])
        ))
        response.circulatingSupplyScaled = sum(
            [c.amountScaled for c in response.categories if c.circulating])
        response.circulatingSupplyUsd = response.circulatingSupplyScaled * input.token.price_usd
        return response
