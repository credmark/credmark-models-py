import math
from typing import List, Optional

import numpy as np
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (Account, Accounts, Address, Contract,
                                NativePosition, NativeToken, Network,
                                Portfolio, Position, Price, Token,
                                TokenPosition, Tokens)
from credmark.dto import DTO

np.seterr(all='raise')


def get_token_transfer_columns(_context) -> List:
    with _context.ledger.TokenTransfer as q:
        transfer_cols = [q.BLOCK_NUMBER,
                         q.LOG_INDEX,
                         q.TRANSACTION_HASH,
                         q.TO_ADDRESS,
                         q.FROM_ADDRESS,
                         q.TOKEN_ADDRESS]

        return transfer_cols


def get_token_transfer(_context, _address) -> List:
    with _context.ledger.TokenTransfer as q:
        transfer_cols = get_token_transfer_columns(_context)
        df_ts = [pd.DataFrame(columns=transfer_cols+['value'], data=[])]
        offset = 0
        while True:
            df_tt = (q.select(
                columns=transfer_cols,
                aggregates=[((f'CASE WHEN {q.TO_ADDRESS.eq(_address)} '
                            f'THEN {q.VALUE} ELSE {q.VALUE.neg_()} END'), 'value')],
                where=(q.TO_ADDRESS.eq(_address).or_(q.FROM_ADDRESS.eq(_address))).parentheses_(),
                order_by=q.BLOCK_NUMBER,
                offset=offset).to_dataframe())

            if df_tt.shape[0] > 0:
                df_ts.append(df_tt)
            if df_tt.shape[0] < 5000:
                break
            offset += 5000

    return df_ts


class TokenReturn(DTO):
    token_address: Address
    token_symbol: str
    current_amount: float
    current_value: Optional[float]
    token_return: Optional[float]


class TokenReturnOutput(DTO):
    token_returns: List[TokenReturn]
    total_current_value: float
    total_return: float

    @classmethod
    def default(cls):
        return cls(token_returns=[], total_current_value=0, total_return=0)


def token_return(_context, _logger, _df, native_amount) -> TokenReturnOutput:
    all_tokens = []

    native_token = NativeToken()

    if not math.isclose(native_amount, 0):
        native_token_price = _context.run_model(slug='price.quote',
                                                input=dict(base=native_token),
                                                return_type=Price).price
        native_token_return = TokenReturn(
            token_address=native_token.address,
            token_symbol=native_token.symbol,
            current_amount=native_amount,
            current_value=native_amount*native_token_price,
            token_return=None
        )
    else:
        native_token_return = TokenReturn(
            token_address=native_token.address,
            token_symbol=native_token.symbol,
            current_amount=0,
            current_value=0,
            token_return=None
        )

    for tok_address, dfa in _df.groupby('token_address'):
        tok = Token(tok_address)

        try:
            dfa = dfa.assign(value=lambda x, tok=tok: x.value.apply(tok.scaled))
        except ModelDataError:
            if tok.abi is not None and 'decimals' not in tok.abi.functions:
                continue  # ERC-721`
            raise

        try:
            tok_symbol = tok.symbol
        except ModelRunError:
            tok_symbol = ''

        balance = 0
        value = 0
        for _n, r in dfa.iterrows():
            balance += r.value
            if value is not None:
                try:
                    then_price = _context.run_model(slug='price.quote',
                                                    input=dict(base=tok),
                                                    return_type=Price,
                                                    block_number=r.block_number).price
                    value += -r.value * then_price
                    _logger.info((r.block_number, tok_symbol, then_price, r.value))
                except ModelRunError as err:
                    if 'No pool to aggregate for' not in err.data.message:
                        raise
                    then_price = None
                    value = None

        if value is not None:
            if balance != 0:
                current_price = _context.run_model(slug='price.quote',
                                                   input=dict(base=tok),
                                                   return_type=Price).price
                current_value = balance * current_price
            else:
                current_value = 0.0

            tok_return = value + current_value
        else:
            tok_return = None
            current_value = None

        all_tokens.append(
            TokenReturn(
                token_address=tok.address,
                token_symbol=tok.symbol,
                current_amount=balance,
                current_value=current_value,
                token_return=tok_return))

    total_current_value = sum(x.current_value for x in all_tokens
                              if x.current_value is not None)

    total_return = sum(x.token_return for x in all_tokens
                       if x.token_return is not None)

    return TokenReturnOutput(
        token_returns=all_tokens + [native_token_return],
        total_current_value=(
            total_current_value +
            (native_token_return.current_value
             if native_token_return.current_value is not None
             else 0)),
        total_return=total_return)


@Model.describe(slug='account.token-return',
                version='1.3',
                display_name='Account Token Return',
                description='Account ERC20 Token Return',
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['token'],
                input=Account,
                output=TokenReturnOutput)
class AccountERC20TokenReturn(Model):
    def run(self, input: Account) -> TokenReturnOutput:
        native_token = NativeToken()
        native_amount = native_token.balance_of_scaled(input.address.checksum)

        df_ts = get_token_transfer(self.context, input.address)
        df = (pd.concat(df_ts)
                .assign(value=lambda x: x.value.apply(int))
                .drop_duplicates()
                .sort_values('block_number')
                .reset_index(drop=True))

        # If we filter for one token address, use below
        # df = df.query('token_address == "0x4e3fbd56cd56c3e72c1403e103b45db9da5b9d2b"')

        return token_return(self.context, self.logger, df, native_amount)


@Model.describe(slug='accounts.token-return',
                version='0.2',
                display_name='Account Token Return',
                description='Account ERC20 Token Return',
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['token'],
                input=Accounts,
                output=TokenReturnOutput)
class AccountsERC20TokenReturn(Model):
    def run(self, input: Accounts) -> TokenReturnOutput:
        transfer_cols = get_token_transfer_columns(self.context)
        df_tss = [pd.DataFrame(columns=transfer_cols+['value'], data=[])]

        native_token = NativeToken()
        native_amount = 0
        for account in input:
            input_address = account.address
            df_ts = get_token_transfer(self.context, input_address)
            df_tss.extend(df_ts)
            native_amount += native_token.balance_of_scaled(account.address.checksum)

        df = (pd.concat(df_tss)
                .assign(value=lambda x: x.value.apply(int))
                .drop_duplicates()
                .sort_values('block_number')
                .reset_index(drop=True))

        erc20_token_returns = token_return(self.context, self.logger, df, native_amount)

        return erc20_token_returns


@Model.describe(slug='account.token-erc20',
                version='1.3',
                display_name='Account Token ERC20',
                description='Account ERC20 transaction table',
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['token'],
                input=Account,
                output=dict)
class AccountERC20Token(Model):
    def run(self, input: Account) -> dict:
        # pylint:disable=locally-disabled,line-too-long
        with self.context.ledger.TokenTransfer as q:
            transfer_cols = [q.BLOCK_NUMBER,
                             q.LOG_INDEX,
                             q.TRANSACTION_HASH,
                             q.TO_ADDRESS,
                             q.FROM_ADDRESS,
                             q.TOKEN_ADDRESS]

            df_ts = []
            offset = 0
            while True:
                df_tt = (
                    q.select(
                        aggregates=[((f'SUM(CASE WHEN {q.TO_ADDRESS.eq(input.address)} '
                                      f'THEN {q.VALUE} ELSE {q.VALUE.neg_()} END)'), 'value')],
                        where=(q.TO_ADDRESS.eq(input.address).or_(q.FROM_ADDRESS.eq(input.address))).parentheses_(),
                        group_by=transfer_cols,
                        offset=offset)
                    .to_dataframe())

                if df_tt.shape[0] > 0:
                    df_ts.append(df_tt)
                if df_tt.shape[0] < 5000:
                    break
                offset += 5000

            if len(df_ts) == 0:
                return pd.DataFrame(columns=transfer_cols, data=[]).to_dict()
            else:
                return (
                    pd.concat(df_ts)
                      .sort_values(['block_number', 'log_index'])
                      .reset_index(drop=True)
                      .to_dict())


@Model.describe(slug="account.portfolio",
                version="0.3",
                display_name="Account Portfolio",
                description="All of the token holdings for an account",
                developer="Credmark",
                category='account',
                subcategory='position',
                tags=['portfolio'],
                input=Account,
                output=Portfolio)
class WalletInfoModel(Model):
    def run(self, input: Account) -> Portfolio:
        positions = []
        native_token = NativeToken()
        native_amount = native_token.balance_of_scaled(input.address.checksum)
        if not math.isclose(native_amount, 0):
            positions.append(
                NativePosition(
                    amount=NativeToken().scaled(native_amount),
                    asset=NativeToken()
                )
            )

        with self.context.ledger.TokenTransfer as q:
            df_ts = []
            offset = 0
            while True:
                df_tt = (q
                         .select(aggregates=[(q.TOKEN_ADDRESS.distinct(), q.TOKEN_ADDRESS)],
                                 # pylint:disable=line-too-long
                                 where=q.FROM_ADDRESS.eq(input.address).or_(q.TO_ADDRESS.eq(input.address)),
                                 offset=offset)
                         .to_dataframe())

                if df_tt.shape[0] > 0:
                    df_ts.append(df_tt)
                if df_tt.shape[0] < 5000:
                    break
                offset += 5000

            if len(df_ts) == 0:
                token_addresses = []
            else:
                token_addresses = (pd
                                   .concat(df_ts)
                                   [q.TOKEN_ADDRESS])

        for t in token_addresses:
            try:
                token = Token(address=t)
                balance = token.scaled(token.functions.balanceOf(input.address).call())
                if not math.isclose(balance, 0):
                    positions.append(
                        TokenPosition(asset=token, amount=balance))
            except Exception as _err:
                # TODO: currently skip NFTs
                pass

        curve_lp_position = self.context.run_model(
            'account.position-in-curve',
            input=input)

        # positions.extend([CurveLPPosition(**p) for p in curve_lp_position['positions']])
        positions.extend(curve_lp_position['positions'])

        return Portfolio(positions=positions)


@Model.describe(
    slug="account.portfolio-aggregate",
    version="0.2",
    display_name="Account Portfolios for a list of Accounts",
    description="All of the token holdings for an account",
    developer="Credmark",
    category='account',
    subcategory='position',
    tags=['portfolio'],
    input=Accounts,
    output=Portfolio)
class AccountsPortfolio(Model):
    def run(self, input: Accounts) -> Portfolio:
        native_position = NativePosition(amount=0, asset=NativeToken())

        all_positions = []
        for acct in input:
            port = self.context.run_model('account.portfolio', input=acct, return_type=Portfolio)
            native_pos_n = None
            for pos_n, pos in enumerate(port.positions):
                if pos.asset.address == native_position.asset.address:
                    native_position.amount += pos.amount
                    native_pos_n = pos_n
                    break

            if native_pos_n is not None:
                port.positions.pop(native_pos_n)
            all_positions.extend(port.positions)

        all_positions.append(native_position)
        return Portfolio(positions=all_positions)


class CurveLPPosition(Position):
    pool: Contract
    supply_position: Portfolio
    lp_position: Portfolio


@Model.describe(
    slug="account.position-in-curve",
    version="1.1",
    display_name="account position in Curve LP",
    description="All the positions in Curve LP",
    developer="Credmark",
    category='account',
    subcategory='position',
    tags=['curve'],
    input=Account,
    output=Portfolio)
class GetCurveLPPosition(Model):
    CURVE_LP_TOKEN = {
        Network.Mainnet: {
            Address('0xc4ad29ba4b3c580e6d59105fff484999997675ff')
        }
    }

    def run(self, input: Account) -> Portfolio:
        df_dict = self.context.run_model('account.token-erc20', input=input)
        df = pd.DataFrame.from_dict(df_dict)

        _lp_tokens = self.CURVE_LP_TOKEN[self.context.network]
        lp_tx = df.query('token_address in @_lp_tokens')

        txs = lp_tx.transaction_hash.unique().tolist()
        lp_position = []
        for _tx in txs:
            df_tx = df.query('transaction_hash == @_tx')
            if df_tx.shape[0] == 2:
                tx_in = df_tx.query('token_address not in @_lp_tokens')
                in_token = Token(address=tx_in.token_address[0])
                in_token_amount = in_token.scaled(tx_in.sum_value[0])
                if tx_in.from_address[0] == input.address:
                    in_token_amount = abs(in_token_amount)
                else:
                    in_token_amount = -abs(in_token_amount)

                tx_out = df_tx.query('token_address in @_lp_tokens')
                lp_token = Token(address=tx_out.token_address[0])
                lp_token_amount = tx_out.sum_value[0]
                _lp_token_amount_scaled = lp_token.scaled(tx_out.sum_value[0])
                if tx_in.from_address[0] == input.address:
                    lp_token_amount = abs(lp_token_amount)
                else:
                    lp_token_amount = -abs(lp_token_amount)

                pool_info = self.context.run_model('curve-fi.pool-info', lp_token)
                pool_contract = Contract(address=pool_info['address'])
                pool_tokens = Tokens(**pool_info['tokens'])
                withdraw_token_amount = np.zeros(len(pool_tokens.tokens))
                np_balances = np.array(pool_info['balances'])
                for tok_n, tok in enumerate(pool_tokens):
                    withdraw_one = [0] * len(pool_tokens.tokens)
                    withdraw_one[tok_n] = 1
                    withdraw_token_amount[tok_n] = pool_contract.functions.calc_token_amount(
                        withdraw_one, False).call()
                    np_balances[tok_n] = np_balances[tok_n] / pool_tokens.tokens[tok_n].scaled(1)

                for tok_n, tok in enumerate(pool_tokens.tokens):
                    ratio = np_balances.dot(withdraw_token_amount) / np_balances[tok_n]
                    amount = lp_token_amount / ratio
                    lp_position.append(Position(asset=tok,
                                                amount=pool_tokens.tokens[tok_n].scaled(amount)))

                _ = CurveLPPosition(
                    asset=lp_token,
                    amount=_lp_token_amount_scaled,
                    pool=Contract(address=lp_token.functions.minter().call()),
                    supply_position=Portfolio(
                        positions=[TokenPosition(asset=in_token,
                                                 amount=in_token_amount)]),
                    lp_position=Portfolio(positions=lp_position))

        return Portfolio(positions=lp_position)
