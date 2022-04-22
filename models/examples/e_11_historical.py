from typing import Any, List
from credmark.cmf.model import Model
from credmark.dto import DTO


class RunModelHistorical(DTO):
    model_slug: str
    model_input: dict


@Model.describe(slug='example.historical', version="1.0", input=RunModelHistorical)
class ExampleHistorical(Model):

    """
    This model returns the library example for every day for the past 30 days
    """

    def run(self, input: RunModelHistorical) -> dict:
        model_slug = input.model_slug
        model_input = input.model_input

        res = self.context.historical.run_model_historical(
            model_slug,
            window='5 hours',
            interval='45 minutes',
            model_input=model_input)

        #  You can get historical elements by blocknumber,
        #  You can get historical elements by time,
        #  or you can iterate through them by index.

        block = res.get(timestamp=1646007299 + (45 * 60))
        if block is not None:
            assert block.output

        block = res.get(block_number=14291219)
        if block is not None:
            assert block.output

        self.logger.info(res[3].dict())

        return res.dict()


@Model.describe(slug='example.historical-snap', version="1.0")
class ExampleHistoricalSnap(Model):

    """
    This model returns the library example for every day for the past 30 days
    """

    def run(self, input):
        class LibrariesDto(DTO):
            libraries: List[Any]

        blocks = self.context.historical.run_model_historical(
            'example.libraries',
            window='5 days',
            interval='1 day',
            snap_clock='1 day',
            model_return_type=LibrariesDto)
        for block in blocks:
            # block.output is type LibrariesDto
            assert block.output.libraries
        return blocks


@Model.describe(slug='example.historical-block-snap', version="1.0")
class ExampleHistoricalBlockSnap(Model):

    """
    This model returns the library example for every day for the past 30 days
    with interval of 100, with end block snapped to the multiples of snap of 153
    """

    def run(self, input):
        return self.context.historical.run_model_historical_blocks(
            'example.echo',
            window=500,
            interval=100,
            snap_block=153)


@Model.describe(slug='example.historical-block', version="1.0")
class ExampleHistoricalBlock(Model):

    """
    This model returns the library example for every day for the past 30 days
    """

    def run(self, input):
        return self.context.historical.run_model_historical_blocks(
            'example.libraries',
            window=500,
            interval=100,
            snap_block=None)
