# pylint: disable=locally-disabled, no-member, line-too-long, invalid-name

import math
from decimal import Decimal
from typing import List, Optional

import requests
from credmark.cmf.model import CachePolicy, ImmutableModel, ImmutableOutput, Model
from credmark.cmf.model.errors import ModelDataError, ModelInputError, ModelRunError
from credmark.cmf.types import (
    Accounts,
    Address,
    BlockNumber,
    BlockNumberOutOfRangeError,
    Contract,
    Contracts,
    Currency,
    FiatCurrency,
    Maybe,
    NativeToken,
    Network,
    NetworkDict,
    Price,
    PriceWithQuote,
    Some,
    Token,
)
from credmark.dto import DTO, DTOField, IterableListGenericDTO, PrivateAttr
from web3 import Web3

SLOT_EIP1967 = hex(
    int(Web3.keccak(text='eip1967.proxy.implementation').hex(), 16) - 1)


def get_eip1967_proxy(context, logger, address, verbose):
    # pylint:disable=locally-disabled,protected-access
    """
    eip-1967 compliant, https://eips.ethereum.org/EIPS/eip-1967
    """
    token = Token(address=address)

    # trigger loading
    try:
        _ = token.abi
    except Exception:
        pass

    # Got 0xca823F78C2Dd38993284bb42Ba9b14152082F7BD unrecognized by etherscan
    # assert token.proxy_for is not None

    # Many aTokens are not recognized as proxy in Etherscan
    # Token(address='0xfe8f19b17ffef0fdbfe2671f248903055afaa8ca').is_transparent_proxy
    # https://etherscan.io/address/0xfe8f19b17ffef0fdbfe2671f248903055afaa8ca#code
    # token.contract_name == 'InitializableImmutableAdminUpgradeabilityProxy'
    proxy_address = Address(
        context.web3.eth.get_storage_at(token.address, SLOT_EIP1967))
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
            logger.info(
                f'Unable to retrieve proxy implementation for {address}')
        return None
    return token


def get_eip1967_proxy_err(context, logger, address, verbose):
    res = get_eip1967_proxy(context, logger, address, verbose)
    if res is None:
        raise ModelInputError(
            f'Unable to retrieve proxy implementation for {address}')
    return res


def get_eip1967_proxy_err_with_abi(context, logger, address, verbose, proxy_abi, implementation_abi):
    proxy_contract = get_eip1967_proxy_err(context, logger, address, verbose)
    assert proxy_contract.proxy_for
    proxy_contract.set_abi(proxy_abi, set_loaded=True)
    # pylint: disable = protected-access
    proxy_contract._meta.proxy_implementation = (Contract(proxy_contract.proxy_for.address)
                                                 .set_abi(implementation_abi, set_loaded=True))
    return proxy_contract


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

    def get_underlying_proxy(self, input: Token):
        try:
            _ = input.abi
        except Exception:
            return None

        # pylint: disable=too-many-return-statements)
        try_eip1967 = get_eip1967_proxy(
            self.context, self.logger, input.address, False)
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

        return None

    address_to_symbol = {
        int(Network.Mainnet): {
            # TODO: iearn DAI
            Address('0xc2cb1040220768554cf699b0d863a3cd4324ce32'): 'DAI',
            Address('0x16de59092dae5ccf4a1e6439d611fd0653f0bd01'): 'DAI',
            # TODO: iearn USDC
            Address('0x26ea744e5b887e5205727f55dfbe8685e3b21951'): 'USDC',
            Address('0xd6ad7a6750a7593e092a9b218d66c0a814a3436e'): 'USDC',
            Address('0xe6354ed5bc4b393a5aad09f21c46e101e692d447'): 'USDT',
            Address('0x83f798e925bcd4017eb265844fddabb448f1707d'): 'USDT',
            Address('0x73a052500105205d34daf004eab301916da8190f'): 'TUSD',
            Address('0x04bc0ab673d88ae9dbc9da2380cb6b79c4bca9ae'): 'BUSD',
            Address('0xbbc455cb4f1b9e4bfc4b73970d360c8f032efee6'): 'LINK',
            Address('0x0e2ec54fc0b509f445631bf4b91ab8168230c752'): 'LINK',
            # TODO: ycDAI
            Address('0x99d1fa417f94dcd62bfe781a1213c092a47041bc'): 'DAI',
            Address('0x9777d7e2b60bb01759d0e2f8be2095df444cb07e'): 'USDC',
            Address('0x1be5d71f2da660bfdee8012ddc58d024448a0a59'): 'USDT',
            # stkAAVE
            Address('0x4da27a545c0c5B758a6BA100e3a049001de870f5'): 'AAVE',
        }
    }

    def run(self, input: Token) -> Maybe[Address]:
        underlying_proxy = self.get_underlying_proxy(input)
        if underlying_proxy is not None:
            return underlying_proxy

        if input.address in self.address_to_symbol.get(self.context.chain_id, {}):
            token = Token(
                symbol=self.address_to_symbol[self.context.chain_id][input.address])
            return Maybe(just=token.address)

        return Maybe(just=None)


@Model.describe(slug="token.info",
                version="1.5",
                display_name="Token Information",
                developer="Credmark",
                category='protocol',
                tags=['token'],
                input=Token,
                output=Token)
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


class TokenDeploymentInput(Token):
    # Use Token as base class to accept symbol as input
    ignore_proxy: bool = DTOField(False, description='Ignore proxy')


class TokenDeploymentOutput(ImmutableOutput):
    deployed_block_number: BlockNumber = DTOField(
        description='Block number of deployment')
    deployed_block_timestamp: Optional[int] = DTOField(
        description='Timestamp of deployment')
    deployer: Optional[Address] = DTOField(description='Deployer address')
    proxy_deployer: Optional[dict] = DTOField(
        description='Proxy deployment')


@Model.describe(slug="token.deployment-maybe",
                version="0.12",
                display_name="Token Information - deployment",
                developer="Credmark",
                category='protocol',
                tags=['token'],
                input=TokenDeploymentInput,
                output=Maybe[TokenDeploymentOutput],
                cache=CachePolicy.SKIP)
class TokenInfoDeploymentMaybe(Model):
    def run(self, input: TokenDeploymentInput) -> Maybe[TokenDeploymentOutput]:
        try:
            res = self.context.run_model('token.deployment', input,
                                         return_type=TokenDeploymentOutput)
            return Maybe(just=res)
        except ModelDataError:
            return Maybe(just=None)


@ImmutableModel.describe(
    slug="token.deployment",
    version="0.12",
    display_name="Token Information - deployment",
    developer="Credmark",
    category='protocol',
    tags=['token'],
    input=TokenDeploymentInput,
    output=TokenDeploymentOutput)
class TokenInfoDeployment(ImmutableModel):
    """
    Return token's information on deployment
    """

    code_by_block = {}

    def binary_search(self, low: int, high: int, contract_address) -> int:
        # Check base case
        if high >= low:
            msg = f'[{self.slug}] Searching block {low}-{high} for {contract_address}'
            self.logger.info(msg)
            # print(msg)
            mid = (high + low)//2
            if high == low:
                return low

            mid_hex = hex(mid)
            if self.code_by_block.get(mid_hex) is None:
                try_get_code = self.context.web3.eth.get_code(contract_address, mid).hex()
                self.code_by_block[mid_hex] = try_get_code
            else:
                try_get_code = self.code_by_block[mid_hex]
            if try_get_code != '0x':
                return self.binary_search(low, mid, contract_address)
            elif try_get_code == '0x':
                return self.binary_search(mid+1, high, contract_address)
            else:
                return -1
        else:
            return -1

    def run(self, input: TokenDeploymentInput) -> TokenDeploymentOutput:
        self.code_by_block = {}

        if self.context.web3.eth.get_code(input.address.checksum).hex() == '0x':
            raise ModelDataError(
                f'{input.address} is not an EOA account on block {self.context.block_number}')

        res = self.binary_search(
            0, int(self.context.block_number), input.address.checksum)

        if res == -1:
            raise ModelDataError(
                f'Can not find deployment information for {input.address}')

        block = self.context.web3.eth.get_block(res)
        txs = block['transactions'] if 'transactions' in block else []
        deployer = None
        for tx in txs:
            receipt = self.context.web3.eth.get_transaction_receipt(
                tx.hex())  # type: ignore
            if receipt['contractAddress'] == input.address:
                deployer = receipt['from']
                break
            for log in receipt['logs']:
                if log['address'] == input.address:
                    deployer = receipt['from']
                    break

        # TODO: remove when we have loaded ABI for non-mainnet chains
        if self.context.chain_id == Network.Mainnet and not input.ignore_proxy:
            if input.proxy_for is not None:
                proxy_deployer = self.context.run_model(
                    self.slug, input.proxy_for)
                return TokenDeploymentOutput(
                    deployed_block_number=BlockNumber(res),
                    deployed_block_timestamp=block['timestamp'] if 'timestamp' in block else None,
                    deployer=Address(str(deployer)),
                    proxy_deployer=proxy_deployer,
                    firstResultBlockNumber=res,
                )

        return TokenDeploymentOutput(
            deployed_block_number=BlockNumber(res),
            deployed_block_timestamp=block['timestamp'] if 'timestamp' in block else None,
            deployer=Address(str(deployer)) if deployer is not None else None,
            proxy_deployer=None,
            firstResultBlockNumber=res)


class TokenLogoOutput(DTO):
    logo_url: str = DTOField(description="URL of token's logo")


@Model.describe(slug="token.logo",
                version="2.0",
                display_name="Token Logo",
                developer="Credmark",
                category='protocol',
                tags=['token'],
                cache=CachePolicy.IGNORE_BLOCK,
                input=Token,
                output=TokenLogoOutput
                )
class TokenLogoModel(Model):
    """
    Return token's logo
    """

    logos = {
        "trustwallet_assets": NetworkDict(str, {
            Network.Mainnet: "ethereum",
            Network.BSC: "binance",
            Network.Polygon: "polygon",
            Network.Optimism: "optimism",
            Network.ArbitrumOne: "arbitrum",
            Network.Avalanche: "avalanchec",
            Network.Fantom: "fantom"
        }),
        "uniswap_assets": NetworkDict(str, {
            Network.Mainnet: "ethereum",
            Network.BSC: "binance",
            Network.Polygon: "polygon",
            Network.Optimism: "optimism",
            Network.ArbitrumOne: "arbitrum",
            Network.Avalanche: "avalanchec",
            Network.Fantom: "fantom"
        }),
        "sushiswap_assets": NetworkDict(str, {
            Network.Mainnet: "ethereum",
            Network.BSC: "binance",
            Network.Polygon: "polygon",
            Network.Optimism: "optimism",
            Network.ArbitrumOne: "arbitrum",
            Network.Avalanche: "avalanche",
            Network.Fantom: "fantom"
        }),
        "sushiswap_logos": NetworkDict(str, {
            Network.Mainnet: "ethereum",
            Network.BSC: "binance",
            Network.Polygon: "polygon",
            Network.Optimism: "optimism",
            Network.ArbitrumOne: "arbitrum",
            Network.Avalanche: "avalanche",
            Network.Fantom: "fantom"
        }),
        "curve_assets": NetworkDict(str, {
            Network.Mainnet: "assets",
            Network.Polygon: "assets-polygon",
            Network.Optimism: "assets-optimism",
            Network.ArbitrumOne: "assets-arbitrum",
            Network.Avalanche: "assets-avalanche",
            Network.Fantom: "assets-fantom"
        })
    }

    def run(self, input: Token) -> TokenLogoOutput:
        network = self.context.network
        logos = self.logos

        try_urls = []
        # Handle native token
        if input.address == NativeToken().address:
            try_urls.append("https://raw.githubusercontent.com/trustwallet/assets/master"
                            f"/blockchains/{logos['trustwallet_assets'][network]}/info/logo.png")

        if self.context.network in logos['trustwallet_assets']:
            try_urls.append(("https://raw.githubusercontent.com/trustwallet/assets/master"
                             f"/blockchains/{logos['trustwallet_assets'][network]}"
                             f"/assets/{input.address.checksum}/logo.png"))

        if self.context.network in logos['uniswap_assets']:
            try_urls.append(("https://raw.githubusercontent.com/uniswap/assets/master"
                             f"/blockchains/{logos['uniswap_assets'][network]}"
                             f"/assets/{input.address.checksum}/logo.png"))

        if self.context.network in logos['sushiswap_logos']:
            try_urls.append(("https://raw.githubusercontent.com/sushiswap/list/master/logos/token-logos"
                             f"/network/{logos['sushiswap_logos'][network]}"
                             f"/{input.address.checksum}.jpg"))

        if self.context.network in logos['sushiswap_assets']:
            try_urls.append(("https://raw.githubusercontent.com/sushiswap/assets/master"
                             f"/blockchains/{logos['sushiswap_assets'][network]}"
                             f"/assets/{input.address.checksum}/logo.png"))

        if self.context.network in logos['curve_assets']:
            try_urls.append(("https://raw.githubusercontent.com/curvefi/curve-assets/main"
                             f"/images/{logos['curve_assets'][network]}"
                             f"/{input.address}.png"))

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
    account: Address = DTOField(description='Account address for which to fetch balance.')
    quote: Currency = DTOField(FiatCurrency(symbol='USD'),
                               description='Quote token address to count the value')

    class Config:
        schema_extra = {
            'example': {"address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                        "account": "0x55FE002aefF02F77364de339a1292923A15844B8"}
        }


class TokenBalanceOutput(DTO):
    balance: int = DTOField(description="Balance of account")
    balance_scaled: float = DTOField(
        description="Balance scaled to token decimals for account")
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


class TokenTransferInput(Token):
    limit: int = DTOField(100,
                          gt=0, description="Limit the number of transfers that are returned")
    offset: int = DTOField(0,
                           ge=0,
                           description="Omit a specified number of transfers from beginning of result set")


class TokenTransfer(DTO):
    transaction_hash: str
    log_index: int
    from_address: Address
    to_address: Address
    block_number: int
    block_timestamp: str
    amount: int
    amount_str: str
    amount_scaled: float
    usd_amount: float


class TokenTransferOutput(IterableListGenericDTO[TokenTransfer]):
    transfers: List[TokenTransfer] = DTOField(
        default=[], description='List of transfers')
    total_transfers: int = DTOField(description='Total number of transfers')

    _iterator: str = PrivateAttr('transfers')


@Model.describe(slug='token.transfers',
                version='1.3',
                display_name='Token Transfers',
                description='Transfers of a Token',
                category='protocol',
                tags=['token'],
                input=TokenTransferInput,
                output=TokenTransferOutput)
class TokenTransfers(Model):
    def run(self, input: TokenTransferInput) -> TokenTransferOutput:
        with self.context.ledger.TokenTransfer as q:
            rows = q.select(
                aggregates=[('COUNT(*) OVER()', 'total_transfers')],
                columns=[q.BLOCK_NUMBER,
                         q.BLOCK_TIMESTAMP,
                         q.FROM_ADDRESS,
                         q.TO_ADDRESS,
                         q.RAW_AMOUNT,
                         q.USD_AMOUNT,
                         q.TRANSACTION_HASH,
                         q.LOG_INDEX],
                where=q.TOKEN_ADDRESS.eq(input.address),
                order_by=q.BLOCK_NUMBER.desc(),
                limit=input.limit,
                offset=input.offset,
                analytics_mode=True,
            )

            total_transfers = 0
            if len(rows.data) > 0:
                total_transfers = rows[0]['total_transfers']

            return TokenTransferOutput(
                transfers=[TokenTransfer(
                    transaction_hash=row['transaction_hash'],
                    log_index=row['log_index'],
                    from_address=Address(row['from_address']),
                    to_address=Address(row['to_address']),
                    block_number=int(row['block_number']),
                    block_timestamp=row['block_timestamp'],
                    amount=math.floor(Decimal(row['raw_amount'])),
                    amount_str=str(math.floor(Decimal(row['raw_amount']))),
                    amount_scaled=input.scaled(math.floor(Decimal(row['raw_amount']))),
                    usd_amount=float(row['usd_amount']),
                ) for row in rows],
                total_transfers=total_transfers)


class TokenHolderInput(Token):
    limit: int = DTOField(100,
                          gt=0, description="Limit the number of holders that are returned")
    offset: int = DTOField(0,
                           ge=0,
                           description="Omit a specified number of holders from beginning of result set")
    order_by: str = DTOField("balance", description="Sort by balance or newest")
    quote: Currency = DTOField(FiatCurrency(symbol='USD'),
                               description='Quote token address to count the value')
    min_amount: int = DTOField(
        -1, description='Minimum balance for a holder to be included. Default is -1, a minimum \
            balance greater than 0')
    max_amount: int = DTOField(
        -1, description='Maximum balance for a holder to be included. Default is -1, no maximum')


class TokenHolder(DTO):
    class Block(DTO):
        block_number: int
        timestamp: str

    address: Address = DTOField(description="Address of holder")
    balance: int = DTOField(description="Balance of account")
    balance_scaled: float = DTOField(
        description="Balance scaled to token decimals for account")
    value: float = DTOField(description="Balance in terms of quoted currency")
    first_transfer_block: Block
    last_transfer_block: Block


class TokenHoldersOutput(IterableListGenericDTO[TokenHolder]):
    price: PriceWithQuote = DTOField(description="Token price")
    holders: List[TokenHolder] = DTOField(
        default=[], description='List of holders')
    total_holders: int = DTOField(description='Total number of holders')

    _iterator: str = PrivateAttr('holders')


@Model.describe(slug='token.holders',
                version='1.5',
                display_name='Token Holders',
                description='Holders of a Token',
                category='protocol',
                tags=['token'],
                input=TokenHolderInput,
                output=TokenHoldersOutput)
class TokenHolders(Model):
    def run(self, input: TokenHolderInput) -> TokenHoldersOutput:
        with self.context.ledger.TokenBalance as q:
            if input.order_by == 'newest':
                order_by = q.field('first_block_number').dquote().desc()
            else:
                order_by = q.field('balance').dquote().desc()

            having = q.AMOUNT.as_numeric().sum_().gt(0) if input.min_amount == - \
                1 else q.AMOUNT.as_numeric().sum_().ge(input.min_amount)

            if input.max_amount != -1:
                having = having.and_(q.AMOUNT.as_numeric().sum_().le(input.max_amount))

            df = q.select(
                aggregates=[(q.AMOUNT.as_numeric().sum_(), 'balance'),
                            (q.BLOCK_NUMBER.min_(), 'first_block_number'),
                            (q.BLOCK_TIMESTAMP.min_(), 'first_block_timestamp'),
                            (q.BLOCK_NUMBER.max_(), 'last_block_number'),
                            (q.BLOCK_TIMESTAMP.max_(), 'last_block_timestamp'),
                            ('COUNT(*) OVER()', 'total_holders')],
                where=q.TOKEN_ADDRESS.eq(input.address),
                group_by=[q.ADDRESS],
                having=having,
                order_by=order_by.comma_(q.ADDRESS),
                limit=input.limit,
                offset=input.offset,
                bigint_cols=['balance', 'total_holders'],
                analytics_mode=True,
            ).to_dataframe()

            token_price_maybe = Maybe[PriceWithQuote](**self.context.models.price.quote_maybe({
                'base': input,
                'quote': input.quote}))
            token_price = token_price_maybe.get_just(
                PriceWithQuote(price=0, src='', quoteAddress=input.quote.address))

            total_holders = df['total_holders'].values[0]
            if total_holders is None:
                total_holders = 0

            return TokenHoldersOutput(
                price=token_price,
                holders=[TokenHolder(
                    address=Address(row['address']),
                    balance=row['balance'],
                    balance_scaled=input.scaled(row['balance']),
                    value=token_price.price * input.scaled(row['balance']),
                    first_transfer_block=TokenHolder.Block(
                        block_number=row['first_block_number'], timestamp=row['first_block_timestamp']),
                    last_transfer_block=TokenHolder.Block(
                        block_number=row['last_block_number'], timestamp=row['last_block_timestamp']),
                )for _, row in df.iterrows()],
                total_holders=total_holders)


class TokenHoldersCountOutput(DTO):
    count: int = DTOField(description='Total number of holders')


@Model.describe(slug='token.holders-count',
                version='1.1',
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
                aggregates=[(q.AMOUNT.as_numeric().sum_(), 'balance'),
                            ('COUNT(*) OVER()', 'total_holders')],
                where=q.TOKEN_ADDRESS.eq(input.address),
                group_by=[q.ADDRESS],
                order_by=q.AMOUNT.as_numeric().sum_().desc(),
                having=q.AMOUNT.as_numeric().sum_().gt(0)
            ).to_dataframe()

            if df.empty:
                total_holders = 0
            else:
                total_holders = df['total_holders'].values[0]
                if total_holders is None:
                    total_holders = 0

            return TokenHoldersCountOutput(count=total_holders)


@Model.describe(slug='token.holders-all',
                version='0.4',
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
                          having=q.AMOUNT.as_numeric().sum_().gt(0)
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
        response = Contracts.empty()
        response.contracts.extend(
            Contracts(**self.context.models.uniswap_v3.get_pools(input)))
        response.contracts.extend(
            Contracts(**self.context.models.uniswap_v2.get_pools(input)))
        response.contracts.extend(
            Contracts(**self.context.models.sushiswap.get_pools(input)))
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

    class Config:
        schema_extra = {
            'example': {
                "categories": [
                    {"accounts": {"accounts": [{"address": "0x1F98431c8aD98523631AE4a59f267346ea31F984"}]},
                     "categoryName": "",
                     "categoryType": "",
                     "circulating": True}],
                "token": {"symbol": "DAI"}}
        }


class CategorizedSupplyResponse(CategorizedSupplyRequest):
    class CategorizedSupplyCategory(CategorizedSupplyRequest.CategorizedSupplyCategory):
        amountScaled: float = 0.0
        valueUsd: float = 0.0
    categories: List[CategorizedSupplyCategory]
    _iterator: str = 'categories'
    totalSupplyScaled: float = 0.0
    totalSupplyUsd: float = 0.0
    circulatingSupplyScaled: float = 0.0
    circulatingSupplyUsd: float = 0.0


@Model.describe(slug='token.categorized-supply',
                version='1.3',
                display_name='Token Categorized Supply',
                description='The categorized supply for a token',
                category='protocol',
                tags=['token'],
                input=CategorizedSupplyRequest,
                output=CategorizedSupplyResponse)
class TokenCirculatingSupply(Model):
    def run(self, input: CategorizedSupplyRequest) -> CategorizedSupplyResponse:
        response = CategorizedSupplyResponse(**input.dict())
        response.totalSupplyScaled = input.token.scaled(input.token.total_supply)
        token_price = PriceWithQuote(
            **self.context.models.price.quote({'base': input.token}))
        if token_price is None:
            raise ModelRunError(f"No Price for {response.token}")
        for c in response.categories:
            for account in c.accounts:
                bal = response.token.functions.balanceOf(
                    account.address).call()
                c.amountScaled += response.token.scaled(bal)
            if token_price is not None and token_price.price is not None:
                c.valueUsd = c.amountScaled * token_price.price
        response.categories.append(CategorizedSupplyResponse.CategorizedSupplyCategory(
            accounts=Accounts(accounts=[]),
            categoryName='uncategorized',
            categoryType='uncategorized',
            circulating=True,
            amountScaled=response.totalSupplyScaled -
            sum(c.amountScaled for c in response.categories)
        ))
        response.circulatingSupplyScaled = sum(
            c.amountScaled for c in response.categories if c.circulating)

        if isinstance(token_price.price, float):
            if isinstance(response.totalSupplyScaled, float):
                response.totalSupplyUsd = response.totalSupplyScaled * token_price.price
            if isinstance(response.circulatingSupplyScaled, float):
                response.circulatingSupplyUsd = response.circulatingSupplyScaled * token_price.price
        return response


class TokenAllInput(DTO):
    limit: int = DTOField(gt=0, description='Number of tokens per page', default=5000)
    page: int = DTOField(description='Page number', default=1, gt=0)

    class Config:
        schema_extra = {
            'example': {'limit': 10, 'page': 2}
        }


class TokenAllOutput(TokenAllInput):
    total: int = DTOField(description='Total number of tokens')
    result: Some[Token] = DTOField(description='List of token addresses')


@Model.describe(slug='token.all',
                version='0.3',
                display_name='All tokens',
                description='Return all tokens by page',
                category='protocol',
                tags=['token'],
                input=TokenAllInput,
                output=TokenAllOutput)
class TokenAll(Model):
    def run(self, input: TokenAllInput) -> TokenAllOutput:
        with self.context.ledger.Token as token:
            rows = token.select(aggregates=[(token.ADDRESS.count_(), 'count_token_address')],
                                bigint_cols=['count_token_address'])
            count_token_address = int(rows[0]['count_token_address'])

            df = token.select([token.ADDRESS],
                              where=token.BLOCK_NUMBER.le(self.context.block_number),
                              order_by=token.ADDRESS,
                              limit=input.limit,
                              offset=(input.page-1)*input.limit).to_dataframe()

        return TokenAllOutput(total=count_token_address,
                              limit=input.limit,
                              page=input.page,
                              result=Some[Token](some=df.address.to_list()))
