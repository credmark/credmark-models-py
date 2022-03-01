import credmark.model
from credmark.types import BlockNumber
from credmark.types.data.block_number import BlockNumberOutOfRangeException


@credmark.model.describe(slug='example-blocktime',
                         version='1.0',
                         display_name='(Example) BlockNumber',
                         description='The Time of the block of the execution context')
class BlockTimeExample(credmark.model.Model):

    """
    This example returns the timestamp of the context block, contextualized.
    """

    def run(self, input) -> dict:
        block = self.context.block_number

        try:
            block = block + 1
        except BlockNumberOutOfRangeException:
            print("I can't look into the future, so don't try.")

        ten_thousand_blocks_ago = self.context.block_number - 10000

        return {
            "blockNumber": block,
            "blockTime": block.timestamp,
            "blockDatestring": block.datestring,
            "tenThousandBlocksAgo": ten_thousand_blocks_ago,
            "tenThousandBlocksAgoTimestamp": ten_thousand_blocks_ago.timestamp,
            "tenThousandBlocksAgoDatestring": ten_thousand_blocks_ago.datestring
        }
