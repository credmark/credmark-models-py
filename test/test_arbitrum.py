from cmf_test import CMFTest


class TestArbitrum(CMFTest):
    def test(self):
        self.title('Arbitrum One')

        chain_id = 42161

        last_block_output = self.run_model_with_output(
            'chain.get-latest-block', {}, block_number=None, chain_id=chain_id)

        last_block = last_block_output['output']['blockNumber']

        # V3 NFT Manager on Arbitrum
        # https://arbiscan.io/address/0xc36442b4a4522e871399cd717abdd847ab11fe88#code
        self.run_model('uniswap-v3.id',
                       {"id": 350000}, block_number=last_block, chain_id=chain_id)

        self.run_model('uniswap-v3.lp',
                       {"lp": "0x721cf5873d65556f8632feba7fb12a73a5feb22e"},
                       block_number=last_block,
                       chain_id=chain_id)
