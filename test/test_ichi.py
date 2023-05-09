# pylint:disable=locally-disabled,line-too-long

import json

from cmf_test import CMFTest

from models.credmark.protocols.ichi.ichi_vault import IchiVaults
from models.tmp_abi_lookup import ICHI_VAULT


class TestICHI(CMFTest):
    def test_polygon(self):
        self.title('ICHI - Polygon')

        last_block_output = self.run_model_with_output(
            'chain.get-latest-block', {}, block_number=None, chain_id=137)
        last_block = last_block_output['output']['blockNumber'] - 62
        last_block_2 = last_block_output['output']['blockNumber'] - 31
        self.ichi_tests(last_block, last_block_2)

        remainder = last_block % int(last_block // 1_000_000 * 1_000_000)
        for last_block in [25_697_834, 27_697_834, 34_028_518, 39_028_518]:
            # self.ichi_tests(last_block, last_block)
            self.ichi_tests(last_block + remainder, last_block + remainder)

    def test_event_loading(self):
        # credmark-dev run contract.events -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974", "event_name": "Deposit", "event_abi": [{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"shares","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"Deposit","type":"event"}]}' -c 137 --api_url=http://localhost:8700 -j -b 40100090
        deposit_abi = [{"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": True, "internalType": "address", "name": "to", "type": "address"}, {
            "indexed": False, "internalType": "uint256", "name": "shares", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "amount0", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "amount1", "type": "uint256"}], "name": "Deposit", "type": "event"}]

        self.run_model('contract.events',
                       {"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974",
                           "event_name": "Deposit", "event_abi": deposit_abi},
                       block_number=40100090,
                       chain_id=137)

        self.run_model('contract.events',
                       {"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974",
                           "event_name": "Deposit", "event_abi": deposit_abi},
                       block_number=40100100,
                       chain_id=137)

        ichi_vault_abi = json.loads(ICHI_VAULT)
        withdraw_abi = [x for x in ichi_vault_abi
                        if 'name' in x and x['name'] == 'Withdraw' and 'type' in x and x['type'] == 'event']

        self.run_model('contract.events',
                       {"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974",
                           "event_name": "Withdraw", "event_abi": withdraw_abi},
                       block_number=40100090,
                       chain_id=137)

        self.run_model('contract.events',
                       {"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974",
                           "event_name": "Withdraw", "event_abi": withdraw_abi},
                       block_number=40100100,
                       chain_id=137)

    def test_cash_flow(self):
        # credmark-dev run ichi.vault-cashflow -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974"}' -c 137 --api_url=http://localhost:8700 -j -b 42454582
        # credmark-dev run ichi.vault-cashflow -i '{"address": "0x711901e4b9136119Fb047ABe8c43D49339f161c3"}' -c 137 --api_url=http://localhost:8700 -j -b 41675859
        self.run_model('ichi.vault-cashflow',
                       {"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974"}, block_number=41675859, chain_id=137)
        self.run_model('ichi.vault-cashflow',
                       {"address": "0x711901e4b9136119Fb047ABe8c43D49339f161c3"}, block_number=42454582, chain_id=137)

    def get_token_deployment_block(self, address, last_block, chain_id):
        try:
            deployed_info = self.run_model_with_output(
                'token.deployment',
                {"address": address, "ignore_proxy": True},
                block_number=last_block, chain_id=chain_id)

            return deployed_info["output"]["deployed_block_number"]
        except AssertionError:
            return -1

    def ichi_tests(self, last_block, last_block_2):
        # credmark-dev run ichi.vaults  -c 137 -j
        # credmark-dev run ichi.vault-info -i '' -c 137 -j -b

        # vault_factory: "0x2d2c72C4dC71AA32D64e5142e336741131A73fc0"
        factory_block = self.get_token_deployment_block(
            IchiVaults.VAULT_FACTORY, last_block, 137)
        print(f'{factory_block=}')

        # credmark-dev run ichi.vault-info -i '{"address": "0x8ac3d7cd56816da9fb45e7640aa70a24884e02f7"}' -c 137 -j
        if self.get_token_deployment_block('0x8ac3d7cd56816da9fb45e7640aa70a24884e02f7', last_block, 137) >= last_block:
            self.run_model('ichi.vault-info', {"address": "0x8ac3d7cd56816da9fb45e7640aa70a24884e02f7"},
                           block_number=last_block, chain_id=137)

            self.run_model('ichi.vault-info-full', {
                "address": "0x8ac3d7cd56816da9fb45e7640aa70a24884e02f7"},
                block_number=last_block, chain_id=137)

        # 0x692437de2cAe5addd26CCF6650CaD722d914d974 # LINK-WETH, LINK
        # credmark-dev run ichi.vault-first-deposit -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974"}' --api_url http://localhost:8700 -c 137 -j
        # credmark-dev run ichi.vault-first-deposit -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974"}' -c 137 -j
        if self.get_token_deployment_block('0x692437de2cAe5addd26CCF6650CaD722d914d974', last_block, 137) >= last_block:
            self.run_model('ichi.vault-first-deposit', {
                "address": "0x692437de2cAe5addd26CCF6650CaD722d914d974"},
                block_number=last_block, chain_id=137)

            # credmark-dev run ichi.vault-performance -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974", "days_horizon":[7, 30, 60, 90]}' -c 137 --api_url=http://localhost:8700 -j
            self.run_model('ichi.vault-performance',
                           {"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974",
                            "days_horizon": [7, 30, 60, 90]},
                           block_number=last_block, chain_id=137)

        if self.get_token_deployment_block('0xac6c0264511EeEC305Da9Afc2e1ABa08409F99f6', last_block, 137) >= last_block:
            # 0xac6c0264511EeEC305Da9Afc2e1ABa08409F99f6 # WMATIC-ICHI, ICHI
            self.run_model('ichi.vault-performance',
                           {"address": "0xac6c0264511EeEC305Da9Afc2e1ABa08409F99f6",
                            "days_horizon": []},
                           block_number=last_block, chain_id=137)

        # credmark-dev run ichi.vaults --api_url http://localhost:8700 -c 137
        self.run_model('ichi.vaults', {},
                       block_number=last_block, chain_id=137)

        # credmark-dev run ichi.vaults-performance -i '{}' -c 137 --api_url=http://localhost:8700 -j
        self.run_model('ichi.vaults-performance',
                       {},
                       block_number=last_block_2, chain_id=137)

        # credmark-dev run ichi.vaults-performance -i '{"days_horizon":[7, 30, 60, 90]}' -c 137 --api_url=http://localhost:8700 -j
        self.run_model('ichi.vaults-performance',
                       {"days_horizon": [7, 30, 60, 90]},
                       block_number=last_block_2, chain_id=137)

        self.run_model('ichi.vaults-performance',
                       {"days_horizon": [7, 30, 60, 90], "base": 1000},
                       block_number=last_block_2, chain_id=137)
