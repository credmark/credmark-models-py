# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest

from models.credmark.protocols.ichi.vault import IchiVaults


class TestICHI(CMFTest):
    def test_polygon(self):
        self.title('ICHI - Polygon')

        last_block_output = self.run_model_with_output(
            'chain.get-latest-block', {}, block_number=None, chain_id=137)
        last_block = last_block_output['output']['blockNumber']

        # credmark-dev run ichi.vaults  -c 137 -j
        # credmark-dev run ichi.vault-info -i '' -c 137 -j -b

        # "0x2d2c72C4dC71AA32D64e5142e336741131A73fc0"
        deployed_info = self.run_model_with_output(
            'token.deployment',
            {"address": IchiVaults.VAULT_FACTORY, "ignore_proxy": True},
            block_number=last_block, chain_id=137)

        print(f'{deployed_info["output"]["deployed_block_number"]=}')

        self.run_model('ichi.vaults', {},
                       block_number=last_block, chain_id=137)

        self.run_model(
            'ichi.vault-info', {"address": "0x8ac3d7cd56816da9fb45e7640aa70a24884e02f7"},
            block_number=last_block, chain_id=137)
