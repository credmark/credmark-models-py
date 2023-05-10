from cmf_test import CMFTest


class TestOptimism(CMFTest):
    def test(self):
        self.title('Optimism')

        chain_id = 10

        last_block_output = self.run_model_with_output(
            'chain.get-latest-block', {}, block_number=None, chain_id=chain_id)

        last_block = last_block_output['output']['blockNumber'] - 100

        # V3 NFT Manager
        # https://optimistic.etherscan.io/address/0xc36442b4a4522e871399cd717abdd847ab11fe88
        self.run_model('uniswap-v3.id',
                       {"id": 30000}, block_number=last_block, chain_id=chain_id)

        self.run_model('uniswap-v3.lp',
                       {"lp": "0x81cc7da862be71a455dd065e87e0f772184a7210"},
                       block_number=last_block,
                       chain_id=chain_id)

        self.run_model('price.oracle-chainlink',
                       {"base": "0xc40f949f8a4e094d1b49a23ea9241d289b7b2819"},
                       block_number=last_block, chain_id=chain_id)
