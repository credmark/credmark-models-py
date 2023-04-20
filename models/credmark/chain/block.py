from credmark.cmf.model import Model
from credmark.cmf.types import BlockNumber
from credmark.dto import DTO, EmptyInput


class TimestampInput(DTO):
    block_number: int


class TimestampOutput(DTO):
    timestamp: int


@Model.describe(slug="chain.get-block-timestamp",
                version="0.2",
                display_name="Obtain block timestamp",
                description='In UTC',
                category='chain',
                input=TimestampInput,
                output=TimestampOutput)
class GetBlockTimestamp(Model):
    def run(self, input: TimestampInput) -> TimestampOutput:
        return TimestampOutput(timestamp=BlockNumber(input.block_number).timestamp)


class LatestBlock(DTO):
    blockNumber: int
    timestamp: int


@Model.describe(slug="chain.get-latest-block",
                version="0.1",
                display_name="Obtain latest block",
                description='block number and timestamp',
                category='chain',
                input=EmptyInput,
                output=LatestBlock)
class GetLatestBlock(Model):
    def run(self, _) -> LatestBlock:
        block = self.context.web3.eth.get_block("latest")
        block_number = block.number  # type: ignore
        block_timestamp = block.timestamp  # type: ignore
        return LatestBlock(blockNumber=block_number, timestamp=block_timestamp)
