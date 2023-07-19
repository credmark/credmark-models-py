# pylint:disable=unsupported-membership-test, line-too-long, pointless-string-statement, protected-access

from typing import Any, NamedTuple, cast

from credmark.cmf.model import Model
from credmark.cmf.types import (
    Address,
    Contract,
    Contracts,
    Network,
)

from models.credmark.tokens.token import get_eip1967_proxy_err_with_abi
from models.tmp_abi_lookup import (
    AAVE_V3_ATOKEN,
    AAVE_V3_ATOKEN_PROXY,
    AAVE_V3_DATA_PROVIDER,
    AAVE_V3_INCENTIVE,
    AAVE_V3_INCENTIVE_PROXY,
    AAVE_V3_ORACLE,
    AAVE_V3_POOL,
    AAVE_V3_POOL_ADDRESSES_PROVIDER,
    AAVE_V3_POOL_ADDRESSES_PROVIDER_REGISTRY,
    AAVE_V3_POOL_PROXY,
    AAVE_V3_UI_POOL_DATA_PROVIDER,
)


class AaveV3Meta:
    ENABLE_TEST = False

    """
    Returns the lending pool providers
    """
    LENDING_POOL_ADDRESS_PROVIDER_REGISTRY = {
        Network.Mainnet: '0xbaA999AC55EAce41CcAE355c77809e68Bb345170',
        Network.Optimism: '0x770ef9f4fe897e59daCc474EF11238303F9552b6',
        Network.ArbitrumOne: '0x770ef9f4fe897e59daCc474EF11238303F9552b6',
        Network.Polygon: '0x770ef9f4fe897e59daCc474EF11238303F9552b6',
        Network.Fantom: '0x770ef9f4fe897e59daCc474EF11238303F9552b6',
        Network.Avalanche: '0x770ef9f4fe897e59daCc474EF11238303F9552b6',
    }

    """
    Returns the lending pool address provider
    """
    LENDING_POOL_ADDRESS_PROVIDER = {
        Network.Mainnet: '0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e',
        Network.Optimism: '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
        Network.ArbitrumOne: '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
        Network.Polygon: '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
        Network.Fantom: '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
        Network.Avalanche: '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
    }

    """
    Returns the incentive controller
    """
    LENDING_POOL_INCENTIVE_CONTROLLER = {
        Network.Mainnet: '0x8164Cc65827dcFe994AB23944CBC90e0aa80bFcb',
        Network.Optimism: '0x929EC64c34a17401F460460D4B9390518E5B473e',
        Network.ArbitrumOne: '0x929EC64c34a17401F460460D4B9390518E5B473e',
        Network.Polygon: '0x929EC64c34a17401F460460D4B9390518E5B473e',
        Network.Fantom: '0x929EC64c34a17401F460460D4B9390518E5B473e',
        Network.Avalanche: '0x929EC64c34a17401F460460D4B9390518E5B473e',
    }

    UI_POOL_DATA_PROVIDER = {
        Network.Mainnet: '0x91c0eA31b49B69Ea18607702c5d9aC360bf3dE7d',
        Network.Optimism: '0xbd83DdBE37fc91923d59C8c1E0bDe0CccCa332d5',
        Network.ArbitrumOne: '0x145dE30c929a065582da84Cf96F88460dB9745A7',
        Network.Polygon: '0xC69728f11E9E6127733751c8410432913123acf1',
        Network.Fantom: '0xddf65434502E459C22263BE2ed7cF0f1FaFD44c0',
        Network.Avalanche: '0xF71DBe0FAEF1473ffC607d4c555dfF0aEaDb878d',
    }


@Model.describe(slug="aave-v3.get-lending-pool-providers-from-registry",
                version="1.0",
                display_name="Aave V3 - Get lending pool providers",
                description="Aave V3 - Get lending pool providers",
                category='protocol',
                subcategory='aave-v3',
                output=Contracts)
class AaveV3GetLendingPoolProviders(Model, AaveV3Meta):
    def run(self, _) -> Contracts:
        addr = Address(self.LENDING_POOL_ADDRESS_PROVIDER_REGISTRY[self.context.network])
        address_provider_registry = (Contract(address=addr)
                                     .set_abi(AAVE_V3_POOL_ADDRESSES_PROVIDER_REGISTRY, set_loaded=True))
        address_providers = address_provider_registry.functions.getAddressesProvidersList().call()
        all_providers = []
        for addr in cast(list[Address], address_providers):
            cc = Contract(address=addr).set_abi(AAVE_V3_POOL_ADDRESSES_PROVIDER, set_loaded=True)
            all_providers.append(cc)
        return Contracts(contracts=all_providers)


@Model.describe(slug="aave-v3.get-lending-pool-provider",
                version="1.0",
                display_name="Aave V3 - Get lending pool providers",
                description="Aave V3 - Get lending pool providers (use with local=True)",
                category='protocol',
                subcategory='aave-v3',
                output=Contract)
class AaveV3GetAddressProvider(Model, AaveV3Meta):
    def run(self, _) -> Contract:
        cc = (Contract(address=self.LENDING_POOL_ADDRESS_PROVIDER[self.context.network])
              .set_abi(AAVE_V3_POOL_ADDRESSES_PROVIDER, set_loaded=True))
        if self.ENABLE_TEST:
            _ = cc.functions.getPool().call()
        return cc


@Model.describe(slug="aave-v3.get-lending-pool",
                version="1.0",
                display_name="Aave V3 - Get lending pool for main market",
                description="Aave V3 - Get lending pool for main market",
                category='protocol',
                subcategory='aave-v3',
                output=Contract)
class AaveV3GetLendingPool(Model, AaveV3Meta):
    def run(self, _) -> Contract:
        lending_pool_provider = (self.context.run_model(
            'aave-v3.get-lending-pool-provider', {},
            return_type=Contract, local=True)
            .set_abi(AAVE_V3_POOL_ADDRESSES_PROVIDER, set_loaded=True))
        lending_pool_address = lending_pool_provider.functions.getPool().call()
        pool = get_eip1967_proxy_err_with_abi(self.context,
                                              self.logger,
                                              lending_pool_address,
                                              True,
                                              AAVE_V3_POOL_PROXY,
                                              AAVE_V3_POOL)
        if self.ENABLE_TEST:
            _ = pool.functions.getReservesList().call()
        return pool


@Model.describe(slug="aave-v3.get-price-oracle",
                version="1.0",
                display_name="Aave V3 - Get price oracle for main market",
                description="Aave V3 - Get price oracle for main market",
                category='protocol',
                subcategory='aave-v3',
                output=Contract)
class AaveV3GetPriceOracle(Model, AaveV3Meta):
    def run(self, _) -> Contract:
        lending_pool_provider = (self.context.run_model(
            'aave-v3.get-lending-pool-provider', {}, return_type=Contract, local=True)
            .set_abi(AAVE_V3_POOL_ADDRESSES_PROVIDER, set_loaded=True))
        price_oracle_address = lending_pool_provider.functions.getPriceOracle().call()
        price_oracle_contract = (Contract(address=price_oracle_address)
                                 .set_abi(AAVE_V3_ORACLE, set_loaded=True))
        if self.ENABLE_TEST:
            _ = price_oracle_contract.functions.ADDRESSES_PROVIDER().call()
        return price_oracle_contract


@Model.describe(slug="aave-v3.get-incentive-controller",
                version="1.0",
                display_name="Aave V3 - Get incentive controller",
                description="Aave V3 - Get incentive controller (use with local=True)",
                category='protocol',
                subcategory='aave-v3',
                output=Contract)
class AaveV3GetIncentiveController(Model, AaveV3Meta):
    def run(self, _) -> Contract:
        incentive_addr = Address(self.LENDING_POOL_INCENTIVE_CONTROLLER[self.context.network])
        incentive = get_eip1967_proxy_err_with_abi(self.context,
                                                   self.logger,
                                                   incentive_addr,
                                                   True,
                                                   AAVE_V3_INCENTIVE_PROXY,
                                                   AAVE_V3_INCENTIVE)
        if self.ENABLE_TEST:
            _ = incentive.functions.getEmissionManager().call()
        return incentive


@Model.describe(slug="aave-v3.get-protocol-data-provider",
                version="1.0",
                display_name="Aave V3 - Get protocol data provider",
                description="Query data provider from address provider",
                category='protocol',
                subcategory='aave-v3',
                output=Contract)
class AaveV3GetProtocolDataProvider(Model, AaveV3Meta):
    def run(self, _) -> Contract:
        """
        Source:
        https://etherscan.io/address/0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e#code

        bytes32 private constant POOL = 'POOL';
        bytes32 private constant POOL_CONFIGURATOR = 'POOL_CONFIGURATOR';
        bytes32 private constant PRICE_ORACLE = 'PRICE_ORACLE';
        bytes32 private constant ACL_MANAGER = 'ACL_MANAGER';
        bytes32 private constant ACL_ADMIN = 'ACL_ADMIN';
        bytes32 private constant PRICE_ORACLE_SENTINEL = 'PRICE_ORACLE_SENTINEL';
        bytes32 private constant DATA_PROVIDER = 'DATA_PROVIDER';

        from web3 import Web3

        # 1. When in this list
        hex_id_short = Web3.to_bytes(text='POOL').hex()
        # 66 = 0x + 64
        hex_id_long = ''.join(['0x'] + [hex_id_short] + (['0'] * (64 - len(hex_id_short))))
        pool_address = lending_pool_provider.functions.getAddress(hex_id_long).call()

        # 2. When not in this list
        0x703c2c8634bed68d98c029c18f310e7f7ec0e5d6342c590190b3cb8b3ba54532
        self.context.web3.keccak(text="INCENTIVES_CONTROLLER")
        # HexBytes('0x703c2c8634bed68d98c029c18f310e7f7ec0e5d6342c590190b3cb8b3ba54532')
        lending_pool_provider.functions.getAddress('0x703c2c8634bed68d98c029c18f310e7f7ec0e5d6342c590190b3cb8b3ba54532').call()
        """

        lending_pool_provider = (
            self.context.run_model(
                'aave-v3.get-lending-pool-provider', {},
                return_type=Contract, local=True)
            .set_abi(AAVE_V3_POOL_ADDRESSES_PROVIDER, set_loaded=True))

        data_provider_address = lending_pool_provider.functions.getPoolDataProvider().call()

        data_provider = (Contract(data_provider_address)
                         .set_abi(AAVE_V3_DATA_PROVIDER, set_loaded=True))

        if self.ENABLE_TEST:
            _ = data_provider.functions.getAllATokens().call()
        return data_provider


class AggregatedReserveData(NamedTuple):
    underlyingAsset: Address
    name: str
    symbol: str
    decimals: int
    baseLTVasCollateral: int
    reserveLiquidationThreshold: int
    reserveLiquidationBonus: int
    reserveFactor: int
    usageAsCollateralEnabled: bool
    borrowingEnabled: bool
    stableBorrowRateEnabled: bool
    isActive: bool
    isFrozen: bool
    # base data
    liquidityIndex: int
    variableBorrowIndex: int
    liquidityRate: int
    variableBorrowRate: int
    stableBorrowRate: int
    lastUpdateTimestamp: int
    aTokenAddress: Address
    stableDebtTokenAddress: Address
    variableDebtTokenAddress: Address
    interestRateStrategyAddress: Address
    #
    availableLiquidity: int
    totalPrincipalStableDebt: int
    averageStableRate: int
    stableDebtLastUpdateTimestamp: int
    totalScaledVariableDebt: int
    priceInMarketReferenceCurrency: int
    priceOracle: Address
    variableRateSlope1: int
    variableRateSlope2: int
    stableRateSlope1: int
    stableRateSlope2: int
    baseStableBorrowRate: int
    baseVariableBorrowRate: int
    optimalUsageRatio: int
    # v3 only
    isPaused: bool
    isSiloedBorrowing: bool
    accruedToTreasury: int
    unbacked: int
    isolationModeTotalDebt: int
    flashLoanEnabled: bool
    #
    debtCeiling: int
    debtCeilingDecimals: int
    eModeCategoryId: int
    borrowCap: int
    supplyCap: int
    # eMode
    eModeLtv: int
    eModeLiquidationThreshold: int
    eModeLiquidationBonus: int
    eModePriceSource: Address
    eModeLabel: str
    borrowableInIsolation: bool


class BaseCurrencyInfo(NamedTuple):
    marketReferenceCurrencyUnit: int
    marketReferenceCurrencyPriceInUsd: int
    networkBaseTokenPriceInUsd: int
    networkBaseTokenPriceDecimals: int


class AaveV3ReservesData(Contract):
    aggregated_reserve_data: list[AggregatedReserveData]
    base_info: BaseCurrencyInfo


@Model.describe(slug="aave-v3.get-ui-pool-data-provider",
                version="1.0",
                display_name="Aave V3 - Get UI pool protocol data provider and its data",
                description="Obtain Reserves data",
                category='protocol',
                subcategory='aave-v3',
                output=AaveV3ReservesData)
class AaveV3GetUIPoolDataProvider(Model, AaveV3Meta):
    def run(self, _) -> AaveV3ReservesData:
        ui_pool_data_provider = (
            Contract(self.UI_POOL_DATA_PROVIDER[self.context.network])
            .set_abi(AAVE_V3_UI_POOL_DATA_PROVIDER, set_loaded=True))

        lending_pool_provider = self.context.run_model(
            'aave-v3.get-lending-pool-provider', {},
            return_type=Contract, local=True)

        reserves_data = cast(tuple[Any, Any], ui_pool_data_provider.functions.getReservesData(
            lending_pool_provider.address.checksum).call())
        aggregated_reserve_data = [AggregatedReserveData(*x) for x in reserves_data[0]]
        base_info = BaseCurrencyInfo(*reserves_data[1])

        return AaveV3ReservesData(address=ui_pool_data_provider.address,
                                  aggregated_reserve_data=aggregated_reserve_data,
                                  base_info=base_info,)


class AaveV3(Model):
    def run(self, _input):
        pass

    def get_lending_pool(self) -> Contract:
        lending_pool_address = self.context.run_model(
            'aave-v3.get-lending-pool', {}, return_type=Contract, local=True)

        aave_lending_pool = get_eip1967_proxy_err_with_abi(self.context,
                                                           self.logger,
                                                           lending_pool_address.address,
                                                           True,
                                                           AAVE_V3_POOL_PROXY,
                                                           AAVE_V3_POOL)
        return aave_lending_pool

    def get_ui_data_provider(self) -> AaveV3ReservesData:
        return (self.context
                .run_model('aave-v3.get-ui-pool-data-provider', {}, return_type=AaveV3ReservesData, local=True))

    def get_protocol_data_provider(self) -> Contract:
        return (self.context
                .run_model("aave-v3.get-protocol-data-provider", {}, return_type=Contract, local=True)
                .set_abi(AAVE_V3_DATA_PROVIDER, set_loaded=True))

    def get_price_oracle(self) -> Contract:
        return (self.context
                .run_model('aave-v3.get-price-oracle', {}, return_type=Contract, local=True)
                .set_abi(AAVE_V3_ORACLE, set_loaded=True))

    def get_atoken(self, address):
        return get_eip1967_proxy_err_with_abi(self.context,
                                              self.logger,
                                              address,
                                              True,
                                              AAVE_V3_ATOKEN_PROXY,
                                              AAVE_V3_ATOKEN)
