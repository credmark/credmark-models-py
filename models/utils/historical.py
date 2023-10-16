# pylint:disable=no-member
from credmark.cmf.model import CachePolicy, Model
from credmark.cmf.model.errors import ModelBaseError, ModelErrorDTO
from credmark.cmf.types.compose import (
    MapBlockTimeSeriesOutput,
)
from credmark.cmf.types.series import BlockSeries, BlockSeriesErrorRow, BlockSeriesRow

from models.dtos.historical import HistoricalRunModelInput


@Model.describe(slug="historical.empty",
                version="1.4",
                display_name="An empty model to obtain block numbers",
                description="",
                category='utility',
                subcategory='composer',
                output=dict)
class HistoricalEmpty(Model):
    def run(self, _) -> dict:
        return {}


@Model.describe(slug="historical.run-model",
                version="1.4",
                display_name="Run Any model for historical",
                description="Input of window and interval in plain words - 30 days / 1 day",
                category='utility',
                subcategory='composer',
                cache=CachePolicy.SKIP,
                input=HistoricalRunModelInput,
                output=BlockSeries)
class HistoricalRunModel(Model):
    def to_seconds(self, time_str) -> int:
        historical = self.context.historical
        return historical.range_timestamp(*historical.parse_timerangestr(time_str))

    def run(self, input: HistoricalRunModelInput) -> BlockSeries:
        window_in_seconds = self.context.historical.to_seconds(input.window)
        interval_in_seconds = self.context.historical.to_seconds(
            input.interval)
        count = int(window_in_seconds / interval_in_seconds)

        if not input.debug:
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
                results.series.append(out_row)  # type: ignore

            return results

        # debug mode
        empty_series = self.context.run_model(
            slug='compose.map-block-time-series',
            input={"modelSlug": 'historical.empty',
                   "modelInput": {},
                   "endTimestamp": self.context.block_number.timestamp,
                   "interval": interval_in_seconds,
                   "count": count,
                   "exclusive": input.exclusive},
            return_type=MapBlockTimeSeriesOutput[dict])

        results = BlockSeries(
            series=[],
            errors=None)

        blocks = [x.blockNumber for x in empty_series.results]
        for _n_block, block_number in enumerate(blocks):
            block_timestamp = block_number.timestamp
            try:
                output = self.context.run_model(
                    input.model_slug, input.model_input, block_number=block_number)
                out_row = BlockSeriesRow(blockNumber=block_number,
                                         blockTimestamp=block_timestamp,
                                         sampleTimestamp=block_timestamp,
                                         output=output)
                results.series.append(out_row)  # type: ignore

            except ModelBaseError as err:
                if not results.errors:
                    results.errors = []
                results.errors.append(
                    BlockSeriesErrorRow(
                        blockNumber=block_number,
                        blockTimestamp=block_timestamp,
                        sampleTimestamp=block_timestamp,
                        error=ModelErrorDTO(
                            type=err.dto_class.__name__,
                            message=err.data.message,
                            stack=[],
                            code='',
                            detail=None,
                            permanent=False)))

        return results
