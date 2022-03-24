from datetime import (datetime, date, timezone)
import credmark.model
from credmark.dto import (EmptyInput)


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
            self.logger.warn(
                'The example code in this model works with block number input, -b 14234904')

        # We run the model as of block 14234904
        # To obtan the datetime
        res = self.context.block_number.datetime_of(14234904)
        assert res == datetime(2022, 2, 19, 6, 19, 56, tzinfo=timezone.utc)

        # We can not obtain information of a future block
        try:
            res = self.context.block_number.datetime_of(14239569)
        except Exception as _err:
            self.logger.info('You have caught the below error')
            self.logger.info(
                'Expected exception print out in the next line: `"ERROR - ModelError: Invalid future block 14239569 for block 14234904 context`"')
            self.logger.error(_err)

        # To obtain the last block of the day, we provides an input of date.
        # Below warning message may appear if we run as of a block earlier than the end of the day
        # 2022-03-23 15: 20: 15, 540 - credmark.model.engine.context - WARNING - Return the current block 14234904 on 2022-02-19 06: 19: 56+00: 00, because block 14239569 for 2022-02-19 23: 59: 57+00: 00 is later.
        res = self.context.block_number.from_datetime(date(2022, 2, 19))
        assert res == 14234904

        # Let's try with one day earlier. we shall obtain the last block of the day
        res = self.context.block_number.from_datetime(date(2022, 2, 18))
        assert res == 14233162
        # Check the time of the block, it's the last of the day
        res = self.context.block_number.datetime_of(14233162)
        assert res == datetime(2022, 2, 18, 23, 59, 54, tzinfo=timezone.utc)

        # If we input a datetime, time 00:00:00 is by default. We obtain a different block with the input of a date.
        res = self.context.block_number.from_datetime(datetime(2022, 2, 18, tzinfo=timezone.utc))
        assert res == 14226745
        # Check the time of the block, it's the start of the day
        res = self.context.block_number.datetime_of(14226745)
        assert res == datetime(2022, 2, 18, 0, 0, tzinfo=timezone.utc)

        # When we obtain a timestamp from a datetime, Python counts the local timezone if we do not provide a timezone.
        # Below example converts the datetime using local timezone (UTC+8 for below case)
        res = self.context.block_number.from_datetime(datetime(2022, 2, 18).timestamp())
        assert res == 14224550
        res = self.context.block_number.datetime_of(14224550)
        assert res == datetime(2022, 2, 17, 15, 59, 47, tzinfo=timezone.utc)

        # Convert to timezone with a timezone will return the same result as datetime(2022, 2, 18).
        res = self.context.block_number.from_datetime(
            datetime(2022, 2, 18, tzinfo=timezone.utc).timestamp())
        assert res == 14226745
