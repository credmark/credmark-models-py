from typing import Union
import credmark.cmf.model
from credmark.dto import DTO, DTOField
from credmark.cmf.model.errors import ModelDataError, ModelDataErrorDTO
from enum import Enum

class HistoricalInputDataError(ModelDataError):
    dto_class = ModelDataErrorDTO

    @classmethod
    def create(cls, prop:str, desired_type:str):
        message = f'Property "{prop}" myst be {desired_type} '\
        'To use other time data types, set historical_model_type to the desired type.'
        return ModelDataError(message=message)

class HistoricalModelType(Enum):
    TIMESTRING = "timestring"
    TIMESTAMP = "timestamp"
    DATETIME = "datetime"
    BLOCKNUMBER = "blocknumber"

class HistoricalDTO(DTO):

    slug: str = DTOField(description="The slug of the model to run historically")

    version: Union[str,None] = DTOField(
        default=None,
        description="The version of the model that you want to run historically")

    input: Union[dict, DTO] = DTOField(
        default={},
        description="The data input of the model to be run.")

    window: Union[int, str] = DTOField(
        default="30 days",
        description="The size of the window to run the model within. "
            "For time-based models, use a timerange string e.g. '10 days'. "
            "for blocknumber based historical queries, use the maximum number of blocks to run the model within.")

    interval: Union[int, str, None] = DTOField(
        default=None,
        description="The size of the interval that will be run historically. "
            "For time-based models, use a timerange string e.g. '1 day'. "
            "for blocknumber based historical queries, use the number of blocks to skip.")

    snap_to_crossings: bool = DTOField(
        default=True,
        description="If true, the time will snap to the nearest interval crossing in UTC, "
            "or the nearest blocknumber that is divisible by that interval.")
    end: Union[int, None] = DTOField(
        default=None,
        description="If you want to execute this model so that it "
            "ends at a specific point in the past, "
            "set this to the timestamp or blocknumber you wish to end at.")
    historical_model_type: HistoricalModelType = DTOField(
        default=HistoricalModelType.TIMESTRING,
        description="The type of historical query to be run."
        " Options are: timestring, timestamp, datetime, or blocknumber")


@credmark.cmf.model.describe(
    slug="historical.run",
    version="1.0",
    display_name="Historical",
    description="Run a model historically",
    input=HistoricalDTO,
    developer="Credmark")

class Historical(credmark.cmf.model.Model):
    def run(self, input: HistoricalDTO):

        if input.historical_model_type == HistoricalModelType.DATETIME:
            raise NotImplementedError()

        if input.historical_model_type == HistoricalModelType.TIMESTAMP:
            raise NotImplementedError()

        if input.historical_model_type == HistoricalModelType.TIMESTRING:
            if not isinstance(input.window, str):
                raise HistoricalInputDataError.create("window", "str")

            if isinstance(input.interval, int):
                raise HistoricalInputDataError.create("interval", "Union[str, None]")

            return self.context.historical.run_model_historical(
                model_slug=input.slug,
                window=input.window,
                interval=input.interval,
                model_input=input.input,
                model_version= input.version,
                end_timestamp=input.end
            )
        if input.historical_model_type == HistoricalModelType.BLOCKNUMBER:
            if not isinstance(input.window, int):
                raise HistoricalInputDataError.create("window", "int")

            if not isinstance(input.interval, int):
                raise HistoricalInputDataError.create("interval", "int")

            return self.context.historical.run_model_historical_blocks(
                model_slug=input.slug,
                window=input.window,
                interval=input.interval,
                model_input=input.input,
                model_version= input.version,
                end_block=input.end
            )
