import credmark.model
from credmark.types import Address, Token, Wallet
from credmark.types import Position
from credmark.types.dto import DTO, DTOField


class ERC20LookupDTO(DTO):
    address: Address = DTOField(None, description='Token Address')
    symbol: str = DTOField(None, description='Token Symbol')


class BalanceOfInput(DTO):
    token: Token
    wallet: Wallet


@credmark.model.describe(slug='erc20-totalSupply',
                         version='1.0',
                         display_name='ERC20 Total Supply',
                         description='Get the Total Supply of an ERC20',
                         input=Token,
                         output=Position
                         )
class TotalSupply(credmark.model.Model):

    def run(self, input: Token) -> Position:
        totalSupply = input.functions.totalSupply().call()
        return Position(**{"token": input, "amount": totalSupply})


@credmark.model.describe(slug='erc20-balanceOf',
                         version='1.0',
                         display_name='ERC20 balanceOf',
                         description='Get the balance of an ERC20 Token from a wallet address',
                         input=BalanceOfInput)
class BalanceOf(credmark.model.Model):

    def run(self, input: BalanceOfInput) -> Position:
        balanceOf = input.token.instance.functions.balanceOf(input.wallet.address.checksum).call()
        return Position(**{"token": input.token, "amount": balanceOf})
