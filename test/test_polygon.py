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

        # If there is no position, find another account with
        # https://polygonscan.com/token/0xc36442b4a4522e871399cd717abdd847ab11fe88#readProxyContract
        # totalSupply => position for a recent id (-100)
        lp_pos = self.run_model_with_output(
            'uniswap-v3.lp',
            {"lp": "0x470cB7e9981Db525422A16A21d8cD510B0766d17"}, block_number=last_block-1000, chain_id=137)

        lp_pos_id = lp_pos['output']['positions'][0]['id']
        print(f'Fetching Uniswap V3 NFT for {lp_pos_id}')
        self.run_model('uniswap-v3.id',
                       {"id": lp_pos_id}, block_number=last_block-1000, chain_id=137)
