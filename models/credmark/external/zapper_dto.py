from enum import Enum
from typing import Optional
from credmark.cmf.types import Address
from credmark.dto import DTO, DTOField


class ZapperInput(DTO):
    apiKey: str


class ZapperRefreshInput(DTO):
    refresh: bool = DTOField(False, description="Re-compute the balance")
    sleep: int = DTOField(
        10, gt=5, lt=1800, description="Duration (in seconds) to sleep between job status checks.")
    timeout: int = DTOField(
        600, gt=5, lt=1800, description="Timeout (in seconds)")


class ZapperRefreshBalancesInput(ZapperInput):
    addresses: list[Address] = DTOField(..., min_items=1)
    networks: list[str] | None


class ZapperGetBalancesInput(ZapperRefreshBalancesInput, ZapperRefreshInput):
    pass


class ZapperBalancesJobStatusInput(ZapperInput):
    jobId: str


class Value(DTO):
    type: str
    value: float


class StatsItem(DTO):
    label: str
    value: Value


class DisplayProps(DTO):
    label: str
    images: list[str]
    secondaryLabel: Optional[Value] = None
    statsItems: Optional[list[StatsItem]] = None
    labelDetailed: Optional[str] = None
    tertiaryLabel: Optional[str] = None


class AppTokenBalance(DTO):
    type: str
    price: float
    symbol: str
    address: str
    balance: float
    network: str
    decimals: int
    balanceRaw: str
    balanceUSD: float
    metaType: Optional[str] = None
    appId: Optional[str] = None
    supply: Optional[float] = None
    tokens: Optional[list["AppTokenBalance"]] = None
    groupId: Optional[str] = None
    dataProps: Optional[dict] = None
    displayProps: Optional[DisplayProps] = None
    pricePerShare: Optional[list[int]] = None
    key: Optional[str] = None


class Asset(DTO):
    key: str
    type: str
    appId: str
    tokens: list[AppTokenBalance]
    address: str
    groupId: str
    network: str
    dataProps: dict
    balanceUSD: float
    displayProps: DisplayProps
    symbol: Optional[str] = None
    decimals: Optional[int] = None
    supply: Optional[float] = None
    pricePerShare: list[int] | None = None
    price: Optional[float] = None
    balance: Optional[float] = None
    balanceRaw: Optional[str] = None


class MetaItem(DTO):
    label: str
    value: float
    type: str


class Product(DTO):
    label: str
    assets: list[Asset]
    meta: list[MetaItem]


class ZapperBalance(DTO):
    key: str
    address: str
    appId: str
    appName: str
    appImage: str
    network: str
    updatedAt: str
    balanceUSD: float
    products: list[Product]


class ZapperBalancesResponse(DTO):
    __root__: list[ZapperBalance]


class ZapperBalancesOutput(DTO):
    balances: list[ZapperBalance]


class ZapperRefreshBalancesOutput(DTO):
    jobId: str


class ZapperJobStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    UNKNOWN = "unknown"


class ZapperBalancesJobStatusOutput(DTO):
    jobId: str
    status: ZapperJobStatus


class Token(DTO):
    id: str
    networkId: int
    address: str
    label: Optional[str]
    name: str
    symbol: str
    decimals: int
    coingeckoId: str
    status: str
    hide: bool
    canExchange: bool
    verified: bool
    externallyVerified: bool
    priceUpdatedAt: str
    updatedAt: str
    createdAt: str
    price: float
    dailyVolume: float
    totalSupply: str
    holdersEnabled: bool
    marketCap: float
    balance: float
    balanceUSD: float
    balanceRaw: str


class TokenInfo(DTO):
    key: str
    address: str
    network: str
    updatedAt: str
    token: Token


class ZapperTokenBalancesResponse(DTO):
    __root__: dict[str, TokenInfo]


class ZapperTokenBalancesOutput(DTO):
    balances: dict[str, TokenInfo]


class ZapperNftNetWorthInput(ZapperInput):
    addresses: list[Address] = DTOField(..., min_items=1)


class ZapperNftNetWorthResponse(DTO):
    __root__: dict[str, str]


class ZapperNftNetWorthOutput(DTO):
    netWorth: dict[str, str]


class ZapperNftUserTokensInput(ZapperInput):
    address: Address
    network: str | None
    limit: int | None = DTOField(max=100)
    cursor: str | None


class Media(DTO):
    type: str
    originalUrl: str
    fileSize: str
    mimeType: str
    blurhash: Optional[str] = None
    width: int | None = None
    height: int | None = None


class Collection(DTO):
    address: str
    network: str
    name: str
    nftStandard: str
    type: str
    floorPriceEth: str | None
    logoImageUrl: str | None
    openseaId: str


class NftToken(DTO):
    id: str
    name: str
    tokenId: str
    lastSaleEth: Optional[str]
    rarityRank: int
    estimatedValueEth: Optional[str]
    medias: list[Media]
    collection: Collection


class NftItem(DTO):
    balance: str
    token: NftToken


class ZapperNftBalancesOutput(DTO):
    items: list[NftItem]
    cursor: str


class ZapperNftTotalsOutput(DTO):
    count: str
    balanceUSD: str
    totalCount: str


class ZapperNftTotalsInput(ZapperInput):
    addresses: list[Address] = DTOField(..., min_items=1)
    minEstimatedValueUsd: float | None
    search: str | None
    collectionLookUpParams: list[str] | None
    network: str | None


class ZapperNftBalancesInput(ZapperNftTotalsInput):
    limit: int | None = DTOField(max=25)
    cursor: str | None


class SocialLink(DTO):
    name: str
    label: str
    url: str
    logoUrl: str


class Stats(DTO):
    hourlyVolumeEth: float
    hourlyVolumeEthPercentChange: Optional[float]
    dailyVolumeEth: float
    dailyVolumeEthPercentChange: Optional[float]
    weeklyVolumeEth: float
    weeklyVolumeEthPercentChange: Optional[float]
    monthlyVolumeEth: float
    monthlyVolumeEthPercentChange: Optional[float]
    totalVolumeEth: float


class CollectionDetail(DTO):
    name: str
    network: str
    description: str
    logoImageUrl: str
    cardImageUrl: Optional[str]
    bannerImageUrl: Optional[str]
    nftStandard: str
    type: str
    floorPriceEth: Optional[str]
    openseaId: str
    socialLinks: list[SocialLink]
    stats: Stats


class CollectionItem(DTO):
    balance: str
    balanceUSD: str
    collection: CollectionDetail


class ZapperCollectionsBalancesOutput(DTO):
    items: list[CollectionItem]
    cursor: str


class ZapperCollectionsTotalsInput(ZapperInput):
    addresses: list[Address] = DTOField(..., min_items=1)
    minCollectionValueUsd: float | None
    search: str | None
    collectionLookUpParams: list[str] | None
    network: str | None


class ZapperCollectionsBalancesInput(ZapperCollectionsTotalsInput):
    limit: int | None = DTOField(max=25)
    cursor: str | None


class ZapperCollectionsTotalsOutput(DTO):
    count: str
    balanceUSD: str


class TokenItem(DTO):
    address: str
    network: str


class SupportedNetwork(DTO):
    network: str
    actions: list[str]


class AppGroup(DTO):
    type: str
    id: str
    label: Optional[str] = None
    isHiddenFromExplore: bool


class ZapperApp(DTO):
    id: str
    databaseId: int
    slug: str
    name: str
    description: str
    url: str
    imgUrl: str
    tags: list[str]
    token: Optional[TokenItem]
    supportedNetworks: list[SupportedNetwork]
    groups: list[AppGroup]


class ZapperAppsResponse(DTO):
    __root__: list[ZapperApp]


class ZapperAppsOutput(DTO):
    apps: list[ZapperApp]


class ZapperAppInput(ZapperInput):
    appSlug: str


class AppTokenToken(DTO):
    type: str
    network: str
    address: str
    symbol: str
    decimals: int
    price: float
    key: Optional[str] = None
    appId: Optional[str] = None
    supply: Optional[float] = None
    tokens: Optional[list["AppTokenToken"]] = None
    groupId: Optional[str] = None
    dataProps: Optional[dict] = None
    displayProps: Optional[DisplayProps] = None
    pricePerShare: Optional[list[float]] = None


class AppToken(DTO):
    type: str
    price: float
    symbol: str
    address: str
    network: str
    decimals: int
    key: Optional[str] = None
    appId: Optional[str] = None
    supply: Optional[float] = None
    tokens: Optional[list[AppTokenToken]] = None
    groupId: Optional[str] = None
    dataProps: Optional[dict] = None
    displayProps: Optional[DisplayProps] = None
    pricePerShare: Optional[list[float]] = None


class ZapperAppTokensResponse(DTO):
    __root__: list[AppToken]


class ZapperAppTokensOutput(DTO):
    tokens: list[AppToken]


class ZapperAppTokensInput(ZapperInput):
    appId: str
    network: str
    groupId: str


class ZapperPositionToken(DTO):
    metaType: str
    type: str
    network: str
    address: str
    symbol: str
    decimals: int
    price: float
    key: Optional[str] = None
    appId: Optional[str] = None
    supply: Optional[float] = None
    tokens: Optional[list[AppToken]] = None
    groupId: Optional[str] = None
    dataProps: Optional[dict] = None
    displayProps: Optional[DisplayProps] = None
    pricePerShare: Optional[list[float]] = None


class ZapperAppPosition(DTO):
    key: str
    type: str
    appId: str
    groupId: str
    network: str
    address: str
    tokens: list[ZapperPositionToken]
    dataProps: dict
    displayProps: DisplayProps


class ZapperAppPositionsResponse(DTO):
    __root__: list[ZapperAppPosition]


class ZapperAppPositionsOutput(DTO):
    positions: list[ZapperAppPosition]


class ZapperAppPositionsInput(ZapperInput):
    appId: str
    network: str
    groupId: str
