# pylint: disable=line-too-long, pointless-string-statement

from credmark.cmf.model import ImmutableModel, ImmutableOutput, IncrementalModel
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import BlockNumber
from credmark.cmf.types.series import BlockSeries, BlockSeriesRow
from credmark.dto import EmptyInput


@ImmutableModel.describe(
    slug="example.immutable-wrong-output",
    version="0.1",
    display_name="Example for Immutable model with wrong output",
    developer="Credmark",
    category='protocol',
    tags=['token'],
    input=EmptyInput,
    output=dict)
class ExampleImmutableWrong(ImmutableModel):
    def run(self, input: EmptyInput) -> dict:
        return {'result': 3}


@ImmutableModel.describe(
    slug="example.immutable-good-output",
    version="0.1",
    display_name="Example for Immutable model with correct output",
    developer="Credmark",
    category='protocol',
    tags=['token'],
    input=EmptyInput,
    output=ImmutableOutput)
class ExampleImmutable(ImmutableModel):
    def run(self, input: EmptyInput) -> ImmutableOutput:
        # 1. Immutable model shall raise an error if result is not available before a block
        if self.context.block_number < 100:
            raise ModelDataError('Block number shall be greater than 100')
        # 2. Immutable model shall return the type of ImmutableOutput with the field `firstResultBlockNumber`.
        return ImmutableOutput(firstResultBlockNumber=100)


@IncrementalModel.describe(
    slug="example.incremental-wrong-output",
    version="0.1",
    display_name="Example for Incremental model with wrong output type",
    developer="Credmark",
    category='protocol',
    tags=['token'],
    input=EmptyInput,
    output=dict)
class ExampleIncrementalWrong(IncrementalModel):
    def run(self, input: EmptyInput, from_block: BlockNumber) -> dict:
        self.logger.info(f'{from_block=}')
        return {"result": 3}

# Returns 1 result
# credmark-dev run example.incremental-good-output-1 --api_url http://localhost:8700 -l - -j -b 10

# Returns 2 results
# credmark-dev run example.incremental-good-output-1 --api_url http://localhost:8700 -l - -j -b 100


@IncrementalModel.describe(
    slug="example.incremental-wrong-output-block-number",
    version="0.10",
    display_name="Example for Incremental model with wrong output in block number range",
    developer="Credmark",
    category='protocol',
    tags=['token'],
    input=EmptyInput,
    output=BlockSeries[int])
class ExampleIncrementalWrongBlockNumber(IncrementalModel):
    def run(self, input: EmptyInput, from_block: BlockNumber) -> BlockSeries[int]:
        self.logger.info(f'{from_block=}')
        # Incremental model shall return
        # 1. result of BlockSeriesRow type
        # 2. Results with block number less than or equal to the current block number
        # 3. Results with block number greater than or equal to `from_block`.
        # 4. blockNumber >= 0

        # Below output shall be filtered for block number range [from_block, self.context.block_number]
        # Added `.to_range` for BlockSeries object
        return BlockSeries(series=[
            BlockSeriesRow(
                blockNumber=0,
                blockTimestamp=BlockNumber(0).timestamp,
                sampleTimestamp=BlockNumber(0).timestamp,
                output=1
            ),
            BlockSeriesRow(
                blockNumber=100,
                blockTimestamp=BlockNumber(100).timestamp,
                sampleTimestamp=BlockNumber(100).timestamp,
                output=2
            ),
        ])


@IncrementalModel.describe(
    slug="example.incremental-good-output-block-number",
    version="0.10",
    display_name="Example for Incremental model with correct output in block number range",
    developer="Credmark",
    category='protocol',
    tags=['token'],
    input=EmptyInput,
    output=BlockSeries[int])
class ExampleIncrementalGoodBlockNumber(IncrementalModel):
    def run(self, input: EmptyInput, from_block: BlockNumber) -> BlockSeries[int]:
        self.logger.info(f'{from_block=}')
        """
        Incremental model shall return a parameterized class of `BlockSeries` with below requirements:
        1. Results with block number less than or equal to the current block number
        2. Results with block number greater than or equal to `from_block`.
        3. blockNumber >= 0

        Below output shall be filtered for block number range [from_block, self.context.block_number]
        Added `.to_range` for BlockSeries object
        """

        return BlockSeries(series=[
            BlockSeriesRow(
                blockNumber=0,
                blockTimestamp=BlockNumber(0).timestamp,
                sampleTimestamp=BlockNumber(0).timestamp,
                output=1
            ),
            BlockSeriesRow(
                blockNumber=100,
                blockTimestamp=BlockNumber(100).timestamp,
                sampleTimestamp=BlockNumber(100).timestamp,
                output=2
            ),
        ]).to_range(from_block, self.context.block_number)
