from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelInputError
from credmark.cmf.types import Address, Contract
from credmark.dto import DTO, DTOField, IterableListGenericDTO, PrivateAttr


class TxAccountsInput(Contract):
    limit: int = DTOField(100, gt=0, description="Limit the number of holders that are returned")
    offset: int = DTOField(
        0, ge=0, description="Omit a specified number of holders from beginning of result set"
    )
    order_by: str = DTOField("most_transactions", description="Sort by count or newest")
    start_block_number: float = DTOField(
        -1,
        description="Minimum unscaled balance for a holder to be included. Default is -1, a minimum \
            balance greater than 0",
    )


class TxAccount(DTO):
    class Block(DTO):
        block_number: int
        timestamp: str

    address: Address = DTOField(description="Address of holder")
    count: int = DTOField(description="Number of transactions")
    first_transaction_block: Block
    last_transaction_block: Block


class TxAccountsOutput(IterableListGenericDTO[TxAccount]):
    accounts: list[TxAccount] = DTOField(default=[], description="List of accounts")
    total_accounts: int = DTOField(description="Total number of accounts")

    _iterator: str = PrivateAttr("accounts")


@Model.describe(
    slug="transaction.accounts",
    version="0.1",
    display_name="Transaction accounts",
    description="Wallets that interacted with a smart contract",
    category="protocol",
    tags=["token"],
    input=TxAccountsInput,
    output=TxAccountsOutput,
)
class TokenHolders(Model):
    def run(self, input: TxAccountsInput) -> TxAccountsOutput:
        with self.context.ledger.Transaction as q:
            if input.order_by == "newest":
                order_by = q.field("first_block_number").dquote().desc()
            elif input.order_by == "oldest":
                order_by = q.field("first_block_number").dquote().asc()
            elif input.order_by == "least_transactions":
                order_by = q.field("count").dquote().desc()
            elif input.order_by == "most_transactions":
                order_by = q.field("count").dquote().asc()
            else:
                raise ModelInputError("Invalid order by")

            where = q.TO_ADDRESS.eq(input.address)
            if input.start_block_number != -1:
                where = where.and_(q.BLOCK_NUMBER.ge(input.start_block_number))

            df = q.select(
                aggregates=[
                    ("COUNT(*)", "count"),
                    (q.BLOCK_NUMBER.min_(), "first_block_number"),
                    (q.BLOCK_TIMESTAMP.min_(), "first_block_timestamp"),
                    (q.BLOCK_NUMBER.max_(), "last_block_number"),
                    (q.BLOCK_TIMESTAMP.max_(), "last_block_timestamp"),
                    ("COUNT(*) OVER()", "total_accounts"),
                ],
                where=where,
                group_by=[q.FROM_ADDRESS],
                order_by=order_by.comma_(q.FROM_ADDRESS),
                limit=input.limit,
                offset=input.offset,
                bigint_cols=["count", "total_accounts"],
                analytics_mode=True,
            ).to_dataframe()

            if df.empty:
                total_accounts = 0
            else:
                total_accounts = df["total_accounts"].values[0]
                if total_accounts is None:
                    total_accounts = 0

            return TxAccountsOutput(
                accounts=[
                    TxAccount(
                        address=Address(row["from_address"]),
                        count=row["count"],
                        first_transaction_block=TxAccount.Block(
                            block_number=row["first_block_number"],
                            timestamp=row["first_block_timestamp"],
                        ),
                        last_transaction_block=TxAccount.Block(
                            block_number=row["last_block_number"],
                            timestamp=row["last_block_timestamp"],
                        ),
                    )
                    for _, row in df.iterrows()
                ],
                total_accounts=total_accounts,
            )
