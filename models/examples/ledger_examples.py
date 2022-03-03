from tokenize import Token
import credmark.model
from credmark.types import AddressDTO
from credmark.model.ledger.tables import (
    BlockTable,
    TransactionTable,
    ReceiptTable,
    TokenTransferTable,
    TokenTable,
    ContractTable,
    LogTable,
    TraceTable


)


@credmark.model.describe(slug='example-ledger-blocks', version="1.0")
class ExampleLedgerBlock(credmark.model.Model):

    """
    This model returns some information about the past 10 blocks
    """

    def run(self, input):

        return self.context.ledger.get_blocks(columns=[c for c in BlockTable.columns()],
                                              limit="10",
                                              order_by=BlockTable.Columns.NUMBER + " desc")


@credmark.model.describe(slug='example-ledger-transactions', version="1.0")
class ExampleLedgerTransactions(credmark.model.Model):

    """
    This model returns transactions hashes mined in the requested block.
    """

    def run(self, input):
        return self.context.ledger.get_transactions(columns=[TransactionTable.Columns.HASH],
                                                    where=f'{TransactionTable.Columns.BLOCK_TIMESTAMP}={self.context.block_number.timestamp}',
                                                    order_by=TransactionTable.Columns.GAS)


@credmark.model.describe(slug='example-ledger-receipts', version="1.0")
class ExampleLedgerReceipts(credmark.model.Model):

    """
    This model returns the library example for every day for the past 30 days
    """

    def run(self, input):
        return self.context.ledger.get_receipts(columns=[c for c in ReceiptTable.columns()],
                                                where=f'{ReceiptTable.Columns.BLOCK_NUMBER}={self.context.block_number}')


@credmark.model.describe(slug='example-ledger-token-transfers', version="1.0", input=AddressDTO)
class ExampleLedgerTokenTransfers(credmark.model.Model):

    """
    This model returns all ERC20 Token Transfers performed by an address
    """

    def run(self, input: AddressDTO):
        return self.context.ledger.get_erc20_transfers(columns=[c for c in TokenTransferTable.columns()],
                                                       where=f'{TokenTransferTable.Columns.FROM_ADDRESS}=\'{input.address.lower()}\' or \
                                                       {TokenTransferTable.Columns.TO_ADDRESS}=\'{input.address.lower()}\'',
                                                       order_by=f'{TokenTransferTable.Columns.BLOCK_NUMBER} desc')


@credmark.model.describe(slug='example-ledger-tokens', version="1.0")
class ExampleLedgerTokens(credmark.model.Model):

    """
    This model returns 100 ERC20 Tokens

    TODO: NOT IMPLEMENTED YET
    """

    def run(self, input: AddressDTO):
        return self.context.ledger.get_erc20_tokens(columns=[c for c in TokenTable.columns()],
                                                    limit="100",
                                                    order_by=TokenTable.Columns.BLOCK_NUMBER)


@credmark.model.describe(slug='example-ledger-logs', version="1.0")
class ExampleLedgerLogs(credmark.model.Model):

    """
    This model returns current blocks logs

    """

    def run(self, input: AddressDTO):
        return self.context.ledger.get_logs(columns=[c for c in LogTable.columns()],
                                            where=f'{LogTable.Columns.BLOCK_NUMBER}={self.context.block_number}')


@credmark.model.describe(slug='example-ledger-contracts', version="1.0")
class ExampleLedgerContracts(credmark.model.Model):

    """
    This model returns contracts.

    TODO: NOT IMPLEMENTED YET
    """

    def run(self, input: AddressDTO):
        return self.context.ledger.get_contracts(columns=[c for c in ContractTable.columns()], limit="100", order_by=ContractTable.Columns.BLOCK_NUMBER)


@credmark.model.describe(slug='example-ledger-traces', version="1.0")
class ExampleLedgerTraces(credmark.model.Model):

    """
    This model returns all traces mined in the current block
    """

    def run(self, input: AddressDTO):
        return self.context.ledger.get_traces(columns=[c for c in TraceTable.columns()],
                                              where=f'{TraceTable.Columns.BLOCK_NUMBER}={self.context.block_number}')
