from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelErrorDTO
from credmark.cmf.types.compose import (MapBlockTimeSeriesOutput)
from credmark.cmf.types.series import BlockSeries, BlockSeriesRow, BlockSeriesErrorRow
from models.dtos.historical import HistoricalRunModelInput


@Model.describe(slug="historical.run-model",
                version="1.2",
                display_name="Run Any model for historical",
                description="",
                input=HistoricalRunModelInput,
                output=dict)
class HistoricalRunModel(Model):
    def run(self, input: HistoricalRunModelInput) -> dict:
        window_in_seconds = self.context.historical.to_seconds(input.window)
        interval_in_seconds = self.context.historical.to_seconds(input.interval)
        count = int(window_in_seconds / interval_in_seconds)

        price_historical_result = self.context.run_model(
            slug='compose.map-block-time-series',
            input={"modelSlug": input.model_slug,
                   "modelInput": input.model_input,
                   "endTimestamp": self.context.block_number.timestamp,
                   "interval": interval_in_seconds,
                   "count": count,
                   "exclusive": False},
            return_type=MapBlockTimeSeriesOutput[dict])

        results = BlockSeries(
            series=[],
            errors=None)

        for result in price_historical_result:
            if result.error is not None:
                if results.errors is None:
                    results.errors = []
                results.errors.append(
                    BlockSeriesErrorRow(
                        blockNumber=result.blockNumber,
                        blockTimestamp=result.blockNumber.timestamp,
                        sampleTimestamp=result.blockNumber.timestamp,
                        error=result.error))
            if result.output is None:
                if results.errors is None:
                    results.errors = []
                results.errors.append(
                    BlockSeriesErrorRow(
                        blockNumber=result.blockNumber,
                        blockTimestamp=result.blockNumber.timestamp,
                        sampleTimestamp=result.blockNumber.timestamp,
                        error=ModelErrorDTO(
                            type='ModelRunError',
                            message=f'Historical Run had problem with {result.blockNumber}',
                            stack=[],
                            code='',
                            detail=None,
                            permanent=False)))

            results.series.append(BlockSeriesRow(blockNumber=result.blockNumber,
                                                 blockTimestamp=result.blockNumber.timestamp,
                                                 sampleTimestamp=result.blockNumber.timestamp,
                                                 output=result.output))

        return {'result': results}
