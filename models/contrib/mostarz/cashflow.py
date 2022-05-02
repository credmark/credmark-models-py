from credmark.cmf.model import Model
from credmark.cmf.types import Address, Token, BlockNumber, Contract
from credmark.cmf.types.ledger import TokenTransferTable
from credmark.dto import EmptyInput


@Model.describe(
    slug='contrib.neilz-redacted-votium-cashflow',
    version='1.1',
    display_name='Redacted Cartel Votium Cashflow',
    description='Redacted Cartel Votium Cashflow',
    input=Contract,
    output=dict
)
class RedactedVotiumCashflow(Model):
    def run(self, input: None) -> dict:

        transfers = self.context.ledger.get_erc20_transfers(columns=[
            TokenTransferTable.Columns.BLOCK_NUMBER,
            TokenTransferTable.Columns.VALUE,
            TokenTransferTable.Columns.TOKEN_ADDRESS,
            TokenTransferTable.Columns.TRANSACTION_HASH
        ], where=f'{TokenTransferTable.Columns.TO_ADDRESS}=\'{input}\'')
        for transfer in transfers:
            token = Token(address=transfer['token_address']).info
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
