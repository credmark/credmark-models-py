# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


# credmark-dev run price.oracle-chainlink -i '{"base":"0x1ba42e5193dfa8b03d15dd1b86a3113bbbef8eeb"}' -b 23523151 -c 137 -l "*" -j --api_url=http://localhost:8700
class TestPolygon(CMFTest):
    def test(self):
        self.title('BSC')

        self.run_model('price.oracle-chainlink',
                       {"base": "0x1ba42e5193dfa8b03d15dd1b86a3113bbbef8eeb"}, block_number=36286847, chain_id=137)

        self.run_model('chain.get-latest-block', {}, block_number=36286847, chain_id=137)
