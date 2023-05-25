# pylint: disable=line-too-long
import math

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import Network, NetworkDict
from credmark.dto import DTO, EmptyInput


class TimestampInput(DTO):
    block_number: int

    class Config:
        schema_extra = {
            'examples': [{'block_number': 16_837_261}]
        }


class TimestampOutput(DTO):
    timestamp: int


@Model.describe(slug="chain.get-block-timestamp",
                version="0.2",  # DO NOT CHANGE THIS VERSION
                display_name="Obtain block timestamp",
                description='In UTC',
                category='chain',
                input=TimestampInput,
                output=TimestampOutput)
class GetBlockTimestamp(Model):
    def run(self, input: TimestampInput) -> TimestampOutput:
        block_timestamp = self.context.web3.eth.get_block(
            input.block_number)['timestamp']  # type: ignore
        return TimestampOutput(timestamp=block_timestamp)


class BlockInput(DTO):
    timestamp: int

    class Config:
        schema_extra = {
            'examples': [
                {'timestamp': 1683726143, '_test_multi_chain': {'chain_id': 1}}] +
            [{"timestamp": 1628599999, '_test_multi_chain': {'chain_id': chain_id, 'block_number': None}}
                for chain_id in [137, 10, 42161, 56, 250, 43114]],
            'test_multi_chain': True,
        }


class BlockOutput(DTO):
    block_number: int
    block_timestamp: int
    sample_timestamp: int


class Block(DTO):
    block_number: int
    timestamp: int


@Model.describe(slug="chain.get-block",
                version="0.3",  # CAN CHANGE THIS VERSION
                display_name="Obtain block from timestamp",
                description='In UTC',
                category='chain',
                input=BlockInput,
                output=BlockOutput)
class GetBlock(Model):
    def get_block(self, number: int) -> Block:
        output = self.context.run_model(
            "chain.get-block-timestamp",
            input=TimestampInput(block_number=number),
            local=True,
            return_type=TimestampOutput)
        return Block(block_number=number, timestamp=output.timestamp)

    def get_latest_block(self) -> Block:
        output = self.context.run_model(
            "chain.get-latest-block", {}, local=True, return_type=LatestBlock)
        return Block(block_number=output.blockNumber, timestamp=output.timestamp)

    def get_closest_block(self,
                          timestamp: int,
                          start: Block,
                          end: Block) -> Block:
        start_block = start.block_number
        end_block = end.block_number

        if start_block == end_block:
            return start
        # Return the closer one, if we're already between blocks
        if (start_block == end_block - 1
                or timestamp <= start.timestamp
                or timestamp >= end.timestamp):
            return start if abs(timestamp - start.timestamp) < abs(timestamp - end.timestamp) else end

        # K is how far in between start and end we're expected to be
        k = (timestamp - start.timestamp) / (end.timestamp - start.timestamp)
        # We bound, to ensure logarithmic time even when guesses aren't great
        k = min(max(k, 0.05), 0.95)
        # We get the expected block number from K
        expected_block_number = round(
            start_block + k * (end_block - start_block))
        # Make sure to make some progress
        expected_block_number = min(
            max(expected_block_number, start_block + 1), end_block - 1)

        # Get the actual timestamp for that block
        expected_block = self.get_block(expected_block_number)
        expected_block_timestamp = expected_block.timestamp

        # Adjust bound using our estimated block
        if expected_block_timestamp < timestamp:
            start = expected_block
        elif expected_block_timestamp > timestamp:
            end = expected_block
        else:
            # Return the perfect match
            return expected_block

        # Recurse using tightened bounds
        return self.get_closest_block(timestamp, start, end)

    def run(self, input: BlockInput) -> BlockOutput:
        start = self.get_block(0)
        if input.timestamp < start.timestamp:
            raise ModelDataError(
                f'{input.timestamp=} is before the first block ({start.timestamp})')

        end = self.get_latest_block()
        if input.timestamp > end.timestamp:
            return BlockOutput(block_number=end.block_number,
                               block_timestamp=end.timestamp,
                               sample_timestamp=input.timestamp)

        closest_block = self.get_closest_block(input.timestamp, start, end)

        return BlockOutput(block_number=closest_block.block_number,
                           block_timestamp=closest_block.timestamp,
                           sample_timestamp=input.timestamp)


class EmptyInputForLatestBlock(EmptyInput):
    class Config:
        schema_extra = {
            'examples': [{'_test_multi_chain': {'chain_id': chain_id, 'block_number': None}}
                         for chain_id in [1, 137, 10, 42161, 56, 250, 43114]],
            'test_multi_chain': True
        }


class LatestBlock(DTO):
    blockNumber: int
    timestamp: int


@Model.describe(slug="chain.get-latest-block",
                version="0.1",  # DO NOT CHANGE THIS VERSION
                display_name="Obtain latest block",
                description='block number and timestamp',
                category='chain',
                input=EmptyInputForLatestBlock,
                output=LatestBlock)
class GetLatestBlock(Model):
    time_between_blocks = NetworkDict(int, {
        Network.Mainnet: 12,
        Network.Optimism: 0.33,
        Network.BSC: 3,
        Network.Polygon: 2,
        Network.Fantom: 1,
        Network.ArbitrumOne: 0.25,
        Network.Avalanche: 2,
    })

    offset_time = 60

    def run(self, _) -> LatestBlock:
        # This takes care of {code: -32000, message: "header not found"} error
        block_time = self.time_between_blocks[self.context.chain_id]
        if block_time > 0:
            offset_blocks = math.ceil(self.offset_time / block_time)
        else:
            offset_blocks = 0

        original_default_block = self.context.web3.eth.default_block
        self.context.web3.eth.default_block = 'latest'
        block = self.context.web3.eth.get_block("latest")
        block_number = block.number - offset_blocks  # type: ignore
        block_timestamp = self.context.web3.eth.get_block(block_number).timestamp  # type: ignore
        self.context.web3.eth.default_block = original_default_block
        return LatestBlock(blockNumber=block_number, timestamp=block_timestamp)
