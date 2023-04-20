from credmark.cmf.model import Model
from credmark.dto import DTO, EmptyInput

from credmark.cmf.model.errors import (ModelDataError)


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
        block_timestamp = self.context.web3.eth.get_block(
            input.block_number)['timestamp']  # type: ignore
        return TimestampOutput(timestamp=block_timestamp)


class BlockInput(DTO):
    timestamp: int


class BlockOutput(DTO):
    block_number: int
    block_timestamp: int
    sample_timestamp: int


@Model.describe(slug="chain.get-block",
                version="0.1",
                display_name="Obtain block from timestamp",
                description='In UTC',
                category='chain',
                input=BlockInput,
                output=BlockOutput)
class GetBlock(Model):
    timestamp_by_block = {}

    def binary_search(self, low, high, timestamp):
        # Check base case
        assert high >= low
        mid = (high + low)//2
        if high == low:
            return low, self.timestamp_by_block[low]

        if self.timestamp_by_block.get(mid) is None:
            mid_time = self.context.web3.eth.get_block(
                mid)['timestamp']  # type: ignore
            self.timestamp_by_block[mid] = mid_time
        else:
            mid_time = self.timestamp_by_block[mid]

        if mid_time == timestamp:
            return mid, mid_time
        elif high - low == 1:
            return low, self.timestamp_by_block[low]
        elif mid_time < timestamp:
            return self.binary_search(mid, high, timestamp)
        elif mid_time > timestamp:
            return self.binary_search(low, mid-1, timestamp)
        else:
            return -1, -1

    def run(self, input: BlockInput) -> BlockOutput:
        if self.context.block_number != 0:
            return self.context.run_model(self.slug, input, block_number=0, return_type=BlockOutput)

        start_time = self.context.run_model(
            'chain.get-block-timestamp', input={'block_number': 0})
        end_time = self.context.run_model(
            'chain.get-latest-block')

        self.timestamp_by_block[0] = start_time['timestamp']
        self.timestamp_by_block[
            end_time["blockNumber"]] = end_time["timestamp"]

        if input.timestamp < start_time['timestamp']:
            raise ModelDataError(
                f'{input.timestamp=} is before the first block ({start_time["timestamp"]})')

        if input.timestamp > end_time['timestamp']:
            raise ModelDataError(f'{input.timestamp=} is after the the latest block '
                                 f'({end_time["blockNumber"]} @ {end_time["timestamp"]})')

        block_number, block_timestamp = self.binary_search(
            0, end_time['blockNumber'], input.timestamp)

        return BlockOutput(
            block_number=block_number,
            block_timestamp=block_timestamp,
            sample_timestamp=input.timestamp)


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
