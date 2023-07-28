from datetime import datetime, timedelta
from enum import Enum
from time import sleep
from typing import Any, Optional, Type, TypeVar
from urllib.parse import urljoin

import requests
from credmark.cmf.model import CachePolicy, Model
from credmark.cmf.model.errors import ModelDataError
from credmark.dto import DTO, DTOField
from requests import HTTPError, JSONDecodeError, Response


class DuneQueryState(str, Enum):
    PENDING = "QUERY_STATE_PENDING"
    EXECUTING = "QUERY_STATE_EXECUTING"
    FAILED = "QUERY_STATE_FAILED"
    COMPLETED = "QUERY_STATE_COMPLETED"
    CANCELLED = "QUERY_STATE_CANCELLED"
    EXPIRED = "QUERY_STATE_EXPIRED"


class DunePerformanceTier(str, Enum):
    MEDIUM = "medium"
    LARGE = "large"


T = TypeVar("T", bound=DTO)


class DuneClient:
    DEFAULT_TIMEOUT = 10

    @staticmethod
    def _handle_response(
        response: Response,
        dto_cls: Type[T]
    ) -> T:
        try:
            response.raise_for_status()
            return dto_cls.parse_obj(response.json())
        except HTTPError as err:
            raise ModelDataError("Error from Dune: " + str(err)) from None
        except JSONDecodeError:
            raise ModelDataError("Received invalid JSON from Dune.") from None

    @staticmethod
    def _route_url(route: str) -> str:
        return urljoin("https://api.dune.com/api/v1", route)

    def _get(self, *, api_key: str, route: str, dto_cls: Type[T]) -> T:
        url = self._route_url(route)
        response = requests.get(
            url,
            headers={"x-dune-api-key": api_key},
            timeout=self.DEFAULT_TIMEOUT,
        )

        return self._handle_response(response, dto_cls)

    def _post(self, *, api_key: str, route: str, params: Any = None, dto_cls: Type[T]) -> T:
        url = self._route_url(route)
        response = requests.post(
            url=url,
            json=params,
            headers={"x-dune-api-key": api_key},
            timeout=self.DEFAULT_TIMEOUT,
        )

        return self._handle_response(response, dto_cls)


class DuneBaseInput(DTO):
    api_key: str


class DuneQueryInput(DuneBaseInput):
    query_id: str

    class Config:
        schema_extra = {
            'skip_test': True
        }


class DuneExecuteQueryInput(DuneQueryInput):
    performance: Optional[DunePerformanceTier]
    query_parameters: Optional[dict]

    class Config:
        schema_extra = {
            'skip_test': True
        }


class DuneExecuteQueryOutput(DTO):
    execution_id: str
    state: DuneQueryState


@Model.describe(
    slug="dune.execute-query",
    version="1.0",
    display_name="Dune - Execute query",
    description="Execute (run) a query for a specific query id.",
    category="external",
    subcategory="dune",
    cache=CachePolicy.SKIP,
    input=DuneExecuteQueryInput,
    output=DuneExecuteQueryOutput)
class DuneExecuteQuery(Model, DuneClient):
    def run(self, input: DuneExecuteQueryInput) -> DuneExecuteQueryOutput:
        params = {}
        if input.performance is not None:
            params["performance"] = input.performance
        if input.query_parameters is not None:
            params["query_parameters"] = input.query_parameters

        return self._post(api_key=input.api_key,
                          route=f"query/{input.query_id}/execute",
                          params=params,
                          dto_cls=DuneExecuteQueryOutput)


class DuneExecutionInput(DuneBaseInput):
    execution_id: str

    class Config:
        schema_extra = {
            'skip_test': True
        }


class DuneResultMetadata(DTO):
    column_names: list[str]
    result_set_bytes: int
    total_row_count: int
    datapoint_count: int
    pending_time_millis: int
    execution_time_millis: int


class BaseExecutionStatus(DTO):
    execution_id: str
    query_id: str
    state: DuneQueryState
    submitted_at: datetime
    expires_at: Optional[datetime]
    execution_started_at: Optional[datetime]
    execution_ended_at: Optional[datetime]


class DuneExecutionStatus(BaseExecutionStatus):
    result_metadata: Optional[DuneResultMetadata]

    def is_done(self):
        return self.state not in [DuneQueryState.PENDING, DuneQueryState.EXECUTING]

    def raise_for_error(self):
        if self.state == DuneQueryState.CANCELLED:
            raise ModelDataError("Query was cancelled.")
        if self.state == DuneQueryState.FAILED:
            raise ModelDataError("Query has failed.")
        if self.state == DuneQueryState.EXPIRED:
            raise ModelDataError("Query has expired.")


@Model.describe(
    slug="dune.get-execution-status",
    version="1.0",
    display_name="Dune - Get execution status",
    category="external",
    subcategory="dune",
    cache=CachePolicy.SKIP,
    input=DuneExecutionInput,
    output=DuneExecutionStatus)
class DuneGetExecutionStatus(Model, DuneClient):
    def run(self, input: DuneExecutionInput) -> DuneExecutionStatus:
        return self._get(api_key=input.api_key,
                         route=f"execution/{input.execution_id}/status",
                         dto_cls=DuneExecutionStatus)


class DuneExecutionResult(DTO):
    rows: list[dict]
    metadata: DuneResultMetadata


class DuneExecutionResults(BaseExecutionStatus):
    result: DuneExecutionResult


@Model.describe(
    slug="dune.get-execution-results",
    version="1.0",
    display_name="Dune - Get execution results",
    category="external",
    subcategory="dune",
    cache=CachePolicy.SKIP,
    input=DuneExecutionInput,
    output=DuneExecutionResults)
class DuneGetExecutionResults(Model, DuneClient):
    def run(self, input: DuneExecutionInput) -> DuneExecutionResults:
        return self._get(api_key=input.api_key,
                         route=f"execution/{input.execution_id}/results",
                         dto_cls=DuneExecutionResults)


@Model.describe(
    slug="dune.get-latest-query-results",
    version="1.0",
    display_name="Dune - Get latest query results",
    category="external",
    subcategory="dune",
    cache=CachePolicy.SKIP,
    input=DuneQueryInput,
    output=DuneExecutionResults)
class DuneGetLatestQueryResults(Model, DuneClient):
    def run(self, input: DuneQueryInput) -> DuneExecutionResults:
        return self._get(api_key=input.api_key,
                         route=f"query/{input.query_id}/results",
                         dto_cls=DuneExecutionResults)


class DuneCancelExecutionOutput(DTO):
    success: bool = DTOField(
        description="Whether the request to cancel the query execution was made successfully")


@Model.describe(
    slug="dune.cancel-execution",
    version="1.0",
    display_name="Dune - Cancel execution",
    category="external",
    subcategory="dune",
    cache=CachePolicy.SKIP,
    input=DuneExecutionInput,
    output=DuneCancelExecutionOutput)
class DuneCancelExecution(Model, DuneClient):
    def run(self, input: DuneExecutionInput) -> DuneCancelExecutionOutput:
        return self._post(api_key=input.api_key,
                          route=f"execution/{input.execution_id}/cancel",
                          dto_cls=DuneCancelExecutionOutput)


class DuneRunQueryInput(DuneQueryInput):
    sleep: int = DTOField(
        5, gt=5, lt=1800, description="Duration (in seconds) to sleep between status checks.")
    timeout: int = DTOField(
        120, gt=5, lt=1800, description="Timeout (in seconds)")

    class Config:
        schema_extra = {
            'skip_test': True
        }


@Model.describe(
    slug="dune.run-query",
    version="1.0",
    display_name="Dune - Run query",
    category="external",
    subcategory="dune",
    cache=CachePolicy.SKIP,
    input=DuneRunQueryInput,
    output=DuneExecutionResults)
class DuneRunQuery(Model, DuneClient):
    def run(self, input: DuneRunQueryInput) -> DuneExecutionResults:
        expiry_time = datetime.now() + timedelta(seconds=input.timeout)
        execute_result = self.context.run_model('dune.execute-query',
                                                input=input, return_type=DuneExecuteQueryOutput,
                                                local=True)
        status_result = None
        while expiry_time > datetime.now():
            status_result = self.context.run_model('dune.get-execution-status',
                                                   input={
                                                       "api_key": input.api_key,
                                                       "execution_id": execute_result.execution_id
                                                   },
                                                   return_type=DuneExecutionStatus,
                                                   local=True)

            if status_result.is_done():
                status_result.raise_for_error()
                return self.context.run_model('dune.get-execution-results',
                                              input={
                                                  "api_key": input.api_key,
                                                  "execution_id": execute_result.execution_id
                                              },
                                              return_type=DuneExecutionResults,
                                              local=True)

            sleep(input.sleep)

        try:
            self.context.run_model('dune.cancel-execution',
                                   input={
                                       "api_key": input.api_key,
                                       "execution_id": execute_result.execution_id
                                   },
                                   local=True)
        except ModelDataError:
            raise ModelDataError(
                'Execution timed out. Unable to cancel execution: '
                f'{execute_result.execution_id}') from None

        raise ModelDataError("Execution has timed out. ")
