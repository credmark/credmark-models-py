from cmf_test import CMFTest

# 56: bsc
# 137: polygon
# 10: optimism
# 42161: arbitrum
# 250: fantom
# 43114: avalanche


class TestFantom(CMFTest):
    def test(self):
        self.title('Fantom')

        chain_id = 250

        last_block_output = self.run_model_with_output(
            'chain.get-latest-block', {}, block_number=None, chain_id=chain_id)

        last_block = last_block_output['output']['blockNumber'] - 100

        self.run_model('price.oracle-chainlink',
                       {"base": "0x468003b688943977e6130f4f68f23aad939a1040"},
                       block_number=last_block, chain_id=chain_id)
