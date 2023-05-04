
from typing import Dict

from credmark.cmf.model import Model
from credmark.cmf.types import Account, Accounts, Address, NativeToken
from credmark.dto import DTO


class NativeTokenBalance(DTO):
    native_token: NativeToken
    native_token_decimals: int
    native_token_symbol: str
    total_balance: float
    balance_for_accounts: Dict[Address, float]


@Model.describe(slug='account.native-balance',
                version='0.1',
                display_name='Account - Native balance',
                description='balance of native token in an account',
                developer='Credmark',
                category='account',
                tags=['token', 'native'],
                input=Account,
                output=NativeTokenBalance)
class NativeBalance4Account(Model):
    def run(self, input: Account) -> NativeTokenBalance:
        return self.context.run_model('accounts.native-balance',
                                      Accounts(accounts=[Account(input.address)]),
                                      return_type=NativeTokenBalance)


@Model.describe(slug='accounts.native-balance',
                version='0.1',
                display_name='Accounts - Native balance',
                description='balance of native token in some accounts',
                developer='Credmark',
                category='account',
                tags=['token', 'native'],
                input=Accounts,
                output=NativeTokenBalance)
class NativeBalance4Accounts(Model):
    def run(self, input: Accounts) -> NativeTokenBalance:
        native_token = NativeToken()
        total_balance = 0
        balance_for_accounts = {}
        for account in input.accounts:
            balance = self.context.web3.eth.get_balance(account.address.checksum)
            balance = native_token.scaled(balance)
            self.logger.info(f'balance for {account.address}: {balance}')
            balance_for_accounts[account.address] = balance
            total_balance += balance

        return NativeTokenBalance(
            native_token=native_token,
            native_token_decimals=native_token.decimals,
            native_token_symbol=native_token.symbol,
            total_balance=total_balance,
            balance_for_accounts=balance_for_accounts)
