# pylint:disable=line-too-long
from typing import List, Union

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import (
    Account,
    Address,
    BlockNumber,
    JoinType,
    NativeToken,
    PriceWithQuote,
    Token,
)
from credmark.dto import DTO, DTOField, IterableListGenericDTO, PrivateAttr


class TokenNetflowBlockInput(DTO):
    netflow_address: Address = DTOField(..., description="Netflow address")
    block_number: int = DTOField(
        description=(
            "Positive for a block earlier than the current one "
            "or negative or zero for an interval. "
            "Both excludes the start block."
        )
    )

    address: Address
    include_price: bool = DTOField(default=True, description="Include price quote")

    @property
    def token(self):
        return Token(self.address)

    def __init__(self, **data) -> None:
        if "address" not in data:
            data["address"] = Token(**data).address
        super().__init__(**data)

    class Config:
        schema_extra = {
            "example": {
                "address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9",
                "block_number": -1000,
                "netflow_address": "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43",
            }
        }


class TokenNetflowBlockRange(DTO):
    inflow: int
    inflow_scaled: float
    outflow: int
    outflow_scaled: float
    netflow: int
    netflow_scaled: float
    price_last: Union[float, None]
    inflow_value_last: Union[float, None]
    outflow_value_last: Union[float, None]
    netflow_value_last: Union[float, None]
    from_block: int
    from_timestamp: int
    to_block: int
    to_timestamp: int


class TokenNetflowOutput(TokenNetflowBlockRange):
    address: Address


@Model.describe(
    slug="token.netflow-block",
    version="1.5",
    display_name="Token netflow",
    description="The Current Credmark Supported netflow algorithm",
    category="protocol",
    tags=["token"],
    input=TokenNetflowBlockInput,
    output=TokenNetflowOutput,
)
class TokenNetflowBlock(Model):
    def run(self, input: TokenNetflowBlockInput) -> TokenNetflowOutput:
        token_address = input.address
        old_block = input.block_number

        if old_block >= 0:
            if old_block > self.context.block_number:
                raise ModelRunError(
                    f"input {input.block_number=} shall be earlier "
                    f"than the current block {self.context.block_number}"
                )
        else:
            old_block = self.context.block_number + old_block

        to_block = self.context.block_number
        from_block = BlockNumber(old_block + 1)

        native_token = NativeToken()
        if input.address == native_token.address:
            input_token = native_token
            with self.context.ledger.Transaction as q:
                df = q.select(
                    aggregates=[
                        (
                            (
                                f"SUM(CASE WHEN {q.TO_ADDRESS.eq(input.netflow_address)} "
                                f"THEN {q.VALUE} ELSE 0::INTEGER END)"
                            ),
                            "inflow",
                        ),
                        (
                            (
                                f"SUM(CASE WHEN {q.FROM_ADDRESS.eq(input.netflow_address)} "
                                f"THEN {q.VALUE} ELSE 0::INTEGER END)"
                            ),
                            "outflow",
                        ),
                        (
                            (
                                f"SUM(CASE WHEN {q.TO_ADDRESS.eq(input.netflow_address)} "
                                f"THEN {q.VALUE} ELSE {q.VALUE.neg_()} END)"
                            ),
                            "netflow",
                        ),
                    ],
                    where=q.BLOCK_NUMBER.gt(old_block).and_(
                        q.TO_ADDRESS.eq(input.netflow_address)
                        .or_(q.FROM_ADDRESS.eq(input.netflow_address))
                        .parentheses_()
                    ),
                ).to_dataframe()
        else:
            input_token = input.token
            with self.context.ledger.TokenTransfer as q:
                df = q.select(
                    aggregates=[
                        (
                            (
                                f"SUM(CASE WHEN {q.TO_ADDRESS.eq(input.netflow_address)} "
                                f"THEN {q.RAW_AMOUNT} ELSE 0::INTEGER END)"
                            ),
                            "inflow",
                        ),
                        (
                            (
                                f"SUM(CASE WHEN {q.FROM_ADDRESS.eq(input.netflow_address)} "
                                f"THEN {q.RAW_AMOUNT} ELSE 0::INTEGER END)"
                            ),
                            "outflow",
                        ),
                        (
                            (
                                f"SUM(CASE WHEN {q.TO_ADDRESS.eq(input.netflow_address)} "
                                f"THEN {q.RAW_AMOUNT} ELSE {q.RAW_AMOUNT.neg_()} END)"
                            ),
                            "netflow",
                        ),
                    ],
                    where=q.BLOCK_NUMBER.gt(old_block)
                    .and_(q.TOKEN_ADDRESS.eq(token_address))
                    .and_(
                        q.TO_ADDRESS.eq(input.netflow_address)
                        .or_(q.FROM_ADDRESS.eq(input.netflow_address))
                        .parentheses_()
                    ),
                    bigint_cols=["inflow", "outflow", "netflow"],
                ).to_dataframe()

        df = df.fillna(0)
        inflow = df.inflow.values[0]
        inflow = inflow if inflow is not None else 0
        inflow_scaled = input_token.scaled(inflow)
        outflow = df.outflow.values[0]
        outflow = outflow if outflow is not None else 0
        outflow_scaled = input_token.scaled(outflow)
        netflow = df.netflow.values[0]
        netflow = netflow if netflow is not None else 0
        netflow_scaled = input_token.scaled(netflow)

        price_last = None
        inflow_value_last = None
        outflow_value_last = None
        netflow_value_last = None
        if input.include_price:
            price_last = self.context.models.price.quote(
                base=input_token, return_type=PriceWithQuote
            ).price  # type: ignore
            inflow_value_last = inflow_scaled * price_last
            outflow_value_last = outflow_scaled * price_last
            netflow_value_last = netflow_scaled * price_last

        output = TokenNetflowOutput(
            address=input.address,
            inflow=inflow,
            inflow_scaled=inflow_scaled,
            outflow=outflow,
            outflow_scaled=outflow_scaled,
            netflow=netflow,
            netflow_scaled=netflow_scaled,
            price_last=price_last,
            inflow_value_last=inflow_value_last,
            outflow_value_last=outflow_value_last,
            netflow_value_last=netflow_value_last,
            from_block=from_block,
            from_timestamp=from_block.timestamp,
            to_block=to_block,
            to_timestamp=to_block.timestamp,
        )

        return output


class TokenNetflowWindowInput(DTO):
    netflow_address: Address = DTOField(..., description="Netflow address")
    window: str = DTOField(..., description='a string defining a time window, ex. "30 day"')
    address: Address
    include_price: bool = DTOField(default=True, description="Include price quote")

    @property
    def token(self):
        return Token(self.address)

    def __init__(self, **data) -> None:
        if "address" not in data:
            data["address"] = Token(**data).address
        super().__init__(**data)

    class Config:
        schema_extra = {
            "example": {
                "address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9",
                "window": "1 day",
                "netflow_address": "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43",
            }
        }


@Model.describe(
    slug="token.netflow-window",
    version="1.4",
    display_name="Token netflow",
    description="The current Credmark supported netflow algorithm",
    category="protocol",
    tags=["token"],
    input=TokenNetflowWindowInput,
    output=TokenNetflowOutput,
)
class TokenOutflowWindow(Model):
    def run(self, input: TokenNetflowWindowInput) -> TokenNetflowOutput:
        window_in_seconds = self.context.historical.to_seconds(input.window)
        old_block_timestamp = self.context.block_number.timestamp - window_in_seconds
        old_block = BlockNumber.from_timestamp(old_block_timestamp)

        return self.context.run_model(
            "token.netflow-block",
            input=TokenNetflowBlockInput(
                address=input.address,
                netflow_address=input.netflow_address,
                block_number=old_block,
                include_price=input.include_price,
            ),
            return_type=TokenNetflowOutput,
        )


class TokenNetflowSegmentBlockInput(TokenNetflowBlockInput):
    n: int = DTOField(2, ge=1, description="Number of interval to count")


class TokenNetflowSegmentOutput(DTO):
    address: Address
    netflows: List[TokenNetflowBlockRange]


@Model.describe(
    slug="token.netflow-segment-block",
    version="1.5",
    display_name="Token netflow by segment by block",
    description="The Current Credmark Supported netflow algorithm",
    category="protocol",
    tags=["token"],
    input=TokenNetflowSegmentBlockInput,
    output=TokenNetflowSegmentOutput,
)
class TokenVolumeSegmentBlock(Model):
    def run(self, input: TokenNetflowSegmentBlockInput) -> TokenNetflowSegmentOutput:
        token_address = input.address
        old_block = input.block_number

        if old_block >= 0:
            if old_block > self.context.block_number:
                raise ModelRunError(
                    f"input {input.block_number=} shall be earlier "
                    f"than the current block {self.context.block_number}"
                )
            block_seg = self.context.block_number - old_block
        else:
            block_seg = -old_block

        block_start = self.context.block_number - block_seg * input.n
        if block_start < 0:
            raise ModelRunError(
                "Start block shall be larger than zero: "
                f"{self.context.block_number} - {block_seg} * {input.n} = {block_start}"
            )

        native_token = NativeToken()
        token_address = input.address
        old_block = input.block_number

        if old_block >= 0:
            if old_block > self.context.block_number:
                raise ModelRunError(
                    f"input {input.block_number=} shall be earlier "
                    f"than the current block {self.context.block_number}"
                )
            block_seg = self.context.block_number - old_block
        else:
            block_seg = -old_block

        block_end = int(self.context.block_number)
        block_start = block_end - block_seg * input.n
        if block_start < 0:
            raise ModelRunError(
                "Start block shall be larger than zero: "
                f"{block_end} - {block_seg} * {input.n} = {block_start}"
            )

        native_token = NativeToken()
        if token_address == native_token.address:
            input_token = native_token
            with self.context.ledger.Transaction.as_("t") as t, self.context.ledger.Block.as_(
                "s"
            ) as s, self.context.ledger.Block.as_("e") as e:
                df = s.select(
                    aggregates=[
                        (s.NUMBER, "from_block"),
                        (s.TIMESTAMP, "from_timestamp"),
                        (e.NUMBER, "to_block"),
                        (e.TIMESTAMP, "to_timestamp"),
                        (
                            (
                                f"SUM(CASE WHEN {t.TO_ADDRESS.eq(input.netflow_address)} "
                                f"THEN {t.VALUE} ELSE 0::INTEGER END)"
                            ),
                            "inflow",
                        ),
                        (
                            (
                                f"SUM(CASE WHEN {t.FROM_ADDRESS.eq(input.netflow_address)} "
                                f"THEN {t.VALUE} ELSE 0::INTEGER END)"
                            ),
                            "outflow",
                        ),
                        (
                            (
                                f"SUM(CASE WHEN {t.TO_ADDRESS.eq(input.netflow_address)} "
                                f"THEN {t.VALUE} ELSE {t.VALUE.neg_()} END)"
                            ),
                            "netflow",
                        ),
                    ],
                    joins=[
                        (e, e.NUMBER.eq(s.NUMBER.plus_(str(block_seg)).minus_(str(1)))),
                        (
                            JoinType.LEFT_OUTER,
                            t,
                            t.field(f"{t.BLOCK_NUMBER} between {s.NUMBER} and {e.NUMBER}").and_(
                                t.TO_ADDRESS.eq(input.netflow_address)
                                .or_(t.FROM_ADDRESS.eq(input.netflow_address))
                                .parentheses_()
                            ),
                        ),
                    ],
                    group_by=[s.NUMBER, s.TIMESTAMP, e.NUMBER, e.TIMESTAMP],
                    where=s.NUMBER.gt(block_start).and_(s.NUMBER.le(block_end)),
                    having=(
                        s.NUMBER.ge(block_start).and_(
                            s.NUMBER.lt(block_end).and_(
                                f"MOD({e.NUMBER} - {block_start}, {block_seg}) = 0"
                            )
                        )
                    ),
                    order_by=s.NUMBER.asc(),
                ).to_dataframe()

                from_iso8601_str = t.field("").from_iso8601_str
        else:
            input_token = input.token
            with self.context.ledger.TokenTransfer.as_("t") as t, self.context.ledger.Block.as_(
                "s"
            ) as s, self.context.ledger.Block.as_("e") as e:
                df = s.select(
                    aggregates=[
                        (s.NUMBER, "from_block"),
                        (s.TIMESTAMP, "from_timestamp"),
                        (e.NUMBER, "to_block"),
                        (e.TIMESTAMP, "to_timestamp"),
                        (
                            (
                                f"SUM(CASE WHEN {t.TO_ADDRESS.eq(input.netflow_address)} "
                                f"THEN {t.RAW_AMOUNT} ELSE 0::INTEGER END)"
                            ),
                            "inflow",
                        ),
                        (
                            (
                                f"SUM(CASE WHEN {t.FROM_ADDRESS.eq(input.netflow_address)} "
                                f"THEN {t.RAW_AMOUNT} ELSE 0::INTEGER END)"
                            ),
                            "outflow",
                        ),
                        (
                            (
                                f"SUM(CASE WHEN {t.TO_ADDRESS.eq(input.netflow_address)} "
                                f"THEN {t.RAW_AMOUNT} ELSE {t.RAW_AMOUNT.neg_()} END)"
                            ),
                            "netflow",
                        ),
                    ],
                    joins=[
                        (e, e.NUMBER.eq(s.NUMBER.plus_(str(block_seg)).minus_(str(1)))),
                        (
                            JoinType.LEFT_OUTER,
                            t,
                            t.field(f"{t.BLOCK_NUMBER} between {s.NUMBER} and {e.NUMBER}")
                            .and_(t.TOKEN_ADDRESS.eq(token_address))
                            .and_(
                                t.TO_ADDRESS.eq(input.netflow_address)
                                .or_(t.FROM_ADDRESS.eq(input.netflow_address))
                                .parentheses_()
                            ),
                        ),
                    ],
                    group_by=[s.NUMBER, s.TIMESTAMP, e.NUMBER, e.TIMESTAMP],
                    where=s.NUMBER.ge(block_start).and_(s.NUMBER.lt(block_end)),
                    having=f"MOD({e.NUMBER} - {block_start}, {block_seg}) = 0",
                    order_by=s.NUMBER.asc(),
                ).to_dataframe()

                from_iso8601_str = t.field("").from_iso8601_str

        df["from_block"] = df["from_block"].astype("int")
        df["to_block"] = df["to_block"].astype("int")
        df["inflow"] = df["inflow"].astype("float64")
        df["outflow"] = df["outflow"].astype("float64")
        df["netflow"] = df["netflow"].astype("float64")

        df["from_timestamp"] = df["from_timestamp"].apply(from_iso8601_str)
        df["to_timestamp"] = df["to_timestamp"].apply(from_iso8601_str)

        df = df.fillna(0)
        netflows = []
        for _, r in df.iterrows():
            inflow = r["inflow"]
            inflow = inflow if inflow is not None else 0
            inflow_scaled = input_token.scaled(inflow)
            outflow = r["outflow"]
            outflow = outflow if outflow is not None else 0
            outflow_scaled = input_token.scaled(outflow)
            netflow = r["netflow"]
            netflow = netflow if netflow is not None else 0
            netflow_scaled = input_token.scaled(netflow)

            price_last = None
            inflow_value_last = None
            outflow_value_last = None
            netflow_value_last = None
            if input.include_price:
                price_last = (
                    self.context.models(block_number=int(r["to_block"])).price.quote(
                        base=input_token, return_type=PriceWithQuote
                    )
                ).price  # type: ignore
                inflow_value_last = inflow_scaled * price_last
                outflow_value_last = outflow_scaled * price_last
                netflow_value_last = netflow_scaled * price_last

            netflow = TokenNetflowOutput(
                address=input.address,
                inflow=inflow,
                inflow_scaled=inflow_scaled,
                outflow=outflow,
                outflow_scaled=outflow_scaled,
                netflow=netflow,
                netflow_scaled=netflow_scaled,
                price_last=price_last,
                inflow_value_last=inflow_value_last,
                outflow_value_last=outflow_value_last,
                netflow_value_last=netflow_value_last,
                from_block=r["from_block"],
                from_timestamp=r["from_timestamp"],
                to_block=r["to_block"],
                to_timestamp=r["to_timestamp"],
            )
            netflows.append(netflow)

        output = TokenNetflowSegmentOutput(address=input.address, netflows=netflows)

        return output


class TokenNetflowSegmentWindowInput(TokenNetflowWindowInput):
    n: int = DTOField(2, ge=1, description="Number of interval to count")

    class Config:
        schema_extra = {
            "example": {
                "address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9",
                "netflow_address": "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43",
                "window": "1 day",
                "n": 4,
            }
        }


@Model.describe(
    slug="token.netflow-segment-window",
    version="1.4",
    display_name="Token netflow by segment in window",
    description="The current Credmark supported netflow algorithm",
    category="protocol",
    tags=["token"],
    input=TokenNetflowSegmentWindowInput,
    output=TokenNetflowSegmentOutput,
)
class TokenNetflowSegmentWindow(Model):
    def run(self, input: TokenNetflowSegmentWindowInput) -> TokenNetflowSegmentOutput:
        window_in_seconds = self.context.historical.to_seconds(input.window)
        old_block_timestamp = self.context.block_number.timestamp - window_in_seconds
        old_block = BlockNumber.from_timestamp(old_block_timestamp)

        return self.context.run_model(
            "token.netflow-segment-block",
            input=TokenNetflowSegmentBlockInput(
                address=input.address,
                netflow_address=input.netflow_address,
                block_number=old_block,
                n=input.n,
                include_price=input.include_price,
            ),
            return_type=TokenNetflowSegmentOutput,
        )


class SupplyProvider(DTO):
    class Block(DTO):
        block_number: int
        timestamp: str

    address: Address = DTOField(description="Address of holder")
    supply: int = DTOField(description="Supply provided by account")
    supply_scaled: float = DTOField(description="Supply scaled to token decimals for account")
    first_transfer_block: Block
    last_transfer_block: Block


class SupplyProvidersOutput(IterableListGenericDTO[SupplyProvider]):
    providers: list[SupplyProvider] = DTOField(default=[], description="List of supply prviders")
    total_providers: int = DTOField(description="Total number of supply providers")

    _iterator: str = PrivateAttr("holders")


class GetSupplyProvidersInput(Token):
    account: Account = DTOField(
        description="Filter for this account.",
    )
    limit: int = DTOField(100, gt=0, description="Limit the number of holders that are returned")
    offset: int = DTOField(
        0, ge=0, description="Omit a specified number of holders from beginning of result set"
    )
    min_amount: int = DTOField(
        -1,
        description="Minimum supply for a provider to be included. Default is -1, a minimum \
            balance greater than 0",
    )
    max_amount: int = DTOField(
        -1, description="Maximum supply for a provider to be included. Default is -1, no maximum"
    )


@Model.describe(
    slug="token.supply-providers",
    version="0.1",
    display_name="Token supply providers",
    description="Supply providers of a token for an account",
    category="protocol",
    tags=["token"],
    input=GetSupplyProvidersInput,
    output=SupplyProvidersOutput,
)
class TokenGetSupplyProviders(Model):
    def run(self, input: GetSupplyProvidersInput) -> SupplyProvidersOutput:
        with self.context.ledger.TokenBalance as q:
            order_by = q.field("supply").dquote().desc()
            having = (
                q.RAW_AMOUNT.as_numeric().sum_().gt(0)
                if input.min_amount == -1
                else q.RAW_AMOUNT.as_numeric().sum_().ge(input.unscaled(input.min_amount))
            )

            if input.max_amount != -1:
                having = having.and_(
                    q.RAW_AMOUNT.as_numeric().sum_().le(input.unscaled(input.max_amount))
                )

            where = q.TOKEN_ADDRESS.eq(input.address).and_(q.ADDRESS.eq(input.account.address))

            df = q.select(
                aggregates=[
                    (q.RAW_AMOUNT.as_numeric().sum_(), "supply"),
                    (q.BLOCK_NUMBER.min_(), "first_block_number"),
                    (q.BLOCK_TIMESTAMP.min_(), "first_block_timestamp"),
                    (q.BLOCK_NUMBER.max_(), "last_block_number"),
                    (q.BLOCK_TIMESTAMP.max_(), "last_block_timestamp"),
                    ("COUNT(*) OVER()", "total_suppliers"),
                ],
                where=where,
                group_by=[q.COUNTERPARTY_ADDRESS],
                having=having,
                order_by=order_by.comma_(q.COUNTERPARTY_ADDRESS),
                limit=input.limit,
                offset=input.offset,
                bigint_cols=["supply"],
                analytics_mode=True,
            ).to_dataframe()

            if df.empty:
                total_suppliers = 0
            else:
                total_suppliers = df["total_suppliers"].values[0]
                if total_suppliers is None:
                    total_suppliers = 0

            return SupplyProvidersOutput(
                providers=[
                    SupplyProvider(
                        address=Address(row["counterparty_address"]),
                        supply=row["supply"],
                        supply_scaled=input.scaled(row["supply"]),
                        first_transfer_block=SupplyProvider.Block(
                            block_number=row["first_block_number"],
                            timestamp=row["first_block_timestamp"],
                        ),
                        last_transfer_block=SupplyProvider.Block(
                            block_number=row["last_block_number"],
                            timestamp=row["last_block_timestamp"],
                        ),
                    )
                    for _, row in df.iterrows()
                ],
                total_providers=total_suppliers,
            )
