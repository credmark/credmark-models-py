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
