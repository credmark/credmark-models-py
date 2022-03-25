
import credmark.model
from credmark.types import (
    Token,
    Account,
    Position,
    Portfolio,
    NativeToken
)
from credmark.types.models.ledger import (
    TokenTransferTable
)


@credmark.model.describe(
    slug="account.portfolio",
    version="1.0",
    display_name="Account Portfolio",
    description="All of the token holdings for an account",
    developer="Credmark",
    input=Account,
    output=Portfolio)
class WalletInfoModel(credmark.model.Model):
    def run(self, input: Account) -> Portfolio:
        token_addresses = self.context.ledger.get_erc20_transfers(
            columns=[TokenTransferTable.Columns.TOKEN_ADDRESS],
            where=' '.join(
                [f"{TokenTransferTable.Columns.FROM_ADDRESS}='{input.address}'",
                 "or",
                 f"{TokenTransferTable.Columns.TO_ADDRESS}='{input.address}'"]))

        positions = [
            Position(
                amount=self.context.web3.eth.get_balance(input.address),
                token=Token.native_token()
            )
        ]

        for t in list(dict.fromkeys([t['token_address'] for t in token_addresses])):
            try:
                token = Token(address=t)
                balance = token.balance_of(input.address)
                if balance > 0.0:
                    positions.append(
                        Position(token=token, amount=balance.scaled))
            except Exception as _err:
                # TODO: currently skip NFTs
                pass

        return Portfolio(
            positions=positions
        )
