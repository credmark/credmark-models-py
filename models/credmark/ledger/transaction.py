from typing import List
import pandas as pd

from credmark.cmf.types import (Address, NativeToken)


def get_token_transfer(_context, _accounts: List[Address]) -> pd.DataFrame:
    def _use_ledger():
        with _context.ledger.TokenTransfer as q:
            transfer_cols = [q.BLOCK_NUMBER, q.TO_ADDRESS, q.FROM_ADDRESS, q.TOKEN_ADDRESS,
                             q.TRANSACTION_HASH, q.LOG_INDEX]
            df_ts = [pd.DataFrame(columns=transfer_cols+['value'], data=[])]

        with _context.ledger.TokenTransfer as q:
            for _address in _accounts:
                offset = 0
                while True:
                    df_tt = (q.select(
                        columns=transfer_cols,
                        aggregates=[((f'CASE WHEN {q.TO_ADDRESS.eq(_address)} '
                                      f'THEN {q.VALUE} ELSE {q.VALUE.neg_()} END'), 'value')],
                        where=(q.TO_ADDRESS.eq(_address).or_(
                            q.FROM_ADDRESS.eq(_address))).parentheses_(),
                        order_by=q.BLOCK_NUMBER.comma_(q.LOG_INDEX),
                        offset=offset).to_dataframe())

                    if df_tt.shape[0] > 0:
                        df_ts.append(df_tt)
                    if df_tt.shape[0] < 5000:
                        break
                    offset += 5000

        return (pd.concat(df_ts)
                .assign(value=lambda x: x.value.apply(int),
                        block_number=lambda x: x.block_number.apply(int))
                .drop_duplicates()
                .sort_values('block_number')
                .reset_index(drop=True))

    def _use_model():
        result = (pd.DataFrame(_context.run_model(
            'ledger.account-token-transfers',
            {'accounts': _accounts}))
            .assign(value=lambda x: x.transaction_value.apply(int),
                    block_number=lambda x: x.block_number.apply(int))
            .drop(columns='transaction_value'))
        return result

    return _use_model()


def get_native_transfer(_context, _accounts: List[Address]) -> pd.DataFrame:
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
                    .assign(value=lambda x: x.value.apply(int),
                            block_number=lambda x: x.block_number.apply(int))
                    .drop_duplicates()
                    .sort_values('block_number')
                    .rename(columns={'hash': 'transaction_hash', 'transaction_index': 'log_index'})
                    .reset_index(drop=True))

    def _use_model():
        result = (pd.DataFrame(_context.run_model(
            'ledger.account-native-token-transfers',
            {'accounts': _accounts}))
            .assign(value=lambda x: x.transaction_value.apply(int),
                    block_number=lambda x: x.block_number.apply(int),
                    token_address=native_token_addr)
            .drop(columns='transaction_value'))
        return result

    return _use_model()
