#pylint: disable=pointless-string-statement, pointless-statement

import credmark.model
from credmark.types.data.block_number import BlockNumberOutOfRangeError, BlockNumber
from credmark.model.errors import ModelRunError


@credmark.model.describe(slug='example.block-number',
                         version='1.0',
                         display_name='(Example) BlockNumber',
                         description='This example shows the capabilities on the BlockNumber class',
                         output=dict)
class BlockNumberTransformExample(credmark.model.Model):

    """
    This example shows the capabilities on the BlockNumber class
    """

    def run(self, input) -> dict:

        block_number = self.context.block_number
        self.logger.info(
            f"block_number : {block_number}")
        self.logger.info(
            f"block_number.timestamp : {block_number.timestamp}")
        self.logger.info(
            f"block_number.datestring : {block_number.datestring}")
        self.logger.info(
            f"block_number - 100 + 50 : {(block_number - 100) + 50}")
        self.logger.info(
            f"block_number.from_datetime(block_number.timestamp - 3600) : \
                {block_number.from_timestamp(block_number.timestamp - 3600)}")
        self.logger.info(
            f"BlockNumber.from_datetime(block_number.timestamp - 3600) : \
                {BlockNumber.from_timestamp(block_number.timestamp - 3600)}")

        try:
            block_number + 10
            raise ModelRunError(
                message="BlockNumbers cannot exceed the current context.block_number, an exception was NOT caught, and the example has FAILED")
        except BlockNumberOutOfRangeError:
            """
                NOTE: THIS IS FOR DEMONSTRATION ONLY.
                You should NOT catch BlockNumberOutOfRangeError or
                other ModelRunErrors in your models!
            """

            self.logger.info(
                "BlockNumbers cannot exceed the current context.block_number, an exception was caught successfully")

        return dict(block_number=block_number)
