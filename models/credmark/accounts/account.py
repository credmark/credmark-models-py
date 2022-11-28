# pylint: disable=too-many-function-args

import math
from enum import Enum

import numpy as np
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types.compose import MapBlockTimeSeriesOutput
from credmark.cmf.types import (Account, Accounts,
                                NativePosition, NativeToken,
                                Portfolio, Position, Records,
                                Token, TokenPosition)
from credmark.dto import DTOField, EmptyInput, cross_examples
from models.dtos.historical import HistoricalDTO
from models.credmark.accounts.token_return import TokenReturnOutput, token_return
from models.credmark.ledger.transfers import get_token_transfer, get_native_transfer
from web3.exceptions import ContractLogicError

np.seterr(all='raise')


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
                                          accounts=[input.address],  # type: ignore
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
                version='0.7',
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
            native_amount += native_token.balance_of_scaled(account.address.checksum)

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
                version='0.6',
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

            for _, token_bal_row in token_bal.iterrows():
                if not math.isclose(token_bal_row['value'], 0):
                    asset_token = Token(token_bal_row['token_address']).as_erc20()
                    try_price = self.context.run_model('price.quote-maybe',
                                                       input={'base': asset_token},
                                                       block_number=_past_block_number)
                    if try_price['just'] is None:
                        continue

                    try:
                        assets.append(
                            Position(amount=asset_token.scaled(token_bal_row['value']),
                                     asset=asset_token))
                    except (ModelDataError, ContractLogicError):
                        # NFT: ContractLogicError
                        continue

            price_historical_result[n_historical].output = (
                {"value": Portfolio(positions=assets)
                 .get_value(block_number=_past_block_number)})

        return price_historical_result


class AccountHistoricalInput(Account, HistoricalDTO):
    class Config:
        schema_extra = {
            'examples': cross_examples(
                [{'address': '0x388c818ca8b9251b393131c08a736a67ccb19297'}],
                HistoricalDTO.Config.schema_extra['examples'],
                limit=10)}


@Model.describe(
    slug='account.token-historical',
    version='0.3',
    display_name='Account\'s Token Holding Historical',
    description='Account\'s Token Holding Historical',
    developer="Credmark",
    category='account',
    subcategory='position',
    tags=['token'],
    input=AccountHistoricalInput,
    output=MapBlockTimeSeriesOutput[Portfolio])
class AccountERC20TokenHistorical(Model):
    def run(self, input: AccountHistoricalInput) -> MapBlockTimeSeriesOutput[Portfolio]:
        return self.context.run_model(
            'accounts.token-historical',
            AccountsHistoricalInput(
                **input.to_accounts().dict(),   # type: ignore
                window=input.window,
                interval=input.interval,
                exclusive=input.exclusive))


class AccountsHistoricalInput(Accounts, HistoricalDTO):
    class Config:
        schema_extra = {
            'examples': cross_examples(
                Accounts.Config.schema_extra['examples'],
                HistoricalDTO.Config.schema_extra['examples'])
        }


@Model.describe(
    slug='accounts.token-historical',
    version='0.6',
    display_name='Accounts\' Token Holding Historical',
    description='Accounts\' Token Holding Historical',
    developer="Credmark",
    category='account',
    subcategory='position',
    tags=['token'],
    input=AccountsHistoricalInput,
    output=MapBlockTimeSeriesOutput[Portfolio])
class AccountsERC20TokenHistorical(Model):
    def run(self, input: AccountsHistoricalInput) -> MapBlockTimeSeriesOutput[Portfolio]:
        _native_token = NativeToken()

        # TODO: native token transaction (incomplete) and gas spending
        _df_native = get_native_transfer(self.context, input.to_address())

        # ERC-20 transaction
        df_erc20 = get_token_transfer(self.context, input.to_address(), [], 0)

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

        for n_historical, row in df_historical.iterrows():
            _past_block_number = row['blockNumber']
            assets = []
            _native_token_bal = (_df_native
                                 .query('(block_number <= @_past_block_number)')
                                 .groupby('token_address', as_index=False)['value']
                                 .sum())

            # TODO
            # if not _native_token_bal.empty:
            #    assets.append(
            #        Position(amount=_native_token.scaled(native_token_bal['value'][0]),
            #                 asset=_native_token))

            token_bal = (df_erc20
                         .query('(block_number <= @_past_block_number)')
                         .groupby('token_address', as_index=False)['value']
                         .sum())

            for _, token_bal_row in token_bal.iterrows():
                if not math.isclose(token_bal_row['value'], 0):
                    asset_token = Token(token_bal_row['token_address']).as_erc20()
                    try:
                        assets.append(
                            Position(amount=asset_token.scaled(token_bal_row['value']),
                                     asset=asset_token))
                    except (ModelDataError, ContractLogicError):
                        # NFT: ContractLogicError
                        continue

            price_historical_result[n_historical].output = \
                Portfolio(positions=assets)  # type: ignore

        return price_historical_result  # type: ignore


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


@Model.describe(
    slug="account.portfolio-aggregate",
    version="0.2",
    display_name="(PEPRECATED) use accounts.portfolio",
    description="All of the token holdings for an account",
    developer="Credmark",
    category='account',
    subcategory='position',
    tags=['portfolio'],
    input=Accounts,
    output=Portfolio)
class AccountsPortfolioAggregate(Model):
    def run(self, input: Accounts) -> Portfolio:
        return self.context.run_model('accounts.portfolio', input=input, return_type=Portfolio)


@Model.describe(slug="accounts.portfolio",
                version="0.5",
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
                    balance += token.scaled(token.functions.balanceOf(acc.address.checksum).call())
                if not math.isclose(balance, 0):
                    positions.append(
                        TokenPosition(asset=token, amount=balance))
            except Exception as _err:
                # TODO: currently skip NFTs
                pass

        curve_lp_position = self.context.run_model(
            'curve.lp-accounts',
            input=input)

        # positions.extend([CurveLPPosition(**p) for p in curve_lp_position['positions']])
        positions.extend(curve_lp_position['positions'])

        return Portfolio(positions=positions)
