# pylint: disable=locally-disabled, unused-import
from typing import List

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import Address, Accounts, Contract, Contracts, Price, Token
from credmark.dto import DTO, IterableListGenericDTO
from models.dtos.price import AddressMaybe


def get_eip1967_proxy(context, logger, token_address, verbose):
    # pylint:disable=locally-disabled,protected-access
    """
    eip-1967 compliant, https://eips.ethereum.org/EIPS/eip-1967
    """
    default_proxy_address = ''.join(['0'] * 40)

    token = Token(address=token_address)
    # Got 0xca823F78C2Dd38993284bb42Ba9b14152082F7BD unrecognized by etherscan
    # assert token.proxy_for is not None

    # Many aTokens are not recognized as proxy in Etherscan
    # Token(address='0xfe8f19b17ffef0fdbfe2671f248903055afaa8ca').is_transparent_proxy
    # https://etherscan.io/address/0xfe8f19b17ffef0fdbfe2671f248903055afaa8ca#code
    # token.contract_name == 'InitializableImmutableAdminUpgradeabilityProxy'
    proxy_address = context.web3.eth.get_storage_at(
        token.address,
        '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc').hex()
    if proxy_address[-40:] != default_proxy_address:
        proxy_address = '0x' + proxy_address[-40:]
        token_implemenation = Token(address=proxy_address)
        # TODO: Work around before we can load proxy in the past based on block number.
        if (token._meta.is_transparent_proxy and
            token.proxy_for is not None and
                proxy_address != token.proxy_for.address):
            logger.debug(
                f'token\'s implmentation is corrected to '
                f'{proxy_address} from {token.proxy_for.address} for {token.address}')
        else:
            logger.debug(
                f'token\'s implmentation is corrected to '
                f'{proxy_address} from no-proxy for {token.address}')

        token._meta.is_transparent_proxy = True
        token._meta.proxy_implementation = token_implemenation
    else:
        if verbose:
            logger.info(f'Unable to retrieve proxy implementation for {token_address}')
        return None
    return token


def get_eip1967_proxy_err(context, logger, token_address, verbose):
    res = get_eip1967_proxy(context, logger, token_address, verbose)
    if res is None:
        raise ModelDataError(f'Unable to retrieve proxy implementation for {token_address}')
    return res


@Model.describe(slug='token.underlying',
                version='1.1',
                display_name='Token Price - Underlying',
                description='For token backed by underlying - get the address',
                developer='Credmark',
                input=Token,
                output=AddressMaybe)
class TokenUnderlying(Model):
    """
    Return token's underlying token's address
    """

    def run(self, input: Token) -> AddressMaybe:
        try_eip1967 = get_eip1967_proxy(self.context, self.logger, input.address, False)
        if try_eip1967 is not None:
            input = try_eip1967
        if input.abi is not None:
            if input.proxy_for is not None:
                abi_functions = input.proxy_for.abi.functions
            else:
                abi_functions = input.abi.functions

            if 'UNDERLYING_ASSET_ADDRESS' in abi_functions:
                return AddressMaybe(address=input.functions.UNDERLYING_ASSET_ADDRESS().call())

            if 'underlyingAssetAddress' in abi_functions:
                return AddressMaybe(address=input.functions.underlyingAssetAddress().call())

        # TODO: iearn DAI
        if input.address == Address('0xc2cb1040220768554cf699b0d863a3cd4324ce32'):
            return AddressMaybe(address=Token(symbol='DAI').address)

        if input.address == Address('0x16de59092dae5ccf4a1e6439d611fd0653f0bd01'):
            return AddressMaybe(address=Token(symbol='DAI').address)

        # TODO: iearn USDC
        if input.address == Address('0x26ea744e5b887e5205727f55dfbe8685e3b21951'):
            return AddressMaybe(address=Token(symbol='USDC').address)

        if input.address == Address('0xd6ad7a6750a7593e092a9b218d66c0a814a3436e'):
            return AddressMaybe(address=Token(symbol='USDC').address)

        if input.address == Address('0xe6354ed5bc4b393a5aad09f21c46e101e692d447'):
            return AddressMaybe(address=Token(symbol='USDT').address)

        if input.address == Address('0x83f798e925bcd4017eb265844fddabb448f1707d'):
            return AddressMaybe(address=Token(symbol='USDT').address)

        if input.address == Address('0x73a052500105205d34daf004eab301916da8190f'):
            return AddressMaybe(address=Token(symbol='TUSD').address)

        if input.address == Address('0x04bc0ab673d88ae9dbc9da2380cb6b79c4bca9ae'):
            return AddressMaybe(address=Token(symbol='BUSD').address)

        if input.address == Address('0xbbc455cb4f1b9e4bfc4b73970d360c8f032efee6'):
            return AddressMaybe(address=Token(symbol='LINK').address)

        if input.address == Address('0x0e2ec54fc0b509f445631bf4b91ab8168230c752'):
            return AddressMaybe(address=Token(symbol='LINK').address)

        # TODO: ycDAI
        if input.address == Address('0x99d1fa417f94dcd62bfe781a1213c092a47041bc'):
            return AddressMaybe(address=Token(symbol='DAI').address)

        if input.address == Address('0x9777d7e2b60bb01759d0e2f8be2095df444cb07e'):
            return AddressMaybe(address=Token(symbol='USDC').address)

        if input.address == Address('0x1be5d71f2da660bfdee8012ddc58d024448a0a59'):
            return AddressMaybe(address=Token(symbol='USDT').address)

        return AddressMaybe(address=None)


@Model.describe(
    slug="token.info",
    version="1.1",
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
        token_price = Price(**self.context.models.price.quote({'base': input.token}))
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
