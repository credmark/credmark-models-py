from datetime import (datetime, date, timezone)
import credmark.model
from credmark.model import (
    ModelRunError,
)
from credmark.types.data.block_number import (
    BlockNumberOutOfRangeError,
)
from credmark.dto import (EmptyInput)
from credmark.types import (
    BlockNumber
)


@credmark.model.describe(slug='example.blocktime',
                         version='1.0',
                         display_name='(Example) BlockNumber',
                         description='The Time of the block of the execution context',
                         input=EmptyInput)
class BlockTimeExample(credmark.model.Model):

    """
    This example shows the query between block_number, timestamp and Python datetime/date.
    - How to obtain a block from either one type of input timestamp, date or datetime.
    - How to obtain the Python datetime for a block
    It is better to run this model with -b 14234904.
    """

    def run(self, input) -> None:

        if self.context.block_number != 14234904:
            self.logger.info(
                'The example code in this model works with block number input, -b 14234904')

        # We run the model as of block 14234904
        # To obtan the datetime
        res = BlockNumber(14234904).to_datetime()
        assert res == datetime(2022, 2, 19, 6, 19, 56, tzinfo=timezone.utc)
        self.logger.info(f'Block 14234904\'s datetime is {res}')

        # To obtain the last block of the day, we provides an input of date.
        res = self.context.block_number.from_timestamp(
            datetime(2022, 2, 19, 6, 19, 56, tzinfo=timezone.utc).timestamp())
        assert res == 14234904

        # When we obtain a timestamp from a datetime, Python counts the local timezone if we do not provide a timezone.
        # Below example converts the datetime using local timezone (UTC+8 for below case)
        # We will get a different block number other than 14234904 and it's with another UTC time.
        ts = datetime(2022, 2, 19, 6, 19, 56).timestamp()
        res = self.context.block_number.from_timestamp(ts)
        assert res == 14232694
        self.logger.info(f'Block 14232694\'s timestamp is {ts}')

        res = BlockNumber(14232694).to_datetime()
        assert res == datetime(2022, 2, 18, 22, 19, 35, tzinfo=timezone.utc)

        # Let's try with one day earlier. we shall obtain the last block of the day
        ts = datetime(2022, 2, 18, 23, 59, 59, tzinfo=timezone.utc).timestamp()
        res = self.context.block_number.from_timestamp(ts)
        assert res == 14233162
        self.logger.info(f'Block 14232694\'s timestamp is {ts}')

        # Check the time of the block, it's the last of the day
        res = BlockNumber(14233162).to_datetime()
        assert res == datetime(2022, 2, 18, 23, 59, 54, tzinfo=timezone.utc)
        self.logger.info(f'Block 14233162\'s datetime is {res}')

        # We can not obtain information of a future block
        try:
            res = BlockNumber(14239569).to_datetime()
            raise ModelRunError(
                message="BlockNumbers cannot exceed the current context.block_number, an exception was NOT caught, and the example has FAILED")
        except BlockNumberOutOfRangeError as _err:
            _ = """
                NOTE: THIS IS FOR DEMONSTRATION ONLY.
                You should NOT catch BlockNumberOutOfRangeError or
                other ModelRunErrors in your models!
                """

            self.logger.info(
                f'You have caught the below error from querying 14239569\'s datetime because it\'s later than the currente block {self.context.block_number}')
            self.logger.info(
                f'Expected exception print out in the next line: `"ERROR - BlockNumber 14239569 is out of maximum range: {self.context.block_number}"')
            self.logger.error(_err)
