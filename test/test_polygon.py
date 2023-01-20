# pylint:disable=locally-disabled,line-too-long,unsubscriptable-object,assignment-from-none

from cmf_test import CMFTest

# credmark-dev run price.oracle-chainlink -i '{"base":"0x1ba42e5193dfa8b03d15dd1b86a3113bbbef8eeb"}' -b 23523151 -c 137 -l "*" -j --api_url=http://localhost:8700


class TestPolygon(CMFTest):
    def test(self):
        self.title('Polygon')

        last_block_output = self.run_model_with_output('chain.get-latest-block', {}, block_number=None, chain_id=137)
        last_block = last_block_output['output']['blockNumber']

        self.run_model('price.oracle-chainlink',
                       {"base": "0x1ba42e5193dfa8b03d15dd1b86a3113bbbef8eeb"}, block_number=last_block-1000, chain_id=137)
