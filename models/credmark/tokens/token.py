# pylint: disable=locally-disabled, unused-import, no-member
from typing import List

from credmark.cmf.model import Model
from credmark.cmf.model.errors import (ModelDataError, ModelInputError,
                                       ModelRunError)
from credmark.cmf.types import (Accounts, Address, BlockNumber, Contract,
                                Contracts, Maybe, Price, Token)
from credmark.cmf.types.block_number import BlockNumberOutOfRangeError
from credmark.dto import DTO, DTOField, IterableListGenericDTO
from models.tmp_abi_lookup import ERC_20_ABI
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
            logger.info(f'Unable to retrieve proxy implementation for {address}')
        return None
    return token


def get_eip1967_proxy_err(context, logger, address, verbose):
    res = get_eip1967_proxy(context, logger, address, verbose)
    if res is None:
        raise ModelInputError(f'Unable to retrieve proxy implementation for {address}')
    return res


def fix_erc20_token(tok):
    try:
        _ = tok.abi
    except ModelDataError:
        tok = Token(address=tok.checksum, abi=ERC_20_ABI)

    if tok.proxy_for is not None:
        try:
            _ = tok.proxy_for.abi
        except BlockNumberOutOfRangeError as err:
            raise BlockNumberOutOfRangeError(
                err.data.message + f' This is for Contract({tok.address})')
        except ModelDataError:
            tok.proxy_for._loaded = True  # pylint:disable=protected-access
            tok.proxy_for.set_abi(ERC_20_ABI)

    return tok


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
            if input.proxy_for is not None:
                try:
                    abi_functions = input.proxy_for.abi.functions
                except BlockNumberOutOfRangeError as err:
                    raise BlockNumberOutOfRangeError(
                        err.data.message + f' This is the proxy for Contract({input.address})')
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

        return Maybe(just=None)


@Model.describe(
    slug="token.info",
    version="1.1",
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
        return input.info


class TokenHolderInput(Token):
    top_n: int = DTOField(10, description='Top N holders')


@Model.describe(slug='token.holders',
                version='0.2',
                display_name='Token Holders',
                description='The number of holders of a Token',
                category='protocol',
                tags=['token'],
                input=TokenHolderInput,
                output=dict)
class TokenHolders(Model):
    def run(self, input: TokenHolderInput) -> dict:
        with self.context.ledger.TokenBalance as q:
            df = q.select(aggregates=[(q.TRANSACTION_VALUE.sum_(), 'sum_value')],
                          group_by=[q.ADDRESS],
                          where=q.TOKEN_ADDRESS.eq(input.address),
                          order_by=q.field('sum_value').dquote().desc(),
                          limit=input.top_n).to_dataframe()
        return df.to_dict()


@Model.describe(slug='token.holders-all',
                version='0.2',
                display_name='Token Holders All',
                description='All holders of a Token',
                category='protocol',
                tags=['token'],
                input=Token,
                output=dict)
class TokenNumberHolders(Model):
    def run(self, input: Token) -> dict:
        with self.context.ledger.TokenBalance as q:
            df = q.select(aggregates=[],
                          group_by=[q.ADDRESS],
                          where=q.TOKEN_ADDRESS.eq(input.address),
                          having=q.TRANSACTION_VALUE.sum_().gt(0)
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


@Model.describe(slug='token.swap-pool-volume',
                version='1.0',
                display_name='Token Volume',
                description='The current volume for a swap pool',
                category='protocol',
                tags=['token'],
                input=Contract,
                output=dict)
class TokenSwapPoolVolume(Model):
    def run(self, input: Token) -> dict:
        # TODO: Get All Credmark Supported swap Pools for a token
        return {"result": 0}


class TokenVolumeWindowInput(Token):
    window: str


class TokenVolumeOutput(Token):
    volume: int
    volume_scaled: float
    value_last: float

    from_block: int
    to_block: int

    @classmethod
    def default(cls, _address, from_block, to_block):
        return cls(address=_address, volume=0, volume_scaled=0, value_last=0,
                   from_block=from_block, to_block=to_block)


@Model.describe(slug='token.overall-volume-window',
                version='1.0',
                display_name='Token Volume',
                description='The Current Credmark Supported trading volume algorithm',
                category='protocol',
                tags=['token'],
                input=TokenVolumeWindowInput,
                output=TokenVolumeOutput)
class TokenVolumeWindow(Model):
    def run(self, input: TokenVolumeWindowInput) -> TokenVolumeOutput:
        window_in_seconds = self.context.historical.to_seconds(input.window)
        old_block_timestamp = self.context.block_number.timestamp - window_in_seconds
        old_block = BlockNumber.from_timestamp(old_block_timestamp)

        return self.context.run_model(
            'token.overall-volume-block',
            input=TokenVolumeBlockInput(
                address=input.address,
                block_number=old_block),
            return_type=TokenVolumeOutput)


class TokenVolumeBlockInput(Token):
    block_number: int = DTOField(
        description=('Positive for a block earlier than the current one '
                     'or negative or zero for an interval. '
                     'Both excludes the start block.'))


@Model.describe(slug='token.overall-volume-block',
                version='1.0',
                display_name='Token Volume',
                description='The Current Credmark Supported trading volume algorithm',
                category='protocol',
                tags=['token'],
                input=TokenVolumeBlockInput,
                output=TokenVolumeOutput)
class TokenVolumeBlock(Model):
    def run(self, input: TokenVolumeBlockInput) -> TokenVolumeOutput:
        token_address = input.address
        old_block = input.block_number

        if old_block >= 0:
            if old_block > self.context.block_number:
                raise ModelRunError(f'input {input.block_number=} shall be earlier '
                                    f'than the current block {self.context.block_number}')
        else:
            old_block = self.context.block_number + old_block

        to_block = self.context.block_number
        with self.context.ledger.TokenTransfer as q:
            df = q.select(aggregates=[(q.VALUE.sum_(), 'sum_value')],
                          where=(q.TOKEN_ADDRESS.eq(token_address)
                                  .and_(q.BLOCK_NUMBER.gt(old_block))),
                          ).to_dataframe()

        vol = df.sum_value.sum()
        vol_scaled = input.scaled(vol)
        price_last = self.context.models.price.quote(base=Token(input.address),
                                                     return_type=Price).price  # type: ignore
        value_last = vol_scaled * price_last

        output = TokenVolumeOutput(
            address=input.address,
            volume=vol,
            volume_scaled=vol_scaled,
            value_last=value_last,
            from_block=old_block+1,
            to_block=to_block
        )

        return output


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
                version='1.1',
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
        token_price = Price(**self.context.models.price.quote({'base': input.token}))
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
