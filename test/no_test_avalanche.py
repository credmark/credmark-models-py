from cmf_test import CMFTest

# 56: bsc
# 137: polygon
# 10: optimism
# 42161: arbitrum
# 250: fantom
# 43114: avalanche


class TestAvalanche(CMFTest):
    def test(self):
        self.title('Avalanche')

        chain_id = 43114

        last_block_output = self.run_model_with_output(
            'chain.get-latest-block', {}, block_number=None, chain_id=chain_id)

        last_block = last_block_output['output']['blockNumber'] - 100

        self.run_model('price.oracle-chainlink',
                       {"base": "0xabc9547b534519ff73921b1fba6e672b5f58d083"},
                       block_number=last_block, chain_id=chain_id)
