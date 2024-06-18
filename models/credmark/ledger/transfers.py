# pylint: disable=line-too-long
from typing import List, Optional

import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.types import Account, Accounts, Address, NativeToken, Records
from credmark.dto import DTO, DTOField, cross_examples


class Tokens(DTO):
    tokens: List[Address] = DTOField([], description='List of tokens')
    startBlock: int = DTOField(0, description='start block number')

    class Config:
        schema_extra = {
            'examples': [{}, {"tokens": ["0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"]}]
        }


class AccountWithToken(Account, Tokens):
    class Config:
        schema_extra = {
            'examples': cross_examples(
                Tokens.Config.schema_extra['examples'],
                Account.Config.schema_extra['examples'],
                [{}, {'limit': None}],
                limit=10)}
    limit: Optional[int] = DTOField(
        None, description='limit to the number of records')


class AccountsWithToken(Accounts, Tokens):
    class Config:
        schema_extra = {
            'examples': cross_examples(
                Tokens.Config.schema_extra['examples'],
                Accounts.Config.schema_extra['examples'],
                [{}, {'limit': None}],
                limit=10)}
    limit: Optional[int] = DTOField(
        None, description='limit to the number of records')


@Model.describe(slug='account.token-transfer',
                version='1.12',
                display_name='Accounts\' Token Transfer',
                description='Accounts\' Token Transfer Table',
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['token'],
                input=AccountWithToken,
                output=Records)
class AccountERC20Token(Model):
    def run(self, input: AccountWithToken) -> Records:
        return self.context.run_model(
            'accounts.token-transfer',
            input=input.to_accounts().dict() |
            {"tokens": input.tokens,
             "startBlock": input.startBlock,
             'limit': input.limit},
            return_type=Records)


def fix_transfer(df_in):
    return df_in.assign(value=lambda x: x.value.apply(int))


@Model.describe(slug='accounts.token-transfer',
                version='1.12',
                display_name='Account\'s Token Transfer Table',
                description='Account\'s Token Transfer Table',
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['token'],
                input=AccountsWithToken,
                output=Records)
class AccountsERC20Token(Model):
    def run(self, input: AccountsWithToken) -> Records:
        df_erc20 = get_token_transfer(self.context,
                                      input.to_address(),
                                      input.tokens,
                                      input.startBlock,
                                      fix_int=False,
                                      limit=input.limit)
        return Records.from_dataframe(df_erc20, fix_int_columns=['value'])


def get_token_transfer(_context,
                       _accounts: List[Address],
                       _tokens: List[Address],
                       start_block: int,
                       fix_int: bool = True,
                       limit: Optional[int] = None) -> pd.DataFrame:

    def _use_model():
        req = {'accounts': _accounts, 'startBlock': start_block}
        if len(_tokens) > 0:
            req |= {'tokens': _tokens}

        model_result = _context.run_model(
            'ledger.account-token-transfers',
            req)

        result = (pd.DataFrame(model_result)
                  .assign(block_number=lambda x: x.block_number.apply(int))
                  .rename(columns={'transaction_value': 'value'} | ({"limit": limit} if limit is not None else {}))
                  .reset_index(drop=True))
        return result

    if fix_int:
        return fix_transfer(_use_model())

    result = _use_model()

    return result


def get_native_transfer(_context,
                        _accounts: List[Address],
                        fix_int: bool = True,
                        limit: Optional[int] = None) -> pd.DataFrame:
    native_token_addr = NativeToken().address

    def _use_ledger():
        with _context.ledger.Transaction as q:
            transfer_cols = [q.BLOCK_NUMBER, q.TO_ADDRESS, q.FROM_ADDRESS,
                             q.HASH, q.TRANSACTION_INDEX]
            df_ts = [pd.DataFrame(columns=transfer_cols+['value'], data=[])]

        with _context.ledger.Transaction as q:
            for _address in _accounts:
                offset = 0
                while True:
                    rs_tt = (q.select(
                        columns=transfer_cols,
                        aggregates=[((f'CASE WHEN {q.TO_ADDRESS.eq(_address)} '
                                    f'THEN {q.VALUE} ELSE {q.VALUE.neg_()} END'), 'value'),
                                    (q.field(native_token_addr).squote(), 'token_address')],
                        where=(q.TO_ADDRESS.eq(_address).or_(q.FROM_ADDRESS.eq(_address))
                               ).parentheses_().and_(q.field('value').dquote().ne(0)),
                        order_by=q.BLOCK_NUMBER.comma_(q.TRANSACTION_INDEX),
                        offset=offset))

                    df_tt = rs_tt.to_dataframe()

                    if df_tt.shape[0] > 0:
                        df_ts.append(df_tt)
                    if df_tt.shape[0] < 5000:
                        break
                    offset += 5000

            return (pd.concat(df_ts)
                    .assign(block_number=lambda x: x.block_number.apply(int))
                    .drop_duplicates()
                    .sort_values('block_number')
                    .rename(columns={'hash': 'transaction_hash', 'transaction_index': 'log_index'})
                    .reset_index(drop=True))

    def _use_model():
        result = (pd.DataFrame(_context.run_model(
            'ledger.account-native-token-transfers',
            {'accounts': _accounts}))
            .assign(block_number=lambda x: x.block_number.apply(int),
                    token_address=native_token_addr)
            .rename(columns={'transaction_value': 'value'} | ({"limit": limit} if limit is not None else {})))
        return result

    if fix_int:
        df_in = _use_model()
        if df_in.empty:
            return df_in
        return fix_transfer(df_in).assign(gas_used=lambda x: x.gas_used.apply(int))

    return _use_model()
