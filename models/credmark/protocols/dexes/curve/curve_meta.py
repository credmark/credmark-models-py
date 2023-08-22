# pylint: disable=locally-disabled, line-too-long, invalid-name

from enum import Enum
from typing import Optional

from credmark.cmf.types import (
    Accounts,
    Address,
    Contract,
    Contracts,
    Network,
)
from credmark.dto import DTOField, IterableListGenericDTO, PrivateAttr
from web3.exceptions import BadFunctionCallOutput, ContractLogicError

from models.tmp_abi_lookup import (
    CRYPTOSWAP_FACTORY_ABI,
    CRYPTOSWAP_REGISTRY_ABI,
    CURVE_ADDRESS_PROVIDER_ABI,
    CURVE_CRYTOSWAP_ABI,
    CURVE_METAPOOL_ABI,
    CURVE_POOL_INFO_ABI,
    CURVE_REGISTRY_ABI,
    CURVE_STABLESWAP_ABI,
    GAUGE_ABI_LP_TOKEN,
    METAPOOL_FACTORY_ABI,
)


class CurveAllGaugesOutput(Contracts):
    lp_tokens: Accounts


class CurvePoolType(str, Enum):
    StableSwap = 'stableswap'
    MetaPool = 'metapool'
    CryptoSwap = 'cryptoswap'
    CryptoSwapFactory = 'cryptoswap_factory'  # permissionless pool created by users


class CurveMeta:
    CURVE_PROVIDER_ALL_NETWORK = '0x0000000022D53366457F9d5E68Ec105046FC4383'

    STABLE_REGISTRY_ADDRESS = "0x90E00ACe148ca3b23Ac1bC8C240C2a7Dd9c2d7f5"
    STABLESWAP_FACTORY = {
        Network.Mainnet: "0xB9fC157394Af804a3578134A6585C0dc9cc990d4",
        Network.ArbitrumOne: "0xb17b674D9c5CB2e441F8e196a2f048A81355d031",
        Network.Optimism: "0x2db0E83599a91b508Ac268a6197b8B14F5e72840"
    }
    CRYPTO_REGISTRY_ADDRESS = "0x9a32aF1A11D9c937aEa61A3790C2983257eA8Bc0"
    CRYPTO_FACTORY_ADDRESS = "0xF18056Bbd320E96A48e3Fbf8bC061322531aac99"

    '''
    [0]: The main registry contract. Used to locate pools and query information about them.
    {1}: Aggregate getter methods for querying large data sets about a single pool. Designed for off-chain use.
    2: Generalized swap contract. Used for finding rates and performing exchanges.
    [3]: The metapool factory.
    4: The fee distributor. Used to distribute collected fees to veCRV holders.
    [5]: The cryptoswap registry contract. Used to locate and query information about pools for uncorrelated assets.
    [6]: The cryptoswap factory.
    '''

    def get_provider(self):
        return (Contract(address=Address(self.CURVE_PROVIDER_ALL_NETWORK).checksum)
                .set_abi(CURVE_ADDRESS_PROVIDER_ABI, set_loaded=True))

    def get_registry(self):
        provider = self.get_provider()
        reg_addr = provider.functions.get_address(0).call()
        registry = (Contract(address=Address(reg_addr).checksum)
                    .set_abi(CURVE_REGISTRY_ABI, set_loaded=True))
        return registry

    def get_metapool_factory(self):
        provider = self.get_provider()
        reg_addr = provider.functions.get_address(3).call()
        registry = (Contract(address=Address(reg_addr).checksum)
                    .set_abi(METAPOOL_FACTORY_ABI, set_loaded=True))
        return registry

    def get_cryptoswap_registry(self):
        provider = self.get_provider()
        reg_addr = provider.functions.get_address(5).call()
        registry = (Contract(address=Address(reg_addr).checksum)
                    .set_abi(CRYPTOSWAP_REGISTRY_ABI, set_loaded=True))
        return registry

    def get_cryptoswap_factory(self):
        provider = self.get_provider()
        reg_addr = provider.functions.get_address(6).call()
        registry = (Contract(address=Address(reg_addr).checksum)
                    .set_abi(CRYPTOSWAP_FACTORY_ABI, set_loaded=True))
        return registry

    def get_pool_info(self):
        provider = self.get_provider()
        pool_info_addr = provider.functions.get_address(1).call()
        pool_info = (Contract(address=Address(pool_info_addr).checksum)
                     .set_abi(CURVE_POOL_INFO_ABI, set_loaded=True))
        return pool_info

    def get_gauge_controller(self):
        registry = self.get_registry()
        gauge_addr = registry.functions.gauge_controller().call()
        gauge_controller = Contract(address=Address(gauge_addr))
        _ = gauge_controller.abi
        return gauge_controller

    def fix_gauge_lp_token(self, token):
        return token.set_abi(GAUGE_ABI_LP_TOKEN, set_loaded=True)

    def is_meta(self, pool_address):
        pool_address_checked = Address(pool_address).checksum
        registry = self.get_registry()
        is_meta = registry.functions.is_meta(pool_address_checked).call()

        metapool_factory = self.get_metapool_factory()
        if metapool_factory.address.is_null():
            return is_meta
        is_meta |= metapool_factory.functions.is_meta(pool_address_checked).call()
        return is_meta


class CurvePool(Contract):
    pool_type: Optional[CurvePoolType] = DTOField(None, description="Pool Type")

    class Config:
        schema_extra = {
            'examples': [
                {'address': '0x43b4fdfd4ff969587185cdb6f0bd875c5fc83f8c', '_test_multi': {'chain_id': 1}},
                {'address': '0xD51a44d3FaE010294C616388b506AcdA1bfAAE46', '_test_multi': {'chain_id': 1}},
                {'address': '0x29a3d66b30bc4ad674a4fdaf27578b64f6afbfe7', '_test_multi': {'chain_id': 10}},
                {'address': '0xc9b8a3fdecb9d5b218d02555a8baf332e5b740d5',
                    '_test_multi': {'chain_id': 42161}},

            ],
            'test_multi': True,
        }

    def get(self):
        contract = self
        if self.pool_type is None:
            try:
                test_contract = contract.set_abi(CURVE_CRYTOSWAP_ABI, set_loaded=True)
                test_contract.functions.D().call()
                self.pool_type = CurvePoolType.CryptoSwap
            except (BadFunctionCallOutput, ContractLogicError):
                curve_meta = CurveMeta()
                if curve_meta.is_meta(contract.address):
                    self.pool_type = CurvePoolType.MetaPool
                else:
                    self.pool_type = CurvePoolType.StableSwap

        match self.pool_type:
            case CurvePoolType.StableSwap:
                return contract.set_abi(CURVE_STABLESWAP_ABI, set_loaded=True)
            case CurvePoolType.MetaPool:
                return contract.set_abi(CURVE_METAPOOL_ABI, set_loaded=True)
            case CurvePoolType.CryptoSwap:
                return contract.set_abi(CURVE_CRYTOSWAP_ABI, set_loaded=True)
            case CurvePoolType.CryptoSwapFactory:
                return contract.set_abi(CURVE_CRYTOSWAP_ABI, set_loaded=True)


class CurvePools(IterableListGenericDTO[CurvePool]):
    contracts: list[CurvePool] = DTOField(
        default=[], description="A List of Contracts")
    _iterator: str = PrivateAttr('contracts')

    def get(self, pool_id):
        return self.contracts[pool_id].get()
