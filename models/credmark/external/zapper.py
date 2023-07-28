from datetime import datetime, timedelta
from time import sleep
from typing import Type, TypeVar
from urllib.parse import urljoin

import requests
from credmark.cmf.model import CachePolicy, Model
from credmark.cmf.model.errors import ModelDataError
from credmark.dto import DTO
from requests import HTTPError, JSONDecodeError, Response
from requests.auth import HTTPBasicAuth

from models.credmark.external.zapper_dto import (
    ZapperApp,
    ZapperAppInput,
    ZapperAppPositionsInput,
    ZapperAppPositionsOutput,
    ZapperAppPositionsResponse,
    ZapperAppsOutput,
    ZapperAppsResponse,
    ZapperAppTokensInput,
    ZapperAppTokensOutput,
    ZapperAppTokensResponse,
    ZapperBalancesJobStatusInput,
    ZapperBalancesJobStatusOutput,
    ZapperBalancesOutput,
    ZapperBalancesResponse,
    ZapperCollectionsBalancesInput,
    ZapperCollectionsBalancesOutput,
    ZapperCollectionsTotalsInput,
    ZapperCollectionsTotalsOutput,
    ZapperGetBalancesInput,
    ZapperInput,
    ZapperJobStatus,
    ZapperNftBalancesInput,
    ZapperNftBalancesOutput,
    ZapperNftNetWorthInput,
    ZapperNftNetWorthOutput,
    ZapperNftNetWorthResponse,
    ZapperNftTotalsInput,
    ZapperNftTotalsOutput,
    ZapperNftUserTokensInput,
    ZapperRefreshBalancesInput,
    ZapperRefreshBalancesOutput,
    ZapperTokenBalancesOutput,
    ZapperTokenBalancesResponse,
)

T = TypeVar("T", bound=DTO)


class ZapperClient:
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
            raise ModelDataError("Error from zapper: " + str(err)) from None
        except JSONDecodeError:
            raise ModelDataError("Received invalid JSON from Zapper.") from None

    @staticmethod
    def _route_url(route: str) -> str:
        return urljoin("https://api.zapper.xyz", route)

    def _get(self, *, api_key: str, route: str, query_params, dto_cls: Type[T]) -> T:
        url = self._route_url(route)
        response = requests.get(
            url,
            params=query_params,
            auth=HTTPBasicAuth(username=api_key, password=''),
            timeout=self.DEFAULT_TIMEOUT,
        )

        return self._handle_response(response, dto_cls)

    def _post(self, *, api_key: str, route: str, query_params, dto_cls: Type[T]) -> T:
        url = self._route_url(route)
        response = requests.post(
            url=url,
            params=query_params,
            auth=HTTPBasicAuth(username=api_key, password=''),
            timeout=self.DEFAULT_TIMEOUT,
        )

        return self._handle_response(response, dto_cls)


@Model.describe(
    slug="zapper.balances-job-status",
    version="1.0",
    display_name="Zapper - Get status of balances computation job",
    category="external",
    subcategory="zapper",
    cache=CachePolicy.SKIP,
    input=ZapperBalancesJobStatusInput,
    output=ZapperBalancesJobStatusOutput)
class ZapperBalancesJobStatus(Model, ZapperClient):
    def run(self, input: ZapperBalancesJobStatusInput) -> ZapperBalancesJobStatusOutput:
        params = {
            "jobId": input.jobId
        }

        return self._get(api_key=input.apiKey,
                         route="v2/balances/job-status",
                         query_params=params,
                         dto_cls=ZapperBalancesJobStatusOutput)


@Model.describe(
    slug="zapper.refresh-app-balances",
    version="1.0",
    display_name="Zapper - Refresh wallet-specific app balances",
    category="external",
    subcategory="zapper",
    cache=CachePolicy.SKIP,
    input=ZapperRefreshBalancesInput,
    output=ZapperRefreshBalancesOutput)
class ZapperRefreshAppBalances(Model, ZapperClient):
    def run(self, input: ZapperRefreshBalancesInput) -> ZapperRefreshBalancesOutput:
        params: dict = {
            "addresses[]": input.addresses
        }

        if input.networks:
            params['networks[]'] = input.networks

        return self._post(api_key=input.apiKey,
                          route="v2/balances/apps",
                          query_params=params,
                          dto_cls=ZapperRefreshBalancesOutput)


@Model.describe(
    slug="zapper.app-balances",
    version="1.0",
    display_name="Zapper - Get wallet-specific app balances",
    category="external",
    subcategory="zapper",
    cache=CachePolicy.SKIP,
    input=ZapperGetBalancesInput,
    output=ZapperBalancesOutput)
class ZapperGetAppBalances(Model, ZapperClient):
    def run(self, input: ZapperGetBalancesInput) -> ZapperBalancesOutput:
        params: dict = {
            "addresses[]": input.addresses
        }

        if input.networks:
            params['networks[]'] = input.networks

        status = ZapperJobStatus.COMPLETED
        if input.refresh:
            expiry_time = datetime.now() + timedelta(seconds=input.timeout)
            job_id = self.context.run_model('zapper.refresh-app-balances',
                                            input={
                                                "apiKey": input.apiKey,
                                                "addresses": input.addresses,
                                                "networks": input.networks,
                                            },
                                            return_type=ZapperRefreshBalancesOutput,
                                            local=True).jobId
            while expiry_time > datetime.now():
                status = self.context.run_model('zapper.balances-job-status',
                                                input={
                                                    "apiKey": input.apiKey,
                                                    "jobId": job_id,
                                                },
                                                return_type=ZapperBalancesJobStatusOutput,
                                                local=True).status
                if status is not ZapperJobStatus.ACTIVE:
                    break

                sleep(input.sleep)

        if status is ZapperJobStatus.ACTIVE:
            raise ModelDataError('Timeout exceeded when refreshing balances')

        if status is ZapperJobStatus.UNKNOWN:
            raise ModelDataError('Unknown status of balances')

        response = self._get(api_key=input.apiKey,
                             route="v2/balances/apps",
                             query_params=params,
                             dto_cls=ZapperBalancesResponse)

        return ZapperBalancesOutput(balances=response.__root__)


@Model.describe(
    slug="zapper.refresh-token-balances",
    version="1.0",
    display_name="Zapper - Refresh wallet-specific token balances",
    category="external",
    subcategory="zapper",
    cache=CachePolicy.SKIP,
    input=ZapperRefreshBalancesInput,
    output=ZapperRefreshBalancesOutput)
class ZapperRefreshTokenBalances(Model, ZapperClient):
    def run(self, input: ZapperRefreshBalancesInput) -> ZapperRefreshBalancesOutput:
        params: dict = {
            "addresses[]": input.addresses
        }

        if input.networks:
            params['networks[]'] = input.networks

        return self._post(api_key=input.apiKey,
                          route="v2/balances/tokens",
                          query_params=params,
                          dto_cls=ZapperRefreshBalancesOutput)


@Model.describe(
    slug="zapper.get-token-balances",
    version="1.0",
    display_name="Zapper - Get token balances",
    category="external",
    subcategory="zapper",
    cache=CachePolicy.SKIP,
    input=ZapperGetBalancesInput,
    output=ZapperTokenBalancesOutput)
class ZapperGetTokenBalances(Model, ZapperClient):
    def run(self, input: ZapperGetBalancesInput) -> ZapperTokenBalancesOutput:
        params: dict = {
            "addresses[]": input.addresses
        }

        if input.networks:
            params['networks[]'] = input.networks

        status = ZapperJobStatus.COMPLETED
        if input.refresh:
            expiry_time = datetime.now() + timedelta(seconds=input.timeout)
            job_id = self.context.run_model('zapper.refresh-token-balances',
                                            input={
                                                "apiKey": input.apiKey,
                                                "addresses": input.addresses,
                                                "networks": input.networks,
                                            },
                                            return_type=ZapperRefreshBalancesOutput,
                                            local=True).jobId
            while expiry_time > datetime.now():
                status = self.context.run_model('zapper.balances-job-status',
                                                input={
                                                    "apiKey": input.apiKey,
                                                    "jobId": job_id,
                                                },
                                                return_type=ZapperBalancesJobStatusOutput,
                                                local=True).status

                if status is not ZapperJobStatus.ACTIVE:
                    break

                sleep(input.sleep)

        if status is ZapperJobStatus.ACTIVE:
            raise ModelDataError('Timeout exceeded when refreshing balances')

        if status is ZapperJobStatus.UNKNOWN:
            raise ModelDataError('Unknown status of balances')

        response = self._get(api_key=input.apiKey,
                             route="v2/balances/tokens",
                             query_params=params,
                             dto_cls=ZapperTokenBalancesResponse)

        return ZapperTokenBalancesOutput(balances=response.__root__)


@Model.describe(
    slug="zapper.nft-net-worth",
    version="1.0",
    display_name="Zapper - Value of all NFTs in wallets",
    category="external",
    subcategory="zapper",
    cache=CachePolicy.SKIP,
    input=ZapperNftNetWorthInput,
    output=ZapperNftNetWorthOutput)
class ZapperNftNetWorth(Model, ZapperClient):
    def run(self, input: ZapperNftNetWorthInput) -> ZapperNftNetWorthOutput:
        params = {
            "addresses[]": input.addresses
        }

        net_worth = self._get(api_key=input.apiKey,
                              route="v2/nft/balances/net-worth",
                              query_params=params,
                              dto_cls=ZapperNftNetWorthResponse).__root__

        return ZapperNftNetWorthOutput(netWorth=net_worth)


# This model differs from zapper.nft-balances in that it does not
# return an ordered list of NFTs by USD value, and it allows 100 per page
# versus 25 per page in zapper.nft-balances, and this NFT endpoint is
# much more performant.
@Model.describe(
    slug="zapper.nft-user-tokens",
    version="1.0",
    display_name="Zapper - All individual NFTs owned in a given wallet",
    category="external",
    subcategory="zapper",
    cache=CachePolicy.SKIP,
    input=ZapperNftUserTokensInput,
    output=ZapperNftBalancesOutput)
class ZapperNftUserTokens(Model, ZapperClient):
    def run(self, input: ZapperNftUserTokensInput) -> ZapperNftBalancesOutput:
        params = {
            "userAddress": str(input.address),
        }

        if input.network:
            params["network"] = input.network

        if input.limit:
            params["limit"] = str(input.limit)

        if input.cursor:
            params["cursor"] = input.cursor

        return self._get(api_key=input.apiKey,
                         route="v2/nft/user/tokens",
                         query_params=params,
                         dto_cls=ZapperNftBalancesOutput)


@Model.describe(
    slug="zapper.nft-tokens-balances",
    version="1.0",
    display_name="Zapper - All individual NFTs owned in given wallets",
    category="external",
    subcategory="zapper",
    cache=CachePolicy.SKIP,
    input=ZapperNftBalancesInput,
    output=ZapperNftBalancesOutput)
class ZapperNftBalances(Model, ZapperClient):
    def run(self, input: ZapperNftBalancesInput) -> ZapperNftBalancesOutput:
        params: dict = {
            "addresses[]": input.addresses
        }

        if input.minEstimatedValueUsd:
            params["minEstimatedValueUsd"] = input.minEstimatedValueUsd

        if input.search:
            params["search"] = input.search

        if input.collectionLookUpParams:
            params["collectionLookUpParams[]"] = input.collectionLookUpParams

        if input.network:
            params["network"] = input.network

        if input.limit:
            params["limit"] = str(input.limit)

        if input.cursor:
            params["cursor"] = input.cursor

        return self._get(api_key=input.apiKey,
                         route="v2/nft/balances/tokens",
                         query_params=params,
                         dto_cls=ZapperNftBalancesOutput)


@Model.describe(
    slug="zapper.nft-tokens-totals",
    version="1.0",
    display_name="Zapper - Value of NFTs in the wallets",
    category="external",
    subcategory="zapper",
    cache=CachePolicy.SKIP,
    input=ZapperNftTotalsInput,
    output=ZapperNftTotalsOutput)
class ZapperNftTotals(Model, ZapperClient):
    def run(self, input: ZapperNftTotalsInput) -> ZapperNftTotalsOutput:
        params: dict = {
            "addresses[]": input.addresses
        }

        if input.minEstimatedValueUsd:
            params["minEstimatedValueUsd"] = input.minEstimatedValueUsd

        if input.search:
            params["search"] = input.search

        if input.collectionLookUpParams:
            params["collectionLookUpParams[]"] = input.collectionLookUpParams

        if input.network:
            params["network"] = input.network

        return self._get(api_key=input.apiKey,
                         route="v2/nft/balances/tokens-totals",
                         query_params=params,
                         dto_cls=ZapperNftTotalsOutput)


@Model.describe(
    slug="zapper.nft-collections-balances",
    version="1.0",
    display_name="Zapper - All collections owned in given wallets",
    category="external",
    subcategory="zapper",
    cache=CachePolicy.SKIP,
    input=ZapperCollectionsBalancesInput,
    output=ZapperCollectionsBalancesOutput)
class ZapperNftCollectionsBalances(Model, ZapperClient):
    def run(self, input: ZapperCollectionsBalancesInput) -> ZapperCollectionsBalancesOutput:
        params: dict = {
            "addresses[]": input.addresses
        }

        if input.minCollectionValueUsd:
            params["minCollectionValueUsd"] = input.minCollectionValueUsd

        if input.search:
            params["search"] = input.search

        if input.collectionLookUpParams:
            params["collectionLookUpParams[]"] = input.collectionLookUpParams

        if input.network:
            params["network"] = input.network

        if input.limit:
            params["limit"] = str(input.limit)

        if input.cursor:
            params["cursor"] = input.cursor

        return self._get(api_key=input.apiKey,
                         route="v2/nft/balances/collections",
                         query_params=params,
                         dto_cls=ZapperCollectionsBalancesOutput)


@Model.describe(
    slug="zapper.nft-collections-totals",
    version="1.0",
    display_name="Zapper - Value of collections in the wallets",
    category="external",
    subcategory="zapper",
    cache=CachePolicy.SKIP,
    input=ZapperCollectionsTotalsInput,
    output=ZapperCollectionsTotalsOutput)
class ZapperNftCollectionsTotals(Model, ZapperClient):
    def run(self, input: ZapperCollectionsTotalsInput) -> ZapperCollectionsTotalsOutput:
        params: dict = {
            "addresses[]": input.addresses
        }

        if input.minCollectionValueUsd:
            params["minCollectionValueUsd"] = input.minCollectionValueUsd

        if input.search:
            params["search"] = input.search

        if input.collectionLookUpParams:
            params["collectionLookUpParams[]"] = input.collectionLookUpParams

        if input.network:
            params["network"] = input.network

        return self._get(api_key=input.apiKey,
                         route="v2/nft/balances/collections-totals",
                         query_params=params,
                         dto_cls=ZapperCollectionsTotalsOutput)


@Model.describe(
    slug="zapper.apps",
    version="1.0",
    display_name="Zapper - List of all apps",
    category="external",
    subcategory="zapper",
    cache=CachePolicy.SKIP,
    input=ZapperInput,
    output=ZapperAppsOutput)
class ZapperApps(Model, ZapperClient):
    def run(self, input: ZapperInput) -> ZapperAppsOutput:
        apps = self._get(api_key=input.apiKey,
                         route="v2/apps",
                         query_params={},
                         dto_cls=ZapperAppsResponse).__root__

        return ZapperAppsOutput(apps=apps)


@Model.describe(
    slug="zapper.app-by-slug",
    version="1.0",
    display_name="Zapper - Get app by slug",
    category="external",
    subcategory="zapper",
    cache=CachePolicy.SKIP,
    input=ZapperAppInput,
    output=ZapperApp)
class ZapperAppBySlug(Model, ZapperClient):
    def run(self, input: ZapperAppInput) -> ZapperApp:
        return self._get(api_key=input.apiKey,
                         route=f"v2/apps/{input.appSlug}",
                         query_params={},
                         dto_cls=ZapperApp)


@Model.describe(
    slug="zapper.app-tokens",
    version="1.0",
    display_name="Zapper - App tokens held within a given app for a given groupId",
    category="external",
    subcategory="zapper",
    cache=CachePolicy.SKIP,
    input=ZapperAppTokensInput,
    output=ZapperAppTokensOutput)
class ZapperAppTokens(Model, ZapperClient):
    def run(self, input: ZapperAppTokensInput) -> ZapperAppTokensOutput:
        params = {
            "network": input.network,
            "groupId": input.groupId,
        }

        tokens = self._get(api_key=input.apiKey,
                           route=f"v2/apps/{input.appId}/tokens",
                           query_params=params,
                           dto_cls=ZapperAppTokensResponse).__root__

        return ZapperAppTokensOutput(tokens=tokens)


@Model.describe(
    slug="zapper.app-positions",
    version="1.0",
    display_name="Zapper - Contract positions held within a given app for a given groupId",
    category="external",
    subcategory="zapper",
    cache=CachePolicy.SKIP,
    input=ZapperAppPositionsInput,
    output=ZapperAppPositionsOutput)
class ZapperAppPositions(Model, ZapperClient):
    def run(self, input: ZapperAppPositionsInput) -> ZapperAppPositionsOutput:
        params = {
            "network": input.network,
            "groupId": input.groupId,
        }

        positions = self._get(api_key=input.apiKey,
                              route=f"v2/apps/{input.appId}/positions",
                              query_params=params,
                              dto_cls=ZapperAppPositionsResponse).__root__

        return ZapperAppPositionsOutput(positions=positions)
