
# pylint: disable=locally-disabled, line-too-long

from credmark.cmf.model import Model

from credmark.cmf.types import (
    Account
)

from credmark.cmf.types.ledger import (
    BlockTable,
    TransactionTable,
    ReceiptTable,
    TokenTransferTable,
    TokenTable,
    ContractTable,
    LogTable,
    TraceTable
)


@Model.describe(
    slug='example.ledger-blocks',
    version="1.0",
    developer="Credmark")
class ExampleLedgerBlock(Model):

    """
    This model returns some information about the past 10 blocks
    """

    def run(self, input):

        return self.context.ledger.get_blocks(columns=[BlockTable.Columns.DIFFICULTY],
                                              limit="10",
                                              order_by=BlockTable.Columns.NUMBER + " desc")


@Model.describe(slug='example.ledger-transactions', version="1.0")
class ExampleLedgerTransactions(Model):

    """
    This model returns transactions hashes mined in the requested block.
    """

    def run(self, input):
        return self.context.ledger.get_transactions(columns=[TransactionTable.Columns.HASH],
                                                    where=f'{TransactionTable.Columns.BLOCK_TIMESTAMP}={self.context.block_number.timestamp}',
                                                    order_by=TransactionTable.Columns.GAS)


@Model.describe(slug='example.ledger-transactions-gas-stats', version="1.0")
class ExampleLedgerTransactionsMaxGas(Model):
    """
    This model uses aggregate functions to return min, max, and average gas used
    in transactions up to the requested block.
    """

    def run(self, input):
        ledger = self.context.ledger
        return ledger.get_transactions(
            aggregates=[
                ledger.Aggregate(f'MIN({TransactionTable.Columns.GAS})', 'min_gas'),
                ledger.Aggregate(f'MAX({TransactionTable.Columns.GAS})', 'max_gas'),
                ledger.Aggregate(f'AVG({TransactionTable.Columns.GAS})', 'avg_gas')
            ])


@Model.describe(slug='example.ledger-receipts', version="1.0")
class ExampleLedgerReceipts(Model):

    """
    This model returns the library example for every day for the past 30 days
    """

    def run(self, input):
        return self.context.ledger.get_receipts(columns=[ReceiptTable.Columns.CONTRACT_ADDRESS,
                                                         ReceiptTable.Columns.CUMULATIVE_GAS_USED,
                                                         ReceiptTable.Columns.GAS_USED],
                                                where=f'{ReceiptTable.Columns.BLOCK_NUMBER}={self.context.block_number}')


@Model.describe(slug='example.ledger-token-transfers', version="1.0", input=Account)
class ExampleLedgerTokenTransfers(Model):

    """
    This model returns the 10 most recent ERC20 Token Transfers into or out of an address, with respect to blocknumber
    """

    def run(self, input: Account):
        return self.context.ledger.get_erc20_transfers(columns=list(TokenTransferTable.columns()),
                                                       where=f'{TokenTransferTable.Columns.FROM_ADDRESS}=\'{input.address.lower()}\' or \
                                                       {TokenTransferTable.Columns.TO_ADDRESS}=\'{input.address.lower()}\'',
                                                       order_by=f'{TokenTransferTable.Columns.BLOCK_NUMBER} desc',
                                                       limit="10")


@Model.describe(slug='example.ledger-tokens', version="1.0")
class ExampleLedgerTokens(Model):

    """
    This model returns 100 ERC20 Tokens

    TODO: NOT IMPLEMENTED YET
    """

    def run(self, input):
        return self.context.ledger.get_erc20_tokens(columns=list(TokenTable.columns()),
                                                    limit="100",
                                                    order_by=TokenTable.Columns.BLOCK_NUMBER)


@Model.describe(slug='example.ledger-logs', version="1.0")
class ExampleLedgerLogs(Model):

    """
    This model returns current blocks logs

    """

    def run(self, input):
        return self.context.ledger.get_logs(columns=[LogTable.Columns.ADDRESS,
                                                     LogTable.Columns.DATA],
                                            where=f'{LogTable.Columns.BLOCK_NUMBER}={self.context.block_number}')


@Model.describe(slug='example.ledger-contracts', version="1.0")
class ExampleLedgerContracts(Model):

    """
    This model returns contracts.

    TODO: NOT IMPLEMENTED YET
    """

    def run(self, input):
        return self.context.ledger.get_contracts(columns=list(ContractTable.columns()), limit="100", order_by=ContractTable.Columns.BLOCK_NUMBER)


@Model.describe(slug='example.ledger-traces', version="1.0")
class ExampleLedgerTraces(Model):

    """
    This model returns all traces mined in the current block
    """

    def run(self, input):
        return self.context.ledger.get_traces(columns=[TraceTable.Columns.BLOCK_NUMBER,
                                                       TraceTable.Columns.ERROR,
                                                       TraceTable.Columns.CALL_TYPE],
                                              where=f'{TraceTable.Columns.BLOCK_NUMBER}={self.context.block_number}')
