import credmark.model
from credmark.types.data import Address, AddressStr
from credmark.types.dto import DTO, DTOField

min_erc20_abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'


class ERC20LookupDTO(DTO):
    address: AddressStr = DTOField(None, description='Token Address')
    symbol: str = DTOField(None, description='Token Symbol')


class TokenAmountDto(DTO):
    address: AddressStr = DTOField(None, description='Token Address')
    amount: str = DTOField(None, description="The amount of a Token")
    scaledAmount: float = DTOField(
        None, description="The Amount of a Token, scaled by decimal Amount")


class BalanceOfInputDTO(DTO):
    token: AddressStr
    address: AddressStr


@credmark.model.describe(slug='erc20-totalSupply',
                         version='1.0',
                         display_name='ERC20 Total Supply',
                         description='Get the Total Supply of an ERC20',
                         input=Address,
                         output=TokenAmountDto
                         )
class TotalSupply(credmark.model.Model):

    def run(self, input: Address) -> TokenAmountDto:
        contract = self.context.contracts.load_address(input.checksum)
        totalSupply = contract.functions.totalSupply().call()
        decimals = contract.functions.decimals().call()
        scaledAmount = totalSupply / (10**decimals)
        return TokenAmountDto(**{"address": input.address, "amount": totalSupply, "scaledAmount": scaledAmount})


@credmark.model.describe(slug='erc20-balanceOf',
                         version='1.0',
                         display_name='ERC20 balanceOf',
                         description='Get the balance of an ERC20 Token from a wallet address',
                         input=BalanceOfInputDTO)
class BalanceOf(credmark.model.Model):

    def run(self, input: BalanceOfInputDTO) -> TokenAmountDto:
        contract = self.context.contracts.load_address(input.token)
        balanceOf = contract.functions.balanceOf(input.address).call()
        decimals = contract.functions.decimals().call()
        scaledAmount = balanceOf / (10**decimals)
        return TokenAmountDto(**{"address": input.address, "amount": balanceOf, "scaledAmount": scaledAmount})
