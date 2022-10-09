from credmark.cmf.model import Model
from credmark.cmf.types import Address, Token, BlockNumber
from credmark.dto import DTO, DTOField


class TokenBalanceInput(DTO):
    token: Address = DTOField(default=Address('0xD533a949740bb3306d119CC777fa900bA034cd52'))
    wallet: Address = Address('0xd2d43555134dc575bf7279f4ba18809645db0f1d')


class TokenNetInflowInput(DTO):
    from_addr: Address = Address('0xf650C3d88D12dB855b8bf7D11Be6C55A4e07dCC9')
    token: Address = Address('0xdac17f958d2ee523a2206206994597c13d831ec7')
    blocks: BlockNumber


@Model.describe(
    slug='contrib.token-balance-of',
    display_name='fetch balance of a specified token and wallet',
    description=("dynamically fetch balance of an ERC20 token and address"),
    input=TokenBalanceInput,
    version='1.0',
    developer='exa256',
    output=dict
)
class TokenBalanceOf(Model):

    def run(self, input: TokenBalanceInput):
        token = Token(address=input.token)
        balance = token.functions.balanceOf(input.wallet).call()
        supply = token.total_supply
        return {
            'token_address': input.token,
            'token_supply': supply,
            'wallet_address': input.wallet,
            'wallet_balance': balance,
            'balance_to_supply_ratio': token.scaled(balance) / token.scaled(supply)
        }


@Model.describe(
    slug='contrib.token-net-inflow',
    display_name='net inflow of tokens from an address',
    description=("return net token outflow from an address on a given time range"
                 "net inflow is total token inflow - total token outflow"
                 ),
    input=TokenNetInflowInput,
    version='1.1',
    developer='exa256',
    output=dict
)
class TokenNetInflow(Model):
    def run(self, input: TokenNetInflowInput):
        from_addr = input.from_addr

        token = Token(address=input.token)
        past_block = self.context.block_number - input.blocks

        # fetch and store all token transfers
        with self.context.ledger.TokenTransfer as q:
            transfers = q.select(
                columns=[
                    q.TO_ADDRESS,
                    q.FROM_ADDRESS,
                    q.VALUE,
                ],
                where=q.BLOCK_NUMBER.gt(past_block).and_(
                    q.TOKEN_ADDRESS.eq(token.address).and_(
                        q.TO_ADDRESS.eq(from_addr).or_(
                            q.FROM_ADDRESS.eq(from_addr)
                        ).parentheses_()
                    )
                ),
                order_by=q.BLOCK_NUMBER.desc(),
            ).to_dataframe()

        inflow = transfers.query('to_address == @from_addr')['value'].astype(float).sum()
        outflow = transfers.query('from_address == @from_addr')['value'].astype(float).sum()

        return {
            'inflow': token.scaled(inflow),
            'outflow': token.scaled(outflow),
            'net_inflow': token.scaled(inflow) - token.scaled(outflow),
            'from_address': input.from_addr,
            'token': input.token,
            'from_block': self.context.block_number - input.blocks,
            'to_block': self.context.block_number
        }
