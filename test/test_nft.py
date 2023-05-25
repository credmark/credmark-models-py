# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest

from models.credmark.tokens.nft.nft import AZUKI_NFT


class TestNFT(CMFTest):
    def test_nft(self):
        # credmark-dev run nft.about -i '{"address": "0xED5AF388653567Af2F388E6224dC7C4b3241C544"}' -j --api_url http://localhost:8700
        self.run_model('nft.about', {"address": "0xED5AF388653567Af2F388E6224dC7C4b3241C544"}, block_number=17238456)
        self.run_model('nft.about', {"address": AZUKI_NFT}, block_number=17238456)

        self.run_model('nft.mint', {"address": AZUKI_NFT}, block_number=17238456)

        self.run_model('nft.get', {"address": AZUKI_NFT, "id": 100},
                       block_number=17238456)
        self.run_model('nft.get', {"address": '0x5663e3E096f1743e77B8F71b5DE0CF9Dfd058523', "id": 0},
                       block_number=17238456)
