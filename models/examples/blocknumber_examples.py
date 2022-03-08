import credmark.model
from credmark.types import BlockNumber
from credmark.types.data.block_number import BlockNumberOutOfRangeException
from credmark.types.dto import DTO


class BlockNumberTransformExampleOutput(DTO):
    blockNumber: int
    blockTime: int
    blockDatestring: str
    tenThousandBlocksAgo: int
    tenThousandBlocksAgoTimestamp: int
    tenThousandBlocksAgoDatestring: str


@credmark.model.describe(slug='example.blocktime',
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

        try:
            block = block + 1
        except BlockNumberOutOfRangeException:
            print("I can't look into the future, looking at the next block was attempted.")

        ten_thousand_blocks_ago = self.context.block_number - 10000

        return BlockNumberTransformExampleOutput(
            blockNumber=block,
            blockTime=block.timestamp,
            blockDatestring=block.datestring,
            tenThousandBlocksAgo=ten_thousand_blocks_ago,
            tenThousandBlocksAgoTimestamp=ten_thousand_blocks_ago.timestamp,
            tenThousandBlocksAgoDatestring=ten_thousand_blocks_ago.datestring
        )
