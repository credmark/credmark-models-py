from credmark.cmf.model import Model
from credmark.dto import EmptyInput
from credmark.cmf.model.errors import ModelErrorDTO
from credmark.cmf.types.compose import MapBlockTimeSeriesOutput
from credmark.cmf.types.series import (BlockSeries, BlockSeriesErrorRow,
                                       BlockSeriesRow)
from models.dtos.historical import HistoricalRunModelInput


@Model.describe(slug="historical.empty",
                version="1.4",
                display_name="An empty model to obtain block numbers",
                description="",
                category='utility',
                subcategory='composer',
                input=EmptyInput,
                output=dict)
class HistoricalEmpty(Model):
    def run(self, _: EmptyInput) -> dict:
        return {}


@Model.describe(slug="historical.run-model",
                version="1.4",
                display_name="Run Any model for historical",
                description="Input of window and interval in plain words - 30 days / 1 day",
                category='utility',
                subcategory='composer',
                input=HistoricalRunModelInput,
                output=BlockSeries)
class HistoricalRunModel(Model):
    def to_seconds(self, time_str) -> int:
        historical = self.context.historical
        return historical.range_timestamp(*historical.parse_timerangestr(time_str))

    def run(self, input: HistoricalRunModelInput) -> BlockSeries:
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
                   "exclusive": input.exclusive},
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

            out_row = BlockSeriesRow(blockNumber=result.blockNumber,
                                     blockTimestamp=result.blockNumber.timestamp,
                                     sampleTimestamp=result.blockNumber.timestamp,
                                     output=result.output)
            results.series.append(out_row)  # type: ignore #pylint:disable=no-member

        return results
