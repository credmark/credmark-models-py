from credmark.types import Address, Token
from credmark.model.errors import ModelDataError
from credmark.types.models.ledger import TokenTransferTable
from credmark.types.data.block_number import BlockNumber
import credmark.model
from credmark.dto import EmptyInput

from models.tmp_abi_lookup import ERC_20_ABI


@credmark.model.describe(
    slug='contrib.neilz-redacted-votium-cashflow',
    version='1.1',
    display_name='Redacted Cartel Votium Cashflow',
    description='Redacted Cartel Votium Cashflow',
    input=EmptyInput,
    output=dict
)
class RedactedVotiumCashflow(credmark.model.Model):
    def run(self, input: None) -> dict:
        votium_claim_address = Address("0x378Ba9B73309bE80BF4C2c027aAD799766a7ED5A")
        redacted_multisig_address = Address("0xA52Fd396891E7A74b641a2Cb1A6999Fcf56B077e")
        transfers = self.context.ledger.get_erc20_transfers(columns=[
            TokenTransferTable.Columns.BLOCK_NUMBER,
            TokenTransferTable.Columns.VALUE,
            TokenTransferTable.Columns.TOKEN_ADDRESS,
            TokenTransferTable.Columns.TRANSACTION_HASH
        ], where=f'{TokenTransferTable.Columns.TO_ADDRESS}=\'{redacted_multisig_address}\' \
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


@credmark.model.describe(
    slug='contrib.neilz-redacted-convex-cashflow',
    version='1.1',
    display_name='Redacted Cartel Convex Cashflow',
    description='Redacted Cartel Convex Cashflow',
    input=EmptyInput,
    output=dict
)
class RedactedConvexCashflow(credmark.model.Model):
    def run(self, input: None) -> dict:
        convex_addresses = [
            Address("0x72a19342e8F1838460eBFCCEf09F6585e32db86E"),
            Address("0xD18140b4B819b895A3dba5442F959fA44994AF50"),
        ]
        redacted_multisig_address = Address("0xA52Fd396891E7A74b641a2Cb1A6999Fcf56B077e")
        transfers = self.context.ledger.get_erc20_transfers(columns=[
            TokenTransferTable.Columns.BLOCK_NUMBER,
            TokenTransferTable.Columns.VALUE,
            TokenTransferTable.Columns.TOKEN_ADDRESS
        ], where=f'{TokenTransferTable.Columns.TO_ADDRESS}=\'{redacted_multisig_address}\' \
            and {TokenTransferTable.Columns.FROM_ADDRESS} \
                in(\'{convex_addresses[0]}\',\'{convex_addresses[1]}\')')
        for transfer in transfers:
            token = Token(address=transfer['token_address'])
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
