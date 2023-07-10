from credmark.cmf.model import ImmutableModel, ImmutableOutput, IncrementalModel
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import (
    BlockNumber,
)
from credmark.cmf.types.series import BlockSeries, BlockSeriesRow
from credmark.dto import EmptyInput


@ImmutableModel.describe(
    slug="example.immutable-wrong-output",
    version="0.1",
    display_name="Token Information - deployment",
    developer="Credmark",
    category='protocol',
    tags=['token'],
    input=EmptyInput,
    output=dict)
class ExampleImmutableWrong(ImmutableModel):
    def run(self, input: EmptyInput) -> dict:
        return {'result': 3}


@ImmutableModel.describe(
    slug="example.immutable",
    version="0.1",
    display_name="Token Information - deployment",
    developer="Credmark",
    category='protocol',
    tags=['token'],
    input=EmptyInput,
    output=ImmutableOutput)
class ExampleImmutable(ImmutableModel):
    def run(self, input: EmptyInput) -> ImmutableOutput:
        if self.context.block_number < 100:
            raise ModelDataError('Block number shall be greater than 100')
        return ImmutableOutput(firstResultBlockNumber=100)


@IncrementalModel.describe(
    slug="example.incremental-wrong-output",
    version="0.1",
    display_name="Token Information - deployment",
    developer="Credmark",
    category='protocol',
    tags=['token'],
    input=EmptyInput,
    output=dict)
class ExampleIncrementalWrong(IncrementalModel):
    def run(self, input: EmptyInput, from_block: BlockNumber) -> dict:
        self.logger.info(f'{from_block=}')
        return {"result": 3}


@IncrementalModel.describe(
    slug="example.incremental",
    version="0.1",
    display_name="Token Information - deployment",
    developer="Credmark",
    category='protocol',
    tags=['token'],
    input=EmptyInput,
    output=BlockSeries[int])
class ExampleIncremental(IncrementalModel):
    def run(self, input: EmptyInput, from_block: BlockNumber) -> BlockSeries[int]:
        self.logger.info(f'{from_block=}')
        return BlockSeries(series=[
            BlockSeriesRow(
                blockNumber=0,
                blockTimestamp=0,
                sampleTimestamp=0,
                output=1
            ),
            BlockSeriesRow(
                blockNumber=1,
                blockTimestamp=1,
                sampleTimestamp=1,
                output=2
            ),
        ])
