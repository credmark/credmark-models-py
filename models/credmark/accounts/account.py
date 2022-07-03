import math

import numpy as np
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.types import (Account, Accounts, Address, Contract,
                                NativePosition, NativeToken, Portfolio,
                                Position, Token, TokenPosition, Tokens)
from credmark.cmf.types.ledger import TokenTransferTable

np.seterr(all='raise')


@Model.describe(slug='account.token-erc20',
                version='1.0',
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
        transfer_cols = [TokenTransferTable.Columns.BLOCK_NUMBER,
                         TokenTransferTable.Columns.LOG_INDEX,
                         TokenTransferTable.Columns.TRANSACTION_HASH,
                         TokenTransferTable.Columns.TO_ADDRESS,
                         TokenTransferTable.Columns.FROM_ADDRESS,
                         TokenTransferTable.Columns.TOKEN_ADDRESS]

        df_tt = (self.context.ledger.get_erc20_transfers(
            columns=transfer_cols,
            aggregates=[self.context.ledger.Aggregate(
                f'SUM(CASE WHEN {TokenTransferTable.Columns.TO_ADDRESS} = lower(\'{input.address}\') '
                f'THEN {TokenTransferTable.Columns.VALUE} ELSE -{TokenTransferTable.Columns.VALUE} END)', 'sum_value')],
            where=(f'{TokenTransferTable.Columns.TO_ADDRESS} = lower(\'{input.address}\') or '
                   f'{TokenTransferTable.Columns.FROM_ADDRESS} = lower(\'{input.address}\')'),
            group_by=','.join(transfer_cols))
            .to_dataframe())

        if df_tt.empty:
            return pd.DataFrame(columns=transfer_cols, data=[]).to_dict()
        else:
            return (df_tt.sort_values(['block_number', 'log_index'])
                    .reset_index(drop=True)
                    .to_dict())


@Model.describe(
    slug="account.portfolio",
    version="0.2",
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
        native_amount = self.context.web3.eth.get_balance(input.address)
        if not math.isclose(native_amount, 0):
            positions.append(
                NativePosition(
                    amount=NativeToken().scaled(native_amount),
                    asset=NativeToken()
                )
            )

        with self.context.ledger.TokenTransfer as q:
            token_addresses = q.select(
                columns=[q.Columns.TOKEN_ADDRESS],
                where=' '.join(
                    [f"{q.Columns.FROM_ADDRESS}='{input.address}'",
                     "or",
                     f"{q.Columns.TO_ADDRESS}='{input.address}'"]))

        for t in list(dict.fromkeys([t['token_address'] for t in token_addresses])):
            try:
                token = Token(address=t)
                balance = token.scaled(token.functions.balanceOf(input.address).call())
                if balance > 0.0:
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


@ Model.describe(
    slug="account.portfolio-aggregate",
    version="0.1",
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
        token_addresses = []
        native_balance = 0.0
        for a in input:
            token_addresses += self.context.ledger.get_erc20_transfers(
                columns=[TokenTransferTable.Columns.TOKEN_ADDRESS],
                where=' '.join(
                    [f"{TokenTransferTable.Columns.FROM_ADDRESS}='{a.address}'",
                     "or",
                     f"{TokenTransferTable.Columns.TO_ADDRESS}='{a.address}'"]),
                group_by=TokenTransferTable.Columns.TOKEN_ADDRESS)
            native_balance += self.context.web3.eth.get_balance(a.address)
        positions = []

        for t in set(dict.fromkeys([t['token_address'] for t in token_addresses])):
            try:
                token = Token(address=t)
                balance = sum([token.scaled(token.functions.balanceOf(a.address).call())
                               for a in input])
                if balance > 0.0:
                    found = False
                    for p in positions:
                        if p.asset.address == token.address:
                            p.amount += balance
                            found = True
                            break
                    if not found:
                        positions.append(
                            TokenPosition(asset=token, amount=balance))
            except Exception as _err:
                # TODO: currently skip NFTs
                pass

        positions.append(
            NativePosition(
                amount=NativeToken().scaled(native_balance),
                asset=NativeToken()
            )
        )
        return Portfolio(
            positions=positions
        )


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
        1: {
            Address('0xc4ad29ba4b3c580e6d59105fff484999997675ff')
        }
    }

    def run(self, input: Account) -> Portfolio:
        df_dict = self.context.run_model('account.token-erc20', input=input)
        df = pd.DataFrame.from_dict(df_dict)

        _lp_tokens = self.CURVE_LP_TOKEN[self.context.chain_id]
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
