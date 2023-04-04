from credmark.cmf.model import Model
from credmark.cmf.types import Address, Token, BlockNumber
from credmark.dto import DTO


class GCInput(DTO):
    sender_address: Address
    receiver_address: Address

    class Config:
        schema_extra = {
            'examples': [{'sender_address': '0x378Ba9B73309bE80BF4C2c027aAD799766a7ED5A',
                          'receiver_address': '0xA52Fd396891E7A74b641a2Cb1A6999Fcf56B077e'}]
        }


@Model.describe(
    slug='contrib.debt-dao-generalized-cashflow',
    version='1.2',
    display_name='Generalized Cashflow',
    description='Tracks cashflow from sender address to receiver address.',
    category='protocol',
    tags=['token'],
    input=GCInput,
    output=dict
)
class GeneralizedCashflow(Model):
    def run(self, input: GCInput) -> dict:
        with self.context.ledger.TokenTransfer as q:
            transfers = q.select(
                columns=[q.BLOCK_NUMBER,
                         q.VALUE,
                         q.TOKEN_ADDRESS,
                         q.TRANSACTION_HASH],
                where=q.TO_ADDRESS.eq(input.receiver_address).and_(
                    q.FROM_ADDRESS.eq(input.sender_address)))


        for transfer in transfers:
            token = Token(address=transfer['token_address'])
            try:
                transfer['price'] = self.context.run_model(
                    slug='price.quote',
                    input={'base': token},
                    block_number=transfer['block_number'])['price']
            except Exception:
                transfer['price'] = 0
            if transfer['price'] is None:
                transfer['price'] = 0
            transfer['value_usd'] = transfer['price'] * \
                float(transfer['value']) / (10 ** token.decimals)
            transfer['block_time'] = str(BlockNumber(int(transfer['block_number'])).timestamp_datetime)
            transfer['token_symbol'] = token.symbol
        return transfers.dict()
