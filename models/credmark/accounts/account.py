from credmark.cmf.model import Model
from credmark.cmf.types import (
    Token,
    Account,
    Portfolio,
    NativeToken,
    NativePosition,
    TokenPosition
)


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
        with self.context.ledger.TokenTransfer as q:
            token_addresses = q.select(
                columns=[q.Columns.TOKEN_ADDRESS],
                where=' '.join(
                    [f"{q.Columns.FROM_ADDRESS}='{input.address}'",
                     "or",
                     f"{q.Columns.TO_ADDRESS}='{input.address}'"]))

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
