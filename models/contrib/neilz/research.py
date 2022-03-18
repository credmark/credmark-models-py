from credmark.types import Address, Token
from credmark.types.models.ledger import TokenTransferTable
from credmark.types.data.block_number import BlockNumber
import credmark.model


@credmark.model.describe(
    slug='contrib.neilz-redacted-cashflow',
    version='1.0',
    display_name='Redacted Cartel Votium Cashflow',
    description='Redacted Cartel weekly Cashflow',
    input=None,
    output=dict
)
class DebtDaoV1(credmark.model.Model):
    def run(self, input: None) -> dict:
        # TODO: unwonky this
        VOTIUM_CONTRACT_ADDRESS = Address("0x378Ba9B73309bE80BF4C2c027aAD799766a7ED5A")
        REDACTED_MULTISIG_ADDRESS = Address("0xA52Fd396891E7A74b641a2Cb1A6999Fcf56B077e")
        transfers = self.context.ledger.get_erc20_transfers(columns=[
            TokenTransferTable.Columns.BLOCK_NUMBER,
            TokenTransferTable.Columns.VALUE,
            TokenTransferTable.Columns.TOKEN_ADDRESS
        ], where=f'{TokenTransferTable.Columns.TO_ADDRESS}=\'{REDACTED_MULTISIG_ADDRESS}\' and {TokenTransferTable.Columns.FROM_ADDRESS}=\'{VOTIUM_CONTRACT_ADDRESS}\'')
        i = 0
        for transfer in transfers:
            print(transfer, i, len(transfers.data))
            i = i+1
            token = Token(address=transfer['token_address'])
            try:
                transfer['price'] = self.context.run_model(
                    'sushiswap.get-average-price', input=token, block_number=transfer['block_number'])['price']
                if transfer['price'] == 0.0:
                    transfer['price'] = self.context.run_model(
                        'uniswap-v2.get-average-price', input=token, block_number=transfer['block_number'])['price']
                    if transfer['price'] == 0.0:
                        transfer['price'] = self.context.run_model(
                            'uniswap-v3.get-average-price', input=token, block_number=transfer['block_number'])['price']
            except:
                print('price failed')
                transfer['price'] = 0
            transfer['value_usd'] = transfer['price'] * \
                float(transfer['value']) / (10 ** token.decimals)
            transfer['block_time'] = BlockNumber(transfer['block_number']).datestring
            transfer['token_symbol'] = token.symbol
        return transfers
