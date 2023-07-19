# pylint:disable=unsupported-membership-test, line-too-long, pointless-string-statement, protected-access

from typing import cast

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import (
    Address,
    Contract,
    Contracts,
    Network,
)
from web3 import Web3

from models.tmp_abi_lookup import (
    AAVE_DATA_PROVIDER,
    AAVE_LENDING_POOL_PROVIDER,
)


class AaveV2Meta:
    """
    Returns the lending pool providers
    """
    LENDING_POOL_ADDRESS_PROVIDER_REGISTRY = {
        Network.Mainnet: '0x52D306e36E3B6B02c153d0266ff0f85d18BCD413',
        Network.Görli: '0x3465454D658019f8A0eABD3bC61d2d1Dd3a0735F',
        Network.Polygon: '0x3ac4e9aa29940770aeC38fe853a4bbabb2dA9C19',
        Network.Avalanche: '0x4235E22d9C3f28DCDA82b58276cb6370B01265C2',
        # DEPRECATED - Kovan
        # Network.Kovan: '0x1E40B561EC587036f9789aF83236f057D1ed2A90'
    }

    """
    Returns the incentive controller
    """
    LENDING_POOL_INCENTIVE_CONTROLLER = {
        Network.Mainnet: '0xd784927Ff2f95ba542BfC824c8a8a98F3495f6b5',
        Network.Polygon: '0x357D51124f59836DeD84c8a1730D72B749d8BC23',
        Network.Avalanche: '0x01D83Fe6A10D2f2B7AF17034343746188272cAc9',
    }

    """
    Returns the lending pool address provider
    """
    LENDING_POOL_ADDRESS_PROVIDER = {
        Network.Mainnet: '0xB53C1a33016B2DC2fF3653530bfF1848a515c8c5',
        Network.Görli: '0x5E52dEc931FFb32f609681B8438A51c675cc232d',
        Network.Polygon: '0xd05e3E715d945B59290df0ae8eF85c1BdB684744',
        Network.Avalanche: '0xb6A86025F0FE1862B372cb0ca18CE3EDe02A318f',
        # DEPRECATED - Kovan
        # Network.Kovan: '0x88757f2f99175387ab4c6a4b3067c77a695b0349'
    }


@Model.describe(slug="aave-v2.get-lending-pool-providers-from-registry",
                version="1.1",
                display_name="Aave V2 - Get lending pool providers",
                description="Aave V2 - Get lending pool providers",
                category='protocol',
                subcategory='aave-v2',
                output=Contracts)
class AaveV2GetLendingPoolProviders(Model, AaveV2Meta):
    def run(self, _) -> Contracts:
        addr = Address(
            self.LENDING_POOL_ADDRESS_PROVIDER_REGISTRY[self.context.network])
        address_provider_registry = Contract(address=addr)
        address_providers = address_provider_registry.functions.getAddressesProvidersList().call()
        all_providers = []
        for addr in cast(list[Address], address_providers):
            cc = Contract(address=addr)
            _ = cc.abi
            all_providers.append(cc)
        return Contracts(contracts=all_providers)


@Model.describe(slug="aave-v2.get-incentive-controller",
                version="0.1",
                display_name="Aave V2 - Get incentive controller",
                description="Aave V2 - Get incentive controller",
                category='protocol',
                subcategory='aave-v2',
                output=Contract)
class AaveV2GetIncentiveController(Model, AaveV2Meta):
    def run(self, _) -> Contract:
        addr = Address(
            self.LENDING_POOL_INCENTIVE_CONTROLLER[self.context.network])
        return Contract(address=addr)


@Model.describe(slug="aave-v2.get-lending-pool-provider",
                version="1.1",
                display_name="Aave V2 - Get lending pool providers",
                description="Aave V2 - Get lending pool providers",
                category='protocol',
                subcategory='aave-v2',
                output=Contract)
class AaveV2GetAddressProvider(Model, AaveV2Meta):
    def run(self, _) -> Contract:
        cc = Contract(address=self.LENDING_POOL_ADDRESS_PROVIDER[self.context.network]).set_abi(
            AAVE_LENDING_POOL_PROVIDER, set_loaded=True)
        _ = cc.abi
        return cc


@Model.describe(slug="aave-v2.get-protocol-data-provider",
                version="1.2",
                display_name="Aave V2 - Get protocol data provider",
                description="Query data provider from address provider",
                category='protocol',
                subcategory='aave-v2',
                output=Contract)
class AaveV2GetProtocolDataProvider(Model):
    def run(self, _) -> Contract:
        lending_pool_provider = self.context.run_model(
            'aave-v2.get-lending-pool-provider', {},
            return_type=Contract, local=True)

        try:
            _ = lending_pool_provider.abi
        except ModelDataError:
            lending_pool_provider.set_abi(
                AAVE_LENDING_POOL_PROVIDER, set_loaded=True)

        try:
            data_provider_address = lending_pool_provider.functions.getAddress(
                "0x01").call()
        except Exception:  # Web3ValidationError:
            data_provider_address = lending_pool_provider.functions.getAddress(Web3.to_bytes(  # type: ignore  # pylint: disable=no-member
                0x0100000000000000000000000000000000000000000000000000000000000000)).call()
        data_provider = Contract(data_provider_address).set_abi(
            AAVE_DATA_PROVIDER, set_loaded=True)
        return data_provider


@Model.describe(slug="aave-v2.get-lending-pool",
                version="1.2",
                display_name="Aave V2 - Get lending pool for main market",
                description="Aave V2 - Get lending pool for main market",
                category='protocol',
                subcategory='aave-v2',
                output=Contract)
class AaveV2GetLendingPool(Model):
    def run(self, _) -> Contract:
        lending_pool_provider = self.context.run_model(
            'aave-v2.get-lending-pool-provider', {},
            return_type=Contract, local=True)
        lending_pool_address = lending_pool_provider.functions.getLendingPool().call()
        return Contract(address=lending_pool_address)


@Model.describe(slug="aave-v2.get-price-oracle",
                version="1.2",
                display_name="Aave V2 - Get price oracle for main market",
                description="Aave V2 - Get price oracle for main market",
                category='protocol',
                subcategory='aave-v2',
                output=Contract)
class AaveV2GetPriceOracle(Model):
    def run(self, _) -> Contract:
        lending_pool_provider = self.context.run_model(
            'aave-v2.get-lending-pool-provider', {},
            return_type=Contract, local=True)
        price_oracle_address = lending_pool_provider.functions.getPriceOracle().call()
        price_oracle_contract = Contract(address=price_oracle_address)
        _ = price_oracle_contract.abi
        return price_oracle_contract


"""
# PriceOracle
# getAssetPrice() Returns the price of the supported _asset in ETH wei units.
# getAssetsPrices() Returns the price of the supported _asset in ETH wei units.
# getSourceOfAsset()
# getFallbackOracle()
"""
