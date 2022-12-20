# pylint: disable=locally-disabled, unused-import, no-member
from typing import List, Union
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import (Address, BlockNumber, Contract,
                                NativeToken, PriceWithQuote,
                                Token)
from credmark.dto import DTO, DTOField


@Model.describe(slug='token.swap-pool-volume',
                version='1.0',
                display_name='Token Volume',
                description='The current volume for a swap pool',
                category='protocol',
                tags=['token'],
                input=Contract,
                output=dict)
class TokenSwapPoolVolume(Model):
    def run(self, input: Token) -> dict:
        # TODO: Get All Credmark Supported swap Pools for a token
        return {"result": 0}


class TokenVolumeBlockInput(DTO):
    block_number: int = DTOField(
        description=('Positive for a block earlier than the current one '
                     'or negative or zero for an interval. '
                     'Both excludes the start block.'))
    address: Address
    include_price: bool = DTOField(default=True, description='Include price quote')

    def __init__(self, **data) -> None:
        if 'address' in data:
            super().__init__(**data)
        else:
            address = Token(**data).address
            super().__init__(address=address, block_number=data['block_number'])

    def to_token(self) -> Token:
        return Token(self.address)


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
                              where=q.BLOCK_NUMBER.gt(old_block)).to_dataframe()
        else:
            input_token = input.to_token()
            with self.context.ledger.TokenTransfer as q:
                df = q.select(aggregates=[(q.VALUE.sum_(), 'sum_value')],
                              where=(q.TOKEN_ADDRESS.eq(token_address)
                                     .and_(q.BLOCK_NUMBER.gt(old_block))),
                              ).to_dataframe()

        vol = df.sum_value.sum()
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
    include_price: bool = DTOField(default=True, description='Include price quote')

    def __init__(self, **data) -> None:
        if 'address' in data:
            super().__init__(**data)
        else:
            address = Token(**data).address
            super().__init__(address=address, window=data['window'])

    def to_token(self) -> Token:
        return Token(self.address)


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
        old_block_timestamp = self.context.block_number.timestamp - window_in_seconds
        old_block = BlockNumber.from_timestamp(old_block_timestamp)

        return self.context.run_model(
            'token.overall-volume-block',
            input=TokenVolumeBlockInput(
                address=input.address,
                block_number=old_block,
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
                version='1.2',
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

        block_start = self.context.block_number - block_seg * input.n
        if block_start < 0:
            raise ModelRunError(
                'Start block shall be larger than zero: '
                f'{self.context.block_number} - {block_seg} * {input.n} = {block_start}')

        native_token = NativeToken()
        if input.address == native_token.address:
            input_token = native_token
            with self.context.ledger.Transaction as q:
                f1 = q.BLOCK_NUMBER.minus_(str(block_start)).minus_('1').parentheses_()
                df = q.select(aggregates=[
                    (f"floor({f1} / {block_seg})",
                     'block_label'),
                    (q.BLOCK_NUMBER.min_(), 'block_number_min'),
                    (q.BLOCK_TIMESTAMP.min_(), 'block_ts_min'),
                    (q.BLOCK_NUMBER.max_(), 'block_number_max'),
                    (q.BLOCK_TIMESTAMP.max_(), 'block_ts_max'),
                    (q.VALUE.sum_(), 'sum_value')],
                    where=q.BLOCK_NUMBER.gt(block_start),
                    group_by=[q.field('block_label').dquote()],
                    order_by=q.field('block_label').dquote()).to_dataframe()
        else:
            input_token = input.to_token()
            with self.context.ledger.TokenTransfer as q:
                f1 = q.BLOCK_NUMBER.minus_(str(block_start)).minus_('1').parentheses_()
                df = q.select(aggregates=[
                    (f"floor({f1} / {block_seg})",
                     'block_label'),
                    (q.BLOCK_NUMBER.min_(), 'block_number_min'),
                    (q.BLOCK_TIMESTAMP.min_(), 'block_ts_min'),
                    (q.BLOCK_NUMBER.max_(), 'block_number_max'),
                    (q.BLOCK_TIMESTAMP.max_(), 'block_ts_max'),
                    (q.VALUE.sum_(), 'sum_value')],
                    where=(q.TOKEN_ADDRESS.eq(token_address)
                           .and_(q.BLOCK_NUMBER.gt(block_start))),
                    group_by=[q.field('block_label').dquote()],
                    order_by=q.field('block_label').dquote()).to_dataframe()

        volumes = []
        for _, r in df.iterrows():
            vol_scaled = input_token.scaled(r['sum_value'])
            price_last = None
            value_last = None
            if input.include_price:
                price_last = (self.context.models(block_number=r['block_number_max'])
                              .price.quote(base=input_token,
                                           return_type=PriceWithQuote)).price  # type: ignore
                value_last = vol_scaled * price_last

            vol = TokenVolumeBlockRange(volume=r['sum_value'],
                                        volume_scaled=vol_scaled,
                                        price_last=price_last,
                                        value_last=value_last,
                                        from_block=r['block_number_min'],
                                        from_timestamp=r['block_ts_min'],
                                        to_block=r['block_number_max'],
                                        to_timestamp=r['block_ts_max'],)
            volumes.append(vol)

        output = TokenVolumeSegmentOutput(address=input.address, volumes=volumes)

        return output


class TokenVolumeSegmentWindowInput(TokenVolumeWindowInput):
    n: int = DTOField(2, ge=1, description='Number of interval to count')


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
