import credmark.model
from credmark.types.dto import DTO, DTOField


@credmark.model.describe(slug='example-historical', version="1.0")
class ExampleHistorical(credmark.model.Model):

    """
    This model returns the library example for every day for the past 30 days
    """

    def run(self, input):
        return self.context.historical.run_model_historical('example-libraries', window='5 hours', interval='45 minutes')


@credmark.model.describe(slug='example-historical-snap', version="1.0")
class ExampleHistoricalSnap(credmark.model.Model):

    """
    This model returns the library example for every day for the past 30 days
    """

    def run(self, input):
        return self.context.historical.run_model_historical('example-libraries', '5 days', snap_clock=None)


@credmark.model.describe(slug='example-historical-block-snap', version="1.0")
class ExampleHistoricalBlockSnap(credmark.model.Model):

    """
    This model returns the library example for every day for the past 30 days
    """

    def run(self, input):
        return self.context.historical.run_model_historical_blocks('example-libraries', window=500, interval=100, snap_block=100)


@credmark.model.describe(slug='example-historical-block', version="1.0")
class ExampleHistoricalBlock(credmark.model.Model):

    """
    This model returns the library example for every day for the past 30 days
    """

    def run(self, input):
        return self.context.historical.run_model_historical_blocks('example-libraries', window=500, interval=100, snap_block=None)
