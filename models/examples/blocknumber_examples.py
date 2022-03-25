from typing import (
    Optional
)
from datetime import (
    datetime,
    timezone
)

import credmark.model
from credmark.types.data.block_number import BlockNumberOutOfRangeError
from credmark.dto import (
    DTO,
    DTOField,
)
from credmark.types import (
    BlockSeries,
)


class BlockNumberTransformExampleOutput(DTO):
    blockNumber: int
    blockTimestamp: int
    blockDatestring: str
    tenThousandBlocksAgo: int
    tenThousandBlocksAgoTimestamp: int
    tenThousandBlocksAgoDatestring: str


@credmark.model.describe(slug='example.blocknumber-historical',
                         version='1.0',
                         display_name='(Example) BlockNumber',
                         description='The Time of the block of the execution context',
                         output=BlockSeries[BlockNumberTransformExampleOutput])
class BlockNumberHistoricalExample(credmark.model.Model):
    def run(self, input) -> BlockSeries[BlockNumberTransformExampleOutput]:
        # If we run model with latest
        self.context.block_number = 14432493

        print('current block',
              self.context.block_number,
              self.context.block_number.timestamp,
              self.context.block_number.timestamp_datetime)

        # What happend 200-100 seconds before a block is created.
        x = self.context.historical.run_model_historical('example.blocknumber',
                                                         model_input={'use_latest_block': True},
                                                         window='10 minute',
                                                         interval='1 minute',
                                                         end_timestamp=self.context.block_number.datetime_of(
                                                             14432493).timestamp()-10_000
                                                         ).dict()
        for e in x['series']:
            print(e['blockNumber'], e['blockTimestamp'],
                  datetime.fromtimestamp(e['blockTimestamp'], tz=timezone.utc))

        x = self.context.historical.run_model_historical('example.blocknumber',
                                                         model_input={'use_latest_block': True},
                                                         window='10 minute',
                                                         interval='1 minute',
                                                         block_number=14432493-10_000
                                                         ).dict()

        for e in x['series']:
            print(e['blockNumber'], e['blockTimestamp'],
                  datetime.fromtimestamp(e['blockTimestamp'], tz=timezone.utc))

        # What happend 200-100 seconds before a block is created.
        x = self.context.historical.run_model_historical('example.blocknumber',
                                                         window='10 minute',
                                                         interval='1 minute',
                                                         block_number=14432493
                                                         ).dict()

        for e in x['series']:
            print(e['blockNumber'], e['blockTimestamp'],
                  datetime.fromtimestamp(e['blockTimestamp'], tz=timezone.utc))

        # What happend 200-100 seconds before a block is created.
        x = self.context.historical.run_model_historical('example.blocknumber',
                                                         window='100 second',
                                                         interval='1 second',
                                                         end_timestamp=self.context.block_number.datetime_of(
                                                                14432493).timestamp(),
                                                         block_number=14432493
                                                         ).dict()
        for e in x['series']:
            print(e['blockNumber'], e['blockTimestamp'],
                  datetime.fromtimestamp(e['blockTimestamp'], tz=timezone.utc))

        # What happend 100 seconds before a block is created.
        x = self.context.historical.run_model_historical('example.blocknumber',
                                                         window='100 second',
                                                         interval='1 second',
                                                         end_timestamp=self.context.block_number.datetime_of(
                                                                14432493).timestamp(),
                                                         block_number=14432493
                                                         ).dict()
        for e in x['series']:
            print(e['blockNumber'], e['blockTimestamp'],
                  datetime.fromtimestamp(e['blockTimestamp'], tz=timezone.utc))


@credmark.model.describe(slug='example.blocknumber',
                         version='1.0',
                         display_name='(Example) BlockNumber',
                         description='The Time of the block of the execution context',
                         output=BlockNumberTransformExampleOutput)
class BlockNumberTransformExample(credmark.model.Model):

    """
    This example returns information about the current block, attempts
    to look at a future block,
    and offers information about a previous block.
    """

    def run(self, input) -> BlockNumberTransformExampleOutput:

        block = self.context.block_number

        # NOTE: This is for demonstration only.
        # You should NOT catch BlockNumberOutOfRangeError or
        # other ModelRunErrors in your models!
        try:
            block = block + 1
        except BlockNumberOutOfRangeError:
            self.logger.info(
                "I can't look into the future, looking at the next block was attempted.")

        ten_thousand_blocks_ago = self.context.block_number - 10000

        return BlockNumberTransformExampleOutput(
            blockNumber=block,
            blockTimestamp=block.timestamp,
            blockDatestring=block.datestring,
            tenThousandBlocksAgo=ten_thousand_blocks_ago,
            tenThousandBlocksAgoTimestamp=ten_thousand_blocks_ago.timestamp,
            tenThousandBlocksAgoDatestring=ten_thousand_blocks_ago.datestring
        )
