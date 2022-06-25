from credmark.cmf.model import Model
from credmark.cmf.types import (Account, Accounts, Contract, NativePosition,
                                NativeToken, Portfolio, Position, Token,
                                TokenPosition)
from credmark.cmf.types.ledger import TokenTransferTable


@Model.describe(
    slug="account.portfolio",
    version="1.0",
    display_name="Account Portfolio",
    description="All of the token holdings for an account",
    developer="Credmark",
    input=Account,
    output=Portfolio)
class WalletInfoModel(Model):
    def run(self, input: Account) -> Portfolio:
        token_addresses = self.context.ledger.get_erc20_transfers(
            columns=[TokenTransferTable.Columns.TOKEN_ADDRESS],
            where=' '.join(
                [f"{TokenTransferTable.Columns.FROM_ADDRESS}='{input.address}'",
                 "or",
                 f"{TokenTransferTable.Columns.TO_ADDRESS}='{input.address}'"]))

        positions = []
        positions.append(
            NativePosition(
                amount=self.context.web3.eth.get_balance(input.address),
                asset=NativeToken()
            )
        )

        for t in list(dict.fromkeys([t['token_address'] for t in token_addresses])):
            try:
                token = Token(address=t)
                balance = float(token.functions.balanceOf(input.address).call())
                if balance > 0.0:
                    positions.append(
                        TokenPosition(asset=token, amount=balance))
            except Exception as _err:
                # TODO: currently skip NFTs
                pass

        return Portfolio(
            positions=positions
        )


@Model.describe(
    slug="account.portfolio-aggregate",
    version="1.0",
    display_name="Account Portfolios for a list of Accounts",
    description="All of the token holdings for an account",
    developer="Credmark",
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
                     f"{TokenTransferTable.Columns.TO_ADDRESS}='{a.address}'"]))
            native_balance += self.context.web3.eth.get_balance(a.address)
        positions = []

        for t in set(dict.fromkeys([t['token_address'] for t in token_addresses])):
            try:
                token = Token(address=t)
                balance = sum([float(token.functions.balanceOf(a.address).call()) for a in input])
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
                amount=native_balance,
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
