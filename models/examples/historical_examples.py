import credmark.model
from credmark.dto import DTO
from models.examples.library_examples import LibrariesDto


class RunModelHistorical(DTO):
    model_slug: str
    model_input: dict


@credmark.model.describe(slug='example.historical', version="1.0", input=RunModelHistorical)
class ExampleHistorical(credmark.model.Model):

    """
    This model returns the library example for every day for the past 30 days
    """

    def run(self, input: RunModelHistorical) -> dict:
        model_slug = input.model_slug
        model_input = input.model_input

        res = self.context.historical.run_model_historical(
            model_slug, window='5 hours', interval='45 minutes', model_input=model_input)

        #   You can get historical elements by blocknumber,
        #    You can get historical elements by time,
        #   or you can iterate through them by index.

        block = res.get(timestamp=1646007299 + (45 * 60))
        if block is not None:
            assert block.output

        block = res.get(block_number=14291219)
        if block is not None:
            assert block.output

        self.logger.info(res[3].dict())

        return res.dict()


@credmark.model.describe(slug='example.historical-snap', version="1.0")
class ExampleHistoricalSnap(credmark.model.Model):

    """
    This model returns the library example for every day for the past 30 days
    """

    def run(self, input):
        blocks = self.context.historical.run_model_historical(
            'example.libraries', '5 days', snap_clock=None,
            model_return_type=LibrariesDto)
        for block in blocks:
            # block.output is type LibrariesDto
            assert block.output.libraries
        return blocks


@credmark.model.describe(slug='example.historical-block-snap', version="1.0")
class ExampleHistoricalBlockSnap(credmark.model.Model):

    """
    This model returns the library example for every day for the past 30 days
    """

    def run(self, input):
        return self.context.historical.run_model_historical_blocks(
            'example.echo',
            model_input={
                "message": "hello world"},
            window=500, interval=100, snap_block=100)


@credmark.model.describe(slug='example.historical-block', version="1.0")
class ExampleHistoricalBlock(credmark.model.Model):

    """
    This model returns the library example for every day for the past 30 days
    """

    def run(self, input):
        return self.context.historical.run_model_historical_blocks('example.libraries', window=500, interval=100, snap_block=None)
