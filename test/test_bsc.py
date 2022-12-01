# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


# credmark-dev run price.oracle-chainlink -i '{"base":"0xb86abcb37c3a4b64f74f59301aff131a1becc787"}' -b 23523151 --chain_id 56 -l "*" -j --api_url=http://localhost:8700
class TestBSC(CMFTest):
    def test(self):
        self.title('BSC')

        self.run_model('price.oracle-chainlink',
                       {"base": "0xb86abcb37c3a4b64f74f59301aff131a1becc787"}, block_number=23523151, chain_id=56)
