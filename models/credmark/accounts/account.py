# pylint: disable=too-many-function-args, line-too-long

import functools
import math
from enum import Enum

import numpy as np
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (
    Account,
    Accounts,
    BlockNumber,
    Currency,
    FiatCurrency,
    Maybe,
    NativePosition,
    NativeToken,
    Portfolio,
    PortfolioWithPrice,
    Position,
    PositionWithPrice,
    PriceWithQuote,
    Records,
    Some,
    Token,
    TokenPosition,
)
from credmark.cmf.types.compose import MapBlockTimeSeriesOutput
from credmark.dto import DTOField, EmptyInput, cross_examples
from web3.exceptions import ContractLogicError

from models.credmark.accounts.token_return import TokenReturnOutput, token_return
from models.credmark.ledger.transfers import get_native_transfer, get_token_transfer
from models.dtos.historical import HistoricalDTO

np.seterr(all='raise')


# TODO
# Transaction Gas is from receipts per transaction. GAS_USED * EFFECTIVE_GAS_PRICE
# Not full transaction (missing Ether transfers), can be found in TRACES (but lack of context),


# pylint:disable=invalid-name
class TokenListChoice(str, Enum):
    CMF = 'cmf'
    ALL = 'all'


class AccountReturnInput(Account):
    token_list: TokenListChoice = DTOField(
        TokenListChoice.CMF,
        description='Value all tokens or those from token.list, choices: [all, cmf].')

    class Config:
        use_enum_values = True
        schema_extra = {
            'examples': [{'address': '0x388C818CA8B9251b393131C08a736A67ccB19297',
                          'token_list': 'cmf'}]
        }


@Model.describe(slug='account.token-return',
                version='0.6',
                display_name='Account\'s ERC20 Token Return',
                description='Account\'s ERC20 Token Return',
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['token'],
                input=AccountReturnInput,
                output=TokenReturnOutput)
class AccountERC20TokenReturn(Model):
    def run(self, input: AccountReturnInput) -> TokenReturnOutput:
        return self.context.run_model('accounts.token-return',
                                      input=AccountsReturnInput(
                                          # type: ignore
                                          accounts=[Account(input.address)],
                                          token_list=input.token_list).dict(),
                                      return_type=TokenReturnOutput)


class AccountsReturnInput(Accounts):
    token_list: TokenListChoice = DTOField(
        TokenListChoice.CMF,
        description='Value all tokens or those from token.list, choices: [all, cmf].')

    class Config:
        use_enum_values = True
        schema_extra = {
            'examples': [{'accounts': ['0x388C818CA8B9251b393131C08a736A67ccB19297',
                                       '0xf9cbBA7BF1b10E045691dDECa48182dB213E8F8B'],
                          'token_list': 'cmf'}]
        }

# create_instance_from_error_dict(result.error.dict())


@Model.describe(slug='accounts.token-return',
                version='0.9',
                display_name='Accounts\' Token Return',
                description='Accounts\' Token Return',
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['token'],
                input=AccountsReturnInput,
                output=TokenReturnOutput)
class AccountsTokenReturn(Model):
    def run(self, input: AccountsReturnInput) -> TokenReturnOutput:
        native_token = NativeToken()
        native_amount = 0
        for account in input:
            native_amount += native_token.balance_of_scaled(
                account.address.checksum)

        # TODO: native token transaction (incomplete) and gas spending
        _df_native = get_native_transfer(self.context, input.to_address())

        # ERC-20 transaction
        df_erc20 = get_token_transfer(self.context, input.to_address(), [], 0)

        # If we filter for one token address, use below
        # df_erc20 = df_erc20.query('token_address == "0x4e3fbd56cd56c3e72c1403e103b45db9da5b9d2b"')

        return token_return(self.context, self.logger, df_erc20, native_amount, input.token_list)


class AccountReturnHistoricalInput(AccountReturnInput, HistoricalDTO):
    ...


@Model.describe(slug='account.token-return-historical',
                version='0.1',
                display_name='Account\'s Token Return Historical',
                description='Account\'s  Token Return Historical',
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['token'],
                input=AccountReturnHistoricalInput,
                output=MapBlockTimeSeriesOutput[dict])
class AccountERC20TokenReturnHistorical(Model):
    def run(self, input: AccountReturnHistoricalInput) -> MapBlockTimeSeriesOutput[dict]:
        return self.context.run_model(
            'accounts.token-return-historical',
            input=AccountsReturnHistoricalInput(
                **input.to_accounts().dict(),
                token_list=input.token_list,
                window=input.window,
                interval=input.interval,
                exclusive=input.exclusive
            ).dict(),
            return_type=MapBlockTimeSeriesOutput[dict])


class AccountsReturnHistoricalInput(AccountsReturnInput, HistoricalDTO):
    class Config:
        schema_extra = {
            'examples': cross_examples(AccountsReturnInput.Config.schema_extra['examples'],
                                       HistoricalDTO.Config.schema_extra['examples'],
                                       limit=10)
        }


# TODO: NFT
@Model.describe(slug='accounts.token-return-historical',
                version='0.8',
                display_name='Accounts\' Token Return Historical',
                description='Accounts\' ERC20 Token Return',
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['token'],
                input=AccountsReturnHistoricalInput,
                output=MapBlockTimeSeriesOutput[dict])
class AccountsTokenReturnHistorical(Model):
    def run(self, input: AccountsReturnHistoricalInput) -> MapBlockTimeSeriesOutput[dict]:
        window_in_seconds = self.context.historical.to_seconds(input.window)
        interval_in_seconds = self.context.historical.to_seconds(
            input.interval)
        count = int(window_in_seconds / interval_in_seconds)

        price_historical_result = self.context.run_model(
            slug='compose.map-block-time-series',
            input={"modelSlug": 'historical.empty',
                   "modelInput": {},
                   "endTimestamp": self.context.block_number.timestamp,
                   "interval": interval_in_seconds,
                   "count": count,
                   "exclusive": input.exclusive},
            return_type=MapBlockTimeSeriesOutput[dict])

        df_historical = price_historical_result.to_dataframe()

        _native_token = NativeToken()

        # TODO: native token transaction (incomplete) and gas spending
        _df_native = get_native_transfer(self.context, input.to_address())

        # ERC-20 transaction
        df_ts = get_token_transfer(self.context, input.to_address(), [], 0)

        if input.token_list == TokenListChoice.CMF:
            token_list = (self.context.run_model('token.list',
                                                 input=EmptyInput(),
                                                 return_type=Records,
                                                 block_number=0).to_dataframe()
                          ['address'].str.lower()
                          .values)
        else:
            token_list = None

        for n_historical, row in df_historical.iterrows():
            _past_block_number = row['blockNumber']
            assets = []
            _native_token_bal = (_df_native
                                 .query('(block_number <= @_past_block_number)')
                                 .groupby('token_address', as_index=False)['value']
                                 .sum())

            # TODO: disabled
            # if not _native_token_bal.empty:
            #     assets.append(
            #         Position(amount=native_token.scaled(_native_token_bal['value'][0]),
            #                  asset=_native_token))

            if token_list is not None:
                token_bal = (df_ts
                             .query(('(block_number <= @_past_block_number) & '
                                     '(token_address.isin(@token_list))'))
                             .groupby('token_address', as_index=False)['value']
                             .sum())
            else:
                token_bal = (df_ts
                             .query('(block_number <= @_past_block_number)')
                             .groupby('token_address', as_index=False)['value']
                             .sum())

            # Fetch many tokens' prices on one past block
            def _use_model(_assets, _token_bal, _past_block_number):
                non_zero_bal_tokens_dict = {token_bal_row['token_address']: token_bal_row['value']
                                            for _, token_bal_row in _token_bal.iterrows()
                                            if not math.isclose(token_bal_row['value'], 0)}
                non_zero_bal_tokens_addrs = list(
                    non_zero_bal_tokens_dict.keys())

                pqs_maybe = self.context.run_model(
                    slug='price.quote-multiple-maybe',
                    input=Some(some=[{'base': addr}
                               for addr in non_zero_bal_tokens_addrs]),
                    return_type=Some[Maybe[PriceWithQuote]],
                    block_number=_past_block_number
                )

                for p_maybe, (token_addr, token_value) in \
                        zip(pqs_maybe, non_zero_bal_tokens_dict.items()):
                    asset_token = Token(token_addr).as_erc20(set_loaded=True)
                    if p_maybe.just is None:
                        continue
                    try:
                        _assets.append(
                            Position(amount=asset_token.scaled(token_value),
                                     asset=asset_token))
                    except (ModelDataError, ContractLogicError):
                        # NFT: ContractLogicError
                        continue

            # Loop over every token and get its price on the past block.
            def _use_for(_assets, _token_bal, _past_block_number):
                for _, token_bal_row in _token_bal.iterrows():
                    if not math.isclose(token_bal_row['value'], 0):
                        asset_token = Token(
                            token_bal_row['token_address']).as_erc20(set_loaded=True)
                        try_price = self.context.run_model('price.quote-maybe',
                                                           input={
                                                               'base': asset_token},
                                                           block_number=_past_block_number)
                        if try_price['just'] is None:
                            continue

                        try:
                            _assets.append(
                                Position(amount=asset_token.scaled(token_bal_row['value']),
                                         asset=asset_token))
                        except (ModelDataError, ContractLogicError):
                            # NFT: ContractLogicError
                            continue

            _use_model(assets, token_bal, _past_block_number)

            price_historical_result[n_historical].output = (
                {"value": Portfolio(positions=assets)
                 .get_value(block_number=_past_block_number)})

        return price_historical_result


class AccountHistoricalInput(Account, HistoricalDTO):
    include_price: bool = DTOField(
        default=True, description='Include price quote')

    class Config:
        schema_extra = {
            'examples': cross_examples(
                [{'address': '0x388c818ca8b9251b393131c08a736a67ccb19297'},
                 {'address': '0x388c818ca8b9251b393131c08a736a67ccb19297',
                  'include_price': False}],
                HistoricalDTO.Config.schema_extra['examples'],
                limit=10)}


@Model.describe(slug='account.token-historical',
                version='0.5',
                display_name='Account\'s Token Holding Historical',
                description='Account\'s Token Holding Historical',
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['token'],
                input=AccountHistoricalInput,
                output=dict)
class AccountERC20TokenHistorical(Model):
    def run(self, input: AccountHistoricalInput) -> dict:
        return self.context.run_model(
            'accounts.token-historical',
            AccountsHistoricalInput(
                **input.to_accounts().dict(),   # type: ignore
                window=input.window,
                interval=input.interval,
                exclusive=input.exclusive,
                include_price=input.include_price))


class AccountsHistoricalInput(Accounts, HistoricalDTO):
    include_price: bool = DTOField(
        default=True, description='Include price quote')
    quote: Currency = DTOField(default=Currency(symbol='USD'), description='')

    class Config:
        schema_extra = {
            'examples': cross_examples(
                Accounts.Config.schema_extra['examples'],
                HistoricalDTO.Config.schema_extra['examples'],
                [{'address': '0x388c818ca8b9251b393131c08a736a67ccb19297'},
                 {'address': '0x388c818ca8b9251b393131c08a736a67ccb19297',
                 'include_price': False}]),
        }


@Model.describe(slug='accounts.token-historical',
                version='0.11',
                display_name='Accounts\' Token Holding Historical',
                description='Accounts\' Token Holding Historical',
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['token'],
                input=AccountsHistoricalInput,
                output=dict)
class AccountsERC20TokenHistorical(Model):
    def account_token_historical(self, input, do_wobble_price):
        _include_price = input.include_price

        self.logger.info(
            f'[{self.slug}] fetching `accounts.token-historical-balance`')
        balance_result = self.context.run_model(
            'accounts.token-historical-balance', input)

        historical_blocks = balance_result['historical_blocks']
        token_blocks = balance_result['token_blocks']
        token_rows = balance_result['token_rows']

        price_historical_result = MapBlockTimeSeriesOutput[dict](
            **balance_result)

        if _include_price:
            all_blocks = list(functools.reduce(lambda a, b: a | set(b),
                                               token_blocks.values(),
                                               set()))
            all_tokens = list(token_blocks.keys())

            all_prices = []
            len_list = len(all_tokens)
            chunk_size = int(10 * 7 / len(all_blocks))
            range_start = 0
            for i in range(0, len_list, chunk_size):
                rr = (range_start + i, min(len_list, range_start + i + chunk_size))
                self.logger.info('Fetching `price.dex-db-blocks-tokens` '
                                 f'{rr[1]-rr[0]}*{len(all_blocks)}={(rr[1]-rr[0])*len(all_blocks)} '
                                 f'for {i} in total {len_list}')
                all_prices += (self.context.run_model(
                    'price.dex-db-blocks-tokens',
                    input={'addresses': all_tokens[rr[0]:rr[1]], 'blocks': all_blocks})
                    ['results'])

            if len(all_prices) != len(all_tokens):
                raise ModelRunError(
                    'Prices results length is different from input list of tokens')

            all_prices_dict = {d['address']: d['results'] for d in all_prices}

            if input.quote.address != FiatCurrency(symbol='USD').address:
                quotes = (self.context.run_model(
                    'price.dex-db-blocks',
                    input={'address': input.quote.address, 'blocks': all_blocks})
                    ['results'])
                quotes = {q['blockNumber']: q['price'] for q in quotes}
            else:
                quotes = None

            for token_addr, past_blocks in token_blocks.items():
                # pylint: disable=pointless-string-statement
                """
                # Use per-token-many-blocks model

                prices = (self.context.run_model(
                    'price.dex-db-blocks',
                    input={'address': token_addr, 'blocks': list(past_blocks)})
                    ['results'])

                if len(prices) == 0 and len(past_blocks) != 1:
                    continue
                """

                prices = all_prices_dict.get(token_addr)
                if prices is None or len(prices) == 0:
                    continue

                prices = [p for p in prices if p['blockNumber'] in past_blocks]

                if quotes is not None:
                    for p_idx, _ in enumerate(prices):
                        prices[p_idx]['price'] /= quotes[prices[p_idx]
                                                         ['blockNumber']]

                if len(prices) < len(past_blocks):
                    if not do_wobble_price:
                        continue

                    try:
                        last_price = self.context.run_model(
                            'price.dex-db-latest', input={'address': token_addr})
                        if input.quote.address != FiatCurrency(symbol='USD').address:
                            last_quote = self.context.run_model(
                                'price.dex-db-latest', input={'address': input.quote.address})
                            last_price['price'] /= last_quote['price']

                    except ModelDataError as err:
                        if "No price for" in err.data.message:  # pylint:disable=unsupported-membership-test
                            continue
                        raise

                    last_price_block = last_price['blockNumber']
                    # TODO: temporary fix to price not catching up with the latest
                    blocks_in_prices = set(p['blockNumber'] for p in prices)
                    for blk_n, blk in enumerate(past_blocks):
                        if blk not in blocks_in_prices:
                            # 7200 blocks = 1440 minutes = 24 hr = 1 day
                            self.logger.info(
                                f'[{self.slug}] make up last price')
                            blk_diff = blk - last_price_block
                            if 0 < blk_diff < 7200:
                                self.logger.info(
                                    f'Use last price for {token_addr} for '
                                    f'{blk} close to {last_price_block} ({blk_diff=})')
                                prices.insert(blk_n, last_price)
                            else:
                                self.logger.info(
                                    f'Not use last price for {token_addr} '
                                    f'for {blk} far to {last_price_block} ({blk_diff=})')
                                try:
                                    new_price = self.context.run_model(
                                        'price.quote',
                                        input={
                                            'base': token_addr,
                                            'quote': input.quote.address,
                                            'prefer': 'cex'},
                                        block_number=blk)  # type: ignore
                                except ModelRunError:
                                    continue
                                prices.insert(blk_n, new_price)

                # pylint:disable=line-too-long
                for past_block, price in zip(past_blocks, prices):
                    (price_historical_result[historical_blocks[str(past_block)]]  # type: ignore
                        # type: ignore
                        .output['positions'][token_rows[token_addr][str(past_block)]]
                        ['fiat_quote']) = PriceWithQuote(
                            price=price['price'],
                            src='dex',
                            quoteAddress=input.quote.address).dict()

        res = price_historical_result.dict()
        for n in range(len(res['results'])):
            res['results'][n]['blockTimestamp'] = BlockNumber(  # type: ignore
                res['results'][n]['blockNumber']).timestamp  # type: ignore

        return res

    def run(self, input: AccountsHistoricalInput) -> dict:
        return self.account_token_historical(input, True)


@Model.describe(slug='accounts.token-historical-balance',
                version='0.2',
                display_name='Accounts\' Token Holding Historical',
                description='Accounts\' Token Holding Historical',
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['token'],
                input=AccountsHistoricalInput,
                output=dict)
class AccountsERC20TokenHistoricalBalance(Model):
    def run(self, input: AccountsHistoricalInput) -> dict:
        self.logger.info(f'[{self.slug}] Fetching native token transfer')
        _include_price = input.include_price

        _native_token = NativeToken()

        # TODO: native token transaction (incomplete) and gas spending
        _df_native = get_native_transfer(self.context, input.to_address())

        self.logger.info(f'[{self.slug}] Fetching ERC20 token transfer')
        # ERC-20 transaction
        df_erc20 = get_token_transfer(self.context, input.to_address(), [], 0)

        window_in_seconds = self.context.historical.to_seconds(input.window)
        interval_in_seconds = self.context.historical.to_seconds(
            input.interval)
        count = int(window_in_seconds / interval_in_seconds)

        price_historical_result = self.context.run_model(
            slug='compose.map-block-time-series',
            input={"modelSlug": 'historical.empty',
                   "modelInput": {},
                   "endTimestamp": self.context.block_number.timestamp,
                   "interval": interval_in_seconds,
                   "count": count,
                   "exclusive": input.exclusive},
            return_type=MapBlockTimeSeriesOutput[dict])

        df_historical = price_historical_result.to_dataframe()

        historical_blocks = {}
        token_blocks = {}
        token_rows = {}
        all_tokens = {}

        self.logger.info(f'[{self.slug}] Producing account portfolio')
        for n_historical, row in df_historical.iterrows():
            past_block_number = int(row['blockNumber'])  # type: ignore
            assets = []
            _native_token_bal = (_df_native
                                 .query('(block_number <= @past_block_number)')
                                 .groupby('token_address', as_index=False)['value']
                                 .sum())

            # TODO
            # if not _native_token_bal.empty:
            #    assets.append(
            #        Position(amount=_native_token.scaled(native_token_bal['value'][0]),
            #                 asset=_native_token))

            token_bal = (df_erc20
                         .query('(block_number <= @past_block_number)')
                         .groupby('token_address', as_index=False)['value']
                         .sum()
                         .reset_index(drop=True))  # type: ignore

            historical_blocks[past_block_number] = n_historical
            n_skip = 0
            for n_row, token_bal_row in token_bal.iterrows():
                if not math.isclose(token_bal_row['value'], 0):
                    token_bal_addr = token_bal_row['token_address']
                    if all_tokens.get(token_bal_addr) is None:
                        all_tokens[token_bal_addr] = Token(
                            token_bal_addr).as_erc20(set_loaded=True)
                    try:
                        if _include_price:
                            assets.append(
                                PositionWithPrice(
                                    amount=all_tokens[token_bal_addr].scaled(
                                        token_bal_row['value']),
                                    asset=all_tokens[token_bal_addr],
                                    fiat_quote=PriceWithQuote(
                                        price=0.0,
                                        quoteAddress=input.quote.address,
                                        src='')))
                        else:
                            assets.append(
                                Position(
                                    amount=all_tokens[token_bal_addr].scaled(
                                        token_bal_row['value']),
                                    asset=all_tokens[token_bal_addr]))

                        if token_rows.get(token_bal_addr) is None:
                            token_blocks[token_bal_addr] = set(
                                [past_block_number])
                            token_rows[token_bal_addr] = {
                                past_block_number: n_row - n_skip}
                        else:
                            token_blocks[token_bal_addr].add(past_block_number)
                            token_rows[token_bal_addr][past_block_number] = n_row - n_skip

                    except (ModelDataError, ContractLogicError):
                        # NFT: ContractLogicError
                        n_skip += 1
                        continue
                else:
                    n_skip += 1

            if _include_price:
                price_historical_result[n_historical].output = \
                    PortfolioWithPrice(positions=assets)  # type: ignore
            else:
                price_historical_result[n_historical].output = \
                    Portfolio(positions=assets)  # type: ignore

        return price_historical_result.dict() | \
            {'token_blocks': token_blocks,
             'historical_blocks': historical_blocks,
             'token_rows': token_rows}


@Model.describe(slug="account.portfolio",
                version="0.3",
                display_name="Account\'s Token Holding as a Portfolio",
                description="All of the token holdings for an account",
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['portfolio'],
                input=Account,
                output=Portfolio)
class AccountPortfolio(Model):
    def run(self, input: Account) -> Portfolio:
        return self.context.run_model(
            'accounts.portfolio',
            input=input.to_accounts().dict(),
            return_type=Portfolio)


@Model.describe(slug="accounts.portfolio",
                version="0.6",
                display_name="Accounts\' Token Holding as a Portfolio",
                description="All of the token holdings for a list of accounts",
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['portfolio'],
                input=Accounts,
                output=Portfolio)
class AccountsPortfolio(Model):
    def run(self, input: Accounts) -> Portfolio:
        positions = []
        native_token = NativeToken()
        native_amount = 0
        for acc in input.accounts:
            native_amount += native_token.balance_of(acc.address.checksum)

        if not math.isclose(native_amount, 0):
            positions.append(
                NativePosition(
                    amount=native_token.scaled(native_amount),
                    asset=NativeToken()))

        token_addresses = (get_token_transfer(self.context, input.to_address(), [], 0)
                           ['token_address']
                           .drop_duplicates()
                           .to_list())

        for t in token_addresses:
            try:
                token = Token(address=t)
                balance = 0
                for acc in input.accounts:
                    balance += token.scaled(
                        token.functions.balanceOf(acc.address.checksum).call())
                if not math.isclose(balance, 0):
                    positions.append(
                        TokenPosition(asset=token, amount=balance))
            except Exception:
                # TODO: currently skip NFTs
                pass

        curve_lp_position = self.context.run_model(
            'curve.lp-accounts',
            input=input)

        # positions.extend([CurveLPPosition(**p) for p in curve_lp_position['positions']])
        positions.extend(curve_lp_position['positions'])

        return Portfolio(positions=positions)
