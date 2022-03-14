
import credmark.model
from credmark.types import Token, Account, Position, Portfolio
from credmark.types.models.ledger import TokenTransferTable


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
            where=f"{TokenTransferTable.Columns.FROM_ADDRESS}='{input.address}' or {TokenTransferTable.Columns.TO_ADDRESS}='{input.address}'")

        positions = [
            Position(
                amount=Token.native_token().balance_of(input.address),
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
            except:
                # currently skip NFTs
                pass

        return Portfolio(
            positions=positions
        )
