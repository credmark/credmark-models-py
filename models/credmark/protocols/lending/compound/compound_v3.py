# pylint: disable=invalid-name, line-too-long, pointless-string-statement
from typing import cast

from credmark.cmf.model import Model
from credmark.cmf.types import Account, Address, Contract, Network, Token
from credmark.dto import DTO, DTOField, EmptyInput
from web3 import Web3

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

    SLOT_EIP1967 = int(Web3.keccak(text='eip1967.proxy.implementation').hex(), 16) - 1

    def fix_contract(self, address):
        cc = Contract(address).set_abi(COMPOUND_V3_COMET_PROXY, set_loaded=True)
        slot_proxy_address = Address(
            self.context.web3.eth.get_storage_at(address, self.SLOT_EIP1967))
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
    borrowCollateralFactor: float
    liquidateCollateralFactor: float
    liquidationFactor: float
    supplyCap: float

    @classmethod
    def from_tuple(cls, t):
        asset = Token(address=t[1])
        return cls(offset=t[0],
                   asset=Address(t[1]),
                   priceFeed=Address(t[2]),
                   scale=t[3],
                   borrowCollateralFactor=t[4] / 1e18,
                   liquidateCollateralFactor=t[5] / 1e18,
                   liquidationFactor=t[6] / 1e18,
                   supplyCap=asset.scaled(t[7]))

    @staticmethod
    def get_price(price_feed):
        price_feed = Contract(address=price_feed).set_abi(CHAINLINK_AGG, set_loaded=True)
        decimals = cast(int, price_feed.functions.decimals().call())
        price = (cast(tuple[int, int, int, int, int],
                      price_feed.functions.latestRoundData().call()))[1] / 10 ** decimals

        # alternatively, use getPrice from market with the default decimals of 8 to scale
        # price_scale = cast(int, market.functions.priceScale().call())
        # price = market.functions.getPrice(price_feed).call() / 10 ** 8
        return price


class AssetInfoEx(AssetInfo):
    symbol: str
    decimals: int
    name: str
    price: float
    total_collateral: float
    reserved_collateral: float

    @classmethod
    def from_asset_info(cls, info, _market, total_supply_asset, _reserved_collateral):
        token = Token(info.asset)
        price = AssetInfo.get_price(info.priceFeed)
        total_supply_asset = token.scaled(total_supply_asset)
        _reserved_collateral = token.scaled(_reserved_collateral)

        return cls(**info.dict(),
                   symbol=token.symbol,
                   decimals=token.decimals,
                   name=token.name,
                   price=price,
                   total_collateral=total_supply_asset,
                   reserved_collateral=_reserved_collateral)


class MarketInfo(DTO):
    base_token: Address
    base_symbol: str
    base_token_price: float
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


@Model.describe(slug="compound-v3.market",
                version="1.1",
                display_name="Compound V3 - get market information",
                description="Query the comet API for Compound V3 assets in the market",
                category='protocol',
                subcategory='compound',
                output=CompoundV3Markets)
class CompoundV3GetAllPools(CompoundV3Meta):
    def get_market_info(self, market_address):
        comet_market = self.fix_contract(market_address)
        base_token = Token(cast(Address, comet_market.functions.baseToken().call()))
        if base_token.address == Token('WETH').address:
            # For WETH base token, price is set to constant 1.0
            # Use external price oracle to get the price
            base_token_price = self.context.run_model(
                'price.oracle-chainlink', {'base': base_token.address})['price']
        else:
            base_token_price_feed = comet_market.functions.baseTokenPriceFeed().call()
            base_token_price = AssetInfo.get_price(base_token_price_feed)

        total_supply = base_token.scaled(cast(int, comet_market.functions.totalSupply().call()))
        total_borrow = base_token.scaled(cast(int, comet_market.functions.totalBorrow().call()))
        utilization = cast(int, comet_market.functions.getUtilization().call())
        supply_rate = cast(int, comet_market.functions.getSupplyRate(
            utilization).call()) / (1e18)
        supply_apr = supply_rate * self.SECONDS_PER_YEAR * 100

        borrow_rate = cast(int, comet_market.functions.getBorrowRate(
            utilization).call()) / (1e18)
        borrow_apr = borrow_rate * self.SECONDS_PER_YEAR * 100

        # Collateral: meaning
        # Borrow: meaning
        # Lending: meaning

        asset_infos = []
        num_assets = cast(int, comet_market.functions.numAssets().call())
        for i in range(num_assets):
            info = cast(tuple[int, str, str, int, int, int, int, int],
                        comet_market.functions.getAssetInfo(i).call())
            asset_info = AssetInfo.from_tuple(info)
            total_supply_asset, _reserved_collateral = cast(
                tuple[int, int],
                comet_market.functions.totalsCollateral(asset_info.asset).call())
            asset_infos.append(AssetInfoEx.from_asset_info(
                asset_info, comet_market, total_supply_asset, _reserved_collateral))

        return MarketInfo(
            base_symbol=base_token.symbol,
            base_token=base_token.address,
            base_token_price=base_token_price,
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
    """
    Found V3 LP accounts among the events of the market

    supplyBase / withdrawBase / withdrawCollateral /  transferCollateral

    event Supply(address indexed from, address indexed dst, uint amount)
    event Transfer(address indexed from, address indexed to, uint amount)
    event Withdraw(address indexed src, address indexed to, uint amount)

    event SupplyCollateral(address indexed from, address indexed dst, address indexed asset, uint amount)
    event TransferCollateral(address indexed from, address indexed to, address indexed asset, uint amount)
    event WithdrawCollateral(address indexed src, address indexed to, address indexed asset, uint amount)
    """

    class Config:
        schema_extra = {
            'examples': [
                {"address": "0xaa945599E60ab5f634D274087f0CEC7fC6d50C87"},  # Deposit
                {"address": "0x52efFC15dFAA1eFC701a8b9522654E4e1C99b012"}   # SupplyCollateral
            ]
        }


class UserBasic(DTO):
    principal: int = DTOField(
        description="the amount of base asset that the account has supplied (greater than zero) or owes (less than zero) to the protocol.")
    baseTrackingIndex: int
    baseTrackingAccrued: int
    assetsIn: int

    @classmethod
    def from_tuple(cls, t):
        return cls(principal=t[0],
                   baseTrackingIndex=t[1],
                   baseTrackingAccrued=t[2],
                   assetsIn=t[3])


class CollateralInfo(DTO):
    asset: Address
    asset_symbol: str
    balance: float
    reserved: float
    total: float
    price: float
    balance_value: float
    reserved_value: float
    total_value: float


class AccountInfo(DTO):
    balance: float
    borrow_balance: float
    balance_value: float
    borrow_value: float
    base_token_principal: float
    base_token_interest: float
    base_token_price: float
    total_collateral_value: float
    collateral: list[CollateralInfo]


class CompoundV3Account(DTO):
    markets: dict[Address, AccountInfo]


@Model.describe(slug="compound-v3.account",
                version="1.2",
                display_name="Compound V3 - get account information",
                description="Query the comet API for Compound V3 account information",
                category='protocol',
                subcategory='compound',
                input=CompoundV3LP,
                output=CompoundV3Account)
class CompoundV3Account4Network(CompoundV3Meta):
    def get_account_info(self, market_address, account_address) -> AccountInfo:
        comet_market = self.fix_contract(market_address)
        base_token = Token(cast(Address, comet_market.functions.baseToken().call()))
        if base_token.address == Token('WETH').address:
            # For WETH base token, price is set to constant 1.0
            # Use external price oracle to get the price
            base_token_price = self.context.run_model(
                'price.oracle-chainlink', {'base': base_token.address})['price']
        else:
            base_token_price_feed = comet_market.functions.baseTokenPriceFeed().call()
            base_token_price = AssetInfo.get_price(base_token_price_feed)

        balance_of = comet_market.functions.balanceOf(account_address.checksum).call()
        borrow_balance_of = comet_market.functions.borrowBalanceOf(account_address.checksum).call()
        user_basic = UserBasic.from_tuple(
            comet_market.functions.userBasic(account_address.checksum).call())

        collateral_infos = []
        num_assets = cast(int, comet_market.functions.numAssets().call())
        total_collateral_value = 0.0
        for i in range(num_assets):
            info = cast(tuple[int, str, str, int, int, int, int, int],
                        comet_market.functions.getAssetInfo(i).call())
            asset_info = AssetInfo.from_tuple(info)
            price = AssetInfo.get_price(asset_info.priceFeed)
            asset = Token(asset_info.asset)
            balance, _reserved = comet_market.functions.userCollateral(
                account_address.checksum, asset.address.checksum).call()

            balance_scaled = asset.scaled(balance)
            reserved_scaled = asset.scaled(_reserved)
            total_scaled = balance_scaled + reserved_scaled
            balance_value = balance_scaled * price
            reserved_value = reserved_scaled * price
            total_value = (balance_scaled + reserved_scaled) * price
            total_collateral_value += total_value
            collateral_info = CollateralInfo(
                asset=asset_info.asset,
                asset_symbol=asset.symbol,
                balance=balance_scaled,
                reserved=reserved_scaled,
                total=total_scaled,
                balance_value=balance_value,
                reserved_value=reserved_value,
                total_value=total_value,
                price=price)

            collateral_infos.append(collateral_info)

        balance_scaled = base_token.scaled(balance_of)
        borrow_balance_scaled = base_token.scaled(borrow_balance_of)

        account_info = AccountInfo(
            balance=balance_scaled,
            borrow_balance=borrow_balance_scaled,
            balance_value=base_token_price * balance_scaled,
            borrow_value=base_token_price * borrow_balance_scaled,
            base_token_principal=base_token.scaled(user_basic.principal),
            base_token_interest=base_token.scaled(user_basic.baseTrackingAccrued),
            base_token_price=base_token_price,
            total_collateral_value=total_collateral_value,
            collateral=collateral_infos)

        return account_info

    def run(self, input: CompoundV3LP) -> CompoundV3Account:
        market_addresses = self.MARKETS.get(self.context.network, [])

        markets = {}
        for market_address in market_addresses:
            markets[market_address] = self.get_account_info(market_address, input.address)

        return CompoundV3Account(markets=markets)
