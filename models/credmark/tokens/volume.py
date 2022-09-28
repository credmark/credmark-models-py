# pylint: disable=locally-disabled, unused-import, no-member
from typing import List
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
    price_last: float
    value_last: float
    from_block: int
    to_block: int


class TokenVolumeOutput(TokenVolumeBlockRange):
    address: Address

    @classmethod
    def default(cls, _address, from_block, to_block):
        return cls(address=_address,
                   volume=0, volume_scaled=0, price_last=0, value_last=0,
                   from_block=from_block, to_block=to_block)


@Model.describe(slug='token.overall-volume-block',
                version='1.2',
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
        price_last = self.context.models.price.quote(base=input_token,
                                                     return_type=PriceWithQuote)
        value_last = vol_scaled * price_last.price  # type: ignore

        output = TokenVolumeOutput(
            address=input.address,
            volume=vol,
            volume_scaled=vol_scaled,
            price_last=price_last.price,   # type: ignore
            value_last=value_last,
            from_block=old_block+1,
            to_block=to_block
        )

        return output


class TokenVolumeWindowInput(DTO):
    window: str
    address: Address

    def __init__(self, **data) -> None:
        if 'address' in data:
            super().__init__(**data)
        else:
            address = Token(**data).address
            super().__init__(address=address, window=data['window'])

    def to_token(self) -> Token:
        return Token(self.address)


@Model.describe(slug='token.overall-volume-window',
                version='1.0',
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
                block_number=old_block),
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
                version='1.1',
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
            raise ModelRunError('Start block shall be larger than zero: '
                                f'{self.context.block_number} - {block_seg} * {input.n} = {block_start}')

        to_block = self.context.block_number
        native_token = NativeToken()
        if input.address == native_token.address:
            input_token = native_token
            with self.context.ledger.Transaction as q:
                df = q.select(aggregates=[
                    (f"floor({q.BLOCK_NUMBER.minus_(str(block_start)).minus_('1').parentheses_()} / {block_seg})",
                     'block_label'),
                    (q.BLOCK_NUMBER.min_(), 'block_number_min'),
                    (q.BLOCK_NUMBER.max_(), 'block_number_max'),
                    (q.VALUE.sum_(), 'sum_value')],
                    where=q.BLOCK_NUMBER.gt(block_start),
                    group_by=[q.field('block_label').dquote()],
                    order_by=q.field('block_label').dquote()).to_dataframe()
        else:
            input_token = input.to_token()
            with self.context.ledger.TokenTransfer as q:
                df = q.select(aggregates=[
                    (f"floor({q.BLOCK_NUMBER.minus_(str(block_start)).minus_('1').parentheses_()} / {block_seg})",
                     'block_label'),
                    (q.BLOCK_NUMBER.min_(), 'block_number_min'),
                    (q.BLOCK_NUMBER.max_(), 'block_number_max'),
                    (q.VALUE.sum_(), 'sum_value')],
                    where=(q.TOKEN_ADDRESS.eq(token_address)
                           .and_(q.BLOCK_NUMBER.gt(block_start))),
                    group_by=[q.field('block_label').dquote()],
                    order_by=q.field('block_label').dquote()).to_dataframe()

        volumes = []
        for _n, r in df.iterrows():
            vol_scaled = input_token.scaled(r['sum_value'])
            price_last = (self.context.models(block_number=r['block_number_max'])
                              .price.quote(base=input_token,
                                           return_type=PriceWithQuote))
            value_last = vol_scaled * price_last.price  # type: ignore

            vol = TokenVolumeBlockRange(volume=r['sum_value'],
                                        volume_scaled=vol_scaled,
                                        price_last=price_last.price,  # type: ignore
                                        value_last=value_last,
                                        from_block=r['block_number_min'],
                                        to_block=r['block_number_max'])
            volumes.append(vol)

        output = TokenVolumeSegmentOutput(address=input.address, volumes=volumes)

        return output


class TokenVolumeSegmentWindowInput(TokenVolumeWindowInput):
    n: int = DTOField(2, ge=1, description='Number of interval to count')


@Model.describe(slug='token.volume-segment-window',
                version='1.0',
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
                n=input.n),
            return_type=TokenVolumeSegmentOutput)
