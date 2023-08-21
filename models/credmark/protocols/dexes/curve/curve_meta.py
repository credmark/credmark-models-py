# pylint: disable=locally-disabled, line-too-long

from abc import abstractmethod

from credmark.cmf.model import Model
from credmark.cmf.types import (
    Accounts,
    Address,
    Contract,
    Contracts,
)

from models.tmp_abi_lookup import CURVE_ADDRESS_PROVIDER_ABI, CURVE_REGISTRY_ABI, CURVE_VYPER_POOL, GAUGE_ABI_LP_TOKEN


class CurvePoolContract(Contract):
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


class CurveFiAllGaugesOutput(Contracts):
    lp_tokens: Accounts


class CurveMeta(Model):
    CURVE_PROVIDER_ALL_NETWORK = '0x0000000022D53366457F9d5E68Ec105046FC4383'

    def get_provider(self):
        return (Contract(address=Address(self.CURVE_PROVIDER_ALL_NETWORK).checksum)
                .set_abi(CURVE_ADDRESS_PROVIDER_ABI, set_loaded=True))

    def get_registry(self):
        provider = self.get_provider()
        reg_addr = provider.functions.get_registry().call()
        registry = (Contract(address=Address(reg_addr).checksum)
                    .set_abi(CURVE_REGISTRY_ABI, set_loaded=True))
        return registry

    def get_gauge_controller(self):
        registry = self.get_registry()
        gauge_addr = registry.functions.gauge_controller().call()
        gauge_controller = Contract(address=Address(gauge_addr))
        _ = gauge_controller.abi
        return gauge_controller

    def fix_pool(self, contract):
        return contract.set_abi(CURVE_VYPER_POOL, set_loaded=True)

    def fix_gauge_lp_token(self, token):
        return token.set_abi(GAUGE_ABI_LP_TOKEN, set_loaded=True)

    @abstractmethod
    def run(self, input):
        ...
