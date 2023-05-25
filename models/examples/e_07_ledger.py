from credmark.cmf.engine.mocks import ModelMock, ModelMockConfig
from credmark.cmf.model import Model

from models.tmp_abi_lookup import CMK_ADDRESS

from .dtos import ExampleLedgerOutput


@Model.describe(
    slug='example.ledger-blocks',
    version="1.3",
    developer="Credmark",
    display_name="Example - Ledger Blocks",
    description="This model demonstrates the functionality of Ledger's blocks",
    category='example',
    tags=['ledger'],
    output=ExampleLedgerOutput)
class ExampleLedgerBlocks(Model):
    def run(self, _):
        with self.context.ledger.Block as bl:
            ledger_output = bl.select(
                columns=[bl.DIFFICULTY],
                limit=10,
                order_by=bl.NUMBER.desc())

        output = ExampleLedgerOutput(
            title="7a. Example - Ledger Blocks",
            description="This model demonstrates the functionality of Ledger's blocks",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_07_ledger.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "components.html#ledger",
            ledger_output=ledger_output)

        output.log("To fetch some information about the past 10 blocks:")
        output.log_io(input="""
with self.context.ledger.Block as bl:
    ledger_output = bl.select(
        columns=[bl.DIFFICULTY],
        limit=10,
        order_by=bl.NUMBER.desc())
""",
                      output=ledger_output)

        return output


# pylint: disable=line-too-long
# This mock config can be used as mock data for the 'example.ledger-transactions'
# model below.
# Run with:
# credmark-dev run example.ledger-transactions -m models.examples.ledger_examples.ledger_transactions_mocks
ledger_transactions_mocks = ModelMockConfig(
    models={
        'ledger.transaction_data':
        ModelMock(
            {"data":
             [{"hash": "0x8862c4b7bc8b7d48f1671b413dd3b5e0b785d2001443ff3e13ba9602eddb7ef2"},
              {"hash": "0x9a1bbc5508e4fed1e7f08d791740dfb03aa8560965c78c92b6ee8fcc350021db"},
              {"hash": "0x00643f90efc4b949e4c8ed8abfa61d36b035297a996a066c967f64df3d2c7040"}]})
    })


@Model.describe(
    slug='example.ledger-transactions',
    version="1.3",
    developer="Credmark",
    display_name="Example - Ledger Transactions",
    description="This model demonstrates the functionality of Ledger's transactions",
    output=ExampleLedgerOutput)
class ExampleLedgerTransactions(Model):
    def run(self, _):
        with self.context.ledger.Transaction as txn:
            ledger_output = txn.select(
                columns=[txn.HASH],
                where=txn.BLOCK_TIMESTAMP.eq(
                    txn.field(self.context.block_number.timestamp).to_timestamp()),
                limit=10,
                order_by=txn.GAS)

            output = ExampleLedgerOutput(
                title="7b. Example - Ledger Transactions",
                description="This model demonstrates the functionality of Ledger's transactions",
                github_url="https://github.com/credmark/credmark-models-py/blob/main/"
                "models/examples/e_07_ledger.py",
                documentation_url="https://developer-docs.credmark.com/en/latest/"
                "components.html#ledger",
                ledger_output=ledger_output)

            output.log(
                "To fetch 10 transactions hashes mined in the requested block:")
            output.log_io(input="""
with self.context.ledger.Transaction as txn:
    ledger_output = txn.select(
        columns=[txn.HASH],
        where=txn.BLOCK_TIMESTAMP.eq(self.context.block_number.timestamp),
        limit=10,
        order_by=txn.GAS)
""",
                          output=ledger_output)

        return output


@Model.describe(slug='example.ledger-aggregates',
                version="1.3",
                developer="Credmark",
                display_name="Example - Ledger Aggregates",
                description="This model demonstrates the functionality of aggregates in Ledger",
                output=ExampleLedgerOutput)
class ExampleLedgerAggregates(Model):
    def run(self, _):
        with self.context.ledger.Transaction as txn:
            ledger_output = txn.select(
                aggregates=[(txn.GAS.min_(), 'min_gas'),
                            (txn.GAS.max_(), 'max_gas'),
                            (txn.GAS.avg_(), 'avg_gas')],
                where=txn.BLOCK_NUMBER.gt(self.context.block_number - 10000),
                bigint_cols=['min_gas', 'max_gas', 'avg_gas'])

        output = ExampleLedgerOutput(
            title="7c. Example - Ledger Aggregates",
            description="This model demonstrates the functionality of aggregates in Ledger",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_07_ledger.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "components.html#ledger",
            ledger_output=ledger_output)

        output.log("To fetch min, max, and average gas used in transactions "
                   "up to the requested block:")

        output.log_io(input="""
with self.context.ledger.Transaction as txn:
    ledger_output = txn.select(
                aggregates=[(txn.GAS.min_(), 'min_gas'),
                            (txn.GAS.max_(), 'max_gas'),
                            (txn.GAS.avg_(), 'avg_gas')],
                where=txn.BLOCK_NUMBER.gt(self.context.block_number - 10000),
                bigint_cols=['min_gas', 'max_gas', 'avg_gas'])
""",
                      output=ledger_output)

        return output


@Model.describe(
    slug='example.ledger-receipts',
    version="1.3",
    developer="Credmark",
    display_name="Example - Ledger Receipts",
    description="This model demonstrates the functionality of Ledger's receipts",
    output=ExampleLedgerOutput)
class ExampleLedgerReceipts(Model):
    def run(self, _):
        with self.context.ledger.Receipt as rec:
            ledger_output = rec.select(
                columns=[rec.CONTRACT_ADDRESS,
                         rec.CUMULATIVE_GAS_USED,
                         rec.GAS_USED],
                where=rec.BLOCK_NUMBER.eq(self.context.block_number),
                limit=10,
                order_by=rec.CONTRACT_ADDRESS.desc())

        output = ExampleLedgerOutput(
            title="7d. Example - Ledger Receipts",
            description="This model demonstrates the functionality of Ledger's receipts",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_07_ledger.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "components.html#ledger",
            ledger_output=ledger_output)

        output.log("To fetch 10 receipts in the requested block:")

        output.log_io(input="""
with self.context.ledger.Receipt as rec:
    ledger_output = rec.select(
        columns=[rec.CONTRACT_ADDRESS,
                 rec.CUMULATIVE_GAS_USED,
                 rec.GAS_USED],
        where=rec.BLOCK_NUMBER.eq(self.context.block_number),
        limit=10,
        order_by=rec.CONTRACT_ADDRESS.desc())
""",
                      output=ledger_output)

        return output


@Model.describe(
    slug='example.ledger-token-transfers',
    version="1.3",
    developer="Credmark",
    display_name="Example - Ledger Token transfers",
    description="This model demonstrates the functionality of Ledger's ERC20 token transfers",
    output=ExampleLedgerOutput)
class ExampleLedgerTokenTransfers(Model):

    def run(self, _):
        with self.context.ledger.TokenTransfer as ttf:
            ledger_output = ttf.select(
                columns=ttf.columns,
                where=ttf.FROM_ADDRESS.eq(CMK_ADDRESS).or_(
                    ttf.TO_ADDRESS.eq(CMK_ADDRESS)
                ),
                order_by=ttf.BLOCK_NUMBER.desc())

        output = ExampleLedgerOutput(
            title="7e. Example - Ledger Token transfers",
            description="This model demonstrates the functionality of Ledger's "
            "ERC20 token transfers",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_07_ledger.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "components.html#ledger",
            ledger_output=ledger_output)

        output.log("To fetch 10 most recent ERC20 Token Transfers into or out of an address, "
                   "with respect to blocknumber:")

        output.log_io(input="""
with self.context.ledger.TokenTransfer as ttf:
    ledger_output = ttf.select(
        columns=ttf.columns,
        where=ttf.FROM_ADDRESS.eq(CMK_ADDRESS).or_(
            ttf.TO_ADDRESS.eq(CMK_ADDRESS)
        ),
        order_by=ttf.BLOCK_NUMBER.desc(),
        limit=10)
""",
                      output=ledger_output)

        with self.context.ledger.TokenBalance as tb:
            ledger_output = tb.select(
                columns=tb.columns,
                where=tb.FROM_ADDRESS.eq(CMK_ADDRESS).or_(
                    tb.TO_ADDRESS.eq(CMK_ADDRESS)
                ),
                order_by=tb.BLOCK_NUMBER.desc())

        return output


@Model.describe(
    slug='example.ledger-tokens',
    version="1.3",
    developer="Credmark",
    display_name="Example - Ledger Tokens",
    description="This model demonstrates the functionality of Ledger's ERC20 tokens",
    output=ExampleLedgerOutput)
class ExampleLedgerTokens(Model):
    def run(self, _):
        with self.context.ledger.Token as q:
            ledger_output = q.select(columns=q.columns,
                                     limit=100,
                                     order_by=q.BLOCK_NUMBER.asc().comma_(q.ADDRESS.asc()))

        output = ExampleLedgerOutput(
            title="7f. Example - Ledger Tokens",
            description="This model demonstrates the functionality of Ledger's ERC20 tokens",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_07_ledger.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "components.html#ledger",
            ledger_output=ledger_output)

        output.log("To fetch 100 ERC20 Tokens:")
        output.log_io(input="""
with ledger.Token as q:
    ledger_output = q.select(columns=list(q.columns()),
                                limit=100,
                                order_by=q.BLOCK_NUMBER)""",
                      output=ledger_output)

        return output


@Model.describe(
    slug='example.ledger-logs',
    version="1.3",
    developer="Credmark",
    display_name="Example - Ledger Logs",
    description="This model demonstrates the functionality of Ledger's logs",
    output=ExampleLedgerOutput)
class ExampleLedgerLogs(Model):
    def run(self, _):
        ledger = self.context.ledger
        with ledger.Log as q:
            ledger_output = q.select(
                columns=[q.ADDRESS,
                         q.DATA],
                where=q.BLOCK_NUMBER.eq(self.context.block_number),
                limit=10,
                order_by=f'{q.ADDRESS} desc')

        output = ExampleLedgerOutput(
            title="7g. Example - Ledger Logs",
            description="This model demonstrates the functionality of Ledger's logs",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_07_ledger.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "components.html#ledger",
            ledger_output=ledger_output)

        output.log("To fetch 10 logs for the current block:")

        output.log_io(input="""
with ledger.Log as q:
    ledger_output = q.select(
        columns=[q.ADDRESS,
                    q.DATA],
        where=q.BLOCK_NUMBER.eq(self.context.block_number),
        limit=10,
        order_by=f'{q.ADDRESS} desc')""",
                      output=ledger_output)

        return output


@Model.describe(
    slug='example.ledger-contracts',
    version="1.3",
    developer="Credmark",
    display_name="Example - Ledger Contracts",
    description="This model demonstrates the functionality of Ledger's contracts",
    output=ExampleLedgerOutput)
class ExampleLedgerContracts(Model):
    def run(self, _):
        with self.context.ledger.Contract as q:
            ledger_output = q.select(
                columns=q.columns,
                limit=100,
                order_by=q.BLOCK_NUMBER)

        output = ExampleLedgerOutput(
            title="7h. Example - Ledger Contracts",
            description="This model demonstrates the functionality of Ledger's contracts",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_07_ledger.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "components.html#ledger",
            ledger_output=ledger_output)

        output.log("To fetch 100 Contracts:")

        output.log_io(input="""
with self.context.ledger.Contract as q:
    ledger_output = q.select(
        columns=q.columns,
        limit=100,
        order_by=q.BLOCK_NUMBER)
""",
                      output=ledger_output)

        return output


@Model.describe(
    slug='example.ledger-traces',
    version="1.3",
    developer="Credmark",
    display_name="Example - Ledger Traces",
    description="This model demonstrates the functionality of Ledger's traces",
    output=ExampleLedgerOutput)
class ExampleLedgerTraces(Model):

    """
    This model returns all traces mined in the current block
    """

    def run(self, _):
        with self.context.ledger.Trace as q:
            ledger_output = q.select(
                columns=[q.BLOCK_NUMBER,
                         q.ERROR,
                         q.CALL_TYPE],
                where=q.BLOCK_NUMBER.eq(self.context.block_number),
                limit=100,
                order_by=q.FROM_ADDRESS)

        output = ExampleLedgerOutput(
            title="7i. Example - Ledger Traces",
            description="This model demonstrates the functionality of Ledger's traces",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_07_ledger.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "components.html#ledger",
            ledger_output=ledger_output)

        output.log("To fetch 100 traces for the current block:")

        output.log_io(input="""
with self.context.ledger.Trace as q:
    ledger_output = q.select(
        columns=[q.BLOCK_NUMBER,
                 q.ERROR,
                 q.CALL_TYPE],
        where=q.BLOCK_NUMBER.eq(self.context.block_number),
        limit=100,
        order_by=q.FROM_ADDRESS)
""",
                      output=ledger_output)

        return output
