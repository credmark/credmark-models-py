import credmark.model
from credmark.types.dto import DTO, DTOField


class SeriesInput(DTO):
    slug: str = DTOField(..., description='The name of the model you want to run.')
    input: dict = DTOField(..., description='The model Inputs')


@credmark.model.describe(slug='example-30-day-series',
                         version='1.0',
                         display_name='(Example) 30 day window',
                         description='30 samples of a model with a day interval, back from the contexts block number',
                         input=SeriesInput
                         )
class Example30DaySeries(credmark.model.Model):

    """
    This example runs the series model on any model.

    command: `credmark-dev run example-30-day-series --input '{"slug":"echo", "input":{"message":"hello world"}}' --api_url=http://localhost:7000/v1/models/run -b 14234904`

    """

    def run(self, input: SeriesInput) -> dict:

        res = self.context.run_model('series.time-window-interval', {
                                     "modelSlug": input.slug,
                                     "window": (30 * 86400),
                                     "interval": 86400,
                                     "modelInput": input.input})
        return res
