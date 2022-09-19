from credmark.cmf.model import Model
from credmark.dto import DTO, EmptyInput


class TimestampOutput(DTO):
    timestamp: int


@Model.describe(slug="chain.get-block-timestamp",
                version="0.1",
                display_name="Obtain block timestamp",
                description='In UTC',
                category='chain',
                input=EmptyInput,
                output=TimestampOutput)
class GetBlockTimestamp(Model):
    def run(self, _) -> TimestampOutput:
        return TimestampOutput(timestamp=self.context.block_number.timestamp)


class LatestBlock(DTO):
    block_number: int
    timestamp: int


@Model.describe(slug="chain.get-latest-block",
                version="0.1",
                display_name="Obtain latest block",
                description='block number and timestamp',
                category='chain',
                output=LatestBlock)
class GetLatestBlock(Model):
    def run(self, _) -> LatestBlock:
        block_number = self.context.web3.eth.get_block_number()
        block = self.context.web3.eth.get_block(block_number)
        block_timestamp = block.timestamp  # type: ignore
        return LatestBlock(block_number=block_number, timestamp=block_timestamp)
