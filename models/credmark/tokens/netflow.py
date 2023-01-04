# pylint:disable=line-too-long
from typing import List, Union
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import (Address, BlockNumber, JoinType,
                                NativeToken, PriceWithQuote, Token)
from credmark.dto import DTO, DTOField


class TokenNetflowBlockInput(DTO):
    netflow_address: Address = DTOField(..., description="Netflow address")
    block_number: int = DTOField(
        description=('Positive for a block earlier than the current one '
                     'or negative or zero for an interval. '
                     'Both excludes the start block.'))

    address: Address
    include_price: bool = DTOField(default=True, description='Include price quote')

    @property
    def token(self):
        return Token(self.address)

    def __init__(self, **data) -> None:
        if 'address' not in data:
            data['address'] = Token(**data).address
        super().__init__(**data)


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


@Model.describe(slug='token.netflow-block',
                version='1.4',
                display_name='Token netflow',
                description='The Current Credmark Supported netflow algorithm',
                category='protocol',
                tags=['token'],
                input=TokenNetflowBlockInput,
                output=TokenNetflowOutput)
class TokenNetflowBlock(Model):
    def run(self, input: TokenNetflowBlockInput) -> TokenNetflowOutput:
        token_address = input.address
        old_block = input.block_number

        if old_block >= 0:
            if old_block > self.context.block_number:
                raise ModelRunError(f'input {input.block_number=} shall be earlier '
                                    f'than the current block {self.context.block_number}')
        else:
            old_block = self.context.block_number + old_block

        to_block = self.context.block_number
        from_block = BlockNumber(old_block+1)

        native_token = NativeToken()
        if input.address == native_token.address:
            input_token = native_token
            with self.context.ledger.Transaction as q:
                df = q.select(
                    aggregates=[
                        ((f'SUM(CASE WHEN {q.TO_ADDRESS.eq(input.netflow_address)} '
                          f'THEN {q.VALUE} ELSE 0::INTEGER END)'), 'inflow'),
                        ((f'SUM(CASE WHEN {q.FROM_ADDRESS.eq(input.netflow_address)} '
                          f'THEN {q.VALUE} ELSE 0::INTEGER END)'), 'outflow'),
                        ((f'SUM(CASE WHEN {q.TO_ADDRESS.eq(input.netflow_address)} '
                          f'THEN {q.VALUE} ELSE {q.VALUE.neg_()} END)'), 'netflow')],
                    where=q.BLOCK_NUMBER.gt(old_block)
                    .and_(q.TO_ADDRESS.eq(input.netflow_address)
                          .or_(q.FROM_ADDRESS.eq(input.netflow_address)).parentheses_())
                ).to_dataframe()
        else:
            input_token = input.token
            with self.context.ledger.TokenTransfer as q:
                df = q.select(
                    aggregates=[
                        ((f'SUM(CASE WHEN {q.TO_ADDRESS.eq(input.netflow_address)} '
                          f'THEN {q.VALUE} ELSE 0::INTEGER END)'), 'inflow'),
                        ((f'SUM(CASE WHEN {q.FROM_ADDRESS.eq(input.netflow_address)} '
                          f'THEN {q.VALUE} ELSE 0::INTEGER END)'), 'outflow'),
                        ((f'SUM(CASE WHEN {q.TO_ADDRESS.eq(input.netflow_address)} '
                          f'THEN {q.VALUE} ELSE {q.VALUE.neg_()} END)'), 'netflow')],
                    where=q.BLOCK_NUMBER.gt(old_block)
                    .and_(q.TOKEN_ADDRESS.eq(token_address))
                    .and_(q.TO_ADDRESS.eq(input.netflow_address)
                          .or_(q.FROM_ADDRESS.eq(input.netflow_address)).parentheses_()),
                    bigint_cols=['inflow', 'outflow', 'netflow']
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
                base=input_token,
                return_type=PriceWithQuote).price  # type: ignore
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
            to_timestamp=to_block.timestamp
        )

        return output


class TokenNetflowWindowInput(DTO):
    netflow_address: Address = DTOField(..., description="Netflow address")
    window: str = DTOField(..., description='a string defining a time window, ex. "30 day"')
    address: Address
    include_price: bool = DTOField(default=True, description='Include price quote')

    @property
    def token(self):
        return Token(self.address)

    def __init__(self, **data) -> None:
        if 'address' not in data:
            data['address'] = Token(**data).address
        super().__init__(**data)


@Model.describe(slug='token.netflow-window',
                version='1.4',
                display_name='Token netflow',
                description='The current Credmark supported netflow algorithm',
                category='protocol',
                tags=['token'],
                input=TokenNetflowWindowInput,
                output=TokenNetflowOutput)
class TokenOutflowWindow(Model):
    def run(self, input: TokenNetflowWindowInput) -> TokenNetflowOutput:
        window_in_seconds = self.context.historical.to_seconds(input.window)
        old_block_timestamp = self.context.block_number.timestamp - window_in_seconds
        old_block = BlockNumber.from_timestamp(old_block_timestamp)

        return self.context.run_model(
            'token.netflow-block',
            input=TokenNetflowBlockInput(
                address=input.address,
                netflow_address=input.netflow_address,
                block_number=old_block,
                include_price=input.include_price),
            return_type=TokenNetflowOutput)


class TokenNetflowSegmentBlockInput(TokenNetflowBlockInput):
    n: int = DTOField(2, ge=1, description='Number of interval to count')


class TokenNetflowSegmentOutput(DTO):
    address: Address
    netflows: List[TokenNetflowBlockRange]


@Model.describe(slug='token.netflow-segment-block',
                version='1.4',
                display_name='Token netflow by segment by block',
                description='The Current Credmark Supported netflow algorithm',
                category='protocol',
                tags=['token'],
                input=TokenNetflowSegmentBlockInput,
                output=TokenNetflowSegmentOutput)
class TokenVolumeSegmentBlock(Model):
    def run(self, input: TokenNetflowSegmentBlockInput) -> TokenNetflowSegmentOutput:
        token_address = input.address
        old_block = input.block_number

        if old_block >= 0:
            if old_block > self.context.block_number:
                raise ModelRunError(f'input {input.block_number=} shall be earlier '
                                    f'than the current block {self.context.block_number}')
            block_seg = self.context.block_number - old_block
        else:
            block_seg = - old_block

        block_start = self.context.block_number - block_seg * input.n
        if block_start < 0:
            raise ModelRunError(
                'Start block shall be larger than zero: '
                f'{self.context.block_number} - {block_seg} * {input.n} = {block_start}')

        native_token = NativeToken()
        token_address = input.address
        old_block = input.block_number

        if old_block >= 0:
            if old_block > self.context.block_number:
                raise ModelRunError(f'input {input.block_number=} shall be earlier '
                                    f'than the current block {self.context.block_number}')
            block_seg = self.context.block_number - old_block
        else:
            block_seg = - old_block

        block_end = int(self.context.block_number)
        block_start = block_end - block_seg * input.n
        if block_start < 0:
            raise ModelRunError(
                'Start block shall be larger than zero: '
                f'{block_end} - {block_seg} * {input.n} = {block_start}')

        native_token = NativeToken()
        if token_address == native_token.address:
            input_token = native_token
            with self.context.ledger.Transaction.as_('t') as t,\
                    self.context.ledger.Block.as_('s') as s,\
                    self.context.ledger.Block.as_('e') as e:

                df = s.select(
                    aggregates=[
                        (s.NUMBER, 'from_block'),
                        (s.TIMESTAMP, 'from_timestamp'),
                        (e.NUMBER, 'to_block'),
                        (e.TIMESTAMP, 'to_timestamp'),
                        ((f'SUM(CASE WHEN {t.TO_ADDRESS.eq(input.netflow_address)} '
                          f'THEN {t.VALUE} ELSE 0::INTEGER END)'), 'inflow'),
                        ((f'SUM(CASE WHEN {t.FROM_ADDRESS.eq(input.netflow_address)} '
                          f'THEN {t.VALUE} ELSE 0::INTEGER END)'), 'outflow'),
                        ((f'SUM(CASE WHEN {t.TO_ADDRESS.eq(input.netflow_address)} '
                          f'THEN {t.VALUE} ELSE {t.VALUE.neg_()} END)'), 'netflow')
                    ],
                    joins=[
                        (e, e.NUMBER.eq(s.NUMBER.plus_(str(block_seg)).minus_(str(1)))),
                        (JoinType.LEFT_OUTER, t, t.field(f'{t.BLOCK_NUMBER} between {s.NUMBER} and {e.NUMBER}')
                         .and_(t.TO_ADDRESS.eq(input.netflow_address)
                               .or_(t.FROM_ADDRESS.eq(input.netflow_address)).parentheses_()))
                    ],
                    group_by=[s.NUMBER, s.TIMESTAMP, e.NUMBER, e.TIMESTAMP],
                    having=(s.NUMBER.ge(block_start)
                            .and_(s.NUMBER.lt(block_end)
                            .and_(f'MOD({e.NUMBER} - {block_start}, {block_seg}) = 0'))),
                    order_by=s.NUMBER.asc()
                ).to_dataframe()
        else:
            input_token = input.token
            with self.context.ledger.TokenTransfer.as_('t') as t,\
                    self.context.ledger.Block.as_('s') as s,\
                    self.context.ledger.Block.as_('e') as e:

                df = s.select(
                    aggregates=[
                        (s.NUMBER, 'from_block'),
                        (s.TIMESTAMP, 'from_timestamp'),
                        (e.NUMBER, 'to_block'),
                        (e.TIMESTAMP, 'to_timestamp'),
                        ((f'SUM(CASE WHEN {t.TO_ADDRESS.eq(input.netflow_address)} '
                          f'THEN {t.VALUE} ELSE 0::INTEGER END)'), 'inflow'),
                        ((f'SUM(CASE WHEN {t.FROM_ADDRESS.eq(input.netflow_address)} '
                          f'THEN {t.VALUE} ELSE 0::INTEGER END)'), 'outflow'),
                        ((f'SUM(CASE WHEN {t.TO_ADDRESS.eq(input.netflow_address)} '
                          f'THEN {t.VALUE} ELSE {t.VALUE.neg_()} END)'), 'netflow')
                    ],
                    joins=[
                        (e, e.NUMBER.eq(s.NUMBER.plus_(str(block_seg)).minus_(str(1)))),
                        (JoinType.LEFT_OUTER, t, t.field(f'{t.BLOCK_NUMBER} between {s.NUMBER} and {e.NUMBER}')
                         .and_(t.TOKEN_ADDRESS.eq(token_address))
                         .and_(t.TO_ADDRESS.eq(input.netflow_address)
                               .or_(t.FROM_ADDRESS.eq(input.netflow_address)).parentheses_()))
                    ],
                    group_by=[s.NUMBER, s.TIMESTAMP, e.NUMBER, e.TIMESTAMP],
                    having=(s.NUMBER.ge(block_start)
                            .and_(s.NUMBER.lt(block_end)
                            .and_(f'MOD({e.NUMBER} - {block_start}, {block_seg}) = 0'))),
                    order_by=s.NUMBER.asc()
                ).to_dataframe()

        df = df.fillna(0)
        netflows = []
        for _, r in df.iterrows():
            inflow = r['inflow']
            inflow = inflow if inflow is not None else 0
            inflow_scaled = input_token.scaled(inflow)
            outflow = r['outflow']
            outflow = outflow if outflow is not None else 0
            outflow_scaled = input_token.scaled(outflow)
            netflow = r['netflow']
            netflow = netflow if netflow is not None else 0
            netflow_scaled = input_token.scaled(netflow)

            price_last = None
            inflow_value_last = None
            outflow_value_last = None
            netflow_value_last = None
            if input.include_price:
                price_last = (self.context.models(block_number=r['to_block'])
                              .price.quote(base=input_token,
                                           return_type=PriceWithQuote)).price  # type: ignore
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
                from_block=r['from_block'],
                from_timestamp=r['from_timestamp'],
                to_block=r['to_block'],
                to_timestamp=r['to_timestamp']
            )
            netflows.append(netflow)

        output = TokenNetflowSegmentOutput(address=input.address, netflows=netflows)

        return output


class TokenNetflowSegmentWindowInput(TokenNetflowWindowInput):
    n: int = DTOField(2, ge=1, description='Number of interval to count')


@Model.describe(slug='token.netflow-segment-window',
                version='1.4',
                display_name='Token netflow by segment in window',
                description='The current Credmark supported netflow algorithm',
                category='protocol',
                tags=['token'],
                input=TokenNetflowSegmentWindowInput,
                output=TokenNetflowSegmentOutput)
class TokenNetflowSegmentWindow(Model):
    def run(self, input: TokenNetflowSegmentWindowInput) -> TokenNetflowSegmentOutput:
        window_in_seconds = self.context.historical.to_seconds(input.window)
        old_block_timestamp = self.context.block_number.timestamp - window_in_seconds
        old_block = BlockNumber.from_timestamp(old_block_timestamp)

        return self.context.run_model(
            'token.netflow-segment-block',
            input=TokenNetflowSegmentBlockInput(
                address=input.address,
                netflow_address=input.netflow_address,
                block_number=old_block,
                n=input.n,
                include_price=input.include_price),
            return_type=TokenNetflowSegmentOutput)
