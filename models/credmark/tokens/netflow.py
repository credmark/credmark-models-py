from typing import List, Union
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import (Account, Address, BlockNumber, NativeToken,
                                PriceWithQuote, Token)
from credmark.dto import DTO, DTOField


class TokenNetflowBlockInput(Account):
    netflow_address: Address = DTOField(..., description="Netflow address")
    block_number: int = DTOField(
        description=('Positive for a block earlier than the current one '
                     'or negative or zero for an interval. '
                     'Both excludes the start block.'))

    def to_token(self) -> Token:
        return Token(self.address)


class Block(DTO):
    block_number: int = DTOField(..., description='Block number in the series')
    block_timestamp: int = DTOField(..., description='The Timestamp of the Block')
    sample_timestamp: int = DTOField(..., description='The Sample Blocktime')

    @classmethod
    def from_block_number(cls, block_number: Union[BlockNumber, int]):
        if isinstance(block_number, int):
            block_number = BlockNumber(block_number)
        return Block(block_number=block_number,
                     block_timestamp=block_number.timestamp,
                     sample_timestamp=(block_number.timestamp
                                       if block_number.sample_timestamp is None
                                       else block_number.sample_timestamp))


class TokenNetflowBlockRange(DTO):
    volume: int
    volume_scaled: float
    price_last: float
    value_last: float
    from_block: Block
    to_block: Block


class TokenNetflowOutput(TokenNetflowBlockRange):
    token: Token


@Model.describe(slug='token.netflow-block',
                version='1.1',
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
        native_token = NativeToken()
        if input.address == native_token.address:
            input_token = native_token
            with self.context.ledger.Transaction as q:
                df = q.select(
                    aggregates=[((f'SUM(CASE WHEN {q.TO_ADDRESS.eq(input.netflow_address)} '
                                  f'THEN {q.VALUE} ELSE {q.VALUE.neg_()} END)'), 'sum_value')],
                    where=q.BLOCK_NUMBER.gt(old_block)
                    .and_(q.TO_ADDRESS.eq(input.netflow_address)
                          .or_(q.FROM_ADDRESS.eq(input.netflow_address)).parentheses_())
                ).to_dataframe()
        else:
            input_token = input.to_token()
            with self.context.ledger.TokenTransfer as q:
                df = q.select(
                    aggregates=[((f'SUM(CASE WHEN {q.TO_ADDRESS.eq(input.netflow_address)} '
                                  f'THEN {q.VALUE} ELSE {q.VALUE.neg_()} END)'), 'sum_value')],
                    where=q.BLOCK_NUMBER.gt(old_block)
                    .and_(q.TOKEN_ADDRESS.eq(token_address))
                    .and_(q.TO_ADDRESS.eq(input.netflow_address)
                          .or_(q.FROM_ADDRESS.eq(input.netflow_address)).parentheses_()),
                ).to_dataframe()

        vol = df.sum_value.values[0]
        vol = 0 if vol is None else vol
        vol_scaled = input_token.scaled(vol)
        price_last = self.context.run_model('price.quote',
                                            input={'base': input},
                                            return_type=PriceWithQuote)
        value_last = vol_scaled * price_last.price

        output = TokenNetflowOutput(
            token=input_token,
            volume=vol,
            volume_scaled=vol_scaled,
            price_last=price_last.price,
            value_last=value_last,
            from_block=Block.from_block_number(old_block+1),
            to_block=Block.from_block_number(to_block)
        )

        return output


class TokenNetflowWindowInput(Account):
    netflow_address: Address = DTOField(..., description="Netflow address")
    window: str = DTOField(..., description='a string defining a time window, ex. "30 day"')

    def to_token(self) -> Token:
        return Token(self.address)


@Model.describe(slug='token.netflow-window',
                version='1.1',
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
                block_number=old_block),
            return_type=TokenNetflowOutput)


class TokenNetflowSegmentBlockInput(TokenNetflowBlockInput):
    n: int = DTOField(2, ge=1, description='Number of interval to count')


class TokenNetflowSegmentOutput(DTO):
    token: Token
    netflows: List[TokenNetflowBlockRange]


@Model.describe(slug='token.netflow-segment-block',
                version='1.1',
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
        if input.address == native_token.address:
            input_token = native_token
            with self.context.ledger.Transaction as q:
                f1 = q.BLOCK_NUMBER.minus_(str(block_start)).minus_('1').parentheses_()
                df = q.select(aggregates=[
                    (f"floor({f1} / {block_seg})", 'block_label'),
                    ((f'SUM(CASE WHEN {q.TO_ADDRESS.eq(input.netflow_address)} '
                      f'THEN {q.VALUE} ELSE {q.VALUE.neg_()} END)'), 'sum_value')],
                    where=q.BLOCK_NUMBER.gt(block_start)
                    .and_(q.TO_ADDRESS.eq(input.netflow_address)
                          .or_(q.FROM_ADDRESS.eq(input.netflow_address)).parentheses_()),
                    group_by=[q.field('block_label').dquote()],
                    order_by=q.field('block_label').dquote()).to_dataframe()
        else:
            input_token = input.to_token()
            with self.context.ledger.TokenTransfer as q:
                f1 = q.BLOCK_NUMBER.minus_(str(block_start)).minus_('1').parentheses_()
                df = q.select(aggregates=[
                    (f"floor({f1} / {block_seg})", 'block_label'),
                    ((f'SUM(CASE WHEN {q.TO_ADDRESS.eq(input.netflow_address)} '
                     f'THEN {q.VALUE} ELSE {q.VALUE.neg_()} END)'), 'sum_value')],
                    where=q.BLOCK_NUMBER.gt(block_start)
                    .and_(q.TOKEN_ADDRESS.eq(token_address))
                    .and_(q.TO_ADDRESS.eq(input.netflow_address)
                          .or_(q.FROM_ADDRESS.eq(input.netflow_address)).parentheses_()),
                    group_by=[q.field('block_label').dquote()],
                    order_by=q.field('block_label').dquote()).to_dataframe()

        netflows = []
        for _, r in df.iterrows():
            vol = r['sum_value']
            block_offset = int(r['block_label']) * int(block_seg)
            from_block = block_start + block_offset
            to_block = from_block + block_seg
            vol_scaled = input_token.scaled(vol)
            price_last = (self.context.run_model('price.quote',
                                                 input={'base': input_token},
                                                 block_number=to_block,
                                                 return_type=PriceWithQuote))
            value_last = vol_scaled * price_last.price  # type: ignore

            netflow = TokenNetflowBlockRange(
                volume=vol,
                volume_scaled=vol_scaled,
                price_last=price_last.price,
                value_last=value_last,
                from_block=Block.from_block_number(from_block + 1),
                to_block=Block.from_block_number(to_block))

            netflows.append(netflow)

        output = TokenNetflowSegmentOutput(token=input_token, netflows=netflows)

        return output


class TokenNetflowSegmentWindowInput(TokenNetflowWindowInput):
    n: int = DTOField(2, ge=1, description='Number of interval to count')


@Model.describe(slug='token.netflow-segment-window',
                version='1.1',
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
                n=input.n),
            return_type=TokenNetflowSegmentOutput)
