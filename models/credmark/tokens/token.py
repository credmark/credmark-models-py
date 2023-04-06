# pylint: disable=locally-disabled, unused-import, no-member, line-too-long
from typing import List

import requests
from credmark.cmf.model import Model
from credmark.cmf.model.errors import (ModelDataError, ModelInputError,
                                       ModelRunError)
from credmark.cmf.types import (Accounts, Address, Contracts, Currency, FiatCurrency, Maybe,
                                NativeToken, Network, Price, PriceWithQuote,
                                Token)
from credmark.cmf.types.block_number import BlockNumberOutOfRangeError
from credmark.dto import DTO, DTOField, IterableListGenericDTO, PrivateAttr
from web3 import Web3

SLOT_EIP1967 = hex(int(Web3.keccak(text='eip1967.proxy.implementation').hex(), 16) - 1)


def get_eip1967_proxy(context, logger, address, verbose):
    # pylint:disable=locally-disabled,protected-access
    """
    eip-1967 compliant, https://eips.ethereum.org/EIPS/eip-1967
    """
    token = Token(address=address)

    # trigger loading
    try:
        token.abi
    except Exception:
        pass

    # Got 0xca823F78C2Dd38993284bb42Ba9b14152082F7BD unrecognized by etherscan
    # assert token.proxy_for is not None

    # Many aTokens are not recognized as proxy in Etherscan
    # Token(address='0xfe8f19b17ffef0fdbfe2671f248903055afaa8ca').is_transparent_proxy
    # https://etherscan.io/address/0xfe8f19b17ffef0fdbfe2671f248903055afaa8ca#code
    # token.contract_name == 'InitializableImmutableAdminUpgradeabilityProxy'
    proxy_address = Address(context.web3.eth.get_storage_at(token.address, SLOT_EIP1967))
    if not proxy_address.is_null():
        token_implementation = Token(address=proxy_address)
        # TODO: Work around before we can load proxy in the past based on block number.
        if (token._meta.is_transparent_proxy and
            token.proxy_for is not None and
                proxy_address != token.proxy_for.address):
            logger.debug(
                f'token\'s implementation is corrected to '
                f'{proxy_address} from {token.proxy_for.address} for {token.address}')
        else:
            logger.debug(
                f'token\'s implementation is corrected to '
                f'{proxy_address} from no-proxy for {token.address}')

        token._meta.is_transparent_proxy = True
        token._meta.proxy_implementation = token_implementation
    else:
        if verbose:
            logger.info(f'Unable to retrieve proxy implementation for {address}')
        return None
    return token


def get_eip1967_proxy_err(context, logger, address, verbose):
    res = get_eip1967_proxy(context, logger, address, verbose)
    if res is None:
        raise ModelInputError(f'Unable to retrieve proxy implementation for {address}')
    return res


def recursive_proxy(token):
    # if 'tokenURI' in token.abi.functions
    proxy_for = token.proxy_for
    while True:
        if proxy_for is None:
            break

        token = proxy_for
        proxy_for = token.proxy_for


@Model.describe(slug='token.underlying-maybe',
                version='1.1',
                display_name='Token Price - Underlying',
                description='For token backed by underlying - get the address',
                developer='Credmark',
                category='protocol',
                tags=['token'],
                input=Token,
                output=Maybe[Address])
class TokenUnderlying(Model):
    """
    Return token's underlying token's address
    """

    def run(self, input: Token) -> Maybe[Address]:
        # pylint: disable=too-many-return-statements)
        try_eip1967 = get_eip1967_proxy(self.context, self.logger, input.address, False)
        if try_eip1967 is not None:
            input = try_eip1967
        if input.abi is not None:
            if input.proxy_for is not None and input.proxy_for.abi is not None:
                try:
                    abi_functions = input.proxy_for.abi.functions
                except BlockNumberOutOfRangeError as err:
                    raise BlockNumberOutOfRangeError(
                        err.data.message +
                        f' This is the proxy for Contract({input.address})') from err
            else:
                abi_functions = input.abi.functions

            if 'UNDERLYING_ASSET_ADDRESS' in abi_functions:
                return Maybe(just=input.functions.UNDERLYING_ASSET_ADDRESS().call())

            if 'underlyingAssetAddress' in abi_functions:
                return Maybe(just=input.functions.underlyingAssetAddress().call())

        # TODO: iearn DAI
        if input.address == Address('0xc2cb1040220768554cf699b0d863a3cd4324ce32'):
            return Maybe(just=Token(symbol='DAI').address)

        if input.address == Address('0x16de59092dae5ccf4a1e6439d611fd0653f0bd01'):
            return Maybe(just=Token(symbol='DAI').address)

        # TODO: iearn USDC
        if input.address == Address('0x26ea744e5b887e5205727f55dfbe8685e3b21951'):
            return Maybe(just=Token(symbol='USDC').address)

        if input.address == Address('0xd6ad7a6750a7593e092a9b218d66c0a814a3436e'):
            return Maybe(just=Token(symbol='USDC').address)

        if input.address == Address('0xe6354ed5bc4b393a5aad09f21c46e101e692d447'):
            return Maybe(just=Token(symbol='USDT').address)

        if input.address == Address('0x83f798e925bcd4017eb265844fddabb448f1707d'):
            return Maybe(just=Token(symbol='USDT').address)

        if input.address == Address('0x73a052500105205d34daf004eab301916da8190f'):
            return Maybe(just=Token(symbol='TUSD').address)

        if input.address == Address('0x04bc0ab673d88ae9dbc9da2380cb6b79c4bca9ae'):
            return Maybe(just=Token(symbol='BUSD').address)

        if input.address == Address('0xbbc455cb4f1b9e4bfc4b73970d360c8f032efee6'):
            return Maybe(just=Token(symbol='LINK').address)

        if input.address == Address('0x0e2ec54fc0b509f445631bf4b91ab8168230c752'):
            return Maybe(just=Token(symbol='LINK').address)

        # TODO: ycDAI
        if input.address == Address('0x99d1fa417f94dcd62bfe781a1213c092a47041bc'):
            return Maybe(just=Token(symbol='DAI').address)

        if input.address == Address('0x9777d7e2b60bb01759d0e2f8be2095df444cb07e'):
            return Maybe(just=Token(symbol='USDC').address)

        if input.address == Address('0x1be5d71f2da660bfdee8012ddc58d024448a0a59'):
            return Maybe(just=Token(symbol='USDT').address)

        # stkAAVE
        if input.address == Address('0x4da27a545c0c5B758a6BA100e3a049001de870f5'):
            return Maybe(just=Token(symbol='AAVE').address)

        return Maybe(just=None)


@Model.describe(slug="token.info",
                version="1.2",
                display_name="Token Information",
                developer="Credmark",
                category='protocol',
                tags=['token'],
                input=Token,
                output=Token
                )
class TokenInfoModel(Model):
    """
    Return token's information
    """

    def run(self, input: Token) -> Token:
        token_info = input.info
        if token_info.deployed_block_number is None:
            # pylint:disable=protected-access
            token_info._meta.deployed_block_number = self.context.run_model(
                'token.deployment', input)['deployed_block_number']
        return token_info


@Model.describe(slug="token.deployment",
                version="0.1",
                display_name="Token Information - deployment",
                developer="Credmark",
                category='protocol',
                tags=['token'],
                input=Token,
                output=dict)
class TokenInfoDeployment(Model):
    """
    Return token's information on deployment
    """

    code_by_block = {}

    def binary_search(self, low, high, contract_address):
        # Check base case
        if high >= low:
            mid = (high + low)//2
            if high == low:
                return low

            if self.code_by_block.get(hex(mid)) is None:
                try_get_code = self.context.web3.eth.get_code(contract_address, hex(mid)).hex()
                self.code_by_block[hex(mid)] = try_get_code
            else:
                try_get_code = self.code_by_block[hex(mid)]
            if try_get_code != '0x':
                return self.binary_search(low, mid, contract_address)
            elif try_get_code == '0x':
                return self.binary_search(mid+1, high, contract_address)
            else:
                return -1
        else:
            return -1

    def run(self, input: Token) -> dict:
        if self.context.web3.eth.get_code(input.address.checksum).hex() == '0x':
            raise ModelDataError(f'{input.address} is not an EOA account')

        res = self.binary_search(0, int(self.context.block_number), input.address.checksum)
        if res == -1:
            raise ModelDataError(f'Can not find deployment information for {input.address}')

        block = self.context.web3.eth.get_block(res)
        txs = block['transactions'] if 'transactions' in block else []
        deployer = None
        for tx in txs:
            receipt = self.context.web3.eth.get_transaction_receipt(tx.hex())  # type: ignore
            if receipt['contractAddress'] == input.address:
                deployer = receipt['from']
                break
            for log in receipt['logs']:
                if log['address'] == input.address:
                    deployer = receipt['from']
                    break

        if input.proxy_for is not None:
            proxy_deployer = self.context.run_model('token.deployment', input.proxy_for)
            return {'deployed_block_number': res, 'deployer': deployer, 'proxy_deployer': proxy_deployer}

        return {'deployed_block_number': res, 'deployer': deployer}


class TokenLogoOutput(DTO):
    logo_url: str = DTOField(description="URL of token's logo")


@ Model.describe(slug="token.logo",
                 version="1.2",
                 display_name="Token Logo",
                 developer="Credmark",
                 category='protocol',
                 tags=['token'],
                 input=Token,
                 output=TokenLogoOutput
                 )
class TokenLogoModel(Model):
    """
    Return token's logo
    """

    def run(self, input: Token) -> TokenLogoOutput:
        if self.context.chain_id != Network.Mainnet:
            raise ModelDataError(message="Logos are only available for ethereum mainnet",
                                 code=ModelDataError.Codes.NO_DATA)

        if self.context.block_number != 0:
            return self.context.run_model(self.slug,
                                          input,
                                          block_number=0,
                                          return_type=TokenLogoOutput)

        # Handle native token
        if input.address == NativeToken().address:
            return TokenLogoOutput(
                logo_url="https://raw.githubusercontent.com/trustwallet/assets/master"
                "/blockchains/ethereum/info/logo.png"
            )

        try_urls = [
            ("https://raw.githubusercontent.com/trustwallet/assets/master"
             f"/blockchains/ethereum/assets/{input.address.checksum}/logo.png"),
            ("https://raw.githubusercontent.com/uniswap/assets/master"
             f"/blockchains/ethereum/assets/{input.address.checksum}/logo.png"),
            ("https://raw.githubusercontent.com/sushiswap/logos/main"
             f"/network/ethereum/{input.address.checksum}.jpg"),
            ("https://raw.githubusercontent.com/sushiswap/assets/master"
             f"/blockchains/ethereum/assets/{input.address.checksum}/logo.png"),
            ("https://raw.githubusercontent.com/curvefi/curve-assets/main"
             f"/images/assets/{input.address}.png")
        ]

        for url in try_urls:
            # Return the first URL that exists
            if requests.head(url, timeout=60).status_code < 400:
                return TokenLogoOutput(logo_url=url)

        raise ModelDataError(
            message=f"Logo not available for {input.symbol, input.address.checksum}",
            code=ModelDataError.Codes.NO_DATA)


class TokenTotalSupplyOutput(DTO):
    total_supply: int = DTOField(description="Total supply of token")
    total_supply_scaled: float = DTOField(description="Total supply scaled to token decimals")


@Model.describe(slug="token.total-supply",
                version="1.0",
                display_name="Token total supply",
                developer="Credmark",
                category='protocol',
                tags=['token'],
                input=Token,
                output=TokenTotalSupplyOutput)
class TokenTotalSupplyModel(Model):
    """
    Return token's total supply
    """

    def run(self, input: Token) -> TokenTotalSupplyOutput:
        return TokenTotalSupplyOutput(
            total_supply=input.total_supply,
            total_supply_scaled=input.total_supply_scaled,
        )


class TokenBalanceInput(Token):
    account: Address = \
        DTOField(
            description='Account address for which to fetch balance.')
    quote: Currency = \
        DTOField(FiatCurrency(symbol='USD'),
                 description='Quote token address to count the value')


class TokenBalanceOutput(DTO):
    balance: int = DTOField(description="Balance of account")
    balance_scaled: float = DTOField(description="Balance scaled to token decimals for account")
    value: float = DTOField(description="Balance in terms of quoted currency")
    price: Price = DTOField(description="Token price")


@Model.describe(slug="token.balance",
                version="1.1",
                display_name="Token Balance",
                developer="Credmark",
                category='protocol',
                tags=['token'],
                input=TokenBalanceInput,
                output=TokenBalanceOutput)
class TokenBalanceModel(Model):
    """
    Return token's balance
    """

    def run(self, input: TokenBalanceInput) -> TokenBalanceOutput:
        balance = input.balance_of(input.account.checksum)

        token_price = PriceWithQuote(**self.context.models.price.quote({
            'base': input,
            'quote': input.quote
        }))

        return TokenBalanceOutput(
            balance=balance,
            balance_scaled=input.scaled(balance),
            value=token_price.price * input.scaled(balance),
            price=token_price
        )


class TokenHolderInput(Token):
    limit: int = DTOField(100, gt=0, description="Limit the number of holders that are returned")
    offset: int = \
        DTOField(0, ge=0,
                 description="Omit a specified number of holders from beginning of result set")
    quote: Currency = \
        DTOField(FiatCurrency(symbol='USD'),
                 description='Quote token address to count the value')


class TokenHolder(DTO):
    address: Address = DTOField(description="Address of holder")
    balance: int = DTOField(description="Balance of account")
    balance_scaled: float = DTOField(description="Balance scaled to token decimals for account")
    value: float = DTOField(description="Balance in terms of quoted currency")


class TokenHoldersOutput(IterableListGenericDTO[TokenHolder]):
    price: PriceWithQuote = DTOField(description="Token price")
    holders: List[TokenHolder] = DTOField(default=[], description='List of holders')
    total_holders: int = DTOField(description='Total number of holders')

    _iterator: str = PrivateAttr('positions')


@Model.describe(slug='token.holders',
                version='1.2',
                display_name='Token Holders',
                description='Holders of a Token',
                category='protocol',
                tags=['token'],
                input=TokenHolderInput,
                output=TokenHoldersOutput)
class TokenHolders(Model):
    def run(self, input: TokenHolderInput) -> TokenHoldersOutput:
        with self.context.ledger.TokenBalance as q:
            df = q.select(
                aggregates=[(q.TRANSACTION_VALUE.sum_(), 'balance'),
                            ('COUNT(*) OVER()', 'total_holders')],
                where=q.TOKEN_ADDRESS.eq(input.address),
                group_by=[q.ADDRESS],
                order_by=q.field('balance').dquote().desc(),
                having=q.field('balance').dquote().gt(0),
                limit=input.limit,
                offset=input.offset
            ).to_dataframe()

            token_price_maybe = Maybe[PriceWithQuote](**self.context.models.price.quote_maybe({
                'base': input,
                'quote': input.quote}))
            token_price = token_price_maybe.get_just(
                PriceWithQuote(price=0, src='', quoteAddress=input.quote.address))

            total_holders = df['total_holders'].values[0]
            if total_holders is None:
                total_holders = 0

            return TokenHoldersOutput(price=token_price,
                                      holders=[TokenHolder(
                                          address=Address(row['address']),
                                          balance=row['balance'],
                                          balance_scaled=input.scaled(row['balance']),
                                          value=token_price.price * input.scaled(row['balance']))
                                          for _, row in df.iterrows()],
                                      total_holders=total_holders)


class TokenHoldersCountOutput(DTO):
    count: int = DTOField(description='Total number of holders')


@Model.describe(slug='token.holders-count',
                version='1.0',
                display_name='Token Holders count',
                description='Total number of holders of a Token',
                category='protocol',
                tags=['token'],
                input=Token,
                output=TokenHoldersCountOutput)
class TokenHoldersCount(Model):
    def run(self, input: Token) -> TokenHoldersCountOutput:
        with self.context.ledger.TokenBalance as q:
            df = q.select(
                aggregates=[(q.TRANSACTION_VALUE.sum_(), 'balance'),
                            ('COUNT(*) OVER()', 'total_holders')],
                where=q.TOKEN_ADDRESS.eq(input.address),
                group_by=[q.ADDRESS],
                order_by=q.field('balance').dquote().desc(),
                having=q.field('balance').dquote().gt(0),
                limit=1,
            ).to_dataframe()

            total_holders = df['total_holders'].values[0]
            if total_holders is None:
                total_holders = 0

            return TokenHoldersCountOutput(count=total_holders)


@Model.describe(slug='token.holders-all',
                version='0.3',
                display_name='Token Holders All',
                description='All holders of a Token',
                category='protocol',
                tags=['token'],
                input=Token,
                output=dict)
class TokenNumberHolders(Model):
    def run(self, input: Token) -> dict:
        with self.context.ledger.TokenTransfer as q:
            df = q.select(aggregates=[],
                          group_by=[q.ADDRESS],
                          where=q.TOKEN_ADDRESS.eq(input.address),
                          having=q.VALUE.sum_().gt(0)
                          ).to_dataframe()
        return df.to_dict()


@Model.describe(slug='token.swap-pools',
                version='1.0',
                display_name='Swap Pools for Token',
                description='All swap pools available for the current Token',
                category='protocol',
                subcategory='uniswap',
                input=Token,
                output=Contracts)
class TokenSwapPools(Model):
    def run(self, input: Token) -> Contracts:
        response = Contracts(contracts=[])
        response.contracts.extend(Contracts(**self.context.models.uniswap_v3.get_pools(input)))
        response.contracts.extend(Contracts(**self.context.models.uniswap_v2.get_pools(input)))
        response.contracts.extend(Contracts(**self.context.models.sushiswap.get_pools(input)))
        return response


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
                version='1.2',
                display_name='Token Categorized Supply',
                description='The categorized supply for a token',
                category='protocol',
                tags=['token'],
                input=CategorizedSupplyRequest,
                output=CategorizedSupplyResponse)
class TokenCirculatingSupply(Model):
    def run(self, input: CategorizedSupplyRequest) -> CategorizedSupplyResponse:
        response = CategorizedSupplyResponse(**input.dict())
        total_supply_scaled = input.token.scaled(input.token.total_supply)
        token_price = PriceWithQuote(**self.context.models.price.quote({'base': input.token}))
        if token_price is None:
            raise ModelRunError(f"No Price for {response.token}")
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
            amountScaled=total_supply_scaled - sum(c.amountScaled for c in response.categories)
        ))
        response.circulatingSupplyScaled = sum(
            c.amountScaled for c in response.categories if c.circulating)
        if isinstance(token_price.price, float):
            if isinstance(response.circulatingSupplyScaled, float):
                response.circulatingSupplyUsd = response.circulatingSupplyScaled * token_price.price
        return response
