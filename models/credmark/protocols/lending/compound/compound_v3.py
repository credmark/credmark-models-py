# pylint: disable=invalid-name, line-too-long, pointless-string-statement
from typing import cast

from credmark.cmf.model import Model
from credmark.cmf.types import Account, Address, Contract, Network, Token
from credmark.cmf.types.contract import SLOT_EIP1967
from credmark.dto import DTO, EmptyInput

from models.tmp_abi_lookup import CHAINLINK_AGG, COMPOUND_V3_COMET, COMPOUND_V3_COMET_PROXY


class CompoundV3Meta(Model):
    MARKETS = {
        Network.Mainnet: [
            '0xA17581A9E3356d9A858b789D68B4d866e593aE94',  # WETH
            '0xc3d688B66703497DAA19211EEdff47f25384cdc3',  # USDC
        ],
        Network.Polygon: [
            '0xF25212E676D1F7F89Cd72fFEe66158f541246445',  # USDC
        ],
        Network.ArbitrumOne: [
            '0xA5EDBDD9646f8dFF606d7448e414884C7d905dCA',  # USDC
        ],
    }

    SECONDS_PER_YEAR = 60 * 60 * 24 * 365

    def fix_contract(self, address):
        cc = Contract(address).set_abi(COMPOUND_V3_COMET_PROXY, set_loaded=True)
        slot_proxy_address = Address(
            self.context.web3.eth.get_storage_at(address, SLOT_EIP1967))
        # pylint: disable = protected-access
        cc._meta.proxy_implementation = Contract(
            slot_proxy_address).set_abi(COMPOUND_V3_COMET, set_loaded=True)
        return cc

    def run(self, _):
        ...


# .baseToken / .baseScale,

class AssetInfo(DTO):
    offset: int
    asset: Address
    priceFeed: Address
    scale: int
    borrowCollateralFactor: int
    liquidateCollateralFactor: int
    liquidationFactor: int
    supplyCap: int

    @classmethod
    def from_tuple(cls, t):
        return cls(offset=t[0],
                   asset=Address(t[1]),
                   priceFeed=Address(t[2]),
                   scale=t[3],
                   borrowCollateralFactor=t[4],
                   liquidateCollateralFactor=t[5],
                   liquidationFactor=t[6],
                   supplyCap=t[7])


class AssetInfoEx(AssetInfo):
    symbol: str
    decimals: int
    name: str
    price: float
    total_collateral: float
    reserved: float

    @classmethod
    def from_asset_info(cls, info, _market, total_supply_asset, _reserved_collateral):
        token = Token(info.asset)
        price_feed = Contract(address=info.priceFeed).set_abi(CHAINLINK_AGG, set_loaded=True)
        decimals = cast(int, price_feed.functions.decimals().call())
        price = (cast(tuple[int, int, int, int, int],
                      price_feed.functions.latestRoundData().call()))[1] / 10 ** decimals
        # alternatively, use getPrice
        # price_scale = cast(int, _market.functions.priceScale().call())
        # price = market.functions.getPrice(info.priceFeed).call() / 10 ** 8
        total_supply_asset = token.scaled(total_supply_asset)
        _reserved_collateral = token.scaled(_reserved_collateral)
        return cls(**info.dict(),
                   symbol=token.symbol,
                   decimals=token.decimals,
                   name=token.name,
                   price=price,
                   total_collateral=total_supply_asset,
                   reserved=_reserved_collateral)


class MarketInfo(DTO):
    base_token: Address
    base_symbol: str
    utilization: float
    supply_rate: float
    supply_apr: float
    borrow_rate: float
    borrow_apr: float
    total_borrow: float
    total_supply: float
    assets: list[AssetInfoEx]


class CompoundV3Markets(DTO):
    markets: dict[Address, MarketInfo]


class UserBasic(DTO):
    principal: int
    baseTrackingIndex: int
    baseTrackingAccrued: int
    assetsIn: int


@Model.describe(slug="compound-v3.market",
                version="1.0",
                display_name="Compound V3 - get market information",
                description="Query the comet API for Compound V3 assets in the market",
                category='protocol',
                subcategory='compound',
                output=CompoundV3Markets)
class CompoundV2GetAllPools(CompoundV3Meta):
    def get_market_info(self, market_address):

        comet_market = self.fix_contract(market_address)
        base_token = Token(cast(Address, comet_market.functions.baseToken().call()))
        total_supply = base_token.scaled(cast(int, comet_market.functions.totalSupply().call()))
        total_borrow = base_token.scaled(cast(int, comet_market.functions.totalBorrow().call()))
        utilization = cast(int, comet_market.functions.getUtilization().call())
        supply_rate = cast(int, comet_market.functions.getSupplyRate(
            utilization).call()) / (1e18)
        supply_apr = supply_rate * self.SECONDS_PER_YEAR * 100

        borrow_rate = cast(int, comet_market.functions.getBorrowRate(
            utilization).call()) / (1e18)
        borrow_apr = borrow_rate * self.SECONDS_PER_YEAR * 100

        # Comet comet = Comet(0xCometAddress);
        # TotalsCollateral totalsCollateral = comet.totalsCollateral(0xERC20Address);

        # uint balance = comet.balanceOf(0xAccount);
        # uint owed = comet.borrowBalanceOf(0xAccount);
        # UserBasic userBasic = comet.userBasic(0xAccount);

        """
        comet_market.functions.balanceOf('0xa397a8C2086C554B531c02E29f3291c9704B00c7').call();
        comet_market.functions.balanceOf('0xaa945599E60ab5f634D274087f0CEC7fC6d50C87').call();

        comet_market.functions.borrowBalanceOf('0xa397a8C2086C554B531c02E29f3291c9704B00c7').call();
        comet_market.functions.borrowBalanceOf('0xaa945599E60ab5f634D274087f0CEC7fC6d50C87').call();

        comet_market.functions.userBasic('0xa397a8C2086C554B531c02E29f3291c9704B00c7').call();
        comet_market.functions.userBasic('0xaa945599E60ab5f634D274087f0CEC7fC6d50C87').call();
        """

        asset_infos = []
        num_assets = cast(int, comet_market.functions.numAssets().call())
        for i in range(num_assets):
            info = cast(tuple[int, str, str, int, int, int, int, int],
                        comet_market.functions.getAssetInfo(i).call())
            asset_info = AssetInfo.from_tuple(info)
            total_supply_asset, _reserved_collateral = cast(tuple[int, int], comet_market.functions.totalsCollateral(
                asset_info.asset).call())
            asset_infos.append(AssetInfoEx.from_asset_info(
                asset_info, comet_market, total_supply_asset, _reserved_collateral))
        return MarketInfo(
            base_symbol=base_token.symbol,
            base_token=base_token.address,
            utilization=utilization / 1e18,
            supply_rate=supply_rate,
            supply_apr=supply_apr,
            borrow_rate=borrow_rate,
            borrow_apr=borrow_apr,
            total_supply=total_supply,
            total_borrow=total_borrow,
            assets=asset_infos)

    def run(self, _input: EmptyInput) -> CompoundV3Markets:
        market_addresses = self.MARKETS.get(self.context.network, [])

        markets = {}
        for market_address in market_addresses:
            markets[market_address] = self.get_market_info(market_address)

        return CompoundV3Markets(markets=markets)


class CompoundV3LP(Account):
    class Config:
        schema_extra = {
            'examples': [
                {"address": "0xaa945599E60ab5f634D274087f0CEC7fC6d50C87"},  # Deposit
                {"address": "0xa397a8C2086C554B531c02E29f3291c9704B00c7"}  # SupplyCollateral

            ]
        }
