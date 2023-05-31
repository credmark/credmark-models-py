# pylint: disable=locally-disabled, no-member, line-too-long
from typing import List, Union

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import (
    Address,
    BlockNumber,
    JoinType,
    NativeToken,
    PriceWithQuote,
    Token,
)
from credmark.dto import DTO, DTOField


class TokenVolumeBlockInput(DTO):
    block_number: int = DTOField(
        description=('Positive for a block earlier than the current one '
                     'or negative or zero for an interval. '
                     'Both excludes the start block.'))
    address: Address
    include_price: bool = DTOField(
        default=True, description='Include price quote')

    @property
    def token(self):
        return Token(self.address)

    def __init__(self, **data) -> None:
        if 'address' not in data:
            data['address'] = Token(**data).address
        super().__init__(**data)

    class Config:
        schema_extra = {
            'example': {"symbol": "USDC", "block_number": -1000}
        }


class TokenVolumeBlockRange(DTO):
    volume: int
    volume_scaled: float
    price_last: Union[float, None]
    value_last: Union[float, None]
    from_block: int
    from_timestamp: int
    to_block: int
    to_timestamp: int


class TokenVolumeOutput(TokenVolumeBlockRange):
    address: Address


@Model.describe(slug='token.overall-volume-block',
                version='1.3',
                display_name='Token Volume',
                description='The Current Credmark Supported trading volume algorithm',
                category='protocol',
                tags=['token'],
                input=TokenVolumeBlockInput,
                output=TokenVolumeOutput)
class TokenVolumeBlock(Model):
    def run(self, input: TokenVolumeBlockInput) -> TokenVolumeOutput:
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
                df = q.select(aggregates=[(q.VALUE.sum_(), 'sum_value')],
                              where=q.BLOCK_NUMBER.gt(old_block),
                              bigint_cols=['sum_value'],).to_dataframe()
        else:
            input_token = input.token
            with self.context.ledger.TokenTransfer as q:
                df = q.select(aggregates=[(q.VALUE.sum_(), 'sum_value')],
                              where=(q.TOKEN_ADDRESS.eq(token_address)
                                     .and_(q.BLOCK_NUMBER.gt(old_block))),
                              bigint_cols=['sum_value'],
                              ).to_dataframe()

        vol = df['sum_value'][0]
        vol_scaled = input_token.scaled(vol)
        price_last = None
        value_last = None
        if input.include_price:
            price_last = self.context.models.price.quote(
                base=input_token,
                return_type=PriceWithQuote).price  # type: ignore
            value_last = vol_scaled * price_last

        output = TokenVolumeOutput(
            address=input.address,
            volume=vol,
            volume_scaled=vol_scaled,
            price_last=price_last,
            value_last=value_last,
            from_block=from_block,
            from_timestamp=from_block.timestamp,
            to_block=to_block,
            to_timestamp=to_block.timestamp
        )

        return output


class TokenVolumeWindowInput(DTO):
    window: str
    address: Address
    include_price: bool = DTOField(
        default=True, description='Include price quote')

    @property
    def token(self):
        return Token(self.address)

    def __init__(self, **data) -> None:
        if 'address' not in data:
            data['address'] = Token(**data).address
        super().__init__(**data)

    class Config:
        schema_extra = {
            'example': {"address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", "window": "1 day"}
        }


@Model.describe(slug='token.overall-volume-window',
                version='1.1',
                display_name='Token Volume',
                description='The current Credmark supported trading volume algorithm',
                category='protocol',
                tags=['token'],
                input=TokenVolumeWindowInput,
                output=TokenVolumeOutput)
class TokenVolumeWindow(Model):
    def run(self, input: TokenVolumeWindowInput) -> TokenVolumeOutput:
        window_in_seconds = self.context.historical.to_seconds(input.window)
        past_block_timestamp = self.context.block_number.timestamp - window_in_seconds
        past_block_number = BlockNumber.from_timestamp(past_block_timestamp)

        return self.context.run_model(
            'token.overall-volume-block',
            input=TokenVolumeBlockInput(
                address=input.address,
                block_number=past_block_number,
                include_price=input.include_price),
            return_type=TokenVolumeOutput)


class TokenVolumeSegmentBlockInput(TokenVolumeBlockInput):
    n: int = DTOField(2, ge=1, description='Number of interval to count')


class TokenVolumeSegmentOutput(DTO):
    address: Address
    volumes: List[TokenVolumeBlockRange]

    @classmethod
    def default(cls, _address):
        return cls(address=_address, volumes=[])


@Model.describe(slug='token.volume-segment-block',
                version='1.3',
                display_name='Token Volume By Segment by Block',
                description='The Current Credmark Supported trading volume algorithm',
                category='protocol',
                tags=['token'],
                input=TokenVolumeSegmentBlockInput,
                output=TokenVolumeSegmentOutput)
class TokenVolumeSegmentBlock(Model):
    def run(self, input: TokenVolumeSegmentBlockInput) -> TokenVolumeSegmentOutput:
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
                        (t.VALUE.as_numeric().sum_(), 'sum_value')
                    ],
                    where=s.NUMBER.ge(block_start).and_(s.NUMBER.lt(block_end)),
                    joins=[
                        (e, e.NUMBER.eq(s.NUMBER.plus_(str(block_seg)).minus_(str(1)))),
                        (JoinType.LEFT_OUTER, t, t.field(f'{t.BLOCK_NUMBER} between {s.NUMBER} and {e.NUMBER}'))
                    ],
                    group_by=[s.NUMBER, s.TIMESTAMP, e.NUMBER, e.TIMESTAMP],
                    having=f'MOD({e.NUMBER} - {block_start}, {block_seg}) = 0',
                    order_by=s.NUMBER.asc(),
                    bigint_cols=['from_block', 'to_block', 'sum_value']
                ).to_dataframe()

                from_iso8601_str = t.field('').from_iso8601_str
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
                        (t.VALUE.as_numeric().sum_(), 'sum_value')
                    ],
                    where=s.NUMBER.ge(block_start).and_(s.NUMBER.lt(block_end)),
                    joins=[
                        (e, e.NUMBER.eq(s.NUMBER.plus_(str(block_seg)).minus_(str(1)))),
                        (JoinType.LEFT_OUTER,
                         t,
                         t.field(f'{t.BLOCK_NUMBER} between {s.NUMBER} and {e.NUMBER}').and_(
                             t.TOKEN_ADDRESS.eq(token_address)))
                    ],
                    group_by=[s.NUMBER, s.TIMESTAMP, e.NUMBER, e.TIMESTAMP],
                    having=f'MOD({e.NUMBER} - {block_start}, {block_seg}) = 0',
                    order_by=s.NUMBER.asc(),
                    bigint_cols=['from_block', 'to_block', 'sum_value']
                ).to_dataframe()

                from_iso8601_str = t.field('').from_iso8601_str

        df.sum_value = df.sum_value.fillna(0)
        df['from_timestamp'] = df['from_timestamp'].apply(from_iso8601_str)
        df['to_timestamp'] = df['to_timestamp'].apply(from_iso8601_str)

        volumes = []
        for _, r in df.iterrows():
            vol = r['sum_value']
            vol_scaled = input_token.scaled(vol)
            price_last = None
            value_last = None
            if input.include_price:
                price_last = (self.context.models(block_number=int(r['to_block']))
                              .price.quote(base=input_token,
                                           return_type=PriceWithQuote)).price  # type: ignore
                value_last = vol_scaled * price_last

            vol = TokenVolumeBlockRange(volume=vol,
                                        volume_scaled=vol_scaled,
                                        price_last=price_last,
                                        value_last=value_last,
                                        from_block=r['from_block'],
                                        from_timestamp=r['from_timestamp'],
                                        to_block=r['to_block'],
                                        to_timestamp=r['to_timestamp'],)
            volumes.append(vol)

        output = TokenVolumeSegmentOutput(
            address=input.address, volumes=volumes)

        return output


class TokenVolumeSegmentWindowInput(TokenVolumeWindowInput):
    n: int = DTOField(2, ge=1, description='Number of interval to count')

    class Config:
        schema_extra = {
            'skip_test': True
        }


@Model.describe(slug='token.volume-segment-window',
                version='1.1',
                display_name='Token Volume by Segment in Window',
                description='The current Credmark supported trading volume algorithm',
                category='protocol',
                tags=['token'],
                input=TokenVolumeSegmentWindowInput,
                output=TokenVolumeSegmentOutput)
class TokenVolumeSegmentWindow(Model):
    def run(self, input: TokenVolumeSegmentWindowInput) -> TokenVolumeSegmentOutput:
        window_in_seconds = self.context.historical.to_seconds(input.window)
        old_block_timestamp = self.context.block_number.timestamp - window_in_seconds
        old_block = BlockNumber.from_timestamp(old_block_timestamp)

        return self.context.run_model(
            'token.volume-segment-block',
            input=TokenVolumeSegmentBlockInput(
                address=input.address,
                block_number=old_block,
                include_price=input.include_price,
                n=input.n),
            return_type=TokenVolumeSegmentOutput)
