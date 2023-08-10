# pylint: disable=too-many-function-args, line-too-long

import functools
import math
from enum import Enum
from typing import List

import numpy as np
import pandas as pd
from credmark.cmf.model import CachePolicy, Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (
    Account,
    Accounts,
    BlockNumber,
    Currency,
    FiatCurrency,
    Maybe,
    NativeToken,
    Network,
    Portfolio,
    Position,
    PriceWithQuote,
    Records,
    Some,
    Token,
)
from credmark.cmf.types.compose import MapBlockResult, MapBlocksOutput, MapBlockTimeSeriesOutput
from credmark.dto import DTO, DTOField, cross_examples
from web3.exceptions import ContractLogicError

from models.credmark.accounts.token_return import TokenReturnOutput, token_return
from models.credmark.ledger.transfers import get_native_transfer, get_token_transfer
from models.dtos.historical import HistoricalDTO

np.seterr(all='raise')


# HACK - token balance is derived from token transfers which are in turn decoded from
# logs. They are extracted from TokenTransfer(address,address,uint256) type event.
# If an ERC20 token does not emit this event, it will be missed when calculating balance.
# This is the reason ledger sometimes return negative balance for a token.
# If we find negative balance, we simply assume it to be 0.

# pylint:disable=invalid-name
class TokenListChoice(str, Enum):
    CMF = 'cmf'
    ALL = 'all'


class AccountReturnInput(Account):
    token_list: TokenListChoice = DTOField(
        TokenListChoice.CMF,
        description='Value all tokens or those from token.list, choices: [all, cmf].')
    quote: Currency = DTOField(FiatCurrency(symbol='USD'),
                               description='Currency of the returned price if included.')

    class Config:
        use_enum_values = True
        schema_extra = {
            'examples': [{'address': '0x388C818CA8B9251b393131C08a736A67ccB19297',
                          'token_list': 'cmf'}]
        }


@Model.describe(slug='account.token-return',
                version='0.7',
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
                                          accounts=[Account(input.address)],
                                          token_list=input.token_list,
                                          quote=input.quote),
                                      return_type=TokenReturnOutput)


class AccountsReturnInput(Accounts):
    token_list: TokenListChoice = DTOField(
        TokenListChoice.CMF,
        description='Value all tokens or those from token.list, choices: [all, cmf].')
    quote: Currency = DTOField(FiatCurrency(symbol='USD'),
                               description='Currency of the returned price if included.')

    class Config:
        use_enum_values = True
        schema_extra = {
            'examples': [{'accounts': ['0x388C818CA8B9251b393131C08a736A67ccB19297',
                                       '0xf9cbBA7BF1b10E045691dDECa48182dB213E8F8B'],
                          'token_list': 'cmf'}]
        }

# create_instance_from_error_dict(result.error.dict())


@Model.describe(slug='accounts.token-return',
                version='0.10',
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
        _native_amount = 0
        for account in input.accounts:
            _native_amount += native_token.balance_of_scaled(
                account.address.checksum)

        # Native transaction and gas_used for each transaction with account as a from_address
        # Internal transaction are counted from the difference between the tracking balance and the balance from web3 on the block
        df_native = get_native_transfer(self.context, input.to_address())
        if not df_native.empty:
            past_balances = []
            internal_tx = []
            current_balance = 0
            for _n, row in df_native.iterrows():
                current_balance = current_balance + row.value + row.gas_used
                past_block_number = row.block_number
                with self.context.fork(block_number=past_block_number) as past_context:
                    past_balances.append(
                        [past_context.web3.eth.get_balance(account.address.checksum)
                         for account in input.accounts])
                # When we detect a difference on the block, there was an internal transaction on the block.
                internal_tx.append(sum(past_balances[-1]) - current_balance)
                current_balance = sum(past_balances[-1])

            df_native.insert(df_native.shape[1], 'balance', [sum(x) for x in past_balances])
            df_native.insert(df_native.shape[1], 'internal_tx', internal_tx)
            df_native.rename(columns={'value': 'native_amount'}, inplace=True)
            df_native.insert(df_native.shape[1], 'value', df_native['native_amount'] +
                             df_native['gas_used'] + df_native['internal_tx'])
            df_native_comb = df_native.loc[:, ['block_number', 'log_index', 'to_address',
                                               'from_address', 'token_address', 'transaction_hash', 'value']]
        else:
            df_native_comb = pd.DataFrame(
                columns=['block_number', 'log_index', 'to_address', 'from_address', 'token_address', 'value'])

        # ERC-20 transaction
        df_erc20 = get_token_transfer(self.context, input.to_address(), [], 0)

        if df_erc20.empty:
            df_erc20 = pd.DataFrame(
                columns=['block_number', 'log_index', 'to_address', 'from_address', 'token_address', 'value'])

        df_comb = pd.concat([df_native_comb, df_erc20], ignore_index=True).reset_index(drop=True)

        # If we filter for one token address, use below
        # df_erc20 = df_erc20.query('token_address == "0x4e3fbd56cd56c3e72c1403e103b45db9da5b9d2b"')

        return token_return(self.context, self.logger, df_comb, input.token_list, input.quote)


class AccountReturnHistoricalInput(AccountReturnInput, HistoricalDTO):
    class Config:
        schema_extra = {
            'examples': cross_examples(AccountReturnInput.Config.schema_extra['examples'],
                                       HistoricalDTO.Config.schema_extra['examples'],
                                       limit=10)
        }


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
                version='0.10',
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
        interval_in_seconds = self.context.historical.to_seconds(input.interval)
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
            token_list = (self.context.run_model(
                'token.list', {}, return_type=Records)
                .to_dataframe()['address'].str.lower().values)
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
                                            if token_bal_row['value'] > 0 and not math.isclose(token_bal_row['value'], 0)}
                non_zero_bal_tokens_addrs = list(
                    non_zero_bal_tokens_dict.keys())

                pqs_maybe = self.context.run_model(
                    slug='price.quote-multiple-maybe',
                    input=Some(some=[{'base': addr}
                               for addr in non_zero_bal_tokens_addrs]),
                    block_number=_past_block_number,
                    return_type=Some[Maybe[PriceWithQuote]],
                )

                for p_maybe, (token_addr, token_value) in zip(pqs_maybe.some, non_zero_bal_tokens_dict.items()):
                    asset_token = Token(token_addr).as_erc20(set_loaded=True)
                    if p_maybe.just:
                        continue
                    try:
                        _assets.append(Position(amount=asset_token.scaled(token_value),
                                                asset=asset_token))
                    except (ModelDataError, ContractLogicError):
                        # NFT: ContractLogicError
                        continue

            # Loop over every token and get its price on the past block.
            def _use_for(_assets, _token_bal, _past_block_number):
                for _, token_bal_row in _token_bal.iterrows():
                    if token_bal_row['value'] > 0 and not math.isclose(token_bal_row['value'], 0):
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
                cache=CachePolicy.SKIP,
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
    include_price: bool = DTOField(default=True, description='Include price quote')
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
                version='0.14',
                display_name='Accounts\' Token Holding Historical',
                description='Accounts\' Token Holding Historical',
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['token'],
                cache=CachePolicy.SKIP,
                input=AccountsHistoricalInput,
                output=dict)
class AccountsERC20TokenHistorical(Model):
    def account_token_historical(self, input: AccountsHistoricalInput, do_wobble_price: bool):
        _include_price = input.include_price

        self.logger.info(f'[{self.slug}] fetching `accounts.token-historical-balance`')
        balance_result = self.context.run_model(
            'accounts.token-historical-balance', input)

        historical_blocks = balance_result['historical_blocks']
        token_blocks = balance_result['token_blocks']
        token_rows = balance_result['token_rows']

        price_historical_result = MapBlocksOutput[dict](
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
                if prices is None or len(prices) == 0 or len([p for p in prices if p['price'] is None]) > 0:
                    continue

                prices = [p for p in prices if p['blockNumber'] in past_blocks]

                if quotes is not None:
                    for p_idx, _ in enumerate(prices):
                        prices[p_idx]['price'] /= quotes[prices[p_idx]['blockNumber']]

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
                    if price['price'] is not None:
                        (price_historical_result[historical_blocks[str(past_block)]]  # type: ignore
                            # type: ignore
                            .output['positions'][token_rows[token_addr][str(past_block)]]
                            ['price_quote']) = PriceWithQuote(
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
                version='0.3',
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
        native_token = NativeToken()

        df_erc20 = get_token_transfer(self.context, input.to_address(), [], 0)

        results = []

        historical_blocks = {}
        token_blocks = {}
        token_rows = {}
        all_tokens = {}

        self.logger.info(f'[{self.slug}] Producing account portfolio')
        for n_historical, row in enumerate(input.get_blocks()):
            past_block_number = row.number
            results.append(MapBlockResult(blockNumber=BlockNumber.from_dict(row.dict()),
                                          output=None))
            assets = []
            native_amount = 0
            with self.context.fork(block_number=past_block_number):
                for acc in input.accounts:
                    native_amount += native_token.balance_of(acc.address.checksum)
            if not math.isclose(native_amount, 0):
                assets.append(Position(amount=native_token.scaled(native_amount),
                                       asset=native_token))

            token_bal = (df_erc20
                         .query('(block_number <= @past_block_number)')
                         .groupby('token_address', as_index=False)['value']
                         .sum()
                         .reset_index(drop=True))  # type: ignore

            historical_blocks[past_block_number] = n_historical
            n_skip = 0
            for n_row, token_bal_row in token_bal.iterrows():
                if token_bal_row['value'] < 0 or math.isclose(token_bal_row['value'], 0):
                    n_skip += 1
                    continue

                token_bal_addr = token_bal_row['token_address']
                if all_tokens.get(token_bal_addr) is None:
                    all_tokens[token_bal_addr] = Token(
                        token_bal_addr).as_erc20(set_loaded=True)
                try:
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

            results[n_historical].output = Portfolio(positions=assets)

        return {
            'results': results,
            'token_blocks': token_blocks,
            'historical_blocks': historical_blocks,
            'token_rows': token_rows}


class AccountWithPrice(Account):
    with_price: bool = DTOField(default=False, description='Include price in the output')
    include_curve_positions: bool = DTOField(True, description='Include curve fi positions')
    quote: Currency = DTOField(FiatCurrency(symbol='USD'),
                               description='Currency of the returned price if included.')

    def to_accounts(self):
        return AccountsWithPrice(accounts=[self.address],  # type: ignore
                                 with_price=self.with_price,
                                 include_curve_positions=self.include_curve_positions,
                                 quote=self.quote)


class AccountsWithPrice(Accounts):
    with_price: bool = DTOField(default=False, description='Include price in the output')
    include_curve_positions: bool = DTOField(True, description='Include curve fi positions')
    quote: Currency = DTOField(FiatCurrency(symbol='USD'),
                               description='Currency of the returned price if included.')


@Model.describe(slug="account.portfolio",
                version="0.4",
                display_name="Account\'s Token Holding as a Portfolio",
                description="All of the token holdings for an account",
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['portfolio'],
                input=AccountWithPrice,
                output=Portfolio)
class AccountPortfolio(Model):
    def run(self, input: AccountWithPrice) -> Portfolio:
        return self.context.run_model(
            'accounts.portfolio',
            input=input.to_accounts().dict(),
            return_type=Portfolio)


@Model.describe(slug="accounts.portfolio",
                version="0.7",
                display_name="Accounts\' Token Holding as a Portfolio",
                description="All of the token holdings for a list of accounts",
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['portfolio'],
                input=AccountsWithPrice,
                output=Portfolio)
class AccountsPortfolio(Model):
    def run(self, input: AccountsWithPrice) -> Portfolio:
        positions = []
        native_token = NativeToken()
        native_amount = 0
        for acc in input.accounts:
            native_amount += native_token.balance_of(acc.address.checksum)

        if not math.isclose(native_amount, 0):
            positions.append(
                Position(amount=native_token.scaled(native_amount),
                         asset=native_token))

        with self.context.ledger.TokenBalance as bal:
            token_balances = bal.select(
                aggregates=[
                    (f'{bal.TRANSACTION_VALUE.as_numeric().sum_()}', 'balance'),
                    (f'{bal.TOKEN_ADDRESS}', 'address'),
                ],
                having=bal.TRANSACTION_VALUE.as_numeric().sum_().gt(0),
                where=bal.ADDRESS.in_(input.to_address()),
                group_by=[bal.TOKEN_ADDRESS],
            )

        for token_balance in token_balances:
            try:
                token = Token(address=token_balance['address'])
                balance = token.scaled(int(token_balance['balance']))
                if balance > 0 and not math.isclose(balance, 0):
                    positions.append(Position(asset=token, amount=balance))
            except Exception:
                # TODO: currently skip NFTs
                self.logger.info(
                    f"Skipping {token_balance['address']} as it is not ERC20")

        if self.context.network is Network.Mainnet and input.include_curve_positions:
            curve_lp_position = self.context.run_model(
                'curve.lp-accounts',
                input=input)
            positions.extend(curve_lp_position['positions'])

        if not input.with_price:
            return Portfolio(positions=positions)

        pqs_maybe = self.context.run_model(
            slug='price.quote-multiple-maybe',
            input=Some(some=[
                {'base': p.asset.address, 'quote': input.quote} for p in positions
            ]),
            return_type=Some[Maybe[PriceWithQuote]],
        )

        price_positions = []
        for price_maybe, position in zip(pqs_maybe.some, positions):
            price_quote = price_maybe.get_just(PriceWithQuote(price=0.0, src="none",
                                                              quoteAddress=input.quote.address))
            price_positions.append(Position(amount=position.amount,
                                            asset=position.asset,
                                            price_quote=price_quote))

        return Portfolio(positions=price_positions)


class AccountPortfolioValueInput(Account):
    include_curve_positions: bool = DTOField(True, description='Include curve fi positions')
    quote: Currency = DTOField(FiatCurrency(symbol='USD'),
                               description='Currency of the returned price if included.')


class PortfolioValue(DTO):
    value: float = DTOField(description="Portfolio value in terms of quoted currency")


@Model.describe(slug="account.portfolio-value",
                version="0.1",
                display_name="Account\'s portfolio value",
                description="Cumulative value of token holdings of an account",
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['portfolio'],
                input=AccountPortfolioValueInput,
                output=PortfolioValue)
class AccountPortfolioValue(Model):
    def run(self, input: AccountPortfolioValueInput) -> PortfolioValue:
        return self.context.run_model(
            'accounts.portfolio-value',
            input=AccountsPortfolioValueInput(
                accounts=input.to_accounts().accounts,
                include_curve_positions=input.include_curve_positions,
                quote=input.quote,
            ),
            return_type=PortfolioValue)


class AccountsPortfolioValueInput(Accounts):
    include_curve_positions: bool = DTOField(True, description='Include curve fi positions')
    quote: Currency = DTOField(FiatCurrency(symbol='USD'),
                               description='Currency of the returned price if included.')


@Model.describe(slug="accounts.portfolio-value",
                version="0.1",
                display_name="Accounts\' portfolio value",
                description="Cumulative value of token holdings for a list of accounts",
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['portfolio'],
                input=AccountsPortfolioValueInput,
                output=PortfolioValue)
class AccountsPortfolioValue(Model):
    def run(self, input: AccountsPortfolioValueInput) -> PortfolioValue:
        portfolio = self.context.run_model(
            'accounts.portfolio',
            input=AccountsWithPrice(
                accounts=input.accounts,
                include_curve_positions=input.include_curve_positions,
                with_price=True,
                quote=input.quote,
            ),
            return_type=Portfolio)

        value = 0.0
        for position in portfolio:
            if position.price_quote is not None:
                value += position.price_quote.price * position.amount

        return PortfolioValue(value=value)


class AccountBalancesInput(Account):
    tokens: List[Token] = DTOField(default=[], description="A list of Tokens")
    include_price: bool = DTOField(default=False, description='Include price in the output')
    quote: Currency = DTOField(FiatCurrency(symbol='USD'),
                               description='Currency of the returned price if included.')

    def to_accounts(self):
        return AccountsBalancesInput(accounts=[self.address],  # type: ignore
                                     tokens=self.tokens,
                                     include_price=self.include_price,
                                     quote=self.quote)


class AccountsBalancesInput(Accounts):
    tokens: List[Token] = DTOField(default=[], description="A list of Tokens")
    include_price: bool = DTOField(default=False, description='Include price in the output')
    quote: Currency = DTOField(FiatCurrency(symbol='USD'),
                               description='Currency of the returned price if included.')


@Model.describe(slug="account.balances",
                version="1.0",
                display_name="Account\'s token balances",
                description="Balances of tokens for an account",
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['portfolio'],
                input=AccountBalancesInput,
                output=Portfolio)
class AccountBalances(Model):
    def run(self, input: AccountBalancesInput) -> Portfolio:
        return self.context.run_model(
            'accounts.balances',
            input=input.to_accounts().dict(),
            return_type=Portfolio)


@Model.describe(slug="accounts.balances",
                version="1.0",
                display_name="Accounts\' token balances",
                description="Balances of tokens for a list of accounts",
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['portfolio'],
                input=AccountsBalancesInput,
                output=Portfolio)
class AccountsBalances(Model):
    def include_price(self, positions: List[Position], quote: Currency) -> List[Position]:
        pqs_maybe = self.context.run_model(
            slug='price.quote-multiple-maybe',
            input=Some(some=[
                {'base': p.asset.address, 'quote': quote} for p in positions
            ]),
            return_type=Some[Maybe[PriceWithQuote]],
        )

        price_positions = []
        for price_maybe, position in zip(pqs_maybe.some, positions):
            price_quote = price_maybe.get_just(PriceWithQuote(price=0.0, src="none",
                                                              quoteAddress=quote.address))
            price_positions.append(Position(amount=position.amount,
                                            asset=position.asset,
                                            price_quote=price_quote))
        return price_positions

    def run(self, input: AccountsBalancesInput) -> Portfolio:
        native_token = None
        tokens = []
        for token in input.tokens:
            if isinstance(token, NativeToken):
                native_token = token
            else:
                tokens.append(token)

        balances = {}
        if native_token is not None:
            native_amount = 0
            for acc in input.accounts:
                native_amount += native_token.balance_of_scaled(acc.address.checksum)

            balances[str(native_token.address)] = Position(amount=native_amount,
                                                           asset=native_token)

        with self.context.ledger.TokenBalance as bal:
            token_balances = bal.select(
                aggregates=[
                    (f'{bal.TRANSACTION_VALUE.as_numeric().sum_()}', 'balance'),
                    (f'{bal.TOKEN_ADDRESS}', 'address'),
                ],
                having=bal.TRANSACTION_VALUE.as_numeric().sum_().gt(0),
                where=bal.ADDRESS.in_(input.to_address()).and_(
                    bal.TOKEN_ADDRESS.in_([t.address for t in input.tokens])),
                group_by=[bal.TOKEN_ADDRESS],
            )

        for token_balance in token_balances:
            try:
                token = Token(address=token_balance['address'])
                balance = token.scaled(int(token_balance['balance']))
                if balance > 0 and not math.isclose(balance, 0):
                    balances[str(token.address)] = Position(asset=token, amount=balance)
            except Exception:
                # TODO: currently skip NFTs
                self.logger.info(
                    f"Skipping {token_balance['address']} as it is not ERC20")

        positions: List[Position] = []
        for token in input.tokens:
            token_address = str(token.address)
            if token_address in balances:
                positions.append(balances[token_address])
            else:
                positions.append(Position(amount=0, asset=token))

        if input.include_price:
            positions = self.include_price(positions, input.quote)

        return Portfolio(positions=positions)
