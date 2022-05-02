from credmark.cmf.model import Model
from credmark.cmf.types import Address, Token, BlockNumber
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types.ledger import TokenTransferTable
from credmark.dto import DTO

from models.tmp_abi_lookup import ERC_20_ABI

class VCInput(DTO):
    receiver_address: Address

    class Config:
        schema_extra = {
            'examples': [{'receiver_address': '0xA52Fd396891E7A74b641a2Cb1A6999Fcf56B077e'}]
        }

@Model.describe(
    slug='contrib.debt-dao-votium-cashflow',
    version='1.1',
    display_name='Votium Cashflow',
    description='Tracks cashflow from Votium claim to receiver address.',
    input=VCInput,
    output=dict
)
class VotiumCashflow(Model):
    def run(self, input: VCInput) -> dict:
        votium_claim_address = Address("0x378Ba9B73309bE80BF4C2c027aAD799766a7ED5A")
        transfers = self.context.ledger.get_erc20_transfers(columns=[
            TokenTransferTable.Columns.BLOCK_NUMBER,
            TokenTransferTable.Columns.VALUE,
            TokenTransferTable.Columns.TOKEN_ADDRESS,
            TokenTransferTable.Columns.TRANSACTION_HASH
        ], where=f'{TokenTransferTable.Columns.TO_ADDRESS}=\'{input.receiver_address}\' \
        and {TokenTransferTable.Columns.FROM_ADDRESS}=\'{votium_claim_address}\'')
        for transfer in transfers:
            try:
                token = Token(address=transfer['token_address']).info
            except ModelDataError:
                token = Token(address=transfer['token_address'], abi=ERC_20_ABI)
            try:
                transfer['price'] = self.context.run_model(
                    'token.price', input=token, block_number=transfer['block_number'])['price']
            except Exception:
                transfer['price'] = 0
            if transfer['price'] is None:
                transfer['price'] = 0
            transfer['value_usd'] = transfer['price'] * \
                float(transfer['value']) / (10 ** token.decimals)
            transfer['block_time'] = str(BlockNumber(transfer['block_number']).timestamp_datetime)
            transfer['token_symbol'] = token.symbol
        return transfers.dict()
