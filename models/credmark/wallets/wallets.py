
import credmark.model
from credmark.types import Address, Token, Account, Position, Portfolio
from credmark.types.dto import DTO, DTOField
from credmark.types.models.ledger import (
    TokenTransferTable
)


@credmark.model.describe(
    slug="wallet.portfolio",
    version="1.0",
    display_name="Token Information",
    developer="Credmark",
    input=Account,
    output=Portfolio
)
class WalletInfoModel(credmark.model.Model):
    def run(self, input: Account) -> Portfolio:
        transfers = self.context.ledger.get_erc20_transfers(
            columns=[TokenTransferTable.Columns.TOKEN_ADDRESS],
            where=f"{TokenTransferTable.Columns.FROM_ADDRESS}='{input.address}' or {TokenTransferTable.Columns.TO_ADDRESS}='{input.address}'")
        token_addresses = []

        positions = [
            Position(
                amount=Token.native_token().balance_of(input.address),
                token=Token.native_token()
            )
        ]

        for t in list(dict.fromkeys([t['token_address'] for t in token_addresses])):
            try:
                token = Token(address=t)
                positions.append(Position(token=token, amount=token.balance_of(input.address)))
            except:
                # currently skip NFTs
                pass

        return Portfolio(
            positions=positions
        )
