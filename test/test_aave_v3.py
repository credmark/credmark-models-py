# pylint:disable=locally-disabled,line-too-long

from importlib import import_module

from cmf_test import CMFTest

from models.credmark.protocols.lending.aave.aave_v3_deployment import AaveV3Meta


class TestAAVEV3(CMFTest):
    def __init__(self, methodName='runTest'):
        # TODO: useless patching
        mod_model_api = import_module('models.credmark.protocols.lending.aave.aave_v3_deployment')
        mod_model_api.AaveV3Meta.ENABLE_TEST = False
        mod_model_api.AaveV3GetAddressProvider.ENABLE_TEST = False

        super().__init__(methodName)

    def test_aavev3_deployment(self):
        self.title(f"Aave V3 - Deployment - {AaveV3Meta.ENABLE_TEST=}")

        for network in AaveV3Meta.LENDING_POOL_ADDRESS_PROVIDER:
            self.run_model("aave-v3.get-lending-pool-provider",
                           chain_id=network.value,
                           latest_block=True)
            self.run_model('aave-v3.get-lending-pool',
                           chain_id=network.value,
                           latest_block=True)
            self.run_model('aave-v3.get-price-oracle',
                           chain_id=network.value,
                           latest_block=True)
            self.run_model('aave-v3.get-ui-pool-data-provider',
                           chain_id=network.value,
                           latest_block=True)

        for network in AaveV3Meta.LENDING_POOL_ADDRESS_PROVIDER_REGISTRY:
            self.run_model("aave-v3.get-lending-pool-providers-from-registry",
                           chain_id=network.value,
                           latest_block=True)

        for network in AaveV3Meta.LENDING_POOL_INCENTIVE_CONTROLLER:
            self.run_model("aave-v3.get-incentive-controller",
                           chain_id=network.value,
                           latest_block=True)

    def test_account(self):
        mainnet_block_number = 17718493
        polygon_block_number = 45221314

        # credmark-dev run aave-v3.account-summary -i '{"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E"}' -j -b 17718493
        # credmark-dev run aave-v3.account-summary -i '{"address": "0x9b556c24ed6a8b0de593355ba2f6e43830b53699"}' -j -b 45221314 -c 137
        self.run_model('aave-v3.account-summary',
                       {"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E"},
                       chain_id=1,
                       block_number=mainnet_block_number)

        self.run_model('aave-v3.account-summary',
                       {"address": "0x9b556c24ed6a8b0de593355ba2f6e43830b53699"},
                       chain_id=137,
                       block_number=polygon_block_number)

        # credmark-dev run aave-v3.account-info -i '{"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E"}' -j -b 17718493
        # credmark-dev run aave-v3.account-info -i '{"address": "0x9b556c24ed6a8b0de593355ba2f6e43830b53699"}' -j -b 45221314 -c 137
        self.run_model('aave-v3.account-info',
                       {"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E"},
                       chain_id=1,
                       block_number=mainnet_block_number)

        self.run_model('aave-v3.account-info',
                       {"address": "0x9b556c24ed6a8b0de593355ba2f6e43830b53699"},
                       chain_id=137,
                       block_number=polygon_block_number)

        # credmark-dev run aave-v3.account-info-reserve -i '{"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E", "reserve": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"}' -j -b 17718493
        self.run_model('aave-v3.account-info-reserve',
                       {"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E",
                        "reserve": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"},
                       chain_id=1,
                       block_number=mainnet_block_number)

        # credmark-dev run aave-v3.account-info-reserve -i '{"address": "0x9b556c24ed6a8b0de593355ba2f6e43830b53699", "reserve": "0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39"}' -j -b 45221314 -c 137
        self.run_model('aave-v3.account-info-reserve',
                       {"address": "0x9b556c24ed6a8b0de593355ba2f6e43830b53699",
                        "reserve": "0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39"},
                       chain_id=137,
                       block_number=polygon_block_number)

        # credmark-dev run aave-v3.account-summary-historical -i '{"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E", "window": "10 days", "interval": "1 days"}' -j -b 17718493
        # credmark-dev run aave-v3.account-summary-historical -i '{"address": "0x9b556c24ed6a8b0de593355ba2f6e43830b53699", "window": "10 days", "interval": "1 days"}' -j -b 45221314 -c 137
        self.run_model('aave-v3.account-summary-historical',
                       {"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E",
                        "window": "10 days", "interval": "1 days"},
                       chain_id=1,
                       block_number=mainnet_block_number)

        self.run_model('aave-v3.account-summary-historical',
                       {"address": "0x9b556c24ed6a8b0de593355ba2f6e43830b53699",
                        "window": "10 days", "interval": "1 days"},
                       chain_id=137,
                       block_number=polygon_block_number)

        # credmark-dev run aave-v3.account-summary -i '{"address": "0x4aa63e8115c5b29a3e0e062a77c11592931453dc"}' -c 10 -j
        optimism_block_number = 107078524
        self.run_model('aave-v3.account-summary',
                       {"address": "0x4aa63e8115c5b29a3e0e062a77c11592931453dc"},
                       chain_id=10,
                       block_number=optimism_block_number)

        # credmark-dev run aave-v3.account-summary -i '{"address": "0x4aa63e8115c5b29a3e0e062a77c11592931453dc"}' -c 42161 -j
        # credmark-dev run aave-v3.account-info -i '{"address": "0x4aa63e8115c5b29a3e0e062a77c11592931453dc"}' -c 42161 -j
        arbitrum_block_number = 112745173
        self.run_model('aave-v3.account-summary',
                       {"address": "0xfe8da6eded250a4dbc349d8bf6da4f17e9ef14e2"},
                       chain_id=42161,
                       block_number=arbitrum_block_number)

        # credmark-dev run aave-v3.account-summary -i '{"address": "0x34fc4134dc4956955164d8f7ec08d0f78955ac00"}' -c 43114 -j
        # credmark-dev run aave-v3.account-info -i '{"address": "0x34fc4134dc4956955164d8f7ec08d0f78955ac00"}' -c 43114 -j
        avalanche_block_number = 32798022
        self.run_model('aave-v3.account-summary',
                       {"address": "0x34fc4134dc4956955164d8f7ec08d0f78955ac00"},
                       chain_id=43114,
                       block_number=avalanche_block_number)
