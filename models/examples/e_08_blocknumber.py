from datetime import datetime, timedelta, timezone

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelInputError, ModelRunError, BlockNumberOutOfRangeError
from credmark.dto import EmptyInput
from models.dtos.example import ExampleBlockTimeInput, ExampleModelOutput


@ Model.describe(
    slug='example.block-number',
    version='1.2',
    display_name='Example - BlockNumber',
    description='This model gives examples of '
    'the functionality available on the BlockNumber class',
    developer='Credmark',
    input=EmptyInput,
    output=ExampleModelOutput)
class ExampleBlockNumber(Model):

    def run(self, _) -> ExampleModelOutput:
        output = ExampleModelOutput(
            title="8a. BlockNumber",
            description="This model gives examples of "
            "the functionality available on the BlockNumber class",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_08_blocknumber.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "reference/credmark.cmf.types.block_number.BlockNumber.html")

        block_number = self.context.block_number

        output.log("The current environment's BlockNumber is available in the Model Context")
        output.log_io(input="self.context.block_number",
                      output=self.context.block_number)
        output.log_io(input="block_number",
                      output=block_number)
        output.log_io(input="block_number.timestamp",
                      output=block_number.timestamp)
        output.log_io(input="block_number.timestamp_datetime",
                      output=block_number.timestamp_datetime)

        output.log('Addition and subtraction works across BlockNumber and int types')
        output.log_io(input="block_number - 1000",
                      output=block_number - 1000)
        output.log_io(input="(block_number - 1000).timestamp_datetime",
                      output=(block_number - 1000).timestamp_datetime)
        output.log_io(input="block_number.from_datetime(block_number.timestamp - 3600)",
                      output=block_number.from_timestamp(block_number.timestamp - 3600))
        output.log_io(input="self.context.BlockNumber.from_datetime(block_number.timestamp - 3600)",
                      output=self.context.BlockNumber.from_timestamp(block_number.timestamp - 3600))

        # NOTE: THE FOLLOWING IS FOR DEMONSTRATION ONLY.
        # You should NOT catch BlockNumberOutOfRangeError or
        # other ModelRunErrors in your models!

        try:
            # pylint: disable=pointless-statement
            # pyright: reportUnusedExpression=false
            block_number + 1
            raise ModelRunError(
                message='BlockNumbers cannot exceed the current context.block_number, '
                'an exception was NOT caught, and the example has FAILED')
        except BlockNumberOutOfRangeError as _e:
            output.log_error(_e)
            output.log_error("Attempting to create a BlockNumber object higher than the current "
                             "context's block_number raises BlockNumberOutOfRangeError")

        try:
            self.context.BlockNumber(-1)
            raise ModelRunError(
                message="BlockNumbers cannot be negative, an exception was NOT caught, "
                "and the example has FAILED")
        except BlockNumberOutOfRangeError as _e:
            output.log_error(_e)
            output.log_error(
                "Attempting to create a BlockNumber object with a negative block number "
                "raises BlockNumberOutOfRangeError")

        return output


@Model.describe(
    slug='example.block-time',
    version='1.2',
    display_name='Example - BlockTime',
    description='This model demonstrates the conversion between block_number, '
    'timestamp and Python datetime',
    input=ExampleBlockTimeInput,
    output=ExampleModelOutput)
class ExampleBlockTime(Model):
    def run(self, input: ExampleBlockTimeInput) -> ExampleModelOutput:
        output = ExampleModelOutput(
            title="8b. Example - Block Time",
            description="This model demonstrates the conversion between block_number, "
            "timestamp and Python datetime",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_08_blocknumber.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "reference/credmark.cmf.types.block_number.BlockNumber.html")

        output.log("The default input.blockTime is set to 2022/02/19 "
                   "so we can run this example with a past block number >= 14233162")

        block_datetime = input.blockTime.replace(tzinfo=timezone.utc)
        output.log_io(input="Input blockTime", output=block_datetime)

        output.log("CMF's BlockNumber is used to get Block Number from datetime or timestamp")
        block_number = self.context.BlockNumber.from_timestamp(block_datetime)
        output.log("BlockNumber's timestamp might be different from the input timestamp,")
        output.log("as the last block before the datetime is returned")
        output.log_io(input=f"BlockNumber.from_timestamp({block_datetime})", output=block_number)

        output.log_io(input="block_number.timestamp_datetime",
                      output=block_number.timestamp_datetime)

        output.log("Block Number can also be obtained from unix timestamp.")
        output.log("If timezone is not provided, python defaults to UTC timezone")
        output.log(f"{block_datetime} = {block_datetime.timestamp()}s")
        output.log_io(
            input=f"self.context.BlockNumber.from_timestamp({block_datetime.timestamp()})",
            output=self.context.BlockNumber.from_timestamp(block_datetime.timestamp()))

        # To run this code when we are on the latest
        if self.context.web3.eth.get_block_number() - self.context.block_number < 100:
            output.log("Querying block number for a future timestamp "
                       "returns the latest block number")
            future_block_datetime = (datetime.utcnow().replace(tzinfo=timezone.utc) +
                                     timedelta(days=10))
            output.log_io(input="future_block_datetime", output=future_block_datetime)
            output.log_io(
                input=f"self.context.BlockNumber.from_timestamp({future_block_datetime})",
                output=self.context.BlockNumber.from_timestamp(future_block_datetime))

        block_datetime_without_tz = block_datetime.replace(tzinfo=None)
        output.log_io(input="block_datetime_without_tz", output=block_datetime_without_tz)

        try:
            self.context.BlockNumber.from_timestamp(block_datetime_without_tz)
            raise ModelRunError(
                message='BlockNumber cannot be converted from a datetime without timezone, '
                'an exception was NOT caught, and the example has FAILED')
        except ModelInputError as _e:
            output.log_error(_e)
            output.log_error("Attempting to convert a datetime without timezone to BlockNumber "
                             "raises ModelInputError")
        return output
