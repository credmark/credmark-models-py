from pydoc import describe
import credmark.model
from credmark.types import Address, Token, Account, Position
from credmark.types.dto import DTO, DTOField


class TokenInfo(DTO):
    token: Token
    total_supply_wei: int
    total_supply: float


@credmark.model.describe(
    slug="token.info",
    version="1.0",
    display_name="Token Information",
    developer="Credmark",
    input=Token,
    output=TokenInfo
)
class TokenInfoModel(credmark.model.Model):
    def run(self, input: Token) -> TokenInfo:

        input.load()

        total_supply = input.total_supply()
        return TokenInfo(
            token=input,
            total_supply=total_supply.scaled,
            total_supply_wei=total_supply
        )
