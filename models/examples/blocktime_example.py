from datetime import datetime, timedelta, timezone

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelInputError, ModelRunError
from credmark.cmf.types.block_number import BlockNumber
from credmark.dto import DTO, DTOField
from models.examples.example_dtos import ExampleModelOutput


class _BlockTimeInput(DTO):
    blockTime: datetime = DTOField(
        title="Block time",
        description="Unix time, i.e. seconds(if >= -2e10 or <= 2e10) or milliseconds "
        "(if < -2e10 or > 2e10) since 1 January 1970 or string with format "
        "YYYY-MM-DD[T]HH: MM[:SS[.ffffff]][Z or [±]HH[:]MM]]]",
        default_factory=datetime.utcnow
    )


@ Model.describe(slug='example.block-time',
                 version='1.0',
                 display_name='(Example) BlockNumber',
                 description='The Time of the block of the execution context',
                 input=_BlockTimeInput,
                 output=ExampleModelOutput)
class BlockTimeExample(Model):
    """
    This example shows the query between block_number, timestamp and Python datetime/date.
        - How to obtain a block from either one type of input timestamp, date or datetime.
        - How to obtain the Python datetime for a block
    """

    def run(self, input: _BlockTimeInput) -> ExampleModelOutput:
        output = ExampleModelOutput(
            github_url="https://github.com/credmark/credmark-models-py/blob/main/models/examples/blocktime_example.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/_modules/credmark/cmf/types/block_number.html")

        block_time = input.blockTime.replace(tzinfo=timezone.utc)
        output.log_io(input="Input blockTime", output=block_time)

        output.log("CMF's BlockNumber is used to get Block Number from datetime or timestamp")
        block_number = BlockNumber.from_timestamp(block_time)
        output.log("BlockNumber's timestamp might be different from the input timestamp,")
        output.log("as the last block before the datetime is returned")
        output.log_io(input=f"BlockNumber.from_timestamp({block_time})", output=block_number)

        output.log_io(input="block_number.timestamp_datetime", output=block_number.timestamp_datetime)

        output.log("Block Number can also be obtained from unix timestamp.")
        output.log("If timezone is not provided, python defaults to UTC timezone")
        output.log(f"{block_time} = {block_time.timestamp()}s")
        output.log_io(input=f"BlockNumber.from_timestamp({block_time.timestamp()})",
                      output=BlockNumber.from_timestamp(block_time.timestamp()))

        output.log("Querying block number for a future timestamp returns the latest block number")
        future_block_time = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(days=10)
        output.log_io(input="future_block_time", output=future_block_time)
        output.log_io(input=f"BlockNumber.from_timestamp({future_block_time})",
                      output=BlockNumber.from_timestamp(future_block_time))

        block_time_without_tz = block_time.replace(tzinfo=None)
        output.log_io(input="block_time_without_tz", output=block_time_without_tz)

        try:
            BlockNumber.from_timestamp(block_time_without_tz)
            raise ModelRunError(
                message='BlockNumber cannot be converted from a datetime without timezone, '
                'an exception was NOT caught, and the example has FAILED')
        except ModelInputError as _e:
            output.log_error(_e)
            output.log_error("Attempting to convert a datetime without timezone to BlockNumber "
                             "raises ModelInputError")
        return output
