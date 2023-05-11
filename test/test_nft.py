# pylint:disable=locally-disabled,line-too-long

import os

from cmf_test import CMFTest

from models.credmark.tokens.nft.nft import AZUKI_NFT


class TestNFT(CMFTest):
    def test_nft(self):
        # credmark-dev run nft.about -i '{"address": "0xED5AF388653567Af2F388E6224dC7C4b3241C544"}' -j --api_url http://localhost:8700
        self.run_model('nft.about', {"address": "0xED5AF388653567Af2F388E6224dC7C4b3241C544"}, block_number=17238456)
        self.run_model('nft.about', {"address": AZUKI_NFT}, block_number=17238456)

        self.run_model('nft.mint', {"address": AZUKI_NFT}, block_number=17238456)

        key = os.environ.get('INFURA_IPFS_KEY')
        secret = os.environ.get('INFURA_IPFS_SECRET')

        if key is not None and secret is not None:
            self.run_model('nft.get', {"address": AZUKI_NFT, "id": 100},
                           block_number=17238456)
